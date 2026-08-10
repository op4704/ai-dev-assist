"""
Generates documentation (README, API docs, architecture overview) for a
repository by feeding key file contents to Groq. Unlike chat (RAG-based,
top-k retrieval for one question), this pulls broader context directly
from the file list since the goal is a comprehensive document, not an
answer to a specific question.
"""
import os

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import File, GeneratedDoc, Repository

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Cap how much raw source we feed the model — keeps prompts within
# Groq's context window and keeps generation fast.
MAX_CONTEXT_CHARS = 20_000  # Groq free tier is 12k TPM — same tight cap applies everywhere
MAX_API_CONTEXT_CHARS = 20_000

ARCHITECTURE_SYSTEM_PROMPT = """You are a senior software engineer writing an architecture overview for a codebase.
You will be given a broad sample of files from the repository, including entry points, configuration, and core source files.

Write a clear architecture document covering:
- High-level overview (what kind of system this is — web app, CLI, library, etc.)
- Main components/modules and what each is responsible for
- How data/requests flow through the system (e.g. entry point → routing → business logic → data layer, if applicable)
- Key dependencies or frameworks the architecture relies on
- Notable design patterns you observe

Base everything on the actual code and structure shown — do not invent components or flows that aren't evidenced in the context. If the codebase is small or simple, keep the document proportionally short rather than padding it. Output only the document in Markdown, no commentary before or after."""

API_DOCS_SYSTEM_PROMPT = """You are a senior software engineer writing API documentation for a codebase.
You will be given files that likely contain route/endpoint definitions (REST API routes, controllers, or similar).

For each endpoint you find, document:
- HTTP method and path
- Brief description of what it does
- Request parameters/body (if evident from the code)
- Response shape (if evident from the code)

Group endpoints logically (e.g. by resource or router file). If the codebase does not appear to expose any HTTP API (e.g. it's a CLI tool or library), say so clearly instead of inventing endpoints.

Base everything on the actual code shown — do not invent parameters, routes, or behavior not evidenced in the context. Output only the documentation in Markdown, no commentary before or after."""

README_SYSTEM_PROMPT = """You are a senior software engineer writing a README for a GitHub repository.
You will be given a list of files and their contents from the repository.

Write a clear, professional README.md with these sections (skip a section only if there is truly nothing relevant):
- Project title and one-line description
- Overview (what the project does, 2-4 sentences)
- Features (bullet list)
- Installation (based on any config/dependency files you see)
- Usage (basic example if you can infer one)
- Project Structure (brief, based on the files shown)

Base everything on the actual code and files provided — do not invent features or dependencies that aren't evidenced in the context. Output only the README content in Markdown, no commentary before or after."""


class DocGenError(Exception):
    pass


