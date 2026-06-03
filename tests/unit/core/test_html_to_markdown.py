from quill.core.html_to_markdown import extract_cf_html_fragment, html_to_markdown


def test_headings_and_paragraph() -> None:
    md = html_to_markdown("<h1>Title</h1><p>Hello world</p>")
    assert "# Title" in md
    assert "Hello world" in md


def test_bold_and_italic() -> None:
    md = html_to_markdown("<p>This is <strong>bold</strong> and <em>italic</em>.</p>")
    assert "**bold**" in md
    assert "*italic*" in md


def test_link() -> None:
    md = html_to_markdown('<p>See <a href="https://example.org">the site</a>.</p>')
    assert "[the site](https://example.org)" in md


def test_unordered_list() -> None:
    md = html_to_markdown("<ul><li>One</li><li>Two</li></ul>")
    assert "- One" in md
    assert "- Two" in md


def test_ordered_list_numbers() -> None:
    md = html_to_markdown("<ol><li>First</li><li>Second</li></ol>")
    assert "1. First" in md
    assert "2. Second" in md


def test_inline_code_and_block() -> None:
    md = html_to_markdown("<p>Use <code>x = 1</code></p><pre>line1\nline2</pre>")
    assert "`x = 1`" in md
    assert "```" in md
    assert "line1" in md


def test_blockquote() -> None:
    md = html_to_markdown("<blockquote>quoted</blockquote>")
    assert "> " in md
    assert "quoted" in md


def test_scripts_are_dropped() -> None:
    md = html_to_markdown("<p>keep</p><script>alert(1)</script>")
    assert "keep" in md
    assert "alert" not in md


def test_empty_html_returns_empty() -> None:
    assert html_to_markdown("   ") == ""
    assert html_to_markdown("<div></div>") == ""


def test_unknown_tags_keep_text() -> None:
    md = html_to_markdown("<span class='x'>plain text</span>")
    assert "plain text" in md


def test_extract_cf_html_fragment_with_markers() -> None:
    payload = (
        "Version:0.9\r\nStartHTML:00000097\r\n"
        "<html><body><!--StartFragment--><p>Body</p><!--EndFragment--></body></html>"
    )
    fragment = extract_cf_html_fragment(payload)
    assert fragment == "<p>Body</p>"


def test_extract_cf_html_fragment_passthrough() -> None:
    assert extract_cf_html_fragment("<p>plain</p>") == "<p>plain</p>"


def test_cf_html_payload_end_to_end() -> None:
    payload = (
        "Version:0.9\r\n<html><body><!--StartFragment--><h2>Hi</h2><!--EndFragment--></body></html>"
    )
    md = html_to_markdown(payload)
    assert "## Hi" in md
