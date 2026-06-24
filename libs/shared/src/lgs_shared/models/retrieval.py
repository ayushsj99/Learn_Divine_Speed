from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    text: str
    concept: str | None = None
    section: str | None = None
    difficulty: str | None = None
    version: str | None = None
    source_url: str | None = None
    score: float | None = None


class RetrievalQuery(BaseModel):
    framework: str
    version: str
    query: str
    concept: str | None = None
    top_k: int = 5
