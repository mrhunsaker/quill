from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import quill.ui.main_frame as main_frame_module
from quill.core.a11y_regions import RegionTracker
from quill.core.document import Document
from quill.core.epub import EpubBook, EpubChapter, EpubHeading
from quill.core.features import FEATURE_DEFINITIONS, PROFILE_DEFINITIONS, feature_for_command
from quill.core.locations import LocationRing
from quill.core.search import SearchOptions
from quill.core.spellcheck import Misspelling
from quill.ui.main_frame import MainFrame


@pytest.fixture(autouse=True)
def _isolated_quill_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))


class _Editor:
    def __init__(self, text: str, insertion_point: int = 0) -> None:
        self._text = text
        self._insertion_point = insertion_point
        self.selection: tuple[int, int] = (insertion_point, insertion_point)
        self.focused = False

    def GetValue(self) -> str:
        return self._text

    def GetInsertionPoint(self) -> int:
        return self._insertion_point

    def SetInsertionPoint(self, value: int) -> None:
        self._insertion_point = value

    def SetSelection(self, start: int, end: int) -> None:
        self.selection = (start, end)

    def ChangeValue(self, value: str) -> None:
        self._text = value

    def Replace(self, start: int, end: int, value: str) -> None:
        self._text = f"{self._text[:start]}{value}{self._text[end:]}"
        self._insertion_point = start + len(value)

    def SetFocus(self) -> None:
        self.focused = True

    def GetSelection(self) -> tuple[int, int]:
        return self.selection


class _StatusBar:
    def __init__(self) -> None:
        self.focused = False
        self.status: dict[int, str] = {}

    def SetFocus(self) -> None:
        self.focused = True

    def SetStatusText(self, value: str, index: int = 0) -> None:
        self.status[index] = value

    def SetFieldsCount(self, count: int) -> None:
        self.fields_count = count

    def SetStatusWidths(self, widths: list[int]) -> None:
        self.widths = widths


class _Frame:
    def __init__(self) -> None:
        self.focused = False
        self.title = ""

    def SetFocus(self) -> None:
        self.focused = True

    def SetTitle(self, title: str) -> None:
        self.title = title


class _Notebook:
    def __init__(self) -> None:
        self.pages: list[object] = []
        self.selection = 0
        self.titles: list[str] = []
        self.visible = True

    def Bind(self, *_args: object, **_kwargs: object) -> None:
        return None

    def Show(self, value: bool = True) -> None:
        self.visible = value

    def Hide(self) -> None:
        self.visible = False

    def AddPage(self, page: object, title: str, select: bool = False) -> None:
        self.pages.append(page)
        self.titles.append(title)
        if select:
            self.selection = len(self.pages) - 1

    def DeletePage(self, index: int) -> None:
        del self.pages[index]
        del self.titles[index]
        if self.selection >= len(self.pages):
            self.selection = max(0, len(self.pages) - 1)

    def GetSelection(self) -> int:
        return self.selection

    def SetSelection(self, index: int) -> None:
        self.selection = index

    def ChangeSelection(self, index: int) -> None:
        self.selection = index

    def GetPageCount(self) -> int:
        return len(self.pages)

    def SetPageText(self, index: int, title: str) -> None:
        self.titles[index] = title

    def GetPageText(self, index: int) -> str:
        return self.titles[index]


class _MenuItem:
    def __init__(self, menu_id: int, label: str) -> None:
        self.menu_id = menu_id
        self.label = label

    def Enable(self, _enabled: bool) -> None:
        return None


class _Menu:
    def __init__(self) -> None:
        self.items: list[_MenuItem] = []

    def GetMenuItemCount(self) -> int:
        return len(self.items)

    def FindItemByPosition(self, position: int) -> _MenuItem | None:
        if position < 0 or position >= len(self.items):
            return None
        return self.items[position]

    def DestroyItem(self, item: _MenuItem) -> None:
        self.items.remove(item)

    def Append(self, menu_id: int, label: str) -> _MenuItem:
        item = _MenuItem(menu_id, label)
        self.items.append(item)
        return item

    def AppendSeparator(self) -> None:
        return None


def _build_frame(text: str, insertion_point: int = 0) -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame.document = Document(path=Path("note.md"))
    frame.editor = _Editor(text=text, insertion_point=insertion_point)
    frame.statusbar = _StatusBar()
    frame.frame = _Frame()
    frame.notebook = _Notebook()
    frame._sessions_menu = _Menu()
    frame._session_menu_ids = {}
    frame._location_ring = LocationRing()
    frame._region_tracker = RegionTracker()
    frame._focus_regions = ("Editor", "Status Bar")
    frame._active_region_index = 0
    frame._region_tracker.enter("Editor")
    frame._status_message = "Ready"
    frame._overwrite_mode = False
    frame._insert_key_down = False
    frame._extend_selection_mode = False
    frame._extend_selection_anchor = None
    frame._compare_session = None
    frame._compare_ignore_trailing_spaces = True
    frame._compare_ignore_line_endings = True
    frame._document_tabs = [type("Tab", (), {"editor": frame.editor, "document": frame.document})()]
    frame._active_tab_index = 0
    frame.notebook.AddPage(object(), frame.document.name, select=True)
    frame.settings = type(
        "Settings",
        (),
        {
            "persistent_undo": False,
            "wrap_find": True,
            "show_tab_control": False,
            "title_bar_path_mode": "name",
            "dirty_title_style": "text",
            "status_bar_order": ["message", "line_column", "mode", "selection", "file_path"],
            "status_bar_hidden": ["selection"],
        },
    )()
    return frame


def test_navigate_next_region_focuses_status_bar() -> None:
    frame = _build_frame("hello")
    frame.navigate_next_region()
    assert frame._active_region_index == 1
    assert frame.statusbar.focused is True


def test_match_bracket_moves_to_match() -> None:
    text = "alpha (one [two] three)"
    frame = _build_frame(text, insertion_point=text.index("["))
    frame.match_bracket()
    assert frame.editor.GetInsertionPoint() == text.index("]")


def test_navigate_next_structure_moves_to_heading() -> None:
    text = "intro\n## Heading\nbody"
    frame = _build_frame(text, insertion_point=0)
    frame.navigate_next_structure()
    assert frame.editor.GetInsertionPoint() == text.index("## Heading")


