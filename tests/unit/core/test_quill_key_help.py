"""Tests for the QUILL key live cheat sheet (QK-2, QK-9)."""

from __future__ import annotations

from quill.core.quill_key_help import (
    MODE_BROWSE,
    MODE_PREFIX,
    build_cheat_sheet,
    format_cheat_sheet,
    summarize_cheat_sheet,
)


def _no_bindings(_command_id: str) -> str | None:
    return None


def test_prefix_mode_lists_core_follow_on_keys() -> None:
    groups = build_cheat_sheet(
        mode=MODE_PREFIX,
        binding_lookup=_no_bindings,
        counts={},
        selection_active=False,
    )
    assert len(groups) == 1
    keys = [entry.key for entry in groups[0].entries]
    assert "N" in keys
    assert "?" in keys
    assert "Escape" in keys
    assert "M" in keys
    assert "G" in keys
    # No selection: the selection-actions entry is absent.
    assert "A" not in keys


def test_prefix_mode_adds_selection_actions_when_selection_active() -> None:
    groups = build_cheat_sheet(
        mode=MODE_PREFIX,
        binding_lookup=_no_bindings,
        counts={},
        selection_active=True,
    )
    descriptions = " ".join(entry.description for entry in groups[0].entries)
    assert "Selection actions" in descriptions
    assert any(entry.key == "A" for entry in groups[0].entries)


def test_browse_mode_uses_default_keys_and_live_counts() -> None:
    counts = {
        "headings": 4,
        "links": 9,
        "lists": 2,
        "list_items": 7,
        "tables": 1,
        "block_quotes": 0,
        "bookmarks": 3,
        "code_blocks": 2,
        "paragraphs": 12,
        "sentences": 30,
        "heading_level_1": 1,
        "heading_level_2": 3,
    }
    groups = build_cheat_sheet(
        mode=MODE_BROWSE,
        binding_lookup=_no_bindings,
        counts=counts,
    )
    titles = [group.title for group in groups]
    assert "Move by structure" in titles
    assert "Jump to elements" in titles
    assert "Headings by level" in titles

    flat = {entry.key: entry for group in groups for entry in group.entries}
    # Default keys are surfaced when no binding is configured.
    assert flat["A"].description.lower().startswith("next or previous link")
    assert flat["A"].count == 9
    assert flat["L"].count == 2
    # Heading levels carry per-level counts.
    assert flat["1"].count == 1
    assert flat["2"].count == 3
    # A level with no count key reports None rather than zero.
    assert flat["6"].count is None


def test_browse_mode_respects_configured_bindings() -> None:
    def lookup(command_id: str) -> str | None:
        if command_id == "quill.quick_nav.link":
            return "K"
        return None

    groups = build_cheat_sheet(
        mode=MODE_BROWSE,
        binding_lookup=lookup,
        counts={"links": 5},
    )
    flat = {entry.key: entry for group in groups for entry in group.entries}
    assert "K" in flat
    assert flat["K"].count == 5
    # The default A is no longer used for links.
    assert "A" not in flat


def test_format_cheat_sheet_is_readable_text() -> None:
    groups = build_cheat_sheet(
        mode=MODE_PREFIX,
        binding_lookup=_no_bindings,
        counts={},
        selection_active=False,
    )
    text = format_cheat_sheet(groups)
    assert "QUILL key prefix" in text
    assert "Enter browse mode" in text
    assert text.endswith("\n")


def test_format_cheat_sheet_includes_counts() -> None:
    groups = build_cheat_sheet(
        mode=MODE_BROWSE,
        binding_lookup=_no_bindings,
        counts={"links": 9},
    )
    text = format_cheat_sheet(groups)
    assert "(9)" in text


def test_summarize_cheat_sheet_reports_totals() -> None:
    groups = build_cheat_sheet(
        mode=MODE_BROWSE,
        binding_lookup=_no_bindings,
        counts={},
    )
    summary = summarize_cheat_sheet(groups)
    assert summary.startswith("QUILL key help,")
    assert "groups" in summary


def test_unknown_mode_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_cheat_sheet(mode="nope", binding_lookup=_no_bindings, counts={})
