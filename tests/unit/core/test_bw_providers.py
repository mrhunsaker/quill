from __future__ import annotations

from quill.core.bw_providers import (
    get_provider,
    list_providers,
    provider_mode_guidance,
    provider_readiness,
    recommended_provider_id,
)


def test_list_providers_includes_local_and_cloud() -> None:
    providers = list_providers(include_cloud=True)
    ids = {provider.id for provider in providers}
    assert "local_whisper" in ids
    assert "openai_whisper" in ids


def test_list_providers_can_hide_cloud() -> None:
    providers = list_providers(include_cloud=False)
    ids = {provider.id for provider in providers}
    assert ids == {"local_whisper"}


def test_get_provider_returns_expected() -> None:
    provider = get_provider("local_whisper", include_cloud=True)
    assert provider is not None
    assert provider.provider_type == "local"


def test_provider_mode_guidance_mentions_mode() -> None:
    assert "Local-first" in provider_mode_guidance(local_first=True)
    assert "Cloud-first" in provider_mode_guidance(local_first=False)


def test_recommended_provider_id_returns_known_values() -> None:
    provider_id = recommended_provider_id(local_first=True)
    assert provider_id in {"local_whisper", "openai_whisper"}


def test_provider_readiness_unknown_provider() -> None:
    readiness = provider_readiness("does-not-exist", local_first=True)
    assert readiness.ready is False
    assert "unknown" in readiness.summary.lower()
