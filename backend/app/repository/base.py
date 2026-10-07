"""Storage interface used by the pipeline and API.

Callers work with domain dataclasses rather than database rows.
"""

from __future__ import annotations

from typing import Protocol

from app.domain import Enrollment, PatientContext, Task


class Repository(Protocol):
    def patient_ids(self) -> list[str]: ...
    def load_patient_context(self, patient_id: str) -> PatientContext: ...

    def replace_derived_state(
        self, patient_id: str, enrollments: list[Enrollment], tasks: list[Task]
    ) -> None:
        """Replace a patient's enrollments and tasks in one transaction.

        Repeating the same write must not create duplicates.
        """
        ...

    def list_enrollments(self) -> list[Enrollment]: ...
    def list_tasks(
        self,
        *,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> list[Task]: ...
