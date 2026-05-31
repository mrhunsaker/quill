"""Preview and HTML-dialog surfaces — thin adapters over the published
``wx-accessible-webview`` library.

Quill's accessible WebView stack was extracted into the standalone
``wx-accessible-webview`` package so any wxPython app can reuse it. These
adapters keep Quill's original call sites working while delegating all the
WebView / HTML / ARIA / JS work to the library:

  * :data:`HtmlMessageDialog` — the library's ``AccessibleHtmlDialog`` (same
    ``(parent, title, body_html, buttons)`` constructor and ``show_modal()->int``).
  * :data:`SidePreview` — the library's live preview pane (``update`` / ``control``).
  * :class:`MarkdownPreviewDialog` — a modal preview (single Close button,
    optional anchor scroll, links open in the browser) built on the library.

Markdown -> HTML rendering stays in :mod:`quill.core.browser_preview`; the
library is deliberately dependency-light and renders whatever HTML it's given.
"""

from __future__ import annotations

import json

from wx_accessible_webview import AccessibleHtmlDialog, SidePreview

# Quill's HtmlMessageDialog and the library's AccessibleHtmlDialog share the same
# constructor (parent, title, body_html, buttons) and the same show_modal()->int.
HtmlMessageDialog = AccessibleHtmlDialog

__all__ = ["HtmlMessageDialog", "SidePreview", "MarkdownPreviewDialog"]


class MarkdownPreviewDialog:
    """A modal preview of rendered Markdown/HTML, with a single Close button.

    ``start_anchor`` scrolls to a heading id on load; ``open_links_externally``
    opens ``http(s)`` links in the system browser. Built on the library's
    ``AccessibleHtmlDialog``.
    """

    def __init__(
        self,
        parent: object,
        title: str,
        body_html: str,
        start_anchor: str | None = None,
        open_links_externally: bool = False,
    ) -> None:
        import wx

        if start_anchor:
            # Inline scripts in a full-document load execute, so scroll to the
            # target heading once the page is ready.
            body_html += (
                "<script>window.addEventListener('load',function(){"
                f"var n=document.getElementById({json.dumps(start_anchor)});"
                "if(n){n.scrollIntoView();}});</script>"
            )
        self._dialog = AccessibleHtmlDialog(
            parent,
            title,
            body_html,
            [("Close", wx.ID_CANCEL)],
            size=(820, 760),
            open_links_externally=open_links_externally,
        )

    def show(self) -> None:
        self._dialog.show_modal()
