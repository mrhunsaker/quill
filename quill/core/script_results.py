"""Result and error types for the QUILL scripting / developer console."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScriptSuccess:
    """A successful console execution."""

    value: object = None
    output: str = ""  # captured stdout/stderr printed by user code


@dataclass(frozen=True, slots=True)
class ScriptError:
    """A failed console execution."""

    message: str  # plain-language first
    detail: str = ""  # technical traceback, collapsed by default
    suggestion: str = ""


ScriptResult = ScriptSuccess | ScriptError
