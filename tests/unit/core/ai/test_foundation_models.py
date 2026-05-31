from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Apple Foundation Models is macOS-only")

from quill.core.ai.foundation_models import FoundationModelsBackend


def test_backend_reports_availability() -> None:
    available, reason = FoundationModelsBackend().is_available()
    assert isinstance(available, bool)
    if not available:
        assert isinstance(reason, str)


def test_respond_when_available() -> None:
    backend = FoundationModelsBackend()
    available, _ = backend.is_available()
    if not available:
        pytest.skip("Apple Intelligence not available on this machine")
    out = backend.respond("Reply with exactly the word: ok")
    assert isinstance(out, str) and out.strip() != ""
