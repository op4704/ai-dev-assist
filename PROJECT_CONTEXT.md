# PROJECT CONTEXT

## 1. Project Overview

- **Project name:** AI Developer Assistant
- **Main goal:** AI-powered repository analysis platform — import a GitHub repo, chat with it, generate documentation, scan for security issues, review code quality, visualize architecture. Lightweight Cody/Cursor-style tool focused on repository understanding.
- **Problem being solved:** Give developers a $0-budget, low-end-hardware-friendly way to understand unfamiliar codebases using RAG + multi-agent LLM orchestration.
- **Current stage:** Phase 0 (Foundation) + Phase 1 (Repository Ingestion) backend complete and tested. Frontend scaffold in progress (SPA shell, CSS theme, API client done; page templates and app.js router not yet built).
- **Overall architecture:** Single-port full-stack app. FastAPI serves both the JSON API (under `/api/*`) and the static frontend (StaticFiles mount at `/`) — no separate frontend server, no CORS complexity in production. Vanilla HTML/CSS/JS frontend (no build step, no React) using a template-swappable structure so UI can be replaced without touching logic.

---

## 2. Current Progress

**Backend — done and tested:**
- Full async FastAPI app, 7 SQLAlchemy ORM models, SQLite (dev) / Postgres (prod) via one `DATABASE_URL`.
- Phase 1 ingestion pipeline: clone GitHub repo → filter/walk files → store metadata. 4 endpoints, all under `/api` prefix.
- 5 integration tests, all passing, run against real GitHub repo (`octocat/Spoon-Knife`).
- App serves BOTH the API (`/api/*`) and the frontend (`/`) on one port via `StaticFiles(html=True)`.

**Frontend — DONE (Phase 1 UI complete):**
- `frontend/index.html` — SPA shell.
- `frontend/css/style.css` — full theme, terminal-inspired dark UI, all colors/fonts/spacing as CSS variables in `:root`.
- `frontend/js/api/client.js` — the ONLY file that calls the backend.
- `frontend/js/app.js` — hash-based router (`#/`, `#/import`, `#/repo/:id`), mounts sidebar/topbar/page content.
- `frontend/js/templates/sidebar.js`, `topbar.js`, `components.js` — reusable UI pieces (nav, breadcrumbs, badges, empty states, banners, formatters, XSS-safe `esc()`).
- `frontend/js/pages/dashboard.js` — stat grid + repository list, route `#/`.
- `frontend/js/pages/import.js` — GitHub URL form with live step-by-step import→process progress UI, route `#/import`.
- `frontend/js/pages/repoDetail.js` — file explorer grouped by language, route `#/repo/:id`.
- `frontend/TEMPLATES.md` — guide explaining exactly which file to edit for any kind of UI change (theme/component/page/new-route).
- **Verified:** all JS syntax-checked with `node --check`; template functions executed in Node with a DOM shim to catch runtime errors; full manual curl walkthrough of the exact import→process→list→files sequence the UI performs, confirming response shapes match what the JS expects.

**Not started:** Phases 2–10 (RAG, chat, docs gen, security scanner, code review, architecture agent, LangGraph multi-agent orchestration, deployment).

---

## 3. Files Created / Modified

### Backend

