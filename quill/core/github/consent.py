"""GitHub network-access consent state (one-time user confirmation)."""

from __future__ import annotations

from pathlib import Path

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

_CONSENT_FILE = "github_consent.json"


def load_github_consent_complete() -> bool:
    """Return True if the user has already accepted the GitHub access notice."""
    path = _consent_path()
    data = read_json(path) if path.exists() else {}
    return bool(data.get("accepted", False))


def save_github_consent_complete() -> None:
    """Record that the user accepted the GitHub access consent notice."""
    write_json_atomic(_consent_path(), {"accepted": True})


def _consent_path() -> Path:
    return app_data_dir() / _CONSENT_FILE
