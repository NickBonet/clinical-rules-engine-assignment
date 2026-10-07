"""Patient and task endpoints, with specialty, task-type, and role filters.

SQLite loads CSV data at startup; Postgres reads previously ingested results.
Rule evaluation stays in the engine and pipeline, not the routes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.domain import TaskType
from app.pipeline.bootstrap import build_sqlite_repository, open_postgres_repository

# Task types visible to each role.
_ROLE_VISIBILITY: dict[str, tuple[str, ...]] = {
    "scheduler": (TaskType.SCHEDULING,),
    "clinical": (TaskType.SCHEDULING, TaskType.REFERRAL),
}


class Role(StrEnum):
    SCHEDULER = "scheduler"
    CLINICAL = "clinical"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Postgres requires an earlier ingest; SQLite builds its data at startup.
    if settings.backend == "postgres":
        repo, as_of = open_postgres_repository()
    else:
        repo, as_of = build_sqlite_repository(settings.data_dir, settings.as_of)
    app.state.repo = repo
    app.state.as_of = as_of
    yield


app = FastAPI(title="Clinical Rules Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def _task_dict(t) -> dict:
    return {
        "patient_id": t.patient_id,
        "program": t.program,
        "need_type": t.need_type,
        "specialty": t.specialty,
        "task_type": str(t.task_type),
        "reason": t.reason,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "as_of": app.state.as_of.isoformat()}


@app.get("/patients")
def list_patients() -> list[dict]:
    """List patients with their enrollments, risk tiers, and tasks."""
    repo = app.state.repo
    tasks_by_patient: dict[str, list] = {}
    for t in repo.list_tasks():
        tasks_by_patient.setdefault(t.patient_id, []).append(t)

    enrollments_by_patient: dict[str, list] = {}
    for e in repo.list_enrollments():
        enrollments_by_patient.setdefault(e.patient_id, []).append(e)

    out = []
    for pid in repo.patient_ids():
        enrollments = enrollments_by_patient.get(pid, [])
        if not enrollments and pid not in tasks_by_patient:
            continue
        out.append({
            "patient_id": pid,
            "enrollments": [
                {"program": e.program, "risk_tier": e.risk_tier} for e in enrollments
            ],
            "tasks": [_task_dict(t) for t in tasks_by_patient.get(pid, [])],
        })
    return out


@app.get("/tasks")
def list_tasks(
    role: Annotated[
        Role, Query(description="scheduler sees scheduling only; clinical sees both")
    ] = Role.CLINICAL,
    specialty: Annotated[str | None, Query()] = None,
    task_type: Annotated[TaskType | None, Query()] = None,
) -> list[dict]:
    """List tasks visible to the role, with optional specialty and type filters."""
    repo = app.state.repo
    tasks = repo.list_tasks(
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=_ROLE_VISIBILITY[role],
    )
    return [_task_dict(t) for t in tasks]
