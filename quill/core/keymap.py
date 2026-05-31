from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

DEFAULT_KEYMAP: dict[str, str] = {
    "file.new": "Ctrl+N",
    "file.open": "Ctrl+O",
    "file.save": "Ctrl+S",
    "file.save_as": "Ctrl+Shift+S",
    "file.close_document": "Ctrl+W",
    "file.print": "Ctrl+P",
    "window.next_document": "Ctrl+Tab",
    "window.previous_document": "Ctrl+Shift+Tab",
    "view.send_to_tray": "Ctrl+Alt+T",
    "view.toggle_soft_wrap": "Alt+Z",
    "view.toggle_tab_control": "Ctrl+Alt+Shift+T",
    "app.command_palette": "Ctrl+Shift+P",
    "app.preferences": "Ctrl+,",
    "app.exit": "Alt+F4",
    "navigate.go_to_line": "Ctrl+G",
    "navigate.go_to_page": "Ctrl+Shift+G",
    "navigate.next_region": "F6",
    "navigate.previous_region": "Shift+F6",
    "navigate.back_location": "Alt+Left",
    "navigate.forward_location": "Alt+Right",
    "navigate.outline_navigator": "Ctrl+Shift+O",
    "navigate.match_bracket": "Ctrl+Shift+\\",
    "navigate.next_structure": "Alt+Down",
    "navigate.previous_structure": "Alt+Up",
    "navigate.heading_organizer": "Ctrl+Alt+Shift+H",
    "navigate.list_bookmarks": "Alt+Shift+B",
    "tools.word_count": "Ctrl+Shift+W",
    "tools.spell_check_dialog": "F7",
    "tools.next_misspelling": "Alt+F7",
    "tools.previous_misspelling": "Shift+Alt+F7",
    "tools.misspelling_list": "Alt+Shift+L",
    "tools.thesaurus": "Shift+F7",
    "tools.read_aloud_start_pause": "Ctrl+Alt+P",
    "tools.read_aloud_stop": "Ctrl+Alt+S",
    "tools.dictation_toggle": "Ctrl+Alt+V",
    "tools.document_intake_report": "Ctrl+Shift+I",
    "help.switch_feature_profile": "Alt+Shift+P",
    "edit.copy_with_source": "Ctrl+Shift+C",
    "edit.undo": "Ctrl+Z",
    "edit.redo": "Ctrl+Y",
    "edit.toggle_extend_selection_mode": "F8",
    "edit.find": "Ctrl+F",
    "edit.find_next": "F3",
    "edit.find_previous": "Shift+F3",
    "edit.find_all_matches": "Alt+F3",
    "edit.replace": "Ctrl+H",
    "tools.search_in_files": "Ctrl+Shift+F",
    "tools.replace_in_files": "Ctrl+Shift+R",
    "tools.sticky_note_capture": "Ctrl+Alt+Shift+N",
    "edit.replace_all": "Ctrl+Shift+H",
    "edit.insert_link": "Ctrl+K",
    "edit.follow_link": "Ctrl+Enter",
    "edit.word_prediction": "Ctrl+Space",
    "view.browser_preview": "Ctrl+Shift+V",
    "view.preview": "Ctrl+Shift+P",
    "view.split_preview": "Ctrl+Shift+Backslash",
    "view.focus_preview": "F6",
    "edit.set_mark": "Ctrl+Shift+M",
    "edit.pop_mark": "Ctrl+M",
    "edit.exchange_point_mark": "Ctrl+Shift+X",
    "edit.list_marks": "Alt+M",
    "edit.select_to_start_of_line": "Shift+Home",
    "edit.select_to_end_of_line": "Shift+End",
    "edit.select_to_start_of_document": "Ctrl+Shift+Home",
    "edit.select_to_end_of_document": "Ctrl+Shift+End",
    "format.toggle_line_comment": "Ctrl+/",
    "format.toggle_block_comment": "Shift+Alt+A",
    "format.indent": "Ctrl+]",
    "format.outdent": "Ctrl+[",
    "format.list_manager": "Ctrl+Alt+L",
    "format.bold": "Ctrl+B",
    "format.italic": "Ctrl+I",
    "format.heading_1": "Ctrl+Alt+1",
    "format.heading_2": "Ctrl+Alt+2",
    "format.heading_3": "Ctrl+Alt+3",
    "format.heading_4": "Ctrl+Alt+4",
    "format.heading_5": "Ctrl+Alt+5",
    "format.heading_6": "Ctrl+Alt+6",
    "format.decrease_heading_level": "Alt+Shift+Left",
    "format.increase_heading_level": "Alt+Shift+Right",
    "format.insert_html_tag": "Ctrl+Alt+H",
    "format.insert_markdown_tag": "Ctrl+Alt+M",
    "format.insert_snippet": "Ctrl+Alt+Space",
    "format.manage_snippets": "Ctrl+Alt+Shift+Space",
}

