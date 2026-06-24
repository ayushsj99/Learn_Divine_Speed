from uuid import UUID

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError
from pydantic import BaseModel

from api_gateway.clients import orchestrator_client

router = APIRouter()


class SubmissionRequest(BaseModel):
    concept_id: UUID
    code: str


@router.post("/sessions/{session_id}/submissions")
async def submissions(session_id: UUID, req: SubmissionRequest) -> dict:
    try:
        return await orchestrator_client.request(
            "POST",
            f"/sessions/{session_id}/submissions",
            json={"concept_id": str(req.concept_id), "code": req.code},
        )
    except HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
