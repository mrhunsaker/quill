from quill.core.set_ops import (
    format_lines,
    lines_common_to_both,
    lines_in_first_not_second,
)

# Cursor placed at the start of the line after "cherry" splits the document into
# first = [apple, banana, cherry] and second = [banana, date, apple].
_TEXT = "apple\nbanana\ncherry\nbanana\ndate\napple"
_CURSOR = len("apple\nbanana\ncherry\n")


def test_lines_in_first_not_second() -> None:
    assert lines_in_first_not_second(_TEXT, _CURSOR) == ["cherry"]


def test_lines_common_to_both() -> None:
    assert lines_common_to_both(_TEXT, _CURSOR) == ["apple", "banana"]


def test_case_insensitivity() -> None:
    text = "Apple\nBanana\napple\nbanana"
    cursor = len("Apple\nBanana\n")
    assert lines_common_to_both(text, cursor, case_sensitive=False) == ["Apple", "Banana"]
    assert lines_common_to_both(text, cursor, case_sensitive=True) == []


def test_format_lines() -> None:
    assert format_lines(["a", "b"]) == "a\nb"
