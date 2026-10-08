"""Role-visible task endpoints."""

from fastapi import APIRouter, Query

from app.api.dependencies import (
    RepositoryDependency,
    SpecialtyFilter,
    TaskTypeFilter,
    VisibleTaskTypes,
)
from app.api.schemas import TaskPageResponse, TaskResponse

router = APIRouter(tags=["Tasks"])


@router.get("/tasks", summary="List role-visible tasks")
def list_tasks(
    repo: RepositoryDependency,
    allowed_task_types: VisibleTaskTypes,
    specialty: SpecialtyFilter = None,
    task_type: TaskTypeFilter = None,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum tasks to return."),
    cursor: int | None = Query(default=None, ge=0, description="Task ID to continue after."),
) -> TaskPageResponse:
    """List tasks visible to the role, with optional specialty and type filters."""
    page = repo.list_task_page(
        limit=limit,
        cursor=cursor,
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=allowed_task_types,
    )
    return TaskPageResponse(
        items=[TaskResponse.model_validate(task) for task in page.items],
        next_cursor=page.next_cursor,
    )
