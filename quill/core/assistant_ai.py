from __future__ import annotations

import json
import ssl
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from quill.core.ai.providers import (
    ModelRecommendation as ModelRecommendation,
)
from quill.core.ai.providers import (
    default_host_for_provider as default_host_for_provider,
)
from quill.core.ai.providers import (
    default_model_for_provider as default_model_for_provider,
)
from quill.core.ai.providers import (
    provider_api_key_label as provider_api_key_label,
)
from quill.core.ai.providers import (
    provider_help_text as provider_help_text,
)
from quill.core.ai.providers import (
    provider_requires_api_key as provider_requires_api_key,
)
from quill.core.ai.providers import (
    recommended_model_guidance as recommended_model_guidance,
)
from quill.core.ai.providers import (
    recommended_models_for_provider as recommended_models_for_provider,
)
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
_CLOUD_PROVIDERS = frozenset({
    "openai",
    "claude",
    "openrouter",
    "gemini",
    "azure_openai",
    "ollama_cloud",
})


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
        host = str(
            data.get("host", default_host_for_provider(provider))
        ).strip() or default_host_for_provider(provider)
        model = str(
            data.get("model", default_model_for_provider(provider))
        ).strip() or default_model_for_provider(provider)
        return cls(provider=provider, host=host, model=model)


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
        key=lambda err: (
            _CATEGORY_PRIORITY.index(err.category)
            if err.category in _CATEGORY_PRIORITY
            else len(_CATEGORY_PRIORITY)
        ),
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


def _context_for(endpoint: str) -> ssl.SSLContext | None:
    """Return a certificate-verifying context for HTTPS endpoints.

    Cloud providers are always HTTPS and must verify certificates. Local
    providers (Ollama on loopback or a private host) use plain HTTP, which has
    no TLS context; returning ``None`` lets urllib proceed without one. HTTPS is
    never downgraded to an unverified context.
    """
    if urlparse(endpoint).scheme == "https":
        from quill.core.net import verified_ssl_context

        return verified_ssl_context()
    return None


def _fetch_models_from_endpoint(
    endpoint: str,
    headers: dict[str, str],
    *,
    timeout_seconds: float,
    max_models: int,
) -> tuple[list[str], _FetchError | None]:
    request = Request(endpoint, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds, context=_context_for(endpoint)) as response:
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
        return [], _FetchError("timeout", _message_for_category("timeout", endpoint=endpoint))
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


def clear_assistant_api_key() -> bool:
    """Forget the stored assistant API key (SEC-7).

    Removes the key from *both* persistence layers: the Windows Credential
    Manager entry and the DPAPI-protected ``assistant-secret.json`` fallback.
    Returns ``True`` when a stored key was actually present and removed, so the
    caller can announce "key forgotten" versus "no key was stored".

    Note (shared-account limitation): the Credential Manager entry is scoped to
    the current Windows user account. On a shared Windows account, anyone using
    that account shares the same credential store, so forgetting the key removes
    it for every person who signs in as that user — and a key saved by one of
    them is visible to the others. Use separate Windows user accounts to keep
    assistant keys private.
    """

    had_credential = bool(_load_api_key_from_credential_manager())
    _delete_api_key_from_credential_manager()

    path = assistant_secret_path()
    had_file = path.exists()
    if had_file:
        path.unlink(missing_ok=True)

    return had_credential or had_file


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


# --- Chat generation (AI-13, AI-15, AI-17) --------------------------------
#
# A configured cloud or Ollama provider must actually produce the response,
# instead of generation silently falling back to the bundled local model. These
# functions build the per-provider request, parse the per-provider response, and
# reuse the same endpoint-security check, verified TLS context, retry/backoff,
# and error taxonomy as model listing so the chat path reports the same
# cause-specific, screen-reader-friendly messages.

_DEFAULT_MAX_TOKENS = 1024
# Providers whose chat API is OpenAI chat-completions compatible.
_OPENAI_COMPATIBLE = frozenset({"openai", "openrouter", "custom", "ollama_cloud"})


def chat_endpoint(provider: str, host: str, model: str) -> str:
    """Return the chat endpoint URL for a provider (pure; no network)."""
    normalized = provider.strip().lower()
    host = host.rstrip("/")
    if normalized == "claude":
        return f"{host}/v1/messages"
    if normalized == "gemini":
        return f"{host}/v1beta/models/{quote(model)}:generateContent"
    if normalized == "azure_openai":
        # Azure targets a *deployment* in the path, not a model in the body.
        version = quote("2024-10-21")
        return f"{host}/openai/deployments/{quote(model)}/chat/completions?api-version={version}"
    if normalized == "ollama":
        return f"{host}/api/chat"
    return f"{host}/v1/chat/completions"


