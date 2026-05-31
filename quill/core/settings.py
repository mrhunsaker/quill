from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from quill.core.paths import app_data_dir
from quill.core.storage import read_json, write_json_atomic

STATUS_BAR_ITEMS: tuple[str, ...] = (
    "line_column",
    "message",
    "word_count",
    "mode",
    "selection",
    "encoding",
    "line_endings",
    "spell_check",
    "background_tasks",
    "notifications",
    "read_aloud",
    "autosave",
    "search_term",
    "file_path",
)


def _default_status_bar_order() -> list[str]:
    return list(STATUS_BAR_ITEMS)


def _default_status_bar_hidden() -> list[str]:
    return [
        "selection",
        "encoding",
        "line_endings",
        "spell_check",
        "background_tasks",
        "notifications",
        "read_aloud",
        "autosave",
        "search_term",
        "file_path",
    ]


def _normalize_status_bar_order(raw: object) -> list[str]:
    if not isinstance(raw, list):
        values: list[str] = []
    else:
        values = [value for value in raw if isinstance(value, str)]
    allowed = set(STATUS_BAR_ITEMS)
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in allowed or value in seen:
            continue
        unique.append(value)
        seen.add(value)
    for item in STATUS_BAR_ITEMS:
        if item not in seen:
            unique.append(item)
    return unique


def _normalize_status_bar_hidden(raw: object, order: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return _default_status_bar_hidden()
    order_set = set(order)
    hidden: list[str] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str):
            continue
        if value not in order_set or value in seen:
            continue
        hidden.append(value)
        seen.add(value)
    return hidden