def test_persistent_undo_steps_across_history() -> None:
    frame = _build_frame("one", insertion_point=0)
    frame.settings = type(
        "Settings",
        (),
        {
            "persistent_undo": True,
            "wrap_find": True,
            "show_tab_control": False,
            "title_bar_path_mode": "name",
            "dirty_title_style": "text",
            "status_bar_order": ["message", "line_column", "mode", "selection", "file_path"],
            "status_bar_hidden": ["selection"],
        },
    )()
    frame._persistent_undo_history = ["one", "two", "three"]
    frame._persistent_undo_index = 2
    frame._suspend_persistent_undo = False
    frame._step_persistent_undo(-1)
    assert frame.editor.GetValue() == "two"


def test_statusbar_shows_line_and_column() -> None:
    frame = _build_frame("one\ntwo", insertion_point=5)
    frame._apply_statusbar_layout()
    assert frame.statusbar.fields_count == 6
    assert frame.statusbar.status[1] == "Ln 2, Col 2"
    assert frame.statusbar.status[2] == "INS"


def test_statusbar_respects_order_and_hidden_items() -> None:
    frame = _build_frame("hello", insertion_point=1)
    frame.settings.status_bar_order = ["line_column", "mode", "file_path", "message", "selection"]
    frame.settings.status_bar_hidden = ["file_path", "selection"]
    frame._apply_statusbar_layout()
    assert frame.statusbar.fields_count == 5
    assert frame.statusbar.status[0] == "Ln 1, Col 2"
    assert frame.statusbar.status[1] == "INS"


def test_refresh_title_uses_full_path_when_enabled() -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.document.modified = True
    frame.settings.title_bar_path_mode = "full_path"
    frame.settings.dirty_title_style = "asterisk"

    frame._refresh_title()

    assert frame.frame.title == f"{frame.document.path} * - Quill"


def test_statusbar_hides_file_path_when_title_uses_full_path() -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.settings.title_bar_path_mode = "full_path"

    items = frame._statusbar_items()

    assert "file_path" not in items


def test_statusbar_hides_modified_message_when_title_shows_dirty_state() -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.document.modified = True
    frame.settings.dirty_title_style = "text"
    frame._status_message = "Modified"

    message = frame._statusbar_text_for_item("message")

    assert message == "Ready"


def test_refresh_title_uses_asterisk_text_dirty_style() -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.document.modified = True
    frame.settings.title_bar_path_mode = "name"
    frame.settings.dirty_title_style = "asterisk_text"

    frame._refresh_title()

    assert frame.frame.title == "note.md * [modified] - Quill"


def test_feature_coverage_maps_new_surfaces_to_known_features() -> None:
    assert set(MainFrame._STATUS_BAR_FEATURES.values()) <= set(FEATURE_DEFINITIONS)

    command_ids = [
        "tools.profiles_and_features_settings",
        "help.switch_feature_profile",
        "help.undo_last_profile_change",
        "help.reset_feature_profile",
        "help.run_profile_onboarding",
        "help.why_dont_i_see_feature",
        "help.feature_profile_health_check",
        "tools.regex_helper",
        "tools.status_bar_settings",
        "tools.open_welcome_guide",
        "tools.open_keyboard_reference",
        "tools.read_aloud_start_pause",
        "tools.read_aloud_stop",
        "tools.announcement_backend",
        "tools.announcement_trace_toggle",
    ]
    assert all(feature_for_command(command_id) in FEATURE_DEFINITIONS for command_id in command_ids)


def test_increase_heading_level_for_markdown_line() -> None:
    frame = _build_frame("# Heading", insertion_point=2)
    frame.increase_heading_level()
    assert frame.editor.GetValue() == "## Heading"


def test_next_document_switches_active_tab() -> None:
    frame = _build_frame("one", insertion_point=0)
    second_editor = _Editor("two", insertion_point=0)
    second_doc = Document(path=Path("two.md"))
    frame._document_tabs.append(
        type("Tab", (), {"editor": second_editor, "document": second_doc})()
    )
    frame.notebook.AddPage(object(), "two.md", select=False)
    frame.notebook.selection = 0
    frame.next_document()
    assert frame.document.path == Path("two.md")
    assert frame.editor.GetValue() == "two"


def test_close_current_document_removes_tab() -> None:
    frame = _build_frame("one", insertion_point=0)
    second_editor = _Editor("two", insertion_point=0)
    second_doc = Document(path=Path("two.md"))
    frame._document_tabs.append(
        type("Tab", (), {"editor": second_editor, "document": second_doc})()
    )
    frame.notebook.AddPage(object(), "two.md", select=False)
    frame.notebook.selection = 1
    frame._prompt_to_save_active_document = lambda _label: True  # type: ignore[assignment]
    frame.close_current_document()
    assert len(frame._document_tabs) == 1
    assert frame.document.path == Path("note.md")


def test_prompt_to_save_active_document_saves_when_requested() -> None:
    frame = _build_frame("one", insertion_point=0)
    frame.document.modified = True
    frame._wx = type("WX", (), {"ID_YES": 1, "ID_CANCEL": 0})()
    actions: list[str] = []

    frame._prompt_unsaved_changes_action = lambda *_args: 1  # type: ignore[method-assign]

    def _save_file() -> None:
        actions.append("saved")
        frame.document.modified = False

    frame.save_file = _save_file  # type: ignore[method-assign]

    assert frame._prompt_to_save_active_document("closing") is True
    assert actions == ["saved"]


def test_prompt_to_save_active_document_cancels_when_requested() -> None:
    frame = _build_frame("one", insertion_point=0)
    frame.document.modified = True
    frame._wx = type("WX", (), {"ID_YES": 1, "ID_CANCEL": 0})()
    frame._prompt_unsaved_changes_action = lambda *_args: 0  # type: ignore[method-assign]

    assert frame._prompt_to_save_active_document("closing") is False


def test_prompt_to_save_active_document_discards_when_requested() -> None:
    frame = _build_frame("one", insertion_point=0)
    frame.document.modified = True
    frame._wx = type("WX", (), {"ID_YES": 1, "ID_CANCEL": 0, "ID_NO": 2})()
    frame._prompt_unsaved_changes_action = lambda *_args: 2  # type: ignore[method-assign]

    assert frame._prompt_to_save_active_document("closing") is True


