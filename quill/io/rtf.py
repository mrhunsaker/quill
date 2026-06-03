"""RTF round-trip through the io layer (EDS-21).

Promotes RTF from the previous lossy extract-only path to a real ``io/*`` format
that reads RTF formatting into QUILL's Markdown-style internal markup and writes
that markup back out to valid RTF, following the
``read(path) -> Document`` / ``write(doc, path)`` contract.

The mapping is intentionally line-oriented (one RTF paragraph per source line) so
that the plain-text-first editor surface is unchanged. Supported constructs that
survive a round trip: headings, **bold**, *italic*, bullet lists, and links.
"""

from __future__ import annotations

import re
from pathlib import Path

from quill.core.document import Document

__all__ = [
    "markdown_to_rtf",
    "read_rtf_document",
    "rtf_to_markdown",
    "write_rtf_document",
]

_RTF_ENCODING = "cp1252"

# Private sentinels used to carry a parsed hyperlink through the tokenizer.
_LINK_OPEN = "\x01"
_LINK_SEP = "\x02"
_LINK_CLOSE = "\x03"

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^[-*]\s+(.*)$")
_LINK_MD_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_FIELD_RE = re.compile(
    r'\{\\field\{\\\*\\fldinst\s*HYPERLINK\s*"([^"]*)"\s*\}\{\\fldrslt\s*(.*?)\}\}',
    re.DOTALL,
)
_SENTINEL_RE = re.compile(f"{_LINK_OPEN}(.*?){_LINK_SEP}(.*?){_LINK_CLOSE}", re.DOTALL)

_SKIP_DESTINATIONS = {
    "fonttbl",
    "colortbl",
    "stylesheet",
    "info",
    "pntext",
    "pntxta",
    "pntxtb",
    "listtable",
    "listoverridetable",
    "generator",
    "themedata",
    "colorschememapping",
    "latentstyles",
    "datastore",
    "mmath",
    "header",
    "footer",
}


# --------------------------------------------------------------------------- #
# Markdown -> RTF
# --------------------------------------------------------------------------- #
def _escape_rtf_text(text: str) -> str:
    out: list[str] = []
    for char in text:
        code = ord(char)
        if char in "\\{}":
            out.append("\\" + char)
        elif code < 128:
            out.append(char)
        else:
            out.append(f"\\u{code}?")
    return "".join(out)


def _inline_to_rtf(text: str) -> str:
    result: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        link = _LINK_MD_RE.match(text, index)
        if link:
            url = _escape_rtf_text(link.group(2))
            label = _inline_to_rtf(link.group(1))
            result.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{url}"}}{{\\fldrslt {label}}}}}')
            index = link.end()
            continue
        if text.startswith("**", index):
            close = text.find("**", index + 2)
            if close != -1:
                result.append("{\\b " + _inline_to_rtf(text[index + 2 : close]) + "}")
                index = close + 2
                continue
        if text[index] == "*":
            close = text.find("*", index + 1)
            if close != -1:
                result.append("{\\i " + _inline_to_rtf(text[index + 1 : close]) + "}")
                index = close + 1
                continue
        result.append(_escape_rtf_text(text[index]))
        index += 1
    return "".join(result)


def markdown_to_rtf(markdown: str) -> str:
    """Render QUILL Markdown-style markup to a valid RTF document string."""
    body: list[str] = []
    for line in markdown.split("\n"):
        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            content = _inline_to_rtf(heading.group(2))
            body.append(f"\\pard\\outlinelevel{level - 1}\\b {content}\\b0\\par")
            continue
        item = _LIST_RE.match(line)
        if item:
            content = _inline_to_rtf(item.group(1))
            body.append(f"\\pard\\fi-360\\li720{{\\pntext\\bullet\\tab}}{content}\\par")
            continue
        body.append(f"\\pard {_inline_to_rtf(line)}\\par")
    header = "{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Calibri;}}\n"
    return header + "\n".join(body) + "\n}"


# --------------------------------------------------------------------------- #
# RTF -> Markdown
# --------------------------------------------------------------------------- #
def _strip_rtf_inline(fragment: str) -> str:
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", fragment)
    text = text.replace("{", "").replace("}", "")
    return text.strip()


def _tokenize(rtf: str) -> list[tuple[str, object, object]]:
    tokens: list[tuple[str, object, object]] = []
    index = 0
    length = len(rtf)
    while index < length:
        char = rtf[index]
        if char == "\\":
            nxt = rtf[index + 1] if index + 1 < length else ""
            if nxt.isalpha():
                end = index + 1
                while end < length and rtf[end].isalpha():
                    end += 1
                word = rtf[index + 1 : end]
                param: int | None = None
                if end < length and (rtf[end] == "-" or rtf[end].isdigit()):
                    start = end
                    if rtf[end] == "-":
                        end += 1
                    while end < length and rtf[end].isdigit():
                        end += 1
                    param = int(rtf[start:end])
                if end < length and rtf[end] == " ":
                    end += 1
                tokens.append(("word", word, param))
                index = end
            elif nxt == "'":
                hex_digits = rtf[index + 2 : index + 4]
                try:
                    tokens.append(("char", chr(int(hex_digits, 16)), None))
                except ValueError:
                    pass
                index += 4
            else:
                tokens.append(("symbol", nxt, None))
                index += 2
        elif char == "{":
            tokens.append(("group_open", None, None))
            index += 1
        elif char == "}":
            tokens.append(("group_close", None, None))
            index += 1
        elif char in "\r\n":
            index += 1
        else:
            tokens.append(("char", char, None))
            index += 1
    return tokens


