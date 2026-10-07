"""Resolve the single reference ("as-of") date threaded through all evaluation.

Default = max(lab result_date): the latest lab guarantees at least one A1C inside
the 180-day window while leaving later encounters as "future" (see architecture
doc). An explicit override wins.
"""

from __future__ import annotations

from datetime import date

from app.domain import LabResult


def resolve_as_of(labs: list[LabResult], override: date | None = None) -> date:
    if override is not None:
        return override
    if not labs:
        raise ValueError("Cannot derive as_of: no lab results. Pass an explicit --as-of.")
    return max(lab.result_date for lab in labs)
