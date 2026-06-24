import os

import httpx

from doc_ingestion_worker.pipeline.chunk_tag import TaggedChunk


def _retrieval_url() -> str:
    return os.environ.get("RETRIEVAL_URL", "http://retrieval:8003")


async def publish_chunks(framework: str, version: str, chunks: list[TaggedChunk]) -> dict:
    payload = {
        "framework": framework,
        "version": version,
        "chunks": [
            {
                "text": c.text,
                "concept": c.concept,
                "section": c.section,
                "difficulty": c.difficulty,
                "source_url": c.source_url,
            }
            for c in chunks
        ],
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{_retrieval_url()}/upsert", json=payload)
        resp.raise_for_status()
        return resp.json()
