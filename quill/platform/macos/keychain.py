"""Secret storage on macOS via the login Keychain.

Replaces the Windows DPAPI module (``quill.platform.windows.dpapi``). Rather
than returning portable ciphertext, secrets live in the Keychain and are
referenced by an account label. A DPAPI-shaped ``protect_secret`` /
``unprotect_secret`` facade is provided for the cross-platform secret layer:
``protect_secret`` stores the value and returns an opaque locator token;
``unprotect_secret`` resolves that token back to the secret.

Uses the ``security`` CLI so there is no third-party dependency.
"""
from __future__ import annotations

import subprocess
import uuid

DEFAULT_SERVICE = "Quill"
_TOKEN_PREFIX = "macos-keychain:"


class KeychainError(RuntimeError):
    pass


def set_secret(account: str, secret: str, service: str = DEFAULT_SERVICE) -> None:
    # -U updates the item if it already exists.
    result = subprocess.run(
        ["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", secret],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise KeychainError(result.stderr.strip() or "security add-generic-password failed")


def get_secret(account: str, service: str = DEFAULT_SERVICE) -> str | None:
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.rstrip("\n")


def delete_secret(account: str, service: str = DEFAULT_SERVICE) -> None:
    subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", account],
        check=False,
        capture_output=True,
        text=True,
    )


# DPAPI-shaped facade -------------------------------------------------------

def protect_secret(secret: str, entropy: bytes = b"quill-credential") -> str:
    """Store ``secret`` in the Keychain and return an opaque locator token."""
    account = f"{entropy.decode('utf-8', 'replace')}.{uuid.uuid4().hex}"
    set_secret(account, secret)
    return f"{_TOKEN_PREFIX}{account}"


def unprotect_secret(encoded: str, entropy: bytes = b"quill-credential") -> str:
    """Resolve a locator token produced by :func:`protect_secret`."""
    if not encoded.startswith(_TOKEN_PREFIX):
        raise KeychainError("Not a macOS Keychain locator token")
    account = encoded[len(_TOKEN_PREFIX):]
    secret = get_secret(account)
    if secret is None:
        raise KeychainError(f"No Keychain item for account {account!r}")
    return secret
