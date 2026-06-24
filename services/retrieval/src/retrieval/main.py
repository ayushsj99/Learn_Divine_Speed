from typing import Any

from fastapi import FastAPI
from lgs_shared.models.retrieval import RetrievalQuery, RetrievedChunk
from pydantic import BaseModel

from retrieval.embeddings import embed_text
from retrieval.qdrant_client_wrapper import collection_name, collection_point_count, search, upsert_chunks

app = FastAPI(title="Retrieval Service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/collections/{name}")
def collection_status(name: str) -> dict:
    return {"name": name, "point_count": collection_point_count(name)}


class UpsertChunk(BaseModel):
    text: str
    concept: str | None = None
    section: str | None = None
    difficulty: str | None = None
    source_url: str | None = None


class UpsertRequest(BaseModel):
    framework: str
    version: str
    chunks: list[UpsertChunk]


class UpsertResponse(BaseModel):
    collection: str
    upserted: int


@app.post("/upsert", response_model=UpsertResponse)
async def upsert(req: UpsertRequest) -> UpsertResponse:
    name = collection_name(req.framework, req.version)
    vectors = [await embed_text(chunk.text) for chunk in req.chunks]
    payloads: list[dict[str, Any]] = [
        {
            "text": chunk.text,
            "concept": chunk.concept,
            "section": chunk.section,
            "difficulty": chunk.difficulty,
            "version": req.version,
            "source_url": chunk.source_url,
        }
        for chunk in req.chunks
    ]
    count = upsert_chunks(name, vectors, payloads)
    return UpsertResponse(collection=name, upserted=count)


@app.post("/query", response_model=list[RetrievedChunk])
async def query(req: RetrievalQuery) -> list[RetrievedChunk]:
    name = collection_name(req.framework, req.version)
    vector = await embed_text(req.query)
    results = search(name, vector, top_k=req.top_k, concept=req.concept)
    return [
        RetrievedChunk(
            text=r.get("text", ""),
            concept=r.get("concept"),
            section=r.get("section"),
            difficulty=r.get("difficulty"),
            version=r.get("version"),
            source_url=r.get("source_url"),
            score=r.get("score"),
        )
        for r in results
    ]
