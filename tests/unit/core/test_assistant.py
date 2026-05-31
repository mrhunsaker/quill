from __future__ import annotations

from quill.core.assistant import (
    assistant_prompt_presets,
    build_assistant_tools,
    rank_assistant_tools,
    render_assistant_prompt,
)
from quill.core.commands import CommandRegistry
from quill.core.features import FeatureManager


def test_assistant_tool_catalog_includes_registered_commands() -> None:
    registry = CommandRegistry()
    registry.register("edit.find", "Find", lambda: None)
    registry.register("tools.run_python", "Run Python", lambda: None)

    tools = build_assistant_tools(registry, FeatureManager())

    assert any(tool.command_id == "edit.find" for tool in tools)
    assert any(tool.command_id == "tools.run_python" for tool in tools)
    assert any(tool.name == "run_python" for tool in tools)


def test_assistant_tool_ranking_prefers_python_matches() -> None:
    registry = CommandRegistry()
    registry.register("edit.find", "Find", lambda: None)
    registry.register("tools.run_python", "Run Python", lambda: None)

    tools = build_assistant_tools(registry, FeatureManager())
    ranked = rank_assistant_tools("python", tools, limit=3)

    assert ranked[0].command_id == "tools.run_python"


def test_assistant_prompt_presets_include_rewrite_and_summary() -> None:
    presets = assistant_prompt_presets()

    assert {preset.name for preset in presets} >= {"rewrite", "summarize", "grammar"}


def test_assistant_prompt_rendering_includes_selection_text() -> None:
    prompt = render_assistant_prompt("rewrite", selection_text="hello world")

    assert "hello world" in prompt
