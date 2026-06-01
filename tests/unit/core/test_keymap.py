from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.keymap as keymap_module
from quill.core.keymap import (
    DEFAULT_KEYMAP,
    KEYBOARD_PACK_DEFAULT,
    KEYBOARD_PACKS,
    build_keymap_for_pack,
    export_keymap,
    find_keymap_conflict,
    import_keymap,
    keyboard_pack_names,
    keyboard_pack_preview,
    load_keymap,
    reset_keymap,
    save_keymap,
)


def _duplicates(mapping: dict[str, str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for command_id, binding in mapping.items():
        normalized = binding.strip().upper()
        if not normalized:
            continue
        grouped.setdefault(normalized, []).append(command_id)
    return {binding: commands for binding, commands in grouped.items() if len(commands) > 1}


def test_load_keymap_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    keymap = load_keymap()
    assert keymap == DEFAULT_KEYMAP
    assert _duplicates(keymap) == {}


def test_load_keymap_merges_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    save_keymap({"file.save": "Ctrl+Shift+Alt+S"})
    keymap = load_keymap()
    assert keymap["file.save"] == "Ctrl+Shift+Alt+S"
    assert keymap["file.open"] == DEFAULT_KEYMAP["file.open"]


def test_merge_keymaps_ignores_conflicting_bindings() -> None:
    merged = keymap_module.merge_keymaps(
        {
            "app.command_palette": "Ctrl+Shift+P",
            "view.preview": "Ctrl+Shift+P",
        }
    )
    assert merged["app.command_palette"] == "Ctrl+Shift+P"
    assert merged["view.preview"] == DEFAULT_KEYMAP["view.preview"]
    assert _duplicates(merged) == {}


def test_import_keymap_saves_merged_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_path = tmp_path / "keymap-store.json"
    source_path = tmp_path / "incoming.json"
    export_keymap(source_path, {"edit.find": "Ctrl+Alt+F"})
    monkeypatch.setattr(keymap_module, "keymap_path", lambda: store_path)

    merged = import_keymap(source_path)

    assert merged["edit.find"] == "Ctrl+Alt+F"
    saved = load_keymap()
    assert saved["edit.find"] == "Ctrl+Alt+F"
    assert saved["file.save"] == DEFAULT_KEYMAP["file.save"]


def test_reset_keymap_restores_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store_path = tmp_path / "keymap-store.json"
    monkeypatch.setattr(keymap_module, "keymap_path", lambda: store_path)
    save_keymap({"file.new": "Ctrl+Alt+N"})

    reset = reset_keymap()

    assert reset == DEFAULT_KEYMAP
    assert load_keymap() == DEFAULT_KEYMAP


def test_find_keymap_conflict_matches_existing_command() -> None:
    keymap = {"file.save": "Ctrl+S", "edit.find": "Ctrl+F"}
    conflict = find_keymap_conflict(keymap, "file.open", "Ctrl+S")
    assert conflict == "file.save"


def test_keyboard_pack_names_include_default() -> None:
    names = keyboard_pack_names()
    assert names[0] == KEYBOARD_PACK_DEFAULT
    assert "Windows Notepad" in names
    assert "VS Code" in names


def test_build_keymap_for_pack_applies_overlay() -> None:
    keymap = build_keymap_for_pack("VS Code")
    assert keymap["file.open"] == "Ctrl+P"
    assert keymap["format.duplicate_line"] == "Shift+Alt+Down"
    assert keymap["file.save"] == DEFAULT_KEYMAP["file.save"]


def test_previous_misspelling_shortcut_is_available() -> None:
    assert DEFAULT_KEYMAP["tools.previous_misspelling"] == "Shift+Alt+F7"


def test_replace_shortcut_is_available() -> None:
    assert DEFAULT_KEYMAP["edit.replace"] == "Ctrl+H"


def test_snippet_shortcuts_are_available() -> None:
    assert DEFAULT_KEYMAP["edit.word_prediction"] == "Ctrl+Space"
    assert DEFAULT_KEYMAP["format.insert_snippet"] == "Ctrl+Shift+Grave, S"
    assert DEFAULT_KEYMAP["format.manage_snippets"] == "Ctrl+Shift+Grave, Shift+S"


def test_sticky_note_shortcut_is_available() -> None:
    assert DEFAULT_KEYMAP["tools.sticky_note_capture"] == "Ctrl+Shift+Grave, N"


def test_indent_shortcuts_are_available() -> None:
    assert DEFAULT_KEYMAP["format.indent"] == "Ctrl+]"
    assert DEFAULT_KEYMAP["format.outdent"] == "Ctrl+["
    assert DEFAULT_KEYMAP["format.list_manager"] == "Ctrl+Shift+Grave, L"


def test_browser_preview_shortcut_is_available() -> None:
    assert DEFAULT_KEYMAP["view.preview"] == "Ctrl+Shift+V"
    assert DEFAULT_KEYMAP["view.browser_preview"] == "Ctrl+Shift+Grave, V"


def test_legacy_preview_conflict_migrates_to_in_app_preview() -> None:
    merged = keymap_module.merge_keymaps(
        {
            "view.preview": "Ctrl+Shift+P",
            "view.browser_preview": "Ctrl+Shift+V",
        }
    )
    assert merged["view.preview"] == "Ctrl+Shift+V"
    assert merged["view.browser_preview"] == "Ctrl+Shift+Grave, V"


def test_profile_picker_shortcut_is_available() -> None:
    assert DEFAULT_KEYMAP["help.switch_feature_profile"] == "Alt+Shift+P"


def test_keyboard_pack_preview_mentions_highlights() -> None:
    preview = keyboard_pack_preview("Quill Review")
    assert "Highlights:" in preview
    assert "Copy With Source" in preview


def test_keyboard_packs_are_known() -> None:
    assert KEYBOARD_PACK_DEFAULT in KEYBOARD_PACKS
    assert "Quill Writer" in KEYBOARD_PACKS
