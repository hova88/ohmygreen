from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from cli.core.generation import generate_post, parse_title
from cli.transport.http_client import api_login, api_publish

console = Console()


def save_draft(markdown: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")


def render_header() -> None:
    console.print(
        Panel.fit(
            "[bold green]ohmygreen[/bold green]\n"
            "[dim]AI + BearBlog + CLI[/dim]\n"
            "[dim]agent loop: plan -> draft -> refine -> publish[/dim]",
            border_style="green",
        )
    )


def render_context(topic: str, audience: str, tone: str, provider: str) -> None:
    table = Table(show_header=False, box=None)
    table.add_row("[bold]Topic[/bold]", topic)
    table.add_row("[bold]Audience[/bold]", audience)
    table.add_row("[bold]Tone[/bold]", tone)
    table.add_row("[bold]Provider[/bold]", provider)
    console.print(Panel(table, title="Session", border_style="cyan"))


def interactive_shell() -> None:
    render_header()
    topic = Prompt.ask("Topic")
    audience = Prompt.ask("Audience", default="indie builders")
    tone = Prompt.ask("Tone", default="clear and practical")
    provider = Prompt.ask("AI provider", choices=["openai", "qwen"], default="openai")

    render_context(topic, audience, tone, provider)
    console.print("[yellow]Generating draft...[/yellow]")
    markdown = generate_post(topic=topic, audience=audience, tone=tone, provider=provider)
    console.print(Panel(Markdown(markdown), title="Draft Preview", border_style="magenta"))

    while True:
        action = Prompt.ask("Action", choices=["publish", "save", "regen", "quit"], default="save")

        if action == "regen":
            extra = Prompt.ask("Refinement instruction", default="make it denser and more tactical")
            markdown = generate_post(
                topic=f"{topic}. Additional instruction: {extra}",
                audience=audience,
                tone=tone,
                provider=provider,
            )
            console.print(Panel(Markdown(markdown), title="Regenerated Draft", border_style="magenta"))
            continue

        if action == "save":
            path = Path(Prompt.ask("Save path", default="drafts/latest.md"))
            save_draft(markdown, path)
            console.print(f"[green]Saved:[/green] {path}")
            continue

        if action == "publish":
            base_url = Prompt.ask("Server URL", default=os.getenv("OHMYGREEN_BASE_URL", "http://127.0.0.1:8000"))
            username = Prompt.ask("Username")
            password = Prompt.ask("Password", password=True)
            token = api_login(base_url, username, password)
            post_id = api_publish(base_url, token, parse_title(markdown), markdown)
            console.print(f"[bold green]Published as post #{post_id}[/bold green]")
            continue

        console.print("[dim]See you next draft.[/dim]")
        break