KEYBOARD_PACK_DEFAULT = "Quill Default"
KEYBOARD_PACK_CUSTOM = "Custom"


@dataclass(frozen=True, slots=True)
class KeyboardPack:
    name: str
    description: str
    bindings: dict[str, str]


_PACK_LABELS: dict[str, str] = {
    "app.command_palette": "Command Palette",
    "edit.copy_with_source": "Copy With Source",
    "edit.find": "Find",
    "edit.find_all_matches": "Find All Matches",
    "edit.find_next": "Find Next",
    "edit.insert_link": "Insert Link",
    "edit.redo": "Redo",
    "edit.replace": "Replace",
    "edit.replace_all": "Replace All",
    "edit.word_prediction": "Word Prediction",
    "edit.select_line": "Select Line",
    "edit.undo": "Undo",
    "file.new": "New",
    "file.open": "Open",
    "file.save": "Save",
    "file.save_as": "Save As",
    "format.bold": "Bold",
    "format.delete_line": "Delete Line",
    "format.duplicate_line": "Duplicate Line",
    "format.indent": "Indent",
    "format.italic": "Italic",
    "format.lower_case": "Lower Case",
    "format.move_line_down": "Move Line Down",
    "format.move_line_up": "Move Line Up",
    "format.outdent": "Outdent",
    "format.list_manager": "List Manager",
    "format.insert_snippet": "Insert Snippet",
    "format.manage_snippets": "Manage Snippets",
    "format.toggle_line_comment": "Toggle Line Comment",
    "format.upper_case": "Upper Case",
    "navigate.back_location": "Back",
    "navigate.forward_location": "Forward",
    "navigate.go_to_line": "Go To Line",
    "navigate.go_to_page": "Go To Page",
    "navigate.list_bookmarks": "List Bookmarks",
    "navigate.next_region": "Next Region",
    "navigate.next_structure": "Next Structure",
    "navigate.heading_organizer": "Heading Organizer",
    "navigate.outline_navigator": "Outline Navigator",
    "navigate.previous_region": "Previous Region",
    "navigate.previous_structure": "Previous Structure",
    "tools.document_intake_report": "Document Intake Report",
    "tools.previous_misspelling": "Previous Misspelling",
    "tools.next_misspelling": "Next Misspelling",
    "tools.misspelling_list": "Misspelling List",
    "tools.spell_check_dialog": "Spell Check",
    "tools.replace_in_files": "Replace Across Files",
    "tools.thesaurus": "Thesaurus",
    "tools.search_in_files": "Search In Files",
    "tools.word_count": "Word Count",
    "view.browser_preview": "Browser Preview",
    "view.preview": "Preview",
    "view.split_preview": "Preview Side by Side",
    "view.focus_preview": "Focus Preview",
    "help.switch_feature_profile": "Switch Feature Profile",
    "view.toggle_tab_control": "Tab Control",
}


