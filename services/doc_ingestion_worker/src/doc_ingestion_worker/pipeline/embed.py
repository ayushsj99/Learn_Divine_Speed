from doc_ingestion_worker.pipeline.chunk_tag import TaggedChunk


def prepare_for_embedding(chunks: list[TaggedChunk]) -> list[TaggedChunk]:
    """Embedding itself is delegated to the Retrieval Service's /upsert
    endpoint (which calls the local Ollama nomic-embed-text model) — this
    keeps a single embedding code path shared between query-time and
    write-time, rather than duplicating model/normalization logic here. This
    step is the pass-through boundary documenting that delegation; it does
    not compute vectors."""
    return chunks