def test_confirm_discard_changes_accepts_reload_only() -> None:
    frame = _build_frame("one", insertion_point=0)
    frame._wx = type("WX", (), {"ID_YES": 1, "ID_CANCEL": 0})()
    frame._prompt_unsaved_changes_action = lambda *_args: 1  # type: ignore[method-assign]

    assert frame._confirm_discard_changes() is True


def test_show_startup_wizard_page_uses_rendered_html_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = MainFrame.__new__(MainFrame)
    frame.frame = _Frame()
    frame.settings = type("Settings", (), {"bw_provider_id": "", "bw_speech_model_id": ""})()
    statuses: list[str] = []
    frame._set_status = statuses.append  # type: ignore[method-assign]

    captured: dict[str, object] = {}

    class _PreviewDialog:
        def __init__(self, parent: object, title: str, body_html: str) -> None:
            captured["parent"] = parent
            captured["title"] = title
            captured["body_html"] = body_html

        def show(self) -> None:
            captured["shown"] = True

    preview_module = types.ModuleType("quill.ui.preview_dialog")
    preview_module.MarkdownPreviewDialog = _PreviewDialog
    monkeypatch.setitem(sys.modules, "quill.ui.preview_dialog", preview_module)

    frame.show_startup_wizard_page()

    assert captured["parent"] is frame.frame
    assert captured["title"] == "Startup Wizard"
    assert "<!doctype html>" not in str(captured["body_html"])
    assert "<h1 id='startup-wizard'>Startup Wizard</h1>" in str(captured["body_html"])
    assert captured["shown"] is True
    assert statuses == ["Opened Startup Wizard overview"]


def test_compare_group_builder_classifies_case_only_changes() -> None:
    frame = _build_frame("Alpha")
    groups = frame._build_compare_groups([("left.txt", "Alpha\n"), ("right.txt", "alpha\n")])
    assert len(groups) == 1
    assert groups[0].kind == "case-only"


def test_compare_group_builder_ignores_trailing_space_when_enabled() -> None:
    frame = _build_frame("Alpha")
    frame._compare_ignore_trailing_spaces = True
    groups = frame._build_compare_groups([("left.txt", "Alpha\n"), ("right.txt", "Alpha   \n")])
    assert groups == []


class _KeyEvent:
    def __init__(self, key_code: int) -> None:
        self._key_code = key_code
        self.skipped = False
        self._control = False
        self._shift = False
        self._alt = False

    def GetKeyCode(self) -> int:
        return self._key_code

    def ControlDown(self) -> bool:
        return self._control

    def ShiftDown(self) -> bool:
        return self._shift

    def AltDown(self) -> bool:
        return self._alt

    def Skip(self) -> None:
        self.skipped = True


def test_insert_key_toggles_overwrite_mode_status() -> None:
    frame = _build_frame("hello", insertion_point=5)
    event = _KeyEvent(45)
    frame._wx = type("WX", (), {"WXK_INSERT": 45})()
    frame._on_editor_key_down(event)
    assert frame.statusbar.status[2] == "OVR"


def test_ctrl_shift_o_opens_outline_navigator_from_editor() -> None:
    frame = _build_frame("# Title", insertion_point=0)
    called = {"outline": False}

    def fake_open_outline_navigator() -> None:
        called["outline"] = True

    frame.open_outline_navigator = fake_open_outline_navigator  # type: ignore[method-assign]
    event = _KeyEvent(ord("O"))
    event._control = True
    event._shift = True
    frame._wx = type("WX", (), {"WXK_INSERT": 45, "WXK_F8": 119})()

    frame._on_editor_key_down(event)

    assert called["outline"] is True


def test_enter_continues_markdown_list_item() -> None:
    frame = _build_frame("- item", insertion_point=6)
    frame._wx = type(
        "WX",
        (),
        {
            "WXK_INSERT": 45,
            "WXK_F8": 119,
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 370,
            "WXK_TAB": 9,
        },
    )()
    event = _KeyEvent(13)

    frame._on_editor_key_down(event)

    assert frame.editor.GetValue() == "- item\n- "
    assert frame._status_message == "Continued list item"


def test_enter_on_empty_list_item_exits_list() -> None:
    frame = _build_frame("- ", insertion_point=2)
    frame._wx = type(
        "WX",
        (),
        {
            "WXK_INSERT": 45,
            "WXK_F8": 119,
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 370,
            "WXK_TAB": 9,
        },
    )()
    event = _KeyEvent(13)

    frame._on_editor_key_down(event)

    assert frame.editor.GetValue() == ""
    assert frame._status_message == "Exited list"


def test_tab_and_shift_tab_adjust_list_nesting() -> None:
    frame = _build_frame("- one\n- two", insertion_point=8)
    frame._wx = type(
        "WX",
        (),
        {
            "WXK_INSERT": 45,
            "WXK_F8": 119,
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 370,
            "WXK_TAB": 9,
        },
    )()
    event = _KeyEvent(9)
    frame._on_editor_key_down(event)
    assert frame.editor.GetValue() == "- one\n    - two"
    assert frame._status_message == "Nested list item"

    shift_event = _KeyEvent(9)
    shift_event._shift = True
    frame._on_editor_key_down(shift_event)
    assert frame.editor.GetValue() == "- one\n- two"
    assert frame._status_message == "Promoted list item"


def test_extract_list_manager_state_tracks_nested_items() -> None:
    frame = _build_frame("- Parent\n    - [x] Child\n1. Ordered", insertion_point=14)

    state = frame._extract_list_manager_state()

    assert state is not None
    assert [item.kind for item in state.items] == ["bullet", "task", "ordered"]
    assert [item.level for item in state.items] == [0, 1, 0]


def test_open_outline_navigator_routes_epub_to_epub_navigator() -> None:
    frame = _build_frame("# EPUB: Book", insertion_point=0)
    frame.document.path = Path("book.epub")
    called = {"epub": False}

    def fake_open_epub_navigator() -> None:
        called["epub"] = True

    frame.open_epub_navigator = fake_open_epub_navigator  # type: ignore[method-assign]

    frame.open_outline_navigator()

    assert called["epub"] is True


