from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_ONBOARDING_STATE_FILE = "onboarding-complete.json"
_ASSISTANT_ONBOARDING_STATE_FILE = "assistant-onboarding-complete.json"


def onboarding_complete_path() -> Path:
    return app_data_dir() / _ONBOARDING_STATE_FILE


def assistant_onboarding_complete_path() -> Path:
    return app_data_dir() / _ASSISTANT_ONBOARDING_STATE_FILE


def load_onboarding_complete() -> bool:
    raw = read_json(onboarding_complete_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("completed", False))


def mark_onboarding_complete() -> None:
    write_json_atomic(onboarding_complete_path(), {"completed": True})


def load_assistant_onboarding_complete() -> bool:
    raw = read_json(assistant_onboarding_complete_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("completed", False))


def mark_assistant_onboarding_complete() -> None:
    write_json_atomic(assistant_onboarding_complete_path(), {"completed": True})