class _RtfReader:
    def __init__(self, rtf: str) -> None:
        self._tokens = _tokenize(rtf)
        self._paragraphs: list[str] = []
        self._parts: list[str] = []
        self._bold = False
        self._italic = False
        self._emitted_bold = False
        self._emitted_italic = False
        self._outline: int | None = None
        self._is_list = False
        self._stack: list[tuple[bool, bool]] = []
        self._depth = 0
        self._skip_to_depth: int | None = None
        self._skip_chars = 0

    def _sync(self) -> None:
        if self._bold != self._emitted_bold:
            self._parts.append("**")
            self._emitted_bold = self._bold
        if self._italic != self._emitted_italic:
            self._parts.append("*")
            self._emitted_italic = self._italic

    def _append_text(self, text: str) -> None:
        self._sync()
        self._parts.append(text)

    def _flush_paragraph(self) -> None:
        self._bold = False
        self._italic = False
        self._sync()
        content = "".join(self._parts)
        if self._outline is not None:
            prefix = "#" * (self._outline + 1) + " "
            content = prefix + content
        elif self._is_list:
            content = "- " + content
        self._paragraphs.append(content)
        self._parts = []
        self._outline = None
        self._is_list = False

    def parse(self) -> str:
        for kind, value, param in self._tokens:
            if kind == "group_open":
                self._depth += 1
                self._stack.append((self._bold, self._italic))
                continue
            if kind == "group_close":
                if self._stack:
                    self._bold, self._italic = self._stack.pop()
                self._depth -= 1
                if self._skip_to_depth is not None and self._depth < self._skip_to_depth:
                    self._skip_to_depth = None
                continue
            if self._skip_to_depth is not None:
                continue
            if kind == "symbol":
                if value == "*":
                    self._skip_to_depth = self._depth
                continue
            if kind == "word":
                self._handle_word(str(value), param if isinstance(param, int) else None)
                continue
            if kind == "char":
                if self._skip_chars > 0:
                    self._skip_chars -= 1
                    continue
                self._append_text(str(value))
        if self._parts:
            # Trailing content with no final \par still becomes a paragraph.
            self._flush_paragraph()
        result = "\n".join(self._paragraphs)
        return _SENTINEL_RE.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", result)

    def _handle_word(self, word: str, param: int | None) -> None:
        if word in _SKIP_DESTINATIONS:
            self._skip_to_depth = self._depth
            return
        if word == "par":
            self._flush_paragraph()
        elif word == "pard":
            self._outline = None
            self._is_list = False
        elif word == "b":
            # Headings carry visual \b in RTF but are conveyed by the "#" prefix
            # in Markdown, so don't also emit bold markers inside a heading.
            self._bold = param != 0 and self._outline is None
        elif word == "i":
            self._italic = param != 0
        elif word == "outlinelevel":
            self._outline = param if param is not None else 0
        elif word == "li":
            if param:
                self._is_list = True
        elif word == "tab":
            self._append_text("\t")
        elif word == "u" and param is not None:
            code = param + 65536 if param < 0 else param
            self._append_text(chr(code))
            self._skip_chars = 1


def rtf_to_markdown(rtf: str) -> str:
    """Convert an RTF document string to QUILL Markdown-style markup."""
    pre = _FIELD_RE.sub(
        lambda m: (
            f"{_LINK_OPEN}{m.group(1)}{_LINK_SEP}{_strip_rtf_inline(m.group(2))}{_LINK_CLOSE}"
        ),
        rtf,
    )
    return _RtfReader(pre).parse()


# --------------------------------------------------------------------------- #
# io contract
# --------------------------------------------------------------------------- #
def read_rtf_document(path: Path) -> Document:
    """Read an RTF file into a Document whose text is Markdown-style markup."""
    raw = path.read_text(encoding=_RTF_ENCODING, errors="replace")
    return Document(
        text=rtf_to_markdown(raw),
        path=path,
        modified=False,
        encoding="utf-8",
        line_ending="\n",
        source_metadata={"source_kind": "rtf", "engine": "rtf", "quality_score": 100},
    )


def write_rtf_document(document: Document, path: Path | None = None) -> Path:
    """Write a Document's Markdown-style markup out as valid RTF."""
    target_path = path or document.path
    if target_path is None:
        raise ValueError("A path is required to save this document.")
    rtf = markdown_to_rtf(document.text)
    target_path.write_text(rtf, encoding=_RTF_ENCODING, errors="replace")
    document.mark_saved(target_path)
    return target_path
