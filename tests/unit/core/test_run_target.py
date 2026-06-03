from quill.core.run_target import (
    classify_target,
    is_dangerous_executable,
    target_at_cursor,
)


def test_target_at_cursor_uses_selection_first() -> None:
    assert target_at_cursor("anything", 0, selection="  picked  ") == "picked"


def test_target_at_cursor_extracts_token() -> None:
    text = "see https://example.org/page now"
    cursor = text.index("example")
    assert target_at_cursor(text, cursor) == "https://example.org/page"


def test_target_at_cursor_strips_trailing_punctuation() -> None:
    text = "visit https://example.org."
    cursor = text.index("example")
    assert target_at_cursor(text, cursor) == "https://example.org"


def test_target_at_cursor_empty() -> None:
    assert target_at_cursor("", 0) == ""


def test_classify_http_url_is_safe() -> None:
    target = classify_target("https://example.org")
    assert target.kind == "url"
    assert target.safe is True


def test_classify_bare_www_is_promoted_to_https() -> None:
    target = classify_target("www.example.org")
    assert target.kind == "url"
    assert target.safe is True
    assert target.value == "https://www.example.org"


def test_classify_email_is_safe() -> None:
    target = classify_target("writer@example.org")
    assert target.kind == "email"
    assert target.safe is True


def test_classify_mailto_is_safe() -> None:
    target = classify_target("mailto:writer@example.org")
    assert target.kind == "email"
    assert target.safe is True


def test_classify_rejects_javascript_scheme() -> None:
    target = classify_target("javascript:alert(1)")
    assert target.safe is False
    assert "scheme" in target.reason.lower()


def test_classify_rejects_file_scheme() -> None:
    target = classify_target("file:///c:/windows/system32/cmd.exe")
    assert target.safe is False


def test_classify_rejects_executable_path() -> None:
    target = classify_target("C:/tools/evil.exe")
    assert target.kind == "path"
    assert target.safe is False
    assert "executable" in target.reason.lower() or "script" in target.reason.lower()


def test_classify_allows_plain_path() -> None:
    target = classify_target("notes/todo.txt")
    assert target.kind == "path"
    assert target.safe is True


def test_classify_empty_is_unknown() -> None:
    target = classify_target("   ")
    assert target.kind == "unknown"
    assert target.safe is False


def test_is_dangerous_executable_variants() -> None:
    assert is_dangerous_executable("run.BAT") is True
    assert is_dangerous_executable("script.ps1") is True
    assert is_dangerous_executable("readme.md") is False
