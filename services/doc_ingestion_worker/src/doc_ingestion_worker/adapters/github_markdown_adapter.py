from doc_ingestion_worker.adapters.base import BaseAdapter, RawPage


class GithubMarkdownAdapter(BaseAdapter):
    """Pulls docs markdown/MDX directly from the project's repo at a release
    tag. Not yet implemented for v1 — FastAPI's llms_txt adapter covers the
    seed framework; this is the next adapter to fill in when onboarding a
    framework without an llms.txt."""

    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise NotImplementedError("github_markdown adapter not yet implemented")
