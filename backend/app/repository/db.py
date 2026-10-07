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
    """In-process, in-memory SQLite shared across sessions.

    A plain `sqlite://` URL gives each new connection its own empty database, so
    with per-operation sessions a write and a later read would hit different DBs.
    `StaticPool` pins a single shared connection (hence `check_same_thread=False`
    for FastAPI's threadpool), making one ephemeral database live for the process.
    Foreign keys are enabled per connection for parity with Postgres (SQLite
    leaves them off by default).
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
    # expire_on_commit=False: domain objects are built from row attributes before
    # the session closes, so we never touch expired attributes post-commit.
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)
