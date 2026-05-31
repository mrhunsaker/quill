from pathlib import Path

from quill.core.format_ops import (
    continue_markdown_list,
    convert_indentation_to_spaces,
    convert_indentation_to_tabs,
    indent_lines,
    normalize_whitespace,
    outdent_lines,
    remove_duplicate_lines,
    reverse_lines,
    sort_lines,
    toggle_block_comment,
    toggle_line_comment,
    trim_trailing_whitespace,
)


def test_indent_and_outdent_lines() -> None:
    indented, start, end = indent_lines("alpha\nbeta", 0, 10)
    assert indented == "    alpha\n    beta"
    assert (start, end) == (0, len(indented))

    outdented, _, _ = outdent_lines(indented, 0, len(indented))
    assert outdented == "alpha\nbeta"


def test_toggle_line_comment_prefix_style() -> None:
    text = "print('x')\nprint('y')\n"
    commented, _, _ = toggle_line_comment(text, 0, len(text), Path("script.py"))
    assert commented == "# print('x')\n# print('y')\n"

    uncommented, _, _ = toggle_line_comment(commented, 0, len(commented), Path("script.py"))
    assert uncommented == text


def test_toggle_line_comment_prefix_style_on_blank_line() -> None:
    commented, _, _ = toggle_line_comment("", 0, 0, Path("script.py"))
    assert commented == "# "


def test_toggle_line_comment_html_style() -> None:
    text = "hello\nworld"
    commented, _, _ = toggle_line_comment(text, 0, len(text), Path("notes.md"))
    assert commented == "<!-- hello -->\n<!-- world -->"

    uncommented, _, _ = toggle_line_comment(commented, 0, len(commented), Path("notes.md"))
    assert uncommented == text


def test_toggle_line_comment_html_style_on_blank_line() -> None:
    commented, _, _ = toggle_line_comment("", 0, 0, Path("notes.md"))
    assert commented == "<!--  -->"


def test_toggle_block_comment_wraps_and_unwraps() -> None:
    wrapped, start, end = toggle_block_comment("alpha", 0, 5, Path("script.py"))
    assert wrapped == "/* alpha */"
    assert wrapped[start:end] == "/* alpha */"

    unwrapped, _, _ = toggle_block_comment(wrapped, 0, len(wrapped), Path("script.py"))
    assert unwrapped == "alpha"


def test_toggle_block_comment_insert_when_no_selection() -> None:
    updated, start, end = toggle_block_comment("", 0, 0, Path("notes.md"))
    assert updated == "<!--  -->"
    assert start == end == len("<!-- ")


def test_text_cleanup_helpers() -> None:
    text = "beta  \nalpha\t\nalpha\n"

    assert trim_trailing_whitespace(text) == "beta\nalpha\nalpha\n"
    assert normalize_whitespace(" one\t two \n\nthree   four ") == "one two\n\nthree four"
    assert sort_lines(text) == "alpha\nalpha\t\nbeta  \n"
    assert reverse_lines("one\ntwo\nthree") == "three\ntwo\none"
    assert remove_duplicate_lines("one\ntwo\none\nONE\n") == "one\ntwo\nONE\n"
    assert convert_indentation_to_spaces("\talpha\n  beta", 4) == "    alpha\n  beta"
    assert convert_indentation_to_tabs("        alpha\n  beta", 4) == "\t\talpha\n  beta"


def test_continue_markdown_list_for_bullets() -> None:
    source = "- item"
    result = continue_markdown_list(source, len(source))
    assert result is not None
    assert result.text == "- item\n- "
    assert result.exited_list is False


def test_continue_markdown_list_for_numbered_items() -> None:
    source = "2. next"
    result = continue_markdown_list(source, len(source))
    assert result is not None
    assert result.text == "2. next\n3. "
    assert result.exited_list is False


def test_continue_markdown_list_for_task_items() -> None:
    source = "- [x] done"
    result = continue_markdown_list(source, len(source))
    assert result is not None
    assert result.text == "- [x] done\n- [ ] "
    assert result.exited_list is False


def test_continue_markdown_list_exits_empty_item() -> None:
    source = "- "
    result = continue_markdown_list(source, len(source))
    assert result is not None
    assert result.text == ""
    assert result.caret == 0
    assert result.exited_list is True
