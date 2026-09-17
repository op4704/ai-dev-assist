# AI Developer Assistant

An AI-powered repository analysis platform: import a GitHub repo, chat with it, generate documentation, scan for security issues, review code quality, and visualize architecture — all on a $0 budget using free-tier APIs, running on a single port with zero build step for the frontend.

**Status:** Phase 0 (foundation) + Phase 1 (repository ingestion) — backend AND frontend built and tested end-to-end.

## Quickstart

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
uvicorn app.main:app --reload
```

Open **`http://localhost:8000`** — that's it. One port serves both the UI and the API:

- `http://localhost:8000/` → the web app (import a repo, browse files)
- `http://localhost:8000/api/*` → REST API
- `http://localhost:8000/api/docs` → interactive Swagger docs

No separate frontend server, no CORS setup needed, no `npm install`, no build step. The bundled `.env` is pre-configured for SQLite so this works with nothing else installed.

## Using the app

1. Open `http://localhost:8000` in your browser
2. Click **+ Import Repository**, paste a public GitHub URL (e.g. `https://github.com/octocat/Spoon-Knife`)
3. Watch it clone → index → redirect to the file browser
4. Browse indexed files grouped by language

## Run the tests

```bash
cd backend
pytest tests/ -v
```

Real integration tests — they clone an actual public GitHub repo over the network. Requires internet access.

## Project structure

```
ai-dev-assist/
├── backend/            FastAPI app + SQLAlchemy models + services
│   └── app/main.py     mounts frontend/ as static files AFTER /api routes
└── frontend/
    ├── index.html       Marketing landing page, served at /
    ├── css/, js/         landing page assets
    └── app/              The actual SPA, served at /app/ — vanilla JS, no build step
        ├── index.html
        ├── css/style.css   ← edit this to re-theme the whole app
        ├── js/api/client.js       the only file that calls the backend
        ├── js/templates/           reusable UI pieces (sidebar, badges, etc.)
        └── js/pages/                one file per route (dashboard, import, chat, repo detail)
```

**Want to change the UI?** See [`frontend/app/TEMPLATES.md`](frontend/app/TEMPLATES.md) — it explains exactly which file to edit for every kind of change, from re-theming to adding whole new pages, without touching backend code.

## Documentation

| Doc | Contents |
|---|---|
| [`frontend/TEMPLATES.md`](frontend/TEMPLATES.md) | How to swap/restyle the UI |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System diagram, layer breakdown, design decisions |
| [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | ER diagram, all 7 tables |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Every endpoint, request/response bodies, error codes |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | All 8 phases + free-tier signup links |
| [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) | Theory, real bugs hit + fixes, production notes |
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Full project state — hand this to any AI assistant to continue development |

## Moving to Postgres (optional, for production)

```bash
docker compose up
```

Same code, only `DATABASE_URL` changes. (Untested in this build sandbox — no Docker daemon available there — verify locally.)

## License

Your project — license as you see fit.
