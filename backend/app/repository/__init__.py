"""Storage layer. Depends on `app.domain`; swappable behind the `Repository` Protocol.

TODO: add a SQLAlchemy/Postgres implementation (`sql.py`) alongside `memory.py`.
"""

from app.repository.base import Repository
from app.repository.memory import InMemoryRepository

__all__ = ["InMemoryRepository", "Repository"]
