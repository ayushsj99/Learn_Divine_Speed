from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel


class TaskType(StrEnum):
    """Routed by the LLM Router's routing.yaml — task_type -> provider/model.
    Adding a task here requires a matching entry in routing.yaml, never a
    code change to the caller."""

    ORCHESTRATOR_ROUTING = "orchestrator_routing"
    DIAGNOSTIC_QUESTION_GEN = "diagnostic_question_gen"
    DIAGNOSTIC_GRADING_CHECK = "diagnostic_grading_check"
    FIRST_PASS_HINT = "first_pass_hint"
    FULLER_EXPLANATION = "fuller_explanation"
    SYLLABUS_BUILDER = "syllabus_builder"
    LESSON_GENERATOR = "lesson_generator"
    EXERCISE_GENERATOR = "exercise_generator"
    DOC_TAGGING = "doc_tagging"


class LLMRequest(BaseModel):
    task_type: TaskType
    payload: dict[str, Any]
    response_format: Literal["text", "json"] = "text"


class LLMResponse(BaseModel):
    text: str | None = None
    json_data: dict[str, Any] | None = None
    provider: str
    model: str