def test_open_outline_navigator_reports_plain_text_as_unsupported() -> None:
    frame = _build_frame("Plain text", insertion_point=0)
    frame.document.path = Path("notes.txt")
    frame._build_outline_navigator_nodes = lambda: (_ for _ in ()).throw(  # type: ignore[method-assign]
        AssertionError("outline nodes should not be built for plain text")
    )

    frame.open_outline_navigator()

    assert frame._status_message == "Outline is not available for plain text files"


def test_open_preferences_shows_dialog_and_routes_selection() -> None:
    frame = _build_frame("hello", insertion_point=0)
    called: list[str] = []

    class _ChoiceDialog:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.selection = 0

        def __enter__(self) -> _ChoiceDialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def SetSelection(self, selection: int) -> None:
            self.selection = selection

        def GetSelection(self) -> int:
            return self.selection

    def _show_modal(dialog: object, _label: str) -> int:
        dialog.selection = 3  # type: ignore[attr-defined]
        return 1

    frame._wx = type("WX", (), {"SingleChoiceDialog": _ChoiceDialog, "ID_OK": 1})()
    frame._show_modal_dialog = _show_modal  # type: ignore[method-assign]
    frame.open_general_preferences = lambda: called.append("general")  # type: ignore[method-assign]
    frame.open_profiles_and_features_settings = lambda: called.append("profiles")  # type: ignore[method-assign]
    frame.open_status_bar_settings = lambda: called.append("status")  # type: ignore[method-assign]
    frame.open_keymap_editor = lambda: called.append("keymap")  # type: ignore[method-assign]

    frame.open_preferences()

    assert called == ["keymap"]


def test_open_preferences_sets_cancelled_status_when_dialog_is_cancelled() -> None:
    frame = _build_frame("hello", insertion_point=0)

    class _ChoiceDialog:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.selection = 0

        def __enter__(self) -> _ChoiceDialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def SetSelection(self, selection: int) -> None:
            self.selection = selection

        def GetSelection(self) -> int:
            return self.selection

    frame._wx = type("WX", (), {"SingleChoiceDialog": _ChoiceDialog, "ID_OK": 1})()
    frame._show_modal_dialog = lambda _dialog, _label: 0  # type: ignore[method-assign]

    frame.open_preferences()

    assert frame._status_message == "Preferences cancelled"


def test_open_preferences_routes_to_general_settings() -> None:
    frame = _build_frame("hello", insertion_point=0)
    called: list[str] = []

    class _ChoiceDialog:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.selection = 0

        def __enter__(self) -> _ChoiceDialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def SetSelection(self, selection: int) -> None:
            self.selection = selection

        def GetSelection(self) -> int:
            return self.selection

    frame._wx = type("WX", (), {"SingleChoiceDialog": _ChoiceDialog, "ID_OK": 1})()
    frame._show_modal_dialog = lambda _dialog, _label: 1  # type: ignore[method-assign]
    frame.open_general_preferences = lambda: called.append("general")  # type: ignore[method-assign]
    frame.open_profiles_and_features_settings = lambda: called.append("profiles")  # type: ignore[method-assign]
    frame.open_status_bar_settings = lambda: called.append("status")  # type: ignore[method-assign]
    frame.open_keymap_editor = lambda: called.append("keymap")  # type: ignore[method-assign]

    frame.open_preferences()

    assert called == ["general"]


def test_build_outline_navigator_nodes_tracks_heading_hierarchy() -> None:
    frame = _build_frame("# Title\nBody\n## Child\nText\n# Next\n", insertion_point=0)

    nodes = frame._build_outline_navigator_nodes()

    assert [node.label for node in nodes] == ["Title", "Next"]
    assert [node.label for node in nodes[0].children] == ["Child"]
    assert "## Child" in nodes[0].children[0].preview
    assert nodes[0].children[0].action_label == "Jump to Heading"


def test_build_epub_navigator_nodes_uses_chapter_titles_and_preview() -> None:
    frame = _build_frame("# EPUB", insertion_point=0)
    book = EpubBook(
        title="Sample Book",
        chapters=(
            EpubChapter(
                title="One",
                href="one.xhtml",
                text="Heading First chapter",
                headings=(EpubHeading(level=1, title="Heading"),),
            ),
            EpubChapter(title="Two", href="two.xhtml", text="Second chapter"),
        ),
    )

    nodes = frame._build_epub_navigator_nodes(book)

    assert [node.label for node in nodes] == ["One", "Two"]
    assert nodes[0].action_label == "Open Chapter"
    assert nodes[0].children[0].label == "Heading"
    assert nodes[0].children[0].action_label == "Jump to Heading"
    assert "First chapter" in nodes[0].preview


def test_refresh_contextual_menu_disables_insert_table_for_plain_documents() -> None:
    frame = _build_frame("Heading-like text\n- item\n", insertion_point=0)
    frame.document.path = Path("note.txt")

    class _TrackedMenuItem:
        def __init__(self) -> None:
            self.enabled: bool | None = None

        def Enable(self, enabled: bool) -> None:
            self.enabled = enabled

    class _MenuBar:
        def __init__(self, table_item: _TrackedMenuItem) -> None:
            self._table_item = table_item

        def FindItemById(self, item_id: int) -> object | None:
            if item_id == frame._id_insert_table:
                return self._table_item
            return None

    table_item = _TrackedMenuItem()
    frame.frame.GetMenuBar = lambda: _MenuBar(table_item)  # type: ignore[attr-defined]
    frame._id_insert_markdown_tag = 1001
    frame._id_heading_1 = 1002
    frame._id_heading_2 = 1003
    frame._id_heading_3 = 1004
    frame._id_heading_4 = 1005
    frame._id_heading_5 = 1006
    frame._id_heading_6 = 1007
    frame._id_insert_bullet_list = 1008
    frame._id_insert_numbered_list = 1009
    frame._id_insert_task_list = 1010
    frame._id_insert_code_block = 1011
    frame._id_insert_footnote = 1012
    frame._id_insert_table = 1013
    frame._id_insert_html_tag = 1014

    frame._refresh_contextual_menu_items()

    assert table_item.enabled is False


def test_find_heading_position_returns_matching_heading_offset() -> None:
    frame = _build_frame("# EPUB", insertion_point=0)
    chapter_text = "# Chapter\n\nIntro text Heading body\n"

    position = frame._find_heading_position(chapter_text, "Heading", 0)

    assert position == chapter_text.index("Heading")


