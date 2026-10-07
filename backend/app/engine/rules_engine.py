"""Evaluate the configured programs for one patient."""

from __future__ import annotations

from datetime import date

from app.domain import Enrollment, PatientContext
from app.engine.programs import ProgramRule, default_programs


class RulesEngine:
    def __init__(self, programs: tuple[ProgramRule, ...] | None = None) -> None:
        self.programs = programs if programs is not None else default_programs()

    def evaluate_patient(self, ctx: PatientContext, as_of: date) -> tuple[Enrollment, ...]:
        """Return an enrollment for each eligible program, evaluated independently."""
        enrollments: list[Enrollment] = []
        for program in self.programs:
            if not program.is_eligible(ctx, as_of):
                continue
            risk = program.determine_risk(ctx, as_of)
            needs = program.build_needs(ctx, risk)
            enrollments.append(
                Enrollment(
                    patient_id=ctx.patient_id,
                    program=program.name,
                    risk_tier=risk,
                    needs=needs,
                )
            )
        return tuple(enrollments)
