from __future__ import annotations

import logging
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from quill.stability import wx_dispatch as wx_dispatch_module
from quill.stability import wx_heartbeat as heartbeat_module
from quill.stability.crash_report import build_diagnostic_bundle
from quill.stability.feature_contracts import FeatureContract, validate_feature_contract
from quill.stability.memory_watch import start_memory_tracing, write_memory_snapshot
from quill.stability.safe_mode import build_safe_mode_config, should_enable_safe_mode
from quill.stability.safe_regex import RegexTimeoutError, safe_finditer
from quill.stability.safe_subprocess import run_subprocess_safely
from quill.stability.task_manager import CancelledError, TaskManager
from quill.stability.ui_responsiveness import wx_event_handler
from quill.stability.wx_dispatch import CoalescedUiReporter, call_ui_safely


def test_call_ui_safely_schedules_through_callafter(monkeypatch) -> None:
    scheduled: list[object] = []
    monkeypatch.setattr(
        wx_dispatch_module,
        "wx",
        SimpleNamespace(CallAfter=lambda callback: scheduled.append(callback)),
    )

    called: list[str] = []

    call_ui_safely(lambda value: called.append(value), "done")

    assert len(scheduled) == 1
    scheduled[0]()
    assert called == ["done"]


def test_coalesced_ui_reporter_uses_latest_value(monkeypatch) -> None:
    scheduled: list[object] = []
    monkeypatch.setattr(
        wx_dispatch_module,
        "call_ui_safely",
        lambda callback, *args, **kwargs: scheduled.append(lambda: callback(*args, **kwargs)),
    )

    seen: list[int] = []
    reporter = CoalescedUiReporter(lambda value: seen.append(value), min_interval_seconds=999.0)
    reporter.report(1)
    reporter.report(2)

    assert len(scheduled) == 1
    scheduled[0]()
    assert seen == [2]


def test_heartbeat_timer_ticks_state(monkeypatch) -> None:
    class FakeTimer:
        def __init__(self, window: object) -> None:
            self.window = window
            self.running = False
            self.interval = None

        def Start(self, interval_ms: int) -> None:  # noqa: N802 - wx-style API
            self.running = True
            self.interval = interval_ms

        def IsRunning(self) -> bool:  # noqa: N802 - wx-style API
            return self.running

        def Stop(self) -> None:  # noqa: N802 - wx-style API
            self.running = False

    class FakeWindow:
        def __init__(self) -> None:
            self.bound = None

        def Bind(self, event: object, handler: object, timer: object) -> None:  # noqa: N802
            self.bound = (event, handler, timer)

    monkeypatch.setattr(
        heartbeat_module,
        "wx",
        SimpleNamespace(Timer=FakeTimer, EVT_TIMER=object()),
    )
    state = heartbeat_module.HeartbeatState()
    window = FakeWindow()

    timer = heartbeat_module.WxHeartbeatTimer(window, state, interval_ms=250)
    event = SimpleNamespace(Skip=lambda: None)
    before = state.last_ui_tick
    window.bound[1](event)

    assert timer.timer.running is True
    assert timer.timer.interval == 250
    assert state.last_ui_tick >= before


def test_watchdog_dumps_when_heartbeat_is_stale() -> None:
    state = heartbeat_module.HeartbeatState()
    with state.lock:
        state.last_ui_tick = time.monotonic() - 10

    dumped: list[str] = []
    watchdog = heartbeat_module.WxHeartbeatWatchdog(
        state,
        dump_callback=lambda reason: dumped.append(reason),
        warn_after_seconds=0.01,
        dump_after_seconds=0.02,
        poll_seconds=0.01,
    )
    watchdog.start()
    deadline = time.monotonic() + 1.0
    try:
        while not dumped and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        watchdog.stop()

    assert dumped


def test_task_manager_removes_completed_tasks_and_logs_failures(caplog) -> None:
    manager = TaskManager(max_workers=1)
    try:
        with caplog.at_level(logging.INFO):
            task = manager.submit(
                "boom", lambda **_kwargs: (_ for _ in ()).throw(ValueError("boom"))
            )
            with pytest.raises(ValueError):
                task.future.result(timeout=1)

        assert "Task failed" in caplog.text
        assert manager.snapshot() == []
    finally:
        manager.shutdown()


def test_task_manager_cancellation_token_raises_cancelled_error() -> None:
    manager = TaskManager(max_workers=1)
    started = threading.Event()

    def worker(*, cancellation_token, **_kwargs):
        started.set()
        while True:
            cancellation_token.raise_if_cancelled()
            time.sleep(0.01)

    try:
        task = manager.submit("cancel", worker)
        assert started.wait(timeout=1)
        task.cancellation_token.cancel()
        with pytest.raises(CancelledError):
            task.future.result(timeout=1)
    finally:
        manager.shutdown()


def test_run_subprocess_safely_times_out(monkeypatch) -> None:
    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["echo"], timeout=0.1)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(subprocess.TimeoutExpired):
        run_subprocess_safely(["echo", "hello"], timeout_seconds=0.1)


def test_safe_regex_times_out(monkeypatch) -> None:
    class FakeCompiled:
        def finditer(self, _text: str, timeout: float):
            raise TimeoutError("timeout")

    monkeypatch.setattr(
        "quill.stability.safe_regex.regex.compile",
        lambda *_args, **_kwargs: FakeCompiled(),
    )

    with pytest.raises(RegexTimeoutError):
        safe_finditer("(a+)+$", "a" * 100)


def test_memory_snapshot_writes_file(tmp_path: Path) -> None:
    start_memory_tracing()
    path = tmp_path / "memory.txt"
    write_memory_snapshot(path)

    assert path.exists()
    assert "QUILL memory snapshot" in path.read_text(encoding="utf-8")


def test_slow_wx_event_handler_logs_warning(caplog) -> None:
    @wx_event_handler("slow-handler", warn_after_ms=0)
    def handler() -> None:
        time.sleep(0.001)

    with caplog.at_level(logging.WARNING):
        handler()

    assert "Slow operation" in caplog.text


def test_safe_mode_configuration_disables_risky_features() -> None:
    config = build_safe_mode_config(True)

    assert config.enabled is True
    assert config.disable_plugins is True
    assert config.disable_ai_integrations is True
    assert should_enable_safe_mode(["--safe-mode"], {}) is True
    assert should_enable_safe_mode([], {"QUILL_SAFE_MODE": "1"}) is True


def test_feature_contract_validation_rejects_risky_ui_thread_features() -> None:
    contract = FeatureContract(
        feature_id="regex_search",
        display_name="Regular Expression Search",
        stability_level="beta",
        default_enabled=False,
        disabled_in_safe_mode=True,
        runs_on_wx_main_thread=True,
        requires_timeout=True,
        supports_cancellation=True,
        reports_progress=True,
        diagnostic_category="search",
    )

    with pytest.raises(ValueError):
        validate_feature_contract(contract)


def test_diagnostic_bundle_includes_metadata(tmp_path: Path) -> None:
    logs = tmp_path / "quill.log"
    logs.write_text("log line", encoding="utf-8")
    bundle = build_diagnostic_bundle(
        logs_path=logs,
        safe_mode=True,
        enabled_plugins=["plugin-a"],
        recent_commands=["file.open"],
        feature_flags={"core.search": True},
        output_path=tmp_path / "bundle.zip",
    )

    assert bundle.exists()
