import os

import httpx


def _base_url() -> str:
    return os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:8002")


async def request(method: str, path: str, json: dict | None = None) -> dict | list:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.request(method, f"{_base_url()}{path}", json=json)
        resp.raise_for_status()
        return resp.json()
