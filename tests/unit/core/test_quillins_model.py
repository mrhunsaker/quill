"""Tests for the Quillins manifest data model and error hierarchy."""

from __future__ import annotations

from quill.core.quillins.model import (
    API_VERSION,
    CAPABILITIES,
    CONSENT_GATED_CAPABILITIES,
    SCHEMA_ID,
    ApiVersionError,
    CapabilityError,
    ConflictError,
    ConsentDeniedError,
    Contributions,
    ExtensionCommand,
    ExtensionManifest,
    ManifestError,
    QuillinError,
)


def test_schema_and_api_version_are_stable_identifiers() -> None:
    assert SCHEMA_ID == "quill.extension/1"
    assert API_VERSION == 1


def test_consent_gated_caps_are_the_fs_and_net_caps_only() -> None:
    assert CONSENT_GATED_CAPABILITIES == frozenset({"fs.read", "fs.write", "net"})
    assert CONSENT_GATED_CAPABILITIES <= CAPABILITIES


def test_command_is_snippet_or_handler() -> None:
    snippet = ExtensionCommand(id="ext.a.s", title="S", snippet="x")
    handler = ExtensionCommand(id="ext.a.h", title="H", handler="run")
    assert snippet.is_snippet and not snippet.is_handler
    assert handler.is_handler and not handler.is_snippet


def test_manifest_layer_detection() -> None:
    layer1 = ExtensionManifest(id="com.a", name="A", version="1.0.0")
    layer2 = ExtensionManifest(id="com.b", name="B", version="1.0.0", main="extension.py")
    assert not layer1.is_layer_two
    assert layer2.is_layer_two


def test_manifest_has_capability() -> None:
    manifest = ExtensionManifest(
        id="com.a", name="A", version="1.0.0", capabilities=("editor.read",)
    )
    assert manifest.has_capability("editor.read")
    assert not manifest.has_capability("net")


def test_manifest_defaults_are_empty_contributions() -> None:
    manifest = ExtensionManifest(id="com.a", name="A", version="1.0.0")
    assert isinstance(manifest.contributes, Contributions)
    assert manifest.contributes.commands == ()


def test_error_hierarchy_descends_from_quillin_error() -> None:
    for error_type in (
        ManifestError,
        CapabilityError,
        ConsentDeniedError,
        ConflictError,
        ApiVersionError,
    ):
        assert issubclass(error_type, QuillinError)


def test_manifest_error_carries_problem_list() -> None:
    error = ManifestError(["a is bad", "b is bad"])
    assert error.errors == ["a is bad", "b is bad"]
    assert "a is bad" in str(error)


def test_capability_error_names_the_capability() -> None:
    error = CapabilityError("net", detail="fetch(url)")
    assert error.capability == "net"
    assert "net" in str(error)
