"""Cursor-context menu model for the editor (CTX-1).

A pure, ``wx``-free builder for the rich context menu opened by right-click or
the Application/Menu key. The UI layer turns the returned model into a real
``wx.Menu`` and binds each item's ``command`` to its handler; this module owns
*what the menu contains* given the cursor context, so the menu shape, ordering,
and feature-gating are fully testable in ``core``.

The menu is rebuilt live from the word and selection under the cursor:

* On a misspelled word it leads with the in-context spelling suggestions as
  selectable items, then **Add to dictionary** and **Ignore** (FEAT-2), so a fix
  is one keystroke away without opening the F7 dialog.
* Then **Look up** (definition, DICT-2) and **Thesaurus** (synonyms, DICT-1/2)
  for the current word.
* Then the scope-aware selection actions (SEL-3) when text is selected.
* Then the usual cut / copy / paste.

Every entry honors a ``is_feature_enabled`` predicate so items for disabled
features never appear, and a separator is only emitted between two non-empty
groups so the menu never starts, ends, or doubles up on separators.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

# Feature ids that gate context-menu groups.
FEATURE_SPELLCHECK = "core.spellcheck"
FEATURE_DICTIONARY = "core.dictionary"
FEATURE_EDIT = "core.edit"

# Stable command ids for context-menu entries (handlers live in the UI).
CMD_SPELL_SUGGESTION = "context.spell.suggestion"
CMD_SPELL_ADD = "context.spell.add"
CMD_SPELL_IGNORE = "context.spell.ignore"
CMD_LOOK_UP = "context.lookup"
CMD_THESAURUS = "context.thesaurus"
CMD_CUT = "context.cut"
CMD_COPY = "context.copy"
CMD_PASTE = "context.paste"

_SEPARATOR = "__separator__"


@dataclass(frozen=True, slots=True)
class MenuItem:
    """One selectable context-menu entry (or a separator)."""

    command: str
    label: str
    # Optional payload the handler needs (e.g. the replacement word).
    value: str = ""

    @property
    def is_separator(self) -> bool:
        return self.command == _SEPARATOR


def _separator() -> MenuItem:
    return MenuItem(_SEPARATOR, "")


@dataclass(frozen=True, slots=True)
class CursorContext:
    """The editor state the menu is built from."""

    word: str = ""
    selection: str = ""
    misspelled: bool = False
    suggestions: Sequence[str] = field(default_factory=tuple)
    can_paste: bool = True

    @property
    def has_word(self) -> bool:
        return bool(self.word.strip())

    @property
    def has_selection(self) -> bool:
        return bool(self.selection)


def _always_enabled(_feature_id: str) -> bool:
    return True


def build_context_menu(
    context: CursorContext,
    *,
    is_feature_enabled: Callable[[str], bool] = _always_enabled,
    max_suggestions: int = 5,
) -> tuple[MenuItem, ...]:
    """Build the context-menu model for ``context`` (pure).

    Groups are assembled in priority order, each gated by its feature, then
    joined with single separators between non-empty groups.
    """
    groups: list[list[MenuItem]] = []

    spell_enabled = is_feature_enabled(FEATURE_SPELLCHECK)
    if spell_enabled and context.misspelled and context.has_word:
        spelling: list[MenuItem] = [
            MenuItem(CMD_SPELL_SUGGESTION, suggestion, suggestion)
            for suggestion in list(context.suggestions)[:max_suggestions]
        ]
        spelling.append(MenuItem(CMD_SPELL_ADD, "Add to Dictionary", context.word))
        spelling.append(MenuItem(CMD_SPELL_IGNORE, "Ignore", context.word))
        groups.append(spelling)

    if is_feature_enabled(FEATURE_DICTIONARY) and context.has_word:
        groups.append([
            MenuItem(CMD_LOOK_UP, f"Look Up \u201c{context.word}\u201d", context.word),
            MenuItem(CMD_THESAURUS, f"Thesaurus for \u201c{context.word}\u201d", context.word),
        ])

    edit_enabled = is_feature_enabled(FEATURE_EDIT)
    clipboard: list[MenuItem] = []
    if edit_enabled:
        if context.has_selection:
            clipboard.append(MenuItem(CMD_CUT, "Cut", context.selection))
            clipboard.append(MenuItem(CMD_COPY, "Copy", context.selection))
        if context.can_paste:
            clipboard.append(MenuItem(CMD_PASTE, "Paste"))
    if clipboard:
        groups.append(clipboard)

    return _join_groups(groups)


def _join_groups(groups: list[list[MenuItem]]) -> tuple[MenuItem, ...]:
    """Flatten groups, inserting one separator between non-empty groups."""
    items: list[MenuItem] = []
    for group in groups:
        if not group:
            continue
        if items:
            items.append(_separator())
        items.extend(group)
    return tuple(items)
