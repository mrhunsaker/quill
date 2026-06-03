"""Source-contract test for SEC-7 Forget API Key wiring in main_frame."""

from pathlib import Path


def _source() -> str:
    return Path("quill/ui/main_frame.py").read_text(encoding="utf-8")


def test_forget_key_menu_item_is_present() -> None:
    source = _source()
    # An id is allocated and a Forget API Key menu item is appended.
    assert "self._id_ai_forget_key = wx.NewIdRef()" in source
    assert '"&Forget API Key"' in source


def test_forget_key_menu_item_is_bound() -> None:
    source = _source()
    assert "id=self._id_ai_forget_key" in source
    assert "self._forget_assistant_api_key()" in source


def test_forget_key_handler_clears_both_stores() -> None:
    source = _source()
    assert "def _forget_assistant_api_key(self) -> None:" in source
    # The handler confirms, then calls the core clear function.
    assert "from quill.core.assistant_ai import clear_assistant_api_key" in source
    assert "clear_assistant_api_key()" in source
