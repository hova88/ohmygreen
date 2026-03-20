from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Simple helper commands for local ohmygreen setup")
console = Console()


@app.command()
def doctor() -> None:
    """Verify the core folders needed to run the project."""
    required_paths = {
        "frontend/": Path("frontend").exists(),
        "backend/ or app/": Path("backend").exists() or Path("app").exists(),
        "README.md": Path("README.md").exists(),
    }
    for label, ok in required_paths.items():
        console.print(f"{'[green]OK[/green]' if ok else '[red]Missing[/red]'} {label}")


@app.command()
def bootstrap() -> None:
    """Print the fastest way to start the project locally."""
    console.print("[bold]Quick start[/bold]")
    console.print("1. python -m venv .venv && source .venv/bin/activate")
    console.print("2. pip install -e '.[dev]'")
    console.print("3. cd frontend && npm install")
    console.print("4. Start the API, then run the frontend dev server.")


@app.command()
def logo() -> None:
    """Print a minimal wordmark."""
    console.print("[green]ohmygreen[/green]")


if __name__ == "__main__":
    app()
