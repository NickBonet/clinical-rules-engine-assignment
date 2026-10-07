"""Diabetes Management: eligibility, A1C risk tiers, and per-tier needs.

Spec: eligible on an E10.x (Type 1) or E11.x (Type 2) diagnosis. Risk uses the
most recent A1C within the last 6 months (treated as 180 days):
    >= 9.0 High Risk, at least 7.0 and below 9.0 Moderate, < 7.0 Low, none-in-window Unmonitored.
"""

from __future__ import annotations

import pytest

from app.engine.programs.diabetes import DiabetesManagementProgram
from tests.builders import AS_OF, a1c, context, days_after, days_before, diagnosis

program = DiabetesManagementProgram()


def dm_context(labs=(), *, dx: str = "E11.9"):
    return context(age=50, diagnoses=(diagnosis(dx),), labs=labs)


# --- Eligibility -----------------------------------------------------------
@pytest.mark.parametrize("icd_code", ["E10.9", "E11.65", "E10", "E11.8"])
def test_eligible_on_diabetes_diagnosis(icd_code: str) -> None:
    ctx = context(age=50, diagnoses=(diagnosis(icd_code),))
    assert program.is_eligible(ctx, AS_OF) is True


@pytest.mark.parametrize("icd_code", ["I10", "E78.5", "E03.9"])
def test_not_eligible_without_diabetes_diagnosis(icd_code: str) -> None:
    ctx = context(age=50, diagnoses=(diagnosis(icd_code),))
    assert program.is_eligible(ctx, AS_OF) is False


def test_not_eligible_with_no_diagnoses() -> None:
    assert program.is_eligible(context(age=50), AS_OF) is False


# --- Risk tier boundaries --------------------------------------------------
@pytest.mark.parametrize(
    "value, tier",
    [
        (9.0, "High Risk"),    # boundary: >= 9.0
        (9.5, "High Risk"),
        (8.999, "Moderate Risk"),  # just below High
        (7.0, "Moderate Risk"),  # boundary: >= 7.0
        (6.9, "Low Risk"),       # just below Moderate
        (5.0, "Low Risk"),
    ],
)
def test_risk_tier_by_a1c_value(value: float, tier: str) -> None:
    ctx = dm_context(labs=(a1c(value, result_date=days_before(10)),))
    assert program.determine_risk(ctx, AS_OF) == tier


def test_unmonitored_when_no_a1c_at_all() -> None:
    assert program.determine_risk(dm_context(), AS_OF) == "Unmonitored"


def test_unmonitored_when_only_a1c_is_outside_window() -> None:
    # One day past the 6-month window: no longer counts, so Unmonitored.
    stale = a1c(10.0, result_date=days_before(181))
    assert program.determine_risk(dm_context(labs=(stale,)), AS_OF) == "Unmonitored"


def test_a1c_exactly_on_window_edge_still_counts() -> None:
    edge = a1c(9.0, result_date=days_before(180))
    assert program.determine_risk(dm_context(labs=(edge,)), AS_OF) == "High Risk"


def test_unmonitored_when_only_a1c_is_in_the_future() -> None:
    future = a1c(10.0, result_date=days_after(1))
    assert program.determine_risk(dm_context(labs=(future,)), AS_OF) == "Unmonitored"


def test_future_a1c_does_not_override_recent_result() -> None:
    labs = (
        a1c(6.5, result_date=days_before(5)),
        a1c(10.0, result_date=days_after(1)),
    )
    assert program.determine_risk(dm_context(labs=labs), AS_OF) == "Low Risk"


def test_a1c_on_as_of_counts() -> None:
    result = a1c(9.0, result_date=AS_OF)
    assert program.determine_risk(dm_context(labs=(result,)), AS_OF) == "High Risk"


# --- "Most recent" selection ----------------------------------------------
def test_uses_most_recent_a1c_not_the_worst() -> None:
    # An old high value must not override a recent controlled one.
    labs = (
        a1c(6.5, result_date=days_before(5)),
        a1c(10.0, result_date=days_before(120)),
    )
    assert program.determine_risk(dm_context(labs=labs), AS_OF) == "Low Risk"


def test_same_date_tie_breaks_to_higher_value() -> None:
    same_day = days_before(10)
    labs = (a1c(9.2, result_date=same_day), a1c(6.0, result_date=same_day))
    assert program.determine_risk(dm_context(labs=labs), AS_OF) == "High Risk"


def test_non_a1c_labs_are_ignored() -> None:
    from app.domain import LabResult

    ldl = LabResult(patient_id="P0001", test_name="LDL", result_value=200.0,
                    result_date=days_before(5))
    assert program.determine_risk(dm_context(labs=(ldl,)), AS_OF) == "Unmonitored"


# --- Per-tier needs --------------------------------------------------------
def _needs(tier: str):
    return {
        (n.specialty, n.cadence_days)
        for n in program.build_needs(dm_context(), tier)
    }


def test_high_risk_needs() -> None:
    assert _needs("High Risk") == {
        ("Endocrinology", 90), ("Cardiology", 90), ("Podiatry", 180),
        ("Ophthalmology", 365), ("Nephrology", 180),
    }


def test_moderate_risk_needs() -> None:
    assert _needs("Moderate Risk") == {
        ("Endocrinology", 180), ("Ophthalmology", 365), ("Podiatry", 365),
    }


def test_low_risk_needs() -> None:
    assert _needs("Low Risk") == {("Endocrinology", 365), ("Ophthalmology", 365)}


def test_unmonitored_needs_prioritize_endocrinology() -> None:
    assert _needs("Unmonitored") == {("Endocrinology", 90)}


def test_diabetes_needs_are_all_specialist() -> None:
    needs = program.build_needs(dm_context(), "High Risk")
    assert all(n.is_specialist for n in needs)
