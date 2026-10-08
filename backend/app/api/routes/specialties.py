"""Role-visible specialty endpoints."""

from fastapi import APIRouter

from app.api.dependencies import RepositoryDependency, VisibleTaskTypes

router = APIRouter(tags=["Specialties"])


@router.get("/specialties", summary="List role-visible specialties")
def list_specialties(
    repo: RepositoryDependency,
    allowed_task_types: VisibleTaskTypes,
) -> list[str]:
    """Return sorted distinct specialties with a task the role can see."""
    tasks = repo.list_tasks(allowed_task_types=allowed_task_types)
    return sorted({task.specialty for task in tasks if task.specialty is not None})
