import os
from typing import Any, Literal

import httpx


def _base_url() -> str:
    return os.environ.get("LLM_ROUTER_URL", "http://llm_router:8001")


async def generate(
    task_type: str, prompt: str, response_format: Literal["text", "json"] = "text"
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{_base_url()}/generate",
            json={"task_type": task_type, "payload": {"prompt": prompt}, "response_format": response_format},
        )
        resp.raise_for_status()
        return resp.json()


async def generate_text(task_type: str, prompt: str) -> str:
    result = await generate(task_type, prompt, response_format="text")
    return result["text"] or ""


async def generate_json(task_type: str, prompt: str) -> dict[str, Any]:
    result = await generate(task_type, prompt, response_format="json")
    return result["json_data"] or {}
