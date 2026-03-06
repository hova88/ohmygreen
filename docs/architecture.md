# ohmygreen architecture

## Design constraints
1. Simplicity over feature volume.
2. Clear frontend/backend separation.
3. Low dependency count and readable code.

## High-level shape
- `frontend/`: Vite + TypeScript SPA, no framework runtime.
- `backend/`: FastAPI JSON API + SQLAlchemy models.
- `cli/`: Typer developer tool for bootstrap/doctor/deploy helpers.
- `scripts/`: single-purpose shell scripts for local workflows.
- `configs/`: deployment files (Dockerfiles, compose, CI snippets).

## Request flow
1. Browser loads static frontend from Vite/preview container.
2. Frontend calls `GET/POST /api/v1/posts`.
3. FastAPI validates payload and runs service logic.
4. Service writes/reads from SQLite (configurable DB URL).
5. Structured response returned to frontend.

## Why this is maintainable
- Small modules with obvious names.
- Business logic concentrated in `services/`.
- Explicit typed request/response models.
- Environment-driven configuration only.
