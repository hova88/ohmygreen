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

```bash
# Web session
export OHMYGREEN_SESSION_SECRET="change-me"

# Database
export OHMYGREEN_DATABASE_URL="sqlite:///./ohmygreen.db"

# OpenAI
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4.1-mini"

# Qwen (DashScope-compatible)
export QWEN_API_KEY="..."
export QWEN_MODEL="qwen-plus"

# optional
export OHMYGREEN_BASE_URL="http://127.0.0.1:8000"
export OHMYGREEN_AI_PROVIDER="openai"
```

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
