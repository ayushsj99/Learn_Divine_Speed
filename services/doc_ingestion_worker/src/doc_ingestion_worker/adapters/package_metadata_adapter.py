from doc_ingestion_worker.adapters.base import BaseAdapter, RawPage


class PackageMetadataAdapter(BaseAdapter):
    """README/CHANGELOG/docstrings from the published package (npm/PyPI/etc).
    Thinner coverage fallback — not yet implemented for v1."""

    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise NotImplementedError("package_metadata adapter not yet implemented")