def test_build_misspelling_navigator_nodes_uses_line_and_column() -> None:
    frame = _build_frame("hello\nwrng word\n", insertion_point=0)
    nodes = frame._build_misspelling_navigator_nodes([Misspelling(word="wrng", start=6, end=10)])

    assert nodes[0].label == "wrng (Ln 2, Col 1)"
    assert nodes[0].action_label == "Jump to Occurrence"
    assert "wrng word" in nodes[0].preview


def test_open_misspelling_list_jumps_to_selected_occurrence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _build_frame("hello\nwrng word\n", insertion_point=0)
    item = Misspelling(word="wrng", start=6, end=10)
    frame._spell_dictionary = lambda: {"hello", "word"}  # type: ignore[method-assign]
    frame._show_tree_navigator = lambda **_kwargs: item  # type: ignore[method-assign]
    monkeypatch.setattr(
        "quill.ui.main_frame.list_misspellings",
        lambda _text, _dictionary: [item],
    )

    frame.open_misspelling_list()

    assert frame.editor.GetInsertionPoint() == 6
    assert frame.editor.selection == (6, 10)


def test_list_bookmarks_jumps_to_selected_bookmark() -> None:
    frame = _build_frame("alpha\nbeta\n", insertion_point=0)
    frame._bookmarks = {"Middle": 6}
    frame._show_tree_navigator = lambda **_kwargs: "Middle"  # type: ignore[method-assign]

    frame.list_bookmarks()

    assert frame.editor.GetInsertionPoint() == 6
    assert frame._status_message == 'Jumped to bookmark "Middle"'


def test_previous_misspelling_jumps_to_prior_item() -> None:
    frame = _build_frame(
        "wrng\nhello\nlaterbad\n",
        insertion_point=len("wrng\nhello\nlaterbad"),
    )
    frame._spell_dictionary = lambda: {"hello"}  # type: ignore[method-assign]

    frame.previous_misspelling()

    assert frame.editor.GetInsertionPoint() == 11
    assert frame.editor.selection == (11, 19)
    assert frame._status_message == 'Previous misspelling: "laterbad"'


def test_misspelling_context_text_prefers_sentence() -> None:
    frame = _build_frame("This has wrng spelling. Another sentence here.", insertion_point=0)
    item = Misspelling(word="wrng", start=9, end=13)

    context = frame._misspelling_context_text(frame.editor.GetValue(), item)

    assert context == "This has wrng spelling."


def test_spell_word_for_speech_separates_letters_and_symbols() -> None:
    frame = _build_frame("placeholder", insertion_point=0)

    spoken = frame._spell_word_for_speech("can't-do_it")

    assert spoken == "C, A, N, apostrophe, T, dash, D, O, underscore, I, T"


def test_spellcheck_speech_message_includes_single_suggestion_spelling() -> None:
    frame = _build_frame("placeholder", insertion_point=0)

    message = frame._spellcheck_speech_message("wrng", "wrong")

    assert 'Misspelled word: "wrng".' in message
    assert "Spelling: W, R, N, G." in message
    assert 'Only suggestion: "wrong".' in message
    assert "Suggestion spelling: W, R, O, N, G." in message


def test_find_next_does_not_wrap_when_setting_disabled() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=len("alpha beta alpha"))
    frame._last_find_query = "alpha"
    frame._last_search_options = SearchOptions()
    frame.settings.wrap_find = False

    frame.find_next()

    assert frame._status_message == "No matches found from the current position"


def test_find_next_wraps_when_setting_enabled() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=len("alpha beta alpha"))
    frame._last_find_query = "alpha"
    frame._last_search_options = SearchOptions()
    frame.settings.wrap_find = True

    frame.find_next()

    assert frame.editor.selection == (0, 5)
    assert frame._status_message.endswith("(wrapped)")


def test_sort_lines_descending_uses_undo_preserving_replace_path() -> None:
    frame = _build_frame("a\nc\nb\n", insertion_point=0)
    frame.editor.SetSelection(0, len(frame.editor.GetValue()))
    frame.sort_lines_descending()

    assert frame.editor.GetValue() == "c\nb\na\n"


def test_replace_all_uses_undo_preserving_replace_path(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=0)
    frame._wx = type("WX", (), {"ICON_QUESTION": 0, "YES_NO": 0, "NO_DEFAULT": 0, "YES": 1})()
    frame._prompt_search = lambda _title, replacement=False: (  # type: ignore[method-assign]
        "alpha",
        "omega",
        SearchOptions(),
    )
    frame._show_message_box = lambda *_args, **_kwargs: 1  # type: ignore[method-assign]

    frame.replace_all_text()

    assert frame.editor.GetValue() == "omega beta omega"


def test_replace_text_replaces_next_match() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=0)
    frame._wx = type("WX", (), {"ICON_ERROR": 0, "OK": 0})()
    frame._prompt_search = lambda _title, replacement=False: (  # type: ignore[method-assign]
        "alpha",
        "omega",
        SearchOptions(),
    )

    frame.replace_text()

    assert frame.editor.GetValue() == "omega beta alpha"
    assert frame._status_message == "Replaced at position 1"


def test_replace_text_wraps_when_enabled() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=len("alpha beta alpha"))
    frame._wx = type("WX", (), {"ICON_ERROR": 0, "OK": 0})()
    frame.settings.wrap_find = True
    frame._prompt_search = lambda _title, replacement=False: (  # type: ignore[method-assign]
        "alpha",
        "omega",
        SearchOptions(),
    )

    frame.replace_text()

    assert frame.editor.GetValue() == "omega beta alpha"
    assert frame._status_message.endswith("(wrapped)")


def test_tab_key_indents_using_configured_mode() -> None:
    frame = _build_frame("alpha", insertion_point=0)
    frame.settings.indent_with_tabs = True
    frame.settings.indent_size = 2
    frame._wx = type("WX", (), {"WXK_INSERT": 45, "WXK_F8": 119, "WXK_TAB": 9})()
    event = _KeyEvent(9)

    frame._on_editor_key_down(event)

    assert frame.editor.GetValue() == "\talpha"


