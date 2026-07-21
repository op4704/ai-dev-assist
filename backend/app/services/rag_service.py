"""
Orchestrates the full RAG pipeline:
  index_repository:  files (on disk) -> chunks -> embeddings -> Pinecone + DB
  chat_with_repository: question -> embed -> retrieve -> Groq -> answer + citations
"""
import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Chunk, EmbeddingMetadata, File, Repository, ChatSession, ChatMessage
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_texts, embed_query, EmbeddingError
from app.services.vector_store_service import upsert_vectors, query_vectors
from app.services.llm_service import generate_answer


class RagError(Exception):
    pass


EMBED_BATCH_SIZE = 20
BATCH_DELAY_SECONDS = 1.5


def _read_file_content(repository: Repository, file: File) -> str | None:
    if not repository.local_path:
        return None
    full_path = os.path.join(repository.local_path, file.path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None


async def index_repository(db: AsyncSession, repository: Repository) -> dict:
    result = await db.execute(select(File).where(File.repository_id == repository.id))
    files = result.scalars().all()

    if not files:
        raise RagError("Repository has no indexed files yet")

    total_chunks = 0
    total_embedded = 0
    skipped_files = 0

    pending: list[dict] = []
    for file in files:
        content = _read_file_content(repository, file)
        if content is None:
            skipped_files += 1
            continue

        for cr in chunk_text(
            content,
            chunk_size_tokens=settings.chunk_size_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        ):
            pending.append({"file": file, "chunk": cr})

    if not pending:
        raise RagError("No embeddable content found in this repository's files")

    for i in range(0, len(pending), EMBED_BATCH_SIZE):
        batch = pending[i : i + EMBED_BATCH_SIZE]
        texts = [item["chunk"].content for item in batch]

        try:
            embeddings = await embed_texts(texts, task="retrieval.passage")
        except EmbeddingError as exc:
            # Progress from earlier batches was already committed below,
            # so this only loses the current (uncommitted) batch.
            raise RagError(f"Embedding failed on batch {i // EMBED_BATCH_SIZE}: {exc}") from exc

        db_chunks = []
        for item, embedding in zip(batch, embeddings):
            file = item["file"]
            cr = item["chunk"]
            chunk_row = Chunk(
                file_id=file.id,
                repository_id=repository.id,
                chunk_index=cr.chunk_index,
                content=cr.content,
                start_line=cr.start_line,
                end_line=cr.end_line,
                token_count=cr.token_count,
            )
            db.add(chunk_row)
            db_chunks.append((chunk_row, file, embedding))

        await db.flush()  # populate chunk_row.id

        vectors_to_upsert = []
        for chunk_row, file, embedding in db_chunks:
            vector_id = f"repo{repository.id}-chunk{chunk_row.id}"
            vectors_to_upsert.append(
                (
                    vector_id,
                    embedding,
                    {
                        "repository_id": repository.id,
                        "file_id": file.id,
                        "chunk_id": chunk_row.id,
                        "path": file.path,
                        "start_line": chunk_row.start_line,
                        "end_line": chunk_row.end_line,
                    },
                )
            )
            db.add(
                EmbeddingMetadata(
                    chunk_id=chunk_row.id,
                    vector_id=vector_id,
                    embedding_model=settings.jina_model,
                    dimension=settings.embedding_dimension,
                )
            )

        upsert_vectors(vectors_to_upsert)
        await db.commit()  # persist this batch now so a later failure can't roll it back

        total_chunks += len(batch)
        total_embedded += len(batch)

        if i + EMBED_BATCH_SIZE < len(pending):
            await asyncio.sleep(BATCH_DELAY_SECONDS)

    return {
        "files_processed": len(files) - skipped_files,
        "files_skipped": skipped_files,
        "chunks_created": total_chunks,
        "vectors_embedded": total_embedded,
    }


async def chat_with_repository(
    db: AsyncSession,
    repository: Repository,
    question: str,
    session_id: int | None = None,
    top_k: int = 5,
) -> dict:
    query_embedding = await embed_query(question)

    matches = query_vectors(
        query_embedding,
        top_k=top_k,
        filter_metadata={"repository_id": repository.id},
    )

    if not matches:
        raise RagError("No relevant content found — has this repository been indexed yet?")

    context_chunks = [
        {
            "path": m["metadata"].get("path", "unknown"),
            "start_line": m["metadata"].get("start_line"),
            "end_line": m["metadata"].get("end_line"),
            "content": "",
        }
        for m in matches
    ]

    chunk_ids = [cid for cid in (m["metadata"].get("chunk_id") for m in matches) if cid is not None]
    chunk_rows = {}
    if chunk_ids:
        result = await db.execute(select(Chunk).where(Chunk.id.in_(chunk_ids)))
        chunk_rows = {c.id: c for c in result.scalars().all()}

    for i, m in enumerate(matches):
        chunk_row = chunk_rows.get(m["metadata"].get("chunk_id"))
        if chunk_row:
            context_chunks[i]["content"] = chunk_row.content

    if not any(c["content"] for c in context_chunks):
        raise RagError(
            "Matched vectors reference chunks that no longer exist in the database. "
            "This can happen after a failed indexing run — please re-run /index."
        )

    if session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise RagError("Chat session not found")

        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        )
        conversation_history = [{"role": r.role, "content": r.content} for r in result.scalars().all()]
        session_id_value = session.id
    else:
        session = ChatSession(
            repository_id=repository.id,
            user_id=repository.user_id,
            title=question[:255],
        )
        db.add(session)
        await db.flush()
        session_id_value = session.id
        conversation_history = []

    answer = await generate_answer(question, context_chunks, conversation_history)

    citations = [f"{c['path']}:{c['start_line']}-{c['end_line']}" for c in context_chunks]

    db.add(ChatMessage(session_id=session_id_value, role="user", content=question))
    db.add(
        ChatMessage(
            session_id=session_id_value,
            role="assistant",
            content=answer,
            citations=", ".join(citations),
        )
    )
    await db.commit()

    return {
        "session_id": session_id_value,
        "answer": answer,
        "citations": citations,
    }