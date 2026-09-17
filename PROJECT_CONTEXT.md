# PROJECT CONTEXT

## 1. Project Overview

- **Project name:** AI Developer Assistant (branded "Phoenix" on the landing page)
- **Main goal:** AI-powered repository analysis platform — import a GitHub repo, chat with it (RAG), generate documentation, scan for security issues. Lightweight Cody/Cursor-style tool focused on repository understanding.
- **Problem being solved:** Give developers a $0-budget, low-end-hardware-friendly way to understand unfamiliar codebases using RAG + LLM orchestration.
- **Current stage:** Backend Phases 0–5 (foundation, ingestion, RAG/chat, security scan, doc generation) are built and wired to real endpoints. Frontend (landing page + SPA app) is built and served. Verified booting locally, all tests passing, all JS syntax-clean. See §5 for what's real vs. what's still a TODO.
- **Overall architecture:** Single-port full-stack app. FastAPI serves both the JSON API (under `/api/*`) and the static frontend (`StaticFiles` mount at `/`) — no separate frontend server, no CORS complexity in production.
  - `/` → marketing landing page (`frontend/index.html`)
  - `/app/` → the actual SPA (`frontend/app/index.html`) — hash-router, dashboard/import/chat/repoDetail pages
  - `/api/*` → REST API
  - `/api/docs` → Swagger

---

## 2. Current Progress (re-audited this session — see §9 "Session Cleanup")

**Backend — built, tested, verified booting:**
- Full async FastAPI app, SQLAlchemy ORM models (User, Repository, File, Chunk, EmbeddingMetadata, ChatSession, ChatMessage, AgentLog, SecurityFinding, GeneratedDoc), SQLite (dev) / Postgres (prod) via one `DATABASE_URL`.
- **Repository ingestion** (`api/routes/repository.py`): import, process, list, list files, delete. 5 integration tests, all passing against real GitHub repo (`octocat/Spoon-Knife`).
- **RAG / chat** (`api/routes/rag.py`, `services/rag_service.py`, `chunking_service.py`, `embedding_service.py`, `vector_store_service.py`): `POST /{id}/index` (chunk + embed + upsert to Pinecone), `POST /{id}/chat` (retrieve + LLM answer). This is FURTHER ALONG than the previous checkpoint doc claimed — it is not a stub.
- **Security scanning** (`api/routes/security.py`): `POST /{id}/scan`, `GET /{id}/findings`. Split cleanly into `security_scanner_service.py` (pure regex/pattern detection, no DB, no AI — fast & deterministic) and `security_scan_service.py` (orchestrator: reads files from disk, calls the scanner, persists findings to DB). This is NOT duplicated logic — it's a legitimate separation of concerns.
- **Doc generation** (`api/routes/docs.py`, `services/doc_generator_service.py`, 290 lines): `POST /{id}/docs/readme`, `/docs/api`, `/docs/architecture`, `GET /{id}/docs/{doc_type}`.
- **LLM wrapper** (`services/llm_service.py`) — used by both RAG chat and doc generation.
- App serves the API (`/api/*`), the landing page (`/`), and the SPA (`/app/`) all on one port.
- **Verified this session:** fresh `pip install -r requirements.txt` succeeds; server boots clean (`uvicorn app.main:app`); `/api/health`, `/`, `/app/`, `/app/css/style.css`, `/app/js/app.js` all return 200; `pytest tests/ -v` → 5/5 passing; all backend `.py` files pass `py_compile`; all 10 frontend `.js` files pass `node --check`.

**Frontend — built, split into landing + app:**
- `frontend/index.html` + `frontend/css/style.css` + `frontend/js/phoenix-effect.js` — marketing landing page ("Phoenix — Your codebase, reborn as answers"), links to `/app/index.html` for the actual product.
- `frontend/app/index.html` — SPA shell.
- `frontend/app/css/style.css` — full theme, terminal-inspired dark UI, CSS variables in `:root`.
- `frontend/app/js/api/client.js` — the ONLY file that calls the backend; covers every route including chat (`api.sendChatMessage`), scan, findings, docs, delete.
- `frontend/app/js/app.js` — hash-based router.
- `frontend/app/js/templates/sidebar.js`, `topbar.js`, `components.js` — reusable UI pieces.
- `frontend/app/js/pages/dashboard.js`, `import.js`, `chatList.js`, `chat.js`, `repoDetail.js` — one file per route.
- `frontend/app/TEMPLATES.md` — guide for which file to edit for any UI change.

**Not started:** LangGraph multi-agent orchestration, real auth, architecture-visualization page (backend `docs/architecture` endpoint exists but no confirmed matching frontend page beyond generic doc rendering), production deployment hardening.

