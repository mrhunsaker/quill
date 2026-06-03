from pathlib import Path

from quill.core.document import Document
from quill.io.rtf import (
    markdown_to_rtf,
    read_rtf_document,
    rtf_to_markdown,
    write_rtf_document,
)


def test_write_produces_valid_rtf_header() -> None:
    rtf = markdown_to_rtf("hello")
    assert rtf.startswith("{\\rtf1\\ansi")
    assert rtf.rstrip().endswith("}")
    assert "hello" in rtf


def test_read_simple_rtf() -> None:
    rtf = "{\\rtf1\\ansi{\\fonttbl{\\f0 Calibri;}}\\pard Plain text here\\par}"
    assert rtf_to_markdown(rtf) == "Plain text here"


def test_read_bold_and_italic() -> None:
    rtf = "{\\rtf1\\ansi\\pard This is {\\b bold} and {\\i italic}\\par}"
    assert rtf_to_markdown(rtf) == "This is **bold** and *italic*"


def test_round_trip_formatting() -> None:
    markdown = "\n".join([
        "# Heading One",
        "",
        "A paragraph with **bold** and *italic* words.",
        "- first item",
        "- second item",
        "See [QUILL](https://example.com/quill) for more.",
    ])
    restored = rtf_to_markdown(markdown_to_rtf(markdown))
    assert restored == markdown


def test_round_trip_heading_levels() -> None:
    markdown = "## Level Two\n### Level Three"
    assert rtf_to_markdown(markdown_to_rtf(markdown)) == markdown


def test_read_write_document(tmp_path: Path) -> None:
    source = tmp_path / "sample.rtf"
    write_rtf_document(Document(text="# Title\n**strong**"), source)
    document = read_rtf_document(source)
    assert document.text == "# Title\n**strong**"
    assert document.source_metadata["source_kind"] == "rtf"
    assert document.path == source
