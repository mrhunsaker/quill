from quill.core.clipboard_collector import DEFAULT_DIVIDER, append_collected


def test_append_to_empty_document_has_no_divider() -> None:
    assert append_collected("", "first") == "first"


def test_append_inserts_divider() -> None:
    result = append_collected("first", "second")
    assert result == "first" + DEFAULT_DIVIDER + "second"


def test_append_empty_clip_is_noop() -> None:
    assert append_collected("first", "") == "first"


def test_append_custom_divider() -> None:
    assert append_collected("a", "b", divider="\n#\n") == "a\n#\nb"
