from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS Increase Contrast is macOS-only")

from quill.platform.macos.high_contrast import is_high_contrast_enabled


def test_returns_bool() -> None:
    assert isinstance(is_high_contrast_enabled(), bool)
