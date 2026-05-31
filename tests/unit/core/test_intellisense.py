from __future__ import annotations

from quill.core.intellisense import build_intellisense_suggestions, extract_intellisense_context


def test_intellisense_context_detects_html_fragment() -> None:
    context = extract_intellisense_context("<di", 3)

    assert context is not None
    assert context.mode == "html"
    assert context.fragment == "di"
    assert context.replacement_start == 1


def test_intellisense_suggests_document_words() -> None:
    context, suggestions = build_intellisense_suggestions(
        "worl",
        4,
        {"world"},
        limit=4,
    )

    assert context is not None
    assert suggestions
    assert suggestions[0].kind == "word"
    assert any(item.inserted_text == "world" for item in suggestions)


def test_intellisense_suggests_html_and_markdown_tags() -> None:
    _, html_suggestions = build_intellisense_suggestions("<di", 3, set(), limit=4)
    _, markdown_suggestions = build_intellisense_suggestions("heading", 7, set(), limit=4)

    assert any(item.kind == "html" and item.inserted_text == "div>" for item in html_suggestions)
    assert any(item.kind == "markdown" and item.inserted_text.startswith("#") for item in markdown_suggestions)
