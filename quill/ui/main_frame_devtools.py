"""Developer Console mixin for ``MainFrame`` (QDC feature).

Wires the QUILL Developer Console (Python + TypeScript) into the running
editor.  Implements the ``ConsoleHost`` protocol so ``QuillScriptAPI`` can
reach editor state without importing wx.

Threading contract:
- Console UI runs on the wx UI thread.
- Python execution is synchronous on the UI thread (short commands only; long
  commands should be wrapped in a background task by the user via threading).
- TypeScript execution runs a Node subprocess; the result arrives via
  threading.Event and is posted back to the UI with wx.CallAfter.
"""

from __future__ import annotations

import threading
from typing import Any

from quill.core.scripting import QuillScriptAPI
from quill.devtools import history as _history
from quill.devtools.console_window import ConsoleWindow
from quill.devtools.python_console import PythonConsole
from quill.devtools.ts_console import TypeScriptConsole, TypeScriptConsoleError

_CONSENT_KEY = "console_consent_shown"
_CONSENT_TEXT = (
    "Developer Console\n\n"
    "This console can run code inside QUILL and may change the current document.\n"
    "Only run commands you understand or received from a trusted source.\n\n"
    "Recommended:\n"
    "- Use q.run_command(...) or documented q methods.\n"
    "- Do not paste code from unknown sources.\n"
    "- Save your document before running document-wide commands."
)


