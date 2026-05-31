from __future__ import annotations

import builtins

from quill.core.ai.llama_cpp_backend import LlamaCppBackend


def _patched_import(
    monkeypatch,
    side_effect: Exception,
) -> None:
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals=None,  # noqa: A002
        locals=None,  # noqa: A002
        fromlist=(),
        level: int = 0,
    ):
        if name == "llama_cpp":
            raise side_effect
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_is_available_reports_missing_dependency(monkeypatch) -> None:
    _patched_import(monkeypatch, ImportError("missing llama_cpp"))
    available, reason = LlamaCppBackend().is_available()
    assert available is False
    assert reason is not None
    assert "not installed" in reason


def test_is_available_reports_native_loader_failure(monkeypatch) -> None:
    _patched_import(monkeypatch, OSError(-1073741795, "Windows Error 0xc000001d"))
    available, reason = LlamaCppBackend().is_available()
    assert available is False
    assert reason is not None
    assert "0xc000001d" in reason


def test_load_raises_runtime_error_for_native_loader_failure(monkeypatch) -> None:
    _patched_import(monkeypatch, OSError(-1073741795, "Windows Error 0xc000001d"))
    backend = LlamaCppBackend(model_path="dummy.gguf")
    try:
        backend._load()
    except RuntimeError as exc:
        assert "0xc000001d" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for native loader failure")
