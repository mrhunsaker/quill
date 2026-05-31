from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.onboarding import (
    load_assistant_onboarding_complete,
    load_onboarding_complete,
    mark_assistant_onboarding_complete,
    mark_onboarding_complete,
)


def test_onboarding_completion_is_stored_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    assert load_onboarding_complete() is False

    (tmp_path / "features.json").write_text(
        "{\"active_profile_id\": \"essential\"}",
        encoding="utf-8",
    )
    assert load_onboarding_complete() is False

    mark_onboarding_complete()

    assert load_onboarding_complete() is True
    assert (tmp_path / "onboarding-complete.json").exists()


def test_assistant_onboarding_completion_is_stored_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    assert load_assistant_onboarding_complete() is False

    mark_assistant_onboarding_complete()

    assert load_assistant_onboarding_complete() is True
    assert (tmp_path / "assistant-onboarding-complete.json").exists()
