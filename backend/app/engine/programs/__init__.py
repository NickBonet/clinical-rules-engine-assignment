"""Program rules and the default registry.

Add new programs in their own modules and register them in default_programs().
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