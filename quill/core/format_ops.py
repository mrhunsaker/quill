from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quill.core.links import infer_markup_kind


@dataclass(frozen=True, slots=True)
class MarkdownListContinuation:
    text: str
    caret: int
    exited_list: bool


_MARKDOWN_LIST_PATTERN = re.compile(
    r"^(?P<indent>[ \t]*)(?:(?P<number>\d+)(?P<num_sep>[.)])|(?P<bullet>[-+*]))"
    r"(?P<spacing>[ \t]+)(?:(?P<task>\[[ xX]\])(?P<task_spacing>[ \t]+))?(?P<body>.*)$"
)


def continue_markdown_list(text: str, caret: int) -> MarkdownListContinuation | None:
    if caret < 0 or caret > len(text):
        return None
    line_start, line_end = _line_bounds(text, caret, caret)
    line_text = text[line_start:line_end].rstrip("\r\n")
    match = _MARKDOWN_LIST_PATTERN.match(line_text)
    if match is None:
        return None

    marker_end = _marker_end_offset(match)
    line_offset = caret - line_start
    if line_offset < marker_end:
        return None

    before_body = line_text[marker_end:line_offset]
    after_body = line_text[line_offset:]
    if not before_body.strip() and not after_body.strip():
        indent = match.group("indent")
        updated = text[:line_start] + indent + text[line_end:]
        return MarkdownListContinuation(updated, line_start + len(indent), exited_list=True)

    continuation_marker = _continuation_marker(match)
    inserted = "\n" + continuation_marker
    updated = text[:caret] + inserted + text[caret:]
    return MarkdownListContinuation(updated, caret + len(inserted), exited_list=False)


def indent_lines(
    text: str,
    start: int,
    end: int,
    indent_unit: str = "    ",
) -> tuple[str, int, int]:
    line_start, line_end = _line_bounds(text, start, end)
    original = text[line_start:line_end]
    lines = _split_lines_keepends(original)
    updated = "".join(f"{indent_unit}{line}" for line in lines)
    merged = text[:line_start] + updated + text[line_end:]

    if start == end:
        caret = start + len(indent_unit)
        return merged, caret, caret

    return merged, line_start, line_start + len(updated)


def outdent_lines(
    text: str,
    start: int,
    end: int,
    indent_unit: str = "    ",
) -> tuple[str, int, int]:
    line_start, line_end = _line_bounds(text, start, end)
    original = text[line_start:line_end]
    lines = _split_lines_keepends(original)

    updated_parts: list[str] = []
    removed_first = 0
    for index, line in enumerate(lines):
        outdented, removed = _outdent_single_line(line, indent_unit)
        if index == 0:
            removed_first = removed
        updated_parts.append(outdented)
    updated = "".join(updated_parts)
    merged = text[:line_start] + updated + text[line_end:]

    if start == end:
        caret = max(line_start, start - removed_first)
        return merged, caret, caret

    return merged, line_start, line_start + len(updated)


def sort_lines(
    text: str,
    descending: bool = False,
    case_sensitive: bool = False,
) -> str:
    lines, terminal_newline = _split_body_lines(text)
    lines.sort(key=lambda line: _line_sort_key(line, case_sensitive), reverse=descending)
    return _join_body_lines(lines, terminal_newline)


def reverse_lines(text: str) -> str:
    lines, terminal_newline = _split_body_lines(text)
    lines.reverse()
    return _join_body_lines(lines, terminal_newline)


def remove_duplicate_lines(text: str, case_sensitive: bool = True) -> str:
    lines, terminal_newline = _split_body_lines(text)
    seen: set[str] = set()
    updated: list[str] = []
    for line in lines:
        key = _line_sort_key(line, case_sensitive)
        if key in seen:
            continue
        seen.add(key)
        updated.append(line)
    return _join_body_lines(updated, terminal_newline)


def trim_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip(" \t") for line in _split_lines(text))


def normalize_whitespace(text: str) -> str:
    updated = []
    for line in _split_lines(text):
        if not line.strip():
            updated.append("")
            continue
        updated.append(" ".join(line.split()))
    return "\n".join(updated)


def convert_indentation_to_spaces(text: str, indent_width: int = 4) -> str:
    indent_width = max(1, indent_width)
    lines = _split_lines(text)
    updated = []
    for line in lines:
        indent, rest = _split_leading_whitespace(line)
        updated.append(f"{indent.expandtabs(indent_width)}{rest}")
    return "\n".join(updated)


def convert_indentation_to_tabs(text: str, indent_width: int = 4) -> str:
    indent_width = max(1, indent_width)
    lines = _split_lines(text)
    updated = []
    for line in lines:
        indent, rest = _split_leading_whitespace(line)
        expanded = indent.expandtabs(indent_width)
        tabs, spaces = divmod(len(expanded), indent_width)
        updated.append("\t" * tabs + " " * spaces + rest)
    return "\n".join(updated)


def toggle_line_comment(
    text: str,
    start: int,
    end: int,
    path: Path | None,
) -> tuple[str, int, int]:
    line_start, line_end = _line_bounds(text, start, end)
    original = text[line_start:line_end]
    lines = _split_lines_keepends(original)
    style = _line_comment_style(path)

    if style == "html":
        all_commented = _all_html_commented(lines)
        updated = "".join(
            _uncomment_html_line(line) if all_commented else _comment_html_line(line)
            for line in lines
        )
    else:
        all_commented = _all_prefix_commented(lines, style)
        updated = "".join(
            _uncomment_prefix_line(line, style)
            if all_commented
            else _comment_prefix_line(line, style)
            for line in lines
        )

    merged = text[:line_start] + updated + text[line_end:]
    return merged, line_start, line_start + len(updated)


