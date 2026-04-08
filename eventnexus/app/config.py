"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/eventnexus"
    ticketmaster_api_key: str = ""
    eventbrite_api_token: str = ""
    max_concurrent_fetches: int = 10
    request_timeout_seconds: int = 30
    search_days_ahead: int = 365
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]


settings = Settings()