def build_chat_body(
    provider: str,
    model: str,
    prompt: str,
    *,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    stream: bool = False,
) -> dict[str, object]:
    """Return the JSON request body for a provider's chat API (pure).

    ``stream`` requests incremental token delivery (AI-14). Gemini carries the
    streaming choice in its URL rather than the body, so the flag is a no-op
    there; every other provider sets its own ``stream`` field.
    """
    normalized = provider.strip().lower()
    user_message = {"role": "user", "content": prompt}
    if normalized == "claude":
        # Claude requires an explicit max_tokens.
        body: dict[str, object] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [user_message],
        }
        if stream:
            body["stream"] = True
        return body
    if normalized == "gemini":
        # Gemini streams via the :streamGenerateContent?alt=sse endpoint, not a
        # body flag, so the request body is identical for both modes.
        return {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if normalized == "ollama":
        return {"model": model, "messages": [user_message], "stream": stream}
    if normalized == "azure_openai":
        # The deployment is in the URL, so the body omits the model.
        body = {"messages": [user_message], "max_tokens": max_tokens}
        if stream:
            body["stream"] = True
        return body
    body = {"model": model, "messages": [user_message], "max_tokens": max_tokens}
    if stream:
        body["stream"] = True
    return body


def build_chat_headers(provider: str, host: str, api_key: str) -> dict[str, str]:
    """Return chat request headers, including OpenRouter attribution (pure)."""
    headers = _build_auth_headers(provider, host, api_key)
    if provider.strip().lower() == "openrouter":
        # Optional attribution headers OpenRouter uses for app ranking.
        headers.setdefault("HTTP-Referer", "https://github.com/Community-Access/quill")
        headers.setdefault("X-Title", "QUILL")
    return headers


def parse_chat_response(provider: str, payload: object) -> str | None:
    """Extract the response text from a provider's chat payload (pure)."""
    if not isinstance(payload, dict):
        return None
    normalized = provider.strip().lower()
    if normalized == "claude":
        content = payload.get("content")
        if isinstance(content, list):
            text = "".join(
                str(block.get("text", "")) for block in content if isinstance(block, dict)
            ).strip()
            return text or None
        return None
    if normalized == "gemini":
        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content")
                if isinstance(content, dict):
                    parts = content.get("parts")
                    if isinstance(parts, list):
                        text = "".join(
                            str(part.get("text", "")) for part in parts if isinstance(part, dict)
                        ).strip()
                        return text or None
        return None
    if normalized == "ollama":
        message = payload.get("message")
        if isinstance(message, dict):
            text = str(message.get("content", "")).strip()
            return text or None
        response = payload.get("response")
        if isinstance(response, str):
            return response.strip() or None
        return None
    # OpenAI-compatible: openai, openrouter, custom, ollama_cloud, azure_openai.
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                text = str(message.get("content", "")).strip()
                return text or None
            text_value = first.get("text")
            if isinstance(text_value, str):
                return text_value.strip() or None
    return None


def _post_chat(
    endpoint: str,
    headers: dict[str, str],
    body: bytes,
    provider: str,
    *,
    timeout_seconds: float,
) -> tuple[str | None, _FetchError | None]:
    request = Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout_seconds, context=_context_for(endpoint)) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        category = _category_for_status(exc.code)
        return None, _FetchError(
            category,
            _message_for_category(category, endpoint=endpoint, status_code=exc.code),
            exc.code,
        )
    except URLError as exc:
        category = _category_for_url_error(exc)
        return None, _FetchError(
            category, _message_for_category(category, endpoint=endpoint, reason=exc.reason)
        )
    except TimeoutError:
        return None, _FetchError("timeout", _message_for_category("timeout", endpoint=endpoint))
    except json.JSONDecodeError:
        return None, _FetchError(
            "bad_response", _message_for_category("bad_response", endpoint=endpoint)
        )
    text = parse_chat_response(provider, payload)
    if text is None:
        return None, _FetchError(
            "bad_response", _message_for_category("bad_response", endpoint=endpoint)
        )
    return text, None


