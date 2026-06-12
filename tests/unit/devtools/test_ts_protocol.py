"""Tests for quill.devtools.ts_worker_protocol."""

from __future__ import annotations

import json

import pytest

from quill.devtools.ts_worker_protocol import ExecuteMsg, ReturnMsg, parse_node_message


def test_execute_msg_serializes():
    msg = ExecuteMsg(req_id="req1", source="await quill.gotoLine(5);")
    raw = msg.to_json()
    obj = json.loads(raw)
    assert obj["type"] == "execute"
    assert obj["id"] == "req1"
    assert obj["source"] == "await quill.gotoLine(5);"


def test_return_msg_with_value():
    msg = ReturnMsg(req_id="req1", call_id="c1", value=42)
    raw = msg.to_json()
    obj = json.loads(raw)
    assert obj["type"] == "return"
    assert obj["id"] == "req1"
    assert obj["call"] == "c1"
    assert obj["value"] == 42
    assert "error" not in obj


def test_return_msg_with_error():
    msg = ReturnMsg(req_id="req1", call_id="c1", error="command failed")
    raw = msg.to_json()
    obj = json.loads(raw)
    assert obj["type"] == "return"
    assert obj["error"] == "command failed"
    assert "value" not in obj


def test_parse_node_ready_message():
    msg = parse_node_message('{"type": "ready"}')
    assert msg["type"] == "ready"


def test_parse_node_done_message():
    raw = json.dumps({"type": "done", "id": "req1", "value": None, "output": ""})
    msg = parse_node_message(raw)
    assert msg["type"] == "done"
    assert msg["id"] == "req1"


def test_parse_node_invoke_message():
    raw = json.dumps({
        "type": "invoke",
        "id": "req1",
        "call": "c1",
        "method": "gotoLine",
        "args": [5],
    })
    msg = parse_node_message(raw)
    assert msg["method"] == "gotoLine"
    assert msg["args"] == [5]


def test_parse_node_output_message():
    raw = json.dumps({"type": "output", "id": "req1", "stream": "log", "text": "hello"})
    msg = parse_node_message(raw)
    assert msg["stream"] == "log"
    assert msg["text"] == "hello"


def test_parse_node_error_message():
    raw = json.dumps({"type": "error", "id": "req1", "message": "ReferenceError: x is not defined"})
    msg = parse_node_message(raw)
    assert msg["type"] == "error"


def test_parse_raises_on_invalid_json():
    with pytest.raises(ValueError, match="Bad worker JSON"):
        parse_node_message("not json {{{")


def test_parse_raises_on_missing_type():
    with pytest.raises(ValueError, match="Missing 'type'"):
        parse_node_message('{"no_type": true}')
