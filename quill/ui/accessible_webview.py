"""An accessibility-focused chat surface built on wx.html2.WebView.

wx.html2.WebView is a factory-created native control (Edge WebView2 on Windows,
WKWebView on macOS, WebKitGTK on Linux), so it can't be meaningfully
subclassed — but its accessibility is driven by the HTML it renders. This
wrapper renders the *whole* Ask Quill chat as one semantic, screen-reader-
friendly document: transcript, suggestions, and the message edit field all live
inside the page.

  * an ARIA live region (``role="log" aria-live="polite"``) so new messages are
    announced automatically,
  * an assertive ``role="status"`` region for transient state
    ("Quill is responding…"),
  * each message is an ``<article>`` with a heading (speaker) for heading nav,
  * the message edit field is a labelled ``<textarea>`` inside the page; Enter
    sends, Shift+Enter inserts a newline,
  * suggestion buttons that hide themselves after the first message (like
    Apple Intelligence) so they never sit in the way of the conversation,
  * ``lang``, viewport, readable + high-contrast/forced-colors CSS.

Submissions are posted from JavaScript back to Python via a script-message
bridge (``window.quill.postMessage``) so the in-page edit field drives the
on-device assistant directly. The first message can be baked straight into the
page so there is no "empty then rendered" flash on open.
"""
from __future__ import annotations

import html
import json


class AccessibleWebView:
    def __init__(
        self,
        parent: object,
        title: str = "Conversation",
        intro: tuple | None = None,
        suggestions: tuple[str, ...] = (),
        on_send=None,
        on_close=None,
    ) -> None:
        import wx
        import wx.html2 as webview

        self._wx = wx
        self.view = webview.WebView.New(parent)
        self.view.SetName(title)
        self._title = title
        self._ready = False
        self._pending: list[tuple[str, object]] = []
        self._on_send = on_send
        self._on_close = on_close
        self._suggestions = list(suggestions)
        self._want_focus = False

        intro_html = ""
        if intro is not None:
            intro_html = self._article_html(intro[0], intro[1])

        # JS -> Python bridge: window.quill.postMessage(JSON) lands here.
        try:
            self.view.AddScriptMessageHandler("quill")
            self.view.Bind(
                webview.EVT_WEBVIEW_SCRIPT_MESSAGE_RECEIVED, self._on_script_message
            )
        except Exception:  # noqa: BLE001
            # Older/unsupported backend — the in-page composer won't post back,
            # but the transcript still renders. Caller's wx fallback covers input.
            pass

        self.view.Bind(webview.EVT_WEBVIEW_LOADED, self._on_loaded)
        self.view.SetPage(self._skeleton(intro_html), "")

    @property
    def control(self):
        return self.view

    # -- rendering ---------------------------------------------------------

    def _article_html(self, speaker: str, markdown_text: str) -> str:
        from quill.core.browser_preview import _render_markdown

        body = _render_markdown(markdown_text or "")
        css_class = "you" if speaker.lower().startswith("you") else "quill"
        return (
            f'<article class="{css_class}" aria-label="{html.escape(speaker)} message">'
            f"<h2>{html.escape(speaker)}</h2>{body}</article>"
        )

    def _suggestions_html(self) -> str:
        if not self._suggestions:
            return ""
        buttons = "".join(
            f'<button type="button" class="suggestion" data-prompt="{html.escape(s)}">'
            f"{html.escape(s)}</button>"
            for s in self._suggestions
        )
        return (
            '<div id="suggestions" role="group" aria-label="Suggestions">'
            f"{buttons}</div>"
        )

    def _skeleton(self, intro_html: str = "") -> str:
        title = html.escape(self._title)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; }}
  html, body {{ margin: 0; padding: 0; height: 100%; }}
  body {{ font-family: system-ui, sans-serif; font-size: 1.05rem; line-height: 1.5;
          display: flex; flex-direction: column; height: 100vh; }}
  main#log {{ display: block; flex: 1 1 auto; overflow-y: auto; padding: 12px; }}
  article {{ margin: 0 0 14px 0; padding: 10px 12px; border-radius: 8px;
             border: 1px solid GrayText; }}
  article.you {{ background: Field; }}
  article h2 {{ font-size: 0.95rem; margin: 0 0 6px 0; }}
  article p {{ margin: 0.4em 0; }}
  pre {{ background: Field; padding: 8px; overflow-x: auto; }}
  code {{ font-family: ui-monospace, monospace; }}
  a {{ color: LinkText; }}
  :focus {{ outline: 2px solid Highlight; outline-offset: 2px; }}
  #suggestions {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 0 12px 8px; }}
  #suggestions[hidden] {{ display: none; }}
  button.suggestion {{ font-size: 0.95rem; padding: 4px 10px; border-radius: 14px;
                       border: 1px solid GrayText; background: ButtonFace;
                       color: ButtonText; cursor: pointer; }}
  form#composer {{ display: flex; gap: 8px; align-items: flex-end;
                   padding: 8px 12px 12px; border-top: 1px solid GrayText; }}
  form#composer label {{ position: absolute; width: 1px; height: 1px; overflow: hidden;
                         clip: rect(0 0 0 0); white-space: nowrap; }}
  #msg {{ flex: 1 1 auto; font: inherit; padding: 8px; resize: vertical;
          min-height: 2.4em; }}
  #send {{ font: inherit; padding: 8px 16px; }}
  .visually-hidden {{ position: absolute; width: 1px; height: 1px; overflow: hidden;
                      clip: rect(0 0 0 0); white-space: nowrap; }}
  @media (forced-colors: active) {{ article {{ border: 1px solid CanvasText; }} }}
