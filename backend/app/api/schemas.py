"""Public response models, independent of persistence models."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain import TaskType


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(description="Service status.")
    as_of: date = Field(description="Evaluation date for the currently loaded results.")


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str = Field(description="Unique patient identifier.")
    program: str = Field(description="Care program that generated the task.")
    need_type: str = Field(description="Care need that generated the task.")
    specialty: str | None = Field(description="Target specialty, when applicable.")
    task_type: TaskType = Field(description="Scheduling or referral task.")
    reason: str = Field(description="Clinical rationale for the task.")


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program: str = Field(description="Enrolled care program.")
    risk_tier: str = Field(description="Patient's risk tier within this program.")


class PatientResponse(BaseModel):
    patient_id: str = Field(description="Unique patient identifier.")
    enrollments: list[EnrollmentResponse] = Field(description="All program enrollments.")
    tasks: list[TaskResponse] = Field(description="Tasks matching the role and query filters.")


class TaskPageResponse(BaseModel):
    items: list[TaskResponse] = Field(description="Tasks on this page.")
    next_cursor: int | None = Field(description="Cursor for the next page, if one exists.")


class PatientPageResponse(BaseModel):
    items: list[PatientResponse] = Field(description="Patients on this page.")
    next_cursor: str | None = Field(description="Cursor for the next page, if one exists.")
