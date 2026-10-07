"""FastAPI app. Serves patient/task data with specialty, task-type, and role
filters. Role visibility boils down to what task types are mapped for each role in `_ROLE_VISIBILITY`.

On startup, the app builds the repository from the CSVs (in-memory currently, Postgres pending). Business
logic stays in the engine/pipeline, while routes only deal with query parameters and response shaping.
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

# Role -> task types that role may see.
_ROLE_VISIBILITY: dict[str, tuple[str, ...]] = {
    "scheduler": (TaskType.SCHEDULING,),
    "clinical": (TaskType.SCHEDULING, TaskType.REFERRAL),
}


class Role(StrEnum):
    SCHEDULER = "scheduler"
    CLINICAL = "clinical"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # postgres: read already-ingested state (run `ingest --backend postgres` first).
    # sqlite: ingest + evaluate into an ephemeral in-memory DB on startup.
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
    """Patients with their program enrollments, risk tiers, and active tasks."""
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
    """Filter by specialty and/or task type, scoped to the role's visibility."""
    repo = app.state.repo
    tasks = repo.list_tasks(
        specialty=specialty,
        task_type=str(task_type) if task_type else None,
        allowed_task_types=_ROLE_VISIBILITY[role],
    )
    return [_task_dict(t) for t in tasks]
