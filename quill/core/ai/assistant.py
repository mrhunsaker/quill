"""High-level writing assistant built on an AIBackend.

Provides the common writing operations (rewrite, summarize, continue, fix
grammar, change tone) plus access to the Quill command tools. Defaults to the
Apple Foundation Models backend on macOS; pass a different backend elsewhere.
Calls are blocking — the UI should run them off the main thread.
"""
from __future__ import annotations

from quill.core.ai.backend import AIBackend, ContextWindowExceeded
from quill.core.ai.tools import AITool, build_tools_from_registry, run_tool

# Max characters of input we send in one call; larger inputs are chunked.
_CHUNK_CHARS = 4000
# Document-context budgets to try (chars), shrinking until it fits the window.
_CONTEXT_BUDGETS = (6000, 3000, 1200, 0)

_OPERATION_PROMPTS: dict[str, str] = {
    "rewrite": "Rewrite the following text to be clear and well written. "
    "Return only the rewritten text, with no preamble:\n\n{text}",
    "summarize": "Summarize the following text concisely. "
    "Return only the summary:\n\n{text}",
    "continue": "Continue writing naturally from the following text. "
    "Return only the new continuation:\n\n{text}",
    "fix_grammar": "Correct the spelling and grammar of the following text. "
    "Return only the corrected text:\n\n{text}",
    "shorten": "Make the following text more concise while keeping its meaning. "
    "Return only the shortened text:\n\n{text}",
}


def make_default_backend() -> AIBackend:
    """Pick the best available backend for this platform.

    macOS with Apple Intelligence -> Foundation Models (on-device); otherwise
    (Windows, Linux, or macOS without Apple Intelligence) -> llama.cpp CPU.
    """
    import sys

    if sys.platform == "darwin":
        try:
            from quill.core.ai.foundation_models import FoundationModelsBackend

            fm = FoundationModelsBackend()
            if fm.is_available()[0]:
                return fm
        except Exception:  # noqa: BLE001
            pass
    from quill.core.ai.llama_cpp_backend import LlamaCppBackend

    return LlamaCppBackend()


class Assistant:
    def __init__(self, backend: AIBackend | None = None) -> None:
        if backend is None:
            backend = make_default_backend()
        self.backend = backend
        self._style_preamble = ""

    def set_style_preamble(self, preamble: str) -> None:
        """Condition generation on the user's writing style (empty to disable)."""
        self._style_preamble = preamble or ""

    def _wrap(self, prompt: str) -> str:
        if self._style_preamble:
            return f"{self._style_preamble}\n\n{prompt}"
        return prompt

    def is_available(self) -> tuple[bool, str | None]:
        return self.backend.is_available()

    def available_operations(self) -> list[str]:
        return list(_OPERATION_PROMPTS)

    def transform(self, operation: str, text: str) -> str:
        if operation not in _OPERATION_PROMPTS:
            raise ValueError(f"Unknown operation: {operation}")
        template = _OPERATION_PROMPTS[operation]
        if len(text) <= _CHUNK_CHARS:
            return self.backend.respond(self._wrap(template.format(text=text)))
        # Input is larger than the window: process in chunks.
        chunks = _split_into_chunks(text, _CHUNK_CHARS)
        pieces = [self.backend.respond(self._wrap(template.format(text=c))) for c in chunks]
        if operation == "summarize":
            # Map-reduce: summarize the combined chunk summaries.
            combined = "\n\n".join(pieces)
            if len(combined) > _CHUNK_CHARS:
                combined = combined[:_CHUNK_CHARS]
            return self.backend.respond(self._wrap(template.format(text=combined)))
        return "\n".join(pieces)

    def change_tone(self, text: str, tone: str) -> str:
        prompt = (
            f"Rewrite the following text in a {tone} tone. "
            f"Return only the rewritten text:\n\n{text}"
        )
        return self.backend.respond(self._wrap(prompt))

    def ask(self, prompt: str) -> str:
        return self.backend.respond(self._wrap(prompt))

    def _respond_fitting(self, build_prompt) -> str:
        """Try the prompt with shrinking document context until it fits the window."""
        last_error: Exception | None = None
        for budget in _CONTEXT_BUDGETS:
            try:
                return self.backend.respond(self._wrap(build_prompt(budget)))
            except ContextWindowExceeded as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        return self.backend.respond(self._wrap(build_prompt(0)))

    def _document_context(self, document_text: str, budget: int) -> str:
        document_text = (document_text or "").strip()
        if not document_text or budget <= 0:
            return ""
        return f"\n\nThe current document:\n{document_text[:budget]}"

    def answer(self, user_message: str, document_text: str = "") -> str:
        """A full chat answer (uses the document as context, trimmed to fit)."""
        return self._respond_fitting(
            lambda budget: f"{user_message}{self._document_context(document_text, budget)}"
        )

    def write_for_document(self, user_message: str, document_text: str = "") -> str:
        """Generate substantial content to insert; returns only the text."""
        return self._respond_fitting(
            lambda budget: (
                "Write a complete, well-structured piece for the user's document — use "
                "multiple paragraphs and headings where appropriate, not just a title or "
                "a single line. Return ONLY the text to insert, with no preamble, labels, "
                f"or quotation marks.\n\nRequest: {user_message}"
                f"{self._document_context(document_text, budget)}"
            )
        )

    def rewrite_selection(self, user_message: str, selection_text: str) -> str:
        """Apply an instruction to the selected text; returns only the result.

        Large selections are processed in chunks so they never exceed the window.
        """
        instruction = (
            "Apply this instruction to the text and return ONLY the resulting text, "
            f"with no preamble.\n\nInstruction: {user_message}\n\nText:\n"
        )
        if len(selection_text) <= _CHUNK_CHARS:
            return self.backend.respond(self._wrap(instruction + selection_text))
        chunks = _split_into_chunks(selection_text, _CHUNK_CHARS)
        return "\n".join(self.backend.respond(self._wrap(instruction + c)) for c in chunks)

    def tools(self, registry: object, feature_manager: object | None = None) -> list[AITool]:
        return build_tools_from_registry(registry, feature_manager)

    def run_tool(self, registry: object, name: str) -> None:
        run_tool(registry, name)

    def decide(self, user_message: str, document_text: str, tool_ids):
        """Agentic decision: answer / insert / replace / run a tool.

        Falls back to a plain text answer if the backend can't make structured
        decisions.
        """
        from quill.core.ai.agent import AgentDecision

        decide = getattr(self.backend, "decide", None)
        if decide is None:
            return AgentDecision(action="answer", text=self.ask(user_message))
        return decide(user_message, document_text, tuple(tool_ids), self._style_preamble)


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split text into chunks no larger than max_chars, preferring paragraph
    then line then hard boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        block = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(block) <= max_chars:
            current = block
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            # Paragraph itself too big: hard-split.
            for i in range(0, len(paragraph), max_chars):
                piece = paragraph[i : i + max_chars]
                if len(piece) == max_chars:
                    chunks.append(piece)
                else:
                    current = piece
    if current:
        chunks.append(current)
    return chunks