| File | Purpose | Key contents |
|---|---|---|
| `backend/app/main.py` | FastAPI entrypoint | `lifespan()` creates tables; routes mounted under `/api`; `docs_url="/api/docs"`; StaticFiles mounted at `/` LAST (order matters — catch-all); global exception handler |
| `backend/app/core/config.py` | Settings | `Settings` (pydantic-settings, reads `.env`); `allowed_origins` is a **plain str** + `.allowed_origins_list` property (NOT `list[str]` — see bug history) |
| `backend/app/core/limiter.py` | Rate limiting | `limiter = Limiter(key_func=get_remote_address)` — separate module to avoid circular imports |
| `backend/app/database/base.py` | ORM base | `Base(DeclarativeBase)` |
| `backend/app/database/session.py` | DB engine/session | `engine`, `AsyncSessionLocal`, `get_db()` dep; SQLite FK pragma listener |
| `backend/app/models/user.py` | User table | `User` — stub auth, single demo user |
| `backend/app/models/repository.py` | Repository table | `Repository`, `RepositoryStatus` enum (PENDING/CLONING/PROCESSING/READY/FAILED); unique `(user_id, github_url)` |
| `backend/app/models/file.py` | File table | `File` — metadata only, no content stored; unique `(repository_id, path)` |
| `backend/app/models/chunk.py` | Chunk table | `Chunk` — schema ready, empty until Phase 2 |
| `backend/app/models/embedding_metadata.py` | Vector pointer table | `EmbeddingMetadata` — stores Pinecone `vector_id` only, not the vector itself |
| `backend/app/models/chat.py` | Chat tables | `ChatSession`, `ChatMessage` — empty until Phase 3 |
| `backend/app/models/agent_log.py` | Agent observability | `AgentLog` — empty until Phase 8; `session_id` FK is `SET NULL` not `CASCADE` (preserve audit trail) |
| `backend/app/models/__init__.py` | Registers all models on `Base.metadata` | Must be imported in `main.py` even though unused directly |
| `backend/app/schemas/repository.py` | Pydantic I/O schemas | `RepositoryImportRequest` (validates GitHub URL by **parsed hostname**, not regex — SSRF defense), `RepositoryProcessRequest`, `RepositoryResponse`, `FileResponse` |
| `backend/app/services/github_service.py` | Clone logic | `clone_repository()` (shallow clone, depth=1, size-limit enforced), `parse_github_url()`, `GitHubServiceError` |
| `backend/app/services/file_filter_service.py` | File walk/filter | `walk_and_filter()`, `ParsedFile` dataclass; ignores `node_modules/venv/.git/build/dist/__pycache__`; skips symlinks, binaries, oversized files; SHA-256 content hash |
| `backend/app/api/deps.py` | Shared deps | `get_current_user_id()` — auto-creates single demo user (`demo@local.dev`); real auth NOT implemented |
| `backend/app/api/routes/repository.py` | Ingestion endpoints | `router` (prefix `/repository`) + `repositories_router` (bare `/repositories`); both mounted with `/api` prefix in `main.py` |
| `backend/tests/test_repository_ingestion.py` | Integration tests | 5 tests, real network calls to GitHub, uses `pytest_asyncio.fixture` + `app.router.lifespan_context(app)` |
| `backend/requirements.txt` | Deps | fastapi, uvicorn[standard], sqlalchemy[asyncio], aiosqlite, asyncpg, pydantic, pydantic-settings, python-dotenv, GitPython, httpx, slowapi, pytest, pytest-asyncio |
| `backend/.env` | Working dev config | SQLite, all AI API keys blank (Phase 2+), `ALLOWED_ORIGINS=http://localhost:8000` |

### Frontend

| File | Purpose | Status |
|---|---|---|
| `frontend/index.html` | SPA shell | Done — mounts `#sidebar`, `#topbar`, `#content`; loads `js/app.js` as module |
| `frontend/css/style.css` | Theme/styling | Done — terminal dark theme, amber accent, ALL values as CSS vars at top (`:root`), sharp edges (`--radius: 0px`) |
| `frontend/js/api/client.js` | API wrapper | Done — `api.getRepositories()`, `api.importRepository(url)`, `api.processRepository(id)`, `api.getFiles(id)`; base path `const API = '/api'` |
| `frontend/js/app.js` | Router/mount | **NOT YET CREATED** |
| `frontend/js/templates/*.js` | Sidebar/topbar/component templates | **NOT YET CREATED** |
| `frontend/js/pages/*.js` | Page logic (Dashboard, Import, RepoList, FileExplorer) | **NOT YET CREATED** |
| `frontend/TEMPLATES.md` | Guide for swapping UI | **NOT YET CREATED** (referenced in index.html comment) |

### Docs (from earlier session — may need regeneration if sandbox reset wiped them)
`README.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, `docs/API_REFERENCE.md`, `docs/ROADMAP.md`, `docs/DEVELOPMENT_PLAN.md` — written previously; **not yet re-verified to exist after sandbox reset** (see §10 bugs).

---

## 4. Folder Structure

```
ai-dev-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          (config.py, limiter.py)
│   │   ├── database/      (base.py, session.py)
│   │   ├── models/        (7 model files + __init__.py)
│   │   ├── schemas/       (repository.py)
│   │   ├── services/      (github_service.py, file_filter_service.py)
│   │   └── api/
│   │       ├── deps.py
│   │       └── routes/    (repository.py)
│   ├── tests/              (test_repository_ingestion.py)
│   ├── storage/repositories/  (cloned repos land here, gitignored)
│   ├── requirements.txt
│   └── .env / .env.example
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js              ← TODO
│       ├── api/client.js
│       ├── templates/          ← TODO (sidebar.js, topbar.js, etc.)
│       └── pages/              ← TODO (dashboard.js, import.js, repoList.js, fileExplorer.js)
├── docs/                    (ARCHITECTURE.md, DATABASE_SCHEMA.md, API_REFERENCE.md, ROADMAP.md, DEVELOPMENT_PLAN.md)
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 5. Current State

