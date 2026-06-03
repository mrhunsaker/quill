"""Plugin interfaces and loading surfaces.

SEC-8: third-party plugin loading is an *experimental* capability that is
disabled in every QUILL 1.0 build. The loader below is the single entry point
for discovering plugins, and it refuses to load anything unless the
``core.third_party_plugins`` feature flag is enabled. That flag is
``locked_off`` for 1.0 (see :mod:`quill.core.features`), so a default build can
never load untrusted plugin code into the process.

This module imports no ``wx`` and no platform code.
"""

from __future__ import annotations

from collections.abc import Iterable

from quill.plugins.api import PluginManifest

THIRD_PARTY_PLUGINS_FEATURE = "core.third_party_plugins"


def third_party_plugins_enabled(features: object) -> bool:
    """Return whether third-party plugin loading is permitted.

    ``features`` is any object exposing ``is_enabled(feature_id) -> bool``
    (typically a :class:`~quill.core.features.FeatureState`). When the object
    does not expose that method, loading is treated as disabled.
    """

    is_enabled = getattr(features, "is_enabled", None)
    if not callable(is_enabled):
        return False
    return bool(is_enabled(THIRD_PARTY_PLUGINS_FEATURE))


def load_plugins(features: object) -> tuple[PluginManifest, ...]:
    """Discover and return third-party plugin manifests.

    SEC-8 gate: returns an empty tuple unless the ``core.third_party_plugins``
    feature flag is enabled. Because that flag is ``locked_off`` for QUILL 1.0,
    a default build always returns ``()`` and never executes third-party code.
    """

    if not third_party_plugins_enabled(features):
        return ()
    # Discovery of enabled plugins is not implemented for 1.0. When the plugin
    # sandbox, signing, and review process ship, manifest discovery and
    # validation will be wired here behind the same flag.
    return ()


def manifest_ids(manifests: Iterable[PluginManifest]) -> tuple[str, ...]:
    """Return the plugin ids for a collection of manifests."""

    return tuple(manifest.plugin_id for manifest in manifests)
