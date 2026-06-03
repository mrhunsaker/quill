from quill.core.wrap_ops import hard_wrap, widest_line_width


def test_widest_line_width() -> None:
    assert widest_line_width("ab\nabcd\nabc") == 4
    assert widest_line_width("") == 0


def test_hard_wrap_width() -> None:
    text = "the quick brown fox jumps over the lazy dog"
    wrapped = hard_wrap(text, 15)
    assert all(len(line) <= 15 for line in wrapped.split("\n"))
    # Round-trips back to the original words.
    assert wrapped.replace("\n", " ") == text


def test_hard_wrap_preserves_paragraphs() -> None:
    text = "alpha beta gamma\n\ndelta epsilon zeta"
    wrapped = hard_wrap(text, 10)
    assert "" in wrapped.split("\n")  # blank line separator preserved
    assert wrapped.count("\n\n") == 1


def test_hard_wrap_zero_width_noop() -> None:
    assert hard_wrap("anything here", 0) == "anything here"
