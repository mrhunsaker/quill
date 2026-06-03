import pytest

from quill.core.unicode_insert import CodepointError, parse_codepoint


def test_parse_codepoint_hex_default() -> None:
    assert parse_codepoint("41") == "A"
    assert parse_codepoint("1F600") == "\U0001f600"


def test_parse_codepoint_decimal_prefix() -> None:
    assert parse_codepoint("d65") == "A"
    assert parse_codepoint("d8364") == "\u20ac"  # 8364 -> euro sign


def test_parse_codepoint_u_plus() -> None:
    assert parse_codepoint("U+20AC") == "\u20ac"


def test_parse_codepoint_invalid() -> None:
    with pytest.raises(CodepointError):
        parse_codepoint("xyz")
    with pytest.raises(CodepointError):
        parse_codepoint("")
    with pytest.raises(CodepointError):
        parse_codepoint("110000")  # above U+10FFFF
    with pytest.raises(CodepointError):
        parse_codepoint("D800")  # surrogate
