import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.models  # noqa: F401 — registers all models on Base.metadata

from app.api.routes.rag import router as rag_router
from app.api.routes.repository import repositories_router, router as repository_router

from app.core.config import settings
from app.core.limiter import limiter
from app.database.base import Base
from app.database.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the frontend directory (sibling of the backend/ folder)
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB ready (%s)", settings.database_url.split("://")[0])
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})



# ── API routes (all under /api) ──────────────────────────────────────────────
app.include_router(repository_router, prefix="/api")
app.include_router(repositories_router, prefix="/api")
app.include_router(rag_router, prefix="/api")

@app.get("/api/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


# ── Frontend (MUST be last — catches everything not matched above) ────────────
# When the frontend directory exists, FastAPI serves it at /.
# html=True means any path that doesn't match a static file returns index.html
# — this is what makes the SPA's client-side router work on page refresh.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
