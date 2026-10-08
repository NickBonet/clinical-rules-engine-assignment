from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest

from app.api.routes.patients import list_patients
from app.api.routes.tasks import list_tasks as list_task_page
from app.domain import TaskType
from app.repository.db import create_schema, make_session_factory, make_sqlite_engine
from app.repository.models import EnrollmentRow, PatientRow, TaskRow
from app.repository.sql import SqlRepository


@pytest.fixture
def repository() -> Iterator[SqlRepository]:
    engine = make_sqlite_engine()
    create_schema(engine)
    factory = make_session_factory(engine)

    with factory() as session:
        session.add_all(
            PatientRow(
                patient_id=patient_id,
                first_name="Test",
                last_name="Patient",
                date_of_birth=date(1980, 1, 1),
                gender="F",
            )
            for patient_id in ("P001", "P002", "P003", "P004", "P005")
        )
        session.add(EnrollmentRow(patient_id="P001", program="Wellness", risk_tier="Standard"))
        session.add_all(
            [
                TaskRow(
                    patient_id="P002",
                    program="Diabetes",
                    need_type="visit_cadence",
                    specialty="Endocrinology",
                    task_type=TaskType.SCHEDULING.value,
                    reason="task-1",
                ),
                TaskRow(
                    patient_id="P003",
                    program="Diabetes",
                    need_type="visit_cadence",
                    specialty="Endocrinology",
                    task_type=TaskType.REFERRAL.value,
                    reason="task-2",
                ),
                TaskRow(
                    patient_id="P004",
                    program="Wellness",
                    need_type="visit_cadence",
                    specialty="PCP",
                    task_type=TaskType.SCHEDULING.value,
                    reason="task-3",
                ),
                TaskRow(
                    patient_id="P005",
                    program="Diabetes",
                    need_type="visit_cadence",
                    specialty="Cardiology",
                    task_type=TaskType.SCHEDULING.value,
                    reason="task-4",
                ),
            ]
        )
        session.commit()

    yield SqlRepository(factory)
    engine.dispose()


def test_task_pages_preserve_filters_without_gaps_or_duplicates(
    repository: SqlRepository,
) -> None:
    first_page = list_task_page(
        repository,
        (TaskType.SCHEDULING,),
        None,
        None,
        2,
        None,
    )
    second_page = list_task_page(
        repository,
        (TaskType.SCHEDULING,),
        None,
        None,
        2,
        first_page.next_cursor,
    )

    assert [task.reason for task in first_page.items + second_page.items] == [
        "task-1",
        "task-3",
        "task-4",
    ]
    assert first_page.next_cursor is not None
    assert second_page.next_cursor is None


def test_patient_pages_include_enrolled_patients_without_visible_tasks(
    repository: SqlRepository,
) -> None:
    first_page = list_patients(
        repository,
        (TaskType.SCHEDULING,),
        None,
        None,
        2,
        None,
    )
    second_page = list_patients(
        repository,
        (TaskType.SCHEDULING,),
        None,
        None,
        2,
        first_page.next_cursor,
    )
    patients = first_page.items + second_page.items

    assert [patient.patient_id for patient in patients] == ["P001", "P002", "P004", "P005"]
    assert patients[0].enrollments[0].program == "Wellness"
    assert patients[0].tasks == []
    assert second_page.next_cursor is None


def test_patient_pages_filter_by_specialty_and_role(
    repository: SqlRepository,
) -> None:
    clinical = list_patients(
        repository,
        (TaskType.SCHEDULING, TaskType.REFERRAL),
        "Endocrinology",
        None,
        10,
        None,
    )
    scheduler = list_patients(
        repository,
        (TaskType.SCHEDULING,),
        "Endocrinology",
        None,
        10,
        None,
    )

    assert [patient.patient_id for patient in clinical.items] == ["P002", "P003"]
    assert [task.task_type for patient in clinical.items for task in patient.tasks] == [
        TaskType.SCHEDULING,
        TaskType.REFERRAL,
    ]
    assert [patient.patient_id for patient in scheduler.items] == ["P002"]
    assert all(
        task.specialty == "Endocrinology" for patient in scheduler.items for task in patient.tasks
    )
