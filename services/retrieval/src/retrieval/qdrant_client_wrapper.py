import os
from functools import lru_cache
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from retrieval.embeddings import EMBEDDING_DIM


def collection_name(framework: str, version: str) -> str:
    safe_framework = framework.strip().lower().replace(" ", "_")
    safe_version = version.strip().lower().replace(" ", "_").replace(".", "_")
    return f"{safe_framework}_{safe_version}"


@lru_cache
def get_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
    return QdrantClient(url=url)


def ensure_collection(name: str) -> None:
    client = get_client()
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def collection_point_count(name: str) -> int:
    client = get_client()
    if not client.collection_exists(name):
        return 0
    return client.count(collection_name=name).count


def upsert_chunks(name: str, vectors: list[list[float]], payloads: list[dict]) -> int:
    ensure_collection(name)
    client = get_client()
    points = [
        PointStruct(id=str(uuid4()), vector=vector, payload=payload)
        for vector, payload in zip(vectors, payloads)
    ]
    client.upsert(collection_name=name, points=points)
    return len(points)


def search(name: str, query_vector: list[float], top_k: int, concept: str | None = None) -> list[dict]:
    client = get_client()
    if not client.collection_exists(name):
        return []
    query_filter = None
    if concept:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        query_filter = Filter(must=[FieldCondition(key="concept", match=MatchValue(value=concept))])
    results = client.query_points(
        collection_name=name, query=query_vector, limit=top_k, query_filter=query_filter
    ).points
    return [{"score": r.score, **(r.payload or {})} for r in results]
