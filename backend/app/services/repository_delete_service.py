"""
Handles full repository deletion: local clone folder, Pinecone vectors,
and the DB row (which cascades to files/chunks/findings/docs/chat data).
"""
import os
import stat
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmbeddingMetadata, Repository
from app.services.vector_store_service import delete_vectors_by_ids


class DeleteError(Exception):
    pass


async def delete_repository(db: AsyncSession, repository: Repository) -> None:
    # 1. Collect vector IDs before anything is deleted from the DB
    result = await db.execute(
        select(EmbeddingMetadata.vector_id)
        .join(EmbeddingMetadata.chunk)
        .where(EmbeddingMetadata.chunk.has(repository_id=repository.id))
    )
    vector_ids = [row[0] for row in result.all()]

    # 2. Delete vectors from Pinecone (best-effort — don't let a Pinecone
    #    hiccup block the rest of cleanup, since stale vectors are cheap
    #    to have and expensive to be stuck unable to delete a repo over)
    try:
        delete_vectors_by_ids(vector_ids)
    except Exception:
        pass  # local + DB cleanup still proceeds; orphaned vectors are harmless

    # 3. Delete the local cloned folder from disk.
    # Git clones often mark files read-only on Windows, which blocks a
    # plain rmtree — this handler clears the read-only flag and retries.
    if repository.local_path:
        local_path = Path(repository.local_path)
        if local_path.exists():
            def _remove_readonly(func, path, exc_info):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            shutil.rmtree(local_path, onerror=_remove_readonly)

    # 4. Delete the DB row — cascades to files, chunks, embeddings_metadata,
    #    security_findings, generated_docs, chat_sessions, chat_messages
    #    (all already defined with cascade="all, delete-orphan")
    await db.delete(repository)
    await db.commit()