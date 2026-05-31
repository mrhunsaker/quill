from __future__ import annotations

import json
from pathlib import Path

import pytest

import quill.core.assistant_ai as assistant_ai


def test_assistant_connection_settings_round_trip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    assistant_ai.save_assistant_connection_settings(
        assistant_ai.AssistantConnectionSettings(
            provider="custom",
            host="http://127.0.0.1:11434",
            model="qwen2.5",
        )
    )

    loaded = assistant_ai.load_assistant_connection_settings()

    assert loaded.provider == "custom"
    assert loaded.host == "http://127.0.0.1:11434"
    assert loaded.model == "qwen2.5"


def test_assistant_api_key_is_protected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(assistant_ai, "protect_secret", lambda secret: f"enc:{secret}")
    monkeypatch.setattr(
        assistant_ai,
        "unprotect_secret",
        lambda secret: secret.removeprefix("enc:"),
    )

    assistant_ai.save_assistant_api_key("secret-value")

    assert assistant_ai.load_assistant_api_key() == "secret-value"


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_settings_accepts_ollama_cloud_provider() -> None:
    settings = assistant_ai.AssistantConnectionSettings.from_dict(
        {
            "provider": "ollama_cloud",
            "host": "https://ollama.com",
            "model": "qwen3",
        }
    )
    assert settings.provider == "ollama_cloud"


def test_list_assistant_models_reads_ollama_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        assistant_ai,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(
            {"models": [{"name": "qwen3"}, {"name": "llama3.2:1b"}]}
        ),
    )
    settings = assistant_ai.AssistantConnectionSettings(provider="ollama", host="http://localhost:11434")
    models, error = assistant_ai.list_assistant_models(settings, api_key="")
    assert error is None
    assert models == ["qwen3", "llama3.2:1b"]


def test_verify_assistant_connection_reports_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Unauthorized(assistant_ai.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                url="https://ollama.com/api/tags",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            )

    def _raise(*_args, **_kwargs):
        raise _Unauthorized()

    monkeypatch.setattr(assistant_ai, "urlopen", _raise)
    settings = assistant_ai.AssistantConnectionSettings(
        provider="ollama_cloud",
        host="https://ollama.com",
        model="qwen3",
    )
    ok, message = assistant_ai.verify_assistant_connection(settings, api_key="bad-key")
    assert ok is False
    assert "Authentication failed" in message


def test_recommended_models_for_provider_prefers_known_defaults() -> None:
    local = assistant_ai.recommended_models_for_provider("ollama")
    cloud = assistant_ai.recommended_models_for_provider("ollama_cloud")
    assert local[0].startswith("llama3.2")
    assert "qwen3" in cloud
