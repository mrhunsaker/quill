"""Platform-neutral re-export of the announcement transcript API.

The underlying module is pure Python and platform-independent; the handler the
app installs decides how speech is produced (Prism / VoiceOver / status bar).
"""
from __future__ import annotations

from quill.platform.windows.sr_announce import (  # noqa: F401
    announce,
    clear_transcript,
    enable_transcript_capture,
    set_announce_handler,
    set_transcript_path,
    transcript_entries,
)

__all__ = [
    "announce",
    "clear_transcript",
    "enable_transcript_capture",
    "set_announce_handler",
    "set_transcript_path",
    "transcript_entries",
]
