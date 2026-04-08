"""Application configuration using pydantic-settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "events.db",
    )
    max_concurrent_fetches: int = 10
    request_timeout_seconds: int = 30
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]


settings = Settings()
