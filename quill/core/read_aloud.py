from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

try:
    import pyttsx3  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional runtime dependency
    pyttsx3 = None

try:
    import winsound as _winsound  # type: ignore[import]
except ImportError:  # pragma: no cover - non-Windows
    _winsound = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class VoiceOption:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class SentenceSpan:
    start: int
    end: int


DECTALK_VOICE_COMMANDS: dict[str, str] = {
    "paul": "[:np]",
    "harry": "[:nh]",
    "dennis": "[:nd]",
    "frank": "[:nf]",
    "betty": "[:nb]",
    "ursula": "[:nu]",
    "rita": "[:nr]",
    "wendy": "[:nw]",
    "kit": "[:nk]",
}

DECTALK_RELEASE_ZIP_URL = "https://github.com/dectalk/dectalk/releases/download/2023-10-30/vs2022.zip"

KOKORO_VOICES: list[tuple[str, str]] = [
    ("af_heart", "Heart (American Female, warm)"),
    ("af_bella", "Bella (American Female, expressive)"),
    ("af_nicole", "Nicole (American Female, conversational)"),
    ("af_aoede", "Aoede (American Female)"),
    ("af_kore", "Kore (American Female)"),
    ("af_sarah", "Sarah (American Female)"),
    ("af_sky", "Sky (American Female)"),
    ("am_adam", "Adam (American Male, deep)"),
    ("am_echo", "Echo (American Male)"),
    ("am_eric", "Eric (American Male)"),
    ("am_fenrir", "Fenrir (American Male)"),
    ("am_liam", "Liam (American Male)"),
    ("am_michael", "Michael (American Male)"),
    ("am_onyx", "Onyx (American Male)"),
    ("am_puck", "Puck (American Male)"),
    ("bf_alice", "Alice (British Female)"),
    ("bf_emma", "Emma (British Female)"),
    ("bf_isabella", "Isabella (British Female)"),
    ("bf_lily", "Lily (British Female)"),
    ("bm_daniel", "Daniel (British Male)"),
    ("bm_fable", "Fable (British Male)"),
    ("bm_george", "George (British Male)"),
    ("bm_lewis", "Lewis (British Male)"),
]

ESPEAK_ENGLISH_VOICES: list[tuple[str, str]] = [
    ("en", "English (default)"),
    ("en-us", "English (US)"),
    ("en-gb", "English (UK / RP)"),
    ("en-au", "English (Australian)"),
    ("en-ca", "English (Canadian)"),
    ("en-in", "English (Indian)"),
    ("en-sc", "English (Scottish)"),
    ("en-wls", "English (Welsh)"),
    ("en-rp", "English (Received Pronunciation)"),
    ("en-gb-x-rp", "English (RP variant)"),
]

RHVOICE_ENGLISH_VOICES: list[tuple[str, str]] = [
    ("alan", "Alan (English)"),
    ("slt", "SLT (English)"),
    ("bdl", "BDL (English)"),
]

MELOTTS_ENGLISH_VOICES: list[tuple[str, str]] = [
    ("en-us", "MeloTTS English (US)"),
    ("en-br", "MeloTTS English (British)"),
    ("en-india", "MeloTTS English (India)"),
]

CHATTERBOX_ENGLISH_VOICES: list[tuple[str, str]] = [
    ("english_narrator", "Narrator (English)"),
    ("english_warm", "Warm (English)"),
    ("english_clear", "Clear (English)"),
]

OPENVOICE_ENGLISH_VOICES: list[tuple[str, str]] = [
    ("en-base", "OpenVoice Base (English)"),
    ("en-bright", "OpenVoice Bright (English)"),
    ("en-calm", "OpenVoice Calm (English)"),
]


