from __future__ import annotations

from pathlib import Path

import typer

from cli.core.generation import parse_title
from cli.transport.http_client import api_login, api_publish
from cli.ui.workflow import console, interactive_shell

app = typer.Typer(add_completion=False, no_args_is_help=False, help="ohmygreen terminal writing agent")


@app.callback(invoke_without_command=True)
def shell(ctx: typer.Context) -> None:
    """Run `ohmygreen` to enter interactive writing mode."""
    if ctx.invoked_subcommand:
        return
    interactive_shell()


@app.command("publish-file")
def publish_file(
    path: Path = typer.Argument(..., exists=True, readable=True),
    base_url: str = typer.Option("http://127.0.0.1:8000"),
    username: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Publish an existing markdown file via API."""
    content = path.read_text(encoding="utf-8")
    token = api_login(base_url, username, password)
    post_id = api_publish(base_url, token, parse_title(content), content)
    console.print(f"[green]Published[/green] {path} -> post #{post_id}")


if __name__ == "__main__":
    app()
