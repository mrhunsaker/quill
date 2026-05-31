from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from quill.stability.diagnostics import dump_all_thread_stacks

try:  # pragma: no cover - optional dependency in non-UI test environments
    import wx  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HeartbeatState:
    last_ui_tick: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def tick(self) -> None:
        with self.lock:
            self.last_ui_tick = time.monotonic()

    def age_seconds(self) -> float:
        with self.lock:
            return time.monotonic() - self.last_ui_tick


class WxHeartbeatTimer:
    def __init__(self, window: object, state: HeartbeatState, interval_ms: int = 1000) -> None:
        if wx is None:
            raise RuntimeError("wxPython is required for WxHeartbeatTimer")
        self.window = window
        self.state = state
        self.timer = wx.Timer(window)
        window.Bind(wx.EVT_TIMER, self._on_timer, self.timer)
        self.timer.Start(interval_ms)

    def _on_timer(self, event: object) -> None:
        self.state.tick()
        skip = getattr(event, "Skip", None)
        if callable(skip):
            skip()

    def stop(self) -> None:
        if hasattr(self.timer, "IsRunning") and self.timer.IsRunning():
            self.timer.Stop()


class WxHeartbeatWatchdog:
    def __init__(
        self,
        state: HeartbeatState,
        dump_callback: Callable[[str], object] = dump_all_thread_stacks,
        warn_after_seconds: float = 5.0,
        dump_after_seconds: float = 15.0,
        poll_seconds: float = 2.0,
    ) -> None:
        self.state = state
        self.dump_callback = dump_callback
        self.warn_after_seconds = warn_after_seconds
        self.dump_after_seconds = dump_after_seconds
        self.poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="quill-wx-heartbeat-watchdog",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        already_dumped = False
        while not self._stop.wait(self.poll_seconds):
            age = self.state.age_seconds()
            if age >= self.warn_after_seconds:
                logger.warning("wx UI heartbeat stale for %.1f seconds", age)
            if age >= self.dump_after_seconds and not already_dumped:
                logger.error("wx UI appears blocked for %.1f seconds", age)
                self.dump_callback(f"wx UI heartbeat stale for {age:.1f} seconds")
                already_dumped = True
            if age < self.warn_after_seconds:
                already_dumped = False
