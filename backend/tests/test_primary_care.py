"""Primary Care Wellness: eligibility, stratification, and cadence.

Spec: all patients 18+; High Priority if age >= 65 OR any chronic diagnosis
(cadence 180 days), otherwise Standard (365 days).
"""

from __future__ import annotations

from datetime import date

import pytest

from app.engine.programs.primary_care import PrimaryCareWellnessProgram
from tests.builders import AS_OF, context, days_after, days_before, diagnosis

program = PrimaryCareWellnessProgram()


# --- Eligibility: age >= 18 ------------------------------------------------
@pytest.mark.parametrize(
    "age, eligible",
    [(17, False), (18, True), (40, True), (90, True)],
)
def test_eligibility_by_age(age: int, eligible: bool) -> None:
    assert program.is_eligible(context(age=age), AS_OF) is eligible


@pytest.mark.parametrize(
    "evaluation_date, eligible",
    [(days_before(1), False), (days_after(1), True)],
)
def test_eligibility_around_eighteenth_birthday(evaluation_date: date, eligible: bool) -> None:
    ctx = context(age=18)
    assert program.is_eligible(ctx, evaluation_date) is eligible


# --- Stratification --------------------------------------------------------
def test_standard_tier_for_young_patient_without_chronic_dx() -> None:
    assert program.determine_risk(context(age=40), AS_OF) == "Standard"


def test_high_priority_at_age_65() -> None:
    assert program.determine_risk(context(age=65), AS_OF) == "High Priority"


def test_age_64_is_standard() -> None:
    assert program.determine_risk(context(age=64), AS_OF) == "Standard"


@pytest.mark.parametrize(
    "evaluation_date, tier",
    [(days_before(1), "Standard"), (days_after(1), "High Priority")],
)
def test_priority_around_sixty_fifth_birthday(evaluation_date: date, tier: str) -> None:
    ctx = context(age=65)
    assert program.determine_risk(ctx, evaluation_date) == tier


@pytest.mark.parametrize(
    "icd_code",
    ["E10.9", "E11.65", "I10", "E78.5", "J45.909", "N18.3",
     "I25.10", "E03.9", "G47.33", "M81.0"],
)
def test_high_priority_for_any_chronic_condition(icd_code: str) -> None:
    ctx = context(age=30, diagnoses=(diagnosis(icd_code),))
    assert program.determine_risk(ctx, AS_OF) == "High Priority"


def test_unrelated_diagnosis_stays_standard() -> None:
    # Not in the chronic group: a prefix that merely starts similarly must not match.
    ctx = context(age=30, diagnoses=(diagnosis("Z00.00"), diagnosis("G47.00")))
    assert program.determine_risk(ctx, AS_OF) == "Standard"


# --- Cadence ---------------------------------------------------------------
def test_high_priority_cadence_is_180() -> None:
    needs = program.build_needs(context(age=70), "High Priority")
    assert [(n.specialty, n.cadence_days) for n in needs] == [("PCP", 180)]


def test_standard_cadence_is_365() -> None:
    needs = program.build_needs(context(age=40), "Standard")
    assert [(n.specialty, n.cadence_days) for n in needs] == [("PCP", 365)]


def test_pcp_need_is_not_specialist() -> None:
    (need,) = program.build_needs(context(), "Standard")
    assert need.is_specialist is False
    assert need.need_type == "visit_cadence"
