from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="AI Studio", description="FastAPI application name.")
    api_v1_prefix: str = Field(default="/api/v1", description="Versioned API prefix.")
    environment: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_STUDIO_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
