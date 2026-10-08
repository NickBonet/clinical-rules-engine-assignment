"""Patient and task endpoints, with specialty, task-type, and role filters.

SQLite loads CSV data at startup; Postgres reads previously ingested results.
Rule evaluation stays in the engine and pipeline, not the routes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, patients, specialties, tasks
from app.config import settings
from app.pipeline.bootstrap import build_sqlite_repository, open_postgres_repository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Postgres requires an earlier ingest; SQLite builds its data at startup.
    if settings.backend == "postgres":
        repo, as_of = open_postgres_repository()
    else:
        repo, as_of = build_sqlite_repository(settings.data_dir, settings.as_of)
    app.state.repo = repo
    app.state.as_of = as_of
    yield


app = FastAPI(title="Clinical Rules Engine", lifespan=lifespan, root_path=settings.root_path)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


app.include_router(health.router)
app.include_router(patients.router)
app.include_router(specialties.router)
app.include_router(tasks.router)
