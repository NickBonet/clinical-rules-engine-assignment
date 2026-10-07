"""CLI entrypoint: `uv run ingest [--as-of YYYY-MM-DD] [--backend sqlite|postgres]`.

Rebuilds derived state from the CSVs and prints a summary. With `sqlite` (default)
this is an ephemeral dry run; with `postgres` the same call populates the database.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from app.config import settings
from app.pipeline.bootstrap import build_sqlite_repository, ingest_postgres


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate rules and generate tasks from the CSVs.")
    parser.add_argument("--as-of", type=date.fromisoformat, default=settings.as_of,
                        help="Reference date (YYYY-MM-DD). Default: max lab result_date.")
    parser.add_argument("--data-dir", type=Path, default=settings.data_dir)
    parser.add_argument("--backend", choices=("sqlite", "postgres"), default=settings.backend,
                        help="sqlite = ephemeral dry run (no setup); postgres = persist to the database.")
    args = parser.parse_args()

    if args.backend == "postgres":
        repo, as_of = ingest_postgres(args.data_dir, args.as_of)
    else:
        repo, as_of = build_sqlite_repository(args.data_dir, args.as_of)

    enrollments = repo.list_enrollments()
    tasks = repo.list_tasks()
    by_program = Counter(e.program for e in enrollments)
    by_task_type = Counter(str(t.task_type) for t in tasks)

    print(f"as_of = {as_of.isoformat()}")
    print(f"patients: {len(repo.patient_ids())}")
    print(f"enrollments: {dict(by_program)}")
    print(f"tasks: {dict(by_task_type)} (total {len(tasks)})")


if __name__ == "__main__":
    main()
