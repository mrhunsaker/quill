from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.sticky_notes as sticky_notes_module
from quill.core.sticky_notes import (
    delete_sticky_note,
    load_sticky_notes,
    save_sticky_note,
    sticky_note_title,
)


def test_sticky_note_title_uses_first_non_empty_line() -> None:
    assert sticky_note_title("\n  \nProject ideas\nMore text") == "Project ideas"
    assert sticky_note_title("") == "Untitled Note"


def test_save_load_and_delete_sticky_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_path = tmp_path / "sticky-notes.json"
    monkeypatch.setattr(sticky_notes_module, "sticky_notes_path", lambda: store_path)

    note = save_sticky_note("First line\nMore detail")
    notes = load_sticky_notes()

    assert len(notes) == 1
    assert notes[0].id == note.id
    assert notes[0].title == "First line"

    updated = save_sticky_note("Updated title\nBody", note_id=note.id)
    notes = load_sticky_notes()
    assert len(notes) == 1
    assert notes[0].id == updated.id
    assert notes[0].title == "Updated title"

    assert delete_sticky_note(updated.id) is True
    assert load_sticky_notes() == []
