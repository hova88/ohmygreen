from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ohmygreen-api"
    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_prefix="OHMYGREEN_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
