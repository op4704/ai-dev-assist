"""
Calls Groq's chat completion API to answer questions using retrieved context.
"""
import httpx

from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(Exception):
    pass


SYSTEM_PROMPT = """You are a senior software engineer helping a developer understand a codebase.
You will be given relevant code chunks retrieved from the repository, each labeled with its file path and line range.

Rules:
- Answer using ONLY the provided context. If the context doesn't contain enough information, say so clearly.
- Always cite the specific file path and line range(s) you drew your answer from.
- Be precise and technical. Don't pad your answer with generic advice.
- If asked to show code, quote only the relevant lines from the provided context.
"""


def _build_context_block(chunks: list[dict]) -> str:
    """
    chunks: list of dicts with keys: path, start_line, end_line, content
    """
    parts = []
    for c in chunks:
        parts.append(
            f"--- {c['path']} (lines {c['start_line']}-{c['end_line']}) ---\n{c['content']}"
        )
    return "\n\n".join(parts)


async def generate_answer(
    question: str,
    context_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    context_chunks: retrieved chunks with path/start_line/end_line/content
    conversation_history: list of {"role": "user"|"assistant", "content": str}
    """
    if not settings.GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY is not configured")

    context_block = _build_context_block(context_chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        {
            "role": "user",
            "content": f"Context from repository:\n\n{context_block}\n\nQuestion: {question}",
        }
    )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise LLMError(f"Groq API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]