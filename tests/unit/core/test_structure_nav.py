from __future__ import annotations

from quill.core.structure_nav import (
    find_matching_bracket,
    next_structure_position,
    previous_structure_position,
)


def test_find_matching_bracket_handles_nested_pairs() -> None:
    text = "alpha (one [two] three) omega"
    open_paren = text.index("(")
    close_paren = text.index(")")
    assert find_matching_bracket(text, open_paren) == close_paren
    assert find_matching_bracket(text, close_paren) == open_paren


def test_structure_positions_include_headings_and_brackets() -> None:
    text = "# H1\nBody { x }\n## H2"
    first = next_structure_position(text, 0, "markdown")
    assert first is not None
    later = previous_structure_position(text, len(text), "markdown")
    assert later is not None


def test_structure_positions_include_yaml_structure() -> None:
    text = "root:\n  child: value\n"
    assert next_structure_position(text, 0, "yaml") == 6
    assert previous_structure_position(text, len(text), "yaml") == 6
