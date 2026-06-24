import json
import logging
import os
from dataclasses import dataclass

import httpx

from doc_ingestion_worker.pipeline.extract import Section

logger = logging.getLogger("doc_ingestion_worker.chunk_tag")

CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150


@dataclass
class TaggedChunk:
    text: str
    section: str
    source_url: str
    concept: str | None
    difficulty: str | None


def _chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE_CHARS
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP_CHARS
    return chunks


def _llm_router_url() -> str:
    return os.environ.get("LLM_ROUTER_URL", "http://llm_router:8001")


async def _tag_chunk(client: httpx.AsyncClient, framework: str, chunk_text: str) -> dict:
    prompt = (
        f"You are tagging a documentation chunk from the '{framework}' framework. "
        f"Given the text below, respond with JSON: "
        f'{{"concept": "<short concept name>", "difficulty": "beginner|intermediate|advanced"}}.\n\n'
        f"Text:\n{chunk_text[:800]}"
    )
    resp = await client.post(
        f"{_llm_router_url()}/generate",
        json={"task_type": "doc_tagging", "payload": {"prompt": prompt}, "response_format": "json"},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("json_data") or {}


async def chunk_and_tag(sections: list[Section], framework: str) -> list[TaggedChunk]:
    tagged: list[TaggedChunk] = []
    async with httpx.AsyncClient() as client:
        for section in sections:
            for raw_chunk in _chunk_text(section.text):
                try:
                    tags = await _tag_chunk(client, framework, raw_chunk)
                except (httpx.HTTPError, json.JSONDecodeError) as exc:
                    logger.warning("tagging failed for a chunk, leaving concept/difficulty unset: %s", exc)
                    tags = {}
                tagged.append(
                    TaggedChunk(
                        text=raw_chunk,
                        section=section.heading,
                        source_url=section.source_url,
                        concept=tags.get("concept"),
                        difficulty=tags.get("difficulty"),
                    )
                )
    return tagged
