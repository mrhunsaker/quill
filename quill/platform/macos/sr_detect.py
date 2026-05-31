"""Detect an active macOS screen reader (VoiceOver).

Mirrors the public surface of ``quill.platform.windows.sr_detect`` so call
sites can dispatch by platform without special-casing the return type.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScreenReaderDetection:
    detected: bool
    name: str
    source: str


# VoiceOver runs as "VoiceOver" with a helper "VoiceOverAgent".
_VOICEOVER_PROCESSES = ("VoiceOver", "VoiceOverAgent")


def detect_screen_reader(process_snapshot: str | None = None) -> ScreenReaderDetection:
    snapshot = process_snapshot if process_snapshot is not None else _process_snapshot()
    lowered = snapshot.lower()
    for process_name in _VOICEOVER_PROCESSES:
        if process_name.lower() in lowered:
            return ScreenReaderDetection(detected=True, name="VoiceOver", source=process_name)
    return ScreenReaderDetection(detected=False, name="none", source="")


def _process_snapshot() -> str:
    try:
        completed = subprocess.run(
            ["ps", "-axco", "command"],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
    except OSError:
        return ""
    return completed.stdout
