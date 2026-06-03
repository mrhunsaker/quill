"""On-demand cursor/document speech queries (EDS-14) and go-to-percent (EDS-15).

EdSharp's Alt+A speaks the cursor address, Alt+Z the document status, and
Shift+Space the selection length, none of which move the cursor. Ctrl+J jumps to
a document percentage. These helpers are UI-framework agnostic so the exact
phrasing can be unit-tested without ``wx``.
"""

from __future__ import annotations

from quill.core.announcements import pluralize

__all__ = [
    "cursor_address",
    "describe_cursor_address",
    "describe_document_status",
    "describe_selection_length",
    "offset_for_percent",
]


def cursor_address(text: str, cursor: int) -> tuple[int, int, int]:
    """Return ``(line, column, percent)`` for ``cursor`` (1-based line/column)."""
    cursor = max(0, min(cursor, len(text)))
    line = text.count("\n", 0, cursor) + 1
    column = cursor - (text.rfind("\n", 0, cursor) + 1) + 1
    percent = 0 if not text else round(cursor / len(text) * 100)
    return line, column, percent


def describe_cursor_address(text: str, cursor: int) -> str:
    """Phrase the cursor address, for example ``"Line 3, column 5, 42%"``."""
    line, column, percent = cursor_address(text, cursor)
    return f"Line {line}, column {column}, {percent}%"


def describe_document_status(modified: bool, encoding: str) -> str:
    """Phrase the document status, for example ``"Modified, UTF-8"``."""
    state = "Modified" if modified else "Saved"
    return f"{state}, {encoding}"


def describe_selection_length(selection: str) -> str:
    """Phrase the selection length in characters and words."""
    if not selection:
        return "No selection"
    chars = pluralize(len(selection), "character")
    words = pluralize(len(selection.split()), "word")
    return f"Selection: {chars}, {words}"


def offset_for_percent(text: str, percent: float) -> int:
    """Return the character offset at ``percent`` (0-100) through ``text``."""
    clamped = max(0.0, min(100.0, float(percent)))
    if not text:
        return 0
    return min(len(text), round(len(text) * clamped / 100))
