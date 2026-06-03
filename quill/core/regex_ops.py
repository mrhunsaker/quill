"""Regular-expression count and extract commands (EDS-13).

EdSharp's Ctrl+Shift+Y counts regex matches and Ctrl+Shift+E extracts all
matches into a new buffer. UI-framework agnostic so it can be unit-tested
without ``wx``. Invalid patterns raise :class:`RegexError`.
"""

from __future__ import annotations

import re

__all__ = ["RegexError", "count_matches", "extract_matches"]


class RegexError(ValueError):
    """Raised when a regular expression cannot be compiled."""


def _compile(pattern: str, flags: int) -> re.Pattern[str]:
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        raise RegexError(f"Invalid regular expression: {exc}") from exc


def count_matches(text: str, pattern: str, *, flags: int = 0) -> int:
    """Return the number of non-overlapping matches of ``pattern`` in ``text``."""
    return sum(1 for _ in _compile(pattern, flags).finditer(text))


def extract_matches(text: str, pattern: str, *, divider: str = "\n", flags: int = 0) -> str:
    """Return all whole matches of ``pattern`` joined by ``divider``.

    Whole matches (group 0) are extracted even when the pattern contains capture
    groups, matching EdSharp's behaviour.
    """
    matches = [match.group(0) for match in _compile(pattern, flags).finditer(text)]
    return divider.join(matches)
