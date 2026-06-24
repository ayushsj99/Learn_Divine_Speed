from doc_ingestion_worker.adapters.base import BaseAdapter, RawPage


class ScrapeAdapter(BaseAdapter):
    """Headless-browser scrape, only usable when robots.txt/ToS explicitly
    permit it. Not yet implemented for v1 — when implemented, it must check
    robots.txt and skip-with-log on disallow, never bypass it."""

    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise NotImplementedError("scrape adapter not yet implemented")
