"""Source-contract test for the AI session branch browser dialog (AI-20).

The live ``wx.Dialog`` is not runtime-instantiated in tests; the repo validates
dialog wiring through source contracts. This asserts the browser surfaces an
accessible branch list with one-key jump (resume) and a compare view, all built
on the wx-free session-tree engine.
"""

from __future__ import annotations

from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "session_browser.py").read_text(
    encoding="utf-8"
)


def test_consumes_session_engine() -> None:
    assert "from quill.core.ai.sessions import" in SOURCE
    for name in ("branch_rows", "format_comparison", "resume", "save_session"):
        assert name in SOURCE


def test_accessible_branch_list() -> None:
    assert "wx.ListBox" in SOURCE
    assert 'SetName("Session branches")' in SOURCE
    assert "row.is_current" in SOURCE  # pre-selects/announces the active branch


def test_jump_resumes_and_announces() -> None:
    assert "_on_jump" in SOURCE
    assert "resume(self._session, turn_id)" in SOURCE
    assert "save_session(self._session)" in SOURCE
    assert "self._announce(" in SOURCE


def test_compare_view_is_readonly() -> None:
    assert "_on_compare" in SOURCE
    assert "format_comparison(self._session, current, turn_id)" in SOURCE
    assert "wx.TE_MULTILINE | wx.TE_READONLY" in SOURCE


def test_uses_dialog_contract() -> None:
    assert "apply_modal_ids" in SOURCE
    assert "show_modal_dialog" in SOURCE
