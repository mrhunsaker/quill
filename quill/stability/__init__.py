from __future__ import annotations

from .crash_report import build_diagnostic_bundle
from .diagnostics import dump_all_thread_stacks, setup_fault_handler
from .feature_contracts import FeatureContract, validate_feature_contract
from .logging_config import configure_logging
from .memory_watch import start_memory_tracing, write_memory_snapshot
from .safe_mode import SafeModeConfig, build_safe_mode_config
from .safe_regex import RegexTimeoutError, safe_finditer, safe_subn
from .safe_subprocess import run_subprocess_safely
from .task_manager import CancellationToken, CancelledError, QuillTask, TaskManager
from .ui_responsiveness import (
    is_wx_main_thread,
    mark_wx_main_thread,
    timed_operation,
    wx_event_handler,
)
from .wx_dispatch import (
    EVT_QUILL_TASK_COMPLETED,
    EVT_QUILL_TASK_FAILED,
    EVT_QUILL_TASK_PROGRESS,
    CoalescedUiReporter,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskProgressEvent,
    call_ui_safely,
)
from .wx_heartbeat import HeartbeatState, WxHeartbeatTimer, WxHeartbeatWatchdog

__all__ = [
    "CancelledError",
    "CancellationToken",
    "CoalescedUiReporter",
    "EVT_QUILL_TASK_COMPLETED",
    "EVT_QUILL_TASK_FAILED",
    "EVT_QUILL_TASK_PROGRESS",
    "FeatureContract",
    "HeartbeatState",
    "QuillTask",
    "RegexTimeoutError",
    "SafeModeConfig",
    "TaskCompletedEvent",
    "TaskFailedEvent",
    "TaskManager",
    "TaskProgressEvent",
    "WxHeartbeatTimer",
    "WxHeartbeatWatchdog",
    "build_diagnostic_bundle",
    "build_safe_mode_config",
    "call_ui_safely",
    "configure_logging",
    "dump_all_thread_stacks",
    "is_wx_main_thread",
    "mark_wx_main_thread",
    "run_subprocess_safely",
    "safe_finditer",
    "safe_subn",
    "setup_fault_handler",
    "start_memory_tracing",
    "timed_operation",
    "validate_feature_contract",
    "write_memory_snapshot",
    "wx_event_handler",
]
