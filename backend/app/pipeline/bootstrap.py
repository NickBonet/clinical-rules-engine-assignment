"""Set up storage for ingestion or API startup.

SQLite loads and evaluates data in memory. Postgres stores ingestion results
for the API to read later. Both use SqlRepository and return the evaluation date.
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
    """Create tables, load patient data, evaluate rules, and record the run."""
    create_schema(engine)
    factory = make_session_factory(engine)

    contexts = load_contexts(data_dir)
    as_of = resolve_as_of(all_labs(contexts), as_of_override)

    with factory() as session:
        write_facts(session, contexts)

    repo = SqlRepository(factory)
    run_all(as_of, repo)  # Each patient's results are saved in a separate transaction.

    with factory() as session:
        record_run(session, as_of)

    return repo, as_of


def build_sqlite_repository(data_dir: Path, as_of_override: date | None = None) -> tuple[Repository, date]:
    """Load and evaluate CSV data in an in-memory SQLite database."""
    return _ingest_into(make_sqlite_engine(), data_dir, as_of_override)


def ingest_postgres(data_dir: Path, as_of_override: date | None = None) -> tuple[Repository, date]:
    """Load and evaluate CSV data in the configured Postgres database.

    Return the repository and evaluation date for the CLI summary.
    """
    return _ingest_into(make_engine(), data_dir, as_of_override)


def open_postgres_repository() -> tuple[Repository, date]:
    """Open stored Postgres results for the API without rerunning the pipeline."""
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
