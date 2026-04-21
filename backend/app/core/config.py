"""Runtime configuration for the Optico platform."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Optico Agentic ITOps"
    environment: Literal["dev", "shadow", "canary", "prod"] = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # LLM providers (at least one must be configured)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    default_model: str = "claude-opus-4-7"
    fast_model: str = "claude-haiku-4-5-20251001"

    # Neo4j knowledge graph
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "optico-dev-password"

    # Redis (HITL queue, cache, pub/sub)
    redis_url: str = "redis://localhost:6379/0"

    # Postgres (app state: incidents, changes, audit log)
    database_url: str = "sqlite+aiosqlite:///./optico.db"

    # Governance
    default_autonomy_level: int = Field(default=0, ge=0, le=4)
    autonomy_promotion_min_runs: int = 30
    autonomy_promotion_min_accuracy: float = 0.95
    autonomy_promotion_max_calibration_error: float = 0.10

    # CORS (frontend dev server)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Feature flags
    enable_shadow_mode: bool = True
    enable_kill_switch: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
