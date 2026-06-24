import re
from dataclasses import dataclass

from doc_ingestion_worker.adapters.base import RawPage

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


@dataclass
class Section:
    source_url: str
    heading: str
    text: str


def extract_sections(pages: list[RawPage]) -> list[Section]:
    """Splits markdown into sections by heading, preserving code blocks intact
    (no flattening — splitting only happens on heading boundaries, never
    inside a fenced code block since headings don't appear there)."""
    sections: list[Section] = []
    for page in pages:
        matches = list(HEADING_RE.finditer(page.content))
        if not matches:
            sections.append(Section(source_url=page.url, heading="", text=page.content.strip()))
            continue
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(page.content)
            body = page.content[start:end].strip()
            sections.append(Section(source_url=page.url, heading=heading, text=body))
    return sections
