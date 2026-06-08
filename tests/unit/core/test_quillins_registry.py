"""Tests for cross-Quillin contribution merging and conflict detection."""

from __future__ import annotations

from quill.core.quillins.model import (
    ContextMenuContribution,
    Contributions,
    ExtensionCommand,
    ExtensionManifest,
    HotkeyContribution,
    MenuContribution,
)
from quill.core.quillins.registry import build_registry


def _manifest(
    extension_id: str,
    *,
    commands: tuple[ExtensionCommand, ...] = (),
    menus: tuple[MenuContribution, ...] = (),
    context_menu: tuple[ContextMenuContribution, ...] = (),
    hotkeys: tuple[HotkeyContribution, ...] = (),
) -> ExtensionManifest:
    return ExtensionManifest(
        id=extension_id,
        name=extension_id,
        version="1.0.0",
        contributes=Contributions(
            commands=commands, menus=menus, context_menu=context_menu, hotkeys=hotkeys
        ),
    )


def test_single_manifest_registers_everything() -> None:
    manifest = _manifest(
        "com.example.a",
        commands=(ExtensionCommand(id="ext.a.run", title="Run A", snippet="x"),),
        menus=(MenuContribution(parent="Tools", command="ext.a.run"),),
        context_menu=(ContextMenuContribution(command="ext.a.run", when="always"),),
        hotkeys=(HotkeyContribution(command="ext.a.run", binding="Ctrl+Alt+A"),),
    )
    registry = build_registry([manifest])
    assert "ext.a.run" in registry.commands
    assert registry.command_title("ext.a.run") == "Run A"
    assert len(registry.menus) == 1
    assert len(registry.context_menu) == 1
    assert registry.keymap_additions() == {"ext.a.run": "Ctrl+Alt+A"}
    assert registry.conflicts == ()


def test_duplicate_command_id_across_quillins_is_a_conflict() -> None:
    first = _manifest(
        "com.example.a",
        commands=(ExtensionCommand(id="ext.shared.run", title="A", snippet="a"),),
    )
    second = _manifest(
        "com.example.b",
        commands=(ExtensionCommand(id="ext.shared.run", title="B", snippet="b"),),
    )
    registry = build_registry([first, second])
    # First Quillin wins the id; the second is recorded as a conflict, not merged.
    assert registry.commands["ext.shared.run"].extension_id == "com.example.a"
    assert any(
        c.kind == "command" and c.extension_id == "com.example.b" for c in registry.conflicts
    )


def test_hotkey_conflicting_with_host_keymap_is_rejected() -> None:
    manifest = _manifest(
        "com.example.a",
        commands=(ExtensionCommand(id="ext.a.run", title="A", snippet="a"),),
        hotkeys=(HotkeyContribution(command="ext.a.run", binding="Ctrl+S"),),
    )
    registry = build_registry([manifest], host_keymap={"app.save": "Ctrl+S"})
    assert registry.keymap_additions() == {}
    assert any(c.kind == "hotkey" and c.conflicting_with == "app.save" for c in registry.conflicts)


def test_cross_quillin_hotkey_collision_is_rejected() -> None:
    first = _manifest(
        "com.example.a",
        commands=(ExtensionCommand(id="ext.a.run", title="A", snippet="a"),),
        hotkeys=(HotkeyContribution(command="ext.a.run", binding="Ctrl+Alt+Z"),),
    )
    second = _manifest(
        "com.example.b",
        commands=(ExtensionCommand(id="ext.b.run", title="B", snippet="b"),),
        hotkeys=(HotkeyContribution(command="ext.b.run", binding="ctrl+alt+z"),),
    )
    registry = build_registry([first, second])
    # The earlier Quillin keeps the binding; the later collision is dropped.
    assert registry.keymap_additions() == {"ext.a.run": "Ctrl+Alt+Z"}
    assert any(c.kind == "hotkey" and c.extension_id == "com.example.b" for c in registry.conflicts)


def test_menu_title_resolves_from_contributed_command() -> None:
    manifest = _manifest(
        "com.example.a",
        commands=(ExtensionCommand(id="ext.a.run", title="Pretty Title", snippet="a"),),
        menus=(MenuContribution(parent="Format", command="ext.a.run"),),
    )
    registry = build_registry([manifest])
    assert registry.menus[0].title == "Pretty Title"
    assert registry.menus[0].parent == "Format"
