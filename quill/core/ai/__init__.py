"""On-device AI for Quill.

macOS uses Apple Foundation Models (via the official ``apple-fm-sdk``); other
platforms can plug a different backend (e.g. llama.cpp) behind the same
``AIBackend`` interface. Tools are generated from Quill's ``CommandRegistry``
so the assistant can do anything the user can do in the app (see issue #40).
"""
from quill.core.ai.assistant import Assistant
from quill.core.ai.backend import AIBackend
from quill.core.ai.tools import AITool, build_tools_from_registry, run_tool

__all__ = ["Assistant", "AIBackend", "AITool", "build_tools_from_registry", "run_tool"]
