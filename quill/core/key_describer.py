"""Reverse keymap lookup for Key Describer mode (EDS-17).

EdSharp's Key Describer (Ctrl+F1) speaks the action a key would perform instead
of performing it. The reverse lookup from an accelerator string to a command id
is pure and lives here so it can be unit-tested without ``wx``; the UI layer is
responsible only for turning a live key event into an accelerator string.
"""

from __future__ import annotations

__all__ = ["command_for_accelerator", "normalize_accelerator"]


def normalize_accelerator(accelerator: str) -> str:
    """Normalize an accelerator for case- and spacing-insensitive comparison.

    ``"Ctrl + Shift+P"`` and ``"ctrl+shift+p"`` compare equal. Multi-chord
    sequences separated by commas are normalized chord-by-chord.
    """
    chords = [chord.strip() for chord in accelerator.split(",")]
    normalized_chords = []
    for chord in chords:
        parts = [part.strip().lower() for part in chord.split("+") if part.strip()]
        normalized_chords.append("+".join(parts))
    return ", ".join(c for c in normalized_chords if c)


def command_for_accelerator(keymap: dict[str, str], accelerator: str) -> str | None:
    """Return the command id bound to ``accelerator`` in ``keymap``, or ``None``."""
    target = normalize_accelerator(accelerator)
    if not target:
        return None
    for command_id, binding in keymap.items():
        if binding and normalize_accelerator(binding) == target:
            return command_id
    return None
