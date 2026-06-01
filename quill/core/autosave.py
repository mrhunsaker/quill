from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from uuid import UUID

from quill.core.document import Document
from quill.core.paths import app_data_dir


def autosave_document(document: Document, session_id: str, max_snapshots: int = 10) -> Path:
    UUID(session_id)
    autosave_root = app_data_dir() / "autosave" / session_id
    autosave_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    key = _document_key(document)
    target = autosave_root / f"{key}-{stamp}.snap"
    counter = 1
    while target.exists():
        target = autosave_root / f"{key}-{stamp}-{counter:03d}.snap"
        counter += 1
    with target.open("w", encoding=document.encoding, newline="") as file_handle:
        file_handle.write(document.text)

    snapshots = sorted(autosave_root.glob(f"{key}-*.snap"), reverse=True)
    for stale in snapshots[max_snapshots:]:
        stale.unlink(missing_ok=True)
    return target


def latest_autosave(document: Document, session_id: str) -> Path | None:
    UUID(session_id)
    autosave_root = app_data_dir() / "autosave" / session_id
    if not autosave_root.exists():
        return None
    snapshots = sorted(autosave_root.glob(f"{_document_key(document)}-*.snap"), reverse=True)
    if not snapshots:
        return None
    return snapshots[0]


def _document_key(document: Document) -> str:
    seed = str(document.path.resolve()) if document.path else "untitled"
    return sha1(seed.encode("utf-8")).hexdigest()
