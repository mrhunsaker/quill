"""Tests for the pure typography autoformat helpers (SET-4)."""

from __future__ import annotations

from quill.core.autoformat import (
    EM_DASH,
    LEFT_DOUBLE,
    LEFT_SINGLE,
    RIGHT_DOUBLE,
    RIGHT_SINGLE,
    is_dash_merge,
    smart_quote_for,
)


def test_double_quote_opens_at_start_of_buffer() -> None:
    assert smart_quote_for("", '"') == LEFT_DOUBLE


def test_double_quote_opens_after_whitespace() -> None:
    assert smart_quote_for(" ", '"') == LEFT_DOUBLE
    assert smart_quote_for("\n", '"') == LEFT_DOUBLE


def test_double_quote_closes_after_word_char() -> None:
    assert smart_quote_for("d", '"') == RIGHT_DOUBLE


def test_single_quote_opens_and_closes() -> None:
    assert smart_quote_for("", "'") == LEFT_SINGLE
    assert smart_quote_for("t", "'") == RIGHT_SINGLE


def test_double_quote_opens_after_opening_bracket() -> None:
    assert smart_quote_for("(", '"') == LEFT_DOUBLE


def test_non_quote_input_is_unchanged() -> None:
    assert smart_quote_for("a", "x") == "x"


def test_is_dash_merge_only_after_hyphen() -> None:
    assert is_dash_merge("-") is True
    assert is_dash_merge("a") is False
    assert is_dash_merge("") is False


def test_em_dash_constant() -> None:
    assert EM_DASH == "\u2014"