def test_shift_tab_outdents_using_configured_mode() -> None:
    frame = _build_frame("\talpha", insertion_point=1)
    frame.settings.indent_with_tabs = True
    frame.settings.indent_size = 2
    frame._wx = type("WX", (), {"WXK_INSERT": 45, "WXK_F8": 119, "WXK_TAB": 9})()
    event = _KeyEvent(9)
    event._shift = True

    frame._on_editor_key_down(event)

    assert frame.editor.GetValue() == "alpha"


def test_notebook_enter_focuses_active_document() -> None:
    frame = _build_frame("alpha", insertion_point=0)
    frame._activate_tab = lambda _index: None  # type: ignore[method-assign]
    frame._wx = type(
        "WX",
        (),
        {
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 13,
            "WXK_SPACE": 32,
            "WXK_TAB": 9,
            "NOT_FOUND": -1,
        },
    )()
    event = _KeyEvent(13)

    frame._on_notebook_key_down(event)

    assert frame.editor.focused is True
    assert frame._status_message.startswith("Focused document ")


def test_profile_choice_label_includes_description() -> None:
    frame = _build_frame("alpha", insertion_point=0)
    profile = PROFILE_DEFINITIONS["essential"]
    label = frame._profile_choice_label(profile)

    assert label.startswith("Essential — ")
    assert profile.description in label


def test_print_document_cancel_reports_cancelled() -> None:
    frame = _build_frame("alpha", insertion_point=0)
    frame._print_data = object()
    frame._build_text_printout = lambda *_args: type(  # type: ignore[method-assign]
        "_Printout",
        (),
        {"Destroy": lambda self: None},
    )()
    frame._show_message_box = lambda *_args, **_kwargs: None  # type: ignore[method-assign]

    class _Printer:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return

        def Print(self, *_args: object, **_kwargs: object) -> bool:
            return False

        def GetLastError(self) -> int:
            return 2

    frame._wx = type(
        "WX",
        (),
        {
            "PrintDialogData": staticmethod(lambda data: data),
            "Printer": _Printer,
            "PRINTER_NO_ERROR": 0,
            "PRINTER_CANCELLED": 2,
            "ICON_ERROR": 0,
            "OK": 0,
        },
    )()

    frame.print_document()

    assert frame._status_message == "Printing cancelled"


def test_spellcheck_hint_bell_debounces_same_word(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _build_frame("alpha wrng", insertion_point=6)
    bells: list[str] = []
    frame._wx = type("WX", (), {"Bell": staticmethod(lambda: bells.append("bell"))})()
    frame._last_live_misspelling_feedback = None
    frame._last_live_misspelling_feedback_at = 0.0
    frame._spell_dictionary = lambda: {"alpha"}  # type: ignore[method-assign]
    monkeypatch.setattr(
        main_frame_module,
        "find_next_misspelling",
        lambda *_args, **_kwargs: Misspelling("wrng", 6, 10),
    )
    ticks = iter([10.0, 10.1, 11.2])
    monkeypatch.setattr(main_frame_module.time, "monotonic", lambda: next(ticks))

    frame._announce_spellcheck_hint()
    frame._announce_spellcheck_hint()
    frame._announce_spellcheck_hint()

    assert bells == ["bell", "bell"]


def test_extend_selection_mode_moves_down_with_arrow_key() -> None:
    frame = _build_frame("one\ntwo", insertion_point=0)
    frame.toggle_extend_selection_mode(True)
    event = _KeyEvent(317)
    frame._wx = type(
        "WX",
        (),
        {
            "WXK_INSERT": 45,
            "WXK_F8": 119,
            "WXK_LEFT": 314,
            "WXK_RIGHT": 316,
            "WXK_UP": 315,
            "WXK_DOWN": 317,
            "WXK_HOME": 313,
            "WXK_END": 312,
            "WXK_PAGEUP": 366,
            "WXK_PAGEDOWN": 367,
            "WXK_ESCAPE": 27,
        },
    )()

    frame._on_editor_key_down(event)

    assert frame.editor.GetInsertionPoint() == 4
    assert frame.editor.selection == (0, 4)


def test_find_next_extends_selection_when_mode_enabled() -> None:
    frame = _build_frame("alpha beta gamma alpha", insertion_point=0)
    frame.toggle_extend_selection_mode(True)
    frame.editor.SetInsertionPoint(1)
    frame._last_find_query = "alpha"
    frame._last_search_options = SearchOptions()

    frame.find_next()

    assert frame.editor.GetInsertionPoint() == 22
    assert frame.editor.selection == (0, 22)


def test_find_text_sets_anchor_and_extends_when_mode_is_on() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=6)
    frame._wx = type("WX", (), {"ICON_ERROR": 0, "OK": 0, "ICON_INFORMATION": 0})()
    frame.toggle_extend_selection_mode(True)
    frame._extend_selection_anchor = None
    frame._prompt_search = lambda _title, replacement=False: (  # type: ignore[method-assign]
        "alpha",
        None,
        SearchOptions(),
    )

    frame.find_text()

    assert frame._extend_selection_anchor == 6
    assert frame.editor.selection == (6, 16)
    assert frame._status_message == "Found at position 12"


