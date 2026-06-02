"""Cursor-context menu model for the editor (CTX-1)."""

from __future__ import annotations

from quill.core.context_menu import (
    CMD_COPY,
    CMD_CUT,
    CMD_LOOK_UP,
    CMD_PASTE,
    CMD_SPELL_ADD,
    CMD_SPELL_IGNORE,
    CMD_SPELL_SUGGESTION,
    CMD_THESAURUS,
    FEATURE_DICTIONARY,
    FEATURE_EDIT,
    FEATURE_SPELLCHECK,
    CursorContext,
    MenuItem,
    build_context_menu,
)


def _commands(items: tuple[MenuItem, ...]) -> list[str]:
    return [item.command for item in items if not item.is_separator]


def test_misspelled_word_leads_with_suggestions_then_add_and_ignore() -> None:
    context = CursorContext(
        word="teh",
        misspelled=True,
        suggestions=("the", "tea", "ten"),
        can_paste=False,
    )
    items = build_context_menu(context)
    commands = _commands(items)
    # Suggestions come first, then add-to-dictionary and ignore.
    assert commands[:5] == [
        CMD_SPELL_SUGGESTION,
        CMD_SPELL_SUGGESTION,
        CMD_SPELL_SUGGESTION,
        CMD_SPELL_ADD,
        CMD_SPELL_IGNORE,
    ]
    suggestions = [item.value for item in items if item.command == CMD_SPELL_SUGGESTION]
    assert suggestions == ["the", "tea", "ten"]
    add = next(item for item in items if item.command == CMD_SPELL_ADD)
    assert add.value == "teh"


def test_suggestions_are_capped() -> None:
    context = CursorContext(
        word="teh",
        misspelled=True,
        suggestions=tuple(f"s{i}" for i in range(20)),
    )
    items = build_context_menu(context, max_suggestions=3)
    suggestions = [item for item in items if item.command == CMD_SPELL_SUGGESTION]
    assert len(suggestions) == 3


def test_lookup_and_thesaurus_present_for_a_word() -> None:
    items = build_context_menu(CursorContext(word="happy", can_paste=False))
    commands = _commands(items)
    assert CMD_LOOK_UP in commands
    assert CMD_THESAURUS in commands
    look_up = next(item for item in items if item.command == CMD_LOOK_UP)
    assert look_up.value == "happy"
    assert "happy" in look_up.label


def test_selection_yields_cut_and_copy() -> None:
    items = build_context_menu(CursorContext(word="word", selection="picked text", can_paste=True))
    commands = _commands(items)
    assert CMD_CUT in commands
    assert CMD_COPY in commands
    assert CMD_PASTE in commands


def test_no_selection_has_no_cut_or_copy() -> None:
    items = build_context_menu(CursorContext(word="word", can_paste=True))
    commands = _commands(items)
    assert CMD_CUT not in commands
    assert CMD_COPY not in commands
    assert CMD_PASTE in commands


def test_disabled_spellcheck_hides_spelling_group() -> None:
    context = CursorContext(word="teh", misspelled=True, suggestions=("the",))
    items = build_context_menu(
        context,
        is_feature_enabled=lambda fid: fid != FEATURE_SPELLCHECK,
    )
    commands = _commands(items)
    assert CMD_SPELL_SUGGESTION not in commands
    assert CMD_SPELL_ADD not in commands
    # Dictionary lookup is still offered.
    assert CMD_LOOK_UP in commands


def test_disabled_dictionary_hides_lookup_group() -> None:
    items = build_context_menu(
        CursorContext(word="happy", can_paste=False),
        is_feature_enabled=lambda fid: fid != FEATURE_DICTIONARY,
    )
    commands = _commands(items)
    assert CMD_LOOK_UP not in commands
    assert CMD_THESAURUS not in commands


def test_disabled_edit_hides_clipboard_group() -> None:
    items = build_context_menu(
        CursorContext(word="happy", selection="sel", can_paste=True),
        is_feature_enabled=lambda fid: fid != FEATURE_EDIT,
    )
    commands = _commands(items)
    assert CMD_CUT not in commands
    assert CMD_PASTE not in commands


def test_separators_only_between_nonempty_groups() -> None:
    context = CursorContext(
        word="teh",
        misspelled=True,
        suggestions=("the",),
        selection="sel",
        can_paste=True,
    )
    items = build_context_menu(context)
    # Never starts or ends with a separator.
    assert not items[0].is_separator
    assert not items[-1].is_separator
    # Never two separators in a row.
    for first, second in zip(items, items[1:], strict=False):
        assert not (first.is_separator and second.is_separator)
    # Three groups (spelling, dictionary, clipboard) -> two separators.
    assert sum(1 for item in items if item.is_separator) == 2


def test_empty_context_yields_no_items() -> None:
    items = build_context_menu(CursorContext(can_paste=False))
    assert items == ()


def test_word_without_misspelling_has_no_spelling_group() -> None:
    items = build_context_menu(CursorContext(word="fine", can_paste=False))
    commands = _commands(items)
    assert CMD_SPELL_SUGGESTION not in commands
    assert CMD_LOOK_UP in commands
