from __future__ import annotations

from quill.ui.assistant_panel import classify_assistant_error


def test_classify_assistant_error_native_loader_failure() -> None:
    message, disable_chat = classify_assistant_error(
        "llama-cpp-python failed to load native code on this machine "
        "(Windows error 0xc000001d). Install a CPU-compatible build or disable AI."
    )

    assert "0xc000001d" in message
    assert "turn AI off" in message
    assert disable_chat is True


def test_classify_assistant_error_generic() -> None:
    message, disable_chat = classify_assistant_error("temporary network issue")

    assert message == "Error: temporary network issue"
    assert disable_chat is False
