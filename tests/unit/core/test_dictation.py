from __future__ import annotations

from quill.core.dictation import DictationController, DictationSettings, _transcribe_audio


class _FakeRecognizer:
    def __init__(self) -> None:
        self.whisper_calls: list[tuple[object, str, str]] = []
        self.vosk_payload: str | dict[str, str] = '{"text":"hello world"}'

    def recognize_whisper(self, audio: object, *, model: str, language: str) -> str:
        self.whisper_calls.append((audio, model, language))
        return "dictated phrase"

    def recognize_vosk(self, _audio: object) -> str | dict[str, str]:
        return self.vosk_payload


def test_transcribe_audio_uses_whisper_engine() -> None:
    recognizer = _FakeRecognizer()
    text = _transcribe_audio(
        recognizer,
        object(),
        DictationSettings(engine="whisper", model="tiny", language="en-US"),
    )
    assert text == "dictated phrase"
    assert recognizer.whisper_calls[0][1:] == ("tiny", "en-US")


def test_transcribe_audio_parses_vosk_json() -> None:
    recognizer = _FakeRecognizer()
    recognizer.vosk_payload = '{"text":"from vosk"}'
    text = _transcribe_audio(recognizer, object(), DictationSettings(engine="vosk"))
    assert text == "from vosk"


def test_stop_returns_joined_segments_and_resets_state() -> None:
    controller = DictationController()
    controller._segments = ["first", " ", "second"]  # type: ignore[attr-defined]
    result = controller.stop()
    assert result == "first second"
    assert controller.state == "idle"
