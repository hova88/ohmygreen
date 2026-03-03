from __future__ import annotations

import requests

from cli.providers.base import AIConfig


def provider_url(provider: str) -> str:
    if provider == "qwen":
        return "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    return "https://api.openai.com/v1/chat/completions"


class OpenAIClient:
    def chat_completion(self, prompt: str, cfg: AIConfig) -> str:
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
