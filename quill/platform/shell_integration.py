"""Platform-neutral shell/file-type integration (routes to the OS implementation)."""
from __future__ import annotations

import sys

if sys.platform == "darwin":
    from quill.platform.macos.shell_integration import (
        build_shell_integration_plan,
        install_shell_integration,
        launcher_command,
        remove_shell_integration,
    )
elif sys.platform.startswith("win"):
    from quill.platform.windows.shell_integration import (
        build_shell_integration_plan,
        install_shell_integration,
        launcher_command,
        remove_shell_integration,
    )
else:  # pragma: no cover - other platforms
    from dataclasses import dataclass

    @dataclass(frozen=True, slots=True)
    class _PlanEntry:
        path: str

    def launcher_command() -> str:
        return "quill"

    def build_shell_integration_plan(command: str | None = None) -> list[_PlanEntry]:
        return []

    def install_shell_integration(command: str | None = None) -> None:
        return None

    def remove_shell_integration() -> None:
        return None


__all__ = [
    "build_shell_integration_plan",
    "install_shell_integration",
    "launcher_command",
    "remove_shell_integration",
]
