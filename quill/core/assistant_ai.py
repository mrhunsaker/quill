from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from quill.core.ai.model_manager import total_ram_gb
from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic
from quill.platform.windows.credential_manager import (
    credential_manager_available,
    delete_generic_credential,
    load_generic_credential,
    save_generic_credential,
)
from quill.platform.windows.dpapi import protect_secret, unprotect_secret

_ASSISTANT_CONNECTION_FILE = "assistant-connection.json"
_ASSISTANT_SECRET_FILE = "assistant-secret.json"
_ASSISTANT_CREDENTIAL_TARGET = "QUILL:assistant:api-key"
_SUPPORTED_PROVIDERS = {
    "off",
    "ollama",
    "ollama_cloud",
    "openai",
    "claude",
    "openrouter",
    "gemini",
    "azure_openai",
    "custom",
}
_CLOUD_PROVIDERS = frozenset(
    {"openai", "claude", "openrouter", "gemini", "azure_openai", "ollama_cloud"}
)


@dataclass(slots=True)
class ModelRecommendation:
    model: str
    framing: str
    reason: str


@dataclass(slots=True)
class AssistantConnectionSettings:
    provider: str = "ollama"
    host: str = "http://localhost:11434"
    model: str = "llama3.2:1b-instruct-q4_K_M"

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AssistantConnectionSettings:
        provider = str(data.get("provider", "ollama")).strip().lower()
        if provider not in _SUPPORTED_PROVIDERS:
            provider = "ollama"
        host = (
            str(data.get("host", default_host_for_provider(provider))).strip()
            or default_host_for_provider(provider)
        )
        model = (
            str(data.get("model", default_model_for_provider(provider))).strip()
            or default_model_for_provider(provider)
        )
        return cls(provider=provider, host=host, model=model)


def default_host_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "https://api.openai.com"
    if normalized == "claude":
        return "https://api.anthropic.com"
    if normalized == "openrouter":
        return "https://openrouter.ai/api"
    if normalized == "gemini":
        return "https://generativelanguage.googleapis.com"
    if normalized == "azure_openai":
        return "https://YOUR-RESOURCE-NAME.openai.azure.com"
    if normalized == "ollama_cloud":
        return "https://ollama.com"
    if normalized == "custom":
        return "https://api.openai.com"
    if normalized == "off":
        return ""
    return "http://localhost:11434"


def default_model_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "gpt-4o-mini"
    if normalized == "claude":
        return "claude-3-5-sonnet-latest"
    if normalized == "openrouter":
        return "openrouter/auto"
    if normalized == "gemini":
        return "gemini-2.0-flash"
    if normalized == "azure_openai":
        return "gpt-4o-mini"
    if normalized == "ollama_cloud":
        return "qwen3"
    if normalized == "custom":
        return "gpt-4o-mini"
    if normalized == "off":
        return ""
    return "llama3.2:1b-instruct-q4_K_M"


def provider_requires_api_key(provider: str) -> bool:
    normalized = provider.strip().lower()
    return normalized in {
        "ollama_cloud",
        "openai",
        "claude",
        "openrouter",
        "gemini",
        "azure_openai",
        "custom",
    }