KEYBOARD_PACKS: dict[str, KeyboardPack] = {
    KEYBOARD_PACK_DEFAULT: KeyboardPack(
        KEYBOARD_PACK_DEFAULT,
        (
            "Quill's balanced default layout: writing, navigation, and "
            "accessibility commands stay available without overloading the keyboard."
        ),
        {},
    ),
    "Quill Writer": KeyboardPack(
        "Quill Writer",
        (
            "A writing-first pack that keeps revision, spelling, links, "
            "and formatting under familiar document-editing keys."
        ),
        {
            "file.save_as": "F12",
            "edit.select_line": "Ctrl+L",
            "edit.insert_link": "Ctrl+K",
            "tools.spell_check_dialog": "F7",
            "tools.next_misspelling": "Alt+F7",
            "tools.thesaurus": "Shift+F7",
            "format.bold": "Ctrl+B",
            "format.italic": "Ctrl+I",
            "format.upper_case": "Ctrl+Shift+U",
        },
    ),
    "Quill Navigation": KeyboardPack(
        "Quill Navigation",
        (
            "Optimized for structural movement, screen-reader review, "
            "and rapid movement around long documents."
        ),
        {
            "navigate.next_region": "F6",
            "navigate.previous_region": "Shift+F6",
            "navigate.go_to_line": "Ctrl+G",
            "navigate.go_to_page": "Ctrl+Shift+G",
            "navigate.outline_navigator": "Ctrl+Shift+O",
            "navigate.back_location": "Alt+Left",
            "navigate.forward_location": "Alt+Right",
            "navigate.next_structure": "Alt+Down",
            "navigate.previous_structure": "Alt+Up",
            "edit.select_line": "Ctrl+L",
            "format.move_line_up": "Alt+Shift+Up",
            "format.move_line_down": "Alt+Shift+Down",
        },
    ),
    "Quill Review": KeyboardPack(
        "Quill Review",
        (
            "A review-and-analysis pack for outlines, intake reports, "
            "source-aware copying, and find-all workflows."
        ),
        {
            "tools.word_count": "Ctrl+Shift+W",
            "tools.document_intake_report": "Ctrl+Shift+I",
            "edit.copy_with_source": "Ctrl+Shift+C",
            "edit.find_all_matches": "Alt+F3",
            "navigate.outline_navigator": "Ctrl+Shift+O",
            "navigate.go_to_page": "Ctrl+Shift+G",
            "edit.select_line": "Ctrl+L",
        },
    ),
    "Windows Notepad": KeyboardPack(
        "Windows Notepad",
        (
            "A deliberately plain Windows-editor feel that preserves the classic "
            "file, find, replace, and go-to-line muscle memory."
        ),
        {
            "file.new": "Ctrl+N",
            "file.open": "Ctrl+O",
            "file.save": "Ctrl+S",
            "file.save_as": "Ctrl+Shift+S",
            "edit.undo": "Ctrl+Z",
            "edit.redo": "Ctrl+Y",
            "edit.find": "Ctrl+F",
            "edit.find_next": "F3",
            "edit.replace_all": "Ctrl+Shift+H",
            "navigate.go_to_line": "Ctrl+G",
        },
    ),
    "Notepad++": KeyboardPack(
        "Notepad++",
        (
            "A quick, utility-style text editing pack centered on "
            "duplicate/delete-line commands and Windows-friendly search shortcuts."
        ),
        {
            "navigate.go_to_line": "Ctrl+G",
            "edit.find_all_matches": "Alt+F3",
            "format.duplicate_line": "Ctrl+D",
            "format.delete_line": "Ctrl+L",
            "format.move_line_up": "Alt+Up",
            "format.move_line_down": "Alt+Down",
        },
    ),
    "VS Code": KeyboardPack(
        "VS Code",
        (
            "A modern development-oriented pack with quick open, command "
            "palette, outline navigation, and line manipulation."
        ),
        {
            "app.command_palette": "Ctrl+Shift+P",
            "file.open": "Ctrl+P",
            "navigate.go_to_line": "Ctrl+G",
            "navigate.outline_navigator": "Ctrl+Shift+O",
            "edit.select_line": "Ctrl+L",
            "format.duplicate_line": "Shift+Alt+Down",
            "format.move_line_up": "Alt+Up",
            "format.move_line_down": "Alt+Down",
            "format.toggle_line_comment": "Ctrl+/",
            "format.indent": "Ctrl+]",
            "format.outdent": "Ctrl+[",
        },
    ),
    "Microsoft Word": KeyboardPack(
        "Microsoft Word",
        (
            "A document-centric pack that leans on familiar Word shortcuts "
            "for save-as, links, formatting, and spelling tools."
        ),
        {
            "file.save_as": "F12",
            "edit.insert_link": "Ctrl+K",
            "tools.spell_check_dialog": "F7",
            "tools.thesaurus": "Shift+F7",
            "format.bold": "Ctrl+B",
            "format.italic": "Ctrl+I",
        },
    ),
}