def discover_dectalk_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "dectalk"
        for relative in ("speak.exe", "AMD64/speak.exe", "IA32/speak.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    return None


def discover_piper_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "piper"
        for relative in ("piper.exe", "piper/piper.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    return None


def synthesize_with_piper(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    model_path: Path,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if not executable_path.exists():
        raise ReadAloudUnavailableError("Piper executable was not found")
    if not model_path.exists():
        raise ReadAloudUnavailableError("Piper model file was not found")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable_path),
        "--model",
        str(model_path),
        "--output_file",
        str(output_path),
    ]
    completed = subprocess.run(
        command,
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if detail:
            raise ReadAloudUnavailableError(f"Piper failed: {detail}")
        raise ReadAloudUnavailableError(
            f"Piper exited with code {completed.returncode}. Check executable and model settings."
        )


def discover_vibevoice_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "vibevoice"
        for relative in ("vibevoice.exe", "vibevoice/vibevoice.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    return None


def discover_espeak_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "espeak-ng"
        for relative in ("espeak-ng.exe", "espeak-ng/espeak-ng.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    import shutil as _shutil
    found = _shutil.which("espeak-ng")
    if found:
        return Path(found).resolve()
    return None


def discover_rhvoice_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "rhvoice"
        for relative in ("rhvoice.exe", "RHVoice-test.exe", "bin/rhvoice.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    found = shutil.which("rhvoice") or shutil.which("rhvoice.exe")
    if found:
        return Path(found).resolve()
    return None


def discover_melotts_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "melotts"
        for relative in ("melotts.exe", "melo-tts.exe", "bin/melotts.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    found = shutil.which("melotts") or shutil.which("melotts.exe")
    if found:
        return Path(found).resolve()
    return None


def discover_chatterbox_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "chatterbox"
        for relative in ("chatterbox.exe", "bin/chatterbox.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    found = shutil.which("chatterbox") or shutil.which("chatterbox.exe")
    if found:
        return Path(found).resolve()
    return None


def discover_openvoice_executable(configured_path: str = "") -> Path | None:
    if configured_path.strip():
        candidate = Path(configured_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
    app_root = os.environ.get("QUILL_APP_ROOT", "").strip()
    if app_root:
        bundled = Path(app_root) / "tools" / "speech" / "openvoice"
        for relative in ("openvoice.exe", "bin/openvoice.exe"):
            probe = bundled / relative
            if probe.exists():
                return probe.resolve()
    found = shutil.which("openvoice") or shutil.which("openvoice.exe")
    if found:
        return Path(found).resolve()
    return None


def list_kokoro_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in KOKORO_VOICES]


def list_piper_voices(model_search_path: str = "") -> list[VoiceOption]:
    """Return ONNX model files found under model_search_path as voice options."""
    if not model_search_path.strip():
        return []
    root = Path(model_search_path).expanduser()
    if not root.exists():
        return []
    voices: list[VoiceOption] = []
    for onnx_file in sorted(root.rglob("*.onnx")):
        voices.append(VoiceOption(id=str(onnx_file), name=onnx_file.stem))
    return voices


def list_vibevoice_voices(executable_path: str = "") -> list[VoiceOption]:
    exe = discover_vibevoice_executable(executable_path)
    if exe is None:
        return [VoiceOption(id="default", name="Default")]
    try:
        completed = subprocess.run(
            [str(exe), "--list-voices"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        lines = (completed.stdout or "").strip().splitlines()
        voices = [VoiceOption(id=ln.strip(), name=ln.strip()) for ln in lines if ln.strip()]
        return voices if voices else [VoiceOption(id="default", name="Default")]
    except Exception:  # noqa: BLE001
        return [VoiceOption(id="default", name="Default")]


def list_espeak_english_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in ESPEAK_ENGLISH_VOICES]


def list_rhvoice_english_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in RHVOICE_ENGLISH_VOICES]


def list_melotts_english_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in MELOTTS_ENGLISH_VOICES]


def list_chatterbox_english_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in CHATTERBOX_ENGLISH_VOICES]


def list_openvoice_english_voices() -> list[VoiceOption]:
    return [VoiceOption(id=vid, name=name) for vid, name in OPENVOICE_ENGLISH_VOICES]


def synthesize_with_kokoro(
    text: str,
    output_path: Path,
    *,
    voice: str = "af_heart",
    speed: float = 1.0,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    try:
        from kokoro import KPipeline  # type: ignore[import]
    except ImportError as exc:
        raise ReadAloudUnavailableError(
            "Kokoro TTS requires the 'kokoro' package (pip install kokoro)"
        ) from exc
    try:
        import numpy as np  # type: ignore[import]
    except ImportError as exc:
        raise ReadAloudUnavailableError("Kokoro TTS requires the 'numpy' package") from exc
    try:
        import soundfile as sf  # type: ignore[import]
    except ImportError as exc:
        raise ReadAloudUnavailableError(
            "Kokoro audio saving requires the 'soundfile' package (pip install soundfile)"
        ) from exc
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lang_code = "b" if voice.startswith("b") else "a"
    pipeline = KPipeline(lang_code=lang_code)
    samples: list[np.ndarray] = []
    for _g, _p, audio in pipeline(text, voice=voice, speed=float(speed)):
        if audio is not None and len(audio) > 0:
            samples.append(audio)
    if not samples:
        raise ReadAloudUnavailableError("Kokoro produced no audio output")
    sf.write(str(output_path), np.concatenate(samples), 24000)


def synthesize_with_vibevoice(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "default",
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if not executable_path.exists():
        raise ReadAloudUnavailableError("VibeVoice executable was not found")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(executable_path), "--output", str(output_path)]
    if voice and voice != "default":
        command += ["--speaker", voice]
    completed = subprocess.run(
        command,
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ReadAloudUnavailableError(
            f"VibeVoice failed: {detail}" if detail
            else f"VibeVoice exited with code {completed.returncode}."
        )


def synthesize_with_espeak(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "en",
    rate: int = 175,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if not executable_path.exists():
        raise ReadAloudUnavailableError("eSpeak-NG executable was not found")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bounded_rate = max(80, min(450, int(rate)))
    command = [str(executable_path), "-v", voice, "-s", str(bounded_rate), "-w", str(output_path), text]
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        raw = completed.stderr or completed.stdout or b""
        detail = raw.decode("utf-8", errors="replace").strip() if isinstance(raw, bytes) else str(raw).strip()
        raise ReadAloudUnavailableError(
            f"eSpeak-NG failed: {detail}" if detail
            else f"eSpeak-NG exited with code {completed.returncode}."
        )


def _synthesize_with_cli_engine(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str,
    rate: int,
    engine_label: str,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if not executable_path.exists():
        raise ReadAloudUnavailableError(f"{engine_label} executable was not found")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable_path),
        "--text",
        text,
        "--output",
        str(output_path),
        "--voice",
        voice,
        "--rate",
        str(max(80, min(450, int(rate)))),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ReadAloudUnavailableError(
            f"{engine_label} failed: {detail}" if detail
            else f"{engine_label} exited with code {completed.returncode}."
        )


def synthesize_with_rhvoice(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "alan",
    rate: int = 180,
) -> None:
    _synthesize_with_cli_engine(
        text,
        output_path,
        executable_path=executable_path,
        voice=voice,
        rate=rate,
        engine_label="RHVoice",
    )


def synthesize_with_melotts(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "en-us",
    rate: int = 180,
) -> None:
    _synthesize_with_cli_engine(
        text,
        output_path,
        executable_path=executable_path,
        voice=voice,
        rate=rate,
        engine_label="MeloTTS",
    )


def synthesize_with_chatterbox(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "english_narrator",
    rate: int = 180,
) -> None:
    _synthesize_with_cli_engine(
        text,
        output_path,
        executable_path=executable_path,
        voice=voice,
        rate=rate,
        engine_label="Chatterbox",
    )


def synthesize_with_openvoice(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "en-base",
    rate: int = 180,
) -> None:
    _synthesize_with_cli_engine(
        text,
        output_path,
        executable_path=executable_path,
        voice=voice,
        rate=rate,
        engine_label="OpenVoice",
    )


def synthesize_to_file_with_pyttsx3(
    text: str,
    output_path: Path,
    *,
    voice: str = "",
    rate: int = 200,
    volume: float = 1.0,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if pyttsx3 is None:
        raise ReadAloudUnavailableError("pyttsx3 is not available")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    try:
        if voice:
            engine.setProperty("voice", voice)
        engine.setProperty("rate", int(rate))
        engine.setProperty("volume", max(0.0, min(float(volume), 1.0)))
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
    finally:
        engine.stop()


def synthesize_to_file_with_dectalk(
    text: str,
    output_path: Path,
    *,
    executable_path: Path,
    voice: str = "paul",
    rate: int = 180,
) -> None:
    if not text.strip():
        raise ReadAloudUnavailableError("Cannot generate speech from empty text")
    if not executable_path.exists():
        raise ReadAloudUnavailableError("DECtalk executable was not found")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    voice_cmd = DECTALK_VOICE_COMMANDS.get(voice.strip().lower(), "")
    bounded_rate = max(75, min(650, int(rate)))
    payload = f"{voice_cmd} [:ra {bounded_rate}] {text}".strip()
    create_no_window = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8", errors="replace"
    ) as fh:
        fh.write(payload)
        tmp_path = Path(fh.name)
    try:
        completed = subprocess.run(
            [str(executable_path), "-file", str(tmp_path), "-wav", str(output_path)],
            cwd=str(executable_path.parent),
            capture_output=True,
            creationflags=create_no_window,
            check=False,
        )
        if completed.returncode != 0:
            raise ReadAloudUnavailableError(
                f"DECtalk exited with code {completed.returncode}."
            )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def download_dectalk_runtime(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    archive = target_dir / "vs2022.zip"
    with urllib.request.urlopen(DECTALK_RELEASE_ZIP_URL, timeout=180) as response:  # noqa: S310
        archive.write_bytes(response.read())
    extract_root = target_dir / "release"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extract_root)
    for candidate in (
        extract_root / "AMD64" / "speak.exe",
        extract_root / "speak.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    raise ReadAloudUnavailableError("Downloaded DECtalk package did not contain speak.exe")


def list_dectalk_voices() -> list[VoiceOption]:
    return [
        VoiceOption(id="paul", name="Paul"),
        VoiceOption(id="harry", name="Harry"),
        VoiceOption(id="dennis", name="Dennis"),
        VoiceOption(id="frank", name="Frank"),
        VoiceOption(id="betty", name="Betty"),
        VoiceOption(id="ursula", name="Ursula"),
        VoiceOption(id="rita", name="Rita"),
        VoiceOption(id="wendy", name="Wendy"),
        VoiceOption(id="kit", name="Kit"),
    ]


def list_voices() -> list[VoiceOption]:
    if pyttsx3 is None:
        return []
    engine = pyttsx3.init()
    try:
        voices = []
        for voice in engine.getProperty("voices") or []:
            voice_id = str(getattr(voice, "id", "")).strip()
            if not voice_id:
                continue
            name = str(getattr(voice, "name", voice_id)).strip() or voice_id
            voices.append(VoiceOption(id=voice_id, name=name))
        return voices
    finally:
        engine.stop()


def sentence_spans(text: str) -> list[SentenceSpan]:
    spans: list[SentenceSpan] = []
    for match in re.finditer(r".+?(?:[.!?]+(?:\s+|$)|\n+|$)", text, re.DOTALL):
        start, end = match.span()
        if text[start:end].strip():
            spans.append(SentenceSpan(start=start, end=end))
    if not spans and text.strip():
        spans.append(SentenceSpan(0, len(text)))
    return spans


class ReadAloudUnavailableError(RuntimeError):
    pass


class ReadAloudController:
    def __init__(self) -> None:
        self._state = "idle"
        self._cursor = 0
        self._thread: threading.Thread | None = None
        self._active_process: subprocess.Popen[bytes] | None = None
        self._active_wav_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def cursor(self) -> int:
        with self._lock:
            return self._cursor

    def start(  # noqa: PLR0912,PLR0913
        self,
        text: str,
        cursor: int,
        voice_id: str,
        *,
        engine_name: str = "pyttsx3",
        rate: int | None = None,
        volume: float | None = None,
        pitch: int | None = None,
        dectalk_executable: str = "",
        dectalk_voice: str = "",
        dectalk_rate: int = 180,
        dectalk_dictionary: str = "",
        piper_executable: str = "",
        piper_model: str = "",
        kokoro_voice: str = "af_heart",
        kokoro_speed: float = 1.0,
        vibevoice_executable: str = "",
        vibevoice_voice: str = "default",
        espeak_executable: str = "",
        espeak_voice: str = "en",
        espeak_rate: int = 175,
        rhvoice_executable: str = "",
        rhvoice_voice: str = "alan",
        rhvoice_rate: int = 180,
        melotts_executable: str = "",
        melotts_voice: str = "en-us",
        melotts_rate: int = 180,
        chatterbox_executable: str = "",
        chatterbox_voice: str = "english_narrator",
        chatterbox_rate: int = 180,
        openvoice_executable: str = "",
        openvoice_voice: str = "en-base",
        openvoice_rate: int = 180,
        openvoice_consent: bool = False,
        end: int | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        on_state_change: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        normalized_engine = engine_name.strip().lower() or "pyttsx3"
        _valid_engines = {
            "pyttsx3",
            "dectalk",
            "piper",
            "kokoro",
            "vibevoice",
            "espeak",
            "rhvoice",
            "melotts",
            "chatterbox",
            "openvoice",
        }
        if normalized_engine == "pyttsx3" and pyttsx3 is None:
            raise ReadAloudUnavailableError("pyttsx3 is not available")
        if normalized_engine == "dectalk":
            if discover_dectalk_executable(dectalk_executable) is None:
                raise ReadAloudUnavailableError("DECtalk executable was not found")
        if normalized_engine == "piper":
            if discover_piper_executable(piper_executable) is None:
                raise ReadAloudUnavailableError("Piper executable was not found")
            _mdl = Path(piper_model).expanduser() if piper_model.strip() else None
            if _mdl is None or not _mdl.exists():
                raise ReadAloudUnavailableError("Piper model (.onnx) file was not found")
        if normalized_engine == "vibevoice" and discover_vibevoice_executable(vibevoice_executable) is None:
            raise ReadAloudUnavailableError("VibeVoice executable was not found")
        if normalized_engine == "espeak" and discover_espeak_executable(espeak_executable) is None:
            raise ReadAloudUnavailableError(
                "eSpeak-NG executable was not found. "
                "Install eSpeak-NG or configure the path in Read Aloud Settings."
            )
        if normalized_engine == "rhvoice" and discover_rhvoice_executable(rhvoice_executable) is None:
            raise ReadAloudUnavailableError("RHVoice executable was not found")
        if normalized_engine == "melotts" and discover_melotts_executable(melotts_executable) is None:
            raise ReadAloudUnavailableError("MeloTTS executable was not found")
        if normalized_engine == "chatterbox" and discover_chatterbox_executable(chatterbox_executable) is None:
            raise ReadAloudUnavailableError("Chatterbox executable was not found")
        if normalized_engine == "openvoice":
            if not openvoice_consent:
                raise ReadAloudUnavailableError(
                    "OpenVoice requires explicit consent before use. Enable consent in Speech settings."
                )
            if discover_openvoice_executable(openvoice_executable) is None:
                raise ReadAloudUnavailableError("OpenVoice executable was not found")
        if normalized_engine not in _valid_engines:
            raise ReadAloudUnavailableError(f"Unsupported read-aloud engine: {normalized_engine}")
        self.stop()
        spans = [span for span in sentence_spans(text) if span.end > cursor]
        if end is not None:
            spans = [span for span in spans if span.start < end]
        if not spans:
            stop_at = len(text) if end is None else min(len(text), max(cursor, end))
            spans = [SentenceSpan(cursor, stop_at)]
        with self._lock:
            self._state = "playing"
            self._cursor = cursor
        self._stop_event.clear()
        self._pause_event.clear()

        def worker() -> None:
            try:
                if normalized_engine == "pyttsx3":
                    self._run_pyttsx3(
                        spans, text,
                        voice_id=voice_id, rate=rate, volume=volume, pitch=pitch,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "dectalk":
                    self._run_dectalk(
                        spans, text,
                        executable=discover_dectalk_executable(dectalk_executable) or Path(dectalk_executable).expanduser(),
                        voice_id=dectalk_voice,
                        rate=dectalk_rate,
                        dictionary_path=Path(dectalk_dictionary).expanduser() if dectalk_dictionary.strip() else None,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "piper":
                    self._run_piper_live(
                        spans, text,
                        executable=discover_piper_executable(piper_executable) or Path(piper_executable).expanduser(),
                        model=Path(piper_model).expanduser(),
                        on_progress=on_progress,
                    )
                elif normalized_engine == "kokoro":
                    self._run_kokoro_live(
                        spans, text,
                        voice=kokoro_voice, speed=kokoro_speed,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "vibevoice":
                    self._run_vibevoice_live(
                        spans, text,
                        executable=discover_vibevoice_executable(vibevoice_executable) or Path(vibevoice_executable).expanduser(),
                        voice=vibevoice_voice,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "espeak":
                    self._run_espeak_live(
                        spans, text,
                        executable=discover_espeak_executable(espeak_executable) or Path(espeak_executable).expanduser(),
                        voice=espeak_voice, rate=espeak_rate,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "rhvoice":
                    self._run_rhvoice_live(
                        spans,
                        text,
                        executable=discover_rhvoice_executable(rhvoice_executable)
                        or Path(rhvoice_executable).expanduser(),
                        voice=rhvoice_voice,
                        rate=rhvoice_rate,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "melotts":
                    self._run_melotts_live(
                        spans,
                        text,
                        executable=discover_melotts_executable(melotts_executable)
                        or Path(melotts_executable).expanduser(),
                        voice=melotts_voice,
                        rate=melotts_rate,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "chatterbox":
                    self._run_chatterbox_live(
                        spans,
                        text,
                        executable=discover_chatterbox_executable(chatterbox_executable)
                        or Path(chatterbox_executable).expanduser(),
                        voice=chatterbox_voice,
                        rate=chatterbox_rate,
                        on_progress=on_progress,
                    )
                elif normalized_engine == "openvoice":
                    self._run_openvoice_live(
                        spans,
                        text,
                        executable=discover_openvoice_executable(openvoice_executable)
                        or Path(openvoice_executable).expanduser(),
                        voice=openvoice_voice,
                        rate=openvoice_rate,
                        on_progress=on_progress,
                    )
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    self._state = "idle"
                if on_error is not None:
                    on_error(str(exc))
                if on_state_change is not None:
                    on_state_change("error")
                return

            with self._lock:
                if self._pause_event.is_set():
                    self._state = "paused"
                else:
                    self._state = "idle"
            if on_state_change is not None:
                on_state_change(self.state)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def _run_pyttsx3(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        voice_id: str,
        rate: int | None,
        volume: float | None,
        pitch: int | None,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        engine = pyttsx3.init()
        try:
            if voice_id:
                engine.setProperty("voice", voice_id)
            if rate is not None:
                engine.setProperty("rate", int(rate))
            if volume is not None:
                engine.setProperty("volume", max(0.0, min(float(volume), 1.0)))
            if pitch is not None:
                try:
                    engine.setProperty("pitch", int(pitch))
                except Exception:  # noqa: BLE001
                    pass
            for span in spans:
                if self._stop_event.is_set() or self._pause_event.is_set():
                    break
                sentence = text[span.start : span.end].strip()
                if not sentence:
                    continue
                if on_progress is not None:
                    on_progress(span.start, span.end)
                engine.say(sentence)
                engine.runAndWait()
                with self._lock:
                    self._cursor = span.end
        finally:
            engine.stop()

    def _run_dectalk(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice_id: str,
        rate: int,
        dictionary_path: Path | None,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        working_dir = executable.parent
        self._ensure_dectalk_dictionary(working_dir, dictionary_path)
        for span in spans:
            if self._stop_event.is_set() or self._pause_event.is_set():
                break
            sentence = text[span.start : span.end].strip()
            if not sentence:
                continue
            if on_progress is not None:
                on_progress(span.start, span.end)
            payload = self._build_dectalk_payload(sentence, voice_id, rate)
            self._speak_sentence_dectalk(executable, payload)
            with self._lock:
                self._cursor = span.end

    def _build_dectalk_payload(self, sentence: str, voice_id: str, rate: int) -> str:
        parts: list[str] = []
        voice_cmd = DECTALK_VOICE_COMMANDS.get(voice_id.strip().lower(), "")
        if voice_cmd:
            parts.append(voice_cmd)
        bounded_rate = max(75, min(650, int(rate)))
        parts.append(f"[:ra {bounded_rate}]")
        parts.append(sentence)
        return " ".join(parts)

    def _ensure_dectalk_dictionary(self, working_dir: Path, dictionary_path: Path | None) -> None:
        target = working_dir / "dtalk_us.dic"
        if target.exists():
            return
        candidates: list[Path] = []
        if dictionary_path is not None:
            candidates.append(dictionary_path)
        candidates.extend(
            [
                working_dir / "dic" / "dtalk_us.dic",
                working_dir / "dtalk_us.dic",
            ]
        )
        source = next((path for path in candidates if path.exists()), None)
        if source is None:
            raise ReadAloudUnavailableError(
                "DECtalk dictionary dtalk_us.dic was not found. Configure dictionary path in Speech settings."
            )
        if source.resolve() == target.resolve():
            return
        target.write_bytes(source.read_bytes())

    def _speak_sentence_dectalk(self, executable: Path, payload: str) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt",
            encoding="utf-8",
            errors="replace",
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        create_no_window = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            process = subprocess.Popen(
                [str(executable), "-file", str(temp_path)],
                cwd=str(executable.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=create_no_window,
            )
            self._active_process = process
            while process.poll() is None:
                if self._stop_event.is_set() or self._pause_event.is_set():
                    process.terminate()
                    break
                time.sleep(0.05)
            exit_code = process.wait(timeout=2)
            if exit_code != 0 and not (self._stop_event.is_set() or self._pause_event.is_set()):
                raise ReadAloudUnavailableError(
                    f"DECtalk exited with code {exit_code}. Check executable and dictionary settings."
                )
        finally:
            self._active_process = None
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # WAV-based engine helpers
    # ------------------------------------------------------------------

    def _interrupt_wav(self) -> None:
        """Stop any in-progress winsound WAV playback immediately."""
        if _winsound is not None:
            try:
                _winsound.PlaySound(None, _winsound.SND_PURGE)
            except Exception:  # noqa: BLE001
                pass

    def _run_wav_sentences(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        on_progress: Callable[[int, int], None] | None,
        generate_sentence_wav: Callable[[str, Path], None],
    ) -> None:
        """Generate per-sentence WAV then play via winsound. Works for Piper/Kokoro/VibeVoice."""
        for span in spans:
            if self._stop_event.is_set() or self._pause_event.is_set():
                break
            sentence = text[span.start : span.end].strip()
            if not sentence:
                continue
            if on_progress is not None:
                on_progress(span.start, span.end)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
                wav_path = Path(fh.name)
            try:
                generate_sentence_wav(sentence, wav_path)
                if self._stop_event.is_set() or self._pause_event.is_set():
                    break
                if _winsound is not None and wav_path.exists():
                    play_done = threading.Event()

                    def _play(
                        p: Path = wav_path,
                        done: threading.Event = play_done,
                    ) -> None:
                        try:
                            _winsound.PlaySound(  # type: ignore[union-attr]
                                str(p),
                                _winsound.SND_FILENAME | _winsound.SND_NODEFAULT,
                            )
                        except Exception:  # noqa: BLE001
                            pass
                        finally:
                            done.set()

                    wav_thread = threading.Thread(target=_play, daemon=True)
                    self._active_wav_thread = wav_thread
                    wav_thread.start()
                    while not play_done.wait(timeout=0.05):
                        if self._stop_event.is_set() or self._pause_event.is_set():
                            self._interrupt_wav()
                            play_done.wait(timeout=0.5)
                            break
                    self._active_wav_thread = None
            finally:
                try:
                    wav_path.unlink(missing_ok=True)
                except OSError:
                    pass
            with self._lock:
                self._cursor = span.end

    def _run_piper_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        model: Path,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_piper(sentence, out, executable_path=executable, model_path=model)

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_kokoro_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        voice: str,
        speed: float,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_kokoro(sentence, out, voice=voice, speed=speed)

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_vibevoice_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_vibevoice(sentence, out, executable_path=executable, voice=voice)

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_espeak_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        rate: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        """eSpeak-NG plays audio directly - track process for pause/stop."""
        create_no_window = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for span in spans:
            if self._stop_event.is_set() or self._pause_event.is_set():
                break
            sentence = text[span.start : span.end].strip()
            if not sentence:
                continue
            if on_progress is not None:
                on_progress(span.start, span.end)
            bounded_rate = max(80, min(450, int(rate)))
            process = subprocess.Popen(
                [str(executable), "-v", voice, "-s", str(bounded_rate), sentence],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=create_no_window,
            )
            self._active_process = process
            while process.poll() is None:
                if self._stop_event.is_set() or self._pause_event.is_set():
                    process.terminate()
                    break
                time.sleep(0.05)
            self._active_process = None
            exit_code = process.wait(timeout=2)
            if exit_code != 0 and not (self._stop_event.is_set() or self._pause_event.is_set()):
                raise ReadAloudUnavailableError(f"eSpeak-NG exited with code {exit_code}.")
            with self._lock:
                self._cursor = span.end

    def _run_rhvoice_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        rate: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_rhvoice(
                sentence,
                out,
                executable_path=executable,
                voice=voice,
                rate=rate,
            )

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_melotts_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        rate: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_melotts(
                sentence,
                out,
                executable_path=executable,
                voice=voice,
                rate=rate,
            )

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_chatterbox_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        rate: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_chatterbox(
                sentence,
                out,
                executable_path=executable,
                voice=voice,
                rate=rate,
            )

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def _run_openvoice_live(
        self,
        spans: list[SentenceSpan],
        text: str,
        *,
        executable: Path,
        voice: str,
        rate: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> None:
        def gen(sentence: str, out: Path) -> None:
            synthesize_with_openvoice(
                sentence,
                out,
                executable_path=executable,
                voice=voice,
                rate=rate,
            )

        self._run_wav_sentences(spans, text, on_progress=on_progress, generate_sentence_wav=gen)

    def pause(self) -> None:
        with self._lock:
            if self._state != "playing":
                return
            self._state = "paused"
        self._pause_event.set()
        process = self._active_process
        if process is not None and process.poll() is None:
            process.terminate()
        self._interrupt_wav()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()
        process = self._active_process
        if process is not None and process.poll() is None:
            process.terminate()
        self._interrupt_wav()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.2)
        with self._lock:
            self._state = "idle"
        self._thread = None
