import os
from pathlib import Path

import requests
import typer

app = typer.Typer(help="CLI + AI workflow demo for OhMyGreen blog drafting")

SYSTEM_PROMPT = (
    "You are an assistant helping draft short minimalist blog posts. "
    "Return concise markdown with a title and content only."
)


def draft_with_ai(topic: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return f"# {topic.title()}\n\n- key idea\n- reflection\n- next step"

    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Draft a post about: {topic}"},
        ],
    }
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("output", [{}])[0].get("content", [{}])[0].get("text", "") or f"# {topic}\n\nDraft unavailable"


@app.command()
def run(topic: str = typer.Argument(..., help="Topic to draft about"), out: str = "drafts/latest.md"):
    """Basic agent loop demo: propose -> revise -> save."""
    typer.echo("[1/3] Generating draft...")
    draft = draft_with_ai(topic)

    typer.echo("[2/3] Self-critique and revision...")
    revised = f"{draft}\n\n---\n\nRevision notes: keep it practical and personal."

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(revised, encoding="utf-8")
    typer.echo(f"[3/3] Saved to {out}")
    typer.echo("Copy this content into the web app post form.")


if __name__ == "__main__":
    app()