</style>
</head>
<body>
<div id="status" role="status" aria-live="assertive" class="visually-hidden"></div>
<main id="log" role="log" aria-live="polite" aria-label="{title}" tabindex="0">
{intro_html}
</main>
{self._suggestions_html()}
<form id="composer" autocomplete="off">
  <label for="msg">Your message to Quill</label>
  <textarea id="msg" rows="2" placeholder="Ask Quill to write, edit, or run something…"
            aria-label="Your message to Quill"></textarea>
  <button type="submit" id="send">Send</button>
</form>
<script>
  (function() {{
    var log = document.getElementById('log');
    var sug = document.getElementById('suggestions');
    var form = document.getElementById('composer');
    var msg = document.getElementById('msg');
    function send(text) {{
      text = (text || '').trim();
      if (!text) return;
      if (window.quill && window.quill.postMessage) {{
        window.quill.postMessage(JSON.stringify({{type: 'send', text: text}}));
      }}
    }}
    form.addEventListener('submit', function(e) {{
      e.preventDefault();
      var t = msg.value;
      msg.value = '';
      send(t);
    }});
    msg.addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); form.requestSubmit(); }}
    }});
    // Escape closes the chat (the native WebView swallows it, so bridge it out).
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') {{
        e.preventDefault();
        if (window.quill && window.quill.postMessage) {{
          window.quill.postMessage(JSON.stringify({{type: 'close'}}));
        }}
      }}
    }});
    if (sug) {{
      sug.addEventListener('click', function(e) {{
        var b = e.target.closest('button');
        if (b) {{ send(b.getAttribute('data-prompt') || b.textContent); }}
      }});
    }}
    window.quillApi = {{
      append: function(itemHtml) {{
        var tmp = document.createElement('div');
        tmp.innerHTML = itemHtml;
        while (tmp.firstChild) {{ log.appendChild(tmp.firstChild); }}
        log.scrollTop = log.scrollHeight;
      }},
      status: function(s) {{
        var el = document.getElementById('status');
        if (el) {{ el.textContent = s; }}
      }},
      hideSuggestions: function() {{ if (sug) {{ sug.hidden = true; }} }},
      focusInput: function() {{ msg.focus(); }},
      setEnabled: function(on) {{
        msg.disabled = !on;
        document.getElementById('send').disabled = !on;
        if (sug) {{
          var bs = sug.querySelectorAll('button');
          for (var i = 0; i < bs.length; i++) {{ bs[i].disabled = !on; }}
        }}
      }}
    }};
  }})();
</script>
</body>
</html>"""

    # -- bridge ------------------------------------------------------------

    def _on_script_message(self, event: object) -> None:
        try:
            data = json.loads(event.GetString())
        except Exception:  # noqa: BLE001
            return
        kind = data.get("type")
        if kind == "send" and self._on_send is not None:
            text = str(data.get("text", "")).strip()
            if text:
                self._on_send(text)
        elif kind == "close" and self._on_close is not None:
            self._on_close()

    def _on_loaded(self, _event: object) -> None:
        self._ready = True
        pending, self._pending = self._pending, []
        for kind, payload in pending:
            self._dispatch(kind, payload)
        if self._want_focus:
            self._want_focus = False
            self.view.SetFocus()
            self._run("window.quillApi.focusInput();")

    def _dispatch(self, kind: str, payload: object) -> None:
        if kind == "append":
            self._run(f"window.quillApi.append({json.dumps(payload)});")
        elif kind == "status":
            self._run(f"window.quillApi.status({json.dumps(payload)});")
        elif kind == "hide":
            self._run("window.quillApi.hideSuggestions();")
        elif kind == "enable":
            self._run(f"window.quillApi.setEnabled({'true' if payload else 'false'});")

    # -- public API --------------------------------------------------------

    def append_message(self, speaker: str, markdown_text: str) -> None:
        article = self._article_html(speaker, markdown_text)
        if self._ready:
            self._dispatch("append", article)
        else:
            self._pending.append(("append", article))

    def set_status(self, text: str) -> None:
        """Update the assertive status region (announced by screen readers)."""
        if self._ready:
            self._dispatch("status", text)

    def hide_suggestions(self) -> None:
        if self._ready:
            self._dispatch("hide", None)
        else:
            self._pending.append(("hide", None))

    def set_input_enabled(self, enabled: bool) -> None:
        if self._ready:
            self._dispatch("enable", enabled)
        else:
            self._pending.append(("enable", enabled))

    def focus(self) -> None:
        """Move focus into the in-page message edit field."""
        self.view.SetFocus()
        if self._ready:
            self._run("window.quillApi.focusInput();")
        else:
            self._want_focus = True

    def _run(self, script: str) -> None:
        try:
            self.view.RunScript(script)
        except Exception:  # noqa: BLE001
            pass

    def clear(self) -> None:
        self._ready = False
        self._pending = []
        self.view.SetPage(self._skeleton(), "")