@dataclass(slots=True)
class Settings:
    theme: str = "system"
    keyboard_pack: str = "Quill Default"
    soft_wrap: bool = True
    wrap_find: bool = True
    csv_open_mode: str = "prompt"
    word_open_mode: str = "prompt"
    indent_with_tabs: bool = False
    indent_size: int = 4
    auto_check_updates: bool = False
    beta_updates: bool = False
    recent_files_limit: int = 10
    tray_enabled: bool = False
    persistent_undo: bool = False
    spellcheck_as_you_type: bool = False
    intellisense_as_you_type: bool = False
    snippet_trigger_expansion: bool = True
    preview_browser: str = "system"
    auto_side_preview: bool = True
    show_tab_control: bool = False
    title_bar_path_mode: str = "name"
    dirty_title_style: str = "text"
    start_with_no_document_open: bool = False
    read_aloud_engine: str = "pyttsx3"
    read_aloud_voice: str = ""
    read_aloud_rate: int = 200
    read_aloud_volume: int = 100
    read_aloud_pitch: int = 50
    read_aloud_dectalk_executable: str = ""
    read_aloud_dectalk_voice: str = "paul"
    read_aloud_dectalk_rate: int = 180
    read_aloud_dectalk_dictionary: str = ""
    read_aloud_piper_executable: str = ""
    read_aloud_piper_model: str = ""
    announcement_backend: str = "auto"
    read_aloud_piper_model_dir: str = ""
    read_aloud_kokoro_voice: str = "af_heart"
    read_aloud_kokoro_speed: float = 1.0
    read_aloud_vibevoice_executable: str = ""
    read_aloud_vibevoice_voice: str = "default"
    read_aloud_espeak_executable: str = ""
    read_aloud_espeak_voice: str = "en"
    read_aloud_espeak_rate: int = 175
    announcement_trace_enabled: bool = False
    assistant_enabled: bool = False
    assistant_prompt_style: str = "balanced"
    dictation_engine: str = "vosk"
    dictation_language: str = "en-US"
    dictation_model: str = "base"
    dictation_device_index: int = -1
    voice_commands_enabled: bool = False
    status_bar_order: list[str] = field(default_factory=_default_status_bar_order)
    status_bar_hidden: list[str] = field(default_factory=_default_status_bar_hidden)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        theme = str(data.get("theme", "system"))
        keyboard_pack = str(data.get("keyboard_pack", "Quill Default"))
        soft_wrap = bool(data.get("soft_wrap", True))
        wrap_find = bool(data.get("wrap_find", True))
        csv_open_mode = str(data.get("csv_open_mode", "prompt")).strip().lower()
        if csv_open_mode not in {"prompt", "text", "grid"}:
            csv_open_mode = "prompt"
        word_open_mode = str(data.get("word_open_mode", "prompt")).strip().lower()
        if word_open_mode not in {"prompt", "text", "structured"}:
            word_open_mode = "prompt"
        indent_with_tabs = bool(data.get("indent_with_tabs", False))
        indent_size = int(data.get("indent_size", 4))
        auto_check_updates = bool(data.get("auto_check_updates", False))
        beta_updates = bool(data.get("beta_updates", False))
        recent_files_limit = int(data.get("recent_files_limit", 10))
        tray_enabled = bool(data.get("tray_enabled", False))
        persistent_undo = bool(data.get("persistent_undo", False))
        spellcheck_as_you_type = bool(data.get("spellcheck_as_you_type", False))
        intellisense_as_you_type = bool(data.get("intellisense_as_you_type", False))
        snippet_trigger_expansion = bool(data.get("snippet_trigger_expansion", True))
        preview_browser = str(data.get("preview_browser", "system")).strip() or "system"
        auto_side_preview = bool(data.get("auto_side_preview", True))
        show_tab_control = bool(data.get("show_tab_control", False))
        title_bar_path_mode = str(data.get("title_bar_path_mode", "name"))
        if title_bar_path_mode not in {"name", "full_path"}:
            title_bar_path_mode = "name"
        dirty_title_style = str(data.get("dirty_title_style", "text"))
        if dirty_title_style not in {"text", "asterisk", "asterisk_text"}:
            dirty_title_style = "text"
        start_with_no_document_open = bool(data.get("start_with_no_document_open", False))
        read_aloud_engine = str(data.get("read_aloud_engine", "pyttsx3")).strip().lower()
        _valid_engines = {"pyttsx3", "dectalk", "piper", "kokoro", "vibevoice", "espeak"}
        if read_aloud_engine not in _valid_engines:
            read_aloud_engine = "pyttsx3"
        read_aloud_voice = str(data.get("read_aloud_voice", ""))
        read_aloud_rate = int(data.get("read_aloud_rate", 200))
        if read_aloud_rate < 80:
            read_aloud_rate = 80
        if read_aloud_rate > 450:
            read_aloud_rate = 450
        read_aloud_volume = int(data.get("read_aloud_volume", 100))
        if read_aloud_volume < 0:
            read_aloud_volume = 0
        if read_aloud_volume > 100:
            read_aloud_volume = 100
        read_aloud_pitch = int(data.get("read_aloud_pitch", 50))
        if read_aloud_pitch < 0:
            read_aloud_pitch = 0
        if read_aloud_pitch > 100:
            read_aloud_pitch = 100
        read_aloud_dectalk_executable = str(data.get("read_aloud_dectalk_executable", "")).strip()
        read_aloud_dectalk_voice = str(data.get("read_aloud_dectalk_voice", "paul")).strip().lower()
        if not read_aloud_dectalk_voice:
            read_aloud_dectalk_voice = "paul"
        read_aloud_dectalk_rate = int(data.get("read_aloud_dectalk_rate", 180))
        if read_aloud_dectalk_rate < 75:
            read_aloud_dectalk_rate = 75
        if read_aloud_dectalk_rate > 650:
            read_aloud_dectalk_rate = 650
        read_aloud_dectalk_dictionary = str(data.get("read_aloud_dectalk_dictionary", "")).strip()
        read_aloud_piper_executable = str(data.get("read_aloud_piper_executable", "")).strip()
        read_aloud_piper_model = str(data.get("read_aloud_piper_model", "")).strip()
        announcement_backend = str(data.get("announcement_backend", "auto")).strip().lower()
        read_aloud_piper_model_dir = str(data.get("read_aloud_piper_model_dir", "")).strip()
        read_aloud_kokoro_voice = str(data.get("read_aloud_kokoro_voice", "af_heart")).strip() or "af_heart"
        _kokoro_speed_raw = data.get("read_aloud_kokoro_speed", 1.0)
        try:
            read_aloud_kokoro_speed = float(_kokoro_speed_raw)
        except (TypeError, ValueError):
            read_aloud_kokoro_speed = 1.0
        read_aloud_kokoro_speed = max(0.5, min(2.0, read_aloud_kokoro_speed))
        read_aloud_vibevoice_executable = str(data.get("read_aloud_vibevoice_executable", "")).strip()
        read_aloud_vibevoice_voice = str(data.get("read_aloud_vibevoice_voice", "default")).strip() or "default"
        read_aloud_espeak_executable = str(data.get("read_aloud_espeak_executable", "")).strip()
        read_aloud_espeak_voice = str(data.get("read_aloud_espeak_voice", "en")).strip() or "en"
        read_aloud_espeak_rate = int(data.get("read_aloud_espeak_rate", 175))
        if read_aloud_espeak_rate < 80:
            read_aloud_espeak_rate = 80
        if read_aloud_espeak_rate > 450:
            read_aloud_espeak_rate = 450
        if announcement_backend not in {"auto", "prism", "status_only"}:
            announcement_backend = "auto"
        announcement_trace_enabled = bool(data.get("announcement_trace_enabled", False))
        assistant_enabled = bool(data.get("assistant_enabled", False))
        assistant_prompt_style = str(data.get("assistant_prompt_style", "balanced")).strip().lower()
        if assistant_prompt_style not in {"balanced", "concise", "gentle", "technical"}:
            assistant_prompt_style = "balanced"
        dictation_engine = str(data.get("dictation_engine", "vosk")).strip().lower()
        if dictation_engine not in {"vosk", "whisper"}:
            dictation_engine = "vosk"
        dictation_language = str(data.get("dictation_language", "en-US")).strip() or "en-US"
        dictation_model = str(data.get("dictation_model", "base")).strip() or "base"
        dictation_device_index = int(data.get("dictation_device_index", -1))
        if dictation_device_index < -1:
            dictation_device_index = -1
        voice_commands_enabled = bool(data.get("voice_commands_enabled", False))
        status_bar_order = _normalize_status_bar_order(data.get("status_bar_order"))
        status_bar_hidden = _normalize_status_bar_hidden(
            data.get("status_bar_hidden"), status_bar_order
        )
        if recent_files_limit < 1:
            recent_files_limit = 1
        if recent_files_limit > 50:
            recent_files_limit = 50
        if indent_size < 1:
            indent_size = 1
        if indent_size > 8:
            indent_size = 8
        return cls(
            theme=theme,
            keyboard_pack=keyboard_pack,
            soft_wrap=soft_wrap,
            wrap_find=wrap_find,
            csv_open_mode=csv_open_mode,
            word_open_mode=word_open_mode,
            indent_with_tabs=indent_with_tabs,
            indent_size=indent_size,
            auto_check_updates=auto_check_updates,
            beta_updates=beta_updates,
            recent_files_limit=recent_files_limit,
            tray_enabled=tray_enabled,
            persistent_undo=persistent_undo,
            spellcheck_as_you_type=spellcheck_as_you_type,
            intellisense_as_you_type=intellisense_as_you_type,
            snippet_trigger_expansion=snippet_trigger_expansion,
            preview_browser=preview_browser,
            auto_side_preview=auto_side_preview,
            show_tab_control=show_tab_control,
            title_bar_path_mode=title_bar_path_mode,
            dirty_title_style=dirty_title_style,
            start_with_no_document_open=start_with_no_document_open,
            read_aloud_engine=read_aloud_engine,
            read_aloud_voice=read_aloud_voice,
            read_aloud_rate=read_aloud_rate,
            read_aloud_volume=read_aloud_volume,
            read_aloud_pitch=read_aloud_pitch,
            read_aloud_dectalk_executable=read_aloud_dectalk_executable,
            read_aloud_dectalk_voice=read_aloud_dectalk_voice,
            read_aloud_dectalk_rate=read_aloud_dectalk_rate,
            read_aloud_dectalk_dictionary=read_aloud_dectalk_dictionary,
            read_aloud_piper_executable=read_aloud_piper_executable,
            read_aloud_piper_model=read_aloud_piper_model,
            announcement_backend=announcement_backend,
            read_aloud_piper_model_dir=read_aloud_piper_model_dir,
            read_aloud_kokoro_voice=read_aloud_kokoro_voice,
            read_aloud_kokoro_speed=read_aloud_kokoro_speed,
            read_aloud_vibevoice_executable=read_aloud_vibevoice_executable,
            read_aloud_vibevoice_voice=read_aloud_vibevoice_voice,
            read_aloud_espeak_executable=read_aloud_espeak_executable,
            read_aloud_espeak_voice=read_aloud_espeak_voice,
            read_aloud_espeak_rate=read_aloud_espeak_rate,
            announcement_trace_enabled=announcement_trace_enabled,
            assistant_enabled=assistant_enabled,
            assistant_prompt_style=assistant_prompt_style,
            dictation_engine=dictation_engine,
            dictation_language=dictation_language,
            dictation_model=dictation_model,
            dictation_device_index=dictation_device_index,
            voice_commands_enabled=voice_commands_enabled,
            status_bar_order=status_bar_order,
            status_bar_hidden=status_bar_hidden,
        )


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def load_settings() -> Settings:
    raw = read_json(settings_path(), default={})
    if not isinstance(raw, dict):
        return Settings()
    return Settings.from_dict(raw)


def save_settings(settings: Settings) -> None:
    write_json_atomic(settings_path(), asdict(settings))
