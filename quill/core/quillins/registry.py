"""Aggregate Quillin contributions and detect conflicts.

Each validated manifest contributes commands, menu items, context-menu entries,
and hotkeys. Across *several* enabled Quillins these must be merged into a single
picture the host can wire onto its menus and keymap. Two rules from
``docs/scripting.md`` are enforced here:

* A contributed ``ext.*`` command id must be **globally unique** across enabled
  Quillins (§15 rule 4 lifts uniqueness from per-file to per-install).
* A hotkey binding must not collide with the host keymap or another Quillin.
  Conflicts are **rejected, never silently overridden** (§4) — the conflicting
  contribution is dropped and recorded so the Quillins Manager can announce it.

This module imports no ``wx`` and performs no IO.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from quill.core.keymap import find_keymap_conflict
from quill.core.quillins.model import (
    ContextMenuContribution,
    ExtensionCommand,
    ExtensionManifest,
    HotkeyContribution,
    MenuContribution,
)


@dataclass(frozen=True, slots=True)
class Conflict:
    """A contribution that could not be registered because it clashed."""

    kind: str  # "command" | "hotkey"
    extension_id: str
    detail: str
    conflicting_with: str


@dataclass(frozen=True, slots=True)
class ResolvedCommand:
    extension_id: str
    command: ExtensionCommand


@dataclass(frozen=True, slots=True)
class ResolvedMenu:
    extension_id: str
    parent: str
    command_id: str
    title: str


@dataclass(frozen=True, slots=True)
class ResolvedContext:
    extension_id: str
    command_id: str
    title: str
    when: str


@dataclass(frozen=True, slots=True)
class ResolvedHotkey:
    extension_id: str
    command_id: str
    binding: str


@dataclass(frozen=True, slots=True)
class ContributionRegistry:
    """The merged, conflict-free contribution picture for the host."""

    commands: dict[str, ResolvedCommand] = field(default_factory=dict)
    menus: tuple[ResolvedMenu, ...] = ()
    context_menu: tuple[ResolvedContext, ...] = ()
    hotkeys: tuple[ResolvedHotkey, ...] = ()
    conflicts: tuple[Conflict, ...] = ()

    def command_title(self, command_id: str) -> str:
        resolved = self.commands.get(command_id)
        if resolved is not None:
            return resolved.command.title
        return command_id

    def keymap_additions(self) -> dict[str, str]:
        """Return ``{command_id: binding}`` for every registered hotkey."""

        return {hotkey.command_id: hotkey.binding for hotkey in self.hotkeys}


def _normalize_binding(binding: str) -> str:
    return binding.strip().upper()


def build_registry(
    manifests: Iterable[ExtensionManifest],
    *,
    host_keymap: Mapping[str, str] | None = None,
) -> ContributionRegistry:
    """Merge contributions from ``manifests`` into a conflict-free registry.

    ``host_keymap`` is the active QUILL keymap; extension bindings that collide
    with it are rejected. Manifests are processed in iteration order, so an
    earlier Quillin wins a tie and later clashing contributions are recorded as
    conflicts and skipped.
    """

    base_keymap: dict[str, str] = dict(host_keymap or {})

    commands: dict[str, ResolvedCommand] = {}
    menus: list[ResolvedMenu] = []
    context_menu: list[ResolvedContext] = []
    hotkeys: list[ResolvedHotkey] = []
    conflicts: list[Conflict] = []

    # Accumulates accepted extension bindings so cross-extension collisions are
    # detected with the same logic used against the host keymap.
    accepted_bindings: dict[str, str] = dict(base_keymap)

    for manifest in manifests:
        extension_id = manifest.id
        local_titles: dict[str, str] = {}

        for command in manifest.contributes.commands:
            local_titles[command.id] = command.title
            existing = commands.get(command.id)
            if existing is not None:
                conflicts.append(
                    Conflict(
                        kind="command",
                        extension_id=extension_id,
                        detail=command.id,
                        conflicting_with=existing.extension_id,
                    )
                )
                continue
            commands[command.id] = ResolvedCommand(extension_id=extension_id, command=command)

        _register_menus(manifest.contributes.menus, extension_id, local_titles, commands, menus)
        _register_context(
            manifest.contributes.context_menu, extension_id, local_titles, commands, context_menu
        )
        _register_hotkeys(
            manifest.contributes.hotkeys,
            extension_id,
            accepted_bindings,
            hotkeys,
            conflicts,
        )

    return ContributionRegistry(
        commands=commands,
        menus=tuple(menus),
        context_menu=tuple(context_menu),
        hotkeys=tuple(hotkeys),
        conflicts=tuple(conflicts),
    )


def _title_for(
    command_id: str,
    local_titles: Mapping[str, str],
    commands: Mapping[str, ResolvedCommand],
) -> str:
    if command_id in local_titles:
        return local_titles[command_id]
    resolved = commands.get(command_id)
    if resolved is not None:
        return resolved.command.title
    return command_id


def _register_menus(
    contributions: tuple[MenuContribution, ...],
    extension_id: str,
    local_titles: Mapping[str, str],
    commands: Mapping[str, ResolvedCommand],
    out: list[ResolvedMenu],
) -> None:
    for menu in contributions:
        out.append(
            ResolvedMenu(
                extension_id=extension_id,
                parent=menu.parent,
                command_id=menu.command,
                title=_title_for(menu.command, local_titles, commands),
            )
        )


def _register_context(
    contributions: tuple[ContextMenuContribution, ...],
    extension_id: str,
    local_titles: Mapping[str, str],
    commands: Mapping[str, ResolvedCommand],
    out: list[ResolvedContext],
) -> None:
    for entry in contributions:
        out.append(
            ResolvedContext(
                extension_id=extension_id,
                command_id=entry.command,
                title=_title_for(entry.command, local_titles, commands),
                when=entry.when,
            )
        )


def _register_hotkeys(
    contributions: tuple[HotkeyContribution, ...],
    extension_id: str,
    accepted_bindings: dict[str, str],
    out: list[ResolvedHotkey],
    conflicts: list[Conflict],
) -> None:
    for hotkey in contributions:
        existing_command = find_keymap_conflict(accepted_bindings, hotkey.command, hotkey.binding)
        if existing_command is not None:
            conflicts.append(
                Conflict(
                    kind="hotkey",
                    extension_id=extension_id,
                    detail=f"{hotkey.command} -> {hotkey.binding}",
                    conflicting_with=existing_command,
                )
            )
            continue
        accepted_bindings[hotkey.command] = _normalize_binding(hotkey.binding)
        out.append(
            ResolvedHotkey(
                extension_id=extension_id,
                command_id=hotkey.command,
                binding=hotkey.binding,
            )
        )
