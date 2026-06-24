from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ConceptStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class SyllabusConcept(BaseModel):
    id: UUID
    syllabus_id: UUID
    ordinal: int
    name: str
    description: str
    prereq_concept_ids: list[UUID] = []
    difficulty: str
    status: ConceptStatus = ConceptStatus.PENDING


class Syllabus(BaseModel):
    id: UUID
    session_id: UUID
    framework: str
    version: int = 1
    created_at: datetime
    concepts: list[SyllabusConcept] = []


class MasteryEntry(BaseModel):
    """Mirrors the `mastery_entries` table — one row per (session, concept)."""

    id: UUID
    session_id: UUID
    concept_id: UUID
    mastery_score: float = 0.0
    attempts: int = 0
    shaky_flag: bool = False
    last_reinforced_at: datetime | None = None
    updated_at: datetime
