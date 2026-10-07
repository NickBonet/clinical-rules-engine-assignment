"""Build a fully-evaluated repository, for either backend.

Both backends use the one `SqlRepository` over SQLAlchemy; they differ only in
the engine:

- `build_sqlite_repository` — ephemeral in-memory SQLite. Ingests + evaluates in
  process (on the CLI, a dry run; on the API, at startup). No files, no setup.
- `ingest_postgres` (write) + `open_postgres_repository` (read) — the persistent
  Postgres path, where a writer process populates the DB and the API reads it.

All return `(Repository, date)` so callers are backend-agnostic.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import Engine

from app.pipeline.as_of import resolve_as_of
from app.pipeline.ingest import all_labs, load_contexts
from app.pipeline.orchestrator import run_all
from app.repository import Repository, SqlRepository
from app.repository.db import (
    create_schema,
    make_engine,
    make_session_factory,
    make_sqlite_engine,
)
from app.repository.sql import latest_as_of, record_run, write_facts


def _ingest_into(engine: Engine, data_dir: Path, as_of_override: date | None) -> tuple[Repository, date]:
    """Create schema, refresh facts, evaluate, and record the run on `engine`."""
    create_schema(engine)
    factory = make_session_factory(engine)

    contexts = load_contexts(data_dir)
    as_of = resolve_as_of(all_labs(contexts), as_of_override)

    with factory() as session:
        write_facts(session, contexts)

    repo = SqlRepository(factory)
    run_all(as_of, repo)  # per-patient replace_derived_state, each its own txn

    with factory() as session:
        record_run(session, as_of)

    return repo, as_of


def build_sqlite_repository(data_dir: Path, as_of_override: date | None = None) -> tuple[Repository, date]:
    """Zero-setup path: ingest + evaluate into an ephemeral in-memory SQLite DB."""
    return _ingest_into(make_sqlite_engine(), data_dir, as_of_override)


def ingest_postgres(data_dir: Path, as_of_override: date | None = None) -> tuple[Repository, date]:
    """Postgres write path: persist facts + derived state to the configured DB.

    Returns a read repository over the freshly-written state (for the CLI summary).
    """
    return _ingest_into(make_engine(), data_dir, as_of_override)


def open_postgres_repository() -> tuple[Repository, date]:
    """Postgres read path for the API: connect and read; do not re-derive."""
    engine = make_engine()
    factory = make_session_factory(engine)
    with factory() as session:
        as_of = latest_as_of(session)
    if as_of is None:
        raise RuntimeError(
            "No pipeline run found in the database. "
            "Run `uv run ingest --backend postgres` first."
        )
    return SqlRepository(factory), as_of
