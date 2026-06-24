from uuid import UUID

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError
from pydantic import BaseModel

from api_gateway.clients import orchestrator_client

router = APIRouter()


@router.get("/sessions/{session_id}/syllabus")
async def syllabus(session_id: UUID) -> dict:
    try:
        return await orchestrator_client.request("GET", f"/sessions/{session_id}/syllabus")
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc


class LessonStartRequest(BaseModel):
    concept_id: UUID


@router.post("/sessions/{session_id}/lesson/start")
async def lesson_start(session_id: UUID, req: LessonStartRequest) -> dict:
    try:
        return await orchestrator_client.request(
            "POST", f"/sessions/{session_id}/lesson/start", json={"concept_id": str(req.concept_id)}
        )
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc


@router.get("/sessions/{session_id}/mastery")
async def mastery(session_id: UUID) -> list:
    try:
        return await orchestrator_client.request("GET", f"/sessions/{session_id}/mastery")
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
