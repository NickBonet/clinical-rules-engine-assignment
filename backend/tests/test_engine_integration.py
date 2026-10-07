"""Integration checks for program evaluation and task generation."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

from app.domain import TaskType
from app.engine import RulesEngine, generate_task
from app.pipeline.as_of import resolve_as_of
from app.pipeline.ingest import all_labs, load_contexts
from tests.builders import AS_OF, a1c, context, days_after, days_before, diagnosis, encounter

engine = RulesEngine()


def evaluate(ctx):
    """Mirror orchestrator.run_patient: return (enrollments, tasks)."""
    enrollments = list(engine.evaluate_patient(ctx, AS_OF))
    tasks = [
        task
        for e in enrollments
        for need in e.needs
        if (task := generate_task(need, ctx, AS_OF)) is not None
    ]
    return enrollments, tasks


def programs(enrollments) -> set[str]:
    return {e.program for e in enrollments}


def test_young_healthy_patient_enrolls_only_in_wellness() -> None:
    enrollments, tasks = evaluate(context(age=30))
    assert programs(enrollments) == {"Primary Care Wellness"}
    # No PCP history -> no task.
    assert tasks == []


def test_minor_enrolls_in_nothing() -> None:
    enrollments, tasks = evaluate(context(age=10))
    assert enrollments == []
    assert tasks == []


def test_diabetic_minor_enrolls_only_in_diabetes() -> None:
    ctx = context(
        age=10,
        diagnoses=(diagnosis("E11.9"),),
        labs=(a1c(9.4, result_date=days_before(10)),),
    )
    enrollments, tasks = evaluate(ctx)
    assert len(enrollments) == 1
    assert programs(enrollments) == {"Diabetes Management"}
    assert enrollments[0].risk_tier == "High Risk"
    assert len(tasks) == 5
    assert all(task.program == "Diabetes Management" for task in tasks)
    assert all(task.task_type == TaskType.REFERRAL for task in tasks)


def test_diabetic_patient_enrolls_in_both_programs() -> None:
    ctx = context(
        age=55,
        diagnoses=(diagnosis("E11.9"),),
        labs=(a1c(9.4, result_date=days_before(10)),),
    )
    enrollments, _ = evaluate(ctx)
    assert programs(enrollments) == {"Primary Care Wellness", "Diabetes Management"}

    dm = next(e for e in enrollments if e.program == "Diabetes Management")
    assert dm.risk_tier == "High Risk"
    pcw = next(e for e in enrollments if e.program == "Primary Care Wellness")
    assert pcw.risk_tier == "High Priority"  # chronic E11 diagnosis


def test_high_risk_diabetic_no_specialist_history_gets_five_referrals() -> None:
    ctx = context(
        age=55,
        pcp_provider_name=None,
        diagnoses=(diagnosis("E11.9"),),
        labs=(a1c(9.4, result_date=days_before(10)),),
    )
    _, tasks = evaluate(ctx)
    dm_tasks = [t for t in tasks if t.program == "Diabetes Management"]
    assert len(dm_tasks) == 5
    assert all(t.task_type == TaskType.REFERRAL for t in dm_tasks)
    assert {t.specialty for t in dm_tasks} == {
        "Endocrinology", "Cardiology", "Podiatry", "Ophthalmology", "Nephrology",
    }


def test_well_managed_diabetic_with_upcoming_visits_has_no_tasks() -> None:
    # Low risk + every specialty already on the calendar + fresh PCP visit.
    ctx = context(
        age=50,
        diagnoses=(diagnosis("E11.9"),),
        labs=(a1c(6.2, result_date=days_before(10)),),
        encounters=(
            encounter("PCP", on=days_before(20)),
            encounter("Endocrinology", on=days_after(30)),
            encounter("Ophthalmology", on=days_after(30)),
        ),
    )
    enrollments, tasks = evaluate(ctx)
    dm = next(e for e in enrollments if e.program == "Diabetes Management")
    assert dm.risk_tier == "Low Risk"
    assert tasks == []


def test_unmonitored_diabetic_gets_endocrinology_referral() -> None:
    # Diabetic with no A1C in window and no Endo history -> single referral.
    ctx = context(age=50, diagnoses=(diagnosis("E10.9"),))
    enrollments, tasks = evaluate(ctx)
    dm = next(e for e in enrollments if e.program == "Diabetes Management")
    assert dm.risk_tier == "Unmonitored"
    dm_tasks = [t for t in tasks if t.program == "Diabetes Management"]
    assert len(dm_tasks) == 1
    assert dm_tasks[0].specialty == "Endocrinology"
    assert dm_tasks[0].task_type == TaskType.REFERRAL


def test_programs_are_evaluated_independently() -> None:
    # Asthma raises wellness priority but does not qualify for diabetes management.
    ctx = context(age=40, diagnoses=(diagnosis("J45.909"),))
    enrollments, _ = evaluate(ctx)
    assert programs(enrollments) == {"Primary Care Wellness"}
    pcw = next(e for e in enrollments if e.program == "Primary Care Wellness")
    assert pcw.risk_tier == "High Priority"


def test_supplied_csv_data_is_normalized_grouped_and_evaluated() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    contexts = load_contexts(data_dir)
    assert len(contexts) == 300
    assert resolve_as_of(all_labs(contexts)) == AS_OF
    assert all(isinstance(ctx.patient.date_of_birth, date) for ctx in contexts.values())
    assert all(
        record.patient_id == patient_id
        for patient_id, ctx in contexts.items()
        for record in (*ctx.diagnoses, *ctx.labs, *ctx.encounters)
    )

    with (data_dir / "labs.csv").open(newline="") as source:
        raw_labs = list(csv.DictReader(source))
    assert any(row["test_name"] == "HbA1c" for row in raw_labs)
    assert Counter(
        (patient_id, lab.test_name, lab.result_value, lab.result_date)
        for patient_id, ctx in contexts.items() for lab in ctx.labs
    ) == Counter(
        (
            row["patient_id"],
            "A1C" if row["test_name"] == "HbA1c" else row["test_name"],
            float(row["result_value"]),
            date.fromisoformat(row["result_date"]),
        )
        for row in raw_labs
    )

    all_enrollments = []
    all_tasks = []
    for ctx in contexts.values():
        enrollments, tasks = evaluate(ctx)
        all_enrollments.extend(enrollments)
        all_tasks.extend(tasks)
    assert Counter((entry.program, entry.risk_tier) for entry in all_enrollments) == {
        ("Primary Care Wellness", "High Priority"): 217,
        ("Primary Care Wellness", "Standard"): 71,
        ("Diabetes Management", "High Risk"): 29,
        ("Diabetes Management", "Moderate Risk"): 39,
        ("Diabetes Management", "Low Risk"): 24,
        ("Diabetes Management", "Unmonitored"): 23,
    }
    assert Counter(task.task_type for task in all_tasks) == {
        TaskType.SCHEDULING: 154,
        TaskType.REFERRAL: 119,
    }
