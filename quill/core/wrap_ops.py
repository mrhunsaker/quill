"""Hard-wrap text to a maximum line width (EDS-5).

The inverse of join-lines: insert hard line breaks so that no line exceeds a
width, while preserving paragraph boundaries (blank lines). UI-framework
agnostic so it can be unit-tested without ``wx``.
"""

from __future__ import annotations

import textwrap

__all__ = ["hard_wrap", "widest_line_width"]


def widest_line_width(text: str) -> int:
    """Return the length of the longest line in ``text`` (0 for empty text)."""
    return max((len(line) for line in text.splitlines()), default=0)


def hard_wrap(text: str, width: int) -> str:
    """Hard-wrap ``text`` so no produced line exceeds ``width`` characters.

    Consecutive non-blank lines are treated as one paragraph and re-flowed; blank
    lines are preserved as paragraph separators. Long unbreakable words are left
    intact rather than split. A non-positive ``width`` returns ``text`` unchanged.
    """
    if width <= 0:
        return text
    out: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        joined = " ".join(line.strip() for line in paragraph)
        wrapped = textwrap.fill(
            joined,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        out.extend(wrapped.split("\n"))
        paragraph.clear()

    for line in text.split("\n"):
        if line.strip() == "":
            flush()
            out.append(line)
        else:
            paragraph.append(line)
    flush()
    return "\n".join(out)
