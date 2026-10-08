"""Patient population endpoints."""

from fastapi import APIRouter

from app.api.dependencies import (
    RepositoryDependency,
    SpecialtyFilter,
    TaskTypeFilter,
    VisibleTaskTypes,
)
from app.api.schemas import EnrollmentResponse, PatientResponse, TaskResponse
from app.domain import Enrollment, Task

router = APIRouter(tags=["Patients"])


@router.get("/patients", summary="List patients and role-visible tasks")
def list_patients(
    repo: RepositoryDependency,
    allowed_task_types: VisibleTaskTypes,
    specialty: SpecialtyFilter = None,
    task_type: TaskTypeFilter = None,
) -> list[PatientResponse]:
    """List patients with their enrollments, risk tiers, and role-visible tasks.

    Tasks are always restricted to the selected role's visibility.
    Specialty and task-type filters further narrow those tasks and return only
    patients with a matching visible task. Without these filters, include patients
    with an enrollment or a role-visible task; enrolled patients may have an empty
    task list.
    """
    tasks = repo.list_tasks(
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=allowed_task_types,
    )
    tasks_by_patient: dict[str, list[Task]] = {}
    for task in tasks:
        tasks_by_patient.setdefault(task.patient_id, []).append(task)

    enrollments_by_patient: dict[str, list[Enrollment]] = {}
    for enrollment in repo.list_enrollments():
        enrollments_by_patient.setdefault(enrollment.patient_id, []).append(enrollment)

    filtering = specialty is not None or task_type is not None
    patients = []
    for patient_id in repo.patient_ids():
        patient_tasks = tasks_by_patient.get(patient_id, [])
        enrollments = enrollments_by_patient.get(patient_id, [])
        if filtering:
            if not patient_tasks:
                continue
        elif not enrollments and not patient_tasks:
            continue
        patients.append(
            PatientResponse(
                patient_id=patient_id,
                enrollments=[EnrollmentResponse.model_validate(entry) for entry in enrollments],
                tasks=[TaskResponse.model_validate(task) for task in patient_tasks],
            )
        )
    return patients
