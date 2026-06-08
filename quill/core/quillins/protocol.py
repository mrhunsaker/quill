"""Line-delimited JSON RPC framing shared by the Quillins host and worker.

Layer 2 Quillins run **out-of-process** for isolation (``docs/scripting.md`` §3,
§6): a buggy or malicious extension cannot freeze the editor, corrupt the
buffer, or touch ``wx``. The two processes speak a tiny, line-delimited JSON
protocol over stdio — the same framing style as :mod:`quill.core.ipc`.

Message envelope: one JSON object per line, each carrying a ``type`` field. This
module only frames and names messages; capability enforcement lives in
:mod:`quill.core.quillins.host` and the API surface in
:mod:`quill.core.quillins.host_worker`.
"""

from __future__ import annotations

import json
from typing import Any

# Worker -> host: sent once on startup to advertise the API version it targets.
MSG_HELLO = "hello"
# Host -> worker: load the extension module and run its ``register(api)``.
MSG_LOAD = "load"
# Worker -> host: the commands the extension registered (in response to LOAD).
MSG_REGISTERED = "registered"
# Host -> worker: invoke a registered handler for a command.
MSG_INVOKE = "invoke"
# Worker -> host: a capability-gated request to act on the editor/ui/fs/net.
MSG_API_CALL = "api_call"
# Host -> worker: the result (or error) of an api_call.
MSG_API_RESULT = "api_result"
# Worker -> host: a handler/load finished (ok) or raised (error).
MSG_RESULT = "result"
# Worker -> host: a diagnostic line (never document content).
MSG_LOG = "log"
# Host -> worker: shut down cleanly.
MSG_SHUTDOWN = "shutdown"


def encode_message(message: dict[str, Any]) -> str:
    """Serialize a message to a single newline-terminated JSON line."""

    return json.dumps(message, ensure_ascii=True) + "\n"


def decode_message(line: str) -> dict[str, Any]:
    """Parse a single JSON line into a message dict.

    Raises :class:`ValueError` when the line is not a JSON object so callers can
    treat protocol corruption as a hard, visible failure rather than silently
    mis-handling a half-message.
    """

    parsed = json.loads(line)
    if not isinstance(parsed, dict):
        raise ValueError("protocol message must be a JSON object")
    return parsed


def hello(api_version: int) -> dict[str, Any]:
    return {"type": MSG_HELLO, "api_version": api_version}


def load(main: str, capabilities: list[str]) -> dict[str, Any]:
    return {"type": MSG_LOAD, "main": main, "capabilities": capabilities}


def registered(command_ids: list[str]) -> dict[str, Any]:
    return {"type": MSG_REGISTERED, "commands": command_ids}


def invoke(call_id: int, command: str, context: dict[str, Any]) -> dict[str, Any]:
    return {"type": MSG_INVOKE, "id": call_id, "command": command, "context": context}


def api_call(call_id: int, method: str, args: list[Any]) -> dict[str, Any]:
    return {"type": MSG_API_CALL, "id": call_id, "method": method, "args": args}


def api_ok(call_id: int, value: Any) -> dict[str, Any]:
    return {"type": MSG_API_RESULT, "id": call_id, "ok": True, "value": value}


def api_error(call_id: int, error_kind: str, message: str) -> dict[str, Any]:
    return {
        "type": MSG_API_RESULT,
        "id": call_id,
        "ok": False,
        "error_kind": error_kind,
        "message": message,
    }


def result_ok(call_id: int, value: Any = None) -> dict[str, Any]:
    return {"type": MSG_RESULT, "id": call_id, "ok": True, "value": value}


def result_error(call_id: int, error_kind: str, message: str) -> dict[str, Any]:
    return {
        "type": MSG_RESULT,
        "id": call_id,
        "ok": False,
        "error_kind": error_kind,
        "message": message,
    }


def log(message: str) -> dict[str, Any]:
    return {"type": MSG_LOG, "message": message}


def shutdown() -> dict[str, Any]:
    return {"type": MSG_SHUTDOWN}
