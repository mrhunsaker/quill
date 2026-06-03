import re

import pytest

from quill.core.regex_ops import RegexError, count_matches, extract_matches


def test_count_matches() -> None:
    assert count_matches("a1 b2 c3", r"\d") == 3
    assert count_matches("no digits", r"\d") == 0


def test_extract_matches_with_capture_groups() -> None:
    text = "name: Ada\nname: Alan"
    # Pattern has a capture group; whole matches are extracted.
    assert extract_matches(text, r"name: (\w+)") == "name: Ada\nname: Alan"


def test_extract_matches_divider_and_flags() -> None:
    assert extract_matches("A b C", r"[a-z]", divider="|", flags=re.IGNORECASE) == "A|b|C"


def test_invalid_pattern_raises() -> None:
    with pytest.raises(RegexError):
        count_matches("text", r"(")
    with pytest.raises(RegexError):
        extract_matches("text", r"(")
