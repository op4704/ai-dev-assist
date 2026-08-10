"""
Orchestrates security scanning: reads files from disk, runs pattern
detection, and persists findings to the database.
"""
import os

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File, Repository, SecurityFinding
from app.services.security_scanner_service import scan_content


class ScanError(Exception):
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


async def scan_repository(db: AsyncSession, repository: Repository) -> dict:
    """
    Scans every file in the repository for security issues.
    Clears any previous findings for this repository first (so re-scanning
    doesn't duplicate old results).
    """
    result = await db.execute(select(File).where(File.repository_id == repository.id))
    files = result.scalars().all()

    if not files:
        raise ScanError("Repository has no processed files yet")

    # Clear previous findings for a clean re-scan
    await db.execute(delete(SecurityFinding).where(SecurityFinding.repository_id == repository.id))

    total_findings = 0
    files_scanned = 0
    files_skipped = 0
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for file in files:
        content = _read_file_content(repository, file)
        if content is None:
            files_skipped += 1
            continue

        files_scanned += 1
        findings = scan_content(file.path, content)

        for finding in findings:
            db.add(
                SecurityFinding(
                    repository_id=repository.id,
                    file_id=file.id,
                    severity=finding.severity,
                    category=finding.category,
                    title=finding.title,
                    description=finding.description,
                    line_number=finding.line_number,
                    matched_snippet=finding.matched_snippet,
                )
            )
            severity_counts[finding.severity] += 1
            total_findings += 1

    await db.commit()

    return {
        "files_scanned": files_scanned,
        "files_skipped": files_skipped,
        "total_findings": total_findings,
        "critical_count": severity_counts["critical"],
        "high_count": severity_counts["high"],
        "medium_count": severity_counts["medium"],
        "low_count": severity_counts["low"],
    }