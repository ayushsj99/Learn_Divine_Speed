import logging

from doc_ingestion_worker.pipeline.extract import Section

logger = logging.getLogger("doc_ingestion_worker.validate")

MIN_SECTION_CHARS = 40


def validate_sections(sections: list[Section]) -> list[Section]:
    """Quality gate: drop sections that are empty or too short to be useful
    content, rather than silently indexing near-empty/garbled pages."""
    valid = [s for s in sections if len(s.text) >= MIN_SECTION_CHARS]
    dropped = len(sections) - len(valid)
    if dropped:
        logger.warning("dropped %d section(s) failing the quality gate", dropped)
    return valid