### Working
- All backend Phase 0 + Phase 1 endpoints, verified via pytest (5/5 passing) and manual httpx smoke tests.
- Repository clone → filter → store pipeline against real GitHub repos.
- SQLite dev DB auto-created via lifespan startup.
- OpenAPI schema correctly shows all routes under `/api/*`.
- CSS theme file complete and self-contained.
- API client (`client.js`) complete, matches backend `/api` routes exactly.

### Partially Working
- Frontend SPA shell exists (`index.html`) but has no router/page logic wired up yet — will show blank loading screen only, nothing renders.

### Broken
- Nothing currently known to be broken in existing (backend) code.
- **Environment instability:** the build sandbox has reset at least once mid-project, wiping the filesystem (`/home/claude/ai-dev-assistant` was found empty even though earlier turns showed full backend files created and tested). All backend files were rebuilt from scratch after this and re-verified. **If starting a new session, verify the filesystem state before assuming any file exists** — re-check with `find`/`ls` first.

---

## 6. Current Task

Phase 1 (backend + frontend) is complete. No active task in progress — ready to start Phase 2 (RAG pipeline) or address remaining TODOs below.

---

## 7. Remaining TODOs

**High Priority**
- Phase 2: RAG pipeline (chunking, Jina embeddings, Pinecone) — needs free API keys from user first
- Full manual browser test (this sandbox has no browser — only curl/node verification done so far)

**Medium Priority**
- Add Alembic migrations before schema changes further (still using `Base.metadata.create_all()`)
- Background task queue for cloning (currently blocks request thread)

**Low Priority**
- Real auth (JWT/OAuth) to replace stub demo user
- Move repo storage off local disk to S3-compatible object storage for production
- Docker Dockerfile/compose files are untested (no Docker daemon in this sandbox) — verify locally

---

## 8. Decisions Already Made

| Decision | Why |
|---|---|
| **Single port, FastAPI serves frontend via StaticFiles** | User explicitly asked to avoid separate ports/CORS complexity; `app.mount("/", StaticFiles(...), html=True)` mounted LAST so it acts as catch-all without shadowing `/api/*` |
| **All backend routes under `/api` prefix** | Required to cleanly separate API from static frontend files on the same port |
| **Vanilla HTML/CSS/JS frontend, no React, no build step** | User wants to swap "templates" (plain files) to change UI without a build pipeline |
| **CSS variables for all theme values in `:root`** | Enables full re-theme by editing/replacing one file (`style.css`) without touching JS |
| **`js/api/client.js` is the only file allowed to call `fetch()`** | Keeps API contract in one place; page/template files never hardcode endpoint URLs |
| **Async SQLAlchemy 2.0** | FastAPI is async-native; avoids blocking event loop |
| **SQLite (dev) / Postgres (prod) via one `DATABASE_URL`** | Zero-setup local dev, same code path to production |
| **`Base.metadata.create_all()` instead of Alembic (for now)** | Schema still changing per-phase; will switch to Alembic once stable or before first real deploy |
| **Repository `status` stored as plain string, not native Postgres ENUM** | Easier to evolve/add values later; behaves identically on SQLite and Postgres |
| **GitHub URL validated by `urlparse().hostname` exact match, not regex** | Prevents SSRF bypass patterns like `github.com.evil.com` |
| **Shallow clone (`depth=1`)** | Only current file state needed; faster, smaller, fits low-end hardware constraint |
| **Auth stubbed with single demo user** | Real auth wasn't an explicit phase; schema already supports multi-tenancy for later |
| **`allowed_origins` stored as plain `str` + property, not `list[str]`** | `pydantic-settings` JSON-decodes list-typed env vars before validators run — breaks on plain comma-separated strings |
| **`agent_logs.session_id` FK is `ON DELETE SET NULL`, not `CASCADE`** | Preserve audit trail even if the chat session is deleted |
| **No local LLMs, no GPU dependency, $0 budget** | User's explicit hardware (i7-1255U, 16GB RAM, no dGPU) and budget constraints |

