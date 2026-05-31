from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.custom_profiles as custom_profiles_module
from quill.core.custom_profiles import (
    build_bare_bones_profile_data,
    build_parent_profile_data,
    generate_custom_profile_id,
    load_custom_profiles,
    save_custom_profiles,
)
from quill.core.features import PROFILE_ESSENTIAL, PROFILE_WRITER


def test_generate_custom_profile_id_increments_suffix() -> None:
    existing = {"custom_writer", "custom_writer_2"}

    profile_id = generate_custom_profile_id("Writer", existing)

    assert profile_id == "custom_writer_3"


def test_build_parent_profile_data_targets_selected_profile() -> None:
    payload = build_parent_profile_data(PROFILE_WRITER)
    assert payload["active_profile_id"] == PROFILE_WRITER


def test_build_bare_bones_profile_data_turns_off_non_locked_features() -> None:
    payload = build_bare_bones_profile_data()
    assert payload["active_profile_id"] == PROFILE_ESSENTIAL
    overrides = payload.get("overrides")
    assert isinstance(overrides, dict)
    assert overrides.get("core.editor") == "off"


def test_save_and_load_custom_profiles_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_path = tmp_path / "custom-profiles.json"
    monkeypatch.setattr(custom_profiles_module, "custom_profiles_path", lambda: store_path)
    profiles = load_custom_profiles()
    assert profiles == {}

    sample = custom_profiles_module.CustomProfile(
        id="custom_writer",
        name="Custom Writer",
        description="Profile for writing flows.",
        parent_profile_id=PROFILE_WRITER,
        inherits_parent=True,
        feature_profile_data=build_parent_profile_data(PROFILE_WRITER),
        settings_data={"soft_wrap": True},
        keymap_data={"file.save": "Ctrl+S"},
    )
    save_custom_profiles({sample.id: sample})

    loaded = load_custom_profiles()
    assert sample.id in loaded
    assert loaded[sample.id].name == "Custom Writer"
    assert loaded[sample.id].parent_profile_id == PROFILE_WRITER
