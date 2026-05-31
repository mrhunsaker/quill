from __future__ import annotations

from pathlib import Path

import pytest

import quill.core.assistant_prompts as assistant_prompts


def test_custom_prompt_round_trip_and_tag_dedup() -> None:
    prompt = assistant_prompts.CustomPrompt.from_dict(
        {
            "id": "p-1",
            "title": "  Refine Draft  ",
            "template": "Rewrite {selection}",
            "tags": ["editing", "editing", " style "],
            "favorite": True,
            "shortcut": "ctrl+alt+r",
        }
    )
    assert prompt.prompt_id == "p-1"
    assert prompt.title == "Refine Draft"
    assert prompt.tags == ("editing", "style")
    payload = prompt.to_dict()
    assert payload["id"] == "p-1"
    assert payload["tags"] == ["editing", "style"]


def test_template_variables_and_unknown_detection() -> None:
    template = "Goal: {goal} / Audience: {audience} / Extra: {region}"
    assert assistant_prompts.template_variables(template) == ["goal", "audience", "region"]
    assert assistant_prompts.unknown_template_variables(template) == ["region"]


def test_render_prompt_template_uses_known_context_values() -> None:
    rendered = assistant_prompts.render_prompt_template(
        "Tone {tone}; Selection {selection}; Goal {goal}",
        values={"selection": "Draft", "tone": "Direct", "goal": "Polish"},
    )
    assert rendered == "Tone Direct; Selection Draft; Goal Polish"


def test_load_save_upsert_delete_custom_prompts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    prompts = [
        assistant_prompts.CustomPrompt(
            prompt_id="p-2",
            title="Beta",
            template="T {selection}",
            tags=("one",),
        ),
        assistant_prompts.CustomPrompt(
            prompt_id="p-1",
            title="Alpha",
            template="U {selection}",
        ),
    ]
    assistant_prompts.save_custom_prompts(prompts)
    loaded = assistant_prompts.load_custom_prompts()
    assert [item.prompt_id for item in loaded] == ["p-1", "p-2"]

    updated = assistant_prompts.upsert_custom_prompt(
        assistant_prompts.CustomPrompt(
            prompt_id="p-1",
            title="Alpha Updated",
            template="Rewrite {selection}",
            favorite=True,
        )
    )
    assert any(item.title == "Alpha Updated" and item.favorite for item in updated)

    remaining = assistant_prompts.delete_custom_prompt("p-2")
    assert [item.prompt_id for item in remaining] == ["p-1"]
