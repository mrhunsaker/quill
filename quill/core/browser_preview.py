from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from quill.core.navigation import previous_heading_start


@dataclass(frozen=True, slots=True)
class BrowserOption:
    value: str
    label: str
    executable_names: tuple[str, ...] = ()


_BROWSER_OPTIONS: tuple[BrowserOption, ...] = (
    BrowserOption("system", "System default browser"),
    BrowserOption("edge", "Microsoft Edge", ("msedge.exe", "edge.exe")),
    BrowserOption("chrome", "Google Chrome", ("chrome.exe", "chrome")),
    BrowserOption("firefox", "Mozilla Firefox", ("firefox.exe", "firefox")),
    BrowserOption("brave", "Brave", ("brave.exe", "brave-browser.exe", "brave-browser")),
    BrowserOption("opera", "Opera", ("opera.exe", "opera")),
)


def available_browser_options() -> list[BrowserOption]:
    options = [option for option in _BROWSER_OPTIONS if _is_available(option)]
    return options or [BrowserOption("system", "System default browser")]


def browser_choice_labels() -> list[str]:
    return [option.label for option in available_browser_options()]


def browser_choice_value_for_label(label: str) -> str:
    for option in available_browser_options():
        if option.label == label:
            return option.value
    return "system"


def browser_choice_label_for_value(value: str) -> str:
    for option in available_browser_options():
        if option.value == value:
            return option.label
    return "System default browser"


def normalize_browser_choice(value: str) -> str:
    for option in available_browser_options():
        if option.value == value:
            return value
    return "system"


def open_preview_url(url: str, browser_choice: str) -> None:
    choice = normalize_browser_choice(browser_choice)
    if choice == "system":
        webbrowser.open(url, new=2)
        return
    option = next((item for item in _BROWSER_OPTIONS if item.value == choice), None)
    if option is None:
        webbrowser.open(url, new=2)
        return
    executable = _resolve_browser_executable(option)
    if executable is None:
        webbrowser.open(url, new=2)
        return
    subprocess.Popen(
        [str(executable), url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=os.name != "nt",
    )


def preview_anchor_for_text(text: str, cursor: int, kind: str) -> str | None:
    if kind not in {"markdown", "html"}:
        return None
    start = previous_heading_start(text, cursor, kind)
    if start is None:
        start = 0
    heading = _extract_heading_title(text, start, kind)
    if not heading:
        return None
    return _slugify(heading)


def guess_preview_kind(path: Path | None, text: str) -> str:
    if path is not None:
        suffix = path.suffix.lower()
        if suffix in {".md", ".markdown", ".mdx"}:
            return "markdown"
        if suffix in {".html", ".htm", ".xhtml"}:
            return "html"
    stripped = text.lstrip()
    if stripped.startswith("# "):
        return "markdown"
    if re.search(r"^<h[1-6]\b", stripped, flags=re.IGNORECASE | re.MULTILINE):
        return "html"
    return "plain"


def render_preview_body(text: str, kind: str) -> str:
    """Render just the body fragment (no <html> wrapper) for a preview surface."""
    if kind == "markdown":
        return _render_markdown(text)
    if kind == "html":
        return _render_html(text)
    return f"<pre>{html.escape(text)}</pre>"


def render_preview_html(title: str, text: str, kind: str, start_anchor: str | None = None) -> str:
    body = render_preview_body(text, kind)
    anchor_script = ""
    if start_anchor:
        anchor_script = (
            "<script>"
            f'window.addEventListener("load", function(){{'
            f'var node = document.getElementById({start_anchor!r});'
            f'if (node) node.scrollIntoView();'
            "});"
            "</script>"
        )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        '<meta http-equiv="refresh" content="1">'
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{font-family:Segoe UI,Arial,sans-serif;line-height:1.6;margin:2rem;max-width:60rem;}"
        "pre,code{font-family:Consolas,Menlo,monospace;}"
        "pre{white-space:pre-wrap;word-break:break-word;background:#f5f5f5;padding:1rem;border-radius:8px;}"
        "blockquote{border-left:4px solid #ccc;padding-left:1rem;color:#444;}"
        "table{border-collapse:collapse;}"
        "th,td{border:1px solid #ccc;padding:0.4rem 0.6rem;}"
        "h1,h2,h3,h4,h5,h6{scroll-margin-top:1.5rem;}"
        "</style>"
        f"{anchor_script}</head><body>{body}</body></html>"
    )


