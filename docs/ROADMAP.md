# Roadmap

✅ done · 🔜 next · ⏳ planned

## Phase 0 — Foundation ✅
Async SQLAlchemy, 7 tables, FastAPI app, CORS/rate-limit/error handling.

## Phase 1 — Repository Ingestion ✅
Clone → filter → store pipeline, 4 endpoints, 5 passing integration tests, **full vanilla-JS frontend** (dashboard, import flow, file explorer) served on the same port as the API.

## Phase 2 — Repository RAG 🔜
Chunking, Jina embeddings, Pinecone. Free accounts needed:
- Gemini: https://aistudio.google.com/apikey
- Jina: https://jina.ai/embeddings
- Pinecone: https://www.pinecone.io

## Phase 3 — Repository Chat ⏳
`POST /api/chat`, uses existing `chat_sessions`/`chat_messages` tables.

## Phase 4 — Documentation Generator ⏳
## Phase 5 — Security Scanner ⏳
## Phase 6 — Code Review Agent ⏳
## Phase 7 — Architecture Agent ⏳
## Phase 8 — Multi-Agent System (LangGraph) ⏳
## Phase 9 — Deployment ⏳
Render/Railway free tier — single FastAPI process, no separate frontend deploy needed since it's served statically from the same app.

Every ✅ phase has actually been run against real inputs and has passing automated tests — nothing here is a stub pretending to be finished.
