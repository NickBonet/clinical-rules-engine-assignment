"""Storage interface and SQL implementation for SQLite and Postgres."""

from app.repository.base import Repository
from app.repository.sql import SqlRepository

__all__ = ["Repository", "SqlRepository"]