def test_prompt_search_defers_focus_and_wires_escape() -> None:
    frame = _build_frame("alpha beta", insertion_point=0)
    frame._last_find_query = "alpha"
    deferred: list[object] = []
    captured: dict[str, object] = {}

    class _Button:
        def SetDefault(self) -> None:
            return None

    class _ButtonSizer:
        def FindWindowById(self, _window_id: int) -> _Button:
            return _Button()

    class _TextCtrl:
        def __init__(self, _parent: object, value: str = "", style: int = 0) -> None:
            self.value = value
            self.style = style
            self.focused = False
            self.selection: tuple[int, int] | None = None
            self.handlers: dict[int, object] = {}
            captured["query"] = self

        def Bind(self, event: int, handler: object) -> None:
            self.handlers[event] = handler

        def GetValue(self) -> str:
            return self.value

        def SetFocus(self) -> None:
            self.focused = True

        def SetSelection(self, start: int, end: int) -> None:
            self.selection = (start, end)

    class _Dialog:
        def __init__(self, _parent: object, title: str, size: tuple[int, int]) -> None:
            self.title = title
            self.size = size
            self.affirmative_id: int | None = None
            self.escape_id: int | None = None
            self.handlers: dict[int, object] = {}
            self.destroyed = False
            captured["dialog"] = self

        def CreateButtonSizer(self, _style: int) -> _ButtonSizer:
            return _ButtonSizer()

        def SetAffirmativeId(self, value: int) -> None:
            self.affirmative_id = value

        def SetEscapeId(self, value: int) -> None:
            self.escape_id = value

        def SetSizerAndFit(self, _sizer: object) -> None:
            return None

        def Bind(self, event: int, handler: object) -> None:
            self.handlers[event] = handler

        def EndModal(self, _result: int) -> None:
            return None

        def Destroy(self) -> None:
            self.destroyed = True

    class _Panel:
        def __init__(self, _parent: object) -> None:
            return None

        def SetSizer(self, _sizer: object) -> None:
            return None

    class _BoxSizer:
        def __init__(self, _orientation: int) -> None:
            return None

        def Add(self, _item: object, *_args: object, **_kwargs: object) -> None:
            return None

    class _StaticText:
        def __init__(self, _parent: object, label: str) -> None:
            self.label = label

    class _Choice:
        def __init__(self, _parent: object, choices: list[str]) -> None:
            self.choices = choices
            self.selection = 0

        def SetSelection(self, selection: int) -> None:
            self.selection = selection

        def GetStringSelection(self) -> str:
            return self.choices[self.selection]

    class _CheckBox:
        def __init__(self, _parent: object, label: str) -> None:
            self.label = label
            self.value = False

        def GetValue(self) -> bool:
            return self.value

    wx = type(
        "WX",
        (),
        {
            "Dialog": _Dialog,
            "Panel": _Panel,
            "BoxSizer": _BoxSizer,
            "StaticText": _StaticText,
            "TextCtrl": _TextCtrl,
            "Choice": _Choice,
            "CheckBox": _CheckBox,
            "TE_PROCESS_ENTER": 0,
            "VERTICAL": 1,
            "EXPAND": 2,
            "ALL": 4,
            "LEFT": 8,
            "RIGHT": 16,
            "TOP": 32,
            "OK": 1,
            "CANCEL": 2,
            "ID_OK": 1,
            "ID_CANCEL": 0,
            "EVT_CHAR_HOOK": 100,
            "EVT_TEXT_ENTER": 101,
            "WXK_ESCAPE": 27,
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 312,
            "CallAfter": staticmethod(lambda callback: deferred.append(callback)),
        },
    )()
    frame._wx = wx

    def _show_modal(dialog: object, _label: str) -> int:
        assert dialog.affirmative_id == wx.ID_OK  # type: ignore[attr-defined]
        assert dialog.escape_id == wx.ID_CANCEL  # type: ignore[attr-defined]
        query = captured["query"]
        assert query.focused is False  # type: ignore[attr-defined]
        assert deferred
        for callback in deferred:
            callback()
        assert query.focused is True  # type: ignore[attr-defined]
        assert query.selection == (0, len("alpha"))  # type: ignore[attr-defined]
        assert wx.EVT_CHAR_HOOK in dialog.handlers  # type: ignore[attr-defined]
        return wx.ID_CANCEL

    frame._show_modal_dialog = _show_modal  # type: ignore[method-assign]

    result = frame._prompt_search("Find")

    assert result is None
    assert deferred


def test_find_previous_sets_anchor_and_extends_when_mode_is_on() -> None:
    frame = _build_frame("alpha beta alpha", insertion_point=len("alpha beta alpha"))
    frame._last_find_query = "alpha"
    frame._last_search_options = SearchOptions()
    frame.toggle_extend_selection_mode(True)
    frame._extend_selection_anchor = None

    frame.find_previous()

    assert frame._extend_selection_anchor == len("alpha beta alpha")
    assert frame.editor.selection == (11, len("alpha beta alpha"))
    assert frame._status_message == "Found previous at position 12"


def test_format_case_no_selection_targets_current_word() -> None:
    frame = _build_frame("hello world", insertion_point=1)

    frame.format_upper_case()

    assert frame.editor.GetValue() == "HELLO world"
    assert frame._status_message == "Upper case applied to current word"


def test_format_case_no_selection_on_whitespace_noops() -> None:
    frame = _build_frame("hello  world", insertion_point=6)

    frame.format_upper_case()

    assert frame.editor.GetValue() == "hello  world"
    assert frame._status_message == "No current word to transform"


def test_save_all_files_calls_save_file() -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.document.modified = True
    called = {"save": False}

    def fake_save_file() -> None:
        called["save"] = True

    frame.save_file = fake_save_file  # type: ignore[method-assign]
    frame.save_all_files()
    assert called["save"] is True


def test_restore_backup_loads_selected_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frame = _build_frame("hello", insertion_point=0)
    frame.document.path = tmp_path / "note.md"
    backup = tmp_path / "backup.bak"
    backup.write_text("restored text", encoding="utf-8")

    class _Dialog:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.selected = 0

        def __enter__(self) -> _Dialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def ShowModal(self) -> int:
            return 1

        def GetSelection(self) -> int:
            return self.selected

    monkeypatch.setattr("quill.ui.main_frame.list_backups", lambda _path: [backup])
    frame._wx = type("WX", (), {"ID_OK": 1, "SingleChoiceDialog": _Dialog})()
    frame.restore_backup()
    assert frame.editor.GetValue() == "restored text"


