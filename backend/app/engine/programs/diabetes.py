"""Diabetes Management rules and visit needs."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain import Need, PatientContext
from app.engine.programs.base import ProgramRule, _visit

# Treat "within the last 6 months" as 180 days, including the cutoff date.
A1C_WINDOW_DAYS = 180

DIABETES_PREFIXES: tuple[str, ...] = ("E10", "E11")

# Visit specialties and cadences for each risk tier, from the spec.
_DIABETES_NEEDS: dict[str, tuple[tuple[str, int], ...]] = {
    "High Risk": (
        ("Endocrinology", 90),
        ("Cardiology", 90),
        ("Podiatry", 180),
        ("Ophthalmology", 365),
        ("Nephrology", 180),
    ),
    "Moderate Risk": (
        ("Endocrinology", 180),
        ("Ophthalmology", 365),
        ("Podiatry", 365),
    ),
    "Low Risk": (
        ("Endocrinology", 365),
        ("Ophthalmology", 365),
    ),
    "Unmonitored": (
        ("Endocrinology", 90),
    ),
}


class DiabetesManagementProgram(ProgramRule):
    name = "Diabetes Management"

    def is_eligible(self, ctx: PatientContext, as_of: date) -> bool:
        return ctx.has_diagnosis_prefix(DIABETES_PREFIXES)

    def determine_risk(self, ctx: PatientContext, as_of: date) -> str:
        a1c = self._most_recent_a1c(ctx, as_of)
        if a1c is None:
            return "Unmonitored"
        if a1c >= 9.0:
            return "High Risk"
        if a1c >= 7.0:
            return "Moderate Risk"
        return "Low Risk"

    def build_needs(self, ctx: PatientContext, risk_tier: str) -> tuple[Need, ...]:
        specs = _DIABETES_NEEDS[risk_tier]
        return tuple(_visit(self.name, specialty, cadence) for specialty, cadence in specs)

    def _most_recent_a1c(self, ctx: PatientContext, as_of: date) -> float | None:
        """Latest A1C in the window; use the higher value when dates tie."""
        window_start = as_of - timedelta(days=A1C_WINDOW_DAYS)
        in_window = [
            lab for lab in ctx.labs
            if lab.test_name == "A1C" and window_start <= lab.result_date <= as_of
        ]
        if not in_window:
            return None
        best = max(in_window, key=lambda lab: (lab.result_date, lab.result_value))
        return best.result_value