"""Personal writing-style profile for the AI.

Captures the user's writing samples, distills them (via the on-device model)
into a concise style guide, and produces a preamble that conditions the
assistant to write in the user's voice. Stored locally in app data.

This is prompt-based style conditioning (works today, on-device, no training).
A future option is training a Foundation Models LoRA adapter from the samples.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_MAX_SAMPLES = 20
_MAX_SAMPLE_CHARS = 4000
_GUIDE_SAMPLE_BUDGET = 8000

_GUIDE_PROMPT = (
    "Analyze these writing samples from one author and produce a concise STYLE GUIDE "
    "(5-8 short bullet points) capturing their voice: tone, formality, typical sentence "
    "length, vocabulary, punctuation habits, and any quirks. Return only the bullet "
    "points, no preamble.\n\nSamples:\n\n{samples}"
)


@dataclass(slots=True)
class StyleProfile:
    enabled: bool = False
    samples: list[str] = field(default_factory=list)
    guide: str = ""

    def to_dict(self) -> dict:
        return {"enabled": self.enabled, "samples": self.samples, "guide": self.guide}


def style_path() -> Path:
    return app_data_dir() / "ai" / "writing-style.json"


def load_style() -> StyleProfile:
    raw = read_json(style_path(), default={})
    if not isinstance(raw, dict):
        return StyleProfile()
    samples = raw.get("samples", [])
    if not isinstance(samples, list):
        samples = []
    return StyleProfile(
        enabled=bool(raw.get("enabled", False)),
        samples=[str(s) for s in samples][:_MAX_SAMPLES],
        guide=str(raw.get("guide", "")),
    )


def save_style(profile: StyleProfile) -> None:
    write_json_atomic(style_path(), profile.to_dict())


def add_sample(profile: StyleProfile, text: str) -> StyleProfile:
    text = (text or "").strip()
    if text:
        profile.samples.append(text[:_MAX_SAMPLE_CHARS])
        profile.samples = profile.samples[-_MAX_SAMPLES:]
    return profile


def build_guide(assistant: object, profile: StyleProfile) -> str:
    """Use the on-device model to distill a style guide from the samples."""
    if not profile.samples:
        return ""
    joined = "\n\n---\n\n".join(profile.samples)[:_GUIDE_SAMPLE_BUDGET]
    guide = assistant.ask(_GUIDE_PROMPT.format(samples=joined))  # type: ignore[attr-defined]
    profile.guide = guide.strip()
    return profile.guide


def style_preamble(profile: StyleProfile) -> str:
    """Preamble to prepend to generation prompts when style is enabled."""
    if not profile.enabled or not profile.guide:
        return ""
    return (
        "Match the user's personal voice using the style guide below. Apply it to "
        "TONE, word choice, and rhythm only. Do NOT use it as a reason to shorten, "
        "omit, or skip content — always fully complete the requested task at the "
        f"length it deserves.\n\nStyle guide:\n{profile.guide}"
    )
