"""Abstract AI backend so the assistant is engine-agnostic."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ContextWindowExceeded(Exception):
    """Raised when a prompt + response would exceed the model's context window."""


class AIBackend(ABC):
    name: str = "ai"

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        """Return (available, reason). reason is a message when unavailable."""

    @abstractmethod
    def respond(self, prompt: str) -> str:
        """Return the model's text response for a single prompt (blocking)."""
