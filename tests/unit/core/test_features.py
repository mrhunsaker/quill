from __future__ import annotations

import json

from quill.core.commands import CommandRegistry
from quill.core.features import (
    FEATURE_STATE_OFF,
    FEATURE_STATE_ON,
    FEATURE_STATE_QUIET,
    PROFILE_ACCESSIBILITY_PROFESSIONAL,
    PROFILE_DEFINITIONS,
    PROFILE_DEVELOPER_POWER_TEXT,
    PROFILE_ESSENTIAL,
    PROFILE_FULL_QUILL,
    FeatureManager,
    feature_for_command,
    find_feature,
)


def test_feature_mapping_infers_command_groups() -> None:
    assert feature_for_command("edit.find") == "core.search"
    assert feature_for_command("edit.replace") == "core.search"
    assert feature_for_command("edit.replace_all") == "core.search.regex"
    assert feature_for_command("tools.read_aloud_start_pause") == "core.read_aloud"
    assert feature_for_command("tools.announcement_backend") == "core.accessibility"
    assert feature_for_command("tools.announcement_trace_toggle") == "core.accessibility"
    assert feature_for_command("format.insert_table") == "core.format"
    assert feature_for_command("edit.word_prediction") == "core.intellisense"
    assert feature_for_command("help.open_logs_folder") == "core.help"
    assert feature_for_command("help.open_diagnostics_folder") == "core.help"
    assert feature_for_command("tools.yaml_structure_editor") == "core.format"
    assert feature_for_command("tools.ai_assistant") == "future.ai"
    assert feature_for_command("tools.ai_rewrite_selection") == "future.ai"
    assert feature_for_command("tools.ai_summarize_selection") == "future.ai"
    assert feature_for_command("tools.ai_continue_writing") == "future.ai"
    assert feature_for_command("tools.ai_fix_grammar") == "future.ai"
    assert feature_for_command("tools.run_python") == "future.ai"


def test_feature_manager_respects_profile_state() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_ESSENTIAL)
    assert manager.state_for("core.file") == FEATURE_STATE_ON
    assert manager.state_for("core.search.regex") == FEATURE_STATE_QUIET
    assert manager.state_for("future.ai") == FEATURE_STATE_QUIET


def test_feature_manager_can_switch_profiles() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_ESSENTIAL)
    preview = manager.change_profile_preview(PROFILE_DEVELOPER_POWER_TEXT)
    assert "Developer and Power Text" in preview
    comparison = manager.compare_profiles(PROFILE_ESSENTIAL, PROFILE_DEVELOPER_POWER_TEXT)
    assert "Comparing Essential to Developer and Power Text" in comparison
    manager.switch_profile(PROFILE_DEVELOPER_POWER_TEXT)
    assert manager.active_profile_id == PROFILE_DEVELOPER_POWER_TEXT


def test_change_profile_preview_reports_same_profile() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_ESSENTIAL)

    preview = manager.change_profile_preview(PROFILE_ESSENTIAL)

    assert preview.startswith("Essential is already active.")
    assert "No switch was made because this profile is already in use." in preview


def test_feature_manager_undo_and_reset_profile() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_ESSENTIAL)
    manager.switch_profile(PROFILE_DEVELOPER_POWER_TEXT)
    assert manager.undo_last_profile_change() is True
    assert manager.active_profile_id == PROFILE_ESSENTIAL
    manager.reset_to_essential_profile()
    assert manager.active_profile_id == PROFILE_ESSENTIAL


def test_feature_manager_finds_feature_by_alias() -> None:
    feature = find_feature("regex")
    assert feature is not None
    assert feature.id == "core.search.regex"


def test_feature_registry_includes_shipped_profiles() -> None:
    assert PROFILE_ESSENTIAL in PROFILE_DEFINITIONS
    assert PROFILE_DEVELOPER_POWER_TEXT in PROFILE_DEFINITIONS
    assert PROFILE_ACCESSIBILITY_PROFESSIONAL in PROFILE_DEFINITIONS
    assert PROFILE_FULL_QUILL in PROFILE_DEFINITIONS
    assert "reader_and_student" in PROFILE_DEFINITIONS
    assert "office_and_admin" in PROFILE_DEFINITIONS
    assert "low_vision" in PROFILE_DEFINITIONS
    assert "braille_screen_reader_power_user" in PROFILE_DEFINITIONS


def test_intellisense_feature_is_in_registry() -> None:
    assert "core.intellisense" in PROFILE_DEFINITIONS[PROFILE_FULL_QUILL].states


def test_feature_profile_import_and_export_roundtrip() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_DEVELOPER_POWER_TEXT)
    payload = manager.export_profile_data()
    payload["overrides"] = {"future.cleanup": "quiet", "core.profile": "off"}
    payload["schema_version"] = 1

    warnings = manager.import_profile_data(json.loads(json.dumps(payload)))

    assert warnings == []
    assert manager.active_profile_id == PROFILE_DEVELOPER_POWER_TEXT
    assert manager.state_for("future.cleanup") == FEATURE_STATE_QUIET
    assert manager.state_for("core.profile") == FEATURE_STATE_ON


def test_feature_dependency_enforcement_turns_on_required_features() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_ESSENTIAL)
    manager.overrides["core.search"] = FEATURE_STATE_OFF
    affected = manager.enable_feature("core.search.regex")

    assert "core.search" in affected
    assert manager.state_for("core.search") == FEATURE_STATE_ON
    assert manager.state_for("core.search.regex") == FEATURE_STATE_ON


def test_feature_dependency_enforcement_turns_off_dependents() -> None:
    manager = FeatureManager(active_profile_id=PROFILE_FULL_QUILL)
    affected = manager.disable_feature("core.search")

    assert "core.search" in affected
    assert "core.search.regex" in affected
    assert manager.state_for("core.search") == FEATURE_STATE_OFF
    assert manager.state_for("core.search.regex") == FEATURE_STATE_OFF


def test_feature_health_report_includes_coverage() -> None:
    registry = CommandRegistry()
    registry.register("edit.find", "Find", lambda: None)
    registry.register("tools.read_aloud_start_pause", "Read Aloud", lambda: None)

    report = FeatureManager(active_profile_id=PROFILE_ACCESSIBILITY_PROFESSIONAL).health_report(
        registry.list()
    )

    assert "Feature profile health check" in report
    assert "No coverage problems found." in report or "Commands without a feature mapping" in report
