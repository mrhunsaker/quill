"""Tests for the line-delimited JSON protocol framing and the schema/validator agreement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quill.core.quillins import model, protocol


def test_encode_is_single_newline_terminated_json_line() -> None:
    line = protocol.encode_message({"type": "hello", "api_version": 1})
    assert line.endswith("\n")
    assert line.count("\n") == 1
    assert json.loads(line) == {"type": "hello", "api_version": 1}


def test_decode_round_trips_every_message_constructor() -> None:
    messages = [
        protocol.hello(model.API_VERSION),
        protocol.load("extension.py", ["editor.read"]),
        protocol.registered(["title_case"]),
        protocol.invoke(1, "title_case", {"k": "v"}),
        protocol.api_call(2, "get_text", []),
        protocol.api_ok(2, "body"),
        protocol.api_error(2, "CapabilityError", "nope"),
        protocol.result_ok(1),
        protocol.result_error(1, "QuillinError", "boom"),
        protocol.log("diagnostic"),
        protocol.shutdown(),
    ]
    for message in messages:
        assert protocol.decode_message(protocol.encode_message(message)) == message


def test_decode_rejects_non_object_lines() -> None:
    with pytest.raises(ValueError):
        protocol.decode_message("[1, 2, 3]")


def test_api_error_carries_kind_and_message() -> None:
    message = protocol.api_error(7, "ConsentDeniedError", "denied")
    assert message["ok"] is False
    assert message["error_kind"] == "ConsentDeniedError"
    assert message["id"] == 7


def test_schema_capability_enum_matches_model_catalogue() -> None:
    """The published JSON Schema and the enforced model must list identical caps."""

    schema_path = Path(model.__file__).resolve().parents[1] / "schemas" / "extension.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    enum = set(schema["properties"]["capabilities"]["items"]["enum"])
    assert enum == set(model.CAPABILITIES)


def test_schema_menu_parents_match_model() -> None:
    schema_path = Path(model.__file__).resolve().parents[1] / "schemas" / "extension.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    parents = schema["properties"]["contributes"]["properties"]["menus"]["items"]["properties"][
        "parent"
    ]["enum"]
    assert set(parents) == set(model.MENU_PARENTS)


def test_schema_id_constant_matches_model() -> None:
    schema_path = Path(model.__file__).resolve().parents[1] / "schemas" / "extension.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == model.SCHEMA_ID
