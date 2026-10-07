"""Choose one evaluation date for the run, using an override or the latest lab date.

For the supplied data, the latest lab date keeps A1C results in the 180-day window
and leaves later encounters as upcoming visits.
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
