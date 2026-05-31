"""Agentic decision types and the safe tool allowlist for the assistant.

The assistant decides, per turn, whether to answer in chat, insert/replace
text, or RUN one Quill command. Only a curated, safe, automatable subset of
commands is offered for 'run' (no destructive or argument-heavy actions),
constrained via guided generation so the model can only pick a valid id.
"""
from __future__ import annotations

from dataclasses import dataclass

ACTIONS = ("answer", "insert", "replace", "run")

# Curated safe, automatable commands the agent may run. Ids must exist in the
# CommandRegistry; unknown/disabled ones are filtered at runtime.
SAFE_TOOL_IDS: tuple[str, ...] = (
    "file.save",
    "file.save_all",
    "file.new",
    "edit.undo",
    "edit.redo",
    "edit.select_all",
    "format.bold",
    "format.italic",
    "format.upper_case",
    "format.lower_case",
    "format.title_case",
    "format.sentence_case",
    "format.insert_bullet_list",
    "format.insert_numbered_list",
    "tools.word_count",
    "tools.spell_check_dialog",
    "tools.read_aloud_start_pause",
    "tools.read_aloud_stop",
    "navigate.next_heading",
    "navigate.previous_heading",
    "navigate.outline_navigator",
    "edit.find",
    "view.toggle_soft_wrap",
    "app.command_palette",
)


@dataclass(frozen=True, slots=True)
class AgentDecision:
    action: str          # one of ACTIONS
    text: str = ""       # for answer / insert / replace
    tool: str = ""       # command id when action == "run"


def allowed_tools(registry: object, feature_manager: object | None = None) -> list[tuple[str, str]]:
    """Return (id, title) for safe tools that actually exist in the registry."""
    available = {c.id: c.title for c in registry.list(feature_manager=feature_manager)}  # type: ignore[attr-defined]
    return [(tid, available[tid]) for tid in SAFE_TOOL_IDS if tid in available]
