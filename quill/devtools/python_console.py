"""Embedded Python console using stdlib ``code.InteractiveConsole``.

The console runs in-process and maintains a persistent namespace.
Stdout/stderr are captured per execution so output can appear in the
transcript without polluting the terminal.
"""

from __future__ import annotations

import code
import io
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from quill.core.script_results import ScriptError, ScriptResult, ScriptSuccess


class PythonConsole:
    """Wraps :class:`code.InteractiveConsole` with output capture."""

    def __init__(self, namespace: dict[str, Any]) -> None:
        self._ns = dict(namespace)
        self._ic = code.InteractiveConsole(self._ns)
        self._buffer: list[str] = []
        self._needs_more = False

    # ------------------------------------------------------------------
    # Public API

    def push_line(self, line: str) -> tuple[bool, str]:
        """Push one line; returns (needs_more_input, captured_output).

        If *needs_more_input* is True the statement is incomplete (e.g.
        inside a function body) and the caller should display ``...``
        prompt and send more lines before executing.
        """
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            needs_more = self._ic.push(line)
        self._needs_more = needs_more
        return needs_more, buf.getvalue()

    def execute(self, source: str) -> ScriptResult:
        """Execute a complete source block and return a structured result.

        The namespace persists across calls.  Use :meth:`reset_namespace`
        to start fresh.

        Compilation strategy: try "single" mode first (so bare expression
        results are repr-printed, matching the interactive interpreter).
        Python's single mode requires a trailing newline for compound
        statements (for/while/def/class) — we always append one.  If single
        mode still fails (e.g. multi-statement exec blocks), fall back to
        "exec" mode.
        """
        buf = io.StringIO()
        # Ensure trailing newline so compound statements compile in single mode.
        normalised = source if source.endswith("\n") else source + "\n"
        code_obj = None
        try:
            code_obj = compile(normalised, "<console>", "single")
        except SyntaxError:
            pass
        if code_obj is None:
            try:
                code_obj = compile(normalised, "<console>", "exec")
            except SyntaxError as exc:
                return ScriptError(
                    message=f"Syntax error: {exc.msg}",
                    detail=traceback.format_exc(),
                    suggestion="Check indentation and matching brackets.",
                )
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                exec(code_obj, self._ns)  # noqa: S102
            return ScriptSuccess(value=None, output=buf.getvalue())
        except SystemExit:
            return ScriptError(
                message="sys.exit() is not allowed in the console.",
                suggestion="Close the console window to exit QUILL.",
            )
        except Exception:
            tb = traceback.format_exc()
            last_line = _last_error_line(tb)
            captured = buf.getvalue()
            return ScriptError(
                message=last_line,
                detail=(captured + "\n" + tb) if captured else tb,
            )

    def reset_namespace(self, new_namespace: dict[str, Any]) -> None:
        """Replace the console namespace with *new_namespace*."""
        self._ns.clear()
        self._ns.update(new_namespace)
        self._ic = code.InteractiveConsole(self._ns)
        self._buffer = []
        self._needs_more = False

    def update_namespace(self, updates: dict[str, Any]) -> None:
        """Merge *updates* into the current namespace without wiping it."""
        self._ns.update(updates)

    @property
    def namespace(self) -> dict[str, Any]:
        return self._ns


# ---------------------------------------------------------------------------
# Helpers


def _last_error_line(tb: str) -> str:
    """Extract the last meaningful line from a traceback string."""
    lines = [ln.strip() for ln in tb.splitlines() if ln.strip()]
    return lines[-1] if lines else "Unknown error"
