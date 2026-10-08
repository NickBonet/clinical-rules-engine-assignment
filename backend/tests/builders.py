"""Test helpers for patient data and dates relative to AS_OF."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain import (
    Diagnosis,
    Encounter,
    LabResult,
    Patient,
    PatientContext,
)

# Fixed evaluation date for tests, matching the dataset's reference date.
AS_OF = date(2026, 4, 7)

PID = "P0001"


def days_before(n: int, ref: date = AS_OF) -> date:
    return ref - timedelta(days=n)


def days_after(n: int, ref: date = AS_OF) -> date:
    return ref + timedelta(days=n)


def patient(
    *,
    age: int = 40,
    patient_id: str = PID,
    pcp_provider_name: str | None = "Dr. PCP",
    as_of: date = AS_OF,
) -> Patient:
    """A patient whose birthday is on as_of's month/day so `age` is exact."""
    dob = date(as_of.year - age, as_of.month, as_of.day)
    return Patient(
        patient_id=patient_id,
        first_name="Test",
        last_name="Patient",
        date_of_birth=dob,
        gender="F",
        language="English",
        pcp_provider_name=pcp_provider_name,
    )


def diagnosis(
    icd_code: str,
    *,
    patient_id: str = PID,
    diagnosed_date: date | None = None,
) -> Diagnosis:
    return Diagnosis(
        patient_id=patient_id,
        icd_code=icd_code,
        description=icd_code,
        diagnosed_date=diagnosed_date if diagnosed_date is not None else days_before(400),
    )


def a1c(value: float, *, result_date: date, patient_id: str = PID) -> LabResult:
    return LabResult(
        patient_id=patient_id,
        test_name="A1C",
        result_value=value,
        result_date=result_date,
    )


def encounter(specialty: str, *, on: date, patient_id: str = PID) -> Encounter:
    return Encounter(
        patient_id=patient_id,
        specialty=specialty,
        encounter_date=on,
        provider_name=f"Dr. {specialty}",
    )


def context(
    *,
    age: int = 40,
    pcp_provider_name: str | None = "Dr. PCP",
    diagnoses: tuple[Diagnosis, ...] = (),
    labs: tuple[LabResult, ...] = (),
    encounters: tuple[Encounter, ...] = (),
    as_of: date = AS_OF,
) -> PatientContext:
    return PatientContext(
        patient=patient(age=age, pcp_provider_name=pcp_provider_name, as_of=as_of),
        diagnoses=diagnoses,
        labs=labs,
        encounters=encounters,
    )
