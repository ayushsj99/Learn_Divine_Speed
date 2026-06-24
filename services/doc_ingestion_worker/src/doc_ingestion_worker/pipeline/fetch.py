import logging

from doc_ingestion_worker.adapters.api_adapter import ApiAdapter
from doc_ingestion_worker.adapters.base import RawPage, UnsupportedAdapter
from doc_ingestion_worker.adapters.github_markdown_adapter import GithubMarkdownAdapter
from doc_ingestion_worker.adapters.llms_txt_adapter import LlmsTxtAdapter
from doc_ingestion_worker.adapters.package_metadata_adapter import PackageMetadataAdapter
from doc_ingestion_worker.adapters.scrape_adapter import ScrapeAdapter

logger = logging.getLogger("doc_ingestion_worker.fetch")

ADAPTERS = {
    "llms_txt": LlmsTxtAdapter(),
    "github_markdown": GithubMarkdownAdapter(),
    "package_metadata": PackageMetadataAdapter(),
    "api": ApiAdapter(),
    "scrape": ScrapeAdapter(),
    "unsupported": UnsupportedAdapter(),
}


async def fetch_pages(framework_config: dict) -> list[RawPage]:
    """Tries each adapter in the framework's declared priority order, falling
    through on failure to the next tier. Raises if every tier (including the
    terminal 'unsupported' marker) fails — ingestion never silently succeeds
    with no content."""
    last_error: Exception | None = None
    for adapter_name in framework_config["adapter_priority"]:
        adapter = ADAPTERS[adapter_name]
        try:
            pages = await adapter.fetch(framework_config)
            if pages:
                logger.info("fetched %d page(s) via '%s' adapter", len(pages), adapter_name)
                return pages
            logger.warning("'%s' adapter returned no pages, falling through", adapter_name)
        except (NotImplementedError, RuntimeError) as exc:
            logger.info("'%s' adapter unavailable (%s), falling through", adapter_name, exc)
            last_error = exc
    raise RuntimeError(f"No adapter could fetch docs for this framework: {last_error}")
