"""Tests for Quillin discovery, enable/disable state, and the SEC-8 gate.

The loader must return nothing unless the ``core.third_party_plugins`` feature is
enabled (locked off for 1.0). All tests pin discovery to a temporary ``root`` so
they never touch real app data.
"""

from __future__ import annotations

import json
from pathlib import Path

from quill.core.quillins.loader import (
    discover_extensions,
    extensions_root,
    grant_capabilities,
    load_enabled_manifests,
    load_state,
    remove_extension,
    set_enabled,
)


class _Features:
    """Minimal stand-in for the feature registry's ``is_enabled`` surface."""

    def __init__(self, third_party: bool) -> None:
        self._third_party = third_party

    def is_enabled(self, feature_id: str) -> bool:
        if feature_id == "core.third_party_plugins":
            return self._third_party
        return False


def _install(root: Path, extension_id: str, manifest: dict[str, object] | None) -> Path:
    directory = extensions_root(root=root) / extension_id
    directory.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def _snippet_manifest(extension_id: str = "com.example.fence") -> dict[str, object]:
    return {
        "schema": "quill.extension/1",
        "id": extension_id,
        "name": "Code Fence",
        "version": "1.0.0",
        "contributes": {
            "commands": [{"id": "ext.fence.wrap", "title": "Wrap", "run": {"snippet": "x"}}]
        },
    }


def test_discovery_is_empty_when_flag_off(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    assert discover_extensions(_Features(third_party=False), root=tmp_path) == []


def test_discovery_finds_installed_when_flag_on(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    discovered = discover_extensions(_Features(third_party=True), root=tmp_path)
    assert len(discovered) == 1
    assert discovered[0].id == "com.example.fence"
    assert discovered[0].is_valid
    assert not discovered[0].enabled  # default disabled


def test_invalid_manifest_is_surfaced_not_silently_dropped(tmp_path: Path) -> None:
    bad = _snippet_manifest("com.example.bad")
    bad["version"] = "nope"
    _install(tmp_path, "com.example.bad", bad)
    discovered = discover_extensions(_Features(third_party=True), root=tmp_path)
    assert len(discovered) == 1
    assert not discovered[0].is_valid
    assert discovered[0].errors


def test_missing_manifest_is_reported(tmp_path: Path) -> None:
    _install(tmp_path, "no-manifest", manifest=None)
    discovered = discover_extensions(_Features(third_party=True), root=tmp_path)
    assert len(discovered) == 1
    assert not discovered[0].is_valid
    assert any("missing manifest.json" in error for error in discovered[0].errors)


def test_enable_disable_round_trips_through_state(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    set_enabled("com.example.fence", True, root=tmp_path)
    state = load_state(root=tmp_path)
    assert state.entry("com.example.fence").enabled is True
    set_enabled("com.example.fence", False, root=tmp_path)
    assert load_state(root=tmp_path).entry("com.example.fence").enabled is False


def test_load_enabled_manifests_only_returns_enabled_valid(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    features = _Features(third_party=True)
    assert load_enabled_manifests(features, root=tmp_path) == []
    set_enabled("com.example.fence", True, root=tmp_path)
    manifests = load_enabled_manifests(features, root=tmp_path)
    assert [m.id for m in manifests] == ["com.example.fence"]


def test_enabled_but_disabled_flag_still_blocks_loading(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    set_enabled("com.example.fence", True, root=tmp_path)
    # Flag off => SEC-8 returns nothing even though state says enabled.
    assert load_enabled_manifests(_Features(third_party=False), root=tmp_path) == []


def test_grant_capabilities_dedupes_and_persists(tmp_path: Path) -> None:
    grant_capabilities(
        "com.example.fence", ("editor.read", "editor.read", "editor.write"), root=tmp_path
    )
    granted = load_state(root=tmp_path).entry("com.example.fence").granted_capabilities
    assert granted == ("editor.read", "editor.write")


def test_remove_extension_deletes_directory_and_state(tmp_path: Path) -> None:
    _install(tmp_path, "com.example.fence", _snippet_manifest())
    set_enabled("com.example.fence", True, root=tmp_path)
    assert remove_extension("com.example.fence", root=tmp_path) is True
    assert not (extensions_root(root=tmp_path) / "com.example.fence").exists()
    assert "com.example.fence" not in load_state(root=tmp_path).entries


def test_remove_rejects_path_escape(tmp_path: Path) -> None:
    # A crafted id must never delete outside the extensions root.
    assert remove_extension("..", root=tmp_path) is False
