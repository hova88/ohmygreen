# ohmygreen

> A clean writing workspace with a lightweight web app, a practical CLI, and a setup that helps users publish quickly.

ohmygreen is built for people who want to go from idea to published post without fighting a complex dashboard. The product keeps the surface area small:

- **Write fast** with a calm web editor.
- **Publish simply** through a small API.
- **Work from the terminal** when you prefer Markdown and command-line flows.

## Why users like it

- **Minimal interface** — one main writing area, one recent-posts view, fewer decisions.
- **Friendly workflow** — clear prompts, simple statuses, and readable defaults.
- **Flexible usage** — write in the browser, generate drafts in the CLI, or publish local Markdown files.

## Product overview

```text
frontend/              Vite web app for drafting and reviewing posts
backend/               FastAPI-style API implementation
app/                   Additional API/web service implementation used by the CLI routes
cli/                   Terminal writing and publishing tools
posts/                 Example Markdown content
docs/                  Architecture notes
```

## Quick start

### 1. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start the app

Because this repository currently contains both `backend/` and `app/` service code, choose the API entrypoint your environment uses, then start the frontend.

Typical frontend development command:

```bash
cd frontend
npm run dev
```

Then open the local URL printed by Vite.

## Web experience

The web app is designed around two simple actions:

1. **Create a post** — add a title, write content, and publish.
2. **Review recent posts** — the newest post is highlighted and older posts are summarized below.

### Web goals

- Keep the writing surface focused.
- Show only the most important publishing feedback.
- Make recent content easy to scan.

## CLI experience

The CLI now aims to be direct instead of theatrical.

### Guided mode

Run the default interactive flow:

```bash
python -m cli.commands.main
```

You will:

1. enter a topic,
2. get a draft preview,
3. choose to save, publish, retry, or quit.

### Generate a draft directly

```bash
python -m cli.commands.main write "Shipping a tiny product update" --save-to drafts/update.md
```

### Publish an existing Markdown file

```bash
python -m cli.commands.main publish-file drafts/update.md --username demo
```

### Check local setup

```bash
python -m cli.commands.main doctor
python -m cli.ohmygreen_cli.main doctor
```

## Design principles

The redesign follows a few simple rules:

- **One primary action per screen**.
- **Plain language over internal jargon**.
- **Fast defaults over heavy configuration**.
- **Professional presentation without visual noise**.

## Recommended next improvements

If you continue polishing the project, these are strong next steps:

- unify the duplicated API surface between `backend/` and `app/`,
- add screenshots or GIFs of the web and CLI flows,
- document the exact backend startup command for the chosen deployment path,
- add end-to-end tests for publishing from both web and CLI.
