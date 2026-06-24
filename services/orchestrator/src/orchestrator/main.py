from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator import state_machine

app = FastAPI(title="Orchestrator Service (internal)")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class CreateSessionRequest(BaseModel):
    framework: str
    goal: str
    goal_context: dict | None = None


@app.post("/sessions")
async def create_session(req: CreateSessionRequest) -> dict:
    session = await state_machine.start_session(req.framework, req.goal, req.goal_context)
    return {"session_id": str(session["id"])}


@app.get("/sessions/{session_id}")
async def get_session(session_id: UUID) -> dict:
    session = await state_machine.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


class DiagnosticRequest(BaseModel):
    answer: str | None = None


@app.post("/sessions/{session_id}/diagnostic")
async def diagnostic(session_id: UUID, req: DiagnosticRequest) -> dict:
    try:
        return await state_machine.handle_diagnostic(session_id, req.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/sessions/{session_id}/syllabus")
async def syllabus(session_id: UUID) -> dict:
    result = await state_machine.get_syllabus(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="syllabus not yet built")
    return result


class LessonStartRequest(BaseModel):
    concept_id: UUID


@app.post("/sessions/{session_id}/lesson/start")
async def lesson_start(session_id: UUID, req: LessonStartRequest) -> dict:
    try:
        return await state_machine.start_lesson(session_id, req.concept_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class SubmissionRequest(BaseModel):
    concept_id: UUID
    code: str


@app.post("/sessions/{session_id}/submissions")
async def submissions(session_id: UUID, req: SubmissionRequest) -> dict:
    return await state_machine.submit_solution(session_id, req.concept_id, req.code)


@app.get("/sessions/{session_id}/mastery")
async def mastery(session_id: UUID) -> list[dict]:
    return await state_machine.list_mastery(session_id)
