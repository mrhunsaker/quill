"""Tests for watch profiles and the multi-profile manager (WATCH-1, WATCH-5)."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from quill.core.watch_profiles import (
    POST_LEAVE,
    POST_MOVE,
    SCHED_QUIET,
    SCHED_WINDOW,
    WatchManager,
    WatchProfile,
    iter_matching_files,
    profile_is_active,
)
from quill.core.watch_queue import STATE_QUEUED, WatchQueue


def _make_old_file(path: Path, content: str = "hi") -> Path:
    path.write_text(content, encoding="utf-8")
    old = time.time() - 3600
    import os

    os.utime(path, (old, old))
    return path


def test_normalized_clamps_poll_and_fills_id() -> None:
    profile = WatchProfile(poll_interval_seconds=1, name="  ", suffixes=("TXT", ".md")).normalized()
    assert profile.poll_interval_seconds == 2  # clamped to minimum
    assert profile.profile_id  # generated
    assert profile.name == "Untitled profile"
    assert profile.suffixes == (".txt", ".md")  # normalized + deduped


def test_validate_requires_existing_folder(tmp_path: Path) -> None:
    missing = WatchProfile(folder_path=str(tmp_path / "nope"), enabled=True)
    assert any("does not exist" in p for p in missing.validate())
    present = WatchProfile(folder_path=str(tmp_path), enabled=True)
    assert present.validate() == []


def test_validate_move_post_action_needs_destination(tmp_path: Path) -> None:
    profile = WatchProfile(
        folder_path=str(tmp_path),
        enabled=True,
        post_action=POST_MOVE,
        post_action_destination="",
    )
    assert any("destination" in p.lower() for p in profile.validate())


def test_profile_round_trip_dict(tmp_path: Path) -> None:
    profile = WatchProfile(
        profile_id="p1",
        name="Inbox",
        enabled=True,
        folder_path=str(tmp_path),
        action_id="move",
        action_options={"destination": str(tmp_path)},
        post_action=POST_LEAVE,
    ).normalized()
    restored = WatchProfile.from_dict(profile.to_dict())
    assert restored.name == "Inbox"
    assert restored.action_id == "move"
    assert restored.action_options == {"destination": str(tmp_path)}


def test_iter_matching_files_applies_filters(tmp_path: Path) -> None:
    _make_old_file(tmp_path / "keep.txt")
    _make_old_file(tmp_path / "skip.png")
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    profile = WatchProfile(folder_path=str(tmp_path), suffixes=(".txt",), min_size_bytes=1)
    names = {p.name for p in iter_matching_files(profile)}
    assert names == {"keep.txt"}


def test_iter_matching_files_skips_too_new(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh.txt"
    fresh.write_text("hi", encoding="utf-8")
    profile = WatchProfile(folder_path=str(tmp_path), suffixes=(".txt",), min_age_seconds=60.0)
    assert list(iter_matching_files(profile)) == []


def test_iter_matching_files_missing_folder_is_empty(tmp_path: Path) -> None:
    profile = WatchProfile(folder_path=str(tmp_path / "gone"), suffixes=(".txt",))
    assert list(iter_matching_files(profile)) == []


def test_iter_matching_files_subfolders(tmp_path: Path) -> None:
    nested = tmp_path / "sub"
    nested.mkdir()
    _make_old_file(nested / "deep.txt")
    flat = WatchProfile(folder_path=str(tmp_path), suffixes=(".txt",), include_subfolders=False)
    deep = WatchProfile(folder_path=str(tmp_path), suffixes=(".txt",), include_subfolders=True)
    assert list(iter_matching_files(flat)) == []
    assert [p.name for p in iter_matching_files(deep)] == ["deep.txt"]


def test_iter_matching_files_applies_name_patterns(tmp_path: Path) -> None:
    _make_old_file(tmp_path / "report-jan.txt")
    _make_old_file(tmp_path / "report-feb.txt")
    _make_old_file(tmp_path / "notes.txt")
    profile = WatchProfile(
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        name_patterns=("report-*",),
        min_size_bytes=1,
    )
    names = {p.name for p in iter_matching_files(profile)}
    assert names == {"report-jan.txt", "report-feb.txt"}


def test_name_patterns_round_trip(tmp_path: Path) -> None:
    profile = WatchProfile(
        folder_path=str(tmp_path),
        name_patterns=(" *.LOG ", "draft-*"),
    ).normalized()
    assert profile.name_patterns == ("*.LOG", "draft-*")
    restored = WatchProfile.from_dict(profile.to_dict())
    assert restored.name_patterns == ("*.LOG", "draft-*")


def test_schedule_always_is_active() -> None:
    profile = WatchProfile().normalized()
    assert profile_is_active(profile, now=datetime(2026, 6, 2, 3, 0))


def test_schedule_window_active_only_inside() -> None:
    # Active window 09:00-17:00.
    profile = WatchProfile(
        schedule_mode=SCHED_WINDOW,
        schedule_start_minute=9 * 60,
        schedule_end_minute=17 * 60,
    ).normalized()
    assert profile_is_active(profile, now=datetime(2026, 6, 2, 12, 0))
    assert not profile_is_active(profile, now=datetime(2026, 6, 2, 8, 0))
    assert not profile_is_active(profile, now=datetime(2026, 6, 2, 17, 0))


def test_schedule_quiet_hours_wraps_midnight() -> None:
    # Quiet 22:00-07:00 (wraps midnight): dormant inside, active outside.
    profile = WatchProfile(
        schedule_mode=SCHED_QUIET,
        schedule_start_minute=22 * 60,
        schedule_end_minute=7 * 60,
    ).normalized()
    assert not profile_is_active(profile, now=datetime(2026, 6, 2, 23, 30))
    assert not profile_is_active(profile, now=datetime(2026, 6, 2, 2, 0))
    assert profile_is_active(profile, now=datetime(2026, 6, 2, 12, 0))


def test_schedule_window_zero_width_is_invalid() -> None:
    profile = WatchProfile(
        folder_path=".",
        schedule_mode=SCHED_WINDOW,
        schedule_start_minute=600,
        schedule_end_minute=600,
    )
    assert any("schedule window" in p.lower() for p in profile.validate())


def _wait_until(predicate, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def test_manager_enqueues_new_files(tmp_path: Path) -> None:
    queue = WatchQueue()
    manager = WatchManager(queue)
    profile = WatchProfile(
        profile_id="p1",
        name="Inbox",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        min_age_seconds=0.0,
        process_existing=True,
        poll_interval_seconds=2,
    )
    started = manager.start([profile])
    try:
        assert started == ["p1"]
        _make_old_file(tmp_path / "new.txt")
        assert _wait_until(lambda: queue.pending_count() >= 1)
    finally:
        manager.stop()
    assert manager.is_running is False
    sources = {Path(item.source_path).name for item in queue.items()}
    assert "new.txt" in sources


def test_manager_skips_existing_when_disabled(tmp_path: Path) -> None:
    _make_old_file(tmp_path / "already.txt")
    queue = WatchQueue()
    manager = WatchManager(queue)
    profile = WatchProfile(
        profile_id="p1",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        min_age_seconds=0.0,
        process_existing=False,
        poll_interval_seconds=2,
    )
    manager.start([profile])
    try:
        # Existing file should be primed (de-dup reserved), never enqueued.
        time.sleep(0.3)
        assert queue.items() == []
    finally:
        manager.stop()


def test_manager_skips_disabled_and_invalid_profiles(tmp_path: Path) -> None:
    queue = WatchQueue()
    manager = WatchManager(queue)
    disabled = WatchProfile(profile_id="off", enabled=False, folder_path=str(tmp_path))
    invalid = WatchProfile(profile_id="bad", enabled=True, folder_path=str(tmp_path / "nope"))
    started = manager.start([disabled, invalid])
    try:
        assert started == []
    finally:
        manager.stop()


def test_manager_dedup_across_overlapping_profiles(tmp_path: Path) -> None:
    queue = WatchQueue()
    manager = WatchManager(queue)
    common = WatchProfile(
        profile_id="p1",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        min_age_seconds=0.0,
        process_existing=True,
        poll_interval_seconds=2,
    )
    other = WatchProfile(
        profile_id="p2",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        min_age_seconds=0.0,
        process_existing=True,
        poll_interval_seconds=2,
    )
    manager.start([common, other])
    try:
        _make_old_file(tmp_path / "shared.txt")
        assert _wait_until(lambda: queue.pending_count() >= 1)
        time.sleep(0.3)
        matching = [i for i in queue.items() if Path(i.source_path).name == "shared.txt"]
        assert len(matching) == 1  # claimed exactly once across both profiles
        assert matching[0].state == STATE_QUEUED
    finally:
        manager.stop()


# --- M-4: per-profile error tracking ---------------------------------------


def test_manager_records_prescan_error_for_profile(tmp_path: Path, monkeypatch) -> None:
    """M-4: a prescan failure must be attributable to a specific profile_id."""
    queue = WatchQueue()
    manager = WatchManager(queue)
    profile = WatchProfile(
        profile_id="p1",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        process_existing=False,
        poll_interval_seconds=2,
    )

    def boom(_profile):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("quill.core.watch_profiles.iter_matching_files", boom)
    manager.start([profile])
    try:
        assert _wait_until(lambda: manager.last_error("p1") is not None, timeout=3.0)
        assert "PermissionError" in (manager.last_error("p1") or "")
        assert manager.consecutive_error_count("p1") >= 1
    finally:
        manager.stop()


def test_manager_records_scan_error_and_clears_on_recovery(tmp_path: Path, monkeypatch) -> None:
    """M-4: scan errors accumulate; a successful scan clears the counter."""
    queue = WatchQueue()
    manager = WatchManager(queue)
    profile = WatchProfile(
        profile_id="p1",
        enabled=True,
        folder_path=str(tmp_path),
        suffixes=(".txt",),
        process_existing=True,
        poll_interval_seconds=2,
    )

    calls = {"n": 0}

    def flaky(_profile):
        calls["n"] += 1
        if calls["n"] < 3:
            raise OSError(22, "Invalid argument")
        return iter([])

    monkeypatch.setattr("quill.core.watch_profiles.iter_matching_files", flaky)
    manager.start([profile])
    try:
        assert _wait_until(lambda: manager.consecutive_error_count("p1") >= 2, timeout=5.0)
        assert _wait_until(lambda: manager.consecutive_error_count("p1") == 0, timeout=5.0)
        assert manager.last_error("p1") is None
    finally:
        manager.stop()