def toggle_block_comment(
    text: str,
    start: int,
    end: int,
    path: Path | None,
) -> tuple[str, int, int]:
    opening, closing = _block_comment_tokens(path)
    selected = text[start:end]
    if selected:
        stripped = selected.strip()
        if stripped.startswith(opening) and stripped.endswith(closing):
            inner = stripped[len(opening) : len(stripped) - len(closing)].strip()
            merged = text[:start] + inner + text[end:]
            return merged, start, start + len(inner)
        wrapped = f"{opening}{selected}{closing}"
        merged = text[:start] + wrapped + text[end:]
        return merged, start, start + len(wrapped)

    inserted = f"{opening}{closing}"
    merged = text[:start] + inserted + text[end:]
    caret = start + len(opening)
    return merged, caret, caret


def _line_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    left = min(start, end)
    right = max(start, end)
    line_start = text.rfind("\n", 0, left) + 1
    line_end = text.find("\n", right)
    if line_end == -1:
        line_end = len(text)
    else:
        line_end += 1
    return line_start, line_end


def _marker_end_offset(match: re.Match[str]) -> int:
    marker = match.group(0)
    body = match.group("body")
    return len(marker) - len(body)


def _continuation_marker(match: re.Match[str]) -> str:
    indent = match.group("indent")
    bullet = match.group("bullet")
    number = match.group("number")
    num_sep = match.group("num_sep") or "."
    spacing = match.group("spacing") or " "
    task = match.group("task")
    task_spacing = match.group("task_spacing") or " "
    if task is not None:
        return f"{indent}{bullet or '-'} [ ]{task_spacing}"
    if bullet is not None:
        return f"{indent}{bullet}{spacing}"
    next_number = int(number or "1") + 1
    return f"{indent}{next_number}{num_sep}{spacing}"


def _split_lines_keepends(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    return lines or [text]


def _split_lines(text: str) -> list[str]:
    if text == "":
        return [""]
    return text.split("\n")


def _split_body_lines(text: str) -> tuple[list[str], bool]:
    lines = _split_lines(text)
    if lines and lines[-1] == "":
        return lines[:-1], True
    return lines, False


def _join_body_lines(lines: list[str], terminal_newline: bool) -> str:
    updated = "\n".join(lines)
    if terminal_newline:
        return f"{updated}\n"
    return updated


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


def _split_leading_whitespace(text: str) -> tuple[str, str]:
    index = 0
    while index < len(text) and text[index] in {" ", "\t"}:
        index += 1
    return text[:index], text[index:]


def _line_sort_key(line: str, case_sensitive: bool) -> str:
    body, _ = _split_line_ending(line)
    return body if case_sensitive else body.casefold()


def _outdent_single_line(line: str, indent_unit: str) -> tuple[str, int]:
    if not line:
        return line, 0
    if line.startswith(indent_unit):
        return line[len(indent_unit) :], len(indent_unit)
    if line.startswith("\t"):
        return line[1:], 1
    spaces = len(line) - len(line.lstrip(" "))
    if spaces == 0:
        return line, 0
    remove_count = min(len(indent_unit), spaces)
    return line[remove_count:], remove_count


def _line_comment_style(path: Path | None) -> str:
    kind = infer_markup_kind(path)
    if kind in {"html", "markdown"}:
        return "html"

    extension = path.suffix.lower() if path is not None else ""
    if extension in {".sql", ".lua", ".hs"}:
        return "-- "
    if extension in {".py", ".rb", ".sh", ".yml", ".yaml", ".toml", ".ini", ".conf"}:
        return "# "
    return "// "


def _block_comment_tokens(path: Path | None) -> tuple[str, str]:
    style = _line_comment_style(path)
    if style == "html":
        return "<!-- ", " -->"
    return "/* ", " */"


def _all_html_commented(lines: list[str]) -> bool:
    relevant = [line for line in lines if line.strip()]
    if not relevant:
        return False
    return all(_is_html_commented_line(line) for line in relevant)


def _is_html_commented_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("<!--") and stripped.endswith("-->")


def _comment_html_line(line: str) -> str:
    newline = "\n" if line.endswith("\n") else ""
    content = line[:-1] if newline else line
    if not content.strip():
        return f"<!--  -->{newline}"
    return f"<!-- {content} -->{newline}"


def _uncomment_html_line(line: str) -> str:
    newline = "\n" if line.endswith("\n") else ""
    content = line[:-1] if newline else line
    stripped = content.strip()
    if stripped.startswith("<!--") and stripped.endswith("-->"):
        inner = stripped[4:-3].strip()
        return f"{inner}{newline}"
    return line


def _all_prefix_commented(lines: list[str], prefix: str) -> bool:
    relevant = [line for line in lines if line.strip()]
    if not relevant:
        return False
    return all(_is_prefix_commented_line(line, prefix) for line in relevant)


def _is_prefix_commented_line(line: str, prefix: str) -> bool:
    stripped = line.lstrip(" \t")
    return stripped.startswith(prefix)


def _comment_prefix_line(line: str, prefix: str) -> str:
    newline = "\n" if line.endswith("\n") else ""
    content = line[:-1] if newline else line
    indent_length = len(content) - len(content.lstrip(" \t"))
    indent = content[:indent_length]
    body = content[indent_length:]
    return f"{indent}{prefix}{body}{newline}"


def _uncomment_prefix_line(line: str, prefix: str) -> str:
    newline = "\n" if line.endswith("\n") else ""
    content = line[:-1] if newline else line
    indent_length = len(content) - len(content.lstrip(" \t"))
    indent = content[:indent_length]
    body = content[indent_length:]
    if body.startswith(prefix):
        return f"{indent}{body[len(prefix) :]}{newline}"
    return line
