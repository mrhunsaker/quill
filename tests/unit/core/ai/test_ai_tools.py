from __future__ import annotations

from quill.core.ai.tools import AITool, build_tools_from_registry, run_tool


class _FakeCommand:
    def __init__(self, cid: str, title: str) -> None:
        self.id = cid
        self.title = title


class _FakeRegistry:
    def __init__(self) -> None:
        self.ran: list[str] = []
        self._cmds = [_FakeCommand("format.heading_1", "Heading 1"),
                      _FakeCommand("edit.undo", "Undo")]

    def list(self, feature_manager=None):
        return self._cmds

    def run(self, command_id: str) -> None:
        self.ran.append(command_id)


def test_build_tools_from_registry_maps_commands() -> None:
    reg = _FakeRegistry()
    tools = build_tools_from_registry(reg)
    assert tools == [
        AITool(name="format.heading_1", description="Heading 1"),
        AITool(name="edit.undo", description="Undo"),
    ]


def test_run_tool_invokes_registry() -> None:
    reg = _FakeRegistry()
    run_tool(reg, "edit.undo")
    assert reg.ran == ["edit.undo"]
