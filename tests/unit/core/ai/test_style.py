from __future__ import annotations

from quill.core.ai.style import StyleProfile, add_sample, style_preamble


def test_add_sample_appends_and_trims() -> None:
    p = StyleProfile()
    add_sample(p, "  hello  ")
    add_sample(p, "")
    assert p.samples == ["hello"]


def test_style_preamble_empty_when_disabled_or_no_guide() -> None:
    assert style_preamble(StyleProfile(enabled=False, guide="x")) == ""
    assert style_preamble(StyleProfile(enabled=True, guide="")) == ""


def test_style_preamble_includes_guide_when_enabled() -> None:
    out = style_preamble(StyleProfile(enabled=True, guide="- short sentences"))
    assert "short sentences" in out
    assert "personal voice" in out.lower()
