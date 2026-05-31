from __future__ import annotations

from quill.core.ai.agent import AgentDecision
from quill.core.ai.assistant import Assistant


class _Recorder:
    name = "recorder"

    def __init__(self) -> None:
        self.max_len = 0

    def is_available(self):
        return (True, None)

    def respond(self, prompt: str) -> str:
        self.max_len = max(self.max_len, len(prompt))
        return "ok"

    def decide(self, message, document, tool_ids, style_preamble=""):
        self.max_len = max(self.max_len, len(message))
        return AgentDecision(action="answer", text="ok")


def test_answer_clamps_huge_message() -> None:
    backend = _Recorder()
    Assistant(backend=backend).answer("x" * 50_000, document_text="")
    # Bounded well under the context window (cap + small marker), not 50k.
    assert backend.max_len <= 4200


def test_decide_clamps_huge_message() -> None:
    backend = _Recorder()
    Assistant(backend=backend).decide("y" * 50_000, "", ("file.save",))
    assert backend.max_len <= 4200


def test_short_message_is_untouched() -> None:
    backend = _Recorder()
    Assistant(backend=backend).answer("hello", document_text="")
    assert backend.max_len == len("hello")
