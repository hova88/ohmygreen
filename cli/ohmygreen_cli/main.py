from __future__ import annotations

import itertools
import os
import sys
import time
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="ohmygreen developer CLI")
console = Console()

LOGO = r"""
  ____  _                           
 / __ \(_)___ ___  ____ _____  ____
/ / / / / __ `__ \/ __ `/ __ \/ __ \
/ /_/ / / / / / / / /_/ / / / / /_/ /
\____/_/_/ /_/ /_/\__,_/_/ /_/\____/
"""


def animations_enabled() -> bool:
    return os.getenv("OHMYGREEN_NO_ANIMATION", "0") != "1"


def typewriter(text: str, delay: float = 0.02) -> None:
    if not animations_enabled():
        console.print(text)
        return
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def spinner(text: str, seconds: float = 1.0) -> None:
    if not animations_enabled():
        console.print(f"- {text}")
        return
    chars = itertools.cycle("⠋⠙⠸⠴⠦⠇")
    end = time.time() + seconds
    while time.time() < end:
        sys.stdout.write(f"\r{next(chars)} {text}")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write(f"\r✓ {text}\n")


@app.command()
def doctor() -> None:
    """Verify local toolchain."""
    console.print("[grey58]ohmygreen[/grey58] [cyan]doctor[/cyan]")
    spinner("checking backend folder")
    assert Path("backend").exists(), "backend/ not found"
    spinner("checking frontend folder")
    assert Path("frontend").exists(), "frontend/ not found"
    spinner("checking env sample")
    assert Path(".env.example").exists(), ".env.example not found"
    console.print("[cyan]environment looks good[/cyan]")


@app.command()
def bootstrap() -> None:
    """Print first-run commands."""
    console.print("[grey58]ohmygreen[/grey58] [cyan]bootstrap[/cyan]")
    typewriter("python -m venv .venv && source .venv/bin/activate")
    typewriter("pip install -r requirements-dev.txt")
    typewriter("make dev")


@app.command()
def logo() -> None:
    """Print ASCII logo."""
    console.print("[grey58]" + LOGO + "[/grey58]")


if __name__ == "__main__":
    app()
