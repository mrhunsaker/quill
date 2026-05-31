from __future__ import annotations

from dataclasses import dataclass, replace
from importlib import import_module
from typing import Any

try:
    import pyttsx3  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional runtime dependency
    pyttsx3 = None

_VALID_BACKENDS = {"auto", "prism", "status_only"}

_sr_active_cache: bool | None = None


def _screen_reader_active() -> bool:
    """Cached check for a running screen reader (so 'auto' TTS doesn't double-talk)."""
    global _sr_active_cache
    if _sr_active_cache is None:
        try:
            from quill.platform.windows.sr_detect import detect_screen_reader

            _sr_active_cache = bool(detect_screen_reader().detected)
        except Exception:  # noqa: BLE001
            _sr_active_cache = False
    return _sr_active_cache


def normalize_backend_name(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in _VALID_BACKENDS:
        return raw
    return "auto"


@dataclass(frozen=True, slots=True)
class AnnouncementBackendState:
    requested_backend: str
    active_backend: str
    prism_available: bool
    prism_runtime_ready: bool
    backend_name: str
    last_error: str = ""


class AnnouncementEngine:
    def __init__(self, requested_backend: str = "auto") -> None:
        self._runtime_backend: Any | None = None
        self._state = AnnouncementBackendState(
            requested_backend="auto",
            active_backend="status_only",
            prism_available=False,
            prism_runtime_ready=False,
            backend_name="Status Bar",
            last_error="",
        )
        self.configure(requested_backend)

    def configure(self, requested_backend: str) -> AnnouncementBackendState:
        requested = normalize_backend_name(requested_backend)
        backend, probe = _probe_prism_backend()
        prism_available = probe != "missing"
        prism_runtime_ready = backend is not None
        active_backend = "status_only"
        backend_name = "Status Bar"
        last_error = ""

        if requested == "prism":
            if backend is not None:
                active_backend = "prism"
                backend_name = _backend_name(backend)
            else:
                last_error = _probe_to_message(probe)
        elif requested == "auto":
            if backend is not None:
                active_backend = "prism"
                backend_name = _backend_name(backend)
            else:
                backend_name = "Status Bar"
                if probe not in {"missing", "runtime_unavailable"}:
                    last_error = _probe_to_message(probe)

        self._runtime_backend = backend if active_backend == "prism" else None
        self._state = AnnouncementBackendState(
            requested_backend=requested,
            active_backend=active_backend,
            prism_available=prism_available,
            prism_runtime_ready=prism_runtime_ready,
            backend_name=backend_name,
            last_error=last_error,
        )
        return self._state

    def state(self) -> AnnouncementBackendState:
        return self._state

    def announce(self, message: str) -> str | None:
        if self._runtime_backend is None:
            # Only speak via system TTS when NO screen reader is running —
            # otherwise it talks over Narrator/NVDA/JAWS (the screen reader
            # already reads the UI through the accessibility API).
            if (
                self._state.requested_backend == "auto"
                and pyttsx3 is not None
                and not _screen_reader_active()
            ):
                try:
                    engine = pyttsx3.init()
                    try:
                        engine.say(message)
                        engine.runAndWait()
                    finally:
                        engine.stop()
                    self._state = replace(
                        self._state,
                        active_backend="speech",
                        backend_name="System Speech",
                        last_error="",
                    )
                except Exception as exc:  # noqa: BLE001
                    error = f"System speech announcement failed: {exc}"
                    self._state = replace(self._state, last_error=error)
                    return error
            return None
        speak = getattr(self._runtime_backend, "speak", None)
        if not callable(speak):
            error = "Active Prism backend does not expose speak()."
            self._state = replace(self._state, last_error=error)
            return error
        try:
            speak(message, interrupt=False)
            return None
        except TypeError:
            speak(message)
            return None
        except Exception as exc:  # noqa: BLE001
            error = f"Prism announcement failed: {exc}"
            self._state = replace(self._state, last_error=error)
            return error

    def diagnostics_environment(self) -> dict[str, object]:
        return {
            "announcement_backend_requested": self._state.requested_backend,
            "announcement_backend_active": self._state.active_backend,
            "announcement_backend_name": self._state.backend_name,
            "announcement_prism_available": self._state.prism_available,
            "announcement_prism_runtime_ready": self._state.prism_runtime_ready,
            "announcement_backend_error": self._state.last_error,
        }


def _probe_prism_backend() -> tuple[Any | None, str]:
    prism_module = _import_prism_module()
    if prism_module is None:
        return None, "missing"
    try:
        context = prism_module.Context()
    except Exception:  # noqa: BLE001
        return None, "context_error"
    try:
        backend = context.acquire_best()
    except Exception:  # noqa: BLE001
        return None, "acquire_error"
    features = getattr(backend, "features", None)
    runtime_flag = getattr(features, "is_supported_at_runtime", True)
    if not runtime_flag:
        return None, "runtime_unavailable"
    return backend, "ok"


def _import_prism_module() -> Any | None:
    for module_name in ("prism", "prismatoid"):
        try:
            return import_module(module_name)
        except Exception:  # noqa: BLE001
            continue
    return None


def _backend_name(backend: Any) -> str:
    raw = getattr(backend, "name", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "Prism"


def _probe_to_message(probe: str) -> str:
    messages = {
        "missing": "Prism is not installed.",
        "context_error": "Prism failed to initialize context.",
        "acquire_error": "Prism could not acquire a backend.",
        "runtime_unavailable": "Prism backend is not active at runtime.",
    }
    return messages.get(probe, "Unknown Prism backend error.")
