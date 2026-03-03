from __future__ import annotations

from cli.providers.base import AIConfig, ProviderClient
from cli.providers.openai_client import OpenAIClient
from cli.providers.qwen_client import QwenClient


def get_provider_client(provider: str) -> ProviderClient:
    if provider == "qwen":
        return QwenClient()
    return OpenAIClient()


def chat_completion(prompt: str, cfg: AIConfig) -> str:
    client = get_provider_client(cfg.provider)
    return client.chat_completion(prompt, cfg)
