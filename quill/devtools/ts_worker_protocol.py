"""JSON-RPC message types for the Python ↔ Node TypeScript worker bridge.

Protocol overview (all messages are single-line JSON on stdin/stdout):

Python → Node (stdin):
  {"type": "execute", "id": "req1", "source": "await quill.gotoLine(5);"}
  {"type": "return",  "id": "req1", "call": "c1", "value": null}
  {"type": "return",  "id": "req1", "call": "c1", "error": "message"}

Node → Python (stdout):
  {"type": "invoke",  "id": "req1", "call": "c1", "method": "gotoLine", "args": [5]}
  {"type": "done",    "id": "req1", "value": null}
  {"type": "error",   "id": "req1", "message": "ReferenceError: x is not defined",
                       "stack": "..."}
  {"type": "output",  "id": "req1", "stream": "log", "text": "hello"}
  {"type": "ready"}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Messages Python sends to Node


@dataclass(slots=True)
class ExecuteMsg:
    req_id: str
    source: str

    def to_json(self) -> str:
        return json.dumps({"type": "execute", "id": self.req_id, "source": self.source})


@dataclass(slots=True)
class ReturnMsg:
    req_id: str
    call_id: str
    value: Any = None
    error: str | None = None

    def to_json(self) -> str:
        obj: dict[str, Any] = {"type": "return", "id": self.req_id, "call": self.call_id}
        if self.error is not None:
            obj["error"] = self.error
        else:
            obj["value"] = self.value
        return json.dumps(obj)


# ---------------------------------------------------------------------------
# Messages Node sends to Python


def parse_node_message(line: str) -> dict[str, Any]:
    """Parse one stdout line from the worker; raises ValueError on bad JSON."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Bad worker JSON: {line!r}") from exc
    if not isinstance(obj, dict) or "type" not in obj:
        raise ValueError(f"Missing 'type' in worker message: {obj!r}")
    return obj
