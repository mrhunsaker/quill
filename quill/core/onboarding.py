from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_ONBOARDING_STATE_FILE = "onboarding-complete.json"
_ASSISTANT_ONBOARDING_STATE_FILE = "assistant-onboarding-complete.json"
_SPEECH_ONBOARDING_STATE_FILE = "speech-onboarding-complete.json"
_WATCH_FOLDER_ONBOARDING_STATE_FILE = "watch-folder-onboarding-complete.json"
_GLOW_ONBOARDING_STATE_FILE = "glow-onboarding-complete.json"
_TRUST_CONSENT_STATE_FILE = "trust-consent.json"
_STARTUP_WIZARD_PROMPT_STATE_FILE = "startup-wizard-prompt.json"
_TRUST_CONSENT_VERSION = 1


def onboarding_complete_path() -> Path:
    return app_data_dir() / _ONBOARDING_STATE_FILE


def assistant_onboarding_complete_path() -> Path:
    return app_data_dir() / _ASSISTANT_ONBOARDING_STATE_FILE


def speech_onboarding_complete_path() -> Path:
    return app_data_dir() / _SPEECH_ONBOARDING_STATE_FILE


def watch_folder_onboarding_complete_path() -> Path:
    return app_data_dir() / _WATCH_FOLDER_ONBOARDING_STATE_FILE


def glow_onboarding_complete_path() -> Path:
    return app_data_dir() / _GLOW_ONBOARDING_STATE_FILE


def trust_consent_state_path() -> Path:
    return app_data_dir() / _TRUST_CONSENT_STATE_FILE


def startup_wizard_prompt_state_path() -> Path:
    return app_data_dir() / _STARTUP_WIZARD_PROMPT_STATE_FILE


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


def load_speech_onboarding_complete() -> bool:
    raw = read_json(speech_onboarding_complete_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("completed", False))


def mark_speech_onboarding_complete() -> None:
    write_json_atomic(speech_onboarding_complete_path(), {"completed": True})


def load_glow_onboarding_complete() -> bool:
    raw = read_json(glow_onboarding_complete_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("completed", False))


def mark_glow_onboarding_complete() -> None:
    write_json_atomic(glow_onboarding_complete_path(), {"completed": True})


def load_watch_folder_onboarding_complete() -> bool:
    raw = read_json(watch_folder_onboarding_complete_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("completed", False))


def mark_watch_folder_onboarding_complete() -> None:
    write_json_atomic(watch_folder_onboarding_complete_path(), {"completed": True})


def load_trust_consent_complete() -> bool:
    raw = read_json(trust_consent_state_path(), default={})
    if not isinstance(raw, dict):
        return False
    accepted = bool(raw.get("accepted", False))
    version = int(raw.get("version", 0))
    return accepted and version == _TRUST_CONSENT_VERSION


def mark_trust_consent_complete() -> None:
    write_json_atomic(
        trust_consent_state_path(),
        {
            "accepted": True,
            "version": _TRUST_CONSENT_VERSION,
        },
    )


def load_startup_wizard_prompt_suppressed() -> bool:
    raw = read_json(startup_wizard_prompt_state_path(), default={})
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("suppressed", False))


def mark_startup_wizard_prompt_suppressed() -> None:
    write_json_atomic(startup_wizard_prompt_state_path(), {"suppressed": True})
