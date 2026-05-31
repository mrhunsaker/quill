"""Regression tests for sticky-note persistence behavior.

These lock in the invariants that are easy to break in a refactor but invisible
in the happy-path test: created_at is preserved across an edit, edits move a note
to the front (most-recent-first), unknown ids are handled, malformed JSON is
skipped rather than crashing, and titles/bodies are normalized on load.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import quill.core.sticky_notes as sticky_notes_module
from quill.core.sticky_notes import (
    delete_sticky_note,
    get_sticky_note,
    load_sticky_notes,
    save_sticky_note,
    save_sticky_notes,
    sticky_note_title,
)


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the sticky-notes store at a temp file for each test."""
    path = tmp_path / "sticky-notes.json"
    monkeypatch.setattr(sticky_notes_module, "sticky_notes_path", lambda: path)
    return path


def test_edit_preserves_created_at_and_updates_updated_at(store: Path) -> None:
    note = save_sticky_note("Original\nbody")
    edited = save_sticky_note("Original revised\nbody", note_id=note.id)

    assert edited.id == note.id
    assert edited.created_at == note.created_at  # created stays put
    assert edited.updated_at >= note.updated_at  # touched on edit
    assert edited.title == "Original revised"


def test_edit_moves_note_to_front(store: Path) -> None:
    first = save_sticky_note("First")
    second = save_sticky_note("Second")
    # Newest save is at the front.
    assert [n.id for n in load_sticky_notes()] == [second.id, first.id]

    # Editing the older note moves it back to the front.
    save_sticky_note("First edited", note_id=first.id)
    assert [n.id for n in load_sticky_notes()] == [first.id, second.id]


def test_save_with_unknown_id_creates_a_note_with_that_id(store: Path) -> None:
    created = save_sticky_note("Brand new", note_id="custom-id-123")
    assert created.id == "custom-id-123"
    assert get_sticky_note("custom-id-123") is not None


def test_delete_unknown_id_returns_false_and_keeps_others(store: Path) -> None:
    note = save_sticky_note("Keep me")
    assert delete_sticky_note("does-not-exist") is False
    assert [n.id for n in load_sticky_notes()] == [note.id]


def test_get_sticky_note_found_and_missing(store: Path) -> None:
    note = save_sticky_note("Findable")
    assert get_sticky_note(note.id).body == "Findable"
    assert get_sticky_note("nope") is None


def test_body_trailing_whitespace_is_trimmed(store: Path) -> None:
    note = save_sticky_note("Title line\nbody text\n\n   \n")
    assert note.body == "Title line\nbody text"
    assert load_sticky_notes()[0].body == "Title line\nbody text"


def test_load_skips_malformed_entries(store: Path) -> None:
    # Mix valid and invalid records: non-dict, missing id, missing timestamps.
    store.write_text(
        json.dumps(
            [
                {
                    "id": "ok",
                    "title": "Valid",
                    "body": "x",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
                "not a dict",
                {"title": "no id", "body": "y", "created_at": "t", "updated_at": "t"},
                {"id": "no-timestamps", "title": "z", "body": "z"},
            ]
        ),
        encoding="utf-8",
    )
    notes = load_sticky_notes()
    assert [n.id for n in notes] == ["ok"]


def test_load_handles_non_list_payload(store: Path) -> None:
    store.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
    assert load_sticky_notes() == []


def test_load_backfills_missing_title_from_body(store: Path) -> None:
    store.write_text(
        json.dumps(
            [
                {
                    "id": "n1",
                    "title": "",
                    "body": "  \nDerived title\nrest",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    assert load_sticky_notes()[0].title == "Derived title"


def test_round_trip_through_disk(store: Path) -> None:
    note = save_sticky_note("Persisted\ncontent")
    # Re-read straight from disk via the public loader.
    again = load_sticky_notes()
    assert len(again) == 1
    assert again[0] == note


def test_save_sticky_notes_writes_newest_first_order(store: Path) -> None:
    a = save_sticky_note("A")
    b = save_sticky_note("B")
    c = save_sticky_note("C")
    # Reorder explicitly and confirm the order survives a reload.
    save_sticky_notes([a, c, b])
    assert [n.id for n in load_sticky_notes()] == [a.id, c.id, b.id]


def test_title_helper_edge_cases() -> None:
    assert sticky_note_title("   ") == "Untitled Note"
    assert sticky_note_title("\n\n\tFirst real line\nsecond") == "First real line"
