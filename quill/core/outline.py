from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OutlineEntry:
    level: int
    title: str
    position: int


_MD_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_HTML_HEADING_PATTERN = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_YAML_DOC_MARKERS = {"---", "..."}


def extract_outline_entries(text: str, markup_kind: str) -> list[OutlineEntry]:
    if markup_kind == "markdown":
        return [
            OutlineEntry(level=len(prefix), title=title.strip(), position=match.start())
            for match in _MD_HEADING_PATTERN.finditer(text)
            for prefix, title in [(match.group(1), match.group(2))]
        ]
    if markup_kind == "html":
        entries: list[OutlineEntry] = []
        for match in _HTML_HEADING_PATTERN.finditer(text):
            level = int(match.group(1))
            raw = _HTML_TAG_PATTERN.sub("", match.group(2))
            title = " ".join(raw.split())
            entries.append(
                OutlineEntry(level=level, title=title or "(empty heading)", position=match.start())
            )
        return entries
    if markup_kind == "yaml":
        from quill.core.yaml_structure import extract_yaml_outline_entries

        return extract_yaml_outline_entries(text)
    return []
