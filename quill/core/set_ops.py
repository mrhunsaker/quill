"""Set operations on lines, split at the cursor (EDS-12).

EdSharp's Alt+Shift+L and Alt+Shift+Q compute, respectively, the lines that are
in the first block but not the second, and the lines common to both blocks. The
document is split into two blocks at the cursor line. Results preserve the order
of their first appearance in the first block and drop duplicates.
"""

from __future__ import annotations

__all__ = [
    "format_lines",
    "lines_common_to_both",
    "lines_in_first_not_second",
]


def _split_on_cursor(text: str, cursor: int) -> tuple[list[str], list[str]]:
    cursor = max(0, min(cursor, len(text)))
    line_index = text.count("\n", 0, cursor)
    lines = text.split("\n")
    return lines[:line_index], lines[line_index:]


def _key(line: str, case_sensitive: bool) -> str:
    return line if case_sensitive else line.lower()


def lines_in_first_not_second(text: str, cursor: int, *, case_sensitive: bool = True) -> list[str]:
    """Return lines above the cursor that do not appear below it."""
    first, second = _split_on_cursor(text, cursor)
    second_keys = {_key(line, case_sensitive) for line in second}
    seen: set[str] = set()
    result: list[str] = []
    for line in first:
        key = _key(line, case_sensitive)
        if key not in second_keys and key not in seen:
            seen.add(key)
            result.append(line)
    return result


def lines_common_to_both(text: str, cursor: int, *, case_sensitive: bool = True) -> list[str]:
    """Return lines above the cursor that also appear below it."""
    first, second = _split_on_cursor(text, cursor)
    second_keys = {_key(line, case_sensitive) for line in second}
    seen: set[str] = set()
    result: list[str] = []
    for line in first:
        key = _key(line, case_sensitive)
        if key in second_keys and key not in seen:
            seen.add(key)
            result.append(line)
    return result


def format_lines(lines: list[str]) -> str:
    """Join result lines for emitting into a new buffer."""
    return "\n".join(lines)
