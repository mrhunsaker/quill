from quill.core.line_ops import (
    delete_line,
    delete_paragraph,
    delete_to_document_end,
    delete_to_document_start,
    delete_to_line_end,
    delete_to_line_start,
    duplicate_line,
    first_non_blank_position,
    join_with_next_line,
    last_non_blank_position,
    move_line_down,
    move_line_up,
    number_lines,
)


def test_duplicate_line() -> None:
    updated, cursor = duplicate_line("a\nb\nc", 2)
    assert updated == "a\nb\nb\nc"
    assert cursor > 0


def test_delete_line() -> None:
    updated, _ = delete_line("a\nb\nc", 2)
    assert updated == "a\nc"


def test_move_line_up() -> None:
    updated, _ = move_line_up("a\nb\nc", 2)
    assert updated == "b\na\nc"


def test_move_line_down() -> None:
    updated, _ = move_line_down("a\nb\nc", 2)
    assert updated == "a\nc\nb"


def test_join_with_next_line() -> None:
    updated, _ = join_with_next_line("a\nb\nc", 0)
    assert updated == "a b\nc"


def test_number_lines_start_value() -> None:
    assert number_lines("a\nb\nc", start=5) == "5. a\n6. b\n7. c"


def test_number_lines_skips_blank_lines() -> None:
    assert number_lines("a\n\nb", start=1) == "1. a\n\n2. b"


def test_delete_to_line_start() -> None:
    text = "hello world"
    updated, cursor = delete_to_line_start(text, 6)
    assert updated == "world"
    assert cursor == 0


def test_delete_to_line_end() -> None:
    text = "hello world\nnext"
    updated, cursor = delete_to_line_end(text, 5)
    assert updated == "hello\nnext"
    assert cursor == 5


def test_delete_to_document_start() -> None:
    updated, cursor = delete_to_document_start("abc\ndef", 4)
    assert updated == "def"
    assert cursor == 0


def test_delete_to_document_end() -> None:
    updated, cursor = delete_to_document_end("abc\ndef", 4)
    assert updated == "abc\n"
    assert cursor == 4


def test_delete_paragraph() -> None:
    text = "one\ntwo\n\nthree\nfour"
    updated, _ = delete_paragraph(text, 0)
    assert updated == "three\nfour"


def test_first_non_blank_position() -> None:
    text = "    indented"
    assert first_non_blank_position(text, 8) == 4


def test_last_non_blank_position() -> None:
    text = "trailing   "
    assert last_non_blank_position(text, 0) == len("trailing")
