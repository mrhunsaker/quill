from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from quill.core import read_aloud as read_aloud_module
from quill.core.read_aloud import (
    ReadAloudUnavailableError,
    ReadAloudController,
    discover_piper_executable,
    list_dectalk_voices,
    list_voices,
    sentence_spans,
    synthesize_with_piper,
)
from quill.core.read_aloud import (
    ESPEAK_ENGLISH_VOICES,
    KOKORO_VOICES,
    discover_espeak_executable,
    discover_vibevoice_executable,
    list_espeak_english_voices,
    list_kokoro_voices,
    list_piper_voices,
    list_vibevoice_voices,
    synthesize_to_file_with_dectalk,
    synthesize_to_file_with_pyttsx3,
    synthesize_with_espeak,
    synthesize_with_vibevoice,
)


def test_sentence_spans() -> None:
    spans = sentence_spans("One. Two! Three?")
    assert [(span.start, span.end) for span in spans] == [(0, 5), (5, 10), (10, 16)]


def test_list_voices_uses_backend(monkeypatch) -> None:
    class FakeVoice:
        id = "voice-1"
        name = "Voice 1"

    class FakeEngine:
        def __init__(self) -> None:
            self.spoken: list[str] = []
            self.properties: dict[str, object] = {}

        def getProperty(self, name: str):  # noqa: N802
            if name == "voices":
                return [FakeVoice()]
            return None

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            self.properties[name] = value

        def say(self, text: str) -> None:
            self.spoken.append(text)

        def runAndWait(self) -> None:  # noqa: N802
            return None

        def stop(self) -> None:
            return None

    engine = FakeEngine()
    monkeypatch.setattr(read_aloud_module, "pyttsx3", SimpleNamespace(init=lambda: engine))

    voices = list_voices()
    assert [(voice.id, voice.name) for voice in voices] == [("voice-1", "Voice 1")]


