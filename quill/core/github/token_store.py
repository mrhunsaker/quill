"""Secure GitHub token storage backed by Windows Credential Manager (DPAPI)."""

from __future__ import annotations

import sys

_CRED_NAME = "quill-github-token"


def load_github_token() -> str | None:
    """Return the stored token, or None if none is stored or not on Windows."""
    if sys.platform != "win32":
        return None
    try:
        from quill.platform.windows.credential_manager import load_generic_credential

        cred = load_generic_credential(_CRED_NAME)
        return cred.secret if cred else None
    except Exception:  # noqa: BLE001 - credential errors are non-fatal
        return None


def save_github_token(token: str) -> bool:
    """Persist *token* in the Windows Credential Manager. Returns True on success."""
    if sys.platform != "win32":
        return False
    try:
        from quill.platform.windows.credential_manager import save_generic_credential

        save_generic_credential(_CRED_NAME, token)
        return True
    except Exception:  # noqa: BLE001
        return False


def delete_github_token() -> bool:
    """Remove any stored GitHub token. Returns True if a token was deleted."""
    if sys.platform != "win32":
        return False
    try:
        from quill.platform.windows.credential_manager import delete_generic_credential

        return delete_generic_credential(_CRED_NAME)
    except Exception:  # noqa: BLE001
        return False
