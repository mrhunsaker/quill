from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafeModeConfig:
    enabled: bool
    disable_plugins: bool = True
    disable_experimental_features: bool = True
    disable_ai_integrations: bool = True
    disable_startup_restore: bool = True
    disable_background_indexing: bool = True
    disable_file_watchers: bool = True
    disable_custom_themes: bool = True
    disable_custom_snippets: bool = True
    disable_network_services: bool = True


def build_safe_mode_config(enabled: bool) -> SafeModeConfig:
    return SafeModeConfig(enabled=enabled)


def should_enable_safe_mode(arguments: Sequence[str], environment: Mapping[str, str]) -> bool:
    if "--safe-mode" in arguments:
        return True
    return environment.get("QUILL_SAFE_MODE") == "1"


def safe_mode_message() -> str:
    return (
        "QUILL started in Safe Mode. Extensions, experimental features, startup restore, "
        "background indexing, and AI services are disabled for this session."
    )
