"""Primary Care Wellness eligibility, risk stratification, and visit needs."""

from __future__ import annotations

from datetime import date

from app.domain import Need, PatientContext
from app.engine.programs.base import ProgramRule, _visit

# Chronic-conditions group for the Primary Care Wellness high-priority check.
# ICD-10 prefixes; G47.3 is intentionally the 4-char family, the rest are roots.
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
            or ctx.has_diagnosis_prefix(WELLNESS_CHRONIC_PREFIXES)
        )
        return "High Priority" if high else "Standard"

    def build_needs(self, ctx: PatientContext, risk_tier: str) -> tuple[Need, ...]:
        cadence = 180 if risk_tier == "High Priority" else 365
        return (_visit(self.name, "PCP", cadence),)