def test_prompt_untrusted_location_uses_single_checkbox_dialog() -> None:
    frame = _build_frame("hello")

    class _CheckBox:
        def __init__(self, _parent: object, label: str) -> None:
            self.label = label
            self.value = True

        def GetValue(self) -> bool:
            return self.value

    class _Panel:
        def __init__(self, _parent: object) -> None:
            return None

        def SetSizer(self, _sizer: object) -> None:
            return None

    class _BoxSizer:
        def __init__(self, _orientation: int) -> None:
            return None

        def Add(self, _item: object, *_args: object, **_kwargs: object) -> None:
            return None

    class _StaticText:
        def __init__(self, _parent: object, label: str) -> None:
            self.label = label

    class _Dialog:
        def __init__(self, _parent: object, title: str) -> None:
            self.title = title
            self.affirmative_id: int | None = None
            self.escape_id: int | None = None
            self.show_count = 0

        def CreateButtonSizer(self, _style: int) -> object:
            return object()

        def SetAffirmativeId(self, value: int) -> None:
            self.affirmative_id = value

        def SetEscapeId(self, value: int) -> None:
            self.escape_id = value

        def ShowModal(self) -> int:
            self.show_count += 1
            return 1

    wx = type(
        "WX",
        (),
        {
            "Dialog": _Dialog,
            "Panel": _Panel,
            "BoxSizer": _BoxSizer,
            "StaticText": _StaticText,
            "CheckBox": _CheckBox,
            "VERTICAL": 1,
            "ALL": 2,
            "EXPAND": 4,
            "LEFT": 8,
            "RIGHT": 16,
            "BOTTOM": 32,
            "ALIGN_RIGHT": 64,
            "OK": 1,
            "CANCEL": 2,
            "ID_OK": 1,
            "ID_CANCEL": 0,
        },
    )()
    frame._wx = wx

    result = frame._prompt_untrusted_location(Path(r"C:\Users\Jeff\Notes"))

    assert result is True


def test_prompt_unsaved_changes_space_activates_focused_dont_save() -> None:
    frame = _build_frame("hello")
    captured: dict[str, object] = {}

    class _KeyEvent:
        def __init__(self, key_code: int) -> None:
            self._key_code = key_code
            self.skipped = False

        def GetKeyCode(self) -> int:
            return self._key_code

        def Skip(self) -> None:
            self.skipped = True

    class _Dialog:
        def __init__(self, _parent: object, title: str) -> None:
            self.title = title
            self.handlers: dict[int, object] = {}
            self.buttons: list[object] = []
            self.focused: object | None = None
            self.modal_result: int | None = None
            captured["dialog"] = self

        def Bind(self, event: int, handler: object) -> None:
            self.handlers[event] = handler

        def EndModal(self, result: int) -> None:
            self.modal_result = result

        def SetAffirmativeId(self, _value: int) -> None:
            return None

        def SetEscapeId(self, _value: int) -> None:
            return None

        def SetSizerAndFit(self, _sizer: object) -> None:
            return None

        def FindFocus(self) -> object | None:
            return self.focused

        def Destroy(self) -> None:
            return None

    class _Panel:
        def __init__(self, parent: object) -> None:
            self.dialog = parent

        def SetSizer(self, _sizer: object) -> None:
            return None

    class _Button:
        def __init__(self, parent: object, id: int, label: str) -> None:
            self.id = id
            self.label = label
            self.handlers: dict[int, object] = {}
            parent.dialog.buttons.append(self)

        def Bind(self, event: int, handler: object) -> None:
            self.handlers[event] = handler

        def SetDefault(self) -> None:
            return None

    class _StaticText:
        def __init__(self, _parent: object, label: str) -> None:
            self.label = label
            return None

    class _BoxSizer:
        def __init__(self, _orientation: int) -> None:
            return None

        def Add(self, _item: object, *_args: object, **_kwargs: object) -> None:
            return None

        def AddStretchSpacer(self, _prop: int) -> None:
            return None

    wx = type(
        "WX",
        (),
        {
            "Dialog": _Dialog,
            "Panel": _Panel,
            "BoxSizer": _BoxSizer,
            "Button": _Button,
            "StaticText": _StaticText,
            "VERTICAL": 1,
            "HORIZONTAL": 2,
            "ALL": 4,
            "EXPAND": 8,
            "LEFT": 16,
            "RIGHT": 32,
            "BOTTOM": 64,
            "ID_YES": 1,
            "ID_NO": 2,
            "ID_CANCEL": 0,
            "EVT_BUTTON": 100,
            "EVT_CHAR_HOOK": 101,
            "WXK_ESCAPE": 27,
            "WXK_RETURN": 13,
            "WXK_NUMPAD_ENTER": 312,
            "WXK_SPACE": 32,
        },
    )()
    frame._wx = wx

    def _show_modal(dialog: object, _label: str) -> int:
        dont_save = next(
            button for button in dialog.buttons if getattr(button, "id", None) == wx.ID_NO
        )
        dialog.focused = dont_save
        dialog.handlers[wx.EVT_CHAR_HOOK](_KeyEvent(wx.WXK_SPACE))
        return dialog.modal_result

    frame._show_modal_dialog = _show_modal  # type: ignore[method-assign]

    result = frame._prompt_unsaved_changes_action(
        "Unsaved changes",
        "You have unsaved changes. Save before closing?",
        "Save",
        "Don't Save",
    )

    assert result == wx.ID_NO


def test_prompt_table_shape_reprompts_invalid_values() -> None:
    frame = _build_frame("hello")
    messages: list[str] = []

    class _TextEntryDialog:
        values = iter(["abc", "3", "0", "4"])

        def __init__(self, _parent: object, _message: str, _title: str, value: str) -> None:
            self.value = next(self.values, value)

        def __enter__(self) -> _TextEntryDialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def ShowModal(self) -> int:
            return 1

        def GetValue(self) -> str:
            return self.value

    class _MessageDialog:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        def __enter__(self) -> _MessageDialog:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def ShowModal(self) -> int:
            return 1

    wx = type(
        "WX",
        (),
        {
            "TextEntryDialog": _TextEntryDialog,
            "MessageDialog": _MessageDialog,
            "VERTICAL": 1,
            "YES_NO": 2,
            "ICON_QUESTION": 4,
            "ICON_ERROR": 8,
            "OK": 16,
            "ID_OK": 1,
            "ID_YES": 2,
        },
    )()
    frame._wx = wx

    def _show_modal(dialog: object, _label: str) -> int:
        if isinstance(dialog, _MessageDialog):
            return wx.ID_YES
        return wx.ID_OK

    def _show_message_box(message: str, caption: str, _style: int) -> int:
        messages.append(f"{caption}: {message}")
        return wx.OK

    frame._show_modal_dialog = _show_modal  # type: ignore[method-assign]
    frame._show_message_box = _show_message_box  # type: ignore[method-assign]

    result = frame._prompt_table_shape()

    assert result == (4, 3, True)
    assert messages == [
        "Insert Table: Rows and columns must be whole numbers.",
        "Insert Table: Rows must be between 1 and 50.",
    ]
