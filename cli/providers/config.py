from __future__ import annotations

import os

from cli.providers.base import AIConfig


def load_ai_config(provider: str | None = None) -> AIConfig:
    selected = (provider or os.getenv("OHMYGREEN_AI_PROVIDER") or "openai").lower().strip()
    if selected == "qwen":
        return AIConfig(
            provider="qwen",
            model=os.getenv("QWEN_MODEL", "qwen-plus"),
            api_key=os.getenv("QWEN_API_KEY", ""),
        )
    return AIConfig(
        provider="openai",
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )
