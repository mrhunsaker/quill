from __future__ import annotations

import time
from types import SimpleNamespace

from quill.ui.main_frame import MainFrame


class _Event:
    def __init__(
        self,
        key_code: int,
        *,
        ctrl: bool = False,
        shift: bool = False,
        alt: bool = False,
    ) -> None:
        self._key_code = key_code
        self._ctrl = ctrl
        self._shift = shift
        self._alt = alt
        self.skipped = False

    def GetKeyCode(self) -> int:
        return self._key_code

    def ControlDown(self) -> bool:
        return self._ctrl

    def ShiftDown(self) -> bool:
        return self._shift

    def AltDown(self) -> bool:
        return self._alt

    def Skip(self) -> None:
        self.skipped = True


_BACKTICK = ord("`")


def _build_frame(*, binding: str = "Ctrl+Shift+Grave", timeout: float = 1.5) -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame._wx = SimpleNamespace(
        WXK_BACKTICK=_BACKTICK,
        WXK_ESCAPE=27,
        ACCEL_CTRL=1,
        ACCEL_SHIFT=2,
        ACCEL_ALT=4,
    )
    frame.settings = SimpleNamespace(
        quill_key_binding=binding,
        quill_key_timeout_seconds=timeout,
    )
    frame._quill_key_mode_active = False
    frame._quill_key_prefix_pending = False
    frame._quill_key_prefix_started_at = 0.0
    frame._quill_key_mode_started_at = 0.0
    frame._quill_key_mode_timeout_seconds = 1.5
    frame._quill_key_mode_sticky = False
    frame._statuses: list[str] = []
    frame._feedback: list[str] = []
    frame._set_status_quiet = frame._statuses.append  # type: ignore[method-assign]
    frame._refresh_statusbar = lambda: None  # type: ignore[method-assign]

    def _feedback(message, *, status_message=None, sound_kind=None):  # type: ignore[no-untyped-def]
        frame._feedback.append(status_message or message)

    frame._quill_feedback = _feedback  # type: ignore[method-assign]
    return frame


def test_default_prefix_press_sets_pending() -> None:
    frame = _build_frame()
    handled = frame._handle_quill_key_mode_event(_Event(_BACKTICK, ctrl=True, shift=True))
    assert handled is True
    assert frame._quill_key_prefix_pending is True


def test_prefix_then_n_enters_browse_mode() -> None:
    frame = _build_frame()
    frame._handle_quill_key_mode_event(_Event(_BACKTICK, ctrl=True, shift=True))
    handled = frame._handle_quill_key_mode_event(_Event(ord("N")))
    assert handled is True
    assert frame._quill_key_mode_active is True
    assert frame._quill_key_mode_sticky is False


def test_double_press_prefix_enters_sticky_locked_mode() -> None:
    frame = _build_frame()
    frame._handle_quill_key_mode_event(_Event(_BACKTICK, ctrl=True, shift=True))
    handled = frame._handle_quill_key_mode_event(_Event(_BACKTICK, ctrl=True, shift=True))
    assert handled is True
    assert frame._quill_key_mode_active is True
    assert frame._quill_key_mode_sticky is True
    assert any("locked" in message.lower() for message in frame._feedback)


def test_sticky_mode_ignores_timeout() -> None:
    frame = _build_frame(timeout=0.001)
    frame._enter_quill_key_mode(sticky=True)
    frame._quill_key_mode_started_at = time.monotonic() - 10
    assert frame._quill_key_mode_timed_out() is False


def test_zero_timeout_disables_browse_expiry() -> None:
    frame = _build_frame(timeout=0)
    frame._enter_quill_key_mode()
    frame._quill_key_mode_started_at = time.monotonic() - 10
    assert frame._quill_key_mode_timed_out() is False


def test_positive_timeout_expires_browse_mode() -> None:
    frame = _build_frame(timeout=0.5)
    frame._enter_quill_key_mode()
    frame._quill_key_mode_started_at = time.monotonic() - 10
    assert frame._quill_key_mode_timed_out() is True


def test_remappable_binding_matches_configured_key() -> None:
    frame = _build_frame(binding="Alt+M")
    handled = frame._handle_quill_key_mode_event(_Event(ord("M"), alt=True))
    assert handled is True
    assert frame._quill_key_prefix_pending is True
    # The old default chord no longer triggers the prefix.
    frame2 = _build_frame(binding="Alt+M")
    handled2 = frame2._handle_quill_key_mode_event(_Event(_BACKTICK, ctrl=True, shift=True))
    assert handled2 is False
    assert frame2._quill_key_prefix_pending is False


def test_status_bar_reports_quill_key_state() -> None:
    frame = _build_frame()
    assert frame._statusbar_text_for_item("quill_key_mode") == "Off"
    frame._quill_key_prefix_pending = True
    assert frame._statusbar_text_for_item("quill_key_mode") == "Prefix"
    frame._quill_key_prefix_pending = False
    frame._quill_key_mode_active = True
    assert frame._statusbar_text_for_item("quill_key_mode") == "Browse"
    frame._quill_key_mode_sticky = True
    assert frame._statusbar_text_for_item("quill_key_mode") == "Locked"


def test_quill_key_timeout_reads_settings() -> None:
    frame = _build_frame(timeout=3.0)
    assert frame._quill_key_timeout() == 3.0
    frame.settings.quill_key_timeout_seconds = -5
    # Out-of-range values clamp to a non-negative timeout.
    assert frame._quill_key_timeout() == 0.0
