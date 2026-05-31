from __future__ import annotations

import quill.core.assistant_agents as assistant_agents


def test_find_agent_profile_is_case_insensitive() -> None:
    profile = assistant_agents.find_agent_profile("ReWrItE")
    assert profile is not None
    assert profile.agent_id == "rewrite"


def test_build_agent_plan_returns_defaults_and_checks() -> None:
    plan = assistant_agents.build_agent_plan(
        "summarize",
        selection_text="Selected text.",
        document_text="",
        goal="",
        audience="",
        tone="",
    )
    assert plan is not None
    assert plan.profile.agent_id == "summarize"
    assert "Help me complete this writing task." in plan.prompt
    assert "General readers" in plan.prompt
    assert "Clear and practical" in plan.prompt
    assert "Preview changes before applying." in plan.checks


def test_build_agent_plan_returns_none_for_unknown_agent() -> None:
    assert (
        assistant_agents.build_agent_plan(
            "not-a-real-agent",
            selection_text="text",
            document_text="doc",
        )
        is None
    )
