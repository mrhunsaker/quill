from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from quill.core.paths import app_data_dir

FAST_WHISPER_REQUIREMENT = "faster-whisper>=1.2.1,<2"


@dataclass(frozen=True, slots=True)
class SpeechModelSpec:
    id: str
    name: str
    family: str
    repo_id: str
    approx_size_gb: float
    min_ram_gb: int
    min_vram_gb: int
    description: str
    phased: bool = True


_WHISPER_MODELS: tuple[SpeechModelSpec, ...] = (
    SpeechModelSpec(
        id="whisper-tiny",
        name="Whisper Tiny",
        family="whisper",
        repo_id="Systran/faster-whisper-tiny",
        approx_size_gb=0.08,
        min_ram_gb=2,
        min_vram_gb=0,
        description="Fastest startup and lowest hardware demand.",
    ),
    SpeechModelSpec(
        id="whisper-base",
        name="Whisper Base",
        family="whisper",
        repo_id="Systran/faster-whisper-base",
        approx_size_gb=0.15,
        min_ram_gb=2,
        min_vram_gb=0,
        description="Balanced default for most systems.",
    ),
    SpeechModelSpec(
        id="whisper-small",
        name="Whisper Small",
        family="whisper",
        repo_id="Systran/faster-whisper-small",
        approx_size_gb=0.48,
        min_ram_gb=4,
        min_vram_gb=2,
        description="Higher accuracy on modern laptops and desktops.",
    ),
    SpeechModelSpec(
        id="whisper-large-v3-turbo",
        name="Whisper Large v3 Turbo",
        family="whisper",
        repo_id="Systran/faster-whisper-large-v3-turbo",
        approx_size_gb=1.7,
        min_ram_gb=8,
        min_vram_gb=4,
        description="Best quality-speed tradeoff for strong hardware.",
    ),
)

_PARAKEET_MODELS: tuple[SpeechModelSpec, ...] = (
    SpeechModelSpec(
        id="parakeet-ctc-0.6b",
        name="Parakeet CTC 0.6B",
        family="parakeet",
        repo_id="nvidia/parakeet-ctc-0.6b",
        approx_size_gb=1.2,
        min_ram_gb=4,
        min_vram_gb=0,
        description="Phase rollout candidate for advanced offline ASR.",
    ),
    SpeechModelSpec(
        id="parakeet-tdt-0.6b",
        name="Parakeet TDT 0.6B",
        family="parakeet",
        repo_id="nvidia/parakeet-tdt-0.6b",
        approx_size_gb=1.2,
        min_ram_gb=4,
        min_vram_gb=0,
        description="Phase rollout candidate with stronger timestamp behavior.",
    ),
)


def speech_models_dir() -> Path:
    path = app_data_dir() / "speech-models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def whisper_cache_dir() -> Path:
    path = speech_models_dir() / "faster-whisper-cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_models(*, include_parakeet: bool = True) -> list[SpeechModelSpec]:
    models = list(_WHISPER_MODELS)
    if include_parakeet:
        models.extend(_PARAKEET_MODELS)
    return models


def get_model(model_id: str, *, include_parakeet: bool = True) -> SpeechModelSpec | None:
    for spec in list_models(include_parakeet=include_parakeet):
        if spec.id == model_id:
            return spec
    return None


def model_path(spec: SpeechModelSpec) -> Path:
    if spec.family == "whisper":
        cache_key = spec.repo_id.replace("/", "--")
        return whisper_cache_dir() / f"models--{cache_key}"
    return speech_models_dir() / spec.id


def is_downloaded(spec: SpeechModelSpec) -> bool:
    path = model_path(spec)
    if not path.exists():
        return False
    if spec.family == "whisper":
        snapshots_dir = path / "snapshots"
        if not snapshots_dir.exists():
            return False
        try:
            return any(child.is_dir() for child in snapshots_dir.iterdir())
        except OSError:
            return False
    return path.exists() and path.is_dir()


def downloaded_model_ids(*, include_parakeet: bool = True) -> set[str]:
    return {
        spec.id for spec in list_models(include_parakeet=include_parakeet) if is_downloaded(spec)
    }


def total_ram_gb() -> float:
    if sys.platform.startswith("win"):
        import ctypes

        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys / (1024**3)
    return 8.0


def has_nvidia_gpu() -> bool:
    cmd = shutil.which("nvidia-smi")
    if not cmd:
        return False
    result = subprocess.run([cmd, "-L"], check=False, capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def recommended_model_id(*, include_parakeet: bool = False) -> str:
    ram = total_ram_gb()
    gpu = has_nvidia_gpu()
    if include_parakeet and ram >= 16 and gpu:
        return "parakeet-tdt-0.6b"
    if ram < 6:
        return "whisper-tiny"
    if ram < 10:
        return "whisper-base"
    if ram < 16:
        return "whisper-small"
    if gpu:
        return "whisper-large-v3-turbo"
    return "whisper-small"


def machine_guidance() -> str:
    ram = total_ram_gb()
    gpu = has_nvidia_gpu()
    return f"Detected RAM: {ram:.1f} GB. NVIDIA GPU detected: {'Yes' if gpu else 'No'}."


def free_disk_gb() -> float:
    usage = shutil.disk_usage(speech_models_dir())
    return usage.free / (1024**3)


def has_disk_capacity(spec: SpeechModelSpec, *, extra_buffer_gb: float = 1.0) -> bool:
    return free_disk_gb() >= (spec.approx_size_gb + extra_buffer_gb)


def faster_whisper_status() -> tuple[bool, str]:
    installed = importlib.util.find_spec("faster_whisper") is not None
    if installed:
        return True, "faster-whisper engine is installed and available."
    return (
        False,
        "faster-whisper engine is not installed. Install it in your active environment with "
        f"{FAST_WHISPER_REQUIREMENT}.",
    )


def _download_whisper_model(spec: SpeechModelSpec, progress=None) -> Path:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required to acquire whisper models in this phase. "
            f"Install {FAST_WHISPER_REQUIREMENT} first."
        ) from exc

    if progress is not None:
        progress(0, 0)

    # Creating the model object triggers download into download_root if absent.
    # This is intentionally phase-1 infra only and does not run transcription.
    _ = WhisperModel(
        spec.repo_id,
        device="cpu",
        compute_type="int8",
        download_root=str(whisper_cache_dir()),
    )

    if progress is not None:
        progress(1, 1)

    path = model_path(spec)
    if not is_downloaded(spec):
        raise RuntimeError(
            "Whisper model download did not produce the expected local cache layout."
        )
    return path


def download_model(spec: SpeechModelSpec, progress=None) -> Path:
    if spec.family != "whisper":
        raise RuntimeError(
            "Only whisper model acquisition is enabled in phase 1. "
            "Parakeet rollout remains gated for later phases."
        )
    if is_downloaded(spec):
        return model_path(spec)
    return _download_whisper_model(spec, progress=progress)


def remove_model(spec: SpeechModelSpec) -> bool:
    path = model_path(spec)
    if not path.exists():
        return False
    shutil.rmtree(path, ignore_errors=True)
    return True
