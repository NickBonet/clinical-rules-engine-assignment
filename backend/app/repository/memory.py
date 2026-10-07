"""In-memory Repository implementation.

Lets the pipeline, API, and frontend run end-to-end with zero database. The
SQLAlchemy/Postgres implementation is a drop-in replacement behind the same
Protocol (see repository/base.py).
"""

from __future__ import annotations

from app.domain import Enrollment, PatientContext, Task


class InMemoryRepository:
    def __init__(self, contexts: dict[str, PatientContext]) -> None:
        self._contexts = contexts
        self._enrollments: dict[str, list[Enrollment]] = {}
        self._tasks: dict[str, list[Task]] = {}

    # --- facts ------------------------------------------------------------
    def patient_ids(self) -> list[str]:
        return list(self._contexts)

    def load_patient_context(self, patient_id: str) -> PatientContext:
        return self._contexts[patient_id]

    # --- derived state (write) -------------------------------------------
    def replace_derived_state(
        self, patient_id: str, enrollments: list[Enrollment], tasks: list[Task]
    ) -> None:
        self._enrollments[patient_id] = list(enrollments)
        self._tasks[patient_id] = list(tasks)

    # --- derived state (read) --------------------------------------------
    def list_enrollments(self) -> list[Enrollment]:
        return [e for group in self._enrollments.values() for e in group]

    def list_tasks(
        self,
        *,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> list[Task]:
        out = [t for group in self._tasks.values() for t in group]
        if specialty is not None:
            out = [t for t in out if t.specialty == specialty]
        if task_type is not None:
            out = [t for t in out if t.task_type == task_type]
        if allowed_task_types is not None:
            out = [t for t in out if t.task_type in allowed_task_types]
        return out
