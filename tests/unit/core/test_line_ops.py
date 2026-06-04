from quill.core.line_ops import (
    delete_line,
    delete_paragraph,
    delete_to_document_end,
    delete_to_document_start,
    delete_to_line_end,
    delete_to_line_start,
    duplicate_line,
    first_non_blank_position,
    join_paragraph,
    join_selected_lines,
    join_with_next_line,
    last_non_blank_position,
    move_line_down,
    move_line_up,
    move_lines_down,
    move_lines_up,
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


def test_move_lines_up_moves_whole_selection() -> None:
    # Select line3 and line4 (issue #133): both move, not just the first.
    text = "line1\nline2\nline3\nline4"
    start = text.index("line3")
    end = len(text)
    updated, new_start, new_end = move_lines_up(text, start, end)
    assert updated == "line1\nline3\nline4\nline2"
    assert updated[new_start:new_end] == "line3\nline4"


def test_move_lines_down_moves_whole_selection() -> None:
    text = "line1\nline2\nline3\nline4"
    start = text.index("line1")
    end = text.index("line2") + len("line2")
    updated, new_start, new_end = move_lines_down(text, start, end)
    assert updated == "line3\nline1\nline2\nline4"
    assert updated[new_start:new_end] == "line1\nline2"


def test_move_lines_up_single_line_without_selection() -> None:
    text = "a\nb\nc"
    caret = text.index("b")
    updated, _start, _end = move_lines_up(text, caret, caret)
    assert updated == "b\na\nc"


def test_move_lines_up_at_top_is_noop() -> None:
    text = "a\nb\nc"
    updated, start, end = move_lines_up(text, 0, 0)
    assert updated == text
    assert (start, end) == (0, 0)


def test_join_selected_lines_collapses_whole_selection() -> None:
    # Issue #135: each word on its own line, select all, join -> one line.
    text = "this\nis\na\ntest\nof\nthe\neditor"
    updated, new_start, new_end = join_selected_lines(text, 0, len(text))
    assert updated == "this is a test of the editor"
    assert updated[new_start:new_end] == "this is a test of the editor"


def test_join_selected_lines_preserves_paragraph_breaks() -> None:
    text = "one\ntwo\n\nthree\nfour"
    updated, _start, _end = join_selected_lines(text, 0, len(text))
    assert updated == "one two\n\nthree four"


def test_join_paragraph_without_selection() -> None:
    text = "this\nis\na\ntest\n\nnext para"
    caret = text.index("this")
    updated, cursor = join_paragraph(text, caret)
    assert updated == "this is a test\n\nnext para"
    assert cursor == 0


def test_join_paragraph_on_blank_line_is_noop() -> None:
    text = "a\n\nb"
    blank = text.index("\n\n") + 1
    updated, cursor = join_paragraph(text, blank)
    assert updated == text
    assert cursor == blank


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