def test_read_aloud_controller_speaks_sentences(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.spoken: list[str] = []
            self.properties: dict[str, object] = {}

        def getProperty(self, name: str):  # noqa: N802
            return []

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            self.properties[name] = value

        def say(self, text: str) -> None:
            self.spoken.append(text)

        def runAndWait(self) -> None:  # noqa: N802
            return None

        def stop(self) -> None:
            return None

    engine = FakeEngine()
    monkeypatch.setattr(read_aloud_module, "pyttsx3", SimpleNamespace(init=lambda: engine))

    controller = ReadAloudController()
    controller.start("One. Two!", 0, "voice-1")
    assert controller._thread is not None
    controller._thread.join(timeout=1)

    assert engine.properties["voice"] == "voice-1"
    assert engine.spoken == ["One.", "Two!"]


def test_list_dectalk_voices_has_expected_defaults() -> None:
    voices = list_dectalk_voices()
    assert voices
    assert voices[0].id == "paul"
    assert any(voice.id == "betty" for voice in voices)


def test_build_dectalk_payload_includes_voice_and_rate() -> None:
    controller = ReadAloudController()
    payload = controller._build_dectalk_payload("Hello there", "paul", 200)
    assert "[:np]" in payload
    assert "[:ra 200]" in payload
    assert "Hello there" in payload


def test_discover_piper_executable_uses_explicit_path(tmp_path: Path) -> None:
    exe = tmp_path / "piper.exe"
    exe.write_text("binary", encoding="utf-8")
    discovered = discover_piper_executable(str(exe))
    assert discovered == exe.resolve()


def test_synthesize_with_piper_runs_process(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "piper.exe"
    model = tmp_path / "voice.onnx"
    output = tmp_path / "speech.wav"
    exe.write_text("binary", encoding="utf-8")
    model.write_text("model", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    called: dict[str, object] = {}

    def fake_run(command, **kwargs):
        called["command"] = command
        called["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr(read_aloud_module.subprocess, "run", fake_run)

    synthesize_with_piper(
        "Hello from piper",
        output,
        executable_path=exe,
        model_path=model,
    )
    assert called["command"] == [
        str(exe),
        "--model",
        str(model),
        "--output_file",
        str(output),
    ]
    assert called["kwargs"]["input"] == "Hello from piper"


def test_synthesize_with_piper_raises_for_failure(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "piper.exe"
    model = tmp_path / "voice.onnx"
    output = tmp_path / "speech.wav"
    exe.write_text("binary", encoding="utf-8")
    model.write_text("model", encoding="utf-8")

    class Completed:
        returncode = 1
        stdout = ""
        stderr = "bad model"

    monkeypatch.setattr(read_aloud_module.subprocess, "run", lambda *_args, **_kwargs: Completed())

    try:
        synthesize_with_piper(
            "Hello from piper",
            output,
            executable_path=exe,
            model_path=model,
        )
    except ReadAloudUnavailableError as exc:
        assert "Piper failed" in str(exc)
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


# ---------------------------------------------------------------------------
# eSpeak-NG helpers
# ---------------------------------------------------------------------------

def test_list_espeak_english_voices_covers_key_variants() -> None:
    voices = list_espeak_english_voices()
    ids = [v.id for v in voices]
    assert "en" in ids
    assert "en-us" in ids
    assert "en-gb" in ids
    assert "en-au" in ids
    # eSpeak is English-only in Quill — no non-English variants expected
    assert all(id_.startswith("en") for id_ in ids)


def test_discover_espeak_executable_explicit_path(tmp_path: Path) -> None:
    exe = tmp_path / "espeak-ng.exe"
    exe.write_text("binary", encoding="utf-8")
    found = discover_espeak_executable(str(exe))
    assert found == exe.resolve()


def test_discover_espeak_executable_missing_returns_none() -> None:
    found = discover_espeak_executable("/nonexistent/path/espeak-ng.exe")
    assert found is None


def test_synthesize_with_espeak_calls_process(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "espeak-ng.exe"
    exe.write_text("binary", encoding="utf-8")
    output = tmp_path / "speech.wav"

    class Completed:
        returncode = 0

    called: dict[str, object] = {}

    def fake_run(command, **kwargs):
        called["command"] = command
        return Completed()

    monkeypatch.setattr(read_aloud_module.subprocess, "run", fake_run)
    synthesize_with_espeak("Hello world", output, executable_path=exe, voice="en-us", rate=175)
    cmd = called["command"]
    assert str(exe) in cmd
    assert "-v" in cmd and "en-us" in cmd
    assert "-w" in cmd and str(output) in cmd


def test_synthesize_with_espeak_raises_on_failure(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "espeak-ng.exe"
    exe.write_text("binary", encoding="utf-8")
    output = tmp_path / "speech.wav"

    class Completed:
        returncode = 1
        stderr = b"error"
        stdout = b""

    monkeypatch.setattr(read_aloud_module.subprocess, "run", lambda *_a, **_kw: Completed())
    try:
        synthesize_with_espeak("Hi", output, executable_path=exe, voice="en")
    except ReadAloudUnavailableError as exc:
        assert "eSpeak-NG" in str(exc)
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


# ---------------------------------------------------------------------------
# Kokoro helpers
# ---------------------------------------------------------------------------

def test_list_kokoro_voices_has_american_and_british() -> None:
    voices = list_kokoro_voices()
    ids = [v.id for v in voices]
    assert any(i.startswith("af_") for i in ids), "no American female voices"
    assert any(i.startswith("am_") for i in ids), "no American male voices"
    assert any(i.startswith("bf_") for i in ids), "no British female voices"
    assert any(i.startswith("bm_") for i in ids), "no British male voices"


def test_list_kokoro_voices_default_is_af_heart() -> None:
    voices = list_kokoro_voices()
    assert voices[0].id == "af_heart"


def test_synthesize_with_kokoro_raises_when_package_missing(monkeypatch, tmp_path: Path) -> None:
    import builtins
    real_import = builtins.__import__

    def _block(name, *args, **kwargs):
        if name == "kokoro":
            raise ImportError("no kokoro")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block)
    from quill.core.read_aloud import synthesize_with_kokoro
    try:
        synthesize_with_kokoro("Hello", tmp_path / "out.wav")
    except ReadAloudUnavailableError as exc:
        assert "kokoro" in str(exc).lower()
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


# ---------------------------------------------------------------------------
# VibeVoice helpers
# ---------------------------------------------------------------------------

def test_discover_vibevoice_explicit_path(tmp_path: Path) -> None:
    exe = tmp_path / "vibevoice.exe"
    exe.write_text("binary", encoding="utf-8")
    found = discover_vibevoice_executable(str(exe))
    assert found == exe.resolve()


def test_list_vibevoice_voices_fallback_when_no_exe() -> None:
    voices = list_vibevoice_voices("/nonexistent/vibevoice.exe")
    assert len(voices) == 1
    assert voices[0].id == "default"


def test_synthesize_with_vibevoice_calls_process(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "vibevoice.exe"
    exe.write_text("binary", encoding="utf-8")
    output = tmp_path / "speech.wav"

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    called: dict[str, object] = {}

    def fake_run(command, **kwargs):
        called["command"] = command
        called["input"] = kwargs.get("input", "")
        return Completed()

    monkeypatch.setattr(read_aloud_module.subprocess, "run", fake_run)
    synthesize_with_vibevoice("Hello world", output, executable_path=exe, voice="alloy")
    assert str(exe) in called["command"]
    assert "--output" in called["command"]
    assert "--speaker" in called["command"]
    assert "alloy" in called["command"]


def test_synthesize_with_vibevoice_raises_on_failure(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "vibevoice.exe"
    exe.write_text("binary", encoding="utf-8")
    output = tmp_path / "speech.wav"

    class Completed:
        returncode = 1
        stdout = ""
        stderr = "failed"

    monkeypatch.setattr(read_aloud_module.subprocess, "run", lambda *_a, **_kw: Completed())
    try:
        synthesize_with_vibevoice("Hi", output, executable_path=exe)
    except ReadAloudUnavailableError as exc:
        assert "VibeVoice" in str(exc)
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


# ---------------------------------------------------------------------------
# Pyttsx3 file synthesis helper
# ---------------------------------------------------------------------------

def test_synthesize_to_file_with_pyttsx3_saves_file(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "speech.wav"

    class FakeEngine:
        def __init__(self) -> None:
            self.properties: dict[str, object] = {}
            self.saved: list[tuple[str, str]] = []

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            self.properties[name] = value

        def save_to_file(self, text: str, path: str) -> None:  # noqa: N802
            self.saved.append((text, path))

        def runAndWait(self) -> None:  # noqa: N802
            pass

        def stop(self) -> None:
            pass

    engine = FakeEngine()
    monkeypatch.setattr(read_aloud_module, "pyttsx3", SimpleNamespace(init=lambda: engine))
    synthesize_to_file_with_pyttsx3("Hello", output, voice="voice-1", rate=200, volume=1.0)
    assert engine.saved == [("Hello", str(output))]
    assert engine.properties["rate"] == 200


# ---------------------------------------------------------------------------
# DECtalk file synthesis helper
# ---------------------------------------------------------------------------

def test_synthesize_to_file_with_dectalk_calls_wav_flag(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "speak.exe"
    exe.write_text("binary", encoding="utf-8")
    output = tmp_path / "speech.wav"

    class Completed:
        returncode = 0
        stdout = b""
        stderr = b""

    called: dict[str, object] = {}

    def fake_run(command, **kwargs):
        called["command"] = command
        return Completed()

    monkeypatch.setattr(read_aloud_module.subprocess, "run", fake_run)
    synthesize_to_file_with_dectalk("Hello", output, executable_path=exe, voice="paul", rate=200)
    cmd = called["command"]
    assert "-wav" in cmd
    assert str(output) in cmd


# ---------------------------------------------------------------------------
# Piper voice list from directory
# ---------------------------------------------------------------------------

def test_list_piper_voices_finds_onnx_files(tmp_path: Path) -> None:
    (tmp_path / "en_US-amy-medium.onnx").write_text("model", encoding="utf-8")
    (tmp_path / "en_GB-alan-low.onnx").write_text("model", encoding="utf-8")
    voices = list_piper_voices(str(tmp_path))
    names = {v.name for v in voices}
    assert "en_US-amy-medium" in names
    assert "en_GB-alan-low" in names


def test_list_piper_voices_empty_when_no_dir() -> None:
    assert list_piper_voices("") == []
    assert list_piper_voices("/nonexistent/path") == []


# ---------------------------------------------------------------------------
# Settings round-trip: new fields
# ---------------------------------------------------------------------------

def test_settings_round_trip_all_engine_fields() -> None:
    from quill.core.settings import Settings
    data = {
        "read_aloud_engine": "espeak",
        "read_aloud_espeak_voice": "en-gb",
        "read_aloud_espeak_rate": 160,
        "read_aloud_kokoro_voice": "am_adam",
        "read_aloud_kokoro_speed": 1.25,
        "read_aloud_vibevoice_voice": "onyx",
        "read_aloud_piper_model_dir": "/models/piper",
    }
    s = Settings.from_dict(data)
    assert s.read_aloud_engine == "espeak"
    assert s.read_aloud_espeak_voice == "en-gb"
    assert s.read_aloud_espeak_rate == 160
    assert s.read_aloud_kokoro_voice == "am_adam"
    assert abs(s.read_aloud_kokoro_speed - 1.25) < 0.001
    assert s.read_aloud_vibevoice_voice == "onyx"
    assert s.read_aloud_piper_model_dir == "/models/piper"


def test_settings_rejects_unknown_engine() -> None:
    from quill.core.settings import Settings
    s = Settings.from_dict({"read_aloud_engine": "bananavoice"})
    assert s.read_aloud_engine == "pyttsx3"


def test_settings_clamps_espeak_rate() -> None:
    from quill.core.settings import Settings
    s_low = Settings.from_dict({"read_aloud_espeak_rate": 10})
    s_high = Settings.from_dict({"read_aloud_espeak_rate": 999})
    assert s_low.read_aloud_espeak_rate == 80
    assert s_high.read_aloud_espeak_rate == 450


def test_settings_clamps_kokoro_speed() -> None:
    from quill.core.settings import Settings
    s_low = Settings.from_dict({"read_aloud_kokoro_speed": 0.1})
    s_high = Settings.from_dict({"read_aloud_kokoro_speed": 5.0})
    assert s_low.read_aloud_kokoro_speed == 0.5
    assert s_high.read_aloud_kokoro_speed == 2.0


# ---------------------------------------------------------------------------
# Controller: all engines reach error when executable missing
# ---------------------------------------------------------------------------

def test_controller_espeak_raises_when_not_found() -> None:
    controller = ReadAloudController()
    try:
        controller.start(
            "Hello", 0, "",
            engine_name="espeak",
            espeak_executable="/nonexistent/espeak-ng.exe",
            espeak_voice="en",
        )
    except ReadAloudUnavailableError as exc:
        assert "eSpeak-NG" in str(exc)
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


def test_controller_vibevoice_raises_when_not_found() -> None:
    controller = ReadAloudController()
    try:
        controller.start(
            "Hello", 0, "",
            engine_name="vibevoice",
            vibevoice_executable="/nonexistent/vibevoice.exe",
        )
    except ReadAloudUnavailableError as exc:
        assert "VibeVoice" in str(exc)
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")


def test_controller_piper_raises_when_model_missing(tmp_path: Path) -> None:
    exe = tmp_path / "piper.exe"
    exe.write_text("binary", encoding="utf-8")
    controller = ReadAloudController()
    try:
        controller.start(
            "Hello", 0, "",
            engine_name="piper",
            piper_executable=str(exe),
            piper_model="/nonexistent/voice.onnx",
        )
    except ReadAloudUnavailableError as exc:
        assert "model" in str(exc).lower()
    else:
        raise AssertionError("Expected ReadAloudUnavailableError")
