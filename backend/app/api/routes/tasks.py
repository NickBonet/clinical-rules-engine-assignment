"""Role-visible task endpoints."""

from fastapi import APIRouter

from app.api.dependencies import (
    RepositoryDependency,
    SpecialtyFilter,
    TaskTypeFilter,
    VisibleTaskTypes,
)
from app.api.schemas import TaskResponse

router = APIRouter(tags=["Tasks"])


@router.get("/tasks", summary="List role-visible tasks")
def list_tasks(
    repo: RepositoryDependency,
    allowed_task_types: VisibleTaskTypes,
    specialty: SpecialtyFilter = None,
    task_type: TaskTypeFilter = None,
) -> list[TaskResponse]:
    """List tasks visible to the role, with optional specialty and type filters."""
    tasks = repo.list_tasks(
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=allowed_task_types,
    )
    return [TaskResponse.model_validate(task) for task in tasks]
