"""
Handles storing and retrieving embedding vectors in Pinecone.
Uses the modern Pinecone client (v9+, no environment param needed).
"""
from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings


class VectorStoreError(Exception):
    pass


_pc_client: Pinecone | None = None


def _get_client() -> Pinecone:
    global _pc_client
    if not settings.pinecone_api_key:
        raise VectorStoreError("PINECONE_API_KEY is not configured")
    if _pc_client is None:
        _pc_client = Pinecone(api_key=settings.pinecone_api_key)
    return _pc_client


def _ensure_index(pc: Pinecone) -> None:
    existing = [idx["name"] for idx in pc.list_indexes()]
    if settings.pinecone_index_name not in existing:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


def upsert_vectors(
    vectors: list[tuple[str, list[float], dict]],
) -> None:
    """
    vectors: list of (vector_id, embedding, metadata_dict)
    """
    if not vectors:
        return

    pc = _get_client()
    _ensure_index(pc)
    index = pc.Index(settings.pinecone_index_name)

    payload = [
        {"id": vec_id, "values": embedding, "metadata": metadata}
        for vec_id, embedding, metadata in vectors
    ]
    index.upsert(vectors=payload)


def query_vectors(
    query_embedding: list[float],
    top_k: int = 5,
    filter_metadata: dict | None = None,
) -> list[dict]:
    pc = _get_client()
    _ensure_index(pc)
    index = pc.Index(settings.pinecone_index_name)

    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_metadata,
    )
    return [
        {
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        }
        for match in result.get("matches", [])
    ]


def delete_repository_vectors(repository_id: int) -> None:
    """Removes all vectors for a repository when it's deleted/reindexed."""
    pc = _get_client()
    index = pc.Index(settings.pinecone_index_name)
    index.delete(filter={"repository_id": repository_id})