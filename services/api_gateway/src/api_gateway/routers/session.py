from uuid import UUID

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError
from pydantic import BaseModel

from api_gateway.clients import orchestrator_client

router = APIRouter()


class CreateSessionRequest(BaseModel):
    framework: str
    goal: str
    goal_context: dict | None = None


@router.post("/sessions")
async def create_session(req: CreateSessionRequest) -> dict:
    return await orchestrator_client.request("POST", "/sessions", json=req.model_dump())


@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID) -> dict:
    try:
        return await orchestrator_client.request("GET", f"/sessions/{session_id}")
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
