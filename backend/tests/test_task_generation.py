"""Visit-cadence task generation: overdue visits, upcoming visits, and referrals."""

from __future__ import annotations

import pytest

from app.domain import Need, TaskType
from app.engine.tasks import generate_task
from tests.builders import AS_OF, context, days_after, days_before, encounter


def pcp_need(cadence: int = 365) -> Need:
    return Need("Primary Care Wellness", "visit_cadence", "PCP", cadence, is_specialist=False)


def specialist_need(specialty: str = "Endocrinology", cadence: int = 90) -> Need:
    return Need("Diabetes Management", "visit_cadence", specialty, cadence, is_specialist=True)


# --- Prior visit, stale vs fresh ------------------------------------------
def test_stale_past_visit_generates_scheduling_task() -> None:
    ctx = context(encounters=(encounter("PCP", on=days_before(400)),))
    task = generate_task(pcp_need(365), ctx, AS_OF)
    assert task is not None
    assert task.task_type == TaskType.SCHEDULING
    assert task.specialty == "PCP"
    assert "365-day cadence" in task.reason


def test_fresh_past_visit_generates_no_task() -> None:
    ctx = context(encounters=(encounter("PCP", on=days_before(30)),))
    assert generate_task(pcp_need(365), ctx, AS_OF) is None


def test_cadence_boundary_exactly_at_limit_is_not_overdue() -> None:
    # (as_of - last).days > cadence_days is strict, so exactly cadence = no task.
    ctx = context(encounters=(encounter("PCP", on=days_before(365)),))
    assert generate_task(pcp_need(365), ctx, AS_OF) is None


def test_cadence_boundary_one_day_over_is_overdue() -> None:
    ctx = context(encounters=(encounter("PCP", on=days_before(366)),))
    assert generate_task(pcp_need(365), ctx, AS_OF) is not None


@pytest.mark.parametrize("cadence", [90, 180, 365])
def test_specialist_task_at_cadence_boundary(cadence: int) -> None:
    ctx = context(encounters=(
        encounter("Endocrinology", on=days_before(cadence)),
    ))
    assert generate_task(specialist_need(cadence=cadence), ctx, AS_OF) is None

    overdue = context(encounters=(
        encounter("Endocrinology", on=days_before(cadence + 1)),
    ))
    task = generate_task(specialist_need(cadence=cadence), overdue, AS_OF)
    assert task is not None
    assert task.task_type == TaskType.SCHEDULING
    assert task.specialty == "Endocrinology"


# --- Upcoming visits suppress tasks ---------------------------------------
def test_upcoming_visit_suppresses_task_even_with_stale_history() -> None:
    ctx = context(encounters=(
        encounter("PCP", on=days_before(400)),  # overdue on its own...
        encounter("PCP", on=days_after(10)),    # ...but already scheduled ahead
    ))
    assert generate_task(pcp_need(365), ctx, AS_OF) is None


def test_upcoming_specialist_visit_suppresses_referral() -> None:
    # No past Endocrinology visit, but one is on the calendar -> no referral.
    ctx = context(encounters=(encounter("Endocrinology", on=days_after(5)),))
    assert generate_task(specialist_need("Endocrinology"), ctx, AS_OF) is None


def test_visit_exactly_on_as_of_is_not_upcoming() -> None:
    # as_of itself counts as "seen" (<= as_of), so it is a fresh past visit.
    ctx = context(encounters=(encounter("PCP", on=AS_OF),))
    assert generate_task(pcp_need(365), ctx, AS_OF) is None


# --- No prior encounter ----------------------------------------------------
def test_no_prior_specialist_encounter_generates_referral() -> None:
    task = generate_task(specialist_need("Cardiology"), context(), AS_OF)
    assert task is not None
    assert task.task_type == TaskType.REFERRAL
    assert task.specialty == "Cardiology"
    assert "referral" in task.reason.lower()


def test_no_prior_pcp_encounter_generates_no_task() -> None:
    assert generate_task(pcp_need(365), context(), AS_OF) is None


def test_encounter_with_other_specialty_does_not_satisfy_need() -> None:
    # A PCP visit does not count toward an Endocrinology need -> referral.
    ctx = context(encounters=(encounter("PCP", on=days_before(10)),))
    task = generate_task(specialist_need("Endocrinology"), ctx, AS_OF)
    assert task is not None
    assert task.task_type == TaskType.REFERRAL


def test_most_recent_past_visit_drives_the_decision() -> None:
    # Multiple past visits: only the latest matters, and it is fresh.
    ctx = context(encounters=(
        encounter("Endocrinology", on=days_before(10)),
        encounter("Endocrinology", on=days_before(400)),
    ))
    assert generate_task(specialist_need("Endocrinology", 90), ctx, AS_OF) is None
