import os
import shutil
import stat
import time
from pathlib import Path
from urllib.parse import urlparse
import git
from app.core.config import settings


class GitHubServiceError(Exception):
    pass


def _force_remove_readonly(func, path, exc_info):
    """
    shutil.rmtree error handler for Windows.
    Git marks files under .git/objects/pack/ as read-only. On Linux/Mac,
    shutil.rmtree deletes them without complaint since the owner can still
    unlink a read-only file. On Windows, the read-only attribute blocks
    deletion outright and rmtree raises PermissionError ([WinError 5]) instead
    of silently succeeding. This handler clears the read-only bit and retries
    the failed operation, which is the standard workaround for this exact
    cross-platform gap.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _safe_rmtree(path: Path, retries: int = 5, delay_seconds: float = 0.5) -> None:
    """
    Deletes a directory tree, retrying on Windows file locks.

    Beyond the read-only issue handled above, Windows can also raise
    WinError 32 ("used by another process") for a newly-cloned file that's
    momentarily held open by something else on the machine — most commonly
    antivirus real-time scanning or the Search Indexer reacting to the
    thousands of new files a large clone just created. This is a timing
    race, not a permanent lock, so a short retry-with-backoff resolves it
    without needing the user to disable any OS-level scanning.
    """
    last_error: OSError | None = None
    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=_force_remove_readonly)
            return
        except OSError as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay_seconds * (attempt + 1))
    raise GitHubServiceError(
        "Could not clean up a previous copy of this repository because a file was "
        "locked by another process (often antivirus or search indexing). "
        "Please close any programs that might have the storage folder open and try again."
    ) from last_error


def parse_github_url(github_url: str) -> tuple[str, str]:
    parsed = urlparse(github_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise GitHubServiceError(f"Cannot parse owner/repo from: {github_url}")
    return parts[0], parts[1].removesuffix(".git")


def clone_repository(github_url: str, repository_id: int) -> tuple[Path, str]:
    owner, repo_name = parse_github_url(github_url)
    storage_root = Path(settings.repo_storage_path)
    storage_root.mkdir(parents=True, exist_ok=True)
    destination = storage_root / f"{repository_id}_{owner}_{repo_name}"
    if destination.exists():
        _safe_rmtree(destination)
    try:
        cloned = git.Repo.clone_from(github_url, destination, depth=1, single_branch=True)
    except git.exc.GitCommandError as exc:
        raise GitHubServiceError("Failed to clone. Repository may be private, deleted, or the URL is incorrect.") from exc
    try:
        branch = cloned.active_branch.name
    except TypeError:
        branch = "main"
    total = sum(f.stat().st_size for f in destination.rglob("*") if f.is_file())
    if total > settings.max_repo_size_mb * 1024 * 1024:
        _safe_rmtree(destination)
        raise GitHubServiceError(f"Repository exceeds {settings.max_repo_size_mb}MB limit.")
    return destination, branch