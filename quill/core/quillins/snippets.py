"""Layer 1 snippet placeholder expansion for Quillins.

A snippet-only Quillin (no ``main`` module, no capabilities) contributes literal
text with a small, fixed set of placeholders documented in ``docs/scripting.md``
§14.3. This module expands those placeholders. It executes **no code** — it only
substitutes known tokens — which is exactly why Layer 1 is fully sandboxable.

Supported placeholders:

* ``${selection}`` — the current selection (empty string if none)
* ``${clipboard}`` — current clipboard text (requires the ``clipboard.read``
  capability at the call site; this module just substitutes what it is given)
* ``${date}`` — current date in the user's configured format
* ``${time}`` — current time in the user's configured format
* ``${filename}`` — current document file name (empty if unsaved)
* ``${cursor}`` — marks where the caret lands after insertion

Unknown ``${...}`` tokens are left untouched so an author sees their mistake in
the inserted text rather than silently losing it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

_PLACEHOLDER_PATTERN = re.compile(r"\$\{([^{}]+)\}")


@dataclass(frozen=True, slots=True)
class SnippetContext:
    """Values available to a snippet at expansion time.

    ``date`` and ``time`` may be pre-formatted by the caller (honouring the
    user's configured formats); when omitted they fall back to ISO-ish defaults
    so the engine stays usable and deterministic in tests.
    """

    selection: str = ""
    clipboard: str = ""
    filename: str = ""
    date: str | None = None
    time: str | None = None


@dataclass(frozen=True, slots=True)
class SnippetExpansion:
    """The result of expanding a snippet body."""

    text: str
    cursor: int


def expand_snippet(body: str, context: SnippetContext) -> SnippetExpansion:
    """Expand ``body`` against ``context`` and locate the final caret.

    The first ``${cursor}`` marker sets the caret offset; when absent the caret
    lands at the end of the inserted text.
    """

    now = datetime.now()
    date_value = context.date if context.date is not None else now.strftime("%Y-%m-%d")
    time_value = context.time if context.time is not None else now.strftime("%H:%M")
    substitutions = {
        "selection": context.selection,
        "clipboard": context.clipboard,
        "filename": context.filename,
        "date": date_value,
        "time": time_value,
    }

    chunks: list[str] = []
    cursor: int | None = None
    index = 0
    for match in _PLACEHOLDER_PATTERN.finditer(body):
        chunks.append(body[index : match.start()])
        token = match.group(1).strip()
        if token == "cursor":
            if cursor is None:
                cursor = len("".join(chunks))
        elif token in substitutions:
            chunks.append(substitutions[token])
        else:
            chunks.append(match.group(0))
        index = match.end()
    chunks.append(body[index:])

    text = "".join(chunks)
    if cursor is None or cursor > len(text):
        cursor = len(text)
    return SnippetExpansion(text=text, cursor=cursor)
