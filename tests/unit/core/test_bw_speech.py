from __future__ import annotations

from pathlib import Path

import pytest

from quill.core.bw_speech import (
    downloaded_model_ids,
    faster_whisper_status,
    get_model,
    list_models,
    machine_guidance,
    model_path,
    recommended_model_id,
    remove_model,
    speech_models_dir,
)


def test_list_models_contains_whisper_defaults() -> None:
    model_ids = {model.id for model in list_models(include_parakeet=False)}
    assert "whisper-tiny" in model_ids
    assert "whisper-base" in model_ids
    assert "whisper-small" in model_ids
    assert "whisper-large-v3-turbo" in model_ids


def test_list_models_can_include_parakeet() -> None:
    model_ids = {model.id for model in list_models(include_parakeet=True)}
    assert "parakeet-ctc-0.6b" in model_ids


def test_recommended_model_is_known() -> None:
    model_ids = {model.id for model in list_models(include_parakeet=True)}
    assert recommended_model_id(include_parakeet=True) in model_ids


def test_machine_guidance_mentions_ram_and_gpu() -> None:
    text = machine_guidance().lower()
    assert "ram" in text
    assert "gpu" in text


def test_model_path_lives_under_speech_model_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    model = get_model("whisper-base", include_parakeet=False)
    assert model is not None
    path = model_path(model)
    assert str(path).startswith(str(speech_models_dir()))
    assert path.name.startswith("models--")


def test_downloaded_model_ids_detects_local_markers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    model = get_model("whisper-base", include_parakeet=False)
    assert model is not None
    cache_repo_dir = model_path(model)
    (cache_repo_dir / "snapshots" / "123").mkdir(parents=True, exist_ok=True)

    ids = downloaded_model_ids(include_parakeet=False)
    assert "whisper-base" in ids


def test_remove_model_removes_marker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    model = get_model("whisper-base", include_parakeet=False)
    assert model is not None
    cache_repo_dir = model_path(model)
    (cache_repo_dir / "snapshots" / "123").mkdir(parents=True, exist_ok=True)

    assert remove_model(model) is True
    assert cache_repo_dir.exists() is False


def test_download_model_rejects_parakeet_in_phase_1() -> None:
    model = get_model("parakeet-ctc-0.6b", include_parakeet=True)
    assert model is not None
    with pytest.raises(RuntimeError, match="Only whisper model acquisition"):
        from quill.core.bw_speech import download_model

        download_model(model)


def test_faster_whisper_status_returns_message() -> None:
    ok, message = faster_whisper_status()
    assert isinstance(ok, bool)
    assert isinstance(message, str)
    assert message != ""