---

## 3. Folder Structure (current, post-cleanup)

```
ai-dev-assist/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            (config.py, limiter.py)
│   │   ├── database/        (base.py, session.py)
│   │   ├── models/          (10 model files + __init__.py)
│   │   ├── schemas/         (repository.py, rag.py, security.py, docs.py)
│   │   ├── services/        (github_service, file_filter_service, chunking_service,
│   │   │                      embedding_service, vector_store_service, rag_service,
│   │   │                      security_scanner_service, security_scan_service,
│   │   │                      doc_generator_service, llm_service, repository_delete_service)
│   │   └── api/
│   │       ├── deps.py
│   │       └── routes/      (repository.py, rag.py, security.py, docs.py)
│   ├── tests/                (test_repository_ingestion.py — 5 passing)
│   ├── test_chunking.py, test_scanner.py   (manual smoke scripts, not pytest)
│   ├── storage/repositories/  (cloned repos land here, gitignored)
│   ├── Dockerfile
│   ├── run.py                (alt entrypoint: python run.py — same as uvicorn --reload)
│   ├── requirements.txt
│   └── .env / .env.example
├── frontend/
│   ├── index.html            ← landing page
│   ├── css/style.css
│   ├── js/phoenix-effect.js
│   └── app/                  ← the actual SPA, served at /app/
│       ├── index.html
│       ├── css/style.css
│       ├── TEMPLATES.md
│       └── js/
│           ├── app.js
│           ├── api/client.js
│           ├── templates/    (sidebar.js, topbar.js, components.js)
│           └── pages/        (dashboard.js, import.js, chatList.js, chat.js, repoDetail.js)
├── docs/                     (ARCHITECTURE.md, DATABASE_SCHEMA.md, API_REFERENCE.md, ROADMAP.md, DEVELOPMENT_PLAN.md)
├── docker-compose.yml
├── .gitignore
└── README.md
```

**Note:** as of this session, duplicate/stale copies of the frontend that previously existed at repo root (`/index.html`, `/js/`, `/css/`) and in `/landing/` (byte-identical to `frontend/`) have been deleted, along with two stale zip archives (`frontend.zip`, `frontend/full-site.zip`). `frontend/` is now the single source of truth.

---

## 4. All API Endpoints (verified via `/api/openapi.json`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | health check |
| GET | `/api/repositories` | list user's repos |
| POST | `/api/repository/import` | clone + register a repo |
| POST | `/api/repository/process` | walk/filter/store file metadata |
| GET | `/api/repository/{id}` | (implicit, via delete/get helper) |
| DELETE | `/api/repository/{id}` | delete a repo |
| GET | `/api/repository/{id}/files` | list indexed files |
| POST | `/api/repository/{id}/index` | chunk + embed + upsert vectors |
| POST | `/api/repository/{id}/chat` | RAG chat — ask a question about the repo |
| POST | `/api/repository/{id}/scan` | run security scanner |
| GET | `/api/repository/{id}/findings` | list security findings |
| POST | `/api/repository/{id}/docs/readme` | generate README |
| POST | `/api/repository/{id}/docs/api` | generate API docs |
| POST | `/api/repository/{id}/docs/architecture` | generate architecture doc |
| GET | `/api/repository/{id}/docs/{doc_type}` | fetch a generated doc |

---

## 5. Current State

### Working (verified this session)
- Full backend boot + all routes registered correctly under `/api`.
- Repository clone → filter → store pipeline (real GitHub repos).
- 5/5 pytest integration tests passing.
- All backend `.py` files compile clean; all frontend `.js` files syntax-clean.
- Landing page (`/`) and SPA (`/app/`) both serve 200, CSS/JS load correctly.
- API client (`frontend/app/js/api/client.js`) matches every backend endpoint 1:1, including chat/scan/docs — this was NOT true of an older frontend copy that got deleted.

### Needs real-world verification (not yet tested end-to-end with actual keys)
- RAG chat: needs `GEMINI_API_KEY`, `JINA_API_KEY`, `PINECONE_API_KEY` populated in `backend/.env` to actually run (currently blank — free-tier signup still pending).
- Doc generation: needs `GEMINI_API_KEY`.
- Security scanner: regex-based, no API key needed — should work standalone; not yet click-tested through the browser UI.
- Full manual browser walkthrough of the SPA (import → chat → scan → docs) has not been done yet — only curl/API-level and syntax-level checks so far.

