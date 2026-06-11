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
    "file.open_from_remote": "Ctrl+Shift+Grave, Shift+O",  # QUILL-key chord (R taken by read-aloud)
    "file.save_to_remote": "Ctrl+Shift+Grave, W",  # QUILL-key chord
    "file.manage_remote_sites": "Ctrl+Shift+Grave, Shift+M",  # QUILL-key chord
    "file.close_document": "Ctrl+W",
    "file.print": "Ctrl+P",
    "window.next_document": "Ctrl+Shift+Grave, Tab",
    "window.previous_document": "Ctrl+Shift+Grave, Shift+Tab",
    "view.send_to_tray": "Ctrl+Shift+Grave, T",
    "view.toggle_soft_wrap": "Alt+Z",
    "view.toggle_tab_control": "Ctrl+Shift+Grave, Shift+T",
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
    "navigate.heading_organizer": "Ctrl+Shift+Grave, O",
    "navigate.list_bookmarks": "Alt+Shift+B",
    "tools.word_count": "Ctrl+Shift+W",
    "tools.spell_check_dialog": "F7",
    "tools.next_misspelling": "Alt+F7",
    "tools.previous_misspelling": "Shift+Alt+F7",
    "tools.misspelling_list": "Alt+Shift+L",
    "tools.thesaurus": "Shift+F7",
    "tools.read_aloud_start_pause": "Ctrl+Shift+Grave, R",  # §10.8.2: P→R
    "tools.read_aloud_stop": "Ctrl+Shift+Grave, Shift+R",  # §10.8.2: Shift+P→Shift+R
    "tools.dictation_toggle": "Ctrl+Shift+Grave, D",
    "tools.describe_image": "Ctrl+Shift+Grave, I",
    "tools.document_intake_report": "Ctrl+Shift+I",
    "help.switch_feature_profile": "Alt+Shift+P",
    "edit.copy_with_source": "Ctrl+Shift+C",
    "edit.copy_selection_for_email": "Ctrl+Shift+Grave, C",
    "edit.undo": "Ctrl+Z",
    "edit.redo": "Ctrl+Y",
    "edit.toggle_extend_selection_mode": "",  # no default binding; assign via keymap editor
    "edit.start_selection": "F8",
    "edit.complete_selection": "Shift+F8",
    "edit.reselect": "Ctrl+Shift+F8",
    "edit.go_to_start_of_selection": "Alt+Shift+F8",
    "edit.copy_all": "Ctrl+F8",
    "edit.unselect_all": "Ctrl+Shift+A",
    "edit.say_selected": "",  # Shift+Space — conditional intercept in _on_editor_key_down
    "edit.read_all": "Alt+F8",
    "edit.find": "Ctrl+F",
    "edit.find_next": "F3",
    "edit.find_previous": "Shift+F3",
    "edit.find_all_matches": "Alt+F3",
    "edit.replace": "Ctrl+H",
    "tools.search_in_files": "Ctrl+Shift+F",
    "tools.replace_in_files": "Ctrl+Shift+R",
    "tools.sticky_note_capture": "Ctrl+Shift+Grave, N",
    "edit.replace_all": "Ctrl+Shift+H",
    "edit.insert_link": "Ctrl+K",
    "edit.follow_link": "Ctrl+Enter",
    "edit.word_prediction": "Ctrl+Space",
    "view.preview": "Ctrl+Shift+V",
    "view.browser_preview": "Ctrl+Shift+Grave, V",  # §10.8.2: QUILL-key chord
    "view.split_preview": "Ctrl+Shift+Backslash",
    "view.focus_preview": "Ctrl+F6",
    "view.switch_editing_lens": "Ctrl+Shift+Grave, K",
    "edit.set_mark": "Ctrl+Shift+M",
    "edit.pop_mark": "Ctrl+M",
    "edit.exchange_point_mark": "Ctrl+Shift+X",
    "edit.list_marks": "Alt+M",
    "edit.select_paragraph": "",  # Ctrl+Alt+P removed (§10.8 screen-reader-hostile)
    "edit.select_block": "Ctrl+Shift+B",
    "edit.expand_selection": "Alt+Shift+Up",
    "edit.shrink_selection": "Alt+Shift+Down",
    "edit.set_named_mark": "",
    "edit.jump_to_named_mark": "",
    "edit.open_review_buffer": "",
    "edit.select_to_start_of_line": "Shift+Home",
    "edit.select_to_end_of_line": "Shift+End",
    "edit.select_to_start_of_document": "Ctrl+Shift+Home",
    "edit.select_to_end_of_document": "Ctrl+Shift+End",
    "format.toggle_line_comment": "Ctrl+/",
    "format.toggle_block_comment": "Shift+Alt+A",
    "format.indent": "Ctrl+]",
    "format.outdent": "Ctrl+[",
    "format.list_manager": "Ctrl+Shift+Grave, L",
    "format.bold": "Ctrl+B",
    "format.italic": "Ctrl+I",
    "format.heading_1": "Ctrl+Shift+Grave, 1",
    "format.heading_2": "Ctrl+Shift+Grave, 2",
    "format.heading_3": "Ctrl+Shift+Grave, 3",
    "format.heading_4": "Ctrl+Shift+Grave, 4",
    "format.heading_5": "Ctrl+Shift+Grave, 5",
    "format.heading_6": "Ctrl+Shift+Grave, 6",
    "format.decrease_heading_level": "Alt+Shift+Left",
    "format.increase_heading_level": "Alt+Shift+Right",
    "format.insert_html_tag": "Ctrl+Shift+Grave, H",
    "format.insert_markdown_tag": "Ctrl+Shift+Grave, M",
    "format.insert_snippet": "Ctrl+Shift+Grave, S",
    "format.manage_snippets": "Ctrl+Shift+Grave, Shift+S",
    "quill.quick_nav.heading": "H",
    "quill.quick_nav.link": "A",
    "quill.quick_nav.list": "L",
    "quill.quick_nav.list_item": "I",
    "quill.quick_nav.table": "T",
    "quill.quick_nav.block_quote": "Q",
    "quill.quick_nav.bookmark": "B",
    "quill.quick_nav.code_block": "'",
    "quill.quick_nav.table_of_contents": "C",
    "quill.quick_nav.paragraph": "P",
    "quill.quick_nav.sentence": "S",
    "quill.quick_nav.block": "TAB",
    "quill.quick_nav.skip_forward": "]",
    "quill.quick_nav.skip_backward": "[",
    # §8.1 — context help for current mode (Alt+H) and doc summary (Alt+I).
    "help.context_help": "Alt+H",
    "document.summary": "Alt+I",
    # §8.2 — universal "Go to anything" palette (Quill+G).
    "navigate.go_to_anything": "Ctrl+Shift+Grave, G",
    # §8.1 — QUILL-key cheatsheet overlay (Alt+?).
    "help.key_cheatsheet": "Alt+Shift+/",
    # §8.1 — live contrast check announcement.
    "view.announce_contrast": "Ctrl+Shift+Grave, Shift+C",
    # §8.2 — explain why the focused item is unavailable ("Why don't I see…?").
    "help.why_unavailable": "Alt+F1",
    # §10.8 — magic paste moves to QUILL key, V (handled in QuillKeyMixin prefix
    # state machine).  Ctrl+Alt+V removed — screen readers eat Ctrl+Alt+ chords.
    "edit.magic_paste": "",
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
    "app.menu_editor": "Customize Menus",
    "edit.copy_with_source": "Copy With Source",
    "edit.copy_selection_for_email": "Copy Selection For Email",
    "edit.find": "Find",
    "edit.find_all_matches": "Find All Matches",
    "edit.find_next": "Find Next",
    "edit.insert_link": "Insert Link",
    "edit.redo": "Redo",
    "edit.replace": "Replace",
    "edit.replace_all": "Replace All",
    "edit.word_prediction": "Word Prediction",
    "edit.start_selection": "Start Selection",
    "edit.complete_selection": "Complete Selection",
    "edit.reselect": "Reselect",
    "edit.go_to_start_of_selection": "Go to Start of Selection",
    "edit.copy_all": "Copy All",
    "edit.unselect_all": "Unselect All",
    "edit.say_selected": "Say Selected",
    "edit.read_all": "Read All",
    "edit.select_line": "Select Line",
    "edit.expand_selection": "Expand Selection",
    "edit.shrink_selection": "Shrink Selection",
    "edit.select_paragraph": "Select Paragraph",
    "edit.select_block": "Select Block",
    "edit.set_named_mark": "Set Named Mark",
    "edit.jump_to_named_mark": "Jump to Named Mark",
    "edit.open_review_buffer": "Open Review Buffer",
    "edit.selection_actions": "Selection Actions",
    "edit.undo": "Undo",
    "file.new": "New",
    "file.open": "Open",
    "file.save": "Save",
    "file.save_as": "Save As",
    "file.open_from_remote": "Open From Remote...",
    "file.save_to_remote": "Save To Remote",
    "file.save_copy_to_remote": "Save Copy To Remote...",
    "file.manage_remote_sites": "Manage Remote Sites...",
    "file.open_url": "Open From URL...",
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
    "navigate.quick_nav": "Quick Nav (Go to Anything)",
    "navigate.next_region": "Next Region",
    "navigate.next_structure": "Next Structure",
    "navigate.heading_organizer": "Heading Organizer",
    "navigate.outline_navigator": "Outline Navigator",
    "navigate.previous_region": "Previous Region",
    "navigate.previous_structure": "Previous Structure",
    "tools.document_intake_report": "Document Intake Report",
    "tools.describe_image": "Describe Image",
    "tools.previous_misspelling": "Previous Misspelling",
    "tools.next_misspelling": "Next Misspelling",
    "tools.misspelling_list": "Misspelling List",
    "tools.spell_check_dialog": "Spell Check",
    "tools.replace_in_files": "Replace Across Files",
    "tools.thesaurus": "Thesaurus",
    "tools.search_in_files": "Search In Files",
    "tools.word_count": "Word Count",
    "tools.writing_instructions": "Open Writing Instructions",
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
    legacy_rebindings = {
        "window.next_document": ("CTRL+TAB", "Ctrl+Shift+Grave, Tab"),
        "window.previous_document": ("CTRL+SHIFT+TAB", "Ctrl+Shift+Grave, Shift+Tab"),
        "view.send_to_tray": ("CTRL+ALT+T", "Ctrl+Shift+Grave, T"),
        "view.toggle_tab_control": ("CTRL+ALT+SHIFT+T", "Ctrl+Shift+Grave, Shift+T"),
        "navigate.heading_organizer": ("CTRL+ALT+SHIFT+H", "Ctrl+Shift+Grave, O"),
        "tools.read_aloud_start_pause": ("CTRL+ALT+P", "Ctrl+Shift+Grave, R"),
        "tools.read_aloud_stop": ("CTRL+ALT+S", "Ctrl+Shift+Grave, Shift+R"),
        "tools.dictation_toggle": ("CTRL+ALT+V", "Ctrl+Shift+Grave, D"),
        "edit.toggle_extend_selection_mode": ("F8", ""),
        "edit.copy_selection_for_email": ("CTRL+ALT+C", "Ctrl+Shift+Grave, C"),
        "tools.sticky_note_capture": ("CTRL+ALT+SHIFT+N", "Ctrl+Shift+Grave, N"),
        "view.browser_preview": ("CTRL+ALT+SHIFT+V", "Ctrl+Shift+Grave, V"),
        "format.list_manager": ("CTRL+ALT+L", "Ctrl+Shift+Grave, L"),
        "format.heading_1": ("CTRL+ALT+1", "Ctrl+Shift+Grave, 1"),
        "format.heading_2": ("CTRL+ALT+2", "Ctrl+Shift+Grave, 2"),
        "format.heading_3": ("CTRL+ALT+3", "Ctrl+Shift+Grave, 3"),
        "format.heading_4": ("CTRL+ALT+4", "Ctrl+Shift+Grave, 4"),
        "format.heading_5": ("CTRL+ALT+5", "Ctrl+Shift+Grave, 5"),
        "format.heading_6": ("CTRL+ALT+6", "Ctrl+Shift+Grave, 6"),
        "format.insert_html_tag": ("CTRL+ALT+H", "Ctrl+Shift+Grave, H"),
        "format.insert_markdown_tag": ("CTRL+ALT+M", "Ctrl+Shift+Grave, M"),
        "format.insert_snippet": ("CTRL+ALT+SPACE", "Ctrl+Shift+Grave, S"),
        "format.manage_snippets": ("CTRL+ALT+SHIFT+SPACE", "Ctrl+Shift+Grave, Shift+S"),
    }
    legacy_preview_conflict = (
        str(raw.get("view.preview", "")).strip().upper() == "CTRL+SHIFT+P"
        and str(raw.get("view.browser_preview", "")).strip().upper() == "CTRL+SHIFT+V"
    )
    for command_id, binding in raw.items():
        if isinstance(command_id, str) and isinstance(binding, str):
            normalized = binding
            if legacy_preview_conflict and command_id == "view.preview":
                normalized = "Ctrl+Shift+V"
            elif legacy_preview_conflict and command_id == "view.browser_preview":
                normalized = "Ctrl+Alt+Shift+V"
            legacy_binding = legacy_rebindings.get(command_id)
            if legacy_binding is not None and normalized.strip().upper() == legacy_binding[0]:
                normalized = legacy_binding[1]
            if not normalized.strip():
                merged[command_id] = ""
                continue
            conflict = find_keymap_conflict(merged, command_id, normalized)
            if conflict is None:
                merged[command_id] = normalized
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
