from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text

from blog.builder import BlogBuilder
from blog.config import BlogConfig
from blog.utils import slugify

app = typer.Typer(help="Minimal blog CLI")
console = Console()

LOGO = r"""
   __    __
  / /_  / /___  ____ _
 / __ \/ / __ \/ __ `/
/ /_/ / / /_/ / /_/ /
\____/_/\____/\__, /
             /____/
"""


def _show_logo(no_anim: bool = False) -> None:
    logo_text = Text(LOGO, style="bright_black")
    if no_anim or os.getenv("BLOG_NO_ANIMATION") == "1":
        console.print(logo_text)
        return
    for line in LOGO.splitlines():
        console.print(Text(line, style="bright_black"))
        time.sleep(0.03)


@app.command()
def new(title: str) -> None:
    """Create a new markdown post with frontmatter."""
    slug = slugify(title)
    path = Path("posts") / f"{slug}.md"
    if path.exists():
        raise typer.Exit(code=1)
    body = f"""---
title: {title}
date: {datetime.now().strftime('%Y-%m-%d')}
slug: {slug}
tags:
  - notes
---

Write your post here.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    console.print(f"[blue]Created[/blue] {path}")


@app.command()
def build(no_anim: bool = typer.Option(False, "--no-anim", help="Disable logo animation")) -> None:
    """Generate static blog output in dist/."""
    _show_logo(no_anim=no_anim)
    with console.status("[cyan]Building static blog...[/cyan]"):
        BlogBuilder(BlogConfig()).build()
    console.print("[cyan]Build complete[/cyan] -> dist/")


@app.command()
def dev(
    port: int = typer.Option(4173, "--port"),
    watch: bool = typer.Option(True, "--watch/--no-watch"),
    no_anim: bool = typer.Option(False, "--no-anim"),
) -> None:
    """Build and serve the blog locally."""
    import http.server
    import socketserver
    import threading

    _show_logo(no_anim=no_anim)
    builder = BlogBuilder(BlogConfig())
    builder.build()

    if watch:
        thread = threading.Thread(target=_watch_posts, args=(builder,), daemon=True)
        thread.start()

    os.chdir("dist")
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        console.print(f"[cyan]Preview[/cyan] http://localhost:{port}")
        httpd.serve_forever()


@app.command()
def deploy(target: str = typer.Option("netlify", "--target")) -> None:
    """Build then print deployment command for static hosts."""
    BlogBuilder(BlogConfig()).build()
    commands = {
        "netlify": "netlify deploy --prod --dir=dist",
        "vercel": "vercel --prod dist",
        "s3": "aws s3 sync dist/ s3://<bucket-name> --delete",
    }
    command = commands.get(target, "rsync -av dist/ <server>:/var/www/blog/")
    console.print(f"[blue]Run:[/blue] {command}")


def _watch_posts(builder: BlogBuilder) -> None:
    tracked: dict[Path, float] = {}
    while True:
        changed = False
        for file in Path("posts").glob("*.md"):
            mtime = file.stat().st_mtime
            if tracked.get(file) != mtime:
                tracked[file] = mtime
                changed = True
        if changed:
            builder.build()
            console.print("[bright_black]rebuilt[/bright_black]")
        time.sleep(1)


if __name__ == "__main__":
    app()
