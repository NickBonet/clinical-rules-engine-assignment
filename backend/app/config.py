"""Runtime configuration. The as-of date and data location are overridable so the
pipeline is reproducible and testable."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # "sqlite" runs with an ephemeral in-memory SQLite DB (no setup); "postgres"
    # uses the persistent Postgres DB. Both go through the one SQL repository.
    backend: Literal["sqlite", "postgres"] = "sqlite"

    # Used only when backend is set to postgres. Host
    # is "localhost" for a host-run backend and the "db" service name inside the
    # compose network; override with APP_DATABASE_URL accordingly.
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/clinical"

    data_dir: Path = REPO_ROOT / "data"

    # None -> derive from data (max lab result_date) at ingest time.
    as_of: date | None = None


settings = Settings()