def generate_assistant_response(
    settings: AssistantConnectionSettings,
    api_key: str,
    prompt: str,
    *,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    timeout_seconds: float = 60.0,
    max_attempts: int = 3,
) -> tuple[str | None, str | None]:
    """Generate a chat response from the configured provider.

    Returns ``(text, error)``: on success ``text`` is the response and ``error``
    is ``None``; on failure ``text`` is ``None`` and ``error`` is a cause-specific
    message from the shared taxonomy.
    """
    provider = settings.provider.strip().lower()
    if provider == "off":
        return None, "The AI provider is set to Off."
    host = (settings.host or "").strip().rstrip("/") or default_host_for_provider(provider)
    policy_error = _validate_endpoint_security(provider, host)
    if policy_error:
        return None, policy_error
    model = (settings.model or "").strip() or default_model_for_provider(provider)
    endpoint = chat_endpoint(provider, host, model)
    headers = build_chat_headers(provider, host, api_key)
    body = json.dumps(build_chat_body(provider, model, prompt, max_tokens=max_tokens)).encode(
        "utf-8"
    )

    last_error: _FetchError | None = None
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        text, error = _post_chat(endpoint, headers, body, provider, timeout_seconds=timeout_seconds)
        if error is None:
            return text, None
        last_error = error
        if error.category not in _RETRYABLE_CATEGORIES:
            break
        if attempt + 1 < attempts:
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt, len(_RETRY_BACKOFF_SECONDS) - 1)]
            time.sleep(backoff)

    if last_error is None:
        return None, "Could not reach AI endpoint."
    return None, last_error.message


# --- Streaming chat generation (AI-14, AI-1) ------------------------------
#
# Each wired provider can stream tokens as the model produces them, so the UI
# announces the reply incrementally instead of waiting for the whole thing. The
# wire format differs by provider — OpenAI-compatible, Claude, and Gemini speak
# Server-Sent Events (``data:`` lines terminated by ``[DONE]``); Ollama's local
# ``/api/chat`` speaks newline-delimited JSON. The parsing below is pure so it
# is tested without a network, and a clean non-streaming fallback lives on the
# backend (``AIBackend.respond_stream``) for providers or builds that can't
# stream.

# Providers whose streaming wire format is newline-delimited JSON, not SSE.
_NDJSON_STREAM_PROVIDERS = frozenset({"ollama"})


def stream_chat_endpoint(provider: str, host: str, model: str) -> str:
    """Return the streaming chat endpoint URL for a provider (pure; no network).

    Identical to :func:`chat_endpoint` except for Gemini, which uses a distinct
    ``:streamGenerateContent`` method with ``alt=sse`` so it returns Server-Sent
    Events instead of one buffered JSON array.
    """
    normalized = provider.strip().lower()
    if normalized == "gemini":
        host = host.rstrip("/")
        return f"{host}/v1beta/models/{quote(model)}:streamGenerateContent?alt=sse"
    return chat_endpoint(provider, host, model)


def parse_stream_event(provider: str, data: str) -> str | None:
    """Extract the incremental text from one decoded stream payload (pure).

    ``data`` is the JSON portion of a single Server-Sent Event (the part after
    ``data:``) or one newline-delimited JSON line. Returns the text delta, or
    ``None`` for control frames (role openers, ``[DONE]``, keep-alives) that
    carry no text.
    """
    data = data.strip()
    if not data or data == "[DONE]":
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    normalized = provider.strip().lower()
    if normalized == "claude":
        if payload.get("type") != "content_block_delta":
            return None
        delta = payload.get("delta")
        if isinstance(delta, dict):
            text = str(delta.get("text", ""))
            return text or None
        return None
    if normalized == "gemini":
        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content")
                if isinstance(content, dict):
                    parts = content.get("parts")
                    if isinstance(parts, list):
                        text = "".join(
                            str(part.get("text", "")) for part in parts if isinstance(part, dict)
                        )
                        return text or None
        return None
    if normalized == "ollama":
        message = payload.get("message")
        if isinstance(message, dict):
            text = str(message.get("content", ""))
            return text or None
        return None
    # OpenAI-compatible delta: openai, openrouter, custom, ollama_cloud, azure.
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            delta = first.get("delta")
            if isinstance(delta, dict):
                text = str(delta.get("content", ""))
                return text or None
            # Some compatible servers send full messages even when streaming.
            message = first.get("message")
            if isinstance(message, dict):
                text = str(message.get("content", ""))
                return text or None
    return None