### Broken
- Nothing currently known to be broken in the code. (Previous "environment instability" notes from earlier sessions were sandbox-specific and don't apply to this local Windows dev setup.)

---

## 6. Current Task

Session cleanup complete (see §9). Next: get free-tier API keys (Gemini, Jina, Pinecone) into `backend/.env` and do a full manual browser walkthrough of the real user flow: import repo → index → chat → scan → generate docs.

---

## 7. Remaining TODOs

**High Priority**
- Populate `backend/.env` with real free-tier keys (Gemini, Jina, Pinecone) and do an end-to-end manual browser test of every feature.
- Confirm `/{id}/docs/architecture` has a frontend page to render it (or decide it reuses a generic doc viewer).

**Medium Priority**
- Add Alembic migrations before schema changes further (still using `Base.metadata.create_all()`).
- Background task queue for cloning/indexing (currently blocks request thread).
- LangGraph multi-agent orchestration (not started).

**Low Priority**
- Real auth (JWT/OAuth) to replace stub demo user.
- Move repo storage off local disk to S3-compatible object storage for production.
- Docker Dockerfile/compose — exists but untested locally this session; verify with `docker compose up`.

---

## 8. Decisions Already Made

| Decision | Why |
|---|---|
| **Single port, FastAPI serves frontend via StaticFiles** | Avoids separate ports/CORS complexity. |
| **Landing page at `/`, SPA app at `/app/`** | Marketing site and product are separate concerns; both are static, both served by the same FastAPI static mount. |
| **All backend routes under `/api` prefix** | Cleanly separates API from static frontend files on the same port. |
| **Vanilla HTML/CSS/JS frontend, no React, no build step** | Swap "templates" (plain files) to change UI without a build pipeline. |
| **CSS variables for all theme values in `:root`** | Full re-theme by editing one file. |
| **`frontend/app/js/api/client.js` is the only file allowed to call `fetch()`** | Keeps API contract in one place. |
| **Async SQLAlchemy 2.0** | FastAPI is async-native. |
| **SQLite (dev) / Postgres (prod) via one `DATABASE_URL`** | Zero-setup local dev, same code path to production. |
| **`security_scanner_service.py` (pure detection) split from `security_scan_service.py` (DB orchestration)** | Detection logic is reusable/testable standalone (see `test_scanner.py`); orchestration owns DB/session concerns. |
| **GitHub URL validated by `urlparse().hostname` exact match, not regex** | Prevents SSRF bypass patterns like `github.com.evil.com`. |
| **Shallow clone (`depth=1`)** | Only current file state needed; faster, smaller. |
| **No local LLMs, no GPU dependency, $0 budget** | Hardware/budget constraint (i7-1255U, 16GB RAM, no dGPU). |

---

## 9. Session Cleanup (this session — full re-audit + fix pass)

Starting state when this session began: project had just been freshly cloned from GitHub (`op4704/ai-dev-assist`) and had NOT been booted or verified locally yet.

**Fixed:**
1. Created `backend/.env` from `.env.example` (SQLite dev DB, blank AI keys — Phase 2+ keys still needed from user).
2. Installed backend deps fresh (`pip install -r requirements.txt`) — all resolved cleanly, no conflicts.
3. Booted the server and discovered the repo had **four duplicate frontend copies**: repo-root (`/index.html`, `/js/`, `/css/`), `/landing/` (byte-identical to `frontend/`), and two zip archives. Diffed everything, confirmed `frontend/` (landing page) + `frontend/app/` (SPA) is the one actually mounted and served by `main.py`, and that `frontend/app/js/api/client.js` is the ONLY copy whose API calls match every current backend route (including `/chat`, `/scan`, `/docs/*` — the other frontend copies were stale and missing these).
4. Deleted: root `index.html`/`js/`/`css/`, `/landing/`, `/TEMPLATES.md` (root dup), `frontend.zip`, `frontend/full-site.zip`.
5. Verified `main.py`'s StaticFiles mount needed NO code change — it was already correctly pointed at `frontend/` the whole time; the "wrong frontend" concern from the previous session's analysis was actually about clutter, not a real routing bug.
6. Confirmed `/api/{id}/chat` route already existed in `api/routes/rag.py` — no missing route, previous analysis was based on a stale/incomplete file listing.
7. Ran `pytest tests/ -v` → 5/5 passing (first run hit a `PermissionError` on `dev.db` because the running uvicorn process held a lock — killed the server, reran, all green).
8. `py_compile` on every backend `.py` file — clean. `node --check` on every frontend `.js` file — clean.
9. Rewrote this file to reflect actual current state (previous version was stale — claimed Phase 2 RAG "not started" when it was actually built).

**Not yet done (see §7):** real API keys, full manual browser click-through, architecture doc frontend confirmation.

---

## 10. Important Context

- **Hardware constraint:** i7-1255U, 16GB RAM, Intel Iris Xe (no dedicated GPU) — no local LLM inference.
- **Budget constraint:** $0 — free tiers only (Gemini API, Pinecone free tier, Jina Embeddings free tier).
- **Test repo used for integration tests:** `https://github.com/octocat/Spoon-Knife` (do NOT use `octocat/Hello-World` — only one extensionless file, filter yields 0 matches).
- **Dev machine:** Windows, Python 3.11.16, bash via git-bash/MSYS.

---

## 11. Commands

```bash
# Install backend deps
cd backend && pip install -r requirements.txt

# Run dev server (serves API + frontend on same port)
cd backend && uvicorn app.main:app --reload
# → http://localhost:8000        (landing page)
# → http://localhost:8000/app/   (the actual app/SPA)
# → http://localhost:8000/api/*  (API)
# → http://localhost:8000/api/docs (Swagger)

# Alt entrypoint
cd backend && python run.py

# Run tests
cd backend && pytest tests/ -v

# Reset local dev DB between manual test runs (stop the server first — it locks the file)
rm -f backend/dev.db

# Postgres via Docker (untested this session)
docker compose up
```

---

## 12. Variables

**Environment variables** (`backend/.env`, created this session from `.env.example`):
- `APP_NAME`, `ENVIRONMENT`, `SECRET_KEY`
- `DATABASE_URL` (set to `sqlite+aiosqlite:///./dev.db` for local dev)
- `REPO_STORAGE_PATH`, `MAX_REPO_SIZE_MB`, `RATE_LIMIT_IMPORT`
- `GEMINI_API_KEY` (blank — needed for chat + doc generation)
- `JINA_API_KEY` (blank — needed for embeddings/indexing)
- `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME` (blank — needed for vector storage)
- `ALLOWED_ORIGINS` (set to `http://localhost:8000` for local dev)

**Ports:** `8000` — single port for everything.

**Paths:**
- `backend/storage/repositories/` — cloned repo storage (gitignored)
- `backend/dev.db` — SQLite dev database (gitignored)
- `frontend/` — served as static root at `/`; `frontend/app/` served at `/app/`

---

## 13. Next Immediate Step

Get the three free-tier API keys (Gemini, Jina, Pinecone) from Om, put them in `backend/.env`, restart the server, and do a full manual browser walkthrough: import a real repo → index it → ask it a question in chat → run a security scan → generate a README doc. That's the only way to know if Phases 2–5 (RAG, chat, scan, docs) actually work end-to-end, since so far they've only been verified to compile and route correctly, not to execute successfully against real AI APIs.

---

## 14. Things NOT To Change

- Do not reintroduce a separate frontend dev server/port — single-port serving via FastAPI `StaticFiles` is an explicit requirement.
- Do not move API routes out from under the `/api` prefix.
- Do not put `fetch()` calls anywhere outside `frontend/app/js/api/client.js`.
- Do not hardcode colors/fonts/spacing in JS or HTML — always reference CSS variables.
- Do not switch the frontend to React or add a JS build step.
- Do not remove the `app.mount("/", StaticFiles(...))` line's position at the END of `main.py`.
- Do not use `octocat/Hello-World` as a test fixture repo.
- Do not recreate duplicate frontend copies at repo root — `frontend/` (landing) + `frontend/app/` (SPA) is the single source of truth now.

---

## 15. Project History

**Version 0.1** — Backend foundation: FastAPI app, SQLAlchemy models, async DB session, settings, rate limiter.

**Version 0.2** — Phase 1 repository ingestion complete: clone/filter/store pipeline, endpoints, 5 passing integration tests.

**Version 0.3** — All API routes moved under `/api` prefix; frontend served by FastAPI via `StaticFiles` at `/`.

**Version 0.4 (this session)** — Cloned fresh from GitHub, booted and verified locally for the first time outside the original build sandbox. Discovered RAG/chat, security scanning, and doc generation were already built (previous PROJECT_CONTEXT.md was stale and understated progress). Found and removed 4x duplicate frontend copies + 2 stale zips. Confirmed `frontend/app/` is the correct, fully-wired SPA. All tests passing, all files syntax-clean, server boots and serves correctly end-to-end (minus real AI API keys, which are still needed).

---

## 16. Last Updated

- **Session:** Local dev environment setup + full project audit + cleanup
- **Latest milestone:** Repo cloned, booted, tested, duplicate frontend clutter removed, PROJECT_CONTEXT.md brought back in sync with actual code state.
