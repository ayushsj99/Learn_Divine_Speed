from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class GoalType(StrEnum):
    APPLY_TO_PROJECT = "apply_to_project"
    INTERVIEW_PREP = "interview_prep"
    UNDERSTAND_ONLY = "understand_only"


class Phase(StrEnum):
    INTAKE = "intake"
    DIAGNOSTIC = "diagnostic"
    SYLLABUS_BUILDING = "syllabus_building"
    LESSON_WORKED_EXAMPLE = "lesson_worked_example"
    LESSON_GUIDED_PRACTICE = "lesson_guided_practice"
    LESSON_EXERCISE = "lesson_exercise"
    GRADING = "grading"
    COMPLETED = "completed"


class SessionState(BaseModel):
    """Mirrors the `sessions` table. The framework/library is always supplied
    by the user at intake — never hardcoded by any service."""

    id: UUID
    user_id: UUID
    framework: str
    framework_version: str | None = None
    goal: GoalType
    goal_context: dict | None = None
    level: str | None = None
    syllabus_id: UUID | None = None
    current_concept_id: UUID | None = None
    phase: Phase = Phase.INTAKE
    created_at: datetime
    updated_at: datetime
