from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests
import typer
from app.core.settings import Settings, get_settings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

app = typer.Typer(add_completion=False, no_args_is_help=False, help="ohmygreen terminal writing agent")
console = Console()


@dataclass
class AIConfig:
    provider: str
    model: str
    api_key: str


def load_ai_config(settings: Settings, provider: str | None = None) -> AIConfig:
    selected = (provider or settings.ai_provider).lower().strip()
    if selected == "qwen":
        return AIConfig(provider="qwen", model=settings.qwen_model, api_key=settings.qwen_api_key)
    return AIConfig(provider="openai", model=settings.openai_model, api_key=settings.openai_api_key)


def provider_url(provider: str) -> str:
    if provider == "qwen":
        return "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    return "https://api.openai.com/v1/chat/completions"


def chat_completion(prompt: str, cfg: AIConfig) -> str:
    if not cfg.api_key:
        return (
            "# Draft Title\n\n"
            "## Problem\nDescribe one sharp writing pain in plain words.\n\n"
            "## Approach\nShow your AI + CLI workflow in concrete steps.\n\n"
            "## CLI Action\n```bash\nohmygreen\n```"
        )

    payload = {
        "model": cfg.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write minimalist technical blog posts inspired by BearBlog style: "
                    "calm, compact, useful, no fluff, practical details first."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
    }
    response = requests.post(
        provider_url(cfg.provider),
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def generate_post(topic: str, audience: str, tone: str, provider: str, settings: Settings) -> str:
    cfg = load_ai_config(settings=settings, provider=provider)

    plan_prompt = (
        f"Topic: {topic}\nAudience: {audience}\nTone: {tone}\n"
        "Create a concise 3-step writing plan with section names and intent."
    )
    plan = chat_completion(plan_prompt, cfg)

    draft_prompt = (
        "Use this plan to write a final markdown post:\n"
        f"{plan}\n\n"
        "Rules:\n"
        "1) Start with '# Title'.\n"
        "2) Keep short sections and practical examples.\n"
        "3) End with '## CLI Action' and one runnable command."
    )
    draft = chat_completion(draft_prompt, cfg)

    refine_prompt = (
        "Refine the post to remove fluff, tighten wording, and keep every paragraph actionable:\n\n"
        f"{draft}"
    )
    return chat_completion(refine_prompt, cfg)


def parse_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()[:180] or "Untitled"
    return "Untitled"


def save_draft(markdown: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")


def api_login(base_url: str, username: str, password: str) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/auth/login",
        json={"username": username, "password": password},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["token"]


def api_publish(base_url: str, token: str, title: str, content: str) -> int:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title, "content": content},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["id"]


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


@app.callback(invoke_without_command=True)
def shell(ctx: typer.Context) -> None:
    """Run `ohmygreen` to enter interactive writing mode."""
    if ctx.invoked_subcommand:
        return

    settings = get_settings()

    render_header()
    topic = Prompt.ask("Topic")
    audience = Prompt.ask("Audience", default="indie builders")
    tone = Prompt.ask("Tone", default="clear and practical")
    provider = Prompt.ask("AI provider", choices=["openai", "qwen"], default=settings.ai_provider)

    render_context(topic, audience, tone, provider)
    console.print("[yellow]Generating draft...[/yellow]")
    markdown = generate_post(topic=topic, audience=audience, tone=tone, provider=provider, settings=settings)
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
                settings=settings,
            )
            console.print(Panel(Markdown(markdown), title="Regenerated Draft", border_style="magenta"))
            continue

        if action == "save":
            path = Path(Prompt.ask("Save path", default="drafts/latest.md"))
            save_draft(markdown, path)
            console.print(f"[green]Saved:[/green] {path}")
            continue

        if action == "publish":
            base_url = Prompt.ask("Server URL", default=settings.base_url)
            username = Prompt.ask("Username")
            password = Prompt.ask("Password", password=True)
            token = api_login(base_url, username, password)
            post_id = api_publish(base_url, token, parse_title(markdown), markdown)
            console.print(f"[bold green]Published as post #{post_id}[/bold green]")
            continue

        console.print("[dim]See you next draft.[/dim]")
        break


@app.command("publish-file")
def publish_file(
    path: Path = typer.Argument(..., exists=True, readable=True),
    base_url: str | None = typer.Option(None),
    username: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Publish an existing markdown file via API."""
    settings = get_settings()
    target_base_url = base_url or settings.base_url
    content = path.read_text(encoding="utf-8")
    token = api_login(target_base_url, username, password)
    post_id = api_publish(target_base_url, token, parse_title(content), content)
    console.print(f"[green]Published[/green] {path} -> post #{post_id}")


if __name__ == "__main__":
    app()
