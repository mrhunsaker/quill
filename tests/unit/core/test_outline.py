from __future__ import annotations

from quill.core.outline import extract_outline_entries


def test_extract_outline_entries_for_markdown() -> None:
    entries = extract_outline_entries("# Title\n## Child\nText\n", "markdown")
    assert [entry.level for entry in entries] == [1, 2]
    assert [entry.title for entry in entries] == ["Title", "Child"]


def test_extract_outline_entries_for_html() -> None:
    entries = extract_outline_entries("<h1>Main</h1><h2>Sub <em>topic</em></h2>", "html")
    assert [entry.level for entry in entries] == [1, 2]
    assert entries[1].title == "Sub topic"


def test_extract_outline_entries_for_yaml() -> None:
    text = "root:\n  child: value\n  items:\n    - name: first\n    - second\n"
    entries = extract_outline_entries(text, "yaml")
    assert [entry.level for entry in entries] == [0, 2, 2, 4, 4]
    assert [entry.title for entry in entries] == ["root", "child", "items", "name", "second"]
