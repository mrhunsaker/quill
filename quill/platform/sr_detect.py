"""Platform-neutral screen-reader detection (routes to the OS implementation)."""
from __future__ import annotations

import sys

if sys.platform == "darwin":
    from quill.platform.macos.sr_detect import ScreenReaderDetection, detect_screen_reader
elif sys.platform.startswith("win"):
    from quill.platform.windows.sr_detect import ScreenReaderDetection, detect_screen_reader
else:  # pragma: no cover - other platforms
    from dataclasses import dataclass

    @dataclass(frozen=True, slots=True)
    class ScreenReaderDetection:
        detected: bool
        name: str
        source: str

    def detect_screen_reader(process_snapshot: str | None = None) -> "ScreenReaderDetection":
        return ScreenReaderDetection(detected=False, name="none", source="")


__all__ = ["ScreenReaderDetection", "detect_screen_reader"]