def _is_available(option: BrowserOption) -> bool:
    if option.value == "system":
        return True
    return _resolve_browser_executable(option) is not None


def _resolve_browser_executable(option: BrowserOption) -> Path | None:
    for executable_name in option.executable_names:
        discovered = shutil.which(executable_name)
        if discovered:
            return Path(discovered)
    candidates = _browser_paths(option)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _browser_paths(option: BrowserOption) -> list[Path]:
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LocalAppData", "")
    candidates: dict[str, list[Path]] = {
        "edge": [
            Path(program_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(program_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ],
        "chrome": [
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "firefox": [
            Path(program_files) / "Mozilla Firefox" / "firefox.exe",
            Path(program_files_x86) / "Mozilla Firefox" / "firefox.exe",
        ],
        "brave": [
            Path(program_files) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(program_files_x86)
            / "BraveSoftware"
            / "Brave-Browser"
            / "Application"
            / "brave.exe",
        ],
        "opera": [
            Path(program_files) / "Opera" / "launcher.exe",
            Path(program_files_x86) / "Opera" / "launcher.exe",
        ],
    }
    return candidates.get(option.value, [])


def _extract_heading_title(text: str, start: int, kind: str) -> str | None:
    if kind == "markdown":
        line_end = text.find("\n", start)
        if line_end == -1:
            line_end = len(text)
        line = text[start:line_end].strip()
        match = re.match(r"#{1,6}\s+(.*)$", line)
        if match:
            return match.group(1).strip()
    if kind == "html":
        line_end = text.find("</h", start)
        if line_end == -1:
            return None
        candidate = text[start:line_end]
        candidate = re.sub(r"<[^>]+>", " ", candidate)
        candidate = html.unescape(" ".join(candidate.split()))
        return candidate or None
    return None


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "preview"


def _render_html(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("<"):
        return text
    return f"<pre>{html.escape(text)}</pre>"


def _render_markdown(text: str) -> str:
    lines = text.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_tag = ""
    code_lines: list[str] = []
    in_code = False
    code_language = ""

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{_render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_tag
        if list_items:
            blocks.append(f"<{list_tag}>" + "".join(list_items) + f"</{list_tag}>")
            list_items = []
            list_tag = ""

    for line in lines:
        stripped = line.rstrip()
        if in_code:
            if stripped.startswith("```"):
                blocks.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                in_code = False
                code_lines = []
                code_language = ""
                continue
            code_lines.append(line)
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            in_code = True
            code_language = stripped[3:].strip()
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            slug = _slugify(title)
            blocks.append(
                f'<h{level} id="{slug}">{_render_inline(title)}</h{level}>'
            )
            continue
        bullet = re.match(r"^(\s*)([-*+])\s+(.*)$", line)
        numbered = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if bullet or numbered:
            flush_paragraph()
            if not list_tag:
                list_tag = "ul" if bullet else "ol"
            list_items.append(f"<li>{_render_inline((bullet or numbered).group(3))}</li>")
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if list_tag:
            flush_list()
        paragraph.append(stripped)

    if in_code:
        blocks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    flush_paragraph()
    flush_list()
    return "\n".join(blocks) if blocks else f"<p>{html.escape(text) or '&nbsp;'}</p>"


def _render_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def file_url(path: Path) -> str:
    return path.as_uri()

