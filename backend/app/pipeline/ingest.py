"""CSV ingestion: parse the provided files into normalized domain facts and
assemble one PatientContext per patient."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from app.domain import Diagnosis, Encounter, LabResult, Patient, PatientContext

# Raw lab test_name -> canonical name the rules read against.
_TEST_NAME_MAP = {"HbA1c": "A1C"}


def _d(value: str) -> date:
    return date.fromisoformat(value.strip())


def _null(value: str | None) -> str | None:
    v = (value or "").strip()
    return v or None


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def load_contexts(data_dir: Path) -> dict[str, PatientContext]:
    patients = {
        r["patient_id"]: Patient(
            patient_id=r["patient_id"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            date_of_birth=_d(r["date_of_birth"]),
            gender=r["gender"],
            language=_null(r.get("language")),
            pcp_provider_name=_null(r.get("pcp_provider_name")),
        )
        for r in _read(data_dir / "patients.csv")
    }

    diagnoses: dict[str, list[Diagnosis]] = {}
    for r in _read(data_dir / "diagnoses.csv"):
        diagnoses.setdefault(r["patient_id"], []).append(
            Diagnosis(r["patient_id"], r["icd_code"].strip(), r["description"], _d(r["diagnosed_date"]))
        )

    labs: dict[str, list[LabResult]] = {}
    for r in _read(data_dir / "labs.csv"):
        name = r["test_name"].strip()
        labs.setdefault(r["patient_id"], []).append(
            LabResult(
                r["patient_id"],
                _TEST_NAME_MAP.get(name, name),
                float(r["result_value"]),
                _d(r["result_date"]),
            )
        )

    encounters: dict[str, list[Encounter]] = {}
    for r in _read(data_dir / "encounters.csv"):
        encounters.setdefault(r["patient_id"], []).append(
            Encounter(r["patient_id"], r["specialty"].strip(), _d(r["encounter_date"]), r["provider_name"])
        )

    return {
        pid: PatientContext(
            patient=p,
            diagnoses=tuple(diagnoses.get(pid, ())),
            labs=tuple(labs.get(pid, ())),
            encounters=tuple(encounters.get(pid, ())),
        )
        for pid, p in patients.items()
    }


def all_labs(contexts: dict[str, PatientContext]) -> list[LabResult]:
    return [lab for ctx in contexts.values() for lab in ctx.labs]
