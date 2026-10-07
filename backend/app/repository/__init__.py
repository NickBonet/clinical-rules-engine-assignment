"""Storage layer. Depends on `app.domain`; accessed behind the `Repository` Protocol.

`SqlRepository` (SQLAlchemy) is the single implementation, used for both the
ephemeral in-memory SQLite backend and the persistent Postgres backend.
"""

from app.repository.base import Repository
from app.repository.sql import SqlRepository

__all__ = ["Repository", "SqlRepository"]
