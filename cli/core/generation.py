from __future__ import annotations

from cli.providers.config import load_ai_config
from cli.providers.service import chat_completion


def fallback_draft() -> str:
    return (
        "# Draft Title\n\n"
        "## Problem\nDescribe one sharp writing pain in plain words.\n\n"
        "## Approach\nShow your AI + CLI workflow in concrete steps.\n\n"
        "## CLI Action\n```bash\nohmygreen\n```"
    )


def generate_post(topic: str, audience: str, tone: str, provider: str) -> str:
    cfg = load_ai_config(provider)
    if not cfg.api_key:
        return fallback_draft()

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
