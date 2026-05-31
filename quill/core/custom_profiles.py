from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from quill.core.features import (
    DEFAULT_PROFILE_ID,
    FEATURE_DEFINITIONS,
    FEATURE_STATE_OFF,
    PROFILE_DEFINITIONS,
    FeatureManager,
)
from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


@dataclass(slots=True)
class CustomProfile:
    id: str
    name: str
    description: str
    parent_profile_id: str
    inherits_parent: bool
    feature_profile_data: dict[str, object]
    settings_data: dict[str, object]
    keymap_data: dict[str, str]


def custom_profiles_path() -> Path:
    return app_data_dir() / "custom-profiles.json"


def load_custom_profiles() -> dict[str, CustomProfile]:
    raw = read_json(custom_profiles_path(), default={})
    if not isinstance(raw, dict):
        return {}
    entries = raw.get("profiles", [])
    if not isinstance(entries, list):
        return {}
    profiles: dict[str, CustomProfile] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        profile_id = str(entry.get("id", "")).strip()
        name = str(entry.get("name", "")).strip()
        if not profile_id or not name:
            continue
        parent_profile_id = str(entry.get("parent_profile_id", DEFAULT_PROFILE_ID))
        if parent_profile_id not in PROFILE_DEFINITIONS:
            parent_profile_id = DEFAULT_PROFILE_ID
        raw_feature_data = entry.get("feature_profile_data")
        feature_profile_data = (
            dict(raw_feature_data)
            if isinstance(raw_feature_data, dict)
            else build_parent_profile_data(parent_profile_id)
        )
        raw_settings_data = entry.get("settings_data")
        settings_data = dict(raw_settings_data) if isinstance(raw_settings_data, dict) else {}
        raw_keymap_data = entry.get("keymap_data")
        keymap_data: dict[str, str] = {}
        if isinstance(raw_keymap_data, dict):
            for command_id, binding in raw_keymap_data.items():
                if isinstance(command_id, str) and isinstance(binding, str):
                    keymap_data[command_id] = binding
        profiles[profile_id] = CustomProfile(
            id=profile_id,
            name=name,
            description=str(entry.get("description", "")).strip(),
            parent_profile_id=parent_profile_id,
            inherits_parent=bool(entry.get("inherits_parent", True)),
            feature_profile_data=feature_profile_data,
            settings_data=settings_data,
            keymap_data=keymap_data,
        )
    return profiles


def save_custom_profiles(profiles: dict[str, CustomProfile]) -> None:
    payload = {
        "schema_version": 1,
        "profiles": [asdict(profile) for profile in profiles.values()],
    }
    write_json_atomic(custom_profiles_path(), payload)


def generate_custom_profile_id(name: str, existing_ids: set[str]) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    base = "_".join(segment for segment in base.split("_") if segment)
    if not base:
        base = "custom_profile"
    candidate = f"custom_{base}"
    suffix = 2
    while candidate in existing_ids:
        candidate = f"custom_{base}_{suffix}"
        suffix += 1
    return candidate


def build_parent_profile_data(profile_id: str) -> dict[str, object]:
    if profile_id not in PROFILE_DEFINITIONS:
        profile_id = DEFAULT_PROFILE_ID
    manager = FeatureManager(active_profile_id=profile_id)
    return manager.export_profile_data()


def build_bare_bones_profile_data() -> dict[str, object]:
    overrides: dict[str, str] = {}
    for feature_id, definition in FEATURE_DEFINITIONS.items():
        if definition.locked_on:
            continue
        overrides[feature_id] = FEATURE_STATE_OFF
    return {
        "schema_version": 1,
        "active_profile_id": DEFAULT_PROFILE_ID,
        "previous_profile_id": None,
        "overrides": overrides,
        "show_quiet_features": True,
    }
