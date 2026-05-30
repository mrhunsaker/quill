"""llama.cpp backend (CPU, in-process) for Windows and other non-macOS systems.

Uses ``llama-cpp-python`` to run a local GGUF model entirely on the CPU — no
GPU, no server, no cloud (per issue #40). Optional dependency: if it or a model
isn't present, it reports unavailable and the UI degrades gracefully.

Model resolution order:
  1. ``QUILL_LLAMA_MODEL`` environment variable (path to a .gguf), then
  2. the first ``*.gguf`` found in ``<app data>/models``.
Recommended default model: Phi-4-mini (Q4); Llama 3.2 1B for low-end machines.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from quill.core.ai.agent import ACTIONS, AgentDecision
from quill.core.ai.backend import AIBackend, ContextWindowExceeded
from quill.core.paths import app_data_dir

_N_CTX = 4096
_MAX_TOKENS = 1024


def _models_dir() -> Path:
    return app_data_dir() / "models"


def default_model_path() -> str | None:
    override = os.environ.get("QUILL_LLAMA_MODEL")
    if override and Path(override).expanduser().exists():
        return str(Path(override).expanduser())
    models = _models_dir()
    if models.exists():
        for candidate in sorted(models.glob("*.gguf")):
            return str(candidate)
    return None


class LlamaCppBackend(AIBackend):
    name = "llama.cpp (local CPU)"

    def __init__(self, model_path: str | None = None, n_ctx: int = _N_CTX) -> None:
        self._model_path = model_path or default_model_path()
        self._n_ctx = n_ctx
        self._llm = None

    def _load(self):
        if self._llm is None:
            from llama_cpp import Llama  # type: ignore[import-not-found]

            self._llm = Llama(model_path=self._model_path, n_ctx=self._n_ctx, verbose=False)
        return self._llm

    def is_available(self) -> tuple[bool, str | None]:
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            return False, "llama-cpp-python is not installed (pip install llama-cpp-python)"
        if not self._model_path or not Path(self._model_path).exists():
            return False, (
                "No GGUF model found. Set QUILL_LLAMA_MODEL or place a .gguf file in "
                f"{_models_dir()} (e.g. Phi-4-mini Q4)."
            )
        return True, None

    def _complete(self, messages: list[dict], response_format: dict | None = None) -> str:
        llm = self._load()
        kwargs: dict = {"messages": messages, "max_tokens": _MAX_TOKENS}
        if response_format is not None:
            kwargs["response_format"] = response_format
        try:
            out = llm.create_chat_completion(**kwargs)
        except ValueError as exc:
            if "context" in str(exc).lower() or "token" in str(exc).lower():
                raise ContextWindowExceeded(str(exc)) from exc
            raise
        return out["choices"][0]["message"]["content"].strip()

    def respond(self, prompt: str) -> str:
        return self._complete([{"role": "user", "content": prompt}])

    def decide(
        self,
        user_message: str,
        document_text: str,
        tool_ids: tuple[str, ...],
        style_preamble: str = "",
    ) -> AgentDecision:
        # JSON-constrained decision (llama.cpp supports JSON response_format).
        system = (
            "You are Quill's editor assistant. Decide how to handle the user's request "
            "about the single document they are editing. Reply with a JSON object: "
            '{"action": one of ' + json.dumps(list(ACTIONS)) + ', "text": string, "tool": '
            "string}. action=answer replies in chat; insert=new text for the cursor; "
            "replace=rewrites the selection; run=run ONE tool id. tool must be one of: "
            + json.dumps(list(tool_ids))
            + " (empty unless action is run)."
        )
        if style_preamble:
            system = f"{system}\n\n{style_preamble}"
        for budget in (6000, 3000, 1200, 0):
            context = document_text[:budget]
            try:
                raw = self._complete(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Request: {user_message}\n\nDocument:\n{context}"},
                    ],
                    response_format={"type": "json_object"},
                )
                break
            except ContextWindowExceeded:
                if budget == 0:
                    return AgentDecision(action="answer", text="")
                continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return AgentDecision(action="answer", text=raw)
        action = data.get("action") if data.get("action") in ACTIONS else "answer"
        tool = data.get("tool", "") if action == "run" and data.get("tool") in tool_ids else ""
        if action == "run" and not tool:
            action = "answer"
        return AgentDecision(action=action, text=str(data.get("text") or ""), tool=tool)
