"""CLI entrypoint: `uv run ingest [--as-of YYYY-MM-DD]`.

Rebuilds derived state from the CSVs and prints a summary. With the in-memory
repository this is a dry run; once a persistent repository is wired in, the same
call will populate the database.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from app.config import settings
from app.pipeline.bootstrap import build_repository


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate rules and generate tasks from the CSVs.")
    parser.add_argument("--as-of", type=date.fromisoformat, default=settings.as_of,
                        help="Reference date (YYYY-MM-DD). Default: max lab result_date.")
    parser.add_argument("--data-dir", type=Path, default=settings.data_dir)
    args = parser.parse_args()

    repo, as_of = build_repository(args.data_dir, args.as_of)

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
