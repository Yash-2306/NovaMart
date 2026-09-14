"""Application configuration using Pydantic Settings."""

from __future__ import annotations

import logging
import sys
from functools import lru_cache
from typing import Literal

import structlog
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    groq_api_key: str = "your_groq_api_key_here"
    database_url: str = "sqlite+aiosqlite:///./data/novamart.db"
    checkpoint_db_url: str = "sqlite:///./data/checkpoints.db"
    log_level: str = "INFO"
    environment: Literal["development", "production", "testing"] = "development"
    groq_model: str = "openai/gpt-oss-120b"
    groq_fast_model: str = "openai/gpt-oss-120b"
    # Admin dashboard API key — shown in README for evaluators
    admin_api_key: str = "novamart-admin-2024"

    @field_validator("groq_api_key", mode="after")
    @classmethod
    def validate_groq_api_key(cls, v: str) -> str:
        if v == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY must be configured in .env file. Please add your Groq API key to proceed.")
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Configure structlog for JSON (production) or colored console (development) output."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.environment == "development":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    # Quiet noisy loggers
    for name in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
