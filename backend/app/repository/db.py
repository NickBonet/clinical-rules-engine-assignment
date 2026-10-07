"""Engine, session factory, and schema creation for the SQL backend."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.repository.models import Base


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or settings.database_url, future=True)


def make_sqlite_engine() -> Engine:
    """Create an in-memory SQLite database shared across sessions.

    StaticPool keeps sessions on the same connection so they see the same data.
    Allow access from FastAPI's worker threads and enable foreign key checks,
    which SQLite disables by default.
    """
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _record):  # pragma: no cover - driver hook
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    # Keep loaded row attributes available after a commit.
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)
