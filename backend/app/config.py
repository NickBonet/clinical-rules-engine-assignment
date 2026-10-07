"""Runtime settings, read from APP_ environment variables or .env."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the data directory relative to the repo, not the working directory.
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # SQLite runs in memory; Postgres saves data between runs.
    backend: Literal["sqlite", "postgres"] = "sqlite"

    # Postgres only. Use localhost when running locally, or db inside Docker Compose.
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/clinical"

    data_dir: Path = REPO_ROOT / "data"

    # Default to the latest lab date during ingest.
    as_of: date | None = None


settings = Settings()
