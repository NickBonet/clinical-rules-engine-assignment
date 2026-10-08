"""Patient population endpoints."""

from fastapi import APIRouter, Query

from app.api.dependencies import (
    RepositoryDependency,
    SpecialtyFilter,
    TaskTypeFilter,
    VisibleTaskTypes,
)
from app.api.schemas import (
    EnrollmentResponse,
    PatientPageResponse,
    PatientResponse,
    TaskResponse,
)
from app.domain import Enrollment, Task

router = APIRouter(tags=["Patients"])


@router.get("/patients", summary="List patients and role-visible tasks")
def list_patients(
    repo: RepositoryDependency,
    allowed_task_types: VisibleTaskTypes,
    specialty: SpecialtyFilter = None,
    task_type: TaskTypeFilter = None,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum patients to return."),
    cursor: str | None = Query(
        default=None, min_length=1, description="Patient ID to continue after."
    ),
) -> PatientPageResponse:
    """List patients with their enrollments, risk tiers, and role-visible tasks.

    Tasks are always restricted to the selected role's visibility.
    Specialty and task-type filters further narrow those tasks and return only
    patients with a matching visible task. Without these filters, include patients
    with an enrollment or a role-visible task; enrolled patients may have an empty
    task list.
    """
    page = repo.list_patient_id_page(
        limit=limit,
        cursor=cursor,
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=allowed_task_types,
    )
    tasks = repo.list_tasks(
        patient_ids=page.items,
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=allowed_task_types,
    )
    tasks_by_patient: dict[str, list[Task]] = {}
    for task in tasks:
        tasks_by_patient.setdefault(task.patient_id, []).append(task)

    enrollments_by_patient: dict[str, list[Enrollment]] = {}
    for enrollment in repo.list_enrollments(patient_ids=page.items):
        enrollments_by_patient.setdefault(enrollment.patient_id, []).append(enrollment)

    patients = []
    for patient_id in page.items:
        patient_tasks = tasks_by_patient.get(patient_id, [])
        enrollments = enrollments_by_patient.get(patient_id, [])
        patients.append(
            PatientResponse(
                patient_id=patient_id,
                enrollments=[EnrollmentResponse.model_validate(entry) for entry in enrollments],
                tasks=[TaskResponse.model_validate(task) for task in patient_tasks],
            )
        )
    return PatientPageResponse(items=patients, next_cursor=page.next_cursor)
