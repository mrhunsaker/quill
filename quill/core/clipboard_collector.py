"""Clipboard collector mode append logic (EDS-11).

EdSharp's paste-board mode (Alt+7) appends every subsequent clipboard copy into
the document, separated by a divider. This wx-free helper holds the pure append
logic so the divider behaviour can be unit-tested without ``wx``.
"""

from __future__ import annotations

__all__ = ["DEFAULT_DIVIDER", "append_collected"]

DEFAULT_DIVIDER = "\n\n----\n\n"


def append_collected(document_text: str, clip_text: str, *, divider: str = DEFAULT_DIVIDER) -> str:
    """Return ``document_text`` with ``clip_text`` appended after a divider.

    An empty ``clip_text`` leaves the document unchanged. When the document is
    empty the clip is used as-is, with no leading divider.
    """
    if not clip_text:
        return document_text
    if not document_text:
        return clip_text
    return document_text + divider + clip_text
