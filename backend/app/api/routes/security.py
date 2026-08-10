from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models import File, Repository, SecurityFinding
from app.schemas.security import FindingWithPathResponse, ScanResponse
from app.services.security_scan_service import ScanError, scan_repository

router = APIRouter(prefix="/repository", tags=["security"])


async def _get_repo(db: AsyncSession, repo_id: int, user_id: int) -> Repository:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.post("/{repository_id}/scan", response_model=ScanResponse)
async def scan_repo(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    repo = await _get_repo(db, repository_id, user_id)

    if repo.total_files == 0:
        raise HTTPException(
            status_code=400,
            detail="Repository has no processed files yet. Call /api/repository/process first.",
        )

    try:
        result = await scan_repository(db, repo)
    except ScanError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc

    return result


@router.get("/{repository_id}/findings", response_model=list[FindingWithPathResponse])
async def list_findings(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    repo = await _get_repo(db, repository_id, user_id)

    result = await db.execute(
        select(SecurityFinding, File.path)
        .join(File, File.id == SecurityFinding.file_id)
        .where(SecurityFinding.repository_id == repo.id)
        .order_by(SecurityFinding.severity, SecurityFinding.created_at)
    )
    rows = result.all()

    return [
        FindingWithPathResponse(
            id=finding.id,
            file_id=finding.file_id,
            severity=finding.severity,
            category=finding.category,
            title=finding.title,
            description=finding.description,
            line_number=finding.line_number,
            matched_snippet=finding.matched_snippet,
            created_at=finding.created_at,
            file_path=path,
        )
        for finding, path in rows
    ]