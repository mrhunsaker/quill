from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from string import Formatter
from uuid import uuid4

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_PROMPTS_FILE = "assistant-prompts.json"
_KNOWN_VARIABLES = {"selection", "document", "tone", "audience", "goal"}


@dataclass(slots=True, frozen=True)
class CustomPrompt:
    prompt_id: str
    title: str
    template: str
    tags: tuple[str, ...] = ()
    favorite: bool = False
    shortcut: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> CustomPrompt:
        prompt_id = str(payload.get("id", "")).strip() or generate_prompt_id()
        title = str(payload.get("title", "")).strip() or "Untitled prompt"
        template = str(payload.get("template", "")).strip()
        raw_tags = payload.get("tags", [])
        tags: list[str] = []
        if isinstance(raw_tags, list):
            for value in raw_tags:
                tag = str(value).strip()
                if tag and tag not in tags:
                    tags.append(tag)
        favorite = bool(payload.get("favorite", False))
        shortcut = str(payload.get("shortcut", "")).strip()
        return cls(
            prompt_id=prompt_id,
            title=title,
            template=template,
            tags=tuple(tags),
            favorite=favorite,
            shortcut=shortcut,
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["id"] = payload.pop("prompt_id")
        payload["tags"] = list(self.tags)
        return payload


def prompts_path() -> Path:
    return app_data_dir() / "ai" / _PROMPTS_FILE


def generate_prompt_id() -> str:
    return f"prompt-{uuid4().hex[:12]}"


def load_custom_prompts() -> list[CustomPrompt]:
    payload = read_json(prompts_path(), default={})
    if not isinstance(payload, dict):
        return []
    raw_prompts = payload.get("prompts", [])
    if not isinstance(raw_prompts, list):
        return []
    prompts: list[CustomPrompt] = []
    seen: set[str] = set()
    for item in raw_prompts:
        if not isinstance(item, dict):
            continue
        prompt = CustomPrompt.from_dict(item)
        if prompt.prompt_id in seen:
            continue
        seen.add(prompt.prompt_id)
        if not prompt.template:
            continue
        prompts.append(prompt)
    prompts.sort(key=lambda value: value.title.lower())
    return prompts


def save_custom_prompts(prompts: list[CustomPrompt]) -> None:
    payload = {"prompts": [prompt.to_dict() for prompt in prompts]}
    write_json_atomic(prompts_path(), payload)


def upsert_custom_prompt(prompt: CustomPrompt) -> list[CustomPrompt]:
    prompts = load_custom_prompts()
    updated: list[CustomPrompt] = []
    replaced = False
    for existing in prompts:
        if existing.prompt_id == prompt.prompt_id:
            updated.append(prompt)
            replaced = True
        else:
            updated.append(existing)
    if not replaced:
        updated.append(prompt)
    updated.sort(key=lambda value: value.title.lower())
    save_custom_prompts(updated)
    return updated


def delete_custom_prompt(prompt_id: str) -> list[CustomPrompt]:
    normalized = prompt_id.strip()
    prompts = [prompt for prompt in load_custom_prompts() if prompt.prompt_id != normalized]
    save_custom_prompts(prompts)
    return prompts


def template_variables(template: str) -> list[str]:
    found: list[str] = []
    for _literal, name, _spec, _conv in Formatter().parse(template):
        if not name:
            continue
        normalized = name.strip()
        if normalized and normalized not in found:
            found.append(normalized)
    return found


def unknown_template_variables(template: str) -> list[str]:
    return [name for name in template_variables(template) if name not in _KNOWN_VARIABLES]


def render_prompt_template(template: str, *, values: dict[str, str]) -> str:
    context = {
        "selection": values.get("selection", ""),
        "document": values.get("document", ""),
        "tone": values.get("tone", ""),
        "audience": values.get("audience", ""),
        "goal": values.get("goal", ""),
    }
    return template.format(**context).strip()
