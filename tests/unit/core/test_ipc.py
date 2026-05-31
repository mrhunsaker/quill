from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.ipc as ipc
from quill.core.ipc import (
    drain_open_requests,
    enqueue_open_request,
    release_primary_instance,
    try_claim_primary_instance,
)


def test_try_claim_and_release_primary_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    assert try_claim_primary_instance() is True
    assert try_claim_primary_instance() is False
    release_primary_instance()
    assert try_claim_primary_instance() is True


def test_try_claim_reclaims_dead_pid_lock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    lock_path = tmp_path / "ipc" / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('{"pid": 999999, "created": 1.0}', encoding="utf-8")
    monkeypatch.setattr(ipc, "_pid_is_running", lambda _pid: False)
    assert try_claim_primary_instance() is True


def test_try_claim_reclaims_reused_pid_lock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # PID is alive but its creation time differs from the lock's recorded
    # identity (the PID was reused by another process): reclaim it.
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    lock_path = tmp_path / "ipc" / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('{"pid": 999999, "created": 1.0}', encoding="utf-8")
    monkeypatch.setattr(ipc, "_pid_is_running", lambda _pid: True)
    monkeypatch.setattr(ipc, "_pid_creation_time", lambda _pid: 9999.0)
    assert try_claim_primary_instance() is True


def test_try_claim_honors_live_matching_lock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # PID alive and creation time matches the lock: a real instance is running.
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    lock_path = tmp_path / "ipc" / "instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('{"pid": 999999, "created": 1234.0}', encoding="utf-8")
    monkeypatch.setattr(ipc, "_pid_is_running", lambda _pid: True)
    monkeypatch.setattr(ipc, "_pid_creation_time", lambda _pid: 1234.0)
    assert try_claim_primary_instance() is False


def test_enqueue_and_drain_open_requests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    first = tmp_path / "one.md"
    second = tmp_path / "two.md"
    enqueue_open_request(first)
    enqueue_open_request(second)
    drained = drain_open_requests()
    assert drained == [first, second]
    assert drain_open_requests() == []


def test_enqueue_show_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    enqueue_open_request(None)
    assert drain_open_requests() == [None]
