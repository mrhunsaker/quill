from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic


@dataclass(frozen=True, slots=True)
class StickyNote:
    id: str
    title: str
    body: str
    created_at: str
    updated_at: str

    @classmethod
    def create(cls, body: str, note_id: str | None = None) -> StickyNote:
        timestamp = datetime.now(UTC).isoformat()
        return cls(
            id=note_id or str(uuid4()),
            title=sticky_note_title(body),
            body=body.rstrip(),
            created_at=timestamp,
            updated_at=timestamp,
        )


def sticky_notes_path() -> Path:
    return app_data_dir() / "sticky-notes.json"


def sticky_note_title(body: str) -> str:
    for line in body.splitlines():
        title = line.strip()
        if title:
            return title
    return "Untitled Note"


def _load_note(raw: object) -> StickyNote | None:
    if not isinstance(raw, dict):
        return None
    note_id = str(raw.get("id", "")).strip()
    title = str(raw.get("title", "")).strip()
    body = str(raw.get("body", "")).rstrip()
    created_at = str(raw.get("created_at", "")).strip()
    updated_at = str(raw.get("updated_at", "")).strip()
    if not note_id or not created_at or not updated_at:
        return None
    if not title:
        title = sticky_note_title(body)
    return StickyNote(
        id=note_id,
        title=title,
        body=body,
        created_at=created_at,
        updated_at=updated_at,
    )


def load_sticky_notes() -> list[StickyNote]:
    raw = read_json(sticky_notes_path(), default=[])
    if not isinstance(raw, list):
        return []
    notes: list[StickyNote] = []
    for item in raw:
        note = _load_note(item)
        if note is not None:
            notes.append(note)
    return notes


def save_sticky_notes(notes: list[StickyNote]) -> None:
    write_json_atomic(sticky_notes_path(), [asdict(note) for note in notes])


def get_sticky_note(note_id: str) -> StickyNote | None:
    for note in load_sticky_notes():
        if note.id == note_id:
            return note
    return None


def save_sticky_note(body: str, note_id: str | None = None) -> StickyNote:
    notes = load_sticky_notes()
    existing_index = -1
    existing = None
    if note_id is not None:
        for index, note in enumerate(notes):
            if note.id == note_id:
                existing_index = index
                existing = note
                break
    now = datetime.now(UTC).isoformat()
    updated = StickyNote(
        id=note_id or (existing.id if existing is not None else str(uuid4())),
        title=sticky_note_title(body),
        body=body.rstrip(),
        created_at=existing.created_at if existing is not None else now,
        updated_at=now,
    )
    if existing_index >= 0:
        del notes[existing_index]
    notes.insert(0, updated)
    save_sticky_notes(notes)
    return updated


def delete_sticky_note(note_id: str) -> bool:
    notes = load_sticky_notes()
    filtered = [note for note in notes if note.id != note_id]
    if len(filtered) == len(notes):
        return False
    save_sticky_notes(filtered)
    return True

