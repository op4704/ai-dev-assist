from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models import GeneratedDoc, Repository
from app.schemas.docs import GeneratedDocResponse
from app.services.doc_generator_service import DocGenError, generate_api_docs, generate_architecture_doc, generate_readme

router = APIRouter(prefix="/repository", tags=["docs"])


async def _get_repo(db: AsyncSession, repo_id: int, user_id: int) -> Repository:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.post("/{repository_id}/docs/readme", response_model=GeneratedDocResponse)
async def generate_readme_doc(
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
        doc = await generate_readme(db, repo)
    except DocGenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Doc generation failed: {exc}") from exc

    return doc

@router.post("/{repository_id}/docs/api", response_model=GeneratedDocResponse)
async def generate_api_docs_route(
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
        doc = await generate_api_docs(db, repo)
    except DocGenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Doc generation failed: {exc}") from exc

    return doc


@router.post("/{repository_id}/docs/architecture", response_model=GeneratedDocResponse)
async def generate_architecture_doc_route(
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
        doc = await generate_architecture_doc(db, repo)
    except DocGenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Doc generation failed: {exc}") from exc

    return doc


@router.get("/{repository_id}/docs/{doc_type}", response_model=GeneratedDocResponse)
async def get_generated_doc(
    repository_id: int,
    doc_type: str,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    repo = await _get_repo(db, repository_id, user_id)

    result = await db.execute(
        select(GeneratedDoc).where(
            GeneratedDoc.repository_id == repo.id, GeneratedDoc.doc_type == doc_type
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"No {doc_type} has been generated yet for this repository.")

    return doc
