"""Markdown Helpers — a proof-of-concept Layer 2 Quillin entry module.

QUILL loads this module inside the sandboxed Quillin worker process and calls
``register(api)`` exactly once. The ``wrap_bold`` handler runs only when the
user invokes the ``ext.mdh.bold`` command (from the Format menu, the editor
context menu, or the Ctrl+Shift+B hotkey declared in ``manifest.json``).

The handler stays within the capabilities the manifest declares — ``editor.read``
to read the selection, ``editor.write`` to replace it, ``ui.announce`` to report
the outcome with NVDA/JAWS/Narrator parity, and ``ui.command`` because it is a
handler command. It never touches the filesystem, network, or clipboard, so it
triggers no consent prompt.
"""

from __future__ import annotations


def register(api):
    """Register every command handler this Quillin contributes."""

    def wrap_bold(ctx):
        selection = ctx.get_selection()
        if not selection:
            ctx.announce("Select some text first, then run Wrap Selection in Bold.")
            return
        ctx.replace_selection(f"**{selection}**")
        ctx.announce("Wrapped the selection in Markdown bold.")

    api.register_command("wrap_bold", wrap_bold)