---

## 9. Important Context

- **Hardware constraint:** i7-1255U, 16GB RAM, Intel Iris Xe (no dedicated GPU) — no local LLM inference.
- **Budget constraint:** $0 — free tiers only (Gemini API, Pinecone free tier, Jina Embeddings free tier, PostgreSQL local, GitHub public repos).
- **Python version:** 3.12.3 (confirmed in sandbox)
- **Key package versions confirmed installed:** SQLAlchemy 2.0.51, greenlet 3.3.2
- **Planned AI providers (Phase 2+, not yet integrated):** Gemini API (LLM), Jina Embeddings (embeddings), Pinecone (vector DB)
- **Test repo used for integration tests:** `https://github.com/octocat/Spoon-Knife` (has exactly 3 supported files: README.md, index.html, styles.css — do NOT use `octocat/Hello-World`, it has only one extensionless file and yields 0 matches, which looks like a bug but isn't)
- **Sandbox/environment instability:** filesystem has been observed to reset between turns at least once. Always verify file existence before assuming prior work persisted.

---

## 10. Known Bugs

| Bug | Cause | Status |
|---|---|---|
| `pydantic-settings` JSONDecodeError on `allowed_origins` | `list[str]` settings field attempts JSON-decode of raw env var before custom validators run; plain comma-separated string fails | **Fixed** — changed field to plain `str` + `.allowed_origins_list` property |
| `httpx.AsyncClient` + `ASGITransport` never runs FastAPI lifespan | Known httpx/ASGI transport limitation — startup hook (`create_all`) never fires, causing "no such table" errors | **Fixed** — tests explicitly wrap calls in `async with app.router.lifespan_context(app):` |
| Manual smoke test against `octocat/Hello-World` returned 0 files | Not a bug — that repo genuinely has only one extensionless README file; file filter correctly excluded it | **Resolved** — switched test fixture repo to `octocat/Spoon-Knife` |
| Sandbox filesystem reset mid-project | Unknown cause (environment/session boundary) — all previously created files vanished | **Worked around** — backend fully rebuilt and re-verified; frontend build proceeding fresh. **Not fixed at the root cause; may recur.** |

---

## 11. Commands

```bash
# Install backend deps
cd backend && pip install -r requirements.txt --break-system-packages

# Run dev server (serves API + frontend on same port)
cd backend && uvicorn app.main:app --reload
# → http://localhost:8000        (frontend)
# → http://localhost:8000/api/*  (API)
# → http://localhost:8000/api/docs (Swagger)

# Run tests
cd backend && pytest tests/ -v

# Reset local dev DB between manual test runs
rm -f backend/dev.db

# (Untested in this sandbox — no Docker daemon available) Postgres via Docker
docker compose up
```

---

## 12. Variables

**Environment variables** (`backend/.env`):
- `APP_NAME`
- `ENVIRONMENT`
- `SECRET_KEY`
- `DATABASE_URL`
- `REPO_STORAGE_PATH`
- `MAX_REPO_SIZE_MB`
- `RATE_LIMIT_IMPORT`
- `GEMINI_API_KEY` (blank — Phase 2)
- `JINA_API_KEY` (blank — Phase 2)
- `PINECONE_API_KEY` (blank — Phase 2)
- `PINECONE_ENVIRONMENT` (blank — Phase 2)
- `PINECONE_INDEX_NAME`
- `ALLOWED_ORIGINS`

**Ports:**
- `8000` — single port for both API and frontend (dev: `uvicorn ... --reload`, default port)

**Paths:**
- `backend/storage/repositories/` — cloned repo storage (gitignored)
- `backend/dev.db` — SQLite dev database (gitignored)
- `frontend/` — served as static root at `/`

**URL prefixes:**
- `/api/*` — all backend REST endpoints
- `/api/docs`, `/api/redoc`, `/api/openapi.json` — API docs (moved from root to avoid clashing with frontend)
- `/` — frontend SPA (StaticFiles, `html=True` fallback to `index.html`)

---

## 13. Next Immediate Step

Create `frontend/js/app.js` — a minimal hash-based router that:
1. Renders the sidebar (via `js/templates/sidebar.js`, not yet created) and topbar into `#sidebar`/`#topbar`.
2. Listens to `hashchange`/`load`, matches routes (`#/`, `#/import`, `#/repo/:id`), and mounts the matching page module's `render()` into `#content`.
3. Then build `js/templates/sidebar.js` and `js/templates/topbar.js`, then the four page modules under `js/pages/`, in that order, so each layer can be tested as soon as its dependency exists.

---

## 14. Session Summary

- Rebuilt entire backend from scratch after sandbox filesystem reset wiped prior work; re-verified all 5 integration tests pass against real GitHub repo.
- Restructured backend routing: all API endpoints moved under `/api` prefix; docs moved to `/api/docs`.
- Updated `main.py` to mount frontend via `StaticFiles(html=True)` at `/`, enabling single-port full-stack serving (user's explicit request — no separate frontend port, no CORS friction).
- Rewrote `tests/test_repository_ingestion.py` to match new `/api` route prefix — all 5 tests still passing.
- Designed frontend for template-swappability per user's explicit request: CSS theme fully isolated in `style.css` via CSS variables; API calls fully isolated in `js/api/client.js`; page/component rendering to be isolated in `js/templates/` and `js/pages/`.
- Built `frontend/index.html` (SPA shell), `frontend/css/style.css` (full terminal-dark theme), `frontend/js/api/client.js` (API wrapper matching all 4 backend endpoints).
- Frontend router (`app.js`) and all page/template modules still outstanding — explicitly scoped as the next step.

---

## 15. Things NOT To Change

- Do not reintroduce a separate frontend dev server/port — single-port serving via FastAPI `StaticFiles` is an explicit user requirement.
- Do not move API routes out from under the `/api` prefix.
- Do not put `fetch()` calls anywhere outside `frontend/js/api/client.js`.
- Do not hardcode colors/fonts/spacing in JS or HTML — always reference CSS variables defined in `style.css`.
- Do not switch the frontend to React or add a JS build step — vanilla HTML/CSS/JS by explicit user choice.
- Do not remove the `app.mount("/", StaticFiles(...))` line's position at the END of `main.py` — it must be registered after all `/api` routes or it will shadow them.
- Do not change `RepositoryStatus` to a native Postgres ENUM.
- Do not replace the GitHub URL regex-based validation with a permissive regex — must remain exact hostname match via `urlparse()`.
- Do not use `octocat/Hello-World` as a test fixture repo (single extensionless file, not useful for filter testing) — use `octocat/Spoon-Knife`.

---

## 16. AI Instructions

- Always verify file/folder existence on disk before assuming prior session's work persisted (sandbox has reset before).
- Follow existing code style: async/await throughout backend, type hints on all function signatures, docstrings/comments explaining *why* not *what* for non-obvious decisions.
- Every new backend feature should get a real integration test (network calls against real GitHub repos where relevant), not mocked-only tests, consistent with Phase 1's testing approach.
- Frontend: keep the three-layer separation strict — `api/` (data), `templates/` (reusable UI pieces), `pages/` (route-level composition). Never blend concerns across these folders.
- Do not fabricate documentation of features that haven't been built — mark clearly as TODO/planned, consistent with how Phases 2–10 have been documented so far (scoped, not stubbed).
- When resuming work, re-run `pytest tests/ -v` before adding new backend code to confirm the baseline still passes.
- Keep responses focused on the current task; don't re-explain finished/tested phases unless asked.

---

## 17. Project History

**Version 0.1**
- Backend foundation: FastAPI app, 7 SQLAlchemy models, async DB session, settings, rate limiter.

**Version 0.2**
- Phase 1 repository ingestion complete: clone/filter/store pipeline, 4 endpoints, 5 passing integration tests against real GitHub repos.
- Full docs written: ARCHITECTURE.md, DATABASE_SCHEMA.md, API_REFERENCE.md, ROADMAP.md, DEVELOPMENT_PLAN.md, README.md.

**Version 0.3**
- Sandbox filesystem reset; backend fully rebuilt from scratch and re-verified (5/5 tests passing).
- Architecture change: all API routes moved under `/api` prefix; frontend now served by FastAPI via `StaticFiles` at `/` on the same port (single-port full-stack app, no CORS needed in practice).
- Frontend build started: `index.html`, `css/style.css` (full theme), `js/api/client.js` complete. Router and page templates outstanding.

---

## 18. Last Updated

- **Date:** Current session (date not tracked by system)
- **Session Number:** 3 (post-reset rebuild + frontend start)
- **Latest milestone:** Backend Phase 0+1 rebuilt and verified after sandbox reset; frontend SPA shell + theme + API client complete; router and page templates are the next build step.
