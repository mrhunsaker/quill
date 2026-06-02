"""External file-change detection and safe-reload decisions (FEAT-19).

A small, UI-agnostic helper that watches the open document's file for external
modification or deletion and decides what should happen, without ever touching
``wx`` or moving the cursor itself. The UI layer owns the editor buffer and is
responsible for preserving the cursor, selection, and scroll position when it
acts on a decision; this module only answers *what* should happen.

The model is deliberately pure and testable:

* :class:`FileSnapshot` captures the on-disk identity of a file (existence,
  size, modification time, and a content hash) at a point in time.
* :class:`ExternalChangeWatcher` remembers the last snapshot it reported and,
  on each poll, classifies the file as unchanged, modified, or deleted.
* :func:`decide_reload` turns a change plus the buffer's dirty state and the
  user's settings into one of a small set of :class:`ReloadDecision` actions.

The watcher is polled (reusing the existing watch-folder polling pattern) off
the UI thread; the decision functions are synchronous and side-effect free.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Change classifications reported by the watcher.
CHANGE_NONE = "none"
CHANGE_MODIFIED = "modified"
CHANGE_DELETED = "deleted"


class ReloadAction(Enum):
    """What the UI should do in response to an external change."""

    NONE = "none"
    RELOAD = "reload"
    PROMPT_CONFLICT = "prompt_conflict"
    PROMPT_DELETED = "prompt_deleted"


@dataclass(frozen=True, slots=True)
class ReloadDecision:
    """An action plus a ready-to-speak announcement for the UI to honor."""

    action: ReloadAction
    announcement: str

    @property
    def needs_prompt(self) -> bool:
        return self.action in (ReloadAction.PROMPT_CONFLICT, ReloadAction.PROMPT_DELETED)


@dataclass(frozen=True, slots=True)
class FileSnapshot:
    """The on-disk identity of a file at one moment.

    ``exists`` is ``False`` for a missing/deleted file, in which case the other
    fields are zeroed. ``digest`` is a content hash so a save that rewrites the
    same bytes (or only touches the mtime) is correctly seen as *unchanged*.
    """

    exists: bool
    size: int = 0
    mtime_ns: int = 0
    digest: str = ""

    @classmethod
    def of(cls, path: str | Path) -> FileSnapshot:
        """Snapshot ``path`` now. A missing or unreadable file is ``exists=False``."""
        file_path = Path(path)
        try:
            stat = file_path.stat()
        except (OSError, ValueError):
            return cls(exists=False)
        digest = _hash_file(file_path)
        if digest is None:
            return cls(exists=False)
        return cls(
            exists=True,
            size=int(stat.st_size),
            mtime_ns=int(stat.st_mtime_ns),
            digest=digest,
        )

    def same_content_as(self, other: FileSnapshot) -> bool:
        """True when both exist and hold identical content (ignoring mtime)."""
        if not (self.exists and other.exists):
            return False
        return self.size == other.size and self.digest == other.digest


def _hash_file(path: Path, *, chunk_size: int = 65536) -> str | None:
    """Return a hex SHA-256 of ``path``'s bytes, or None if it can't be read."""
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                hasher.update(chunk)
    except (OSError, ValueError):
        return None
    return hasher.hexdigest()


def classify_change(previous: FileSnapshot, current: FileSnapshot) -> str:
    """Classify the transition from ``previous`` to ``current`` (pure).

    Returns :data:`CHANGE_NONE`, :data:`CHANGE_MODIFIED`, or
    :data:`CHANGE_DELETED`. A file that never existed and still does not is
    ``CHANGE_NONE``; a file that reappears with new content is ``CHANGE_MODIFIED``.
    """
    if not current.exists:
        return CHANGE_DELETED if previous.exists else CHANGE_NONE
    if not previous.exists:
        # The file (re)appeared where we had none — treat as a modification so
        # the UI can offer to load it rather than silently ignoring it.
        return CHANGE_MODIFIED
    return CHANGE_NONE if current.same_content_as(previous) else CHANGE_MODIFIED


class ExternalChangeWatcher:
    """Remembers the last reported snapshot of one file and reports changes.

    Construct with the file's path; :meth:`prime` records the baseline (call it
    right after opening or saving). :meth:`poll` re-snapshots and returns the
    classification relative to the last reported state, advancing the baseline
    so each external change is reported exactly once.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._last = FileSnapshot.of(self._path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def last(self) -> FileSnapshot:
        return self._last

    def prime(self, snapshot: FileSnapshot | None = None) -> None:
        """Reset the baseline to ``snapshot`` (or a fresh on-disk snapshot)."""
        self._last = snapshot if snapshot is not None else FileSnapshot.of(self._path)

    def poll(self) -> str:
        """Re-snapshot and return the change since the last reported state."""
        current = FileSnapshot.of(self._path)
        change = classify_change(self._last, current)
        if change != CHANGE_NONE:
            self._last = current
        return change


def decide_reload(
    change: str,
    *,
    buffer_dirty: bool,
    watch_enabled: bool = True,
    auto_reload_when_clean: bool = True,
    prompt_on_conflict: bool = True,
    file_name: str = "",
) -> ReloadDecision:
    """Decide what to do for ``change`` given the buffer state and settings (pure).

    Safe and quiet by default:

    * Watching off, or no change → do nothing.
    * Modified while the buffer is clean → reload in place (when enabled), or
      prompt so nothing is silent (when auto-reload is off).
    * Modified while the buffer is dirty → never overwrite silently; prompt for
      reload / keep-mine / compare (when prompting is on), else stay quiet.
    * Deleted → prompt; the buffer is kept so the user's text is never lost.
    """
    if not watch_enabled or change == CHANGE_NONE:
        return ReloadDecision(ReloadAction.NONE, "")

    label = f" ({file_name})" if file_name else ""

    if change == CHANGE_DELETED:
        if prompt_on_conflict:
            return ReloadDecision(
                ReloadAction.PROMPT_DELETED,
                f"The file{label} was deleted on disk. Keep your text or close.",
            )
        return ReloadDecision(ReloadAction.NONE, "")

    # change == CHANGE_MODIFIED
    if buffer_dirty:
        if prompt_on_conflict:
            return ReloadDecision(
                ReloadAction.PROMPT_CONFLICT,
                f"The file{label} changed on disk and you have unsaved edits. "
                "Reload, keep mine, or compare.",
            )
        return ReloadDecision(ReloadAction.NONE, "")

    if auto_reload_when_clean:
        return ReloadDecision(ReloadAction.RELOAD, "Reloaded from disk.")
    return ReloadDecision(
        ReloadAction.PROMPT_CONFLICT,
        f"The file{label} changed on disk. Reload to see the new version.",
    )
