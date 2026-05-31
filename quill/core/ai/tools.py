"""Expose Quill's commands to the AI as callable tools.

Every registered command becomes a tool (name = command id, description =
human title), so the assistant can perform anything the user can do via the
Command Palette/menus. Content tools (read/insert text) are layered on top by
the UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AITool:
    name: str          # command id, e.g. "format.heading_1"
    description: str    # human-readable title


def build_tools_from_registry(registry: object, feature_manager: object | None = None) -> list[AITool]:
    commands = registry.list(feature_manager=feature_manager)  # type: ignore[attr-defined]
    return [AITool(name=c.id, description=c.title) for c in commands]


def run_tool(registry: object, name: str) -> None:
    registry.run(name)  # type: ignore[attr-defined]
