"""Official QUILL scripting API — the ``q`` object exposed in the developer console.

The ``QuillScriptAPI`` class is the only stable, supported way to automate the
running editor from console code.  All mutations route through the command
registry so undo/redo, dirty-state tracking, status-bar updates, and
screen-reader announcements remain consistent.

The ``ConsoleHost`` protocol is implemented by the UI mixin
``main_frame_devtools.DevToolsMixin``; it keeps this module wx-free and
independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Host protocol (implemented in the UI layer — no wx import here)
# ---------------------------------------------------------------------------


class ConsoleHost(Protocol):
    """Minimal surface the scripting API needs from the live editor."""

    def console_get_editor_text(self) -> str: ...
    def console_set_editor_text(self, text: str) -> None: ...
    def console_get_selected_text(self) -> str: ...
    def console_replace_selection(self, text: str) -> None: ...
    def console_goto_line(self, line: int) -> None: ...
    def console_goto_offset(self, offset: int) -> None: ...
    def console_get_document_name(self) -> str: ...
    def console_run_command(self, command_id: str) -> None: ...
    def console_command_exists(self, command_id: str) -> bool: ...
    def console_list_commands(self, query: str | None) -> list[tuple[str, str]]: ...
    def console_announce(self, text: str) -> None: ...
    def console_get_last_announcements(self) -> list[str]: ...
    def console_document_stats(self) -> dict[str, int]: ...


# ---------------------------------------------------------------------------
# Snapshot types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentSnapshot:
    name: str
    path: str
    modified: bool
    line_count: int
    char_count: int


@dataclass(frozen=True, slots=True)
class DocumentStats:
    words: int
    lines: int
    chars: int
    paragraphs: int


@dataclass(frozen=True, slots=True)
class CommandInfo:
    id: str
    title: str


# ---------------------------------------------------------------------------
# Sub-facades
# ---------------------------------------------------------------------------


class _A11yFacade:
    """Announcement and accessibility testing facade (q.a11y)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def announce(self, text: str) -> None:
        """Send a screen-reader announcement through QUILL's normal path."""
        self._host.console_announce(text)

    def last_announcements(self) -> list[str]:
        """Return recent announcements (most recent last)."""
        return self._host.console_get_last_announcements()


class _CommandsFacade:
    """Command registry facade (q.commands / standalone ``commands`` name)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def search(self, query: str) -> list[str]:
        """Return command IDs whose title or ID contains *query* (case-insensitive)."""
        q = query.lower()
        return [
            cmd_id
            for cmd_id, title in self._host.console_list_commands(None)
            if q in cmd_id.lower() or q in title.lower()
        ]

    def exists(self, command_id: str) -> bool:
        return self._host.console_command_exists(command_id)

    def run(self, command_id: str) -> None:
        self._host.console_run_command(command_id)

    def list(self, query: str | None = None) -> list[CommandInfo]:
        return [
            CommandInfo(id=cid, title=title)
            for cid, title in self._host.console_list_commands(query)
        ]


class _FocusFacade:
    """Focus inspection facade (q.focus)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def describe(self) -> str:
        """Describe the current editor focus state."""
        name = self._host.console_get_document_name()
        stats = self._host.console_document_stats()
        lines = stats.get("lines", 0)
        chars = stats.get("chars", 0)
        selected = self._host.console_get_selected_text()
        sel_info = f", {len(selected)} chars selected" if selected else ", no selection"
        return f"Editor: {name or '(no document)'}, {lines} lines, {chars} chars{sel_info}"


