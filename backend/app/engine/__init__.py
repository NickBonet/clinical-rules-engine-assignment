"""Pure evaluation core: program rules, orchestration, and task generation.

Imports only `app.domain` — never repository, pipeline, or api. This keeps the
core serializable and side-effect-free (and physically unable to touch I/O),
which is what makes it safe to run under a future TaskIQ worker unchanged.
"""

from app.engine.programs import (
    DiabetesManagementProgram,
    PrimaryCareWellnessProgram,
    ProgramRule,
    default_programs,
)
from app.engine.rules_engine import RulesEngine
from app.engine.tasks import generate_task, resolver

__all__ = [
    "DiabetesManagementProgram",
    "PrimaryCareWellnessProgram",
    "ProgramRule",
    "RulesEngine",
    "default_programs",
    "generate_task",
    "resolver",
]
