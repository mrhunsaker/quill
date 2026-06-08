"""Validation tests for the ``quill.extension/1`` manifest contract.

These exercise :mod:`quill.core.quillins.validation`, the hand-rolled validator
that is the authority the loader enforces (no ``jsonschema`` dependency ships).
"""

from __future__ import annotations

import pytest

from quill.core.quillins.model import ExtensionManifest, ManifestError
from quill.core.quillins.validation import parse_manifest, validate_manifest


def _snippet_manifest() -> dict[str, object]:
    """A minimal, valid Layer 1 (snippet-only) manifest."""

    return {
        "schema": "quill.extension/1",
        "id": "com.example.fence",
        "name": "Code Fence",
        "version": "1.0.0",
        "contributes": {
            "commands": [
                {
                    "id": "ext.fence.wrap",
                    "title": "Wrap In Code Fence",
                    "run": {"snippet": "```\n${selection}\n```\n${cursor}"},
                }
            ],
            "context_menu": [{"when": "editor.hasSelection", "command": "ext.fence.wrap"}],
            "hotkeys": [{"command": "ext.fence.wrap", "binding": "Ctrl+Shift+Grave, F"}],
        },
    }


def _handler_manifest() -> dict[str, object]:
    """A minimal, valid Layer 2 (Python handler) manifest."""

    return {
        "schema": "quill.extension/1",
        "id": "com.example.titlecase",
        "name": "Title Case",
        "version": "1.0.0",
        "capabilities": ["editor.read", "editor.write", "ui.announce", "ui.command"],
        "main": "extension.py",
        "contributes": {
            "commands": [
                {
                    "id": "ext.titlecase.run",
                    "title": "Title Case Selection",
                    "run": {"handler": "title_case"},
                }
            ],
            "menus": [{"parent": "Format", "command": "ext.titlecase.run"}],
        },
    }


def test_valid_snippet_manifest_has_no_errors() -> None:
    assert validate_manifest(_snippet_manifest()) == []


def test_valid_handler_manifest_has_no_errors() -> None:
    assert validate_manifest(_handler_manifest()) == []


def test_parse_builds_immutable_model() -> None:
    manifest = parse_manifest(_handler_manifest())
    assert isinstance(manifest, ExtensionManifest)
    assert manifest.id == "com.example.titlecase"
    assert manifest.is_layer_two
    assert manifest.has_capability("ui.command")
    command = manifest.contributes.commands[0]
    assert command.is_handler and command.handler == "title_case"


def test_parse_snippet_is_layer_one() -> None:
    manifest = parse_manifest(_snippet_manifest())
    assert not manifest.is_layer_two
    assert manifest.contributes.commands[0].is_snippet


def test_non_object_manifest_is_rejected() -> None:
    assert validate_manifest(["not", "an", "object"]) == ["manifest must be a JSON object"]


def test_wrong_schema_is_rejected() -> None:
    raw = _snippet_manifest()
    raw["schema"] = "quill.extension/2"
    errors = validate_manifest(raw)
    assert any("schema must be" in error for error in errors)


def test_unknown_top_level_property_is_rejected() -> None:
    raw = _snippet_manifest()
    raw["surprise"] = True
    errors = validate_manifest(raw)
    assert any("unknown property 'surprise'" in error for error in errors)


@pytest.mark.parametrize("bad_id", ["Com.Example", "ab", "a..b", "ext space"])
def test_invalid_id_is_rejected(bad_id: str) -> None:
    raw = _snippet_manifest()
    raw["id"] = bad_id
    assert validate_manifest(raw) != []


@pytest.mark.parametrize("bad_version", ["1.0", "v1.0.0", "1.0.0.0", "1.0.x"])
def test_invalid_version_is_rejected(bad_version: str) -> None:
    raw = _snippet_manifest()
    raw["version"] = bad_version
    assert any("MAJOR.MINOR.PATCH" in error for error in validate_manifest(raw))


def test_command_id_must_be_ext_namespaced() -> None:
    raw = _snippet_manifest()
    raw["contributes"]["commands"][0]["id"] = "wrap"  # type: ignore[index]
    errors = validate_manifest(raw)
    assert any("must match 'ext." in error for error in errors)


def test_command_run_requires_exactly_one_of_snippet_or_handler() -> None:
    raw = _snippet_manifest()
    raw["contributes"]["commands"][0]["run"] = {  # type: ignore[index]
        "snippet": "x",
        "handler": "y",
    }
    errors = validate_manifest(raw)
    assert any("exactly one of snippet or handler" in error for error in errors)


def test_handler_command_requires_main_and_ui_command() -> None:
    raw = _handler_manifest()
    raw.pop("main")
    del raw["capabilities"]  # type: ignore[arg-type]
    errors = validate_manifest(raw)
    assert any("requires a top-level 'main' module" in error for error in errors)
    assert any("requires the 'ui.command' capability" in error for error in errors)


def test_unknown_capability_is_rejected() -> None:
    raw = _snippet_manifest()
    raw["capabilities"] = ["editor.read", "telepathy"]
    errors = validate_manifest(raw)
    assert any("not a known capability" in error for error in errors)


def test_duplicate_capability_is_rejected() -> None:
    raw = _snippet_manifest()
    raw["capabilities"] = ["editor.read", "editor.read"]
    errors = validate_manifest(raw)
    assert any("duplicate" in error for error in errors)


def test_duplicate_command_id_is_rejected() -> None:
    raw = _snippet_manifest()
    commands = raw["contributes"]["commands"]  # type: ignore[index]
    commands.append(dict(commands[0]))
    errors = validate_manifest(raw)
    assert any("duplicate" in error for error in errors)


def test_menu_parent_must_be_known() -> None:
    raw = _handler_manifest()
    raw["contributes"]["menus"][0]["parent"] = "Bogus"  # type: ignore[index]
    errors = validate_manifest(raw)
    assert any("parent must be one of" in error for error in errors)


def test_context_when_must_be_known() -> None:
    raw = _snippet_manifest()
    raw["contributes"]["context_menu"][0]["when"] = "editor.onMars"  # type: ignore[index]
    errors = validate_manifest(raw)
    assert any("when must be one of" in error for error in errors)


def test_menu_referencing_unknown_ext_command_is_rejected() -> None:
    raw = _snippet_manifest()
    raw["contributes"]["menus"] = [{"parent": "Tools", "command": "ext.nope.missing"}]  # type: ignore[index]
    errors = validate_manifest(raw)
    assert any("unknown contributed command 'ext.nope.missing'" in error for error in errors)


def test_builtin_command_reference_checked_when_set_supplied() -> None:
    raw = _snippet_manifest()
    raw["contributes"]["menus"] = [{"parent": "Tools", "command": "app.does_not_exist"}]  # type: ignore[index]
    errors = validate_manifest(raw, builtin_command_ids=frozenset({"app.real"}))
    assert any("unknown built-in command 'app.does_not_exist'" in error for error in errors)
    # Without the built-in set, a non-ext reference is accepted unchecked.
    assert not any("built-in" in error for error in validate_manifest(raw))


def test_parse_raises_manifest_error_with_problem_list() -> None:
    raw = _snippet_manifest()
    raw["version"] = "nope"
    with pytest.raises(ManifestError) as excinfo:
        parse_manifest(raw)
    assert excinfo.value.errors
