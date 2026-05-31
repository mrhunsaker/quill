"""In-app Markdown / HTML preview, using the same accessible WebView stack as
the Ask Quill chat.

Two surfaces share one accessible page:

  * ``MarkdownPreviewDialog`` — a modal preview (View → Preview…).
  * ``SidePreview`` — a live pane shown to the right of the editor in a splitter
    (View → Preview Side by Side), re-rendered as the user types.

The rendered document goes into a ``wx.html2.WebView`` (Edge WebView2 on
Windows) so headings, lists, tables, and code render properly and the browser
engine's native accessibility carries the screen-reader experience. The page is
``lang``-tagged with readable + high-contrast / forced-colors CSS, headings keep
``scroll-margin``, focus moves into the view on open, and Escape is bridged out
of the native control (which swallows it) to close the modal.
"""

from __future__ import annotations

import html
import json
import re

_STYLES = """
  :root { color-scheme: light dark; }
  html, body { margin: 0; padding: 0; }
  body { font-family: system-ui, Segoe UI, Arial, sans-serif; font-size: 1.05rem;
         line-height: 1.6; padding: 16px 20px; max-width: 60rem; }
  h1, h2, h3, h4, h5, h6 { scroll-margin-top: 1.5rem; }
  pre { background: Field; padding: 10px; border-radius: 8px; overflow-x: auto;
        white-space: pre-wrap; word-break: break-word; }
  code { font-family: ui-monospace, Consolas, monospace; }
  blockquote { border-left: 4px solid GrayText; padding-left: 1rem; }
  table { border-collapse: collapse; }
  th, td { border: 1px solid GrayText; padding: 0.4rem 0.6rem; }
  a { color: LinkText; }
  :focus { outline: 2px solid Highlight; outline-offset: 2px; }
  @media (forced-colors: active) {
    th, td { border: 1px solid CanvasText; }
    blockquote { border-left-color: CanvasText; }
  }
"""


def _preview_page(
    title: str,
    body_html: str,
    *,
    start_anchor: str | None = None,
    escape_bridge: bool = False,
    return_bridge: bool = False,
) -> str:
    t = html.escape(title)
    scripts = []
    if escape_bridge:
        scripts.append(
            "document.addEventListener('keydown', function(e){"
            "if(e.key==='Escape'){e.preventDefault();"
            "if(window.quill&&window.quill.postMessage){"
            "window.quill.postMessage(JSON.stringify({type:'close'}));}}});"
        )
    if return_bridge:
        # Escape or F6 hands focus back to the editor (the native control eats
        # these, so we bridge them out to Python).
        scripts.append(
            "document.addEventListener('keydown', function(e){"
            "if(e.key==='Escape'||e.key==='F6'){e.preventDefault();"
            "if(window.quill&&window.quill.postMessage){"
            "window.quill.postMessage(JSON.stringify({type:'return'}));}}});"
        )
    if start_anchor:
        scripts.append(
            "window.addEventListener('load', function(){"
            f"var n=document.getElementById({json.dumps(start_anchor)});"
            "if(n){n.scrollIntoView();}});"
        )
    script_block = f"<script>{''.join(scripts)}</script>" if scripts else ""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{t}</title><style>{_STYLES}</style></head>"
        f'<body><main id="content" tabindex="-1">\n{body_html}\n</main>'
        f"{script_block}</body></html>"
    )


