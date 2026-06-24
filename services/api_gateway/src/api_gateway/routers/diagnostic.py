from uuid import UUID

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError
from pydantic import BaseModel

from api_gateway.clients import orchestrator_client

router = APIRouter()


class DiagnosticRequest(BaseModel):
    answer: str | None = None


@router.post("/sessions/{session_id}/diagnostic")
async def diagnostic(session_id: UUID, req: DiagnosticRequest) -> dict:
    try:
        return await orchestrator_client.request(
            "POST", f"/sessions/{session_id}/diagnostic", json=req.model_dump()
        )
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
