# ohmygreen

Minimal full-stack writing platform inspired by BearBlog's engineering philosophy:
small surface area, clear boundaries, and pragmatic defaults.

## Stack
- **Frontend**: Vite + TypeScript (vanilla, no SPA framework)
- **Backend**: FastAPI + SQLAlchemy
- **CLI**: Typer + Rich
- **Build**: Make + npm + pip
- **Deploy**: Docker Compose

## Repository layout

```text
backend/
  app/
    api/
    core/
    db/
    domain/
    services/
frontend/
  src/
cli/
  ohmygreen_cli/
scripts/
configs/
docs/
```

## Quick start

```bash
make dev
source .venv/bin/activate
make backend
```

In a second terminal:

```bash
make frontend
```

## CLI

```bash
make cli         # opens dev CLI
make doctor      # verifies local setup
```

Disable animations:

```bash
OHMYGREEN_NO_ANIMATION=1 make cli
```

## API

- `GET /api/v1/health`
- `GET /api/v1/posts`
- `POST /api/v1/posts`

## Deployment

```bash
docker compose -f configs/docker-compose.yml up --build
```

## Security baseline

- Pydantic request validation for API payloads.
- Environment based secrets and runtime config.
- CORS allow-list from `OHMYGREEN_CORS_ORIGINS`.
- Generic JSON errors without secret leakage.
