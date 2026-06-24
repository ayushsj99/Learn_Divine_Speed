import argparse
import asyncio
import logging
from pathlib import Path

import yaml

from doc_ingestion_worker.pipeline.chunk_tag import chunk_and_tag
from doc_ingestion_worker.pipeline.dedup import dedup_sections
from doc_ingestion_worker.pipeline.embed import prepare_for_embedding
from doc_ingestion_worker.pipeline.eval_check import eval_check
from doc_ingestion_worker.pipeline.extract import extract_sections
from doc_ingestion_worker.pipeline.fetch import fetch_pages
from doc_ingestion_worker.pipeline.publish import publish_chunks
from doc_ingestion_worker.pipeline.render import render_pages
from doc_ingestion_worker.pipeline.validate import validate_sections

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s: %(message)s")
logger = logging.getLogger("doc_ingestion_worker.run")

SOURCES_PATH = Path(__file__).parent / "sources.yaml"


def load_sources() -> dict:
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def ingest(framework: str) -> None:
    sources = load_sources()
    config = sources.get(framework.lower())
    if config is None:
        raise RuntimeError(
            f"'{framework}' is not configured in sources.yaml — "
            f"add an entry before ingesting (framework is user-supplied at intake, "
            f"but only pre-approved sources are ingested automatically)."
        )
    version = config["version"]

    logger.info("fetching pages for '%s'", framework)
    pages = await fetch_pages(config)

    pages = render_pages(pages)
    sections = extract_sections(pages)
    sections = validate_sections(sections)
    sections = dedup_sections(sections)
    logger.info("%d section(s) after validate+dedup", len(sections))

    chunks = await chunk_and_tag(sections, framework)
    chunks = prepare_for_embedding(chunks)
    logger.info("%d chunk(s) ready to publish", len(chunks))

    result = await publish_chunks(framework, version, chunks)
    logger.info("published to collection '%s': %d points upserted", result["collection"], result["upserted"])

    await eval_check(result["collection"], expected_min_points=1)
    logger.info("eval_check passed — '%s@%s' is ready for use", framework, version)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a framework's docs into the retrieval index")
    parser.add_argument("--framework", required=True, help="Framework name, e.g. fastapi")
    args = parser.parse_args()
    asyncio.run(ingest(args.framework))


if __name__ == "__main__":
    main()
