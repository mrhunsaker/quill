from quill.core.cursor_address import (
    cursor_address,
    describe_cursor_address,
    describe_document_status,
    describe_selection_length,
    offset_for_percent,
)


def test_cursor_address() -> None:
    text = "abc\ndef\nghi"
    assert cursor_address(text, 0) == (1, 1, 0)
    # Offset 5 is the 'e' on line 2, column 2.
    line, column, percent = cursor_address(text, 5)
    assert (line, column) == (2, 2)
    assert 0 <= percent <= 100


def test_describe_cursor_address() -> None:
    assert describe_cursor_address("hello", 5) == "Line 1, column 6, 100%"


def test_describe_document_status() -> None:
    assert describe_document_status(True, "UTF-8") == "Modified, UTF-8"
    assert describe_document_status(False, "UTF-8") == "Saved, UTF-8"


def test_describe_selection_length() -> None:
    assert describe_selection_length("hello world") == "Selection: 11 characters, 2 words"
    assert describe_selection_length("x") == "Selection: 1 character, 1 word"
    assert describe_selection_length("") == "No selection"


def test_offset_for_percent() -> None:
    text = "0123456789"  # length 10
    assert offset_for_percent(text, 0) == 0
    assert offset_for_percent(text, 50) == 5
    assert offset_for_percent(text, 100) == 10
    assert offset_for_percent(text, 150) == 10  # clamped
    assert offset_for_percent("", 50) == 0
