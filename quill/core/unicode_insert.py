"""Parse Unicode code points for the Insert Special Character command (EDS-1).

EdSharp's Insert Special Character (F2) accepts a code point as hexadecimal, or
as decimal when prefixed with ``d``. This module is UI-framework agnostic so the
parsing can be unit-tested without ``wx``.
"""

from __future__ import annotations

__all__ = ["CodepointError", "parse_codepoint"]

_MAX_CODEPOINT = 0x10FFFF


class CodepointError(ValueError):
    """Raised when a code point string cannot be turned into a character."""


def parse_codepoint(value: str) -> str:
    """Return the character for ``value``.

    ``value`` is interpreted as hexadecimal by default (``"41"`` -> ``"A"``), as
    decimal when prefixed with a lowercase ``d`` (``"d65"`` -> ``"A"``), or as a
    ``U+`` escape (``"U+1F600"``). Surrogate and out-of-range values are rejected.
    A leading uppercase ``D`` is treated as a hexadecimal digit, not a prefix.
    """
    raw = value.strip()
    if not raw:
        raise CodepointError("Enter a Unicode code point")
    try:
        if raw[0] == "d" and raw[1:].isdigit():
            number = int(raw[1:], 10)
        elif raw[:2].lower() == "u+":
            number = int(raw[2:], 16)
        else:
            number = int(raw, 16)
    except ValueError as exc:
        raise CodepointError(f"Invalid code point: {value}") from exc
    if number < 0 or number > _MAX_CODEPOINT:
        raise CodepointError(f"Code point out of range: {value}")
    if 0xD800 <= number <= 0xDFFF:
        raise CodepointError(f"Code point is an unpaired surrogate: {value}")
    return chr(number)
