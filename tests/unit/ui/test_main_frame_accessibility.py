from __future__ import annotations

from dataclasses import dataclass

from quill.core.a11y_regions import RegionTracker
from quill.platform.windows.sr_announce import (
    clear_transcript,
    enable_transcript_capture,
    set_transcript_path,
    transcript_entries,
)
from quill.ui.main_frame import MainFrame


@dataclass
class _DummyDialog:
    result: int

    def ShowModal(self) -> int:
        return self.result


class _DummyWx:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def MessageBox(self, message: str, caption: str, style: int) -> int:
        self.calls.append((message, caption, style))
        return 7


def test_show_modal_dialog_announces_entry_and_exit() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._region_tracker = RegionTracker()
    dialog = _DummyDialog(result=42)
    set_transcript_path(None)
    clear_transcript()
    enable_transcript_capture(True)
    try:
        result = frame._show_modal_dialog(dialog, "Find")
        assert result == 42
        assert transcript_entries() == ["Entered Find dialog", "Exited Find dialog"]
    finally:
        enable_transcript_capture(False)
        clear_transcript()


def test_show_message_box_announces_entry_and_exit() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._region_tracker = RegionTracker()
    frame._wx = _DummyWx()
    set_transcript_path(None)
    clear_transcript()
    enable_transcript_capture(True)
    try:
        result = frame._show_message_box("Body", "Caption", 123)
        assert result == 7
        assert frame._wx.calls == [("Body", "Caption", 123)]
        assert transcript_entries() == ["Entered Caption dialog", "Exited Caption dialog"]
    finally:
        enable_transcript_capture(False)
        clear_transcript()


def test_request_menu_refresh_defers_when_menu_is_open() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._menu_open_depth = 1
    frame._pending_menu_refresh = False

    class _Wx:
        pass

    frame._wx = _Wx()

    called: list[str] = []
    frame._refresh_contextual_menu_items = lambda: called.append("context")
    frame._sync_announcement_backend_menu_state = lambda: called.append("announce")
    frame._apply_watch_folder_menu_state = lambda: called.append("watch")
    frame._apply_ai_menu_enabled = lambda: called.append("ai")
    frame._refresh_recent_menu = lambda: called.append("recent")
    frame._refresh_sessions_menu = lambda: called.append("sessions")

    frame._request_menu_refresh()

    assert frame._pending_menu_refresh is True
    assert called == []


def test_request_menu_refresh_flushes_when_menu_is_closed() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._menu_open_depth = 0
    frame._pending_menu_refresh = False

    class _Wx:
        pass

    frame._wx = _Wx()

    called: list[str] = []
    frame._refresh_contextual_menu_items = lambda: called.append("context")
    frame._sync_announcement_backend_menu_state = lambda: called.append("announce")
    frame._apply_watch_folder_menu_state = lambda: called.append("watch")
    frame._apply_ai_menu_enabled = lambda: called.append("ai")
    frame._refresh_recent_menu = lambda: called.append("recent")
    frame._refresh_sessions_menu = lambda: called.append("sessions")

    frame._request_menu_refresh()

    assert frame._pending_menu_refresh is False
    assert called == ["recent", "sessions", "context", "announce", "watch", "ai"]


def test_refresh_recent_menu_defers_when_menu_is_open() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._menu_open_depth = 1
    frame._pending_menu_refresh = False

    class _Wx:
        pass

    frame._wx = _Wx()
    frame._recent_menu = object()
    frame._request_menu_refresh = MainFrame._request_menu_refresh.__get__(frame, MainFrame)

    frame._refresh_recent_menu()

    assert frame._pending_menu_refresh is True


def test_refresh_sessions_menu_defers_when_menu_is_open() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._menu_open_depth = 1
    frame._pending_menu_refresh = False

    class _Wx:
        pass

    frame._wx = _Wx()
    frame._sessions_menu = object()
    frame._request_menu_refresh = MainFrame._request_menu_refresh.__get__(frame, MainFrame)

    frame._refresh_sessions_menu()

    assert frame._pending_menu_refresh is True


class _StubEditor:
    def __init__(self, text: str, selection: tuple[int, int], cursor: int) -> None:
        self._text = text
        self._selection = selection
        self._cursor = cursor

    def GetValue(self) -> str:
        return self._text

    def GetSelection(self) -> tuple[int, int]:
        return self._selection

    def GetInsertionPoint(self) -> int:
        return self._cursor


def _writing_action_frame(editor: _StubEditor) -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame.editor = editor
    frame._status_messages = []
    frame._set_status = frame._status_messages.append
    frame._writing_prompts = []
    frame.open_writing_assistant = frame._writing_prompts.append
    return frame


def test_writing_action_blocked_when_ai_disabled(monkeypatch) -> None:
    import quill.core.ai.model_manager as model_manager

    monkeypatch.setattr(model_manager, "load_ai_enabled", lambda: False)
    editor = _StubEditor("Hello world.", selection=(0, 5), cursor=0)
    frame = _writing_action_frame(editor)

    frame.open_ai_rewrite_selection()

    assert frame._writing_prompts == []
    assert any("AI is turned off" in msg for msg in frame._status_messages)


def test_writing_action_falls_back_to_paragraph_without_selection(monkeypatch) -> None:
    import quill.core.ai.model_manager as model_manager

    monkeypatch.setattr(model_manager, "load_ai_enabled", lambda: True)
    text = "First paragraph.\n\nSecond paragraph here."
    cursor = text.index("Second")
    editor = _StubEditor(text, selection=(cursor, cursor), cursor=cursor)
    frame = _writing_action_frame(editor)

    frame.open_ai_rewrite_selection()

    assert len(frame._writing_prompts) == 1
    assert "Second paragraph here." in frame._writing_prompts[0]
    assert any("paragraph" in msg for msg in frame._status_messages)


def test_summarize_falls_back_to_whole_document_without_selection(monkeypatch) -> None:
    import quill.core.ai.model_manager as model_manager

    monkeypatch.setattr(model_manager, "load_ai_enabled", lambda: True)
    text = "Alpha.\n\nBeta.\n\nGamma."
    editor = _StubEditor(text, selection=(2, 2), cursor=2)
    frame = _writing_action_frame(editor)

    frame.open_ai_summarize_selection()

    assert len(frame._writing_prompts) == 1
    assert "Gamma." in frame._writing_prompts[0]
    assert any("document" in msg for msg in frame._status_messages)
