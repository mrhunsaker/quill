from quill.core.indent_infer import (
    describe_indent_change,
    describe_indent_unit,
    indent_columns,
    infer_indent_unit,
)


def test_infer_indent_unit_spaces() -> None:
    text = "def f():\n    a = 1\n    if a:\n        b = 2\n"
    assert infer_indent_unit(text) == "    "


def test_infer_indent_unit_two_spaces_gcd() -> None:
    text = "a\n  b\n    c\n"
    assert infer_indent_unit(text) == "  "


def test_infer_indent_unit_tabs() -> None:
    text = "a\n\tb\n\t\tc\n"
    assert infer_indent_unit(text) == "\t"


def test_infer_indent_unit_none() -> None:
    assert infer_indent_unit("no indent here\nstill none\n") is None


def test_describe_indent_unit() -> None:
    assert describe_indent_unit("    ") == "4 spaces"
    assert describe_indent_unit(" ") == "1 space"
    assert describe_indent_unit("\t") == "tab"
    assert describe_indent_unit(None) == "no indentation"


def test_indent_columns() -> None:
    assert indent_columns("    x") == 4
    assert indent_columns("\tx", tab_width=4) == 4
    assert indent_columns("no indent") == 0


def test_describe_indent_change() -> None:
    assert describe_indent_change(0, 4) == "Indent 4"
    assert describe_indent_change(4, 0) == "Outdent 0"
    assert describe_indent_change(4, 4) is None
