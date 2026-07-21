import asyncio
import httpx

from app.core.config import settings

JINA_URL = "https://api.jina.ai/v1/embeddings"
MAX_RETRIES = 5


class EmbeddingError(Exception):
    pass


async def embed_texts(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    if not settings.jina_api_key:
        raise EmbeddingError("JINA_API_KEY is not configured")
    if not texts:
        return []

    headers = {
        "Authorization": f"Bearer {settings.jina_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.jina_model,
        "task": task,
        "input": texts,
        "truncate": True,
    }

    delay = 2.0
    last_error = ""

    for attempt in range(MAX_RETRIES):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(JINA_URL, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = sorted(data["data"], key=lambda item: item["index"])
            return [item["embedding"] for item in results]

        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            wait_time = float(retry_after) if retry_after else delay
            last_error = f"429 rate limited, retrying in {wait_time}s"
            await asyncio.sleep(wait_time)
            delay *= 2
            continue

        raise EmbeddingError(f"Jina API error {response.status_code}: {response.text}")

    raise EmbeddingError(f"Jina rate-limited after {MAX_RETRIES} retries: {last_error}")


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text], task="retrieval.query")
    return vectors[0]