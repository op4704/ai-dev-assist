from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user_id
from app.core.limiter import limiter
from app.core.config import settings
from app.database.session import get_db
from app.models import File as FileModel, Repository, RepositoryStatus
from app.schemas.repository import FileResponse, RepositoryImportRequest, RepositoryProcessRequest, RepositoryResponse
from app.services.file_filter_service import walk_and_filter
from app.services.github_service import GitHubServiceError, clone_repository, parse_github_url
from app.services.repository_delete_service import delete_repository

router = APIRouter(prefix="/repository", tags=["repository"])
repositories_router = APIRouter(tags=["repository"])


@router.post("/import", response_model=RepositoryResponse, status_code=201)
@limiter.limit(settings.rate_limit_import)
async def import_repository(request: Request, payload: RepositoryImportRequest, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    owner, repo_name = parse_github_url(payload.github_url)
    existing = await db.execute(select(Repository).where(Repository.github_url == payload.github_url, Repository.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already imported.")
    repo = Repository(user_id=user_id, github_url=payload.github_url, owner=owner, name=repo_name, status=RepositoryStatus.PENDING)
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    try:
        repo.status = RepositoryStatus.CLONING
        await db.commit()
        local_path, branch = clone_repository(payload.github_url, repo.id)
        repo.local_path = str(local_path)
        repo.default_branch = branch
        repo.status = RepositoryStatus.PENDING
        await db.commit()
        await db.refresh(repo)
    except GitHubServiceError as exc:
        repo.status = RepositoryStatus.FAILED
        repo.error_message = str(exc)
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return repo


@router.post("/process", response_model=RepositoryResponse)
async def process_repository(payload: RepositoryProcessRequest, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    repo = await _get_repo(db, payload.repository_id, user_id)
    if not repo.local_path:
        raise HTTPException(status_code=400, detail="Repository not cloned yet. Call /api/repository/import first.")
    repo.status = RepositoryStatus.PROCESSING
    await db.commit()
    try:
        files = walk_and_filter(Path(repo.local_path))
        await db.execute(delete(FileModel).where(FileModel.repository_id == repo.id))
        for f in files:
            db.add(FileModel(repository_id=repo.id, path=f.relative_path, language=f.language, size_bytes=f.size_bytes, content_hash=f.content_hash))
        repo.total_files = len(files)
        repo.status = RepositoryStatus.READY
        await db.commit()
        await db.refresh(repo)
    except Exception as exc:
        repo.status = RepositoryStatus.FAILED
        repo.error_message = str(exc)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc
    return repo

@router.delete("/{repository_id}", status_code=204)
async def delete_repository_route(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    repo = await _get_repo(db, repository_id, user_id)

    try:
        await delete_repository(db, repo)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc


@router.get("/{repository_id}/files", response_model=list[FileResponse])
async def list_files(repository_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    repo = await _get_repo(db, repository_id, user_id)
    result = await db.execute(select(FileModel).where(FileModel.repository_id == repo.id).order_by(FileModel.path))
    return list(result.scalars().all())


@repositories_router.get("/repositories", response_model=list[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    result = await db.execute(select(Repository).where(Repository.user_id == user_id).order_by(Repository.created_at.desc()))
    return list(result.scalars().all())


async def _get_repo(db: AsyncSession, repo_id: int, user_id: int) -> Repository:
    result = await db.execute(select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo
