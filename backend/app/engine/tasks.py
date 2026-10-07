"""Task generation: turn a Need into an actionable Task (or nothing).

A thin dispatcher keyed by `need_type`, with one resolver per type. Today only
"visit_cadence" exists; adding a "lab_order" need type means registering a new
resolver here and nothing else.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from app.domain import Need, PatientContext, Task, TaskType

Resolver = Callable[[Need, PatientContext, date], Task | None]
_RESOLVERS: dict[str, Resolver] = {}


def resolver(need_type: str) -> Callable[[Resolver], Resolver]:
    def register(fn: Resolver) -> Resolver:
        _RESOLVERS[need_type] = fn
        return fn

    return register


def generate_task(need: Need, ctx: PatientContext, as_of: date) -> Task | None:
    try:
        resolve = _RESOLVERS[need.need_type]
    except KeyError:  # pragma: no cover - guards against an unregistered need type
        raise ValueError(
            f"No task resolver registered for need_type={need.need_type!r}"
        ) from None
    return resolve(need, ctx, as_of)


@resolver("visit_cadence")
def _resolve_visit_cadence(need: Need, ctx: PatientContext, as_of: date) -> Task | None:
    encounters = ctx.encounters_for(need.specialty)

    # An already-scheduled future visit for this specialty supersedes any task.
    if any(e.encounter_date > as_of for e in encounters):
        return None

    past = [e.encounter_date for e in encounters if e.encounter_date <= as_of]
    if past:
        last = max(past)
        if (as_of - last).days > need.cadence_days:
            return Task(
                patient_id=ctx.patient_id,
                program=need.program,
                need_type=need.need_type,
                specialty=need.specialty,
                task_type=TaskType.SCHEDULING,
                reason=(
                    f"Last {need.specialty} visit {last.isoformat()} exceeds "
                    f"{need.cadence_days}-day cadence"
                ),
            )
        return None  # seen recently enough

    # No prior encounter for this specialty.
    if need.is_specialist:
        return Task(
            patient_id=ctx.patient_id,
            program=need.program,
            need_type=need.need_type,
            specialty=need.specialty,
            task_type=TaskType.REFERRAL,
            reason=f"No prior {need.specialty} encounter; referral review required",
        )
    # PCP with no encounter history -> no task (per spec).
    return None
