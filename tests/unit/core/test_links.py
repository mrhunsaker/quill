from pathlib import Path

from quill.core.links import build_link_text, find_link_at_cursor, infer_markup_kind


def test_infer_markup_kind() -> None:
    assert infer_markup_kind(Path("doc.md")) == "markdown"
    assert infer_markup_kind(Path("page.html")) == "html"
    assert infer_markup_kind(Path("config.yaml")) == "yaml"
    assert infer_markup_kind(Path("notes.txt")) == "plain"


def test_build_link_text_markdown() -> None:
    assert (
        build_link_text("markdown", "Docs", "https://example.com") == "[Docs](https://example.com)"
    )


def test_build_link_text_html() -> None:
    assert (
        build_link_text("html", "Docs", "https://example.com")
        == '<a href="https://example.com">Docs</a>'
    )


def test_build_link_text_plain() -> None:
    assert build_link_text("plain", "Docs", "https://example.com") == "Docs (https://example.com)"


def test_find_link_at_cursor_markdown() -> None:
    text = "See [docs](https://example.com/docs) now"
    cursor = text.index("https")
    assert find_link_at_cursor(text, cursor) == "https://example.com/docs"


def test_find_link_at_cursor_html() -> None:
    text = '<a href="https://example.com">Docs</a>'
    cursor = text.index("example")
    assert find_link_at_cursor(text, cursor) == "https://example.com"
