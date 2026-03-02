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
- Interactive terminal loop: `plan -> draft -> refine -> save/publish`.
- Minimal fallback draft generation when no AI key is configured.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## CLI usage

```bash
ohmygreen
```

The CLI will ask for:
- topic
- audience
- tone
- provider (`openai` or `qwen`)

Then it renders a draft preview and lets you choose:
- `regen`
- `save`
- `publish`
- `quit`

## Environment variables

```bash
# Web session
export OHMYGREEN_SESSION_SECRET="change-me"

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

## Architecture

- `app/main.py` - FastAPI web + API routes
- `app/models.py` - SQLAlchemy models
- `app/security.py` - password hashing + token generation
- `cli/blog_agent.py` - Typer + Rich interactive terminal agent
- `templates/`, `static/` - minimalist UI

## Design note

This project **references BearBlog principles** (simplicity, readability, minimal UI), not a line-by-line implementation of the BearBlog codebase.
