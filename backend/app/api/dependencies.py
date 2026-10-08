"""Shared request dependencies and documented query parameters."""

from datetime import date
from enum import StrEnum
from typing import Annotated, cast

from fastapi import Depends, Query, Request

from app.domain import TaskType
from app.repository import Repository


class Role(StrEnum):
    SCHEDULER = "scheduler"
    CLINICAL = "clinical"


_ROLE_VISIBILITY: dict[Role, tuple[str, ...]] = {
    Role.SCHEDULER: (TaskType.SCHEDULING,),
    Role.CLINICAL: (TaskType.SCHEDULING, TaskType.REFERRAL),
}


def get_repository(request: Request) -> Repository:
    return cast(Repository, request.app.state.repo)


def get_as_of(request: Request) -> date:
    return cast(date, request.app.state.as_of)


def get_visible_task_types(
    role: Annotated[
        Role, Query(description="scheduler sees scheduling only; clinical sees both")
    ] = Role.CLINICAL,
) -> tuple[str, ...]:
    return _ROLE_VISIBILITY[role]


RepositoryDependency = Annotated[Repository, Depends(get_repository)]
AsOfDependency = Annotated[date, Depends(get_as_of)]
VisibleTaskTypes = Annotated[tuple[str, ...], Depends(get_visible_task_types)]
SpecialtyFilter = Annotated[
    str | None, Query(description="Exact specialty name to filter visible tasks.")
]
TaskTypeFilter = Annotated[
    TaskType | None, Query(description="Task type to filter within the role's visibility.")
]
