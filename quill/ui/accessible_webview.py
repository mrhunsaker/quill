"""Ask Quill's accessible chat surface — a thin adapter over the published
``wx-accessible-webview`` library.

The WebView/ARIA/JS chat stack Quill pioneered lives in
``wx_accessible_webview.AccessibleChatView`` now. This adapter keeps Quill's
original API — ``intro`` and :meth:`append_message` accept **Markdown** (rendered
here via :func:`quill.core.browser_preview._render_markdown`), and ``set_status``
matches Quill's existing call sites — while delegating everything else to the
library.
"""

from __future__ import annotations

from wx_accessible_webview import AccessibleChatView

from quill.core.browser_preview import _render_markdown


class AccessibleWebView(AccessibleChatView):
    """Quill's chat surface: Markdown in, accessible WebView out."""

    def __init__(
        self,
        parent: object,
        title: str = "Conversation",
        intro: tuple | None = None,
        suggestions: tuple[str, ...] = (),
        on_send=None,
        on_close=None,
    ) -> None:
        rendered_intro = None
        if intro is not None:
            rendered_intro = (intro[0], _render_markdown(intro[1] or ""))
        super().__init__(
            parent,
            title=title,
            intro=rendered_intro,
            suggestions=tuple(suggestions),
            placeholder="Ask Quill to write, edit, or run something…",
            composer_label="Your message to Quill",
            on_send=on_send,
            on_close=on_close,
        )

    def append_message(self, speaker: str, markdown_text: str) -> None:
        """Append a turn; ``markdown_text`` is rendered to HTML before display."""
        super().append_message(speaker, _render_markdown(markdown_text or ""))

    def set_status(self, text: str) -> None:
        """Announce transient status (Quill's name for the library's ``status``)."""
        self.status(text)
