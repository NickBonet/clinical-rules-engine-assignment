"""Primary Care Wellness rules and visit needs."""

from __future__ import annotations

from datetime import date

from app.domain import Need, PatientContext
from app.engine.programs.base import ProgramRule, _visit

# Diagnosis prefixes that trigger High Priority.
# G47.3 covers the sleep apnea family; the other prefixes are ICD-10 roots.
WELLNESS_CHRONIC_PREFIXES: tuple[str, ...] = (
    "E10", "E11", "I10", "E78", "J45", "N18", "I25", "E03", "G47.3", "M81",
)


class PrimaryCareWellnessProgram(ProgramRule):
    name = "Primary Care Wellness"

    def is_eligible(self, ctx: PatientContext, as_of: date) -> bool:
        return ctx.patient.age_at(as_of) >= 18

    def determine_risk(self, ctx: PatientContext, as_of: date) -> str:
        high = (
            ctx.patient.age_at(as_of) >= 65
            or ctx.has_diagnosis_prefix(WELLNESS_CHRONIC_PREFIXES, as_of)
        )
        return "High Priority" if high else "Standard"

    def build_needs(self, ctx: PatientContext, risk_tier: str) -> tuple[Need, ...]:
        if risk_tier == "High Priority":
            cadence = 180
        elif risk_tier == "Standard":
            cadence = 365
        else:
            raise ValueError(f"Unknown Primary Care Wellness risk tier: {risk_tier!r}")
        return (_visit(self.name, "PCP", cadence),)