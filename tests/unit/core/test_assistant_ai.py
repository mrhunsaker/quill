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
            provider="openai",
            host="https://api.openai.com",
            model="gpt-4o-mini",
        )
    )
    loaded = assistant_ai.load_assistant_connection_settings()
    assert loaded.provider == "openai"
    assert loaded.host == "https://api.openai.com"
    assert loaded.model == "gpt-4o-mini"


def test_assistant_api_key_is_protected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(assistant_ai, "_save_api_key_with_credential_manager", lambda *_args: False)
    monkeypatch.setattr(assistant_ai, "_load_api_key_from_credential_manager", lambda: "")
    monkeypatch.setattr(assistant_ai, "protect_secret", lambda secret: f"enc:{secret}")
    monkeypatch.setattr(
        assistant_ai,
        "unprotect_secret",
        lambda secret: secret.removeprefix("enc:"),
    )
    assistant_ai.save_assistant_api_key("secret-value")
    assert assistant_ai.load_assistant_api_key() == "secret-value"


def test_assistant_api_key_prefers_credential_manager(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    saved: dict[str, str] = {}

    def _save(secret: str) -> bool:
        saved["secret"] = secret
        return True

    monkeypatch.setattr(assistant_ai, "_save_api_key_with_credential_manager", _save)
    monkeypatch.setattr(
        assistant_ai,
        "_load_api_key_from_credential_manager",
        lambda: saved.get("secret", ""),
    )
    assistant_ai.save_assistant_api_key("vault-secret")
    assert assistant_ai.load_assistant_api_key() == "vault-secret"
    assert not assistant_ai.assistant_secret_path().exists()


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.parametrize(
    ("provider", "expected_host"),
    [
        ("openai", "https://api.openai.com"),
        ("claude", "https://api.anthropic.com"),
        ("openrouter", "https://openrouter.ai/api"),
        ("gemini", "https://generativelanguage.googleapis.com"),
        ("azure_openai", "https://YOUR-RESOURCE-NAME.openai.azure.com"),
    ],
)
def test_default_host_for_provider(provider: str, expected_host: str) -> None:
    assert assistant_ai.default_host_for_provider(provider) == expected_host


def test_settings_accepts_new_provider() -> None:
    settings = assistant_ai.AssistantConnectionSettings.from_dict(
        {
            "provider": "gemini",
            "host": "https://generativelanguage.googleapis.com",
            "model": "gemini-2.0-flash",
        }
    )
    assert settings.provider == "gemini"


def test_list_assistant_models_reads_openai_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        assistant_ai,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(
            {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4.1"}]}
        ),
    )
    settings = assistant_ai.AssistantConnectionSettings(provider="openai", host="https://api.openai.com")
    models, error = assistant_ai.list_assistant_models(settings, api_key="x")
    assert error is None
    assert models == ["gpt-4o-mini", "gpt-4.1"]


def test_verify_assistant_connection_reports_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Unauthorized(assistant_ai.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                url="https://api.openai.com/v1/models",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            )

    def _raise(*_args, **_kwargs):
        raise _Unauthorized()

    monkeypatch.setattr(assistant_ai, "urlopen", _raise)
    settings = assistant_ai.AssistantConnectionSettings(
        provider="openai",
        host="https://api.openai.com",
        model="gpt-4o-mini",
    )
    ok, message = assistant_ai.verify_assistant_connection(settings, api_key="bad-key")
    assert ok is False
    assert "Authentication failed" in message


def test_verify_assistant_connection_rejects_non_https_cloud_endpoint() -> None:
    settings = assistant_ai.AssistantConnectionSettings(
        provider="openai",
        host="http://api.openai.com",
        model="gpt-4o-mini",
    )
    ok, message = assistant_ai.verify_assistant_connection(settings, api_key="bad-key")
    assert ok is False
    assert "Only HTTPS endpoints are allowed" in message


def test_verify_assistant_connection_allows_local_custom_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        assistant_ai,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse({"data": [{"id": "llama3.1:8b"}]}),
    )
    settings = assistant_ai.AssistantConnectionSettings(
        provider="custom",
        host="http://localhost:11434",
        model="llama3.1:8b",
    )
    ok, message = assistant_ai.verify_assistant_connection(settings, api_key="")
    assert ok is True
    assert "Connection verified" in message


def test_build_auth_headers_for_provider_types() -> None:
    assert "Authorization" in assistant_ai._build_auth_headers(
        "openai", "https://api.openai.com", "sk-1"
    )
    claude_headers = assistant_ai._build_auth_headers(
        "claude", "https://api.anthropic.com", "claude-key"
    )
    assert claude_headers["x-api-key"] == "claude-key"
    assert claude_headers["anthropic-version"] == "2023-06-01"
    gemini_headers = assistant_ai._build_auth_headers(
        "gemini", "https://generativelanguage.googleapis.com", "gem-key"
    )
    assert gemini_headers["x-goog-api-key"] == "gem-key"
    azure_headers = assistant_ai._build_auth_headers(
        "azure_openai", "https://example.openai.azure.com", "az-key"
    )
    assert azure_headers["api-key"] == "az-key"


def test_filter_model_names_prioritizes_prefix_matches() -> None:
    models = ["gpt-4o-mini", "claude-3-5-sonnet-latest", "gpt-4.1", "gemini-2.0-flash"]
    filtered = assistant_ai.filter_model_names(models, "gpt")
    assert filtered[0] == "gpt-4.1"
    assert "gpt-4o-mini" in filtered
    assert "claude-3-5-sonnet-latest" not in filtered


def test_recommended_models_for_provider_cloud_and_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(assistant_ai, "total_ram_gb", lambda: 6.0)
    local = assistant_ai.recommended_models_for_provider("ollama")
    assert local[0] == "llama3.2:1b-instruct-q4_K_M"
    cloud = assistant_ai.recommended_models_for_provider("openai")
    assert "gpt-4o-mini" in cloud


def test_recommended_model_guidance_returns_framing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(assistant_ai, "total_ram_gb", lambda: 16.0)
    guidance = assistant_ai.recommended_model_guidance("ollama")
    assert guidance
    assert guidance[0].framing != ""
