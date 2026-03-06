# ohmygreen

Minimal, static, markdown-first technical blog platform inspired by Bear-style writing.

## Why this architecture?

This project uses **static site generation** to maximize simplicity, speed, and reliability:

- no runtime backend required
- markdown posts committed in Git
- tiny frontend footprint (mostly HTML + CSS)
- cheap deployment on any static host

## Repository structure

```text
blog/                 # Static build engine and markdown parser
cli/                  # `blog` CLI commands
frontend/
  templates/          # Jinja templates (homepage, blog index, post, 404, RSS, sitemap)
  static/             # Minimal serif styles
posts/                # Markdown content with frontmatter
dist/                 # Generated site output
scripts/              # Utility scripts
docs/                 # Architecture notes
configs/              # Deployment/container placeholders
backend/              # Reserved (empty by default)
```

## CLI

```bash
blog new "Post Title"
blog dev
blog build
blog deploy --target netlify
```

Disable CLI animation:

```bash
blog build --no-anim
# or
BLOG_NO_ANIMATION=1 blog dev
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
blog dev
```

Open http://localhost:4173.

## Markdown post format

```markdown
---
title: My Post
date: 2026-03-05
slug: my-post
tags:
  - architecture
---

Your markdown body.
```

## Deployment

1. Build static output: `blog build`
2. Deploy `dist/` to Netlify, Vercel, Cloudflare Pages, S3+CloudFront, or any CDN/static host.
