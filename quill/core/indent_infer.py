"""Indentation inference and announcement helpers (EDS-18).

EdSharp's Infer Indent (Alt+RightBracket) reports the document's indent unit and
can adopt it, while an opt-in mode announces indentation-level changes while
navigating by line. UI-framework agnostic so it can be unit-tested without
``wx``.
"""

from __future__ import annotations

from functools import reduce
from math import gcd

__all__ = [
    "describe_indent_change",
    "describe_indent_unit",
    "indent_columns",
    "infer_indent_unit",
]

DEFAULT_TAB_WIDTH = 4


def infer_indent_unit(text: str) -> str | None:
    """Return the inferred indent unit (``"\\t"`` or N spaces), or ``None``.

    If any indented line uses tabs and none use spaces, the unit is a tab.
    Otherwise the unit is the greatest common divisor of the space-indent widths.
    """
    tab_lines = 0
    space_widths: list[int] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        lead = line[: len(line) - len(line.lstrip())]
        if not lead:
            continue
        if "\t" in lead:
            tab_lines += 1
        elif lead.count(" ") == len(lead):
            space_widths.append(len(lead))
    if space_widths:
        unit = reduce(gcd, space_widths)
        if unit > 0:
            return " " * unit
    if tab_lines:
        return "\t"
    return None


def describe_indent_unit(unit: str | None) -> str:
    """Return a screen-reader-friendly phrase for an inferred indent unit."""
    if unit is None:
        return "no indentation"
    if unit == "\t":
        return "tab"
    count = len(unit)
    return f"{count} space" if count == 1 else f"{count} spaces"


def indent_columns(line: str, *, tab_width: int = DEFAULT_TAB_WIDTH) -> int:
    """Return the visual indentation width of ``line`` in columns."""
    columns = 0
    for char in line:
        if char == "\t":
            columns += tab_width - (columns % tab_width)
        elif char == " ":
            columns += 1
        else:
            break
    return columns


def describe_indent_change(previous: int, current: int) -> str | None:
    """Describe a change in indentation columns, or ``None`` if unchanged."""
    if current > previous:
        return f"Indent {current}"
    if current < previous:
        return f"Outdent {current}"
    return None
