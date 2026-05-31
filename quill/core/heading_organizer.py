from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HeadingBlock:
    source_index: int
    level: int
    title: str
    start: int
    end: int
    section_start: int
    section_end: int
    attributes: str = ""


_MD_HEADING_PATTERN = re.compile(r"^(?P<marker>#{1,6})[ \t]*(?P<title>.*)$", re.MULTILINE)
_HTML_HEADING_PATTERN = re.compile(
    r"<h(?P<level>[1-6])(?P<attrs>[^>]*)>(?P<body>.*?)</h(?P=level)>",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_heading_blocks(text: str, markup_kind: str) -> list[HeadingBlock]:
    if markup_kind == "markdown":
        return _parse_markdown_heading_blocks(text)
    if markup_kind == "html":
        return _parse_html_heading_blocks(text)
    return []


def validate_heading_sequence(
    blocks: list[HeadingBlock],
    *,
    require_single_h1: bool = False,
) -> list[str]:
    issues: list[str] = []
    if not blocks:
        return issues
    first = blocks[0]
    if first.level != 1:
        issues.append(f"Heading order should start at H1 (found H{first.level}: {first.title or '(empty)'})")
    h1_count = 0
    previous_level = 0
    for block in blocks:
        title = block.title.strip()
        if not title:
            issues.append(f"Heading H{block.level} is empty")
        if block.level == 1:
            h1_count += 1
        if previous_level and block.level > previous_level + 1:
            issues.append(
                f"Heading level skipped: H{previous_level} -> H{block.level} at "
                f"'{title or '(empty heading)'}'"
            )
        previous_level = block.level
    if require_single_h1 and h1_count > 1:
        issues.append(f"Expected a single H1 but found {h1_count}")
    return issues


def apply_heading_organizer_edits(
    text: str,
    markup_kind: str,
    updated_blocks: list[HeadingBlock],
) -> str:
    original_blocks = parse_heading_blocks(text, markup_kind)
    if not original_blocks or not updated_blocks:
        return text
    by_index = {block.source_index: block for block in original_blocks}
    first_start = min(block.section_start for block in original_blocks)
    last_end = max(block.section_end for block in original_blocks)
    rebuilt: list[str] = [text[:first_start]]
    for block in updated_blocks:
        original = by_index.get(block.source_index)
        if original is None:
            continue
        section = text[original.section_start : original.section_end]
        rebuilt.append(_rewrite_first_heading(section, markup_kind, block.level, block.title, original))
    rebuilt.append(text[last_end:])
    return "".join(rebuilt)


def _parse_markdown_heading_blocks(text: str) -> list[HeadingBlock]:
    matches = list(_MD_HEADING_PATTERN.finditer(text))
    blocks: list[HeadingBlock] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(
            HeadingBlock(
                source_index=index,
                level=len(match.group("marker")),
                title=(match.group("title") or "").strip(),
                start=start,
                end=end,
                section_start=start,
                section_end=section_end,
            )
        )
    return blocks


def _parse_html_heading_blocks(text: str) -> list[HeadingBlock]:
    matches = list(_HTML_HEADING_PATTERN.finditer(text))
    blocks: list[HeadingBlock] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_title = _HTML_TAG_PATTERN.sub("", match.group("body"))
        blocks.append(
            HeadingBlock(
                source_index=index,
                level=int(match.group("level")),
                title=" ".join(raw_title.split()),
                start=start,
                end=end,
                section_start=start,
                section_end=section_end,
                attributes=match.group("attrs") or "",
            )
        )
    return blocks


def _rewrite_first_heading(
    section: str,
    markup_kind: str,
    level: int,
    title: str,
    original: HeadingBlock,
) -> str:
    normalized_level = min(6, max(1, int(level)))
    normalized_title = title.strip()
    if markup_kind == "markdown":
        return _MD_HEADING_PATTERN.sub(
            f"{'#' * normalized_level} {normalized_title}",
            section,
            count=1,
        )
    if markup_kind == "html":
        replacement = f"<h{normalized_level}{original.attributes}>{normalized_title}</h{normalized_level}>"
        return _HTML_HEADING_PATTERN.sub(replacement, section, count=1)
    return section
