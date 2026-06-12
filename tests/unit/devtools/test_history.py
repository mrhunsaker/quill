"""Tests for quill.devtools.history."""

from __future__ import annotations

import pytest

from quill.devtools import history as hist


@pytest.fixture(autouse=True)
def _isolated_history(tmp_path, monkeypatch):
    """Redirect app_data_dir to a temp path for each test."""
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("quill.core.paths._DEV_BUILD", True)
    yield


def test_add_and_load_roundtrip():
    hist.add_entry("python", "q.goto_line(1)", success=True)
    hist.add_entry("typescript", "await quill.gotoLine(1)", success=False)
    entries = hist.load()
    assert len(entries) == 2
    assert entries[0].language == "python"
    assert entries[0].source == "q.goto_line(1)"
    assert entries[0].success is True
    assert entries[1].language == "typescript"
    assert entries[1].success is False


def test_load_returns_newest_last():
    for i in range(5):
        hist.add_entry("python", f"line {i}", success=True)
    entries = hist.load()
    assert entries[-1].source == "line 4"


def test_load_respects_max():
    for i in range(20):
        hist.add_entry("python", f"cmd {i}", success=True)
    entries = hist.load(max_entries=5)
    assert len(entries) == 5
    assert entries[0].source == "cmd 15"


def test_clear_removes_all_entries():
    hist.add_entry("python", "q.help()", success=True)
    hist.clear()
    assert hist.load() == []


def test_load_on_missing_file_returns_empty():
    entries = hist.load()
    assert entries == []


def test_corrupted_lines_are_skipped(tmp_path, monkeypatch):
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    path = tmp_path / "console" / "history.jsonl"
    path.parent.mkdir(parents=True)
    valid = '{"timestamp":"t","language":"python","source":"ok","success":true}'
    path.write_text('{"not_valid": true}\n' + valid + "\n", encoding="utf-8")
    entries = hist.load()
    # The corrupted first entry (missing required fields) silently skips;
    # the second valid entry must survive.
    assert any(e.source == "ok" for e in entries)
