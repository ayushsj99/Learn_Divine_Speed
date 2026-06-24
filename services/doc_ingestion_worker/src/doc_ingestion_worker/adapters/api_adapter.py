from doc_ingestion_worker.adapters.base import BaseAdapter, RawPage


class ApiAdapter(BaseAdapter):
    """Docs-as-JSON/OpenAPI export meant for tooling, when the docs platform
    exposes one. Not yet implemented for v1."""

    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise NotImplementedError("api adapter not yet implemented")