def _strip_tags(markup: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


class MarkdownPreviewDialog:
    def __init__(
        self,
        parent: object,
        title: str,
        body_html: str,
        start_anchor: str | None = None,
        open_links_externally: bool = False,
    ) -> None:
        import wx

        self._wx = wx
        self._fallback = None
        self.view = None
        self._loaded = False

        self.dialog = wx.Dialog(
            parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.dialog.SetSize((820, 760))
        outer = wx.BoxSizer(wx.VERTICAL)

        try:
            import wx.html2 as webview

            self.view = webview.WebView.New(self.dialog)
            self.view.SetName(title)
            try:
                self.view.AddScriptMessageHandler("quill")
                self.view.Bind(webview.EVT_WEBVIEW_SCRIPT_MESSAGE_RECEIVED, self._on_script_message)
            except Exception:  # noqa: BLE001
                pass
            if open_links_externally:
                # Guarded so it can't interfere with the initial SetPage render:
                # only act on user link clicks after the page has loaded.
                self.view.Bind(
                    webview.EVT_WEBVIEW_LOADED, lambda _e: setattr(self, "_loaded", True)
                )
                self.view.Bind(webview.EVT_WEBVIEW_NAVIGATING, self._on_navigating)
            self.view.SetPage(
                _preview_page(title, body_html, start_anchor=start_anchor, escape_bridge=True), ""
            )
            outer.Add(self.view, 1, wx.EXPAND)
        except Exception:  # noqa: BLE001
            self.view = None
            self._fallback = wx.TextCtrl(
                self.dialog, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
            )
            self._fallback.SetName(title)
            self._fallback.SetValue(_strip_tags(body_html))
            outer.Add(self._fallback, 1, wx.EXPAND | wx.ALL, 8)

        footer = wx.BoxSizer(wx.HORIZONTAL)
        footer.AddStretchSpacer()
        footer.Add(wx.Button(self.dialog, wx.ID_CANCEL, label="Close"), 0)
        outer.Add(footer, 0, wx.EXPAND | wx.ALL, 10)
        self.dialog.SetSizer(outer)
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

    def _on_navigating(self, event: object) -> None:
        url = event.GetURL() or ""
        # Only divert real link clicks after load; never the initial page load.
        if self._loaded and url.startswith(("http://", "https://")):
            event.Veto()
            import webbrowser

            webbrowser.open(url)

    def _on_char_hook(self, event: object) -> None:
        if event.GetKeyCode() == self._wx.WXK_ESCAPE:
            self._close()
            return
        event.Skip()

    def _close(self) -> None:
        self.dialog.EndModal(self._wx.ID_CANCEL)

    def _on_script_message(self, event: object) -> None:
        try:
            data = json.loads(event.GetString())
        except Exception:  # noqa: BLE001
            return
        if data.get("type") == "close":
            self._close()

    def _focus(self) -> None:
        if self.view is not None:
            self.view.SetFocus()
        elif self._fallback is not None:
            self._fallback.SetFocus()

    def show(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self._wx.CallAfter(self._focus)
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()


class SidePreview:
    """A live preview pane (right side of the editor splitter).

    Created lazily when the user turns on side-by-side preview. ``update()``
    replaces the rendered body in place (via ``innerHTML``) so scroll position
    is preserved while typing, rather than reloading the whole page each stroke.
    Falls back to a read-only text control where no WebView backend exists.
    """

    def __init__(self, parent: object, title: str = "Preview", on_return=None) -> None:
        import wx

        self._wx = wx
        self.view = None
        self._fallback = None
        self._ready = False
        self._pending: str | None = None
        self._on_return = on_return
        try:
            import wx.html2 as webview

            self.view = webview.WebView.New(parent)
            self.view.SetName(title)
            try:
                self.view.AddScriptMessageHandler("quill")
                self.view.Bind(webview.EVT_WEBVIEW_SCRIPT_MESSAGE_RECEIVED, self._on_script_message)
            except Exception:  # noqa: BLE001
                pass
            self.view.Bind(webview.EVT_WEBVIEW_LOADED, self._on_loaded)
            self.view.SetPage(_preview_page(title, "", return_bridge=True), "")
        except Exception:  # noqa: BLE001
            self.view = None
            self._fallback = wx.TextCtrl(
                parent, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
            )
            self._fallback.SetName(title)

    def _on_script_message(self, event: object) -> None:
        try:
            data = json.loads(event.GetString())
        except Exception:  # noqa: BLE001
            return
        if data.get("type") == "return" and self._on_return is not None:
            self._on_return()

    @property
    def control(self):
        return self.view if self.view is not None else self._fallback

    def _on_loaded(self, _event: object) -> None:
        self._ready = True
        if self._pending is not None:
            body, self._pending = self._pending, None
            self._apply(body)

    def update(self, body_html: str) -> None:
        if self._fallback is not None:
            self._fallback.SetValue(_strip_tags(body_html))
            return
        if self._ready:
            self._apply(body_html)
        else:
            self._pending = body_html

    def _apply(self, body_html: str) -> None:
        script = (
            "var c=document.getElementById('content');"
            f"if(c){{c.innerHTML={json.dumps(body_html)};}}"
        )
        try:
            self.view.RunScript(script)
        except Exception:  # noqa: BLE001
            pass


class HtmlMessageDialog:
    """A modal message dialog whose body renders as HTML in a WebView (same
    surface as the preview/chat), with a configurable row of buttons.

    ``buttons`` is a list of ``(label, return_id)``. ``show_modal()`` returns the
    chosen id (or wx.ID_CANCEL on Escape / close). Links open in the browser.
    """

    def __init__(self, parent: object, title: str, body_html: str, buttons) -> None:
        import wx

        self._wx = wx
        self._result = wx.ID_CANCEL
        self._loaded = False
        self._fallback = None
        self.view = None

        self.dialog = wx.Dialog(
            parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.dialog.SetName(title)
        self.dialog.SetSize((640, 560))
        outer = wx.BoxSizer(wx.VERTICAL)

        try:
            import wx.html2 as webview

            self.view = webview.WebView.New(self.dialog)
            self.view.SetName(title)
            self.view.Bind(webview.EVT_WEBVIEW_LOADED, lambda _e: setattr(self, "_loaded", True))
            self.view.Bind(webview.EVT_WEBVIEW_NAVIGATING, self._on_navigating)
            # Escape inside the native WebView is swallowed; bridge it out to close.
            try:
                self.view.AddScriptMessageHandler("quill")
                self.view.Bind(
                    webview.EVT_WEBVIEW_SCRIPT_MESSAGE_RECEIVED,
                    lambda _e: self._end(self._wx.ID_CANCEL),
                )
            except Exception:  # noqa: BLE001
                pass
            self.view.SetPage(_preview_page(title, body_html, escape_bridge=True), "")
            outer.Add(self.view, 1, wx.EXPAND)
        except Exception:  # noqa: BLE001
            self.view = None
            self._fallback = wx.TextCtrl(
                self.dialog, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
            )
            self._fallback.SetName(title)
            self._fallback.SetValue(_strip_tags(body_html))
            outer.Add(self._fallback, 1, wx.EXPAND | wx.ALL, 8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.AddStretchSpacer()
        for index, (label, return_id) in enumerate(buttons):
            button = wx.Button(self.dialog, return_id, label=label)
            if index == len(buttons) - 1:
                button.SetDefault()
            button.Bind(wx.EVT_BUTTON, lambda _e, r=return_id: self._end(r))
            row.Add(button, 0, wx.LEFT, 8)
        outer.Add(row, 0, wx.EXPAND | wx.ALL, 12)

        self.dialog.SetSizer(outer)
        self.dialog.Bind(
            wx.EVT_CHAR_HOOK,
            lambda e: self._end(wx.ID_CANCEL) if e.GetKeyCode() == wx.WXK_ESCAPE else e.Skip(),
        )

    def _on_navigating(self, event: object) -> None:
        url = event.GetURL() or ""
        if self._loaded and url.startswith(("http://", "https://")):
            event.Veto()
            import webbrowser

            webbrowser.open(url)

    def _end(self, return_id: int) -> None:
        self._result = return_id
        self.dialog.EndModal(return_id)

    def show_modal(self) -> int:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()
        return self._result
