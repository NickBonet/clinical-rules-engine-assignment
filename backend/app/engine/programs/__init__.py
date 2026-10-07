"""Stateless program rules and their explicit default registry.

Adding a program means adding a module and registering its class here; nothing
else in the engine, pipeline, or API changes.
"""

from app.engine.programs.base import ProgramRule
from app.engine.programs.diabetes import DiabetesManagementProgram
from app.engine.programs.primary_care import PrimaryCareWellnessProgram

__all__ = [
    "DiabetesManagementProgram",
    "PrimaryCareWellnessProgram",
    "ProgramRule",
    "default_programs",
]


def default_programs() -> tuple[ProgramRule, ...]:
    return (PrimaryCareWellnessProgram(), DiabetesManagementProgram())