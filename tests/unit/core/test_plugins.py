from __future__ import annotations

from quill.core.features import FEATURE_DEFINITIONS, FeatureManager
from quill.plugins import (
    THIRD_PARTY_PLUGINS_FEATURE,
    load_plugins,
    manifest_ids,
    third_party_plugins_enabled,
)
from quill.plugins.api import PluginManifest


def test_third_party_plugins_feature_is_locked_off() -> None:
    # SEC-8: the loader flag must be defined, experimental, and locked off so a
    # default 1.0 build can never enable third-party plugin loading.
    definition = FEATURE_DEFINITIONS[THIRD_PARTY_PLUGINS_FEATURE]
    assert definition.locked_off is True
    assert definition.maturity == "experimental"


def test_third_party_plugins_disabled_in_default_build() -> None:
    manager = FeatureManager.load(persistent=False)
    assert manager.is_enabled(THIRD_PARTY_PLUGINS_FEATURE) is False
    assert third_party_plugins_enabled(manager) is False


def test_load_plugins_returns_empty_when_flag_off() -> None:
    manager = FeatureManager.load(persistent=False)
    assert load_plugins(manager) == ()


def test_load_plugins_treats_missing_feature_api_as_disabled() -> None:
    assert load_plugins(object()) == ()
    assert third_party_plugins_enabled(object()) is False


def test_manifest_ids_extracts_ids() -> None:
    manifests = (
        PluginManifest("alpha", "Alpha", "1.0", "MIT"),
        PluginManifest("beta", "Beta", "2.0", "Apache-2.0"),
    )
    assert manifest_ids(manifests) == ("alpha", "beta")
