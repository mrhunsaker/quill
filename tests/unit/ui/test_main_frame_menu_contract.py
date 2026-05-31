from __future__ import annotations

import re
from pathlib import Path


def test_menu_item_ids_have_menu_bindings() -> None:
    source = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
        encoding="utf-8"
    )
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


def test_top_level_menu_append_order_places_insert_and_view_before_search() -> None:
    source = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
        encoding="utf-8"
    )
    edit_index = source.index('menu_bar.Append(edit_menu, "&Edit")')
    insert_index = source.index('menu_bar.Append(insert_menu, "&Insert")')
    view_index = source.index('menu_bar.Append(view_menu, "&View")')
    search_index = source.index('menu_bar.Append(search_menu, "&Search")')
    navigate_index = source.index('menu_bar.Append(navigate_menu, "&Navigate")')

    assert edit_index < insert_index < view_index < search_index < navigate_index


def test_update_toggle_is_in_help_menu_not_view_menu() -> None:
    source = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
        encoding="utf-8"
    )
    assert 'view_menu.AppendCheckItem(self._id_toggle_auto_check_updates' not in source
    help_check_index = source.index('help_menu.Append(self._id_check_updates, "Check for &Updates...")')
    toggle_match = re.search(
        r"help_menu\.AppendCheckItem\(\s*self\._id_toggle_auto_check_updates",
        source,
    )

    assert toggle_match is not None
    assert toggle_match.start() < help_check_index


def test_replace_menu_uses_interactive_replace_command() -> None:
    source = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
        encoding="utf-8"
    )
    assert '_menu_label("&Replace...", "edit.replace")' in source
