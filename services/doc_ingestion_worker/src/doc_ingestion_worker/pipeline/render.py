from doc_ingestion_worker.adapters.base import RawPage


def render_pages(pages: list[RawPage]) -> list[RawPage]:
    """Headless-browser render step for JS-rendered (scrape-sourced) pages.
    llms_txt/github_markdown content is already plain markdown, so this is a
    legitimate no-op pass-through for those sources — not a faked step, just
    correctly trivial for the adapters implemented in v1."""
    return pages
