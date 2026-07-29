"""Application configuration loaded from environment variables (12-factor).

All settings are validated at import time via Pydantic Settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    """Typed, validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    environment: Environment = "development"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production", min_length=8)

    # Auth (self-contained JWT)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "PSX Value Investor Platform API"
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+psycopg://psx:psx@localhost:5432/psx"

    # CORS — strict allow-list of trusted origins
    cors_origins: list[str] = ["http://localhost:3000"]

    # Observability
    sentry_dsn: str | None = None
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
