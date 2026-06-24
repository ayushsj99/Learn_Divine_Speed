import os

import httpx


def _retrieval_url() -> str:
    return os.environ.get("RETRIEVAL_URL", "http://retrieval:8003")


async def eval_check(collection_name: str, expected_min_points: int) -> None:
    """Minimal real regression check for v1: assert the published collection
    actually has points indexed. A fuller eval harness (fixed known-answer
    queries) is a v2 extension point, not solved here."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_retrieval_url()}/collections/{collection_name}")
        resp.raise_for_status()
        data = resp.json()

    if data["point_count"] < expected_min_points:
        raise RuntimeError(
            f"eval_check failed: collection '{collection_name}' has "
            f"{data['point_count']} points, expected >= {expected_min_points}"
        )
