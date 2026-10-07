"""Repository interface — the single I/O seam between the application(s) and storage.

The pipeline and API depend on this Protocol, not on a concrete backend, so the
in-memory implementation (now) and a SQLAlchemy/Postgres one (later) are
interchangeable. `load_patient_context` + `replace_derived_state` are exactly the
two calls the TaskIQ-ready `run_patient` seam needs.
"""

from __future__ import annotations

from typing import Protocol

from app.domain import Enrollment, PatientContext, Task


class Repository(Protocol):
    # --- facts (read) -----------------------------------------------------
    def patient_ids(self) -> list[str]: ...
    def load_patient_context(self, patient_id: str) -> PatientContext: ...

    # --- derived state (write) -------------------------------------------
    def replace_derived_state(
        self, patient_id: str, enrollments: list[Enrollment], tasks: list[Task]
    ) -> None:
        """Idempotently replace this patient's enrollments + tasks (per-patient
        transaction), so a retried job yields identical state."""
        ...

    # --- derived state (read, for the API) -------------------------------
    def list_enrollments(self) -> list[Enrollment]: ...
    def list_tasks(
        self,
        *,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> list[Task]: ...
