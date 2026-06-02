from __future__ import annotations

from dataclasses import fields

from quill.core.settings import Settings
from quill.core.settings_registry import (
    SETTING_GROUPS,
    SETTING_SPECS,
    default_value,
    export_settings,
    find_spec,
    groups,
    import_settings,
    reset_all,
    reset_setting,
    search_specs,
    set_value,
    specs_for_group,
)


def test_every_spec_maps_to_a_real_settings_field() -> None:
    field_names = {field.name for field in fields(Settings)}
    for spec in SETTING_SPECS:
        assert spec.key in field_names, f"{spec.key} is not a Settings field"


def test_every_spec_belongs_to_a_declared_group() -> None:
    group_ids = {group.id for group in SETTING_GROUPS}
    for spec in SETTING_SPECS:
        assert spec.group in group_ids, f"{spec.key} -> unknown group {spec.group}"


def test_spec_keys_are_unique() -> None:
    keys = [spec.key for spec in SETTING_SPECS]
    assert len(keys) == len(set(keys))


def test_previously_unsurfaced_fields_are_registered() -> None:
    keys = {spec.key for spec in SETTING_SPECS}
    for key in ("auto_side_preview", "csv_open_mode", "word_open_mode"):
        assert key in keys, f"{key} should be surfaced in the Settings registry"


def test_set2_set3_set4_fields_are_registered() -> None:
    keys = {spec.key for spec in SETTING_SPECS}
    for key in (
        # SET-2 timing and pacing
        "autosave_interval_seconds",
        "quick_nav_debounce_ms",
        "quick_nav_min_chars",
        "announcement_throttle_ms",
        "read_aloud_sentence_pause_ms",
        "dictation_sensitivity",
        # SET-3 verbosity and announcements
        "announcement_verbosity",
        "announce_wrap",
        "announce_counts",
        "announce_mode_changes",
        "announce_spelling",
        "announce_punctuation_level",
        # SET-4 behavior toggles
        "browse_mode_sticky",
        "confirm_destructive_actions",
        "default_export_preset",
        "default_new_document_format",
        "autoformat_smart_quotes",
        "autoformat_dashes",
        "quick_nav_include_headings",
        "quick_nav_include_links",
        "quick_nav_include_lists",
    ):
        assert key in keys, f"{key} should be surfaced in the Settings registry"


def test_specs_for_group_filters() -> None:
    for group in groups():
        for spec in specs_for_group(group.id):
            assert spec.group == group.id


def test_choice_values_are_accepted_by_settings() -> None:
    base = Settings()
    for spec in SETTING_SPECS:
        if spec.kind != "choice":
            continue
        for stored_value, _label in spec.choices:
            updated = set_value(base, spec.key, stored_value)
            assert getattr(updated, spec.key) == stored_value


def test_search_matches_label_keyword_and_description() -> None:
    assert any(spec.key == "theme" for spec in search_specs("dark mode"))
    assert any(spec.key == "soft_wrap" for spec in search_specs("wrap"))
    assert search_specs("") == list(SETTING_SPECS)
    assert search_specs("zzzz-no-match") == []


def test_reset_setting_restores_default() -> None:
    spec = find_spec("recent_files_limit")
    assert spec is not None
    changed = set_value(Settings(), "recent_files_limit", 3)
    assert changed.recent_files_limit == 3
    restored = reset_setting(changed, "recent_files_limit")
    assert restored.recent_files_limit == default_value("recent_files_limit")


def test_reset_all_returns_defaults() -> None:
    assert reset_all() == Settings()


def test_set_value_clamps_out_of_range() -> None:
    clamped = set_value(Settings(), "recent_files_limit", 9999)
    assert clamped.recent_files_limit <= 50


def test_export_import_round_trip() -> None:
    original = set_value(Settings(), "theme", "dark")
    original = set_value(original, "recent_files_limit", 12)
    exported = export_settings(original)
    assert exported["schema_version"] == 1
    restored = import_settings(exported)
    assert restored == original


def test_import_accepts_bare_mapping_and_ignores_unknown() -> None:
    restored = import_settings({"theme": "light", "not_a_real_key": 1})
    assert restored.theme == "light"


def test_import_garbage_returns_defaults() -> None:
    assert import_settings(None) == Settings()
    assert import_settings([1, 2, 3]) == Settings()