class _SupportFacade:
    """Support and diagnostics facade (q.support)."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host

    def diagnostic_summary(self) -> str:
        """Return a plain-text diagnostic summary suitable for support tickets."""
        import sys

        from quill.core.paths import app_data_dir

        name = self._host.console_get_document_name() or "(none)"
        stats = self._host.console_document_stats()
        lines = [
            "QUILL diagnostic summary",
            f"Python: {sys.version.split()[0]}",
            f"Active document: {name}",
            f"Document lines: {stats.get('lines', 0)}",
            f"Document words: {stats.get('words', 0)}",
            f"Data directory: {app_data_dir()}",
            "Document content included: no",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Primary scripting API
# ---------------------------------------------------------------------------


class QuillScriptAPI:
    """The ``q`` object available in the QUILL developer console."""

    def __init__(self, host: ConsoleHost) -> None:
        self._host = host
        self.a11y = _A11yFacade(host)
        self.commands = _CommandsFacade(host)
        self.focus = _FocusFacade(host)
        self.support = _SupportFacade(host)

    # -- Text mutations (route through host which routes through command registry) --

    def insert_text(self, text: str) -> None:
        """Insert *text* at the current caret position."""
        if not isinstance(text, str):
            raise TypeError(f"insert_text expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)

    def replace_selection(self, text: str) -> None:
        """Replace the current selection with *text* (or insert if no selection)."""
        if not isinstance(text, str):
            raise TypeError(f"replace_selection expects a str, got {type(text).__name__}")
        self._host.console_replace_selection(text)

    def selected_text(self) -> str:
        """Return the currently selected text (empty string if no selection)."""
        return self._host.console_get_selected_text()

    def document_text(self) -> str:
        """Return the full text of the active document."""
        return self._host.console_get_editor_text()

    def set_document_text(self, text: str) -> None:
        """Replace the entire document text with *text*."""
        if not isinstance(text, str):
            raise TypeError(f"set_document_text expects a str, got {type(text).__name__}")
        self._host.console_set_editor_text(text)

    # -- Navigation --

    def goto_line(self, line: int) -> None:
        """Move the caret to 1-based *line*."""
        if not isinstance(line, int) or line < 1:
            raise ValueError(f"goto_line expects a positive int, got {line!r}")
        self._host.console_goto_line(line)

    def goto_offset(self, offset: int) -> None:
        """Move the caret to absolute character *offset* (0-based)."""
        if not isinstance(offset, int) or offset < 0:
            raise ValueError(f"goto_offset expects a non-negative int, got {offset!r}")
        self._host.console_goto_offset(offset)

    # -- Commands --

    def run_command(self, command_id: str, **kwargs: object) -> None:
        """Run a registered command by ID."""
        if not self._host.console_command_exists(command_id):
            suggestions = self.commands.search(command_id.split(".")[-1])
            hint = ""
            if suggestions:
                hint = f"  Suggestion: try one of {suggestions[:3]}"
            raise KeyError(f"Unknown command: {command_id!r}.{hint}")
        self._host.console_run_command(command_id)

    def command_exists(self, command_id: str) -> bool:
        return self._host.console_command_exists(command_id)

    def list_commands(self, query: str | None = None) -> list[CommandInfo]:
        return [
            CommandInfo(id=cid, title=title)
            for cid, title in self._host.console_list_commands(query)
        ]

    # -- State inspection --

    def active_document(self) -> DocumentSnapshot:
        name = self._host.console_get_document_name()
        stats = self._host.console_document_stats()
        return DocumentSnapshot(
            name=name or "",
            path="",
            modified=False,
            line_count=stats.get("lines", 0),
            char_count=stats.get("chars", 0),
        )

    def document_stats(self) -> DocumentStats:
        s = self._host.console_document_stats()
        return DocumentStats(
            words=s.get("words", 0),
            lines=s.get("lines", 0),
            chars=s.get("chars", 0),
            paragraphs=s.get("paragraphs", 0),
        )

    def refresh_context(self) -> None:
        """Signal that snapshot variables should be updated."""

    # -- Help --

    def help(self, topic: str | None = None) -> str:
        if topic is None:
            return (
                "QUILL scripting API (q):\n"
                "  q.insert_text(text)         Insert text at caret\n"
                "  q.replace_selection(text)   Replace selection\n"
                "  q.selected_text()           Read selection\n"
                "  q.document_text()           Read full document\n"
                "  q.goto_line(n)              Move to line n (1-based)\n"
                "  q.run_command(id)           Run a command by ID\n"
                "  q.list_commands(query)      List/search commands\n"
                "  q.a11y.announce(text)       Send SR announcement\n"
                "  q.support.diagnostic_summary()  Diagnostic report\n"
                "  q.help('method_name')       Help on a specific method"
            )
        doc = getattr(self.__class__, topic, None)
        if doc and doc.__doc__:
            return doc.__doc__.strip()
        return f"No help found for {topic!r}. Try q.list_commands() or q.help()."

    def __repr__(self) -> str:
        return "<QuillScriptAPI — type q.help() for usage>"
