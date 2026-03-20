from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from cli.core.generation import generate_post, parse_title
from cli.transport.http_client import APIClientError, api_login, api_publish

console = Console()


def save_draft(markdown: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")


def render_header() -> None:
    console.print(
        Panel.fit(
            "[bold green]ohmygreen[/bold green]\n"
            "[dim]A simple writing assistant for drafting and publishing posts.[/dim]",
            border_style="green",
        )
    )


def preview(markdown: str, title: str = "Draft preview") -> None:
    console.print(Panel(Markdown(markdown), title=title, border_style="green"))


def publish_markdown(markdown: str, base_url: str | None = None) -> None:
    target_base_url = base_url or os.getenv("OHMYGREEN_BASE_URL", "http://127.0.0.1:8000")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)

    try:
        token = api_login(target_base_url, username, password)
        post_id = api_publish(target_base_url, token, parse_title(markdown), markdown)
    except APIClientError as exc:
        console.print(f"[red]Publish failed:[/red] {exc}")
        return

    console.print(f"[green]Published successfully[/green] as post #{post_id}")


def interactive_shell() -> None:
    render_header()
    topic = Prompt.ask("What do you want to write about?")
    audience = Prompt.ask("Audience (optional)", default="general readers")
    tone = Prompt.ask("Tone (optional)", default="clear and friendly")
    provider = Prompt.ask("AI provider", choices=["openai", "qwen"], default="openai")

    console.print("[yellow]Generating draft...[/yellow]")
    markdown = generate_post(topic=topic, audience=audience, tone=tone, provider=provider)
    preview(markdown)

    next_step = Prompt.ask(
        "Next step",
        choices=["save", "publish", "retry", "quit"],
        default="save",
    )

    if next_step == "retry":
        extra = Prompt.ask("Optional improvement", default="make it shorter and more practical")
        markdown = generate_post(
            topic=f"{topic}. Additional instruction: {extra}",
            audience=audience,
            tone=tone,
            provider=provider,
        )
        preview(markdown, title="Updated draft")
        next_step = Prompt.ask("Now choose", choices=["save", "publish", "quit"], default="save")

    if next_step == "save":
        path = Path(Prompt.ask("Save path", default="drafts/latest.md"))
        save_draft(markdown, path)
        console.print(f"[green]Saved[/green] {path}")
        if Confirm.ask("Publish it now?", default=False):
            publish_markdown(markdown)
        return

    if next_step == "publish":
        publish_markdown(markdown)
        return

    console.print("[dim]No problem. Your draft preview is above if you want to reuse it.[/dim]")
