"""Pure typography autoformat helpers (SET-4).

These are wx-free transforms applied as the user types: straight quotes become
curly quotes and a double hyphen becomes an em dash. The UI layer owns the
insertion-point manipulation; these functions only decide the replacement.
"""

from __future__ import annotations

__all__ = [
    "LEFT_DOUBLE",
    "RIGHT_DOUBLE",
    "LEFT_SINGLE",
    "RIGHT_SINGLE",
    "EM_DASH",
    "smart_quote_for",
    "is_dash_merge",
]

LEFT_DOUBLE = "\u201c"
RIGHT_DOUBLE = "\u201d"
LEFT_SINGLE = "\u2018"
RIGHT_SINGLE = "\u2019"
EM_DASH = "\u2014"

#: Characters before which a straight quote should open (rather than close).
_OPENING_CONTEXT = " \t\n\r([{" + LEFT_DOUBLE + LEFT_SINGLE


def smart_quote_for(preceding_char: str, typed_quote: str) -> str:
    """Return the curly replacement for a straight quote typed at a position.

    ``preceding_char`` is the character immediately before the insertion point
    (empty string at the start of the buffer). A quote opens at the start of a
    word (start of buffer, after whitespace, or after an opening bracket) and
    closes otherwise. Non-quote input is returned unchanged.
    """
    if typed_quote == '"':
        opening, closing = LEFT_DOUBLE, RIGHT_DOUBLE
    elif typed_quote == "'":
        opening, closing = LEFT_SINGLE, RIGHT_SINGLE
    else:
        return typed_quote
    if preceding_char == "" or preceding_char in _OPENING_CONTEXT:
        return opening
    return closing


def is_dash_merge(preceding_char: str) -> bool:
    """Return ``True`` when a typed hyphen should merge with the prior one."""
    return preceding_char == "-"
