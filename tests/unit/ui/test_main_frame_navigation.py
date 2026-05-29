from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.a11y_regions import RegionTracker
from quill.core.document import Document
from quill.core.epub import EpubBook, EpubChapter
from quill.core.features import FEATURE_DEFINITIONS, feature_for_command
from quill.core.locations import LocationRing
from quill.ui.main_frame import MainFrame


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

    def Bind(self, *_args: object, **_kwargs: object) -> None:
        return None

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

    def GetPageCount(self) -> int:
        return len(self.pages)

    def SetPageText(self, index: int, title: str) -> None:
        self.titles[index] = title


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
    assert frame.statusbar.fields_count == 6
    assert frame.statusbar.status[0] == "Ln 1, Col 2"
    assert frame.statusbar.status[1] == "INS"


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


def test_open_outline_navigator_routes_epub_to_epub_navigator() -> None:
    frame = _build_frame("# EPUB: Book", insertion_point=0)
    frame.document.path = Path("book.epub")
    called = {"epub": False}

    def fake_open_epub_navigator() -> None:
        called["epub"] = True

    frame.open_epub_navigator = fake_open_epub_navigator  # type: ignore[method-assign]

    frame.open_outline_navigator()

    assert called["epub"] is True


def test_build_outline_navigator_nodes_tracks_heading_hierarchy() -> None:
    frame = _build_frame("# Title\nBody\n## Child\nText\n# Next\n", insertion_point=0)

    nodes = frame._build_outline_navigator_nodes()

    assert [node.label for node in nodes] == ["Title", "Next"]
    assert [node.label for node in nodes[0].children] == ["Child"]
    assert "## Child" in nodes[0].children[0].preview


def test_build_epub_navigator_nodes_uses_chapter_titles_and_preview() -> None:
    frame = _build_frame("# EPUB", insertion_point=0)
    book = EpubBook(
        title="Sample Book",
        chapters=(
            EpubChapter(title="One", href="one.xhtml", text="First chapter"),
            EpubChapter(title="Two", href="two.xhtml", text="Second chapter"),
        ),
    )

    nodes = frame._build_epub_navigator_nodes(book)

    assert [node.label for node in nodes] == ["One", "Two"]
    assert nodes[0].payload == 0
    assert "First chapter" in nodes[0].preview


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
