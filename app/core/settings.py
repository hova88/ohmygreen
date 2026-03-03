import os
from pathlib import Path

SESSION_SECRET = os.getenv("OHMYGREEN_SESSION_SECRET", "dev-secret-change-in-production")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SESSION_SECRET = "dev-secret-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="OHMYGREEN_ENV")
    database_url: str = Field(default="sqlite:///./ohmygreen.db", alias="DATABASE_URL")

    session_secret: str = Field(default=DEFAULT_SESSION_SECRET, alias="OHMYGREEN_SESSION_SECRET")

    ai_provider: str = Field(default="openai", alias="OHMYGREEN_AI_PROVIDER")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")

    qwen_api_key: str = Field(default="", alias="QWEN_API_KEY")
    qwen_model: str = Field(default="qwen-plus", alias="QWEN_MODEL")

    base_url: str = Field(default="http://127.0.0.1:8000", alias="OHMYGREEN_BASE_URL")

    @field_validator("session_secret")
    @classmethod
    def validate_session_secret(cls, value: str, info: ValidationInfo) -> str:
        app_env = str(info.data.get("app_env", "development")).lower().strip()
        normalized = value.strip()
        if app_env == "production" and normalized in {"", DEFAULT_SESSION_SECRET}:
            raise ValueError("OHMYGREEN_SESSION_SECRET must be set to a strong non-default value in production")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
