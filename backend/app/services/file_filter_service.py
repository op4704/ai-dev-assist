import hashlib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".html": "html",
    ".css": "css", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
}
IGNORED_DIRS: set[str] = {"node_modules", "venv", ".venv", ".git", "build", "dist", "__pycache__", ".next", ".pytest_cache"}
MAX_FILE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class ParsedFile:
    relative_path: str
    language: str
    size_bytes: int
    content_hash: str


def walk_and_filter(repo_root: Path) -> list[ParsedFile]:
    results = []
    for path in sorted(repo_root.rglob("*")):
        parts = path.relative_to(repo_root).parts
        if any(p in IGNORED_DIRS for p in parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        results.append(ParsedFile(
            relative_path=str(path.relative_to(repo_root)),
            language=SUPPORTED_EXTENSIONS[path.suffix.lower()],
            size_bytes=size,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        ))
    return results
