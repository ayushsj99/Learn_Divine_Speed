import logging
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from doc_ingestion_worker.adapters.base import BaseAdapter, RawPage

logger = logging.getLogger("doc_ingestion_worker.llms_txt")

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _robots_allows(url: str) -> bool:
    """Defensive check even though llms.txt is itself a permission signal —
    never bypass an explicit disallow, regardless of source type."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
    except Exception:
        # robots.txt unreachable/absent: treat as permissive rather than
        # blocking ingestion on a network hiccup.
        return True
    return parser.can_fetch("LearnGodSpeedBot/1.0", url)


class LlmsTxtAdapter(BaseAdapter):
    async def fetch(self, framework_config: dict) -> list[RawPage]:
        llms_txt_url = framework_config["llms_txt_url"]

        if not _robots_allows(llms_txt_url):
            raise RuntimeError(f"robots.txt disallows fetching {llms_txt_url}")

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(llms_txt_url)
            resp.raise_for_status()
            llms_txt_content = resp.text

            pages = [RawPage(url=llms_txt_url, content=llms_txt_content)]

            linked_urls = {
                urljoin(llms_txt_url, match.group(2))
                for match in MARKDOWN_LINK_RE.finditer(llms_txt_content)
            }
            for url in linked_urls:
                if not _robots_allows(url):
                    logger.warning("robots.txt disallows %s, skipping", url)
                    continue
                try:
                    page_resp = await client.get(url)
                    page_resp.raise_for_status()
                    pages.append(RawPage(url=url, content=page_resp.text))
                except httpx.HTTPError as exc:
                    logger.warning("failed to fetch %s: %s", url, exc)

        return pages
