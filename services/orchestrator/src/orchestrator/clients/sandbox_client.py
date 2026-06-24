import os

import httpx


def _base_url() -> str:
    return os.environ.get("SANDBOX_URL", "http://sandbox:8004")


async def execute(code: str, test_code: str | None, timeout_seconds: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=timeout_seconds + 10) as client:
        resp = await client.post(
            f"{_base_url()}/execute",
            json={"code": code, "test_code": test_code, "timeout_seconds": timeout_seconds},
        )
        resp.raise_for_status()
        return resp.json()
