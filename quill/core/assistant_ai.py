from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic
from quill.platform.windows.dpapi import protect_secret, unprotect_secret

_ASSISTANT_CONNECTION_FILE = "assistant-connection.json"
_ASSISTANT_SECRET_FILE = "assistant-secret.json"
_SUPPORTED_PROVIDERS = {"off", "ollama", "ollama_cloud", "custom"}


@dataclass(slots=True)
class AssistantConnectionSettings:
    provider: str = "ollama"
    host: str = "http://localhost:11434"
    model: str = "llama3.1"

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AssistantConnectionSettings:
        provider = str(data.get("provider", "ollama")).strip().lower()
        if provider not in _SUPPORTED_PROVIDERS:
            provider = "ollama"
        host = str(data.get("host", "http://localhost:11434")).strip() or "http://localhost:11434"
        model = str(data.get("model", "llama3.1")).strip() or "llama3.1"
        return cls(provider=provider, host=host, model=model)


def default_host_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "ollama_cloud":
        return "https://ollama.com"
    return "http://localhost:11434"


def recommended_models_for_provider(provider: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized == "ollama_cloud":
        return ["qwen3", "gpt-oss:20b", "gemma3"]
    if normalized == "ollama":
        return [
            "llama3.2:1b-instruct-q4_K_M",
            "qwen2.5:1.5b-instruct-q4_K_M",
            "qwen2.5:3b-instruct-q4_K_M",
        ]
    return ["qwen3", "gpt-oss:20b", "llama3.2"]


def verify_assistant_connection(
    settings: AssistantConnectionSettings,
    api_key: str,
    *,
    timeout_seconds: float = 8.0,
) -> tuple[bool, str]:
    provider = settings.provider.strip().lower()
    if provider == "off":
        return True, "AI provider is Off."

    models, error = list_assistant_models(settings, api_key, timeout_seconds=timeout_seconds)
    if error is None:
        if models:
            return True, f"Connection verified. Found {len(models)} models."
        return True, "Connection verified."
    return False, error


def list_assistant_models(
    settings: AssistantConnectionSettings,
    api_key: str,
    *,
    timeout_seconds: float = 8.0,
    max_models: int = 200,
) -> tuple[list[str], str | None]:
    provider = settings.provider.strip().lower()
    if provider == "off":
        return [], None

    host = (settings.host or "").strip().rstrip("/")
    if not host:
        host = default_host_for_provider(provider)

    headers = _build_auth_headers(provider, host, api_key)
    candidates = [f"{host}/api/tags", f"{host}/v1/models"]
    errors: list[str] = []

    for endpoint in candidates:
        models, error = _fetch_models_from_endpoint(
            endpoint,
            headers,
            timeout_seconds=timeout_seconds,
            max_models=max_models,
        )
        if error is None:
            return models, None
        errors.append(error)

    if any("401" in item or "403" in item for item in errors):
        return [], "Authentication failed. Check your API key."
    if any("timed out" in item.lower() for item in errors):
        return [], "Connection timed out. Check host URL and network connection."
    return [], errors[-1] if errors else "Could not reach AI endpoint."


def _fetch_models_from_endpoint(
    endpoint: str,
    headers: dict[str, str],
    *,
    timeout_seconds: float,
    max_models: int,
) -> tuple[list[str], str | None]:
    request = Request(endpoint, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        return [], f"HTTP {exc.code} from {endpoint}"
    except URLError as exc:
        return [], f"Failed to reach {endpoint}: {exc.reason}"
    except TimeoutError:
        return [], f"Request timed out for {endpoint}"
    except json.JSONDecodeError:
        return [], f"Invalid JSON from {endpoint}"

    models = _extract_model_names(payload)
    if not models:
        # Empty list is still a valid reachability signal.
        return [], None
    return models[:max_models], None


def _extract_model_names(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []

    names: list[str] = []
    models = payload.get("models")
    if isinstance(models, list):
        for item in models:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    names.append(name)

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = str(item.get("id", "")).strip()
                if name:
                    names.append(name)

    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _build_auth_headers(provider: str, host: str, api_key: str) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    secret = api_key.strip()
    if not secret:
        return headers

    parsed = urlparse(host)
    is_https = parsed.scheme.lower() == "https"
    is_ollama_cloud = "ollama.com" in parsed.netloc.lower()
    if provider in {"custom", "ollama_cloud"} or (is_https and is_ollama_cloud):
        headers["Authorization"] = f"Bearer {secret}"
    return headers


def assistant_connection_path() -> Path:
    return app_data_dir() / _ASSISTANT_CONNECTION_FILE


def assistant_secret_path() -> Path:
    return app_data_dir() / _ASSISTANT_SECRET_FILE


def load_assistant_connection_settings() -> AssistantConnectionSettings:
    raw = read_json(assistant_connection_path(), default={})
    if not isinstance(raw, dict):
        return AssistantConnectionSettings()
    return AssistantConnectionSettings.from_dict(raw)


def save_assistant_connection_settings(settings: AssistantConnectionSettings) -> None:
    write_json_atomic(assistant_connection_path(), asdict(settings))


def load_assistant_api_key() -> str:
    raw = read_json(assistant_secret_path(), default={})
    if not isinstance(raw, dict):
        return ""
    encrypted = str(raw.get("protected_secret", "")).strip()
    if not encrypted:
        return ""
    return unprotect_secret(encrypted)


def save_assistant_api_key(api_key: str) -> None:
    secret = api_key.strip()
    path = assistant_secret_path()
    if not secret:
        if path.exists():
            path.unlink()
        return
    write_json_atomic(path, {"protected_secret": protect_secret(secret)})
