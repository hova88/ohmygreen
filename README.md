# ohmygreen

A private, minimalist, CLI-first AI blogging system inspired by BearBlog's design philosophy.

## Core pillars

- **AI**: Generate and refine posts with OpenAI or Qwen.
- **BearBlog-style minimalism**: Keep UI calm, focused, and reading-first.
- **CLI-first workflow**: Enter a guided terminal agent loop with `ohmygreen`.

## What this project does now

- Private account space with session-based web authentication.
- Per-user post isolation (you only see your own posts).
- Token-based API for CLI publishing.
- Alembic-managed schema migrations (no runtime `create_all`).
- Structured request/error logging with `request_id` and `error_code`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Makefile commands

```bash
make dev      # setup venv + install runtime/dev deps
make format   # ruff format
make lint     # ruff + mypy
make migrate  # alembic upgrade head
make serve    # migrate + uvicorn
make cli      # run ohmygreen terminal agent
```

## Dependency groups

- Runtime dependencies: `requirements.txt` / `[project.dependencies]`
- Development dependencies: `requirements-dev.txt` / `[project.optional-dependencies.dev]`

## Docker

```bash
docker compose up --build
```

Includes:
- multi-stage `Dockerfile`
- `docker-compose.yml` with `web` service + persisted SQLite volume

## Environment variables

Copy `.env.example` to `.env` and update values as needed.

```bash
cp .env.example .env
```

### web
- `OHMYGREEN_ENV` (set to `production` in production)
- `OHMYGREEN_SESSION_SECRET` (**must not** be empty/default in production)
- `DATABASE_URL`

### api
- API uses the same `DATABASE_URL` and `OHMYGREEN_SESSION_SECRET` as web.

### cli
- `OHMYGREEN_BASE_URL`
- `OHMYGREEN_AI_PROVIDER` (`openai` or `qwen`)

### ai
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `QWEN_API_KEY`
- `QWEN_MODEL`

## API endpoints

- `POST /api/auth/login` -> returns `{ username, token }`
- `GET /api/posts` -> list your own posts (Bearer token)
- `POST /api/posts` -> create a post (Bearer token)

Error payload format:

```json
{
  "error": {
    "request_id": "...",
    "error_code": "AUTH_ERROR",
    "message": "Invalid credentials"
  }
}
```
