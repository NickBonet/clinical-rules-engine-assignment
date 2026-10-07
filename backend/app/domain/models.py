"""Core domain entities: facts, derived needs, and tasks.

These are plain, immutable dataclasses with no persistence or framework coupling.
The rules engine and task generator operate purely on these types, which is what
keeps the evaluation core serializable and TaskIQ-ready later on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


# Facts (loaded from the CSVs, 1:1 with the source columns after normalization)
@dataclass(frozen=True)
class Patient:
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    language: str | None
    pcp_provider_name: str | None  # NOTE: not used by task logic; PCP *encounters* are.

    def age_at(self, as_of: date) -> int:
        """Calendar age at `as_of`, adjusting for whether the birthday has passed."""
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
    test_name: str  # normalized (e.g. raw "HbA1c" -> "A1C")
    result_value: float
    result_date: date


@dataclass(frozen=True)
class Encounter:
    patient_id: str
    specialty: str
    encounter_date: date
    provider_name: str


# Patient context: everything the engine needs for one patient
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

    def has_diagnosis_prefix(self, prefixes: tuple[str, ...]) -> bool:
        return any(d.icd_code.startswith(prefixes) for d in self.diagnoses)


@dataclass(frozen=True)
class Need:
    """A clinical requirement produced by a program for a patient at a risk tier.

    `need_type` drives task-generation dispatch. Today only "visit_cadence" exists;
    a future "lab_order" need registers its own resolver without touching the rest.
    """

    program: str
    need_type: str  # "visit_cadence" (future: "lab_order", ...)
    specialty: str | None
    cadence_days: int
    is_specialist: bool


# Task and task type models, representing work items generated for patients based on their needs.
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
    """Derived program state for a patient: which program, which risk tier, needs."""

    patient_id: str
    program: str
    risk_tier: str
    needs: tuple[Need, ...] = field(default_factory=tuple)
