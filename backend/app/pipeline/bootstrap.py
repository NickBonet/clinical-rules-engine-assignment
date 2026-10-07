"""Build a fully-evaluated repository from the CSVs in one call.

Used by both the CLI and the API startup. Returns the in-memory repository today;
swapping in a SQLAlchemy repository later is a one-line change here.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.pipeline.as_of import resolve_as_of
from app.pipeline.ingest import all_labs, load_contexts
from app.pipeline.orchestrator import run_all
from app.repository import InMemoryRepository, Repository


def build_repository(data_dir: Path, as_of_override: date | None = None) -> tuple[Repository, date]:
    contexts = load_contexts(data_dir)
    as_of = resolve_as_of(all_labs(contexts), as_of_override)
    repo = InMemoryRepository(contexts)
    run_all(as_of, repo)
    return repo, as_of
