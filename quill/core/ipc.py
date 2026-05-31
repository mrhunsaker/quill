from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from quill.core.paths import app_data_dir


def try_claim_primary_instance() -> bool:
    lock_path = _lock_file_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        # Only honor a lock that belongs to a still-running instance of *this*
        # app (PID alive AND same process identity). Anything else — a dead PID,
        # a reused PID, or a corrupt lock — is stale, so reclaim it. This makes
        # the single-instance guard self-heal after an unclean exit/crash.
        info = _read_lock(lock_path)
        if info is not None and _lock_belongs_to_live_instance(info):
            return False
        lock_path.unlink(missing_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(_lock_payload())
    return True


def release_primary_instance() -> None:
    lock_path = _lock_file_path()
    info = _read_lock(lock_path)
    if info is not None and info.get("pid") == os.getpid():
        lock_path.unlink(missing_ok=True)


def _lock_payload() -> str:
    return json.dumps({"pid": os.getpid(), "created": _pid_creation_time(os.getpid())})


def _read_lock(lock_path: Path) -> dict | None:
    try:
        raw = lock_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:  # backward compatibility: older locks held a bare PID
            return {"pid": int(raw), "created": None}
        except ValueError:
            return None
    if isinstance(data, dict) and isinstance(data.get("pid"), int):
        return data
    return None


def _lock_belongs_to_live_instance(info: dict) -> bool:
    pid = info.get("pid")
    if not isinstance(pid, int) or not _pid_is_running(pid):
        return False  # dead PID -> stale, reclaim
    created = info.get("created")
    actual = _pid_creation_time(pid)
    if created is not None and actual is not None:
        # Reused PID if the running process didn't start when we recorded it.
        return abs(actual - created) < 2.0
    return True  # no identity info (e.g. non-Windows): alive is enough


@dataclass(frozen=True, slots=True)
class OpenRequest:
    path: Path
    line: int | None = None
    column: int | None = None


def enqueue_open_request(
    path: Path | None,
    *,
    line: int | None = None,
    column: int | None = None,
) -> None:
    queue_path = _queue_file_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8", newline="\n") as handle:
        payload = (
            {"action": "show"}
            if path is None
            else {
                "action": "open",
                "path": str(path),
                "line": line,
                "column": column,
            }
        )
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def drain_open_requests() -> list[OpenRequest | None]:
    queue_path = _queue_file_path()
    if not queue_path.exists():
        return []
    lines = queue_path.read_text(encoding="utf-8").splitlines()
    queue_path.unlink(missing_ok=True)
    requests: list[OpenRequest | None] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        action = str(raw.get("action", "open")).strip().lower()
        if action == "show":
            requests.append(None)
            continue
        if isinstance(raw.get("path"), str):
            line_number = raw.get("line")
            column_number = raw.get("column")
            requests.append(
                OpenRequest(
                    path=Path(raw["path"]),
                    line=int(line_number) if isinstance(line_number, int) else None,
                    column=int(column_number) if isinstance(column_number, int) else None,
                )
            )
    return requests


def _lock_file_path() -> Path:
    return app_data_dir() / "ipc" / "instance.lock"


def _queue_file_path() -> Path:
    return app_data_dir() / "ipc" / "open-requests.jsonl"


def _read_pid(lock_path: Path) -> int | None:
    if not lock_path.exists():
        return None
    raw = lock_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _pid_lock_is_stale(pid: int, lock_path: Path) -> bool:
    if os.name != "nt":
        return False
    process_started = _pid_creation_time(pid)
    if process_started is None:
        return False
    lock_mtime = lock_path.stat().st_mtime
    return process_started > lock_mtime + 2.0


def _pid_creation_time(pid: int) -> float | None:
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return None
    creation_time = wintypes.FILETIME()
    exit_time = wintypes.FILETIME()
    kernel_time = wintypes.FILETIME()
    user_time = wintypes.FILETIME()
    try:
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation_time),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            return None
        return _filetime_to_timestamp(creation_time)
    finally:
        kernel32.CloseHandle(handle)


def _filetime_to_timestamp(filetime: object) -> float:
    ft = cast(Any, filetime)
    low = int(ft.dwLowDateTime)
    high = int(ft.dwHighDateTime)
    value = (high << 32) | low
    return value / 10_000_000 - 11_644_473_600
