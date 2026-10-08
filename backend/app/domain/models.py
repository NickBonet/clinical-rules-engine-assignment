"""Patient data, program needs, and tasks used by the rules engine.

These immutable dataclasses do not depend on the database or API framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


# Patient data loaded from CSVs.
@dataclass(frozen=True)
class Patient:
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    language: str | None
    pcp_provider_name: str | None  # Tasks use PCP encounters, not this field.

    def age_at(self, as_of: date) -> int:
        """Age in full years on the evaluation date."""
        dob = self.date_of_birth
        years = as_of.year - dob.year
        if (as_of.month, as_of.day) < (dob.month, dob.day):
            years -= 1
        return years


@dataclass(frozen=True)
class Diagnosis:
    patient_id: str
    icd_code: str
    description: str
    diagnosed_date: date


@dataclass(frozen=True)
class LabResult:
    patient_id: str
    test_name: str  # Normalized during ingest: "HbA1c" becomes "A1C".
    result_value: float
    result_date: date


@dataclass(frozen=True)
class Encounter:
    patient_id: str
    specialty: str
    encounter_date: date
    provider_name: str


# Data used to evaluate one patient.
@dataclass(frozen=True)
class PatientContext:
    patient: Patient
    diagnoses: tuple[Diagnosis, ...] = ()
    labs: tuple[LabResult, ...] = ()
    encounters: tuple[Encounter, ...] = ()

    @property
    def patient_id(self) -> str:
        return self.patient.patient_id

    def encounters_for(self, specialty: str) -> tuple[Encounter, ...]:
        return tuple(e for e in self.encounters if e.specialty == specialty)

    def has_diagnosis_prefix(self, prefixes: tuple[str, ...], as_of: date) -> bool:
        return any(
            diagnosis.diagnosed_date <= as_of and diagnosis.icd_code.startswith(prefixes)
            for diagnosis in self.diagnoses
        )


@dataclass(frozen=True)
class Need:
    """Care needed for a patient's program and risk tier.

    The task generator chooses a handler using need_type.
    """

    program: str
    need_type: str  # Currently "visit_cadence".
    specialty: str | None
    cadence_days: int
    is_specialist: bool


# Work generated from patient needs.
class TaskType(StrEnum):
    SCHEDULING = "scheduling"
    REFERRAL = "referral"


@dataclass(frozen=True)
class Task:
    patient_id: str
    program: str
    need_type: str
    specialty: str | None
    task_type: TaskType
    reason: str


@dataclass(frozen=True)
class Enrollment:
    """A patient's program, risk tier, and care needs."""

    patient_id: str
    program: str
    risk_tier: str
    needs: tuple[Need, ...] = field(default_factory=tuple)