def provider_api_key_label(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "OpenAI API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "claude":
        return "Claude API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "openrouter":
        return "OpenRouter API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "gemini":
        return "Google Gemini API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "azure_openai":
        return "Azure OpenAI API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "ollama_cloud":
        return "Ollama Cloud API key (Credential Manager or DPAPI-encrypted fallback)"
    if normalized == "custom":
        return "API key (OpenAI-compatible endpoint; Credential Manager or DPAPI fallback)"
    return "API key (optional; Credential Manager or DPAPI-encrypted fallback)"


def provider_help_text(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "ollama":
        return "Local Ollama: no key required. Best for private on-device workflows."
    if normalized == "openai":
        return "OpenAI: default host is prefilled. Add key and list models."
    if normalized == "claude":
        return "Claude: default host is prefilled and model discovery is supported."
    if normalized == "openrouter":
        return "OpenRouter: broad model routing with a single key."
    if normalized == "gemini":
        return "Gemini: default Google API endpoint is prefilled."
    if normalized == "azure_openai":
        return "Azure OpenAI: replace YOUR-RESOURCE-NAME with your Azure resource name."
    if normalized == "ollama_cloud":
        return "Ollama Cloud: add your cloud key to discover hosted models."
    if normalized == "custom":
        return "Advanced OpenAI-compatible endpoint: override host/model as needed."
    return "AI provider is off."


def recommended_models_for_provider(provider: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
    if normalized == "claude":
        return ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"]
    if normalized == "openrouter":
        return ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
    if normalized == "gemini":
        return ["gemini-2.0-flash", "gemini-1.5-pro"]
    if normalized == "azure_openai":
        return ["gpt-4o-mini", "gpt-4o", "o3-mini"]
    if normalized == "ollama_cloud":
        return ["qwen3", "gpt-oss:20b", "gemma3"]
    if normalized == "ollama":
        if total_ram_gb() < 8.0:
            return [
                "llama3.2:1b-instruct-q4_K_M",
                "qwen2.5:1.5b-instruct-q4_K_M",
                "qwen2.5:3b-instruct-q4_K_M",
            ]
        return [
            "qwen2.5:7b-instruct-q4_K_M",
            "llama3.1:8b-instruct-q4_K_M",
            "qwen2.5:3b-instruct-q4_K_M",
        ]
    return ["gpt-4o-mini", "claude-3-5-sonnet-latest", "gemini-2.0-flash"]


def recommended_model_guidance(provider: str) -> list[ModelRecommendation]:
    normalized = provider.strip().lower()
    if normalized == "ollama":
        if total_ram_gb() < 8.0:
            return [
                ModelRecommendation(
                    model="llama3.2:1b-instruct-q4_K_M",
                    framing="Fast local drafting",
                    reason="Best fit for lower-memory devices.",
                ),
                ModelRecommendation(
                    model="qwen2.5:1.5b-instruct-q4_K_M",
                    framing="Balanced local writing",
                    reason="Slightly stronger output with modest resource use.",
                ),
            ]
        return [
            ModelRecommendation(
                model="qwen2.5:7b-instruct-q4_K_M",
                framing="Quality-focused local editing",
                reason="Higher quality while staying practical for local runs.",
            ),
            ModelRecommendation(
                model="llama3.1:8b-instruct-q4_K_M",
                framing="General local assistant",
                reason="Reliable for rewriting, summarizing, and grammar tasks.",
            ),
        ]
    if normalized == "openai":
        return [
            ModelRecommendation(
                model="gpt-4o-mini",
                framing="Cost-aware daily use",
                reason="Fast and efficient for most writing tasks.",
            ),
            ModelRecommendation(
                model="gpt-4.1",
                framing="High-quality reasoning",
                reason="Best for complex transformations and nuanced editing.",
            ),
        ]
    if normalized == "claude":
        return [
            ModelRecommendation(
                model="claude-3-5-haiku-latest",
                framing="Speed-first drafting",
                reason="Responsive for rapid prompt iteration.",
            ),
            ModelRecommendation(
                model="claude-3-5-sonnet-latest",
                framing="Deep writing review",
                reason="Stronger reasoning for long-form revision.",
            ),
        ]
    if normalized == "openrouter":
        return [
            ModelRecommendation(
                model="openrouter/auto",
                framing="Automatic routing",
                reason="Lets the endpoint select a good model for each request.",
            ),
            ModelRecommendation(
                model="openai/gpt-4o-mini",
                framing="Predictable speed and cost",
                reason="Good explicit fallback when you want stable behavior.",
            ),
        ]
    if normalized == "gemini":
        return [
            ModelRecommendation(
                model="gemini-2.0-flash",
                framing="Fast cloud drafting",
                reason="Strong default for low-latency writing help.",
            ),
            ModelRecommendation(
                model="gemini-1.5-pro",
                framing="Long-context analysis",
                reason="Better for larger prompts and deeper synthesis.",
            ),
        ]
    if normalized == "azure_openai":
        return [
            ModelRecommendation(
                model="gpt-4o-mini",
                framing="Enterprise default",
                reason="Balanced quality/cost for managed Azure deployments.",
            ),
            ModelRecommendation(
                model="o3-mini",
                framing="Reasoning-heavy tasks",
                reason="Useful for multi-step editing and refactoring prompts.",
            ),
        ]
    return [
        ModelRecommendation(
            model=name,
            framing="General recommendation",
            reason="Suggested model for this provider.",
        )
        for name in recommended_models_for_provider(provider)
    ]


def filter_model_names(models: list[str], query: str, *, limit: int = 200) -> list[str]:
    needle = query.strip().lower()
    if not needle:
        return models[:limit]
    terms = [term for term in needle.split() if term]
    ranked: list[tuple[int, str]] = []
    for name in models:
        lowered = name.lower()
        score = 0
        if lowered.startswith(needle):
            score += 5
        if needle in lowered:
            score += 3
        for term in terms:
            if term in lowered:
                score += 1
        if score > 0:
            ranked.append((score, name))
    ranked.sort(key=lambda item: (-item[0], item[1].lower()))
    return [name for _score, name in ranked[:limit]]


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


# Error categories used to give callers cause-specific, screen-reader-friendly
# messages instead of scanning formatted strings for substrings like "401".
# Retryable categories are transient and benefit from a brief warm-up retry
# (cloud cold starts, a local server still booting, rate limiting). Auth and
# permission failures are never retried.
_RETRYABLE_CATEGORIES = frozenset({"warming_up", "not_running", "rate_limited", "timeout"})

# Highest-priority first. When several endpoints fail in one attempt we surface
# the most actionable cause (an auth/permission problem outranks a transient one).
_CATEGORY_PRIORITY = (
    "auth_invalid",
    "forbidden",
    "rate_limited",
    "warming_up",
    "not_running",
    "timeout",
    "http_error",
    "bad_response",
    "unreachable",
)

# 5xx and a few transient 4xx codes that typically clear once a provider has
# finished warming up.
_WARMING_UP_STATUS = frozenset({408, 425, 500, 502, 503, 504, 520, 522, 524})

# Bounded warm-up backoff (seconds) between retry attempts.
_RETRY_BACKOFF_SECONDS: tuple[float, ...] = (0.4, 1.0, 2.0)


@dataclass(slots=True)
class _FetchError:
    category: str
    message: str
    status_code: int | None = None


def _category_for_status(code: int) -> str:
    if code == 401:
        return "auth_invalid"
    if code == 403:
        return "forbidden"
    if code == 429:
        return "rate_limited"
    if code in _WARMING_UP_STATUS:
        return "warming_up"
    return "http_error"


def _message_for_category(
    category: str,
    *,
    endpoint: str,
    status_code: int | None = None,
    reason: object | None = None,
) -> str:
    if category == "auth_invalid":
        return "Authentication failed. Check your API key."
    if category == "forbidden":
        return (
            "Access denied. Your API key is valid but lacks permission for this "
            "model or region. Check the provider's model access, billing, or quota."
        )
    if category == "rate_limited":
        return "Rate limited by the AI provider. Wait a moment and try again."
    if category == "warming_up":
        return "The AI provider is warming up. Try again in a moment."
    if category == "not_running":
        return "The local AI server is not running. Start Ollama and try again."
    if category == "timeout":
        return "Connection timed out. Check host URL and network connection."
    if category == "bad_response":
        return f"Received an invalid response from {endpoint}."
    if category == "http_error" and status_code is not None:
        return f"HTTP {status_code} from {endpoint}."
    if reason is not None:
        return f"Failed to reach {endpoint}: {reason}"
    return f"Could not reach {endpoint}."


def _most_significant_error(errors: list[_FetchError]) -> _FetchError | None:
    if not errors:
        return None
    ranked = sorted(
        errors,
        key=lambda err: _CATEGORY_PRIORITY.index(err.category)
        if err.category in _CATEGORY_PRIORITY
        else len(_CATEGORY_PRIORITY),
    )
    return ranked[0]


def list_assistant_models(
    settings: AssistantConnectionSettings,
    api_key: str,
    *,
    timeout_seconds: float = 8.0,
    max_models: int = 200,
    max_attempts: int = 3,
) -> tuple[list[str], str | None]:
    provider = settings.provider.strip().lower()
    if provider == "off":
        return [], None

    host = (settings.host or "").strip().rstrip("/")
    if not host:
        host = default_host_for_provider(provider)
    policy_error = _validate_endpoint_security(provider, host)
    if policy_error:
        return [], policy_error

    headers = _build_auth_headers(provider, host, api_key)
    candidates = _model_endpoint_candidates(provider, host)

    last_error: _FetchError | None = None
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        attempt_errors: list[_FetchError] = []
        for endpoint in candidates:
            models, error = _fetch_models_from_endpoint(
                endpoint,
                headers,
                timeout_seconds=timeout_seconds,
                max_models=max_models,
            )
            if error is None:
                return models, None
            attempt_errors.append(error)

        last_error = _most_significant_error(attempt_errors)
        if last_error is None or last_error.category not in _RETRYABLE_CATEGORIES:
            break
        if attempt + 1 < attempts:
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt, len(_RETRY_BACKOFF_SECONDS) - 1)]
            time.sleep(backoff)

    if last_error is None:
        return [], "Could not reach AI endpoint."
    return [], last_error.message


def _fetch_models_from_endpoint(
    endpoint: str,
    headers: dict[str, str],
    *,
    timeout_seconds: float,
    max_models: int,
) -> tuple[list[str], _FetchError | None]:
    request = Request(endpoint, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        category = _category_for_status(exc.code)
        return [], _FetchError(
            category,
            _message_for_category(category, endpoint=endpoint, status_code=exc.code),
            exc.code,
        )
    except URLError as exc:
        category = _category_for_url_error(exc)
        return [], _FetchError(
            category,
            _message_for_category(category, endpoint=endpoint, reason=exc.reason),
        )
    except TimeoutError:
        return [], _FetchError(
            "timeout", _message_for_category("timeout", endpoint=endpoint)
        )
    except json.JSONDecodeError:
        return [], _FetchError(
            "bad_response", _message_for_category("bad_response", endpoint=endpoint)
        )

    models = _extract_model_names(payload)
    if not models:
        return [], None
    return models[:max_models], None


def _category_for_url_error(exc: URLError) -> str:
    reason = getattr(exc, "reason", None)
    if isinstance(reason, ConnectionRefusedError):
        return "not_running"
    if isinstance(reason, TimeoutError):
        return "timeout"
    text = str(reason).lower()
    if "refused" in text:
        return "not_running"
    if "timed out" in text:
        return "timeout"
    return "unreachable"


def _extract_model_names(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []

    names: list[str] = []
    models = payload.get("models")
    if isinstance(models, list):
        for item in models:
            if isinstance(item, dict):
                names.extend(_extract_names_from_model_item(item))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                names.extend(_extract_names_from_model_item(item))

    items = payload.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                names.extend(_extract_names_from_model_item(item))

    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(name)
    return unique


def _extract_names_from_model_item(item: dict[str, object]) -> list[str]:
    candidates = (
        str(item.get("name", "")).strip(),
        str(item.get("id", "")).strip(),
        str(item.get("model", "")).strip(),
        str(item.get("display_name", "")).strip(),
    )
    return [value for value in candidates if value]


def _model_endpoint_candidates(provider: str, host: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized in {"openai", "openrouter", "custom", "claude"}:
        return [f"{host}/v1/models"]
    if normalized == "gemini":
        return [f"{host}/v1/models", f"{host}/v1beta/models"]
    if normalized == "azure_openai":
        version = quote("2024-10-21")
        return [
            f"{host}/openai/models?api-version={version}",
            f"{host}/openai/deployments?api-version={version}",
        ]
    return [f"{host}/api/tags", f"{host}/v1/models"]


def _validate_endpoint_security(provider: str, host: str) -> str | None:
    parsed = urlparse(host)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    if provider == "off":
        return None
    if scheme == "https":
        return None
    if scheme == "http" and provider in {"ollama", "custom"} and _is_local_host(hostname):
        return None
    if scheme == "http" and provider not in _CLOUD_PROVIDERS and _is_local_host(hostname):
        return None
    return (
        "Only HTTPS endpoints are allowed for cloud providers. "
        "HTTP is only supported for local loopback/private-network endpoints."
    )


def _is_local_host(hostname: str) -> bool:
    if not hostname:
        return False
    if hostname in {"localhost", "::1"}:
        return True
    if hostname.endswith(".localhost"):
        return True
    if hostname.startswith("127."):
        return True
    if hostname.startswith("10.") or hostname.startswith("192.168."):
        return True
    if hostname.startswith("172."):
        try:
            second_octet = int(hostname.split(".")[1])
        except (IndexError, ValueError):
            return False
        return 16 <= second_octet <= 31
    return False


def _build_auth_headers(provider: str, host: str, api_key: str) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    secret = api_key.strip()
    if not secret:
        return headers

    parsed = urlparse(host)
    is_https = parsed.scheme.lower() == "https"
    is_ollama_cloud = "ollama.com" in parsed.netloc.lower()
    if provider in {"openai", "openrouter", "custom", "ollama_cloud"} or (
        is_https and is_ollama_cloud
    ):
        headers["Authorization"] = f"Bearer {secret}"
    if provider == "claude":
        headers["x-api-key"] = secret
        headers["anthropic-version"] = "2023-06-01"
    if provider == "gemini":
        headers["x-goog-api-key"] = secret
    if provider == "azure_openai":
        headers["api-key"] = secret
    return headers


def assistant_connection_path() -> Path:
    return app_data_dir() / _ASSISTANT_CONNECTION_FILE


def assistant_secret_path() -> Path:
    return app_data_dir() / _ASSISTANT_SECRET_FILE


def load_assistant_connection_settings() -> AssistantConnectionSettings:
    raw = read_json(assistant_connection_path(), default={})
    if not isinstance(raw, dict):
        return AssistantConnectionSettings()
    parsed = AssistantConnectionSettings.from_dict(raw)
    if not parsed.host:
        parsed.host = default_host_for_provider(parsed.provider)
    if not parsed.model:
        parsed.model = default_model_for_provider(parsed.provider)
    return parsed


def save_assistant_connection_settings(settings: AssistantConnectionSettings) -> None:
    payload = asdict(settings)
    payload["provider"] = settings.provider.strip().lower() or "ollama"
    payload["host"] = settings.host.strip() or default_host_for_provider(payload["provider"])
    payload["model"] = settings.model.strip() or default_model_for_provider(payload["provider"])
    write_json_atomic(assistant_connection_path(), payload)


def load_assistant_api_key() -> str:
    credential_secret = _load_api_key_from_credential_manager()
    if credential_secret:
        return credential_secret

    raw = read_json(assistant_secret_path(), default={})
    if not isinstance(raw, dict):
        return ""
    encrypted = str(raw.get("protected_secret", "")).strip()
    if not encrypted:
        return ""
    decrypted = unprotect_secret(encrypted)
    if not decrypted:
        return ""
    if _save_api_key_with_credential_manager(decrypted):
        path = assistant_secret_path()
        if path.exists():
            path.unlink()
    return decrypted


def save_assistant_api_key(api_key: str) -> None:
    secret = api_key.strip()
    path = assistant_secret_path()
    if not secret:
        _delete_api_key_from_credential_manager()
        if path.exists():
            path.unlink()
        return
    if _save_api_key_with_credential_manager(secret):
        if path.exists():
            path.unlink()
        return
    write_json_atomic(path, {"protected_secret": protect_secret(secret)})


def assistant_secret_unlock_failed() -> bool:
    """Return True when a secret is saved on disk but cannot be unlocked here.

    This happens when a DPAPI-protected secret travels to a different Windows
    user or machine (for example a portable install moved on a USB drive): the
    ciphertext is present but cannot be decrypted with the current user's keys.
    Callers use this to tell the user to re-enter the key instead of showing a
    misleading "authentication failed" message.
    """
    if _load_api_key_from_credential_manager():
        return False
    raw = read_json(assistant_secret_path(), default={})
    if not isinstance(raw, dict):
        return False
    encrypted = str(raw.get("protected_secret", "")).strip()
    if not encrypted:
        return False
    try:
        decrypted = unprotect_secret(encrypted)
    except Exception:  # noqa: BLE001 - any decrypt failure means "cannot unlock"
        return True
    return not decrypted


def _load_api_key_from_credential_manager() -> str:
    if not credential_manager_available():
        return ""
    credential = load_generic_credential(_ASSISTANT_CREDENTIAL_TARGET)
    if credential is None:
        return ""
    return credential.secret.strip()


def _save_api_key_with_credential_manager(api_key: str) -> bool:
    secret = api_key.strip()
    if not secret or not credential_manager_available():
        return False
    try:
        save_generic_credential(_ASSISTANT_CREDENTIAL_TARGET, secret)
    except OSError:
        return False
    return True


def _delete_api_key_from_credential_manager() -> None:
    if not credential_manager_available():
        return
    try:
        delete_generic_credential(_ASSISTANT_CREDENTIAL_TARGET)
    except OSError:
        return
