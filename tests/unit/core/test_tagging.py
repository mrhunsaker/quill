from quill.core.tagging import (
    HTML_TAG_CHOICES,
    MARKDOWN_TAG_CHOICES,
    build_html_code_block,
    build_html_insertion,
    build_html_table,
    build_markdown_code_block,
    build_markdown_insertion,
    build_markdown_table,
    parse_attribute_pairs,
    search_html_tag_choices,
    search_markdown_tag_choices,
)


def test_parse_attribute_pairs_supports_key_value_and_boolean() -> None:
    parsed = parse_attribute_pairs("class=note; id=main; disabled")
    assert parsed == {"class": "note", "id": "main", "disabled": ""}


def test_build_html_insertion_wraps_selected_text() -> None:
    result = build_html_insertion("strong", "hello", {"class": "callout"})
    assert result.inserted_text == '<strong class="callout">hello</strong>'
    assert result.caret_offset == len(result.inserted_text)


def test_build_html_insertion_for_void_tag() -> None:
    result = build_html_insertion("img", "", {"src": "image.png", "alt": "Sample"})
    assert result.inserted_text == '<img src="image.png" alt="Sample" />'


def test_build_markdown_link_uses_target() -> None:
    result = build_markdown_insertion("Link", "docs", "https://example.com")
    assert result.inserted_text == "[docs](https://example.com)"


def test_build_markdown_table_template() -> None:
    result = build_markdown_insertion("Table", "")
    assert "| Column 1 | Column 2 |" in result.inserted_text


def test_build_markdown_table_with_custom_dimensions() -> None:
    result = build_markdown_table(3, 4, include_header=True)
    assert result.inserted_text.count("| --- | --- | --- | --- |") == 1
    assert result.inserted_text.count("|  |  |  |  |") == 3


def test_build_html_table_with_header() -> None:
    result = build_html_table(2, 3, include_header=True)
    assert "<thead>" in result.inserted_text
    assert result.inserted_text.count("<th>") == 3
    assert result.inserted_text.count("<td></td>") == 6


def test_build_markdown_code_block_with_language_hint() -> None:
    result = build_markdown_code_block("print('hi')", language_hint="python")
    assert result.inserted_text.startswith("```python\n")


def test_build_html_code_block_with_language_hint() -> None:
    result = build_html_code_block("console.log('hi')", language_hint="javascript")
    assert '<code class="language-javascript">' in result.inserted_text


def test_build_markdown_bold_without_selection_inserts_pair() -> None:
    result = build_markdown_insertion("Bold", "")
    assert result.inserted_text == "****"
    assert result.caret_offset == 2


def test_build_markdown_italic_without_selection_inserts_pair() -> None:
    result = build_markdown_insertion("Italic", "")
    assert result.inserted_text == "**"
    assert result.caret_offset == 1


def test_markdown_choices_include_heading_levels_four_to_six() -> None:
    assert "Heading 4" in MARKDOWN_TAG_CHOICES
    assert "Heading 5" in MARKDOWN_TAG_CHOICES
    assert "Heading 6" in MARKDOWN_TAG_CHOICES


def test_html_choices_include_form_controls() -> None:
    for tag in ("form", "label", "input", "textarea", "select", "option", "button"):
        assert tag in HTML_TAG_CHOICES


def test_search_html_choices_matches_radio_to_input() -> None:
    results = search_html_tag_choices("radio")
    assert results
    assert results[0] == "input"


def test_search_html_choices_matches_heading_words() -> None:
    results = search_html_tag_choices("heading 1")
    assert results[0] == "h1"
    assert "h2" in search_html_tag_choices("heading two")


def test_search_markdown_choices_matches_heading_six() -> None:
    results = search_markdown_tag_choices("h6")
    assert "Heading 6" in results


def test_build_markdown_heading_six_without_selection() -> None:
    result = build_markdown_insertion("Heading 6", "")
    assert result.inserted_text == "###### "