def _read_file_content(repository: Repository, file: File) -> str | None:
    if not repository.local_path:
        return None
    full_path = os.path.join(repository.local_path, file.path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None


# Files worth prioritizing when picking context for a README
PRIORITY_NAMES = {"readme.md", "readme", "pyproject.toml", "package.json", "setup.py", "requirements.txt"}
PRIORITY_EXTENSIONS = {".md"}


def _select_readme_context_files(files: list[File]) -> list[File]:
    """
    Picks a manageable, high-signal set of files for README generation:
    existing docs/config files first, then entry-point-like files.
    """
    priority = [
        f for f in files
        if f.path.lower().split("/")[-1] in PRIORITY_NAMES
        or os.path.splitext(f.path)[1].lower() in PRIORITY_EXTENSIONS
    ]

    # Fill remaining budget with other files, favoring shallow paths
    # (root-level / top-level files are usually more structurally important)
    others = sorted(
        (f for f in files if f not in priority),
        key=lambda f: f.path.count("/"),
    )

    return priority + others

# Signals that a file likely contains route/endpoint definitions
API_PATH_HINTS = ("route", "router", "controller", "api", "endpoint", "views")
API_KEYWORD_HINTS = ("@app.", "@router.", "APIRouter", "app.get(", "app.post(", "app.put(", "app.delete(", "express()", "Blueprint(")


def _select_api_context_files(repository: Repository, files: list[File]) -> list[File]:
    """
    Picks files likely to contain route/endpoint definitions, first by
    path naming convention, then falls back to a quick content scan for
    common routing keywords if naming alone doesn't turn up much.
    """
    by_path = [
        f for f in files
        if any(hint in f.path.lower() for hint in API_PATH_HINTS)
        and os.path.splitext(f.path)[1].lower() in {".py", ".js", ".ts"}
    ]

    if len(by_path) >= 1:
        return by_path

    # Fallback: scan a bounded number of source files for routing keywords
    candidates = [
        f for f in files
        if os.path.splitext(f.path)[1].lower() in {".py", ".js", ".ts"}
    ][:200]  # bound the scan so this can't run away on huge repos

    matched = []
    for f in candidates:
        content = _read_file_content(repository, f)
        if content and any(kw in content for kw in API_KEYWORD_HINTS):
            matched.append(f)
            if len(matched) >= 10:  # cap matches so context can't explode
                break

    return matched


# Files that typically anchor a codebase's architecture: entry points,
# core config, and top-level source directories
ARCHITECTURE_HINTS = ("main", "app", "index", "server", "config", "settings", "__init__")


def _select_architecture_context_files(files: list[File]) -> list[File]:
    """
    Picks a broad, structurally-representative sample: entry-point-like
    files first, then a spread across the shallowest directories so the
    model sees the overall shape of the codebase rather than deep detail
    in any one area.
    """
    anchors = [
        f for f in files
        if any(hint in f.path.lower().split("/")[-1] for hint in ARCHITECTURE_HINTS)
    ]

    # Spread remaining budget across shallow, structurally significant files
    # rather than dumping everything from one deep subfolder
    others = sorted(
        (f for f in files if f not in anchors),
        key=lambda f: (f.path.count("/"), f.path),
    )

    return anchors + others


async def _build_context(repository: Repository, files: list[File], max_chars: int) -> str:
    parts = []
    total = 0

    for file in files:
        content = _read_file_content(repository, file)
        if content is None:
            continue

        block = f"--- {file.path} ---\n{content[:3000]}\n"
        if total + len(block) > max_chars:
            break

        parts.append(block)
        total += len(block)

    return "\n".join(parts)


async def _call_groq(system_prompt: str, user_content: str) -> str:
    if not settings.GROQ_API_KEY:
        raise DocGenError("GROQ_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(GROQ_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise DocGenError(f"Groq API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


async def _save_doc(db: AsyncSession, repository_id: int, doc_type: str, content: str) -> GeneratedDoc:
    result = await db.execute(
        select(GeneratedDoc).where(
            GeneratedDoc.repository_id == repository_id, GeneratedDoc.doc_type == doc_type
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.content = content
        doc = existing
    else:
        doc = GeneratedDoc(repository_id=repository_id, doc_type=doc_type, content=content)
        db.add(doc)

    await db.commit()
    await db.refresh(doc)
    return doc


async def generate_readme(db: AsyncSession, repository: Repository) -> GeneratedDoc:
    result = await db.execute(select(File).where(File.repository_id == repository.id))
    files = result.scalars().all()

    if not files:
        raise DocGenError("Repository has no processed files yet")

    selected = _select_readme_context_files(list(files))
    context = await _build_context(repository, selected, MAX_CONTEXT_CHARS)

    if not context:
        raise DocGenError("Could not read any file contents to generate documentation")

    user_content = f"Repository: {repository.owner}/{repository.name}\n\nFiles:\n\n{context}"
    content = await _call_groq(README_SYSTEM_PROMPT, user_content)

    return await _save_doc(db, repository.id, "readme", content)

async def generate_api_docs(db: AsyncSession, repository: Repository) -> GeneratedDoc:
    result = await db.execute(select(File).where(File.repository_id == repository.id))
    files = result.scalars().all()

    if not files:
        raise DocGenError("Repository has no processed files yet")

    selected = _select_api_context_files(repository, list(files))

    if not selected:
        raise DocGenError("No route/endpoint files were found in this repository")

    context = await _build_context(repository, selected, MAX_API_CONTEXT_CHARS)

    if not context:
        raise DocGenError("Could not read any file contents to generate documentation")

    user_content = f"Repository: {repository.owner}/{repository.name}\n\nRoute/API files:\n\n{context}"
    content = await _call_groq(API_DOCS_SYSTEM_PROMPT, user_content)

    return await _save_doc(db, repository.id, "api_docs", content)


async def generate_architecture_doc(db: AsyncSession, repository: Repository) -> GeneratedDoc:
    result = await db.execute(select(File).where(File.repository_id == repository.id))
    files = result.scalars().all()

    if not files:
        raise DocGenError("Repository has no processed files yet")

    selected = _select_architecture_context_files(list(files))
    context = await _build_context(repository, selected, MAX_API_CONTEXT_CHARS)

    if not context:
        raise DocGenError("Could not read any file contents to generate documentation")

    user_content = f"Repository: {repository.owner}/{repository.name}\n\nFiles:\n\n{context}"
    content = await _call_groq(ARCHITECTURE_SYSTEM_PROMPT, user_content)

    return await _save_doc(db, repository.id, "architecture", content)