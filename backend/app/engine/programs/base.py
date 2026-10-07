"""Shared program contract and visit-need construction."""

from __future__ import annotations

from datetime import date

from app.domain import Need, PatientContext


def _visit(program: str, specialty: str, cadence_days: int) -> Need:
    return Need(
        program=program,
        need_type="visit_cadence",
        specialty=specialty,
        cadence_days=cadence_days,
        is_specialist=specialty != "PCP",
    )


class ProgramRule:
    """Base class. Subclasses implement the three pure steps."""

    name: str

    def is_eligible(self, ctx: PatientContext, as_of: date) -> bool:
        raise NotImplementedError

    def determine_risk(self, ctx: PatientContext, as_of: date) -> str:
        raise NotImplementedError

    def build_needs(self, ctx: PatientContext, risk_tier: str) -> tuple[Need, ...]:
        raise NotImplementedError