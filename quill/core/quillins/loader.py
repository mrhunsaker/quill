"""Discovery and enable/disable state for installed Quillins.

Installed Quillins live under ``%APPDATA%\\Quill\\extensions\\<id>\\`` with a
``manifest.json`` at the root of each. Per-extension enablement and granted
capabilities are recorded in ``extensions\\state.json``, written atomically and
schema-validated like every other QUILL store.

**SEC-8 gate (non-negotiable for 1.0).** Discovery returns nothing unless the
``core.third_party_plugins`` feature flag is enabled, and that flag is
``locked_off`` for QUILL 1.0. A default build therefore never discovers, loads,
or runs third-party Quillin code. The gate is shared with :mod:`quill.plugins`
so there is a single source of truth.

This module imports no ``wx`` and no platform code.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.quillins.model import ExtensionManifest
from quill.core.quillins.validation import parse_manifest
from quill.core.storage import read_json, write_json_atomic
from quill.plugins import third_party_plugins_enabled

STATE_SCHEMA_VERSION = 1
_MANIFEST_FILENAME = "manifest.json"
_STATE_FILENAME = "state.json"


@dataclass(frozen=True, slots=True)
class InstalledExtension:
    """A Quillin found on disk, valid or not."""

    id: str
    directory: Path
    manifest: ExtensionManifest | None
    enabled: bool
    granted_capabilities: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.manifest is not None and not self.errors


@dataclass(slots=True)
class _ExtensionStateEntry:
    enabled: bool = False
    granted_capabilities: tuple[str, ...] = ()


@dataclass(slots=True)
class ExtensionState:
    """Per-extension enablement and granted capabilities."""

    entries: dict[str, _ExtensionStateEntry] = field(default_factory=dict)

    def entry(self, extension_id: str) -> _ExtensionStateEntry:
        return self.entries.get(extension_id, _ExtensionStateEntry())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "extensions": {
                extension_id: {
                    "enabled": entry.enabled,
                    "granted_capabilities": list(entry.granted_capabilities),
                }
                for extension_id, entry in sorted(self.entries.items())
            },
        }


def extensions_root(*, root: Path | None = None) -> Path:
    """Return the directory that holds installed Quillins."""

    base = root if root is not None else app_data_dir()
    return base / "extensions"


def _state_path(*, root: Path | None = None) -> Path:
    return extensions_root(root=root) / _STATE_FILENAME


def load_state(*, root: Path | None = None) -> ExtensionState:
    """Read the enablement state store, tolerating a missing or partial file."""

    raw = read_json(_state_path(root=root), default=None)
    state = ExtensionState()
    if not isinstance(raw, dict):
        return state
    extensions = raw.get("extensions")
    if not isinstance(extensions, dict):
        return state
    for extension_id, value in extensions.items():
        if not isinstance(extension_id, str) or not isinstance(value, dict):
            continue
        enabled = bool(value.get("enabled", False))
        raw_caps = value.get("granted_capabilities", [])
        caps = (
            tuple(item for item in raw_caps if isinstance(item, str))
            if isinstance(raw_caps, list)
            else ()
        )
        state.entries[extension_id] = _ExtensionStateEntry(
            enabled=enabled, granted_capabilities=caps
        )
    return state


def save_state(state: ExtensionState, *, root: Path | None = None) -> None:
    """Persist the enablement state store atomically."""

    base = root if root is not None else app_data_dir()
    write_json_atomic(_state_path(root=root), state.to_dict(), base=base)


def _read_manifest(directory: Path) -> tuple[ExtensionManifest | None, tuple[str, ...]]:
    manifest_path = directory / _MANIFEST_FILENAME
    if not manifest_path.exists():
        return None, (f"missing {_MANIFEST_FILENAME}",)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, (f"unreadable manifest: {error}",)
    try:
        manifest = parse_manifest(raw)
    except Exception as error:  # ManifestError carries the detailed problem list
        errors = getattr(error, "errors", None)
        if isinstance(errors, list):
            return None, tuple(str(item) for item in errors)
        return None, (str(error),)
    return manifest, ()


def discover_extensions(features: object, *, root: Path | None = None) -> list[InstalledExtension]:
    """Discover installed Quillins.

    Returns an empty list unless the ``core.third_party_plugins`` flag is enabled
    (SEC-8). Because that flag is ``locked_off`` for 1.0, a default build always
    returns ``[]`` and never reads third-party manifests.
    """

    if not third_party_plugins_enabled(features):
        return []

    directory_root = extensions_root(root=root)
    if not directory_root.exists():
        return []

    state = load_state(root=root)
    discovered: list[InstalledExtension] = []
    for child in sorted(directory_root.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        manifest, errors = _read_manifest(child)
        extension_id = manifest.id if manifest is not None else child.name
        entry = state.entry(extension_id)
        discovered.append(
            InstalledExtension(
                id=extension_id,
                directory=child,
                manifest=manifest,
                enabled=entry.enabled,
                granted_capabilities=entry.granted_capabilities,
                errors=errors,
            )
        )
    return discovered


def load_enabled_manifests(
    features: object, *, root: Path | None = None
) -> list[ExtensionManifest]:
    """Return validated manifests for enabled, valid Quillins only (SEC-8 gated)."""

    manifests: list[ExtensionManifest] = []
    for installed in discover_extensions(features, root=root):
        if installed.enabled and installed.manifest is not None and installed.is_valid:
            manifests.append(installed.manifest)
    return manifests


def set_enabled(extension_id: str, enabled: bool, *, root: Path | None = None) -> ExtensionState:
    """Enable or disable a Quillin and persist the change."""

    state = load_state(root=root)
    entry = state.entries.get(extension_id, _ExtensionStateEntry())
    entry.enabled = enabled
    state.entries[extension_id] = entry
    save_state(state, root=root)
    return state


def grant_capabilities(
    extension_id: str, capabilities: tuple[str, ...], *, root: Path | None = None
) -> ExtensionState:
    """Record the capabilities a user has granted a Quillin and persist."""

    state = load_state(root=root)
    entry = state.entries.get(extension_id, _ExtensionStateEntry())
    entry.granted_capabilities = tuple(dict.fromkeys(capabilities))
    state.entries[extension_id] = entry
    save_state(state, root=root)
    return state


def remove_extension(extension_id: str, *, root: Path | None = None) -> bool:
    """Uninstall a Quillin: delete its directory and forget its state.

    Returns ``True`` when a directory was removed. Path containment is enforced
    so a crafted id can never delete outside the extensions root.
    """

    directory_root = extensions_root(root=root).resolve()
    target = (extensions_root(root=root) / extension_id).resolve()
    if directory_root not in target.parents:
        return False

    removed = False
    if target.is_dir():
        shutil.rmtree(target)
        removed = True

    state = load_state(root=root)
    if extension_id in state.entries:
        del state.entries[extension_id]
        save_state(state, root=root)
    return removed