def keymap_path() -> Path:
    return app_data_dir() / "keymap.json"


def load_keymap() -> dict[str, str]:
    raw = read_json(keymap_path(), default={})
    return merge_keymaps(raw)


def save_keymap(keymap: dict[str, str]) -> None:
    write_json_atomic(keymap_path(), keymap)


def keyboard_pack_names(include_custom: bool = False) -> list[str]:
    names = list(KEYBOARD_PACKS)
    if include_custom:
        names.append(KEYBOARD_PACK_CUSTOM)
    return names


def keyboard_pack_description(name: str) -> str:
    if name == KEYBOARD_PACK_CUSTOM:
        return "A hand-tuned keyboard layout created from manual edits or imported bindings."
    pack = KEYBOARD_PACKS.get(name)
    if pack is None:
        return KEYBOARD_PACKS[KEYBOARD_PACK_DEFAULT].description
    return pack.description


def keyboard_pack_preview(name: str) -> str:
    if name == KEYBOARD_PACK_CUSTOM:
        return keyboard_pack_description(name)
    pack = KEYBOARD_PACKS.get(name)
    if pack is None:
        pack = KEYBOARD_PACKS[KEYBOARD_PACK_DEFAULT]
    if not pack.bindings:
        return pack.description
    lines = [pack.description, "", "Highlights:"]
    for command_id, binding in pack.bindings.items():
        label = _PACK_LABELS.get(command_id, command_id)
        lines.append(f"- {label}: {binding}")
    return "\n".join(lines)


def build_keymap_for_pack(name: str) -> dict[str, str]:
    pack = KEYBOARD_PACKS.get(name)
    merged = DEFAULT_KEYMAP.copy()
    if pack is None:
        return merged
    merged.update(pack.bindings)
    return merged


def merge_keymaps(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return DEFAULT_KEYMAP.copy()
    merged = DEFAULT_KEYMAP.copy()
    for command_id, binding in raw.items():
        if isinstance(command_id, str) and isinstance(binding, str):
            merged[command_id] = binding
    return merged


def export_keymap(target: Path, keymap: dict[str, str]) -> None:
    write_json_atomic(target, keymap)


def import_keymap(source: Path) -> dict[str, str]:
    raw = read_json(source, default={})
    merged = merge_keymaps(raw)
    save_keymap(merged)
    return merged


def reset_keymap() -> dict[str, str]:
    defaults = DEFAULT_KEYMAP.copy()
    save_keymap(defaults)
    return defaults


def find_keymap_conflict(
    keymap: dict[str, str],
    command_id: str,
    binding: str,
) -> str | None:
    candidate = binding.strip().upper()
    if not candidate:
        return None
    for existing_command, existing_binding in keymap.items():
        if existing_command == command_id:
            continue
        if existing_binding.strip().upper() == candidate:
            return existing_command
    return None
