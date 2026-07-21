# API Reference

Base URL: `http://localhost:8000/api`

All endpoints operate against an auto-created demo user — no auth header needed yet.

### `POST /api/repository/import`
```json
{ "github_url": "https://github.com/octocat/Spoon-Knife" }
```
**201** → repository object, `status: "pending"` (cloned, awaiting `/process`)
**422** — invalid URL · **400** — clone failed (private/deleted repo) · **409** — already imported

### `POST /api/repository/process`
```json
{ "repository_id": 1 }
```
**200** → repository object, `status: "ready"`, `total_files` populated
**404** — repository not found · **400** — not cloned yet · **500** — processing failed

### `GET /api/repository/{id}/files`
**200** → `[{ id, path, language, size_bytes }, ...]`
**404** — repository not found

### `GET /api/repositories`
**200** → array of repository objects, newest first

### `GET /api/health`
**200** → `{ "status": "ok", "app": "..." }`

## Docs

Interactive Swagger UI: `http://localhost:8000/api/docs`
ReDoc: `http://localhost:8000/api/redoc`

## Error handling

Every handled error returns `{"detail": "..."}` with an appropriate status code. Unexpected errors fall through to a global handler that logs server-side and returns a generic `500` — never a raw stack trace to the client.
