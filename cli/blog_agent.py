from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests
import typer

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    help="ohmygreen: AI + BearBlog + CLI writing workspace",
)


@dataclass
class AIConfig:
    provider: str
    model: str
    api_key: str


def load_ai_config(provider: str | None = None) -> AIConfig | None:
    selected = (provider or os.getenv("OHMYGREEN_AI_PROVIDER") or "openai").lower()
    if selected == "qwen":
        api_key = os.getenv("QWEN_API_KEY")
        model = os.getenv("QWEN_MODEL", "qwen-plus")
        return AIConfig(provider="qwen", model=model, api_key=api_key or "")

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return AIConfig(provider="openai", model=model, api_key=api_key or "")


def chat_completion(prompt: str, cfg: AIConfig) -> str:
    if not cfg.api_key:
        return (
            "# Draft\n\n"
            "## Core idea\n"
            "Write one sharp argument in 3-5 sentences.\n\n"
            "## Personal insight\n"
            "Add one real story from your workflow.\n\n"
            "## Action\n"
            "End with one command readers can run today."
        )

    system = (
        "You are an elite minimalist tech blogger. "
        "Write in concise BearBlog style, concrete and authentic."
    )

    if cfg.provider == "qwen":
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    else:
        url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
    }

    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_post(topic: str, audience: str, tone: str, provider: str | None = None) -> str:
    cfg = load_ai_config(provider)
    prompt = (
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Tone: {tone}\n"
        "Return markdown with this structure:\n"
        "# Title\n\n"
        "2-4 short sections, each with practical detail.\n"
        "End with '## CLI Action' and one runnable command."
    )
    draft = chat_completion(prompt, cfg)

    review_prompt = (
        "Revise this draft for clarity and density. Remove fluff, keep technical insight:\n\n"
        f"{draft}"
    )
    return chat_completion(review_prompt, cfg)


def parse_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()[:180] or "Untitled"
    return "Untitled"


def save_draft(markdown: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")


def api_login(base_url: str, username: str, password: str) -> str:
    r = requests.post(
        f"{base_url.rstrip('/')}/api/auth/login",
        json={"username": username, "password": password},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["token"]


def api_publish(base_url: str, token: str, title: str, content: str) -> int:
    r = requests.post(
        f"{base_url.rstrip('/')}/api/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title, "content": content},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["id"]


@app.callback(invoke_without_command=True)
def shell(ctx: typer.Context):
    """Run `ohmygreen` to enter a Codex-like agent loop."""
    if ctx.invoked_subcommand:
        return

    typer.echo("ohmygreen // AI + bearblog + cli")
    typer.echo("Type your idea, and I will run an agent loop: plan -> draft -> refine -> publish.")

    topic = typer.prompt("Topic")
    audience = typer.prompt("Audience", default="indie builders")
    tone = typer.prompt("Tone", default="calm, practical")
    provider = typer.prompt("AI Provider (openai/qwen)", default="openai")

    typer.echo("\n[1/4] Planning + drafting...")
    markdown = generate_post(topic=topic, audience=audience, tone=tone, provider=provider)
    typer.echo("\n===== Draft Preview =====\n")
    typer.echo(markdown[:3000])
    typer.echo("\n=========================\n")

    while True:
        action = typer.prompt("Action: [p]ublish / [s]ave / [r]egenerate / [q]uit", default="s").lower().strip()

        if action == "r":
            extra = typer.prompt("Refine instruction", default="make it more concrete")
            markdown = generate_post(
                topic=f"{topic}. refinement: {extra}",
                audience=audience,
                tone=tone,
                provider=provider,
            )
            typer.echo("\nRegenerated.\n")
            continue

        if action == "s":
            path = Path(typer.prompt("Save path", default="drafts/latest.md"))
            save_draft(markdown, path)
            typer.echo(f"Saved draft -> {path}")
            continue

        if action == "p":
            base_url = typer.prompt("Server URL", default=os.getenv("OHMYGREEN_BASE_URL", "http://127.0.0.1:8000"))
            username = typer.prompt("Username")
            password = typer.prompt("Password", hide_input=True)
            token = api_login(base_url, username, password)
            post_id = api_publish(base_url, token, parse_title(markdown), markdown)
            typer.echo(f"Published as post #{post_id}")
            continue

        if action == "q":
            typer.echo("Bye. Keep writing.")
            break


@app.command()
def publish_file(
    path: Path = typer.Argument(..., exists=True, readable=True),
    base_url: str = typer.Option("http://127.0.0.1:8000"),
    username: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Publish an existing markdown file via API."""
    content = path.read_text(encoding="utf-8")
    token = api_login(base_url, username, password)
    post_id = api_publish(base_url, token, parse_title(content), content)
    typer.echo(f"Published {path} -> post #{post_id}")


if __name__ == "__main__":
    app()
