from __future__ import annotations

import re
from pathlib import Path


def _menu_source() -> str:
    ui = Path(__file__).resolve().parents[3] / "quill" / "ui"
    return (
        (ui / "main_frame.py").read_text(encoding="utf-8")
        + "\n"
        + (ui / "main_frame_menu.py").read_text(encoding="utf-8")
        + "\n"
        + (ui / "main_frame_ssh.py").read_text(encoding="utf-8")
        + "\n"
        + (ui / "main_frame_github.py").read_text(encoding="utf-8")
        + "\n"
        + (ui / "main_frame_devtools.py").read_text(encoding="utf-8")
    )


def test_menu_item_ids_have_menu_bindings() -> None:
    source = _menu_source()
    menu_ids = set(
        re.findall(
            r"\.(?:Append|AppendCheckItem|AppendRadioItem)\(\s*(self\._id_[A-Za-z0-9_]+)",
            source,
        )
    )
    bound_ids = set(
        re.findall(
            r"self\.frame\.Bind\(\s*wx\.EVT_MENU,.*?id\s*=\s*(self\._id_[A-Za-z0-9_]+)",
            source,
            flags=re.S,
        )
    )

    # These are handled by dynamic menu callbacks rather than direct id-specific
    # Bind(...) calls.
    dynamically_handled_ids = {
        "self._id_clear_recent",
        "self._id_clear_recent_sessions",
    }

    missing_bindings = menu_ids - bound_ids - dynamically_handled_ids
    assert missing_bindings == set()


def test_top_level_menu_append_order_is_conventional() -> None:
    # MENU-REORDER (menus.md Phase 1): top-level menus are attached in one place
    # in the conventional Windows order: File, Edit, View, Insert, Format,
    # Navigate, Search, (AI), Tools, Window, Help.
    source = _menu_source()
    edit_index = source.index('menu_bar.Append(edit_menu, "&Edit")')
    view_index = source.index('menu_bar.Append(view_menu, "&View")')
    insert_index = source.index('menu_bar.Append(insert_menu, "&Insert")')
    format_index = source.index('menu_bar.Append(format_menu, "F&ormat")')
    navigate_index = source.index('menu_bar.Append(navigate_menu, "&Navigate")')
    search_index = source.index('menu_bar.Append(search_menu, "&Search")')
    tools_index = source.index('menu_bar.Append(tools_menu, "&Tools")')

    assert (
        edit_index
        < view_index
        < insert_index
        < format_index
        < navigate_index
        < search_index
        < tools_index
    )


def test_update_toggle_is_in_help_menu_not_view_menu() -> None:
    source = _menu_source()
    assert "view_menu.AppendCheckItem(self._id_toggle_auto_check_updates" not in source
    support_marker = 'support_menu.Append(self._id_check_updates, "Check for &Updates")'
    help_marker = 'help_menu.Append(self._id_check_updates, "Check for &Updates...")'
    assert support_marker in source
    assert help_marker in source
    support_index = source.index(support_marker)
    help_index = source.index(help_marker)
    assert support_index < help_index


def test_replace_menu_uses_interactive_replace_command() -> None:
    source = _menu_source()
    assert '_menu_label("Rep&lace...", "edit.replace")' in source


def test_find_group_lives_in_edit_not_search() -> None:
    # menus.md Phase 3: in-document Find/Replace and the find-navigation commands
    # live in Edit; the Search menu is the cross-file search hub only.
    source = _menu_source()
    for fid in (
        "self._id_find",
        "self._id_replace",
        "self._id_find_next",
        "self._id_find_previous",
        "self._id_find_all_matches",
    ):
        assert re.search(rf"edit_menu\.Append\(\s*{re.escape(fid)}\b", source), fid
        assert not re.search(rf"search_menu\.Append\(\s*{re.escape(fid)}\b", source), fid
    assert re.search(r"search_menu\.Append\(\s*self\._id_search_in_files\b", source)
    assert re.search(r"search_menu\.Append\(\s*self\._id_replace_in_files\b", source)


def test_insert_link_is_not_duplicated_in_edit_menu() -> None:
    # MENU-3: Insert Link lives only in the Insert menu (its primary home); the
    # Edit menu must not also append the same edit.insert_link command.
    source = _menu_source()
    insert_link_appends = re.findall(
        r"(\w+_menu)\.Append\(\s*self\._id_insert_link\b",
        source,
    )
    assert insert_link_appends == ["insert_menu"], insert_link_appends
