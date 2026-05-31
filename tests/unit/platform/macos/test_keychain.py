from __future__ import annotations

import sys
import uuid

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS Keychain (security CLI) is macOS-only")

from quill.platform.macos import keychain


def test_keychain_round_trip() -> None:
    account = f"quill-test-{uuid.uuid4().hex}"
    try:
        keychain.set_secret(account, "hunter2")
        assert keychain.get_secret(account) == "hunter2"
    finally:
        keychain.delete_secret(account)
    assert keychain.get_secret(account) is None


def test_protect_unprotect_facade() -> None:
    token = keychain.protect_secret("super-secret")
    try:
        assert token.startswith("macos-keychain:")
        assert keychain.unprotect_secret(token) == "super-secret"
    finally:
        keychain.delete_secret(token[len("macos-keychain:"):])
