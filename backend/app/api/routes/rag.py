from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models import Repository
from app.schemas.rag import ChatRequest, ChatResponse, IndexResponse
from app.services.rag_service import RagError, chat_with_repository, index_repository

router = APIRouter(prefix="/repository", tags=["rag"])


async def _get_repo(db: AsyncSession, repo_id: int, user_id: int) -> Repository:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.post("/{repository_id}/index", response_model=IndexResponse)
async def index_repo(
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
        result = await index_repository(db, repo)
    except RagError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {exc}") from exc

    return result


@router.post("/{repository_id}/chat", response_model=ChatResponse)
async def chat(
    repository_id: int,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    repo = await _get_repo(db, repository_id, user_id)

    try:
        result = await chat_with_repository(
            db, repo, payload.question, session_id=payload.session_id
        )
    except RagError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc

    return result