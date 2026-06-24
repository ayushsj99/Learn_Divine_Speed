import hashlib

from doc_ingestion_worker.pipeline.extract import Section


def dedup_sections(sections: list[Section]) -> list[Section]:
    """Exact-content-hash dedup — drops near-duplicate pages (redirects, old
    version mirrors). No fuzzy/semantic dedup in v1."""
    seen: set[str] = set()
    deduped: list[Section] = []
    for section in sections:
        digest = hashlib.sha256(section.text.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        deduped.append(section)
    return deduped
