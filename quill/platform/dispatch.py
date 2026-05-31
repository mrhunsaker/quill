"""OS-agnostic access to Quill's platform integrations.

Selects the Windows or macOS implementation lazily at call time, so importing
this module never triggers platform-specific imports. Call sites can migrate
from ``quill.platform.windows.*`` to these helpers over time (see issue #42).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


def current_platform() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return "other"


def is_high_contrast_enabled() -> bool:
    platform = current_platform()
    if platform == "macos":
        from quill.platform.macos.high_contrast import is_high_contrast_enabled as impl
        return impl()
    if platform == "windows":
        from quill.platform.windows.high_contrast import is_high_contrast_enabled as impl
        return impl()
    return False


@dataclass(frozen=True, slots=True)
class ScreenReaderDetection:
    detected: bool
    name: str
    source: str


def detect_screen_reader() -> ScreenReaderDetection:
    platform = current_platform()
    if platform == "macos":
        from quill.platform.macos.sr_detect import detect_screen_reader as impl
    elif platform == "windows":
        from quill.platform.windows.sr_detect import detect_screen_reader as impl
    else:
        return ScreenReaderDetection(detected=False, name="none", source="")
    result = impl()
    return ScreenReaderDetection(
        detected=result.detected, name=result.name, source=result.source
    )
