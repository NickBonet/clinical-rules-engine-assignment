"""Database models for patient data, enrollments, tasks, and pipeline runs.

SqlRepository converts these rows to domain dataclasses before passing them
to the rules engine. Each ingest reloads patient data and replaces enrollments
and tasks per patient. Pipeline runs store the evaluation date for the API.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# Patient data, reloaded on each ingest.
class PatientRow(Base):
    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[date]
    gender: Mapped[str]
    language: Mapped[str | None]
    pcp_provider_name: Mapped[str | None]


class DiagnosisRow(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), index=True)
    icd_code: Mapped[str]
    description: Mapped[str]
    diagnosed_date: Mapped[date]


class LabRow(Base):
    __tablename__ = "labs"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), index=True)
    test_name: Mapped[str]
    result_value: Mapped[float]
    result_date: Mapped[date]


class EncounterRow(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), index=True)
    specialty: Mapped[str]
    encounter_date: Mapped[date]
    provider_name: Mapped[str]


# Results, replaced per patient and read by the API.
# No patient FK: patient data and results are replaced separately.
# Needs are used to generate tasks during a run, but are not stored here.
class EnrollmentRow(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(index=True)
    program: Mapped[str]
    risk_tier: Mapped[str]


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(index=True)
    program: Mapped[str]
    need_type: Mapped[str]
    specialty: Mapped[str | None] = mapped_column(index=True)
    task_type: Mapped[str] = mapped_column(index=True)  # Used for role and task filters.
    reason: Mapped[str]


# Evaluation date and timestamp for each ingest.
class PipelineRunRow(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    as_of: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
