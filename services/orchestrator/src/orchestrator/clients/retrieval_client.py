import os

import httpx


def _base_url() -> str:
    return os.environ.get("RETRIEVAL_URL", "http://retrieval:8003")


async def query_chunks(
    framework: str, version: str, query: str, concept: str | None = None, top_k: int = 5
) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_base_url()}/query",
            json={
                "framework": framework,
                "version": version,
                "query": query,
                "concept": concept,
                "top_k": top_k,
            },
        )
        resp.raise_for_status()
        return resp.json()
