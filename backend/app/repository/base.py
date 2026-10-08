"""Storage interface used by the pipeline and API.

Callers work with domain dataclasses rather than database rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from app.domain import Enrollment, PatientContext, Task

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    next_cursor: int | str | None


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

    def list_patient_id_page(
        self,
        *,
        limit: int,
        cursor: str | None = None,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> Page[str]: ...
    def list_enrollments(self, *, patient_ids: list[str] | None = None) -> list[Enrollment]: ...
    def list_tasks(
        self,
        *,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
        patient_ids: list[str] | None = None,
    ) -> list[Task]: ...
    def list_task_page(
        self,
        *,
        limit: int,
        cursor: int | None = None,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> Page[Task]: ...
