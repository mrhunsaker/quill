"""The main window must always close, even if a shutdown step fails (#210)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import quill.ui.main_frame as mf
from quill.ui.main_frame import MainFrame


class _FakeWx:
    @staticmethod
    def GetTopLevelWindows() -> list[Any]:
        return []

    @staticmethod
    def GetApp() -> Any:
        return None

    @staticmethod
    def CallAfter(*_a: object, **_k: object) -> None:
        pass


def _raise() -> None:
    raise RuntimeError("boom")


def _frame_for_close(monkeypatch: pytest.MonkeyPatch) -> MainFrame:
    # Avoid real disk/lock side effects from the guarded shutdown steps.
    monkeypatch.setattr(mf, "save_settings", lambda *_a, **_k: None)
    monkeypatch.setattr(mf, "mark_clean_exit", lambda *_a, **_k: None)

    frame = MainFrame.__new__(MainFrame)
    frame.settings = SimpleNamespace(tray_enabled=False)
    frame._is_exiting = True
    frame._can_close_all_documents = lambda: True  # type: ignore[method-assign]
    frame._watch_queue_monitor = None
    # Several steps deliberately raise to prove they cannot block the close.
    frame._watch_service = SimpleNamespace(stop=_raise)
    frame._unregister_global_hotkeys = _raise  # type: ignore[method-assign]
    frame._remove_tray_icon = lambda: None  # type: ignore[method-assign]
    frame.close_ssh_connections = _raise  # type: ignore[method-assign]
    frame.flush_persistent_undo = _raise  # type: ignore[method-assign]
    frame.session_id = "test-session"
    frame._wx = _FakeWx()
    frame.frame = object()
    return frame


def test_on_close_always_skips_even_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _frame_for_close(monkeypatch)
    skipped: list[bool] = []
    vetoed: list[bool] = []
    event = SimpleNamespace(
        Skip=lambda: skipped.append(True),
        Veto=lambda: vetoed.append(True),
    )

    frame._on_close(event)

    assert skipped == [True], "the window must close (event.Skip) despite failing steps"
    assert vetoed == []


def test_on_close_vetoes_when_documents_cannot_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _frame_for_close(monkeypatch)
    frame._can_close_all_documents = lambda: False  # type: ignore[method-assign]
    skipped: list[bool] = []
    vetoed: list[bool] = []
    event = SimpleNamespace(
        Skip=lambda: skipped.append(True),
        Veto=lambda: vetoed.append(True),
    )

    frame._on_close(event)

    assert vetoed == [True]
    assert skipped == []
