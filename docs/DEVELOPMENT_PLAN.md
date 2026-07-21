# Development Plan — Phase 1 Deep Dive

## Theory highlights

- **Shallow clone (`depth=1`)** — only current file state needed; faster, smaller, fits low-end hardware.
- **Filter before storing** — skip `node_modules`/`.git`/etc. at walk-time, not after.
- **Content hashing** — unused yet, but lets Phase 2's chunker skip re-embedding unchanged files on re-import.
- **URL validated by parsed hostname** — closes SSRF bypasses that a regex like `github\.com` would miss (e.g. `github.com.evil.com`).

## Real bugs hit and fixed

1. **`pydantic-settings` + `list[str]` env fields** — tries to JSON-decode the raw env var before custom validators run. Fix: store `allowed_origins` as plain `str`, expose `.allowed_origins_list` property.
2. **`httpx.AsyncClient` + `ASGITransport` doesn't trigger FastAPI lifespan** — tables never got created under test. Fix: explicitly wrap test calls in `async with app.router.lifespan_context(app):`.
3. **Sandbox filesystem reset mid-project** — all files vanished between sessions. Fix: rebuilt everything from scratch, re-verified with tests; now always `find`/`ls` to check state before assuming prior work persisted.
4. **`octocat/Hello-World` as a test fixture** — has only one extensionless file, correctly yields 0 filtered files (looked like a bug, wasn't). Fix: switched to `octocat/Spoon-Knife` (3 real source files) for all manual/automated tests.
5. **Backgrounded uvicorn dying between tool calls** — each sandbox shell command is a fresh process, so `&` backgrounding doesn't survive. Fix: use `setsid ... &` to detach the process from the controlling shell.

## Testing procedure

```bash
cd backend
pip install -r requirements.txt --break-system-packages
pytest tests/ -v
```

5 integration tests, real network calls to GitHub. Frontend JS was verified via `node --check` (syntax) and executing template functions directly in Node with a minimal DOM shim (runtime correctness), plus a full manual curl-driven walkthrough of the exact API sequence the UI performs (import → process → list → files) confirming response shapes match what the JS expects.

## Production considerations

- Replace `create_all()` with Alembic before first real deploy.
- Move cloning off the request thread (background task/queue) for large repos.
- Tighten rate limit (`.env.example` ships `5/minute` vs `20/minute` dev).
- Swap stub auth for real JWT/OAuth — models already have the FKs for it.
- Add a TTL/cleanup job for `storage/repositories/`, or move to object storage for horizontal scaling.
