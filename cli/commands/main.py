from __future__ import annotations

from pathlib import Path

import typer

from cli.core.generation import generate_post, parse_title
from cli.transport.http_client import APIClientError, api_login, api_publish
from cli.ui.workflow import console, interactive_shell, preview, save_draft

app = typer.Typer(add_completion=False, no_args_is_help=False, help="Simple terminal writing and publishing for ohmygreen")


@app.callback(invoke_without_command=True)
def shell(ctx: typer.Context) -> None:
    """Open the guided writing flow."""
    if ctx.invoked_subcommand:
        return
    interactive_shell()


@app.command("write")
def write(
    topic: str = typer.Argument(..., help="What the post is about."),
    save_to: Path | None = typer.Option(None, "--save-to", help="Write the generated draft to a markdown file."),
    audience: str = typer.Option("general readers", help="Who the draft is for."),
    tone: str = typer.Option("clear and friendly", help="How the draft should sound."),
    provider: str = typer.Option("openai", help="AI provider to use."),
    preview_only: bool = typer.Option(False, "--preview-only", help="Only print the draft preview."),
) -> None:
    """Generate a draft with sensible defaults."""
    markdown = generate_post(topic=topic, audience=audience, tone=tone, provider=provider)
    preview(markdown)

    if save_to is not None:
        save_draft(markdown, save_to)
        console.print(f"[green]Saved[/green] {save_to}")

    if preview_only and save_to is None:
        console.print("[dim]Preview only. Use --save-to to keep the draft.[/dim]")


@app.command("publish-file")
def publish_file(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Markdown file to publish."),
    base_url: str = typer.Option("http://127.0.0.1:8000", help="API server base URL."),
    username: str = typer.Option(..., prompt=True, help="Account username."),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Account password."),
) -> None:
    """Publish a local markdown file through the API."""
    content = path.read_text(encoding="utf-8")

    try:
        token = api_login(base_url, username, password)
        post_id = api_publish(base_url, token, parse_title(content), content)
    except APIClientError as exc:
        console.print(f"[red]Publish failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Published[/green] {path} -> post #{post_id}")


@app.command("doctor")
def doctor() -> None:
    """Show the minimum pieces you need before publishing."""
    checks = {
        "frontend/": Path("frontend").exists(),
        "backend/ or app/": Path("backend").exists() or Path("app").exists(),
        "README.md": Path("README.md").exists(),
    }
    for label, ok in checks.items():
        console.print(f"{'[green]OK[/green]' if ok else '[red]Missing[/red]'} {label}")


if __name__ == "__main__":
    app()
