"""SQLAlchemy-backed Repository — the single storage implementation.

Implements the `Repository` Protocol (see base.py) for both the in-memory SQLite
backend and the Postgres backend, so the pipeline, API, and `run_patient` seam
are backend-agnostic. Each operation runs in its own short-lived
session (via an injected factory) so concurrent API reads and the per-patient
write transaction never share session state. The `write_facts` / `record_run` /
`latest_as_of` module helpers cover the ingest write-path and the API read-path
that the Protocol itself doesn't express.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain import (
    Diagnosis,
    Encounter,
    Enrollment,
    LabResult,
    Patient,
    PatientContext,
    Task,
    TaskType,
)
from app.repository.models import (
    DiagnosisRow,
    EncounterRow,
    EnrollmentRow,
    LabRow,
    PatientRow,
    PipelineRunRow,
    TaskRow,
)

SessionFactory = Callable[[], Session]


class SqlRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def patient_ids(self) -> list[str]:
        with self._session_factory() as session:
            return list(session.scalars(select(PatientRow.patient_id)))

    def load_patient_context(self, patient_id: str) -> PatientContext:
        with self._session_factory() as session:
            patient = session.get(PatientRow, patient_id)
            if patient is None:
                raise KeyError(patient_id)
            diagnoses = session.scalars(
                select(DiagnosisRow).where(DiagnosisRow.patient_id == patient_id)
            ).all()
            labs = session.scalars(
                select(LabRow).where(LabRow.patient_id == patient_id)
            ).all()
            encounters = session.scalars(
                select(EncounterRow).where(EncounterRow.patient_id == patient_id)
            ).all()

        return PatientContext(
            patient=Patient(
                patient_id=patient.patient_id,
                first_name=patient.first_name,
                last_name=patient.last_name,
                date_of_birth=patient.date_of_birth,
                gender=patient.gender,
                language=patient.language,
                pcp_provider_name=patient.pcp_provider_name,
            ),
            diagnoses=tuple(
                Diagnosis(d.patient_id, d.icd_code, d.description, d.diagnosed_date)
                for d in diagnoses
            ),
            labs=tuple(
                LabResult(lab.patient_id, lab.test_name, lab.result_value, lab.result_date)
                for lab in labs
            ),
            encounters=tuple(
                Encounter(e.patient_id, e.specialty, e.encounter_date, e.provider_name)
                for e in encounters
            ),
        )

    def replace_derived_state(
        self, patient_id: str, enrollments: list[Enrollment], tasks: list[Task]
    ) -> None:
        # Delete-then-insert for this patient in one transaction: the unit of
        # idempotency, so a retried job yields identical state.
        with self._session_factory() as session:
            session.execute(
                delete(EnrollmentRow).where(EnrollmentRow.patient_id == patient_id)
            )
            session.execute(delete(TaskRow).where(TaskRow.patient_id == patient_id))
            session.add_all(
                EnrollmentRow(
                    patient_id=e.patient_id, program=e.program, risk_tier=e.risk_tier
                )
                for e in enrollments
            )
            session.add_all(
                TaskRow(
                    patient_id=t.patient_id,
                    program=t.program,
                    need_type=t.need_type,
                    specialty=t.specialty,
                    task_type=t.task_type.value,
                    reason=t.reason,
                )
                for t in tasks
            )
            session.commit()

    def list_enrollments(self) -> list[Enrollment]:
        with self._session_factory() as session:
            rows = session.scalars(select(EnrollmentRow)).all()
        return [
            Enrollment(patient_id=r.patient_id, program=r.program, risk_tier=r.risk_tier)
            for r in rows
        ]

    def list_tasks(
        self,
        *,
        specialty: str | None = None,
        task_type: str | None = None,
        allowed_task_types: tuple[str, ...] | None = None,
    ) -> list[Task]:
        stmt = select(TaskRow)
        if specialty is not None:
            stmt = stmt.where(TaskRow.specialty == specialty)
        if task_type is not None:
            stmt = stmt.where(TaskRow.task_type == str(task_type))
        if allowed_task_types is not None:
            stmt = stmt.where(TaskRow.task_type.in_([str(t) for t in allowed_task_types]))
        with self._session_factory() as session:
            rows = session.scalars(stmt).all()
        return [
            Task(
                patient_id=r.patient_id,
                program=r.program,
                need_type=r.need_type,
                specialty=r.specialty,
                task_type=TaskType(r.task_type),
                reason=r.reason,
            )
            for r in rows
        ]


# Ingest write-path and API read-path helpers (outside the Protocol).
def write_facts(session: Session, contexts: dict[str, PatientContext]) -> None:
    """Full refresh of the fact tables from freshly-ingested contexts.

    Truncate-reload (delete children before parents for the FKs) keeps facts an
    exact mirror of the current CSVs. Commits on success.
    """
    session.execute(delete(EncounterRow))
    session.execute(delete(LabRow))
    session.execute(delete(DiagnosisRow))
    session.execute(delete(PatientRow))

    # Insert parents before children: the child tables FK to patients, and with no
    # ORM relationship() declared the unit-of-work can't infer that ordering on its
    # own, so flush the patients first.
    session.add_all(
        PatientRow(
            patient_id=p.patient_id,
            first_name=p.first_name,
            last_name=p.last_name,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            language=p.language,
            pcp_provider_name=p.pcp_provider_name,
        )
        for p in (ctx.patient for ctx in contexts.values())
    )
    session.flush()

    for ctx in contexts.values():
        session.add_all(
            DiagnosisRow(
                patient_id=d.patient_id,
                icd_code=d.icd_code,
                description=d.description,
                diagnosed_date=d.diagnosed_date,
            )
            for d in ctx.diagnoses
        )
        session.add_all(
            LabRow(
                patient_id=lab.patient_id,
                test_name=lab.test_name,
                result_value=lab.result_value,
                result_date=lab.result_date,
            )
            for lab in ctx.labs
        )
        session.add_all(
            EncounterRow(
                patient_id=e.patient_id,
                specialty=e.specialty,
                encounter_date=e.encounter_date,
                provider_name=e.provider_name,
            )
            for e in ctx.encounters
        )
    session.commit()


def record_run(session: Session, as_of: date) -> None:
    session.add(PipelineRunRow(as_of=as_of))
    session.commit()


def latest_as_of(session: Session) -> date | None:
    return session.scalars(
        select(PipelineRunRow.as_of).order_by(PipelineRunRow.id.desc()).limit(1)
    ).first()