def iter_stream_text(provider: str, raw_lines: Iterable[str | bytes]) -> Iterator[str]:
    """Turn a provider's raw stream lines into text deltas (pure; no network).

    Handles both wire formats: Server-Sent Events (skip ``event:``/comment lines,
    strip the ``data:`` prefix, stop at ``[DONE]``) and newline-delimited JSON
    (each line is a JSON object). Only non-empty text deltas are yielded.
    """
    ndjson = provider.strip().lower() in _NDJSON_STREAM_PROVIDERS
    for raw in raw_lines:
        line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        line = line.strip()
        if not line:
            continue
        if ndjson:
            data = line
        else:
            if line.startswith(":"):
                # SSE comment / keep-alive.
                continue
            if not line.startswith("data:"):
                # Skip "event:" and other SSE field lines that carry no payload.
                continue
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                return
        text = parse_stream_event(provider, data)
        if text:
            yield text


def _post_chat_stream(
    endpoint: str,
    headers: dict[str, str],
    body: bytes,
    provider: str,
    on_delta: Callable[[str], None],
    *,
    timeout_seconds: float,
) -> tuple[str | None, _FetchError | None, bool]:
    """Open one streaming request, emit deltas, and return the full text.

    Returns ``(text, error, emitted)``. ``emitted`` is True once any delta has
    been delivered to ``on_delta`` — the caller uses it to avoid retrying a
    partially streamed response (which would duplicate text).
    """
    request = Request(endpoint, data=body, headers=headers, method="POST")
    chunks: list[str] = []
    emitted = False
    try:
        with urlopen(request, timeout=timeout_seconds, context=_context_for(endpoint)) as response:
            for delta in iter_stream_text(provider, response):
                chunks.append(delta)
                emitted = True
                on_delta(delta)
    except HTTPError as exc:
        category = _category_for_status(exc.code)
        return (
            None,
            _FetchError(
                category,
                _message_for_category(category, endpoint=endpoint, status_code=exc.code),
                exc.code,
            ),
            emitted,
        )
    except URLError as exc:
        category = _category_for_url_error(exc)
        return (
            None,
            _FetchError(
                category, _message_for_category(category, endpoint=endpoint, reason=exc.reason)
            ),
            emitted,
        )
    except TimeoutError:
        return (
            None,
            _FetchError("timeout", _message_for_category("timeout", endpoint=endpoint)),
            emitted,
        )
    text = "".join(chunks)
    if not text:
        return (
            None,
            _FetchError("bad_response", _message_for_category("bad_response", endpoint=endpoint)),
            emitted,
        )
    return text, None, emitted


def generate_assistant_response_stream(
    settings: AssistantConnectionSettings,
    api_key: str,
    prompt: str,
    on_delta: Callable[[str], None],
    *,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    timeout_seconds: float = 120.0,
    max_attempts: int = 3,
) -> tuple[str | None, str | None]:
    """Stream a chat response from the configured provider (AI-14).

    Calls ``on_delta`` with each text fragment as it arrives, and returns
    ``(text, error)`` with the complete response on success. A request that fails
    *before* any token streamed is retried with the same warm-up backoff as the
    blocking path; a request that fails *mid-stream* is not retried (that would
    duplicate already-delivered text). Callers that cannot stream should use the
    backend's non-streaming fallback instead.
    """
    provider = settings.provider.strip().lower()
    if provider == "off":
        return None, "The AI provider is set to Off."
    host = (settings.host or "").strip().rstrip("/") or default_host_for_provider(provider)
    policy_error = _validate_endpoint_security(provider, host)
    if policy_error:
        return None, policy_error
    model = (settings.model or "").strip() or default_model_for_provider(provider)
    endpoint = stream_chat_endpoint(provider, host, model)
    headers = build_chat_headers(provider, host, api_key)
    body = json.dumps(
        build_chat_body(provider, model, prompt, max_tokens=max_tokens, stream=True)
    ).encode("utf-8")

    last_error: _FetchError | None = None
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        text, error, emitted = _post_chat_stream(
            endpoint, headers, body, provider, on_delta, timeout_seconds=timeout_seconds
        )
        if error is None:
            return text, None
        last_error = error
        if emitted or error.category not in _RETRYABLE_CATEGORIES:
            break
        if attempt + 1 < attempts:
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt, len(_RETRY_BACKOFF_SECONDS) - 1)]
            time.sleep(backoff)

    if last_error is None:
        return None, "Could not reach AI endpoint."
    return None, last_error.message
