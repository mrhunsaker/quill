from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS VoiceOver detection is macOS-only")

from quill.platform.macos.sr_detect import ScreenReaderDetection, detect_screen_reader


def test_detects_voiceover_from_snapshot() -> None:
    result = detect_screen_reader(process_snapshot="loginwindow\nVoiceOver\nFinder\n")
    assert result == ScreenReaderDetection(detected=True, name="VoiceOver", source="VoiceOver")


def test_no_screen_reader_when_absent() -> None:
    result = detect_screen_reader(process_snapshot="Finder\nDock\n")
    assert result.detected is False
    assert result.name == "none"
