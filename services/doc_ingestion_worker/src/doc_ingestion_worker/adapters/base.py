from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawPage:
    url: str
    content: str  # markdown or plain text


class BaseAdapter(ABC):
    """Each adapter fetches raw, un-chunked page content for a framework from
    one source type. Selection order (llms_txt > github_markdown >
    package_metadata > api > scrape > unsupported) is enforced by run.py,
    not by the adapters themselves."""

    @abstractmethod
    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise NotImplementedError


class UnsupportedAdapter(BaseAdapter):
    """Terminal fallback — raised explicitly, never silently substituted with
    a scrape or model-knowledge fallback."""

    async def fetch(self, framework_config: dict) -> list[RawPage]:
        raise RuntimeError("Framework has no permitted/available ingestion source")
