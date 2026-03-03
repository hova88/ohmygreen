from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class AIConfig:
    provider: str
    model: str
    api_key: str


class ProviderClient(Protocol):
    def chat_completion(self, prompt: str, cfg: AIConfig) -> str: ...
