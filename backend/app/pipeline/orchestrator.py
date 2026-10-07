"""Load each patient's data, evaluate rules, and save enrollments and tasks.

Patients are processed independently, so the loop can later move to a worker queue.
"""

from __future__ import annotations

from datetime import date

from app.engine import RulesEngine, generate_task
from app.repository import Repository

_engine = RulesEngine()


def run_patient(patient_id: str, as_of: date, repo: Repository) -> None:
    ctx = _engine_context(patient_id, repo)
    enrollments = list(_engine.evaluate_patient(ctx, as_of))

    tasks = []
    for enrollment in enrollments:
        for need in enrollment.needs:
            task = generate_task(need, ctx, as_of)
            if task is not None:
                tasks.append(task)

    repo.replace_derived_state(patient_id, enrollments, tasks)


def run_all(as_of: date, repo: Repository) -> None:
    for patient_id in repo.patient_ids():
        run_patient(patient_id, as_of, repo)


def _engine_context(patient_id: str, repo: Repository):
    return repo.load_patient_context(patient_id)
