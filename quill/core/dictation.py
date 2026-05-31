from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

try:  # pragma: no cover - Windows-only runtime hook
    from quill.platform.windows.dictation import launch_windows_dictation
except ImportError:  # pragma: no cover - non-Windows fallback
    launch_windows_dictation = None


@dataclass(frozen=True, slots=True)
class DictationSettings:
    engine: str = "windows"
    language: str = "en-US"
    model: str = "default"
    device_index: int | None = None


class DictationUnavailableError(RuntimeError):
    pass


class DictationController:
    def __init__(self) -> None:
        self._state = "idle"
        self._stopper: Callable[..., None] | None = None

    @property
    def state(self) -> str:
        return self._state

    def start(
        self,
        settings: DictationSettings,
        *,
        on_state_change: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if launch_windows_dictation is None:
            raise DictationUnavailableError("Windows dictation is only available on Windows")
        try:
            launch_windows_dictation()
        except OSError as error:
            if on_error is not None:
                on_error(str(error))
            raise DictationUnavailableError(str(error)) from error
        self._state = "listening"

    def stop(self, *, on_state_change: Callable[[str], None] | None = None) -> str:
        if self._state == "listening" and launch_windows_dictation is not None:
            try:
                launch_windows_dictation()
            except OSError:
                pass
        self._state = "idle"
        return ""


def list_dictation_devices() -> list[str]:
    return []
