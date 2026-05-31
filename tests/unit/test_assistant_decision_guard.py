"""The Ask Quill decision guard must never turn a plain chat message into a
document edit.

The on-device model sometimes routes greetings and questions to action=insert,
offering to paste a generic chat reply ("Hello! How can I assist you today?")
into the document. Assistant.decide downgrades insert/replace to answer unless
the message contains an explicit write/edit verb.
"""

from __future__ import annotations

import pytest

from quill.core.ai.agent import AgentDecision
from quill.core.ai.assistant import Assistant


class _AlwaysInsertBackend:
    """A backend that always proposes an insert (the buggy behavior we guard)."""

    def decide(self, message, document, tool_ids, style_preamble):
        return AgentDecision(action="insert", text="Hello! How can I assist you today?")

    def respond(self, prompt):
        return "chat reply"

    def is_available(self):
        return (True, None)


@pytest.fixture
def assistant() -> Assistant:
    return Assistant(backend=_AlwaysInsertBackend())


@pytest.mark.parametrize(
    "message",
    [
        "hello",
        "hi there",
        "thanks!",
        "how do I center a heading?",
        "what's a good intro for an essay?",
        "tell me about climate change",
    ],
)
def test_conversational_messages_stay_in_chat(assistant: Assistant, message: str) -> None:
    assert assistant.decide(message, "", ()).action == "answer"


@pytest.mark.parametrize(
    "message",
    [
        "write a paragraph about dogs",
        "add an introduction",
        "continue from here",
        "rewrite this",
        "make this more formal",
        "summarize this document",
        "can you fix the grammar",
    ],
)
def test_explicit_write_or_edit_requests_still_act(assistant: Assistant, message: str) -> None:
    assert assistant.decide(message, "", ()).action in ("insert", "replace")