class DevToolsMixin:
    """Mixin that adds the QUILL Developer Console to ``MainFrame``."""

    # ------------------------------------------------------------------
    # Lazy-init state accessors

    def _dt_python_console(self) -> PythonConsole:
        if not hasattr(self, "_dev_python_console"):
            self._dev_python_console = PythonConsole(self._dt_make_namespace())
        return self._dev_python_console

    def _dt_ts_console(self) -> TypeScriptConsole:
        if not hasattr(self, "_dev_ts_console"):
            self._dev_ts_console = TypeScriptConsole(host=self)
        return self._dev_ts_console

    def _dt_window(self) -> ConsoleWindow:
        if not hasattr(self, "_dev_console_window"):
            self._dev_console_window = ConsoleWindow(
                wx=self._wx,
                parent=self.frame,
                on_execute_python=self._dt_on_execute_python,
                on_execute_ts=self._dt_on_execute_ts,
            )
        return self._dev_console_window

    # ------------------------------------------------------------------
    # ConsoleHost protocol implementation

    def console_get_editor_text(self) -> str:
        try:
            return self.editor.GetValue()
        except Exception:
            return ""

    def console_set_editor_text(self, text: str) -> None:
        try:
            self.editor.SetValue(text)
            self._mark_document_modified()
        except Exception:
            pass

    def console_get_selected_text(self) -> str:
        try:
            return self.editor.GetStringSelection()
        except Exception:
            return ""

    def console_replace_selection(self, text: str) -> None:
        try:
            self.editor.WriteText(text)
            self._mark_document_modified()
        except Exception:
            pass

    def console_goto_line(self, line: int) -> None:
        try:
            idx = self.editor.XYToPosition(0, line - 1)
            self.editor.SetInsertionPoint(idx)
            self.editor.ShowPosition(idx)
        except Exception:
            pass

    def console_goto_offset(self, offset: int) -> None:
        try:
            self.editor.SetInsertionPoint(offset)
            self.editor.ShowPosition(offset)
        except Exception:
            pass

    def console_get_document_name(self) -> str:
        try:
            path = self._active_document_path()
            return path.name if path else ""
        except Exception:
            return ""

    def console_run_command(self, command_id: str) -> None:
        self.commands.run(command_id)

    def console_command_exists(self, command_id: str) -> bool:
        return self.commands.get(command_id) is not None

    def console_list_commands(self, query: str | None) -> list[tuple[str, str]]:
        cmds = self.commands.list()
        if query:
            q = query.lower()
            cmds = [c for c in cmds if q in c.id.lower() or q in c.title.lower()]
        return [(c.id, c.title) for c in cmds]

    def console_announce(self, text: str) -> None:
        self._announce(text)

    def console_get_last_announcements(self) -> list[str]:
        try:
            return list(getattr(self, "_announcement_log", []))
        except Exception:
            return []

    def console_document_stats(self) -> dict[str, int]:
        try:
            text = self.editor.GetValue()
            lines = text.count("\n") + (1 if text else 0)
            words = len(text.split()) if text else 0
            chars = len(text)
            paragraphs = len([p for p in text.split("\n\n") if p.strip()])
            return {"words": words, "lines": lines, "chars": chars, "paragraphs": paragraphs}
        except Exception:
            return {"words": 0, "lines": 0, "chars": 0, "paragraphs": 0}

    # ------------------------------------------------------------------
    # Public entry points

    def open_python_console(self) -> None:
        """Tools > Advanced > Developer Console > Open Python Console"""
        if not self._dt_consent_check():
            return
        win = self._dt_window()
        py = self._dt_python_console()
        py.update_namespace(self._dt_snapshot_vars())
        entries = [e.source for e in _history.load(50)]
        win.load_history(entries)
        win.set_status(f"Ready - Python | {self.console_get_document_name() or 'no document'}")
        win.show()

    def open_typescript_console(self) -> None:
        """Tools > Advanced > Developer Console > Open TypeScript Console"""
        if not self._dt_consent_check():
            return
        win = self._dt_window()
        entries = [e.source for e in _history.load(50) if e.language == "typescript"]
        win.load_history(entries)
        win.set_status(f"Ready - TypeScript | {self.console_get_document_name() or 'no document'}")
        win.show()
        ts = self._dt_ts_console()
        if not ts.is_running():
            threading.Thread(target=self._dt_start_ts_worker, daemon=True).start()

    def copy_diagnostic_summary(self) -> None:
        """Tools > Advanced > Developer Console > Copy Diagnostic Summary"""
        api = QuillScriptAPI(self)
        summary = api.support.diagnostic_summary()
        wx = self._wx
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(summary))
            wx.TheClipboard.Close()
        self._announce("Diagnostic summary copied to clipboard.")

    def restart_typescript_worker(self) -> None:
        self._dt_ts_console()  # ensure created before thread starts
        threading.Thread(target=self._dt_restart_ts_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Execution callbacks (called from ConsoleWindow on UI thread)

    def _dt_on_execute_python(self, source: str, prompt: str) -> None:
        win = self._dt_window()
        py = self._dt_python_console()
        py.update_namespace(self._dt_snapshot_vars())
        win.append_transcript(f"{prompt}{source}\n")
        result = py.execute(source)
        from quill.core.script_results import ScriptSuccess

        if isinstance(result, ScriptSuccess):
            if result.output:
                win.append_transcript(result.output)
                self._dt_announce_output(result.output)
            if result.value is not None:
                win.append_transcript(f"Result: {result.value!r}\n")
                self._announce(f"Result: {result.value!r}")
            elif not result.output:
                # Silent success — announce so SR user knows it ran
                self._announce("Done.")
            _history.add_entry("python", source, success=True)
        else:
            win.append_transcript(f"Error: {result.message}\n")
            if result.suggestion:
                win.append_transcript(f"Suggestion: {result.suggestion}\n")
            if result.detail:
                win.append_transcript(f"Details:\n{result.detail}\n")
            self._announce(f"Error: {result.message}")
            _history.add_entry("python", source, success=False)

    def _dt_on_execute_ts(self, source: str, prompt: str) -> None:
        win = self._dt_window()
        win.append_transcript(f"{prompt}{source}\n")
        win.set_status("Running TypeScript...")
        self._announce("Running TypeScript.")
        ts = self._dt_ts_console()
        threading.Thread(
            target=self._dt_ts_execute_thread,
            args=(ts, source, win),
            daemon=True,
        ).start()

    def _dt_ts_execute_thread(self, ts: TypeScriptConsole, source: str, win: ConsoleWindow) -> None:
        result = ts.execute(source)
        self._wx.CallAfter(self._dt_ts_done, result, source, win)

    def _dt_ts_done(self, result: Any, source: str, win: ConsoleWindow) -> None:
        from quill.core.script_results import ScriptSuccess

        if isinstance(result, ScriptSuccess):
            if result.output:
                win.append_transcript(result.output + "\n")
                self._dt_announce_output(result.output)
            if result.value is not None:
                win.append_transcript(f"Result: {result.value!r}\n")
                self._announce(f"Result: {result.value!r}")
            elif not result.output:
                self._announce("Done.")
            _history.add_entry("typescript", source, success=True)
        else:
            win.append_transcript(f"Error: {result.message}\n")
            if result.detail:
                win.append_transcript(f"Details:\n{result.detail}\n")
            self._announce(f"Error: {result.message}")
            _history.add_entry("typescript", source, success=False)
        win.set_status(f"Ready - TypeScript | {self.console_get_document_name() or 'no document'}")

    # ------------------------------------------------------------------
    # Internal helpers

    def _dt_consent_check(self) -> bool:
        """Show first-run safety warning; return True if user accepted."""
        if getattr(self, "_dev_console_consent_shown", False):
            return True
        wx = self._wx
        result = wx.MessageBox(
            _CONSENT_TEXT,
            "Developer Console",
            wx.OK | wx.CANCEL | wx.ICON_INFORMATION,
            self.frame,
        )
        if result == wx.OK:
            self._dev_console_consent_shown = True
            return True
        return False

    def _dt_make_namespace(self) -> dict[str, Any]:
        api = QuillScriptAPI(self)
        return {
            "q": api,
            "commands": api.commands,
            "a11y": api.a11y,
        }

    def _dt_snapshot_vars(self) -> dict[str, Any]:
        """Fresh snapshot variables refreshed on each execution."""
        from quill.core.scripting import DocumentSnapshot

        name = self.console_get_document_name()
        stats = self.console_document_stats()
        snap = DocumentSnapshot(
            name=name or "",
            path="",
            modified=False,
            line_count=stats.get("lines", 0),
            char_count=stats.get("chars", 0),
        )
        return {
            "doc": snap,
        }

    def _dt_start_ts_worker(self) -> None:
        ts = self._dt_ts_console()
        try:
            ts.start()
            self._wx.CallAfter(
                self._dt_window().set_status,
                f"Ready - TypeScript | {self.console_get_document_name() or 'no document'}",
            )
        except TypeScriptConsoleError as exc:
            self._wx.CallAfter(
                self._dt_window().append_transcript,
                f"Error: Could not start TypeScript worker: {exc}\n",
            )
            self._wx.CallAfter(self._dt_window().set_status, "TypeScript worker unavailable")

    def _dt_restart_ts_worker(self) -> None:
        ts = self._dt_ts_console()
        self._wx.CallAfter(self._dt_window().set_status, "Restarting TypeScript worker...")
        try:
            ts.restart()
            self._wx.CallAfter(
                self._dt_window().set_status,
                f"Ready - TypeScript | {self.console_get_document_name() or 'no document'}",
            )
        except TypeScriptConsoleError as exc:
            self._wx.CallAfter(
                self._dt_window().append_transcript,
                f"Error: {exc}\n",
            )

    def _dt_bind_devtools_menu(self) -> None:
        wx = self._wx
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_python_console(),
            id=self._id_dev_console_python,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_typescript_console(),
            id=self._id_dev_console_ts,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_diagnostic_summary(),
            id=self._id_dev_copy_diagnostic,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.restart_typescript_worker(),
            id=self._id_dev_restart_ts_worker,
        )

    def _dt_announce_output(self, output: str) -> None:
        """Announce stdout/stderr output from a console command.

        Short output (≤150 chars, ≤3 lines) is spoken verbatim so the user
        hears it without having to navigate the transcript.  Longer output
        gets a summary announcement — the full text is in the transcript.
        This matches the PRD §7.3 requirement: long output is summarized,
        not flood-spoken.
        """
        text = output.rstrip()
        if not text:
            return
        lines = text.splitlines()
        if len(lines) <= 3 and len(text) <= 150:
            self._announce(text)
        else:
            self._announce(
                f"{len(lines)} lines of output — review transcript with your screen reader."
            )

    def _mark_document_modified(self) -> None:
        """Signal that the active document has been changed from the console."""
        try:
            self._set_modified(True)
        except Exception:
            pass
