from __future__ import annotations

import html
import json
import os
import re
import threading
import time
import unicodedata
import webbrowser
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import URLError
from uuid import uuid4

if TYPE_CHECKING:  # imports kept out of cold-start path
    from quill.core.epub import EpubBook, EpubChapter

from quill import __version__
from quill.core import thesaurus as thesaurus_engine
from quill.core.a11y_regions import (
    RegionTracker,
    build_accessibility_audit_report,
    render_snapshot,
)
from quill.core.ai import Assistant
from quill.core.ai.agent import allowed_tools
from quill.core.assistant import render_assistant_prompt
from quill.core.autosave import autosave_document
from quill.core.backups import backup_document, list_backups
from quill.core.bookmarks import bookmark_names, bookmark_position, set_bookmark
from quill.core.browser_preview import (
    available_browser_options,
    browser_choice_label_for_value,
    browser_choice_value_for_label,
    guess_preview_kind,
    normalize_browser_choice,
    open_preview_url,
    preview_anchor_for_text,
    render_preview_body,
    render_preview_html,
)
from quill.core.commands import CommandRegistry
from quill.core.contrast import render_contrast_report, validate_theme_contrast
from quill.core.custom_profiles import (
    CustomProfile,
    build_bare_bones_profile_data,
    build_parent_profile_data,
    generate_custom_profile_id,
    load_custom_profiles,
    save_custom_profiles,
)
from quill.core.diagnostics import (
    build_bug_report_payload,
    build_diagnostics_review_text,
    build_support_issue_url,
    collect_environment_info,
    record_diagnostic_event,
    write_diagnostics_bundle,
)
from quill.core.dictation import (
    DictationController,
    DictationSettings,
    DictationUnavailableError,
)
from quill.core.diffing import build_unified_diff
from quill.core.document import Document
from quill.core.external_tools import (
    copyable_install_command,
    get_external_tool_status,
    get_external_tool_statuses,
)
from quill.core.features import (
    FEATURE_DEFINITIONS,
    PROFILE_DEFINITIONS,
    PROFILE_ESSENTIAL,
    FeatureManager,
)
from quill.core.file_search import (
    FileReplaceReport,
    FileSearchReport,
    render_replace_preview,
    render_replace_report,
    render_search_report,
    replace_files,
    search_files,
)
from quill.core.format_ops import (
    continue_markdown_list,
    convert_indentation_to_spaces,
    convert_indentation_to_tabs,
    indent_lines,
    normalize_whitespace,
    outdent_lines,
    remove_duplicate_lines,
    reverse_lines,
    sort_lines,
    toggle_block_comment,
    toggle_line_comment,
    trim_trailing_whitespace,
)
from quill.core.glow import build_audit_report, build_fix_report, fix_text
from quill.core.guides import build_keyboard_reference, build_welcome_guide
from quill.core.heading_organizer import (
    HeadingBlock,
    apply_heading_organizer_edits,
    parse_heading_blocks,
    validate_heading_sequence,
)
from quill.core.heading_styles import HeadingStyle, apply_heading_style
from quill.core.intake import (
    build_bad_extraction_package,
    build_context_help,
    build_extraction_quality_report,
    build_intake_report,
    build_intake_summary,
    build_source_reference,
)
from quill.core.intellisense import (
    IntellisenseContext,
    IntellisenseSuggestion,
    build_intellisense_suggestions,
    collect_document_words,
)
from quill.core.ipc import drain_open_requests
from quill.core.keymap import (
    DEFAULT_KEYMAP,
    KEYBOARD_PACK_CUSTOM,
    KEYBOARD_PACK_DEFAULT,
    build_keymap_for_pack,
    export_keymap,
    find_keymap_conflict,
    import_keymap,
    keyboard_pack_description,
    keyboard_pack_names,
    keyboard_pack_preview,
    load_keymap,
    reset_keymap,
    save_keymap,
)
from quill.core.line_ops import (
    delete_line,
    duplicate_line,
    join_with_next_line,
    move_line_down,
    move_line_up,
)
from quill.core.link_inventory import collect_link_inventory, render_link_inventory_report
from quill.core.links import build_link_text, find_link_at_cursor, infer_markup_kind
from quill.core.locations import LocationRing
from quill.core.macros import MacroManager
from quill.core.marks import MarkRing, line_column_for_position
from quill.core.metrics import compute_document_stats
from quill.core.navigation import (
    next_block_start,
    next_heading_start,
    page_start_for_number,
    page_starts,
    parse_line_column,
    previous_block_start,
    previous_heading_start,
)
from quill.core.notifications import add_notification, clear_notifications, load_notifications
from quill.core.onboarding import (
    load_assistant_onboarding_complete,
    load_onboarding_complete,
    load_speech_onboarding_complete,
    load_trust_consent_complete,
    load_watch_folder_onboarding_complete,
    mark_assistant_onboarding_complete,
    mark_onboarding_complete,
    mark_speech_onboarding_complete,
    mark_trust_consent_complete,
    mark_watch_folder_onboarding_complete,
)
from quill.core.outline import OutlineEntry, extract_outline_entries
from quill.core.paths import app_data_dir, ensure_app_directories
from quill.core.read_aloud import (
    ReadAloudController,
    ReadAloudUnavailableError,
    discover_dectalk_executable,
    discover_chatterbox_executable,
    discover_espeak_executable,
    discover_melotts_executable,
    discover_openvoice_executable,
    discover_piper_executable,
    discover_rhvoice_executable,
    discover_vibevoice_executable,
    download_dectalk_runtime,
    list_chatterbox_english_voices,
    list_dectalk_voices,
    list_espeak_english_voices,
    list_kokoro_voices,
    list_melotts_english_voices,
    list_openvoice_english_voices,
    list_piper_voices,
    list_rhvoice_english_voices,
    list_vibevoice_voices,
    list_voices,
    synthesize_with_chatterbox,
    synthesize_to_file_with_dectalk,
    synthesize_to_file_with_pyttsx3,
    synthesize_with_espeak,
    synthesize_with_kokoro,
    synthesize_with_melotts,
    synthesize_with_openvoice,
    synthesize_with_piper,
    synthesize_with_rhvoice,
    synthesize_with_vibevoice,
)
from quill.core.recent import add_recent_file, clear_recent_files, load_recent_files
from quill.core.recovery import (
    begin_session,
    mark_clean_exit,
    mark_recovery_offer_dismissed,
    mark_recovery_offer_recovered,
    read_recovery_snapshot,
)
from quill.core.search import SearchOptions, SearchPatternError, find_matches, replace_all
from quill.core.search_history import add_search_term, load_search_history
from quill.core.selection import block_span, line_span, paragraph_span
from quill.core.sessions import (
    active_index_from_session,
    add_recent_session,
    build_session_payload,
    clear_recent_sessions,
    documents_from_session,
    load_recent_sessions,
    load_session,
    session_title,
)
from quill.core.sessions import (
    save_session as save_session_file,
)
from quill.core.settings import STATUS_BAR_ITEMS, Settings, load_settings, save_settings
from quill.core.snippets import (
    ExpansionResult as SnippetExpansionResult,
)
from quill.core.snippets import (
    Snippet,
    SnippetLibrary,
    extract_placeholders,
    find_snippet_by_trigger,
    load_snippet_library,
    merge_starter_pack,
    render_snippet,
    save_snippet_library,
    search_snippets,
    starter_pack_names,
)
from quill.core.spellcheck import (
    Misspelling,
    add_word_to_scope,
    list_misspellings,
    load_combined_dictionary,
    load_scope_dictionary,
    misspelling_at_position,
    suggest_words,
)
from quill.core.spellcheck import (
    backend_info as spellcheck_backend_info,
)
from quill.core.spellcheck import (
    next_misspelling as find_next_misspelling,
)
from quill.core.spellcheck import (
    previous_misspelling as find_previous_misspelling,
)
from quill.core.sticky_notes import save_sticky_note
from quill.core.structure_nav import (
    find_matching_bracket,
    next_structure_position,
    previous_structure_position,
)
from quill.core.tagging import (
    HTML_TAG_CHOICES,
    MARKDOWN_TAG_CHOICES,
    InsertionResult,
    build_html_code_block,
    build_html_insertion,
    build_html_table,
    build_markdown_code_block,
    build_markdown_insertion,
    build_markdown_table,
    parse_attribute_pairs,
    search_html_tag_choices,
    search_markdown_tag_choices,
)
from quill.core.transforms import to_lower, to_sentence_case, to_title, to_toggle_case, to_upper
from quill.core.trust import is_trusted_location, load_trusted_locations, save_trusted_locations
from quill.core.undo_store import load_undo_history, save_undo_history
from quill.core.updates import (
    GitHubRelease,
    UpdateManifest,
    URLError,
    download_release_asset,
    fetch_update_manifest,
    fetch_latest_release,
    fetch_releases,
    find_release,
    is_newer_version,
    select_latest,
)
from quill.core.url_ops import format_content_length, host_for_url, is_cross_host_redirect
from quill.core.voice_commands import (
    build_voice_command_aliases,
    resolve_voice_command,
    split_text_delta,
)
from quill.core.watch_folder import WatchFolderConfig, WatchFolderResult, WatchFolderService
from quill.stability.memory_watch import should_trace_memory, start_memory_tracing
from quill.stability.ui_responsiveness import mark_wx_main_thread
from quill.stability.wx_heartbeat import HeartbeatState, WxHeartbeatTimer, WxHeartbeatWatchdog
from quill.core.yaml_structure import (
    YamlNode,
    YamlNodeKind,
    add_yaml_child,
    add_yaml_sibling,
    delete_yaml_node,
    extract_yaml_nodes,
    rename_yaml_node,
)
from quill.io.pandoc import (
    PandocConversionError,
    PandocUnavailableError,
    convert_document_with_pandoc,
)
from quill.io.text import read_text_document, write_text_document
from quill.platform.windows.high_contrast import is_high_contrast_enabled
from quill.platform.windows.prism_bridge import AnnouncementEngine
from quill.platform.windows.shell_integration import (
    build_shell_integration_plan,
    install_shell_integration,
    launcher_command,
    remove_shell_integration,
)
from quill.platform.windows.sr_announce import (
    announce,
    enable_transcript_capture,
    set_announce_handler,
    set_transcript_path,
)
from quill.platform.windows.sr_detect import detect_screen_reader
from quill.ui.ai_model_panel import AIModelDialog
from quill.ui.assistant_panel import AskQuillChatDialog
from quill.ui.assistant_tools import (
    AIHubDialog,
    AgentCenterDialog,
    AssistantConnectionDialog,
    PromptStudioDialog,
    RunPythonDialog,
    WritingAssistantDialog,
)
from quill.ui.csv_grid import CsvGridSurface
from quill.ui.palette import CommandPaletteDialog
from quill.ui.style_panel import TrainStyleDialog
from quill.ui.sticky_notes import StickyNoteEditorDialog, StickyNotesVaultDialog
from quill.ui.word_view import WordDocumentSurface


def _vibevoice_feature_enabled() -> bool:
    """VibeVoice (offline speech-file generator) is an experimental feature gated
    off by default. Set the QUILL_VIBEVOICE env var (1/true/yes/on) to surface its
    AI > Speech menu items. The feature is developed on the feature/vibevoice branch."""
    return os.environ.get("QUILL_VIBEVOICE", "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(slots=True)
class _DocumentTab:
    panel: object
    editor: object
    document: Document
    splitter: object = None
    preview: object = None


@dataclass(slots=True)
class _NavigatorNode:
    label: str
    preview: str
    payload: object
    action_label: str
    children: list[_NavigatorNode]


@dataclass(frozen=True, slots=True)
class _EpubNavigatorTarget:
    chapter_index: int
    heading_index: int | None = None


@dataclass(slots=True)
class _BrowserPreviewSession:
    tab_index: int
    preview_path: Path
    browser_choice: str
    title: str


@dataclass(slots=True)
class _ListManagerItem:
    kind: str
    text: str
    level: int
    bullet: str = "-"
    checked: bool = False


@dataclass(slots=True)
class _ListManagerState:
    start: int
    end: int
    trailing_newline: bool
    base_indent: str
    items: list[_ListManagerItem]


@dataclass(slots=True)
class _StatusBarCell:
    item: str
    button: object


@dataclass(slots=True)
class _CompareLineBlock:
    document_name: str
    start_line: int | None
    end_line: int | None
    text: list[str]


@dataclass(slots=True)
class _CompareDifferenceGroup:
    index: int
    kind: str
    blocks: list[_CompareLineBlock]


@dataclass(slots=True)
class _CompareSession:
    source_documents: list[tuple[str, str]]
    groups: list[_CompareDifferenceGroup]
    current_index: int = 0
    synchronized_navigation: bool = True


@dataclass(slots=True)
class _FileSearchRequest:
    root: Path
    pattern: str
    query: str
    replacement: str | None
    options: SearchOptions
    output_mode: str
    preview_before_replace: bool


class _IntellisensePopup:
    def __init__(self, wx: object, parent: object) -> None:
        self._wx = wx
        self._accept_callback = None
        self.frame = wx.Frame(
            parent,
            title="Word Prediction",
            style=wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_SIMPLE,
        )
        self.frame.SetSize((420, 220))
        root = wx.BoxSizer(wx.VERTICAL)
        self.status = wx.StaticText(self.frame, label="")
        root.Add(self.status, 0, wx.EXPAND | wx.ALL, 6)
        self.listbox = wx.ListBox(self.frame)
        root.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        self.frame.SetSizer(root)
        self.suggestions: list[IntellisenseSuggestion] = []
        self.frame.Bind(wx.EVT_CLOSE, self._on_close)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self._on_accept)

    def set_accept_callback(self, callback: object) -> None:
        self._accept_callback = callback

    def _on_close(self, event: object) -> None:
        self.frame.Hide()
        skip = getattr(event, "Skip", None)
        if callable(skip):
            skip()

    def _on_accept(self, _event: object) -> None:
        if callable(self._accept_callback):
            self._accept_callback()

    def update(self, suggestions: list[IntellisenseSuggestion], status: str) -> None:
        self.suggestions = list(suggestions)
        labels = [item.label for item in suggestions]
        self.listbox.Set(labels)
        if labels:
            self.listbox.SetSelection(0)
        self.status.SetLabel(status)

    def show(self, position: tuple[int, int]) -> None:
        self.frame.SetPosition(position)
        show_without_activating = getattr(self.frame, "ShowWithoutActivating", None)
        if callable(show_without_activating):
            show_without_activating()
        else:
            self.frame.Show(True)
        self.frame.Raise()

    def hide(self) -> None:
        self.frame.Hide()

    def is_visible(self) -> bool:
        return bool(self.frame.IsShown())

    def selection_index(self) -> int:
        return self.listbox.GetSelection()

    def set_selection(self, index: int) -> None:
        if not self.suggestions:
            return
        index = max(0, min(index, len(self.suggestions) - 1))
        self.listbox.SetSelection(index)

    def selected_suggestion(self) -> IntellisenseSuggestion | None:
        index = self.listbox.GetSelection()
        if index < 0 or index >= len(self.suggestions):
            return None
        return self.suggestions[index]


class MainFrame:
    _ANNOUNCEMENT_BACKEND_LABELS: dict[str, str] = {
        "auto": "Automatic (use Prism when available)",
        "prism": "Prism",
        "status_only": "Status Bar Only",
    }
    _STATUS_BAR_LABELS: dict[str, str] = {
        "message": "Status Message",
        "line_column": "Line / Column",
        "word_count": "Word Count",
        "mode": "Insert / Overwrite",
        "selection": "Selection Length",
        "encoding": "Encoding",
        "line_endings": "Line Endings",
        "spell_check": "Spell Check",
        "background_tasks": "Background Tasks",
        "notifications": "Notifications",
        "read_aloud": "Read Aloud",
        "autosave": "Autosave",
        "search_term": "Search Term",
        "file_path": "File Path",
    }
    _STATUS_BAR_WIDTHS: dict[str, int] = {
        "message": -1,
        "line_column": 140,
        "word_count": 140,
        "mode": 110,
        "selection": 110,
        "encoding": 120,
        "line_endings": 140,
        "spell_check": 120,
        "background_tasks": 150,
        "notifications": 140,
        "read_aloud": 140,
        "autosave": 130,
        "search_term": 160,
        "file_path": 260,
    }
    _STATUS_BAR_FEATURES: dict[str, str] = {
        "message": "core.app",
        "line_column": "core.editor",
        "word_count": "core.analysis",
        "mode": "core.editor",
        "selection": "core.editor",
        "encoding": "core.file",
        "line_endings": "core.file",
        "spell_check": "core.spellcheck",
        "background_tasks": "core.notifications",
        "notifications": "core.notifications",
        "read_aloud": "core.read_aloud",
        "autosave": "core.recovery",
        "search_term": "core.search",
        "file_path": "core.file",
    }
    _MACRO_CONTROL_COMMANDS: frozenset[str] = frozenset(
        {
            "tools.start_macro_recording",
            "tools.stop_macro_recording",
            "tools.play_last_macro",
            "tools.manage_macros",
        }
    )

    def __init__(self, safe_mode: bool = False) -> None:
        import wx
        import wx.adv

        self._wx = wx
        self._safe_mode = safe_mode
        self.document = Document()
        ensure_app_directories()
        self._first_run_profile_prompt = not safe_mode and not load_onboarding_complete()
        self._first_run_trust_consent_prompt = not safe_mode and not load_trust_consent_complete()
        self.features = FeatureManager.load(persistent=not safe_mode)
        self.macros = MacroManager.load(persistent=not safe_mode)
        self.settings = load_settings()
        self._first_run_assistant_prompt = (
            not safe_mode
            and not load_assistant_onboarding_complete()
            and not getattr(self.settings, "assistant_enabled", False)
        )
        self._first_run_speech_prompt = not safe_mode and not load_speech_onboarding_complete()
        self._first_run_watch_folder_prompt = (
            not safe_mode and not load_watch_folder_onboarding_complete()
        )
        if safe_mode:
            self.settings.theme = "system"
            self.settings.tray_enabled = False
            self.settings.persistent_undo = False
            self.settings.spellcheck_as_you_type = False
            self.settings.start_with_no_document_open = False
            self.settings.announcement_backend = "status_only"
            self.settings.announcement_trace_enabled = False
            self.settings.assistant_enabled = False
        self.keymap = dict(DEFAULT_KEYMAP) if safe_mode else load_keymap()
        self.recent_files = [] if safe_mode else load_recent_files()
        self._trusted_locations = set() if safe_mode else load_trusted_locations()
        self.session_id = str(uuid4())
        self._recovery_offers = [] if safe_mode else begin_session(self.session_id)
        self._last_autosave_at: datetime | None = None
        self._autosave_interval = timedelta(seconds=30)
        self._last_find_query = ""
        self._last_search_options = SearchOptions()
        self._last_match: tuple[int, int] | None = None
        self._search_history = [] if safe_mode else load_search_history()
        self._searchable_picker_queries: dict[str, str] = {}
        self._notifications = [] if safe_mode else load_notifications()
        self._mark_ring = MarkRing()
        self._location_ring = LocationRing()
        self._region_tracker = RegionTracker()
        self._focus_regions = ("Editor", "Status Bar")
        self._active_region_index = 0
        self._persistent_undo_history: list[str] = [self.document.text]
        self._persistent_undo_index = 0
        self._suspend_persistent_undo = False
        self._persistent_undo_dirty = False
        self._last_persistent_undo_write_at: datetime | None = None
        self._spell_dictionary_cache: tuple[tuple[Path | None, Path], set[str]] | None = None
        self._last_live_misspelling_feedback: tuple[str, int, int] | None = None
        self._last_live_misspelling_feedback_at: float = 0.0
        self._extend_selection_mode = False
        self._extend_selection_anchor: int | None = None
        self._epub_book: EpubBook | None = None
        self._browser_preview_session: _BrowserPreviewSession | None = None
        self._bookmarks: dict[str, int] = {}
        self._tray_icon: object | None = None
        self._is_exiting = False
        self._ipc_timer: object | None = None
        self._status_message = "Ready"
        self._background_task_count = 0
        self._background_tasks: list[dict[str, object]] = []
        self._background_task_sequence = 0
        self._last_intake_report = ""
        self._startup_deferred_ran = False
        self._compare_session: _CompareSession | None = None
        self._compare_ignore_trailing_spaces = True
        self._compare_ignore_line_endings = True
        self._empty_workspace_active = False
        self._announcement_engine = AnnouncementEngine(self.settings.announcement_backend)
        self._announcement_error_reported = ""
        self._read_aloud = ReadAloudController()
        self._dictation = DictationController()
        self._watch_folder = WatchFolderService(
            on_result=lambda result: self._wx.CallAfter(self._on_watch_folder_result, result),
            on_error=lambda path, message: self._wx.CallAfter(
                self._on_watch_folder_error,
                path,
                message,
            ),
            on_state_change=lambda running: self._wx.CallAfter(
                self._on_watch_folder_state_change,
                running,
            ),
        )
        self._voice_command_scan_timer: threading.Timer | None = None
        self._voice_command_baseline_text = ""
        self._voice_command_aliases: dict[str, str] = {}
        self._voice_command_guard = False
        self._overwrite_mode = False
        self._insert_key_down = False
        self._print_data = wx.PrintData()
        self._page_setup_data = wx.PageSetupDialogData(self._print_data)
        self._snippet_library = (
            load_snippet_library() if not safe_mode else SnippetLibrary(version=1, snippets=[])
        )
        self._snippet_expansion_guard = False
        self._intellisense_popup: _IntellisensePopup | None = None
        self._intellisense_context: IntellisenseContext | None = None
        self._intellisense_fragment_text = ""
        self._intellisense_suggestions: list[IntellisenseSuggestion] = []
        self._intellisense_guard = False
        self._sticky_note_hotkey_id = wx.NewIdRef()
        self.commands = CommandRegistry()
        self.commands.set_run_listener(self._on_command_run)
        self._recent_menu_ids: dict[int, Path] = {}
        self._recent_session_menu_ids: dict[int, Path] = {}
        self._session_menu_ids: dict[int, int] = {}
        self._recent_sessions = [] if safe_mode else load_recent_sessions()

        self.frame = wx.Frame(None, title="Untitled - Quill", size=(1000, 700))
        self._intellisense_popup = _IntellisensePopup(wx, self.frame)
        self._intellisense_popup.set_accept_callback(self._apply_intellisense_selection)
        self._tab_control_visible = bool(self.settings.show_tab_control)
        self._documents_panel = wx.Panel(self.frame)
        self._documents_sizer = wx.BoxSizer(wx.VERTICAL)
        self._documents_panel.SetSizer(self._documents_sizer)
        self.notebook = self._create_tab_host(self._tab_control_visible)
        self._document_tabs: list[_DocumentTab] = []
        self._active_tab_index = -1
        self._statusbar_cells: list[_StatusBarCell] = []
        self._active_statusbar_cell_index = 0
        layout = wx.BoxSizer(wx.VERTICAL)
        self._documents_sizer.Add(self.notebook, 1, wx.EXPAND)
        layout.Add(self._documents_panel, 1, wx.EXPAND)
        self.statusbar = wx.Panel(self.frame)
        self._statusbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.statusbar.SetSizer(self._statusbar_sizer)
        layout.Add(self.statusbar, 0, wx.EXPAND)
        self.frame.SetSizer(layout)
        self._create_document_tab(self.document, select=True)
        self._location_ring.record(0)
        self._region_tracker.enter("Editor")
        self._apply_theme(self.settings.theme)

        self._build_commands()
        self._refresh_voice_command_aliases()
        self._build_menu()
        self._apply_watch_folder_menu_state()
        self._refresh_sessions_menu()
        self._apply_accelerators()
        self._reload_global_hotkeys()
        self._bind_events()
        self._apply_startup_document_preference()
        self._apply_announcement_trace_setting()

        set_announce_handler(self._announce)
        if safe_mode:
            self._set_status("Safe mode enabled. Optional state is disabled.")
        else:
            self._set_status("Ready. Tip: press Ctrl+Shift+P for Command Palette.")
        self._announce_backend_state_on_startup()
        self._refresh_title()

    def show(self) -> None:
        self.frame.Show(True)
        # Bring the window to the front and focus the editor, so it doesn't open
        # behind the launching console (screen-reader users land in the editor).
        self.frame.Raise()
        self.frame.RequestUserAttention()
        if getattr(self, "editor", None) is not None:
            self._wx.CallAfter(self.editor.SetFocus)
        if not self._startup_deferred_ran:
            self._startup_deferred_ran = True
            self._wx.CallAfter(self._run_deferred_startup_tasks)
        focus_target = (
            self.notebook if self._empty_workspace_active else getattr(self, "editor", None)
        )
        if focus_target is not None and hasattr(focus_target, "SetFocus"):
            self._wx.CallAfter(focus_target.SetFocus)

    def _run_deferred_startup_tasks(self) -> None:
        self._start_ipc_poll()
        detection = detect_screen_reader()
        if detection.detected:
            self._set_status(f"Detected screen reader: {detection.name}. Adaptive hints enabled.")
        elif not self._safe_mode:
            self._set_status("Ready. Tip: press Ctrl+Shift+P for Command Palette.")
        if getattr(self, "_first_run_trust_consent_prompt", False):
            accepted = self._show_trust_consent_onboarding(force=False)
            self._first_run_trust_consent_prompt = False
            if not accepted:
                self._set_status("Startup consent declined. Quill is closing.")
                self.frame.Close()
                return
        self._offer_crash_recovery()
        self._maybe_run_first_run_onboarding()
        self._maybe_start_watch_folder()
        if getattr(self.settings, "auto_check_updates", False) and not self._safe_mode:
            self.check_for_updates(silent_no_update=True)

    def _apply_startup_document_preference(self) -> None:
        if not self.settings.start_with_no_document_open:
            return
        if len(self._document_tabs) != 1:
            return
        if self.document.path is not None or self.document.modified or self.editor.GetValue():
            return
        self._empty_workspace_active = True
        self.editor.SetEditable(False)
        self._set_tab_page_text(0, "Start")
        self._set_status("No document open. Use File > New or File > Open.")

    def _clear_empty_workspace_state(self) -> None:
        if not self._empty_workspace_active:
            return
        self._empty_workspace_active = False
        self.editor.SetEditable(True)
        self._set_tab_page_text(self._current_tab_index(), self.document.name)

    def _build_commands(self) -> None:
        self.commands.register(
            "file.new",
            "New File",
            self.new_file,
            self._binding_for("file.new"),
        )
        self.commands.register(
            "file.open",
            "Open File...",
            self.open_file,
            self._binding_for("file.open"),
        )
        self.commands.register(
            "file.save",
            "Save",
            self.save_file,
            self._binding_for("file.save"),
        )
        self.commands.register(
            "file.save_as",
            "Save As...",
            self.save_file_as,
            self._binding_for("file.save_as"),
        )
        self.commands.register(
            "file.close_document",
            "Close Document",
            self.close_current_document,
            self._binding_for("file.close_document"),
        )
        self.commands.register(
            "file.save_all",
            "Save All",
            self.save_all_files,
            None,
        )
        self.commands.register(
            "file.reload_from_disk",
            "Reload from Disk",
            self.reload_from_disk,
            None,
        )
        self.commands.register(
            "file.restore_backup",
            "Restore Backup...",
            self.restore_backup,
            None,
        )
        self.commands.register(
            "file.page_setup",
            "Page Setup...",
            self.page_setup,
            None,
        )
        self.commands.register(
            "file.print",
            "Print...",
            self.print_document,
            self._binding_for("file.print"),
        )
        self.commands.register(
            "file.save_as_plain_text",
            "Save As Plain Text...",
            self.save_as_plain_text,
            None,
        )
        self.commands.register(
            "file.choose_encoding",
            "Choose Encoding...",
            self.choose_document_encoding,
            None,
        )
        self.commands.register(
            "file.toggle_line_endings",
            "Toggle Line Endings",
            self.toggle_line_endings,
            None,
        )
        self.commands.register(
            "file.open_containing_folder",
            "Open Containing Folder",
            self.open_containing_folder,
            None,
        )
        self.commands.register(
            "file.open_url",
            "Open from URL...",
            self.open_url,
            None,
        )
        self.commands.register(
            "file.save_session",
            "Save Session...",
            self.save_session,
            None,
        )
        self.commands.register(
            "file.open_session",
            "Open Session...",
            self.open_session,
            None,
        )
        self.commands.register(
            "app.command_palette",
            "Command Palette...",
            self.open_palette,
            self._binding_for("app.command_palette"),
        )
        self.commands.register(
            "app.preferences",
            "Preferences...",
            self.open_preferences,
            self._binding_for("app.preferences"),
        )
        self.commands.register(
            "app.exit",
            "Exit",
            self.exit_app,
            self._binding_for("app.exit"),
        )
        self.commands.register(
            "window.next_document",
            "Next Document",
            self.next_document,
            self._binding_for("window.next_document"),
        )
        self.commands.register(
            "window.previous_document",
            "Previous Document",
            self.previous_document,
            self._binding_for("window.previous_document"),
        )
        self.commands.register(
            "view.send_to_tray",
            "Send to Tray",
            self.send_to_tray,
            self._binding_for("view.send_to_tray"),
        )
        self.commands.register(
            "view.toggle_soft_wrap",
            "Toggle Soft Wrap",
            self.toggle_soft_wrap,
            self._binding_for("view.toggle_soft_wrap"),
        )
        self.commands.register(
            "view.toggle_tab_control",
            "Toggle Tab Control",
            self.toggle_tab_control,
            self._binding_for("view.toggle_tab_control"),
        )
        self.commands.register(
            "view.toggle_find_wrap",
            "Toggle Find Wrap",
            self.toggle_find_wrap,
            None,
        )
        self.commands.register(
            "view.toggle_dark_mode",
            "Toggle Dark Mode",
            self.toggle_dark_mode,
            None,
        )
        self.commands.register(
            "view.toggle_persistent_undo",
            "Toggle Persistent Undo",
            self.toggle_persistent_undo,
            None,
        )
        self.commands.register(
            "view.toggle_spellcheck_as_you_type",
            "Toggle Spell Check As You Type",
            self.toggle_spellcheck_as_you_type,
            None,
        )
        self.commands.register(
            "view.toggle_intellisense_as_you_type",
            "Toggle Word Prediction As You Type",
            self.toggle_intellisense_as_you_type,
            None,
        )
        self.commands.register(
            "view.preview",
            "Preview",
            self.preview_in_app,
            self._binding_for("view.preview"),
        )
        self.commands.register(
            "view.split_preview",
            "Preview Side by Side",
            self.toggle_side_preview,
            self._binding_for("view.split_preview"),
        )
        self.commands.register(
            "view.focus_preview",
            "Focus Preview",
            self.focus_preview,
            self._binding_for("view.focus_preview"),
        )
        self.commands.register(
            "view.browser_preview",
            "Browser Preview",
            self.preview_in_browser,
            self._binding_for("view.browser_preview"),
        )
        self.commands.register(
            "tools.ai_hub",
            "AI Hub",
            self.open_ai_hub,
            None,
        )
        self.commands.register(
            "tools.ai_assistant",
            "Writing Assistant",
            self.open_writing_assistant,
            None,
        )
        self.commands.register(
            "tools.ai_prompt_studio",
            "Prompt Studio",
            self.open_prompt_studio,
            None,
        )
        self.commands.register(
            "tools.ai_agent_center",
            "Agent Center",
            self.open_agent_center,
            None,
        )
        self.commands.register(
            "tools.ask_quill_chat",
            "Ask Quill Chat",
            self.open_ask_quill_chat,
            None,
        )
        self.commands.register(
            "tools.ai_model",
            "AI Model",
            self.open_ai_model_settings,
            None,
        )
        self.commands.register(
            "tools.ai_connection",
            "AI Connection",
            self.open_ai_preferences,
            None,
        )
        self.commands.register(
            "tools.ai_rewrite_selection",
            "Rewrite Selection",
            self.open_ai_rewrite_selection,
            None,
        )
        self.commands.register(
            "tools.ai_summarize_selection",
            "Summarize Selection",
            self.open_ai_summarize_selection,
            None,
        )
        self.commands.register(
            "tools.ai_continue_writing",
            "Continue Writing",
            self.open_ai_continue_writing,
            None,
        )
        self.commands.register(
            "tools.ai_fix_grammar",
            "Fix Grammar",
            self.open_ai_fix_grammar,
            None,
        )
        self.commands.register(
            "tools.train_writing_style",
            "Train Writing Style",
            self.open_train_writing_style,
            None,
        )
        self.commands.register(
            "view.toggle_overwrite_mode",
            "Toggle Overwrite Mode",
            self.toggle_overwrite_mode,
            None,
        )
        self.commands.register(
            "navigate.go_to_line",
            "Go To Line...",
            self.go_to_line,
            self._binding_for("navigate.go_to_line"),
        )
        self.commands.register(
            "navigate.go_to_page",
            "Go To Page...",
            self.go_to_page,
            self._binding_for("navigate.go_to_page"),
        )
        self.commands.register(
            "navigate.back_location",
            "Back Location",
            self.navigate_back_location,
            self._binding_for("navigate.back_location"),
        )
        self.commands.register(
            "navigate.forward_location",
            "Forward Location",
            self.navigate_forward_location,
            self._binding_for("navigate.forward_location"),
        )
        self.commands.register(
            "navigate.next_heading",
            "Next Heading",
            self.navigate_next_heading,
            None,
        )
        self.commands.register(
            "navigate.previous_heading",
            "Previous Heading",
            self.navigate_previous_heading,
            None,
        )
        self.commands.register(
            "navigate.next_block",
            "Next Block",
            self.navigate_next_block,
            None,
        )
        self.commands.register(
            "navigate.previous_block",
            "Previous Block",
            self.navigate_previous_block,
            None,
        )
        self.commands.register(
            "navigate.outline_navigator",
            "Outline Navigator...",
            self.open_outline_navigator,
            self._binding_for("navigate.outline_navigator"),
        )
        self.commands.register(
            "navigate.heading_organizer",
            "Heading Organizer...",
            self.open_heading_organizer,
            self._binding_for("navigate.heading_organizer"),
        )
        self.commands.register(
            "navigate.match_bracket",
            "Match Bracket",
            self.match_bracket,
            self._binding_for("navigate.match_bracket"),
        )
        self.commands.register(
            "navigate.next_structure",
            "Next Structure",
            self.navigate_next_structure,
            self._binding_for("navigate.next_structure"),
        )
        self.commands.register(
            "navigate.previous_structure",
            "Previous Structure",
            self.navigate_previous_structure,
            self._binding_for("navigate.previous_structure"),
        )
        self.commands.register(
            "navigate.next_region",
            "Next Region",
            self.navigate_next_region,
            self._binding_for("navigate.next_region"),
        )
        self.commands.register(
            "navigate.previous_region",
            "Previous Region",
            self.navigate_previous_region,
            self._binding_for("navigate.previous_region"),
        )
        self.commands.register(
            "navigate.set_bookmark",
            "Set Bookmark...",
            self.set_bookmark,
            None,
        )
        self.commands.register(
            "navigate.go_to_bookmark",
            "Go To Bookmark...",
            self.go_to_bookmark,
            None,
        )
        self.commands.register(
            "navigate.list_bookmarks",
            "List Bookmarks...",
            self.list_bookmarks,
            self._binding_for("navigate.list_bookmarks"),
        )
        self.commands.register(
            "tools.word_count",
            "Word Count...",
            self.show_word_count,
            self._binding_for("tools.word_count"),
        )
        self.commands.register(
            "tools.sticky_notes",
            "Sticky Notes...",
            self.manage_sticky_notes,
            None,
        )
        self.commands.register(
            "tools.sticky_note_capture",
            "New Sticky Note...",
            self.create_sticky_note,
            self._binding_for("tools.sticky_note_capture"),
        )
        self.commands.register(
            "tools.spell_check_dialog",
            "Spell Check...",
            self.open_spell_check_dialog,
            self._binding_for("tools.spell_check_dialog"),
        )
        self.commands.register(
            "tools.next_misspelling",
            "Next Misspelling",
            self.next_misspelling,
            self._binding_for("tools.next_misspelling"),
        )
        self.commands.register(
            "tools.previous_misspelling",
            "Previous Misspelling",
            self.previous_misspelling,
            self._binding_for("tools.previous_misspelling"),
        )
        self.commands.register(
            "tools.misspelling_list",
            "Misspelling List...",
            self.open_misspelling_list,
            self._binding_for("tools.misspelling_list"),
        )
        self.commands.register(
            "tools.thesaurus",
            "Thesaurus...",
            self.show_thesaurus,
            self._binding_for("tools.thesaurus"),
        )
        self.commands.register(
            "tools.dictionary_status",
            "Dictionary Status...",
            self.show_dictionary_status,
            None,
        )
        self.commands.register(
            "tools.ocr_image",
            "OCR Image...",
            self.ocr_image_file,
            None,
        )
        self.commands.register(
            "tools.read_aloud_start_pause",
            "Read Aloud Start/Pause",
            self.toggle_read_aloud,
            self._binding_for("tools.read_aloud_start_pause"),
        )
        self.commands.register(
            "tools.read_aloud_stop",
            "Read Aloud Stop",
            self.stop_read_aloud,
            self._binding_for("tools.read_aloud_stop"),
        )
        self.commands.register(
            "tools.read_aloud_voice",
            "Read Aloud Voice...",
            self.choose_read_aloud_voice,
            None,
        )
        self.commands.register(
            "tools.read_aloud_settings",
            "Read Aloud Settings...",
            self.choose_read_aloud_settings,
            None,
        )
        self.commands.register(
            "tools.read_aloud_generate_audio",
            "Generate Speech Audio...",
            self.generate_speech_audio,
            None,
        )
        # VibeVoice is experimental and hidden behind a feature gate (set the
        # QUILL_VIBEVOICE env var to enable). Lives on the feature/vibevoice
        # branch; off by default so it doesn't show up.
        if _vibevoice_feature_enabled():
            self.commands.register(
                "tools.download_vibevoice",
                "Download VibeVoice Speech Model...",
                self.download_vibevoice_model,
                None,
            )
            self.commands.register(
                "tools.generate_vibevoice_audio",
                "Generate Speech with VibeVoice...",
                self.generate_speech_with_vibevoice,
                None,
            )
        self.commands.register(
            "tools.announcement_backend",
            "Announcement Backend...",
            self.choose_announcement_backend,
            None,
        )
        self.commands.register(
            "tools.announcement_trace_toggle",
            "Toggle Announcement Trace Capture",
            self.toggle_announcement_trace_capture,
            None,
        )
        self.commands.register(
            "tools.dictation_toggle",
            "Dictation",
            self.toggle_dictation,
            self._binding_for("tools.dictation_toggle"),
            feature_id="core.dictation",
        )
        self.commands.register(
            "tools.dictation_voice_commands_toggle",
            "Hey QUILL Commands",
            self.toggle_dictation_voice_commands,
            None,
            feature_id="core.voice_commands",
        )
        self.commands.register(
            "tools.watch_folder_toggle",
            "Watch Folder Monitoring",
            self.toggle_watch_folder_monitoring,
            None,
            feature_id="core.watch_folder",
        )
        self.commands.register(
            "tools.watch_folder_settings",
            "Watch Folder Settings...",
            self.open_watch_folder_settings,
            None,
            feature_id="core.watch_folder",
        )
        self.commands.register(
            "tools.watch_folder_status",
            "Watch Folder Status...",
            self.show_watch_folder_status,
            None,
            feature_id="core.watch_folder",
        )
        self.commands.register(
            "tools.document_intake_report",
            "Document Intake Report...",
            self.show_document_intake_report,
            self._binding_for("tools.document_intake_report"),
        )
        self.commands.register(
            "tools.review_extraction_quality",
            "Review Extraction Quality...",
            self.review_extraction_quality,
            None,
        )
        self.commands.register(
            "tools.regex_helper",
            "Regex Helper...",
            self.show_regex_helper,
            None,
        )
        self.commands.register(
            "tools.pandoc_wizard",
            "Pandoc Conversion Wizard...",
            self.open_pandoc_wizard,
            None,
        )
        self.commands.register(
            "tools.external_tools",
            "External Tools and Format Support...",
            self.show_external_tools_dialog,
            None,
        )
        self.commands.register(
            "tools.report_bad_extraction",
            "Report Bad Extraction...",
            self.report_bad_extraction,
            None,
        )
        self.commands.register(
            "tools.shell_install",
            "Install Shell Integration...",
            self.install_shell_integration,
            None,
        )
        self.commands.register(
            "tools.shell_remove",
            "Remove Shell Integration",
            self.remove_shell_integration,
            None,
        )
        self.commands.register(
            "tools.notifications",
            "Open Notifications...",
            self.open_notifications,
            None,
        )
        self.commands.register(
            "tools.check_updates",
            "Check for Updates...",
            self.check_for_updates,
            None,
        )
        self.commands.register(
            "tools.validate_contrast",
            "Validate Contrast...",
            self.validate_contrast,
            None,
        )
        self.commands.register(
            "tools.link_inventory",
            "Link Inventory and Alt-Text Catalog...",
            self.show_link_inventory,
            None,
        )
        self.commands.register(
            "tools.compare_with_file",
            "Compare with File...",
            self.compare_with_file,
            None,
        )
        self.commands.register(
            "tools.compare_open_documents",
            "Compare Open Documents...",
            self.compare_open_documents,
            None,
        )
        self.commands.register(
            "tools.compare_next_difference",
            "Next Difference",
            self.compare_next_difference,
            None,
        )
        self.commands.register(
            "tools.compare_previous_difference",
            "Previous Difference",
            self.compare_previous_difference,
            None,
        )
        self.commands.register(
            "tools.compare_announce_difference",
            "Announce Current Difference",
            self.compare_announce_difference,
            None,
        )
        self.commands.register(
            "tools.compare_difference_list",
            "Open Difference List...",
            self.open_compare_difference_list,
            None,
        )
        self.commands.register(
            "tools.compare_toggle_sync",
            "Toggle Compare Synchronization",
            self.toggle_compare_synchronization,
            None,
        )
        self.commands.register(
            "tools.compare_options",
            "Compare Options...",
            self.open_compare_options,
            None,
        )
        self.commands.register(
            "tools.compare_create_summary",
            "Create Difference Summary",
            self.create_compare_summary_document,
            None,
        )
        self.commands.register(
            "tools.compare_copy_current_difference",
            "Copy Current Difference",
            self.copy_current_difference,
            None,
        )
        self.commands.register(
            "tools.compare_copy_all_differences",
            "Copy All Differences",
            self.copy_all_differences,
            None,
        )
        self.commands.register(
            "tools.export_keymap",
            "Export Keymap...",
            self.export_keymap_file,
            None,
        )
        self.commands.register(
            "tools.keymap_editor",
            "Keymap Editor...",
            self.open_keymap_editor,
            None,
        )
        self.commands.register(
            "tools.status_bar_settings",
            "Status Bar Layout...",
            self.open_status_bar_settings,
            None,
        )
        self.commands.register(
            "tools.import_keymap",
            "Import Keymap...",
            self.import_keymap_file,
            None,
        )
        self.commands.register(
            "tools.reset_keymap",
            "Reset Keymap",
            self.reset_keymap_defaults,
            None,
        )
        self.commands.register(
            "tools.open_welcome_guide",
            "Open Welcome Guide",
            self.open_welcome_guide,
            None,
        )
        self.commands.register(
            "tools.open_keyboard_reference",
            "Open Keyboard Reference",
            self.open_keyboard_reference,
            None,
        )
        self.commands.register(
            "help.open_user_guide",
            "Open User Guide",
            self.open_user_guide,
            None,
        )
        self.commands.register(
            "help.why_dont_i_see_feature",
            "Why Don't I See a Feature?",
            self.show_feature_explanation,
            None,
        )
        self.commands.register(
            "help.switch_feature_profile",
            "Switch Feature Profile...",
            self.switch_feature_profile,
            None,
        )
        self.commands.register(
            "help.feature_profile_health_check",
            "Feature Profile Health Check...",
            self.show_feature_profile_health_check,
            None,
        )
        self.commands.register(
            "tools.profiles_and_features_settings",
            "Profiles and Features...",
            self.open_profiles_and_features_settings,
            None,
        )
        self.commands.register(
            "help.undo_last_profile_change",
            "Undo Last Profile Change",
            self.undo_last_profile_change,
            None,
        )
        self.commands.register(
            "help.reset_feature_profile",
            "Reset to Essential Profile",
            self.reset_feature_profile_to_essential,
            None,
        )
        self.commands.register(
            "help.startup_wizard",
            "Startup Wizard...",
            self.run_startup_wizard,
            None,
        )
        self.commands.register(
            "help.run_profile_onboarding",
            "Startup Wizard...",
            self.run_startup_wizard,
            None,
        )
        self.commands.register(
            "tools.start_macro_recording",
            "Start Macro Recording",
            self.start_macro_recording,
            None,
        )
        self.commands.register(
            "tools.stop_macro_recording",
            "Stop Macro Recording",
            self.stop_macro_recording,
            None,
        )
        self.commands.register(
            "tools.play_last_macro",
            "Play Last Macro",
            self.play_last_macro,
            None,
        )
        self.commands.register(
            "tools.manage_macros",
            "Manage Macros...",
            self.manage_macros,
            None,
        )
        self.commands.register(
            "tools.cycle_autosave_interval",
            "Cycle Autosave Interval",
            self.cycle_autosave_interval,
            None,
        )
        self.commands.register(
            "help.about_quill",
            "About Quill",
            self.show_about_quill,
            None,
        )
        self.commands.register(
            "help.save_diagnostics",
            "Save Diagnostics...",
            self.save_diagnostics_bundle,
            None,
        )
        self.commands.register(
            "help.report_bug",
            "Report a Bug...",
            self.report_bug,
            None,
        )
        self.commands.register(
            "help.open_logs_folder",
            "Open Logs Folder",
            self.open_logs_folder,
            None,
        )
        self.commands.register(
            "help.open_diagnostics_folder",
            "Open Diagnostics Folder",
            self.open_diagnostics_folder,
            None,
        )
        self.commands.register(
            "help.what_can_i_do_here",
            "What Can I Do Here?",
            self.show_context_help,
            None,
        )
        self.commands.register(
            "whisperer.about",
            "About BITS Whisperer (HTML Preview)",
            self.show_whisperer_about_page,
            None,
        )
        self.commands.register(
            "help.status_page",
            "Status Page (HTML Preview)",
            self.show_help_status_page,
            None,
        )
        self.commands.register(
            "tools.keyboard_trap_snapshot",
            "Keyboard Trap Audit Snapshot...",
            self.show_keyboard_trap_snapshot,
            None,
        )
        self.commands.register(
            "tools.accessibility_audit",
            "Accessibility Audit...",
            self.show_accessibility_audit,
            None,
        )
        self.commands.register(
            "tools.glow_audit_document",
            "GLOW Audit Current Document",
            self.glow_audit_document,
            None,
        )
        self.commands.register(
            "tools.glow_audit_selection",
            "GLOW Audit Selection",
            self.glow_audit_selection,
            None,
        )
        self.commands.register(
            "tools.glow_fix_document",
            "GLOW Fix Current Document",
            self.glow_fix_document,
            None,
        )
        self.commands.register(
            "tools.glow_fix_selection",
            "GLOW Fix Selection",
            self.glow_fix_selection,
            None,
        )
        self.commands.register(
            "edit.undo",
            "Undo",
            self.undo,
            self._binding_for("edit.undo"),
        )
        self.commands.register(
            "edit.redo",
            "Redo",
            self.redo,
            self._binding_for("edit.redo"),
        )
        self.commands.register(
            "edit.copy_with_source",
            "Copy With Source",
            self.copy_with_source,
            self._binding_for("edit.copy_with_source"),
        )
        self.commands.register(
            "edit.toggle_extend_selection_mode",
            "Toggle Extend Selection Mode",
            self.toggle_extend_selection_mode,
            self._binding_for("edit.toggle_extend_selection_mode"),
        )
        self.commands.register(
            "edit.find",
            "Find...",
            self.find_text,
            self._binding_for("edit.find"),
        )
        self.commands.register(
            "edit.find_next",
            "Find Next",
            self.find_next,
            self._binding_for("edit.find_next"),
        )
        self.commands.register(
            "edit.find_previous",
            "Find Previous",
            self.find_previous,
            self._binding_for("edit.find_previous"),
        )
        self.commands.register(
            "edit.replace",
            "Replace...",
            self.replace_text,
            self._binding_for("edit.replace"),
        )
        self.commands.register(
            "edit.find_all_matches",
            "Find All Matches",
            self.find_all_matches,
            self._binding_for("edit.find_all_matches"),
        )
        self.commands.register(
            "tools.search_in_files",
            "Search in Files...",
            self.search_in_files,
            self._binding_for("tools.search_in_files"),
        )
        self.commands.register(
            "tools.replace_in_files",
            "Replace Across Files...",
            self.replace_in_files,
            self._binding_for("tools.replace_in_files"),
        )
        self.commands.register(
            "edit.replace_all",
            "Replace All...",
            self.replace_all_text,
            self._binding_for("edit.replace_all"),
        )
        self.commands.register(
            "edit.insert_link",
            "Insert Link...",
            self.insert_link,
            self._binding_for("edit.insert_link"),
        )
        self.commands.register(
            "edit.follow_link",
            "Follow Link",
            self.follow_link,
            self._binding_for("edit.follow_link"),
        )
        self.commands.register(
            "edit.word_prediction",
            "Word Prediction...",
            self.show_word_prediction,
            self._binding_for("edit.word_prediction"),
        )
        self.commands.register(
            "edit.select_line",
            "Select Line",
            self.select_line,
            self._binding_for("edit.select_line"),
        )
        self.commands.register(
            "edit.select_paragraph",
            "Select Paragraph",
            self.select_paragraph,
            None,
        )
        self.commands.register(
            "edit.set_mark",
            "Set Mark",
            self.set_mark,
            self._binding_for("edit.set_mark"),
        )
        self.commands.register(
            "edit.pop_mark",
            "Pop Mark",
            self.pop_mark,
            self._binding_for("edit.pop_mark"),
        )
        self.commands.register(
            "edit.exchange_point_mark",
            "Exchange Point and Mark",
            self.exchange_point_and_mark,
            self._binding_for("edit.exchange_point_mark"),
        )
        self.commands.register(
            "edit.list_marks",
            "List Marks",
            self.list_marks,
            self._binding_for("edit.list_marks"),
        )
        self.commands.register(
            "edit.select_block",
            "Select Block",
            self.select_block,
            None,
        )
        self.commands.register(
            "edit.select_to_start_of_line",
            "Select to Start of Line",
            self.select_to_start_of_line,
            self._binding_for("edit.select_to_start_of_line"),
        )
        self.commands.register(
            "edit.select_to_end_of_line",
            "Select to End of Line",
            self.select_to_end_of_line,
            self._binding_for("edit.select_to_end_of_line"),
        )
        self.commands.register(
            "edit.select_to_start_of_document",
            "Select to Start of Document",
            self.select_to_start_of_document,
            self._binding_for("edit.select_to_start_of_document"),
        )
        self.commands.register(
            "edit.select_to_end_of_document",
            "Select to End of Document",
            self.select_to_end_of_document,
            self._binding_for("edit.select_to_end_of_document"),
        )
        self.commands.register(
            "format.insert_html_tag",
            "Insert HTML Tag...",
            self.insert_html_tag,
            self._binding_for("format.insert_html_tag"),
        )
        self.commands.register(
            "format.toggle_line_comment",
            "Toggle Line Comment",
            self.format_toggle_line_comment,
            self._binding_for("format.toggle_line_comment"),
        )
        self.commands.register(
            "format.toggle_block_comment",
            "Toggle Block Comment",
            self.format_toggle_block_comment,
            self._binding_for("format.toggle_block_comment"),
        )
        self.commands.register(
            "format.indent",
            "Indent",
            self.format_indent,
            self._binding_for("format.indent"),
        )
        self.commands.register(
            "format.outdent",
            "Outdent",
            self.format_outdent,
            self._binding_for("format.outdent"),
        )
        self.commands.register(
            "format.insert_markdown_tag",
            "Insert Markdown Tag...",
            self.insert_markdown_tag,
            self._binding_for("format.insert_markdown_tag"),
        )
        self.commands.register(
            "format.insert_snippet",
            "Insert Snippet...",
            self.insert_snippet,
            self._binding_for("format.insert_snippet"),
        )
        self.commands.register(
            "format.manage_snippets",
            "Manage Snippets...",
            self.manage_snippets,
            self._binding_for("format.manage_snippets"),
        )
        self.commands.register(
            "format.bold",
            "Bold",
            self.format_bold,
            self._binding_for("format.bold"),
        )
        self.commands.register(
            "format.italic",
            "Italic",
            self.format_italic,
            self._binding_for("format.italic"),
        )
        self.commands.register(
            "format.heading_1",
            "Insert Heading 1",
            lambda: self.format_heading(1),
            self._binding_for("format.heading_1"),
        )
        self.commands.register(
            "format.heading_2",
            "Insert Heading 2",
            lambda: self.format_heading(2),
            self._binding_for("format.heading_2"),
        )
        self.commands.register(
            "format.heading_3",
            "Insert Heading 3",
            lambda: self.format_heading(3),
            self._binding_for("format.heading_3"),
        )
        self.commands.register(
            "format.heading_4",
            "Insert Heading 4",
            lambda: self.format_heading(4),
            self._binding_for("format.heading_4"),
        )
        self.commands.register(
            "format.heading_5",
            "Insert Heading 5",
            lambda: self.format_heading(5),
            self._binding_for("format.heading_5"),
        )
        self.commands.register(
            "format.heading_6",
            "Insert Heading 6",
            lambda: self.format_heading(6),
            self._binding_for("format.heading_6"),
        )
        self.commands.register(
            "format.decrease_heading_level",
            "Decrease Heading Level",
            self.decrease_heading_level,
            self._binding_for("format.decrease_heading_level"),
        )
        self.commands.register(
            "format.increase_heading_level",
            "Increase Heading Level",
            self.increase_heading_level,
            self._binding_for("format.increase_heading_level"),
        )
        self.commands.register(
            "format.style_headings",
            "Style Headings...",
            self.style_headings,
            self._binding_for("format.style_headings"),
        )
        self.commands.register(
            "format.upper_case",
            "Upper Case",
            self.format_upper_case,
            self._binding_for("format.upper_case"),
        )
        self.commands.register(
            "format.lower_case",
            "Lower Case",
            self.format_lower_case,
            self._binding_for("format.lower_case"),
        )
        self.commands.register(
            "format.title_case",
            "Title Case",
            self.format_title_case,
            None,
        )
        self.commands.register(
            "format.sentence_case",
            "Sentence Case",
            self.format_sentence_case,
            None,
        )
        self.commands.register(
            "format.toggle_case",
            "Toggle Case",
            self.format_toggle_case,
            None,
        )
        self.commands.register(
            "format.move_line_up",
            "Move Line Up",
            self.move_line_up,
            self._binding_for("format.move_line_up"),
        )
        self.commands.register(
            "format.move_line_down",
            "Move Line Down",
            self.move_line_down,
            self._binding_for("format.move_line_down"),
        )
        self.commands.register(
            "format.duplicate_line",
            "Duplicate Line",
            self.duplicate_line,
            self._binding_for("format.duplicate_line"),
        )
        self.commands.register(
            "format.delete_line",
            "Delete Line",
            self.delete_line,
            self._binding_for("format.delete_line"),
        )
        self.commands.register(
            "format.join_lines",
            "Join Lines",
            self.join_lines,
            None,
        )
        self.commands.register(
            "format.insert_bullet_list",
            "Insert Bullet List",
            self.format_insert_bullet_list,
            None,
        )
        self.commands.register(
            "format.insert_numbered_list",
            "Insert Numbered List",
            self.format_insert_numbered_list,
            None,
        )
        self.commands.register(
            "format.insert_task_list",
            "Insert Task List",
            self.format_insert_task_list,
            None,
        )
        self.commands.register(
            "format.list_manager",
            "List Manager",
            self.open_list_manager,
            self._binding_for("format.list_manager"),
        )
        self.commands.register(
            "format.insert_code_block",
            "Insert Code Block",
            self.format_insert_code_block,
            None,
        )
        self.commands.register(
            "format.insert_footnote",
            "Insert Footnote",
            self.format_insert_footnote,
            None,
        )
        self.commands.register(
            "format.insert_table",
            "Insert Table",
            self.format_insert_table,
            None,
        )
        self.commands.register(
            "edit.sort_lines_ascending",
            "Sort Lines Ascending",
            self.sort_lines_ascending,
            None,
        )
        self.commands.register(
            "edit.sort_lines_descending",
            "Sort Lines Descending",
            self.sort_lines_descending,
            None,
        )
        self.commands.register(
            "edit.reverse_lines",
            "Reverse Lines",
            self.reverse_lines,
            None,
        )
        self.commands.register(
            "edit.remove_duplicate_lines",
            "Remove Duplicate Lines",
            self.remove_duplicate_lines,
            None,
        )
        self.commands.register(
            "edit.trim_trailing_whitespace",
            "Trim Trailing Whitespace",
            self.trim_trailing_whitespace,
            None,
        )
        self.commands.register(
            "edit.normalize_whitespace",
            "Normalize Whitespace",
            self.normalize_whitespace,
            None,
        )
        self.commands.register(
            "edit.convert_indentation_to_spaces",
            "Convert Indentation to Spaces",
            self.convert_indentation_to_spaces,
            None,
        )
        self.commands.register(
            "edit.convert_indentation_to_tabs",
            "Convert Indentation to Tabs",
            self.convert_indentation_to_tabs,
            None,
        )

    def _build_menu(self) -> None:
        wx = self._wx
        menu_bar = wx.MenuBar()

        self._id_new = wx.ID_NEW
        self._id_open = wx.ID_OPEN
        self._id_save = wx.ID_SAVE
        self._id_save_as = wx.ID_SAVEAS
        self._id_exit = wx.ID_EXIT
        self._id_palette = wx.NewIdRef()
        self._id_preferences = wx.NewIdRef()
        self._id_open_url = wx.NewIdRef()
        self._id_close_document = wx.NewIdRef()
        self._id_save_all = wx.NewIdRef()
        self._id_reload_from_disk = wx.NewIdRef()
        self._id_restore_backup = wx.NewIdRef()
        self._id_save_session = wx.NewIdRef()
        self._id_open_session = wx.NewIdRef()
        self._id_clear_recent_sessions = wx.NewIdRef()
        self._id_page_setup = wx.NewIdRef()
        self._id_print = wx.NewIdRef()
        self._id_save_plain_text = wx.NewIdRef()
        self._id_clear_recent = wx.NewIdRef()
        self._sessions_menu = wx.Menu()
        self._open_documents_menu = wx.Menu()
        self._recent_sessions_menu = wx.Menu()

        file_menu = wx.Menu()
        # --- Create / open ---
        file_menu.Append(self._id_new, self._menu_label("&New", "file.new"))
        file_menu.Append(self._id_open, self._menu_label("&Open...", "file.open"))
        self._recent_menu = wx.Menu()
        file_menu.AppendSubMenu(self._recent_menu, "Open &Recent")
        self._refresh_recent_menu()
        file_menu.Append(self._id_open_url, "Open from &URL...")
        file_menu.AppendSubMenu(self._sessions_menu, "&Workspace Snapshots")
        file_menu.AppendSeparator()
        # --- Save ---
        file_menu.Append(self._id_save, self._menu_label("&Save", "file.save"))
        file_menu.Append(self._id_save_as, self._menu_label("Save &As...", "file.save_as"))
        file_menu.Append(self._id_save_all, "Save A&ll")
        file_menu.Append(self._id_save_plain_text, "Save As Plain &Text...")
        file_menu.AppendSeparator()
        # --- Restore / reload ---
        file_menu.Append(self._id_reload_from_disk, "&Reload from Disk")
        file_menu.Append(self._id_restore_backup, "Restore &Backup...")
        file_menu.AppendSeparator()
        # --- Print ---
        file_menu.Append(self._id_page_setup, "Pa&ge Setup...")
        file_menu.Append(self._id_print, self._menu_label("&Print...", "file.print"))
        file_menu.AppendSeparator()
        # --- Close ---
        file_menu.Append(
            self._id_close_document,
            self._menu_label("&Close Document", "file.close_document"),
        )
        file_menu.Append(self._id_exit, self._menu_label("E&xit", "app.exit"))
        menu_bar.Append(file_menu, "&File")

        self._id_find = wx.NewIdRef()
        self._id_undo = wx.NewIdRef()
        self._id_redo = wx.NewIdRef()
        self._id_copy_with_source = wx.NewIdRef()
        self._id_toggle_extend_selection_mode = wx.NewIdRef()
        self._id_replace = wx.NewIdRef()
        self._id_replace_all = wx.NewIdRef()
        self._id_find_next = wx.NewIdRef()
        self._id_find_previous = wx.NewIdRef()
        self._id_find_all_matches = wx.NewIdRef()
        self._id_search_in_files = wx.NewIdRef()
        self._id_replace_in_files = wx.NewIdRef()
        self._id_insert_link = wx.NewIdRef()
        self._id_follow_link = wx.NewIdRef()
        self._id_word_prediction = wx.NewIdRef()
        self._id_select_line = wx.NewIdRef()
        self._id_select_paragraph = wx.NewIdRef()
        self._id_select_block = wx.NewIdRef()
        self._id_select_to_start_of_line = wx.NewIdRef()
        self._id_select_to_end_of_line = wx.NewIdRef()
        self._id_select_to_start_of_document = wx.NewIdRef()
        self._id_select_to_end_of_document = wx.NewIdRef()
        self._id_set_mark = wx.NewIdRef()
        self._id_pop_mark = wx.NewIdRef()
        self._id_exchange_point_mark = wx.NewIdRef()
        self._id_list_marks = wx.NewIdRef()
        self._id_sort_lines_ascending = wx.NewIdRef()
        self._id_sort_lines_descending = wx.NewIdRef()
        self._id_reverse_lines = wx.NewIdRef()
        self._id_remove_duplicate_lines = wx.NewIdRef()
        self._id_trim_trailing_whitespace = wx.NewIdRef()
        self._id_normalize_whitespace = wx.NewIdRef()
        self._id_convert_indentation_to_spaces = wx.NewIdRef()
        self._id_convert_indentation_to_tabs = wx.NewIdRef()
        edit_menu = wx.Menu()
        edit_menu.Append(self._id_undo, self._menu_label("&Undo", "edit.undo"))
        edit_menu.Append(self._id_redo, self._menu_label("&Redo", "edit.redo"))
        edit_menu.AppendSeparator()
        # Standard clipboard items. wxTextCtrl routes these IDs natively, so
        # we don't need to bind handlers; the active editor handles them.
        edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X")
        edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        edit_menu.Append(
            self._id_copy_with_source,
            self._menu_label("Copy With &Source", "edit.copy_with_source"),
        )
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        # Selection submenu (detailed selection operations + mark ring)
        # is populated later in this method and appended here.
        edit_menu.AppendCheckItem(
            self._id_toggle_extend_selection_mode,
            self._menu_label(
                "E&xtend Selection Mode",
                "edit.toggle_extend_selection_mode",
            ),
        )
        edit_menu.Check(self._id_toggle_extend_selection_mode, self._extend_selection_mode)
        edit_menu.AppendSeparator()
        edit_menu.Append(
            self._id_insert_link,
            self._menu_label("Insert &Link...", "edit.insert_link"),
        )
        edit_menu.Append(
            self._id_follow_link,
            self._menu_label("&Follow Link", "edit.follow_link"),
        )
        edit_menu.Append(
            self._id_word_prediction,
            self._menu_label("&Word Prediction...", "edit.word_prediction"),
        )
        edit_menu.AppendSeparator()
        selection_menu = wx.Menu()
        selection_menu.Append(
            self._id_select_line,
            self._menu_label("Select &Line", "edit.select_line"),
        )
        selection_menu.Append(
            self._id_select_paragraph,
            self._menu_label("Select &Paragraph", "edit.select_paragraph"),
        )
        selection_menu.Append(
            self._id_select_block,
            self._menu_label("Select &Block", "edit.select_block"),
        )
        selection_menu.AppendSeparator()
        selection_menu.Append(
            self._id_select_to_end_of_line,
            self._menu_label("Select to End of &Line", "edit.select_to_end_of_line"),
        )
        selection_menu.Append(
            self._id_select_to_start_of_line,
            self._menu_label(
                "Select to Start of Li&ne",
                "edit.select_to_start_of_line",
            ),
        )
        selection_menu.Append(
            self._id_select_to_end_of_document,
            self._menu_label(
                "Select to End of &Document",
                "edit.select_to_end_of_document",
            ),
        )
        selection_menu.Append(
            self._id_select_to_start_of_document,
            self._menu_label(
                "Select to Start of D&ocument",
                "edit.select_to_start_of_document",
            ),
        )
        mark_ring_menu = wx.Menu()
        mark_ring_menu.Append(
            self._id_set_mark,
            self._menu_label("&Set Temporary Mark", "edit.set_mark"),
        )
        mark_ring_menu.Append(
            self._id_pop_mark,
            self._menu_label("&Jump to Previous Mark", "edit.pop_mark"),
        )
        mark_ring_menu.Append(
            self._id_exchange_point_mark,
            self._menu_label(
                "&Swap Cursor and Mark",
                "edit.exchange_point_mark",
            ),
        )
        mark_ring_menu.Append(
            self._id_list_marks,
            self._menu_label("&List Recent Marks", "edit.list_marks"),
        )
        selection_menu.AppendSeparator()
        selection_menu.AppendSubMenu(mark_ring_menu, "Recent &Marks (Ring)")
        edit_menu.AppendSubMenu(selection_menu, "&Selection")
        edit_menu.AppendSeparator()
        edit_menu.Append(
            self._id_preferences,
            self._menu_label("Pre&ferences...", "app.preferences"),
        )
        menu_bar.Append(edit_menu, "&Edit")
        insert_menu = wx.Menu()
        menu_bar.Append(insert_menu, "&Insert")

        search_menu = wx.Menu()
        search_menu.Append(self._id_find, self._menu_label("&Find...", "edit.find"))
        search_menu.Append(
            self._id_replace,
            self._menu_label("&Replace...", "edit.replace"),
        )
        search_menu.AppendSeparator()
        search_menu.Append(
            self._id_find_next,
            self._menu_label("Find &Next", "edit.find_next"),
        )
        search_menu.Append(
            self._id_find_previous,
            self._menu_label("Find &Previous", "edit.find_previous"),
        )
        search_menu.Append(
            self._id_find_all_matches,
            self._menu_label("Find &All Matches", "edit.find_all_matches"),
        )
        search_menu.AppendSeparator()
        search_menu.Append(
            self._id_search_in_files,
            self._menu_label("Search in &Files...", "tools.search_in_files"),
        )
        search_menu.Append(
            self._id_replace_in_files,
            self._menu_label("&Replace Across Files...", "tools.replace_in_files"),
        )
        self._id_send_to_tray = wx.NewIdRef()
        self._id_toggle_tray_mode = wx.NewIdRef()
        self._id_toggle_soft_wrap = wx.NewIdRef()
        self._id_toggle_tab_control = wx.NewIdRef()
        self._id_toggle_find_wrap = wx.NewIdRef()
        self._id_toggle_title_full_path = wx.NewIdRef()
        self._id_toggle_auto_check_updates = wx.NewIdRef()
        self._id_toggle_dark_mode = wx.NewIdRef()
        self._id_toggle_persistent_undo = wx.NewIdRef()
        self._id_toggle_spellcheck_as_you_type = wx.NewIdRef()
        self._id_toggle_intellisense_as_you_type = wx.NewIdRef()
        self._id_browser_preview = wx.NewIdRef()
        self._id_preview = wx.NewIdRef()
        self._id_split_preview = wx.NewIdRef()
        self._id_focus_preview = wx.NewIdRef()
        self._id_toggle_auto_side_preview = wx.NewIdRef()
        self._id_start_with_no_document_open = wx.NewIdRef()
        self._id_dirty_title_text = wx.NewIdRef()
        self._id_dirty_title_asterisk = wx.NewIdRef()
        self._id_dirty_title_asterisk_text = wx.NewIdRef()
        view_menu = wx.Menu()
        view_menu.AppendCheckItem(self._id_toggle_tray_mode, "Enable System Tray &Mode")
        view_menu.Check(self._id_toggle_tray_mode, self.settings.tray_enabled)
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(
            self._id_toggle_soft_wrap,
            self._menu_label("Toggle Soft &Wrap", "view.toggle_soft_wrap"),
        )
        view_menu.Check(self._id_toggle_soft_wrap, self.settings.soft_wrap)
        view_menu.AppendCheckItem(self._id_toggle_auto_side_preview, "&Auto Side-by-Side Preview")
        view_menu.Check(self._id_toggle_auto_side_preview, self.settings.auto_side_preview)
        view_menu.AppendCheckItem(self._id_toggle_tab_control, "Show &Tab Control")
        view_menu.Check(self._id_toggle_tab_control, self.settings.show_tab_control)
        view_menu.AppendCheckItem(self._id_toggle_find_wrap, "Wrap &Find Searches")
        view_menu.Check(self._id_toggle_find_wrap, self.settings.wrap_find)
        view_menu.AppendCheckItem(self._id_toggle_title_full_path, "Show Full Path in &Title Bar")
        view_menu.Check(
            self._id_toggle_title_full_path,
            getattr(self.settings, "title_bar_path_mode", "name") == "full_path",
        )
        dirty_menu = wx.Menu()
        dirty_menu.AppendRadioItem(self._id_dirty_title_text, "Dirty Indicator: Text")
        dirty_menu.AppendRadioItem(self._id_dirty_title_asterisk, "Dirty Indicator: Asterisk")
        dirty_menu.AppendRadioItem(
            self._id_dirty_title_asterisk_text,
            "Dirty Indicator: Asterisk + Text",
        )
        dirty_style = getattr(self.settings, "dirty_title_style", "text")
        dirty_menu.Check(self._id_dirty_title_text, dirty_style == "text")
        dirty_menu.Check(self._id_dirty_title_asterisk, dirty_style == "asterisk")
        dirty_menu.Check(
            self._id_dirty_title_asterisk_text,
            dirty_style == "asterisk_text",
        )
        view_menu.AppendSubMenu(dirty_menu, "&Dirty Title Style")
        view_menu.AppendCheckItem(self._id_toggle_dark_mode, "Toggle &Dark Mode")
        view_menu.Check(self._id_toggle_dark_mode, self.settings.theme == "dark")
        view_menu.AppendCheckItem(
            self._id_toggle_persistent_undo,
            "Enable &Persistent Undo",
        )
        view_menu.Check(self._id_toggle_persistent_undo, self.settings.persistent_undo)
        view_menu.AppendCheckItem(
            self._id_toggle_spellcheck_as_you_type,
            "Spell Check As You &Type",
        )
        view_menu.Check(
            self._id_toggle_spellcheck_as_you_type,
            self.settings.spellcheck_as_you_type,
        )
        view_menu.AppendCheckItem(
            self._id_toggle_intellisense_as_you_type,
            "Word Prediction As You &Type",
        )
        view_menu.Check(
            self._id_toggle_intellisense_as_you_type,
            getattr(self.settings, "intellisense_as_you_type", False),
        )
        view_menu.AppendCheckItem(
            self._id_start_with_no_document_open,
            "Start With &No Document Open",
        )
        view_menu.Check(
            self._id_start_with_no_document_open,
            self.settings.start_with_no_document_open,
        )
        view_menu.Append(
            self._id_preview,
            self._menu_label("&Preview...", "view.preview"),
        )
        view_menu.Append(
            self._id_split_preview,
            self._menu_label("Preview &Side by Side", "view.split_preview"),
        )
        view_menu.Append(
            self._id_focus_preview,
            self._menu_label("&Focus Preview", "view.focus_preview"),
        )
        view_menu.Append(
            self._id_browser_preview,
            self._menu_label("&Browser Preview...", "view.browser_preview"),
        )
        menu_bar.Append(view_menu, "&View")
        menu_bar.Append(search_menu, "&Search")

        navigate_menu = wx.Menu()
        self._id_go_to_line = wx.NewIdRef()
        self._id_set_bookmark = wx.NewIdRef()
        self._id_go_to_bookmark = wx.NewIdRef()
        self._id_list_bookmarks = wx.NewIdRef()
        self._id_go_to_page = wx.NewIdRef()
        self._id_back_location = wx.NewIdRef()
        self._id_forward_location = wx.NewIdRef()
        self._id_next_heading = wx.NewIdRef()
        self._id_previous_heading = wx.NewIdRef()
        self._id_next_block = wx.NewIdRef()
        self._id_previous_block = wx.NewIdRef()
        self._id_outline_navigator = wx.NewIdRef()
        self._id_heading_organizer = wx.NewIdRef()
        self._id_match_bracket = wx.NewIdRef()
        self._id_next_structure = wx.NewIdRef()
        self._id_previous_structure = wx.NewIdRef()
        self._id_next_region = wx.NewIdRef()
        self._id_previous_region = wx.NewIdRef()
        navigate_menu.Append(
            self._id_go_to_line,
            self._menu_label("&Go To Line...", "navigate.go_to_line"),
        )
        navigate_menu.Append(
            self._id_go_to_page,
            self._menu_label("Go To &Page...", "navigate.go_to_page"),
        )
        navigate_menu.Append(
            self._id_back_location,
            self._menu_label("&Back Location", "navigate.back_location"),
        )
        navigate_menu.Append(
            self._id_forward_location,
            self._menu_label("&Forward Location", "navigate.forward_location"),
        )
        navigate_menu.Append(
            self._id_next_heading,
            self._menu_label("Next &Heading", "navigate.next_heading"),
        )
        navigate_menu.Append(
            self._id_previous_heading,
            self._menu_label("Pre&vious Heading", "navigate.previous_heading"),
        )
        navigate_menu.Append(
            self._id_next_block,
            self._menu_label("Next &Block", "navigate.next_block"),
        )
        navigate_menu.Append(
            self._id_previous_block,
            self._menu_label("Previous Bl&ock", "navigate.previous_block"),
        )
        navigate_menu.Append(
            self._id_outline_navigator,
            self._menu_label("Outline &Navigator...", "navigate.outline_navigator"),
        )
        navigate_menu.Append(
            self._id_heading_organizer,
            self._menu_label("&Heading Organizer...", "navigate.heading_organizer"),
        )
        navigate_menu.Append(
            self._id_match_bracket,
            self._menu_label("Match &Bracket", "navigate.match_bracket"),
        )
        navigate_menu.Append(
            self._id_next_structure,
            self._menu_label("Next Str&ucture", "navigate.next_structure"),
        )
        navigate_menu.Append(
            self._id_previous_structure,
            self._menu_label("Previous Structu&re", "navigate.previous_structure"),
        )
        navigate_menu.Append(
            self._id_next_region,
            self._menu_label("Next Re&gion", "navigate.next_region"),
        )
        navigate_menu.Append(
            self._id_previous_region,
            self._menu_label("Previous Regio&n", "navigate.previous_region"),
        )
        navigate_menu.AppendSeparator()
        navigate_menu.Append(
            self._id_set_bookmark,
            self._menu_label("Set &Bookmark...", "navigate.set_bookmark"),
        )
        navigate_menu.Append(
            self._id_go_to_bookmark,
            self._menu_label("Go To &Bookmark...", "navigate.go_to_bookmark"),
        )
        navigate_menu.Append(
            self._id_list_bookmarks,
            self._menu_label("List B&ookmarks...", "navigate.list_bookmarks"),
        )
        self._id_insert_html_tag = wx.NewIdRef()
        self._id_insert_markdown_tag = wx.NewIdRef()
        self._id_insert_snippet = wx.NewIdRef()
        self._id_manage_snippets = wx.NewIdRef()
        self._id_format_bold = wx.NewIdRef()
        self._id_format_italic = wx.NewIdRef()
        self._id_heading_1 = wx.NewIdRef()
        self._id_heading_2 = wx.NewIdRef()
        self._id_heading_3 = wx.NewIdRef()
        self._id_heading_4 = wx.NewIdRef()
        self._id_heading_5 = wx.NewIdRef()
        self._id_heading_6 = wx.NewIdRef()
        self._id_decrease_heading_level = wx.NewIdRef()
        self._id_increase_heading_level = wx.NewIdRef()
        self._id_style_headings = wx.NewIdRef()
        self._id_upper_case = wx.NewIdRef()
        self._id_lower_case = wx.NewIdRef()
        self._id_title_case = wx.NewIdRef()
        self._id_sentence_case = wx.NewIdRef()
        self._id_toggle_case = wx.NewIdRef()
        self._id_toggle_line_comment = wx.NewIdRef()
        self._id_toggle_block_comment = wx.NewIdRef()
        self._id_indent = wx.NewIdRef()
        self._id_outdent = wx.NewIdRef()
        self._id_move_line_up = wx.NewIdRef()
        self._id_move_line_down = wx.NewIdRef()
        self._id_duplicate_line = wx.NewIdRef()
        self._id_delete_line = wx.NewIdRef()
        self._id_join_lines = wx.NewIdRef()
        self._id_insert_bullet_list = wx.NewIdRef()
        self._id_insert_numbered_list = wx.NewIdRef()
        self._id_insert_task_list = wx.NewIdRef()
        self._id_open_list_manager = wx.NewIdRef()
        self._id_insert_code_block = wx.NewIdRef()
        self._id_insert_footnote = wx.NewIdRef()
        self._id_insert_table = wx.NewIdRef()
        format_menu = wx.Menu()
        format_menu.Append(
            self._id_upper_case,
            self._menu_label("&Upper Case", "format.upper_case"),
        )
        format_menu.Append(
            self._id_lower_case,
            self._menu_label("&Lower Case", "format.lower_case"),
        )
        format_menu.Append(
            self._id_title_case,
            self._menu_label("&Title Case", "format.title_case"),
        )
        format_menu.Append(
            self._id_sentence_case,
            self._menu_label("&Sentence Case", "format.sentence_case"),
        )
        format_menu.Append(
            self._id_toggle_case,
            self._menu_label("To&ggle Case", "format.toggle_case"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(
            self._id_toggle_line_comment,
            self._menu_label(
                "Toggle Line &Comment",
                "format.toggle_line_comment",
            ),
        )
        format_menu.Append(
            self._id_toggle_block_comment,
            self._menu_label(
                "Toggle &Block Comment",
                "format.toggle_block_comment",
            ),
        )
        format_menu.Append(
            self._id_indent,
            self._menu_label("&Indent", "format.indent"),
        )
        format_menu.Append(
            self._id_outdent,
            self._menu_label("O&utdent", "format.outdent"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(
            self._id_move_line_up,
            self._menu_label("Move Line &Up", "format.move_line_up"),
        )
        format_menu.Append(
            self._id_move_line_down,
            self._menu_label("Move Line &Down", "format.move_line_down"),
        )
        format_menu.Append(
            self._id_duplicate_line,
            self._menu_label("&Duplicate Line", "format.duplicate_line"),
        )
        format_menu.Append(
            self._id_delete_line,
            self._menu_label("&Delete Line", "format.delete_line"),
        )
        format_menu.Append(
            self._id_join_lines,
            self._menu_label("&Join Lines", "format.join_lines"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(self._id_format_bold, self._menu_label("&Bold", "format.bold"))
        format_menu.Append(self._id_format_italic, self._menu_label("&Italic", "format.italic"))
        heading_menu = wx.Menu()
        heading_menu.Append(self._id_heading_1, self._menu_label("Heading &1", "format.heading_1"))
        heading_menu.Append(self._id_heading_2, self._menu_label("Heading &2", "format.heading_2"))
        heading_menu.Append(self._id_heading_3, self._menu_label("Heading &3", "format.heading_3"))
        heading_menu.Append(self._id_heading_4, self._menu_label("Heading &4", "format.heading_4"))
        heading_menu.Append(self._id_heading_5, self._menu_label("Heading &5", "format.heading_5"))
        heading_menu.Append(self._id_heading_6, self._menu_label("Heading &6", "format.heading_6"))
        heading_menu.AppendSeparator()
        heading_menu.Append(
            self._id_decrease_heading_level,
            self._menu_label(
                "Decrease Level",
                "format.decrease_heading_level",
            ),
        )
        heading_menu.Append(
            self._id_increase_heading_level,
            self._menu_label(
                "Increase Level",
                "format.increase_heading_level",
            ),
        )
        heading_menu.AppendSeparator()
        heading_menu.Append(
            self._id_style_headings,
            self._menu_label("&Style Headings...", "format.style_headings"),
        )
        insert_menu.Append(
            self._id_insert_link,
            self._menu_label("Insert &Link...", "edit.insert_link"),
        )
        insert_menu.AppendSeparator()
        insert_menu.AppendSubMenu(heading_menu, "&Heading")
        list_menu = wx.Menu()
        list_menu.Append(
            self._id_insert_bullet_list,
            self._menu_label("B&ullet", "format.insert_bullet_list"),
        )
        list_menu.Append(
            self._id_insert_numbered_list,
            self._menu_label("&Numbered", "format.insert_numbered_list"),
        )
        list_menu.Append(
            self._id_insert_task_list,
            self._menu_label("&Task", "format.insert_task_list"),
        )
        list_menu.AppendSeparator()
        list_menu.Append(
            self._id_open_list_manager,
            self._menu_label("List &Manager...", "format.list_manager"),
        )
        insert_menu.AppendSubMenu(list_menu, "&List")
        insert_menu.Append(
            self._id_insert_code_block,
            self._menu_label("Insert Code &Block", "format.insert_code_block"),
        )
        insert_menu.Append(
            self._id_insert_footnote,
            self._menu_label("Insert &Footnote", "format.insert_footnote"),
        )
        insert_menu.Append(
            self._id_insert_table,
            self._menu_label("Insert &Table...", "format.insert_table"),
        )
        insert_menu.AppendSeparator()
        insert_menu.Append(
            self._id_insert_html_tag,
            self._menu_label("Insert &HTML Tag...", "format.insert_html_tag"),
        )
        insert_menu.Append(
            self._id_insert_markdown_tag,
            self._menu_label("Insert &Markdown Tag...", "format.insert_markdown_tag"),
        )
        insert_menu.Append(
            self._id_insert_snippet,
            self._menu_label("Insert S&nippet...", "format.insert_snippet"),
        )
        insert_menu.Append(
            self._id_manage_snippets,
            self._menu_label("Manage Snippets...", "format.manage_snippets"),
        )
        self._id_next_document = wx.NewIdRef()
        self._id_previous_document = wx.NewIdRef()
        window_menu = wx.Menu()
        window_menu.Append(
            self._id_next_document,
            self._menu_label("&Next Document", "window.next_document"),
        )
        window_menu.Append(
            self._id_previous_document,
            self._menu_label("&Previous Document", "window.previous_document"),
        )
        window_menu.AppendSeparator()
        window_menu.Append(
            self._id_send_to_tray,
            self._menu_label("Send to S&ystem Tray", "view.send_to_tray"),
        )

        self._id_word_count = wx.NewIdRef()
        self._id_sticky_notes = wx.NewIdRef()
        self._id_new_sticky_note = wx.NewIdRef()
        self._id_spell_check = wx.NewIdRef()
        self._id_previous_misspelling = wx.NewIdRef()
        self._id_next_misspelling = wx.NewIdRef()
        self._id_misspelling_list = wx.NewIdRef()
        self._id_dictionary_status = wx.NewIdRef()
        self._id_ocr_image = wx.NewIdRef()
        self._id_regex_helper = wx.NewIdRef()
        self._id_pandoc_wizard = wx.NewIdRef()
        self._id_external_tools = wx.NewIdRef()
        self._id_read_aloud = wx.NewIdRef()
        self._id_read_aloud_stop = wx.NewIdRef()
        self._id_read_aloud_voice = wx.NewIdRef()
        self._id_read_aloud_settings = wx.NewIdRef()
        self._id_read_aloud_generate_audio = wx.NewIdRef()
        self._id_announcement_backend = wx.NewIdRef()
        self._id_announcement_backend_auto = wx.NewIdRef()
        self._id_announcement_backend_prism = wx.NewIdRef()
        self._id_announcement_backend_status_only = wx.NewIdRef()
        self._id_toggle_announcement_trace = wx.NewIdRef()
        self._id_dictation = wx.NewIdRef()
        self._id_dictation_voice_commands = wx.NewIdRef()
        self._id_watch_folder_toggle = wx.NewIdRef()
        self._id_watch_folder_settings = wx.NewIdRef()
        self._id_watch_folder_status = wx.NewIdRef()
        self._id_document_intake_report = wx.NewIdRef()
        self._id_review_extraction_quality = wx.NewIdRef()
        self._id_report_bad_extraction = wx.NewIdRef()
        self._id_shell_install = wx.NewIdRef()
        self._id_shell_remove = wx.NewIdRef()
        self._id_notifications = wx.NewIdRef()
        self._id_check_updates = wx.NewIdRef()
        self._id_validate_contrast = wx.NewIdRef()
        self._id_status_bar_settings = wx.NewIdRef()
        self._id_keymap_editor = wx.NewIdRef()
        self._id_export_keymap = wx.NewIdRef()
        self._id_import_keymap = wx.NewIdRef()
        self._id_reset_keymap = wx.NewIdRef()
        self._id_profiles_and_features = wx.NewIdRef()
        self._id_glow_audit_document = wx.NewIdRef()
        self._id_glow_audit_selection = wx.NewIdRef()
        self._id_glow_fix_document = wx.NewIdRef()
        self._id_glow_fix_selection = wx.NewIdRef()
        self._id_link_inventory = wx.NewIdRef()
        self._id_ai_hub = wx.NewIdRef()
        self._id_ai_assistant = wx.NewIdRef()
        self._id_ai_prompt_studio = wx.NewIdRef()
        self._id_ai_agent_center = wx.NewIdRef()
        self._id_ask_quill_chat = wx.NewIdRef()
        self._id_ai_enabled = wx.NewIdRef()
        self._id_ai_status_badge = wx.NewIdRef()
        self._id_ai_status_detail = wx.NewIdRef()
        self._id_ai_model = wx.NewIdRef()
        self._id_ai_connection = wx.NewIdRef()
        self._id_ai_rewrite_selection = wx.NewIdRef()
        self._id_ai_summarize_selection = wx.NewIdRef()
        self._id_ai_continue_writing = wx.NewIdRef()
        self._id_ai_fix_grammar = wx.NewIdRef()
        self._id_ai_speech_start_pause = wx.NewIdRef()
        self._id_ai_speech_stop = wx.NewIdRef()
        self._id_ai_speech_voice = wx.NewIdRef()
        self._id_ai_speech_settings = wx.NewIdRef()
        self._id_ai_speech_generate_audio = wx.NewIdRef()
        self._id_ai_speech_download_vibevoice = wx.NewIdRef()
        self._id_ai_speech_vibevoice_generate = wx.NewIdRef()
        self._id_train_style = wx.NewIdRef()
        self._id_compare_with_file = wx.NewIdRef()
        self._id_compare_open_documents = wx.NewIdRef()
        self._id_compare_next_difference = wx.NewIdRef()
        self._id_compare_previous_difference = wx.NewIdRef()
        self._id_compare_announce_difference = wx.NewIdRef()
        self._id_compare_difference_list = wx.NewIdRef()
        self._id_compare_toggle_sync = wx.NewIdRef()
        self._id_compare_options = wx.NewIdRef()
        self._id_compare_create_summary = wx.NewIdRef()
        self._id_compare_copy_current = wx.NewIdRef()
        self._id_compare_copy_all = wx.NewIdRef()
        self._id_start_macro_recording = wx.NewIdRef()
        self._id_stop_macro_recording = wx.NewIdRef()
        self._id_play_last_macro = wx.NewIdRef()
        self._id_manage_macros = wx.NewIdRef()
        self._id_open_welcome_guide = wx.NewIdRef()
        self._id_open_keyboard_reference = wx.NewIdRef()
        self._id_about_quill = wx.NewIdRef()
        self._id_save_diagnostics = wx.NewIdRef()
        self._id_report_bug = wx.NewIdRef()
        self._id_open_logs_folder = wx.NewIdRef()
        self._id_open_diagnostics_folder = wx.NewIdRef()
        self._id_context_help = wx.NewIdRef()
        self._id_help_status_page = wx.NewIdRef()
        self._id_why_dont_i_see_feature = wx.NewIdRef()
        self._id_switch_feature_profile = wx.NewIdRef()
        self._id_feature_profile_health_check = wx.NewIdRef()
        self._id_undo_profile_change = wx.NewIdRef()
        self._id_reset_feature_profile = wx.NewIdRef()
        self._id_profile_onboarding = wx.NewIdRef()
        self._id_keyboard_trap_snapshot = wx.NewIdRef()
        self._id_accessibility_audit = wx.NewIdRef()
        self._id_yaml_structure_editor = wx.NewIdRef()
        self._id_whisperer_about = wx.NewIdRef()
        tools_menu = wx.Menu()
        tools_menu.Append(
            self._id_palette,
            self._menu_label("&Command Palette...", "app.command_palette"),
        )
        tools_menu.AppendSeparator()
        sticky_notes_menu = wx.Menu()
        sticky_notes_menu.Append(
            self._id_sticky_notes,
            self._menu_label("&Sticky Notes...", "tools.sticky_notes"),
        )
        sticky_notes_menu.Append(
            self._id_new_sticky_note,
            self._menu_label("&New Sticky Note...", "tools.sticky_note_capture"),
        )
        tools_menu.AppendSubMenu(sticky_notes_menu, "&Sticky Notes")
        tools_menu.AppendSeparator()

        writing_menu = wx.Menu()
        writing_menu.Append(
            self._id_word_count,
            self._menu_label("&Word Count...", "tools.word_count"),
        )
        writing_menu.Append(
            self._id_spell_check,
            self._menu_label("&Spell Check...", "tools.spell_check_dialog"),
        )
        writing_menu.Append(
            self._id_previous_misspelling,
            self._menu_label("Previous Mi&sspelling", "tools.previous_misspelling"),
        )
        writing_menu.Append(
            self._id_next_misspelling,
            self._menu_label("Next &Misspelling", "tools.next_misspelling"),
        )
        writing_menu.Append(
            self._id_misspelling_list,
            self._menu_label("&Misspelling List...", "tools.misspelling_list"),
        )
        self._id_thesaurus = wx.NewIdRef()
        writing_menu.Append(
            self._id_thesaurus,
            self._menu_label("&Thesaurus...", "tools.thesaurus"),
        )
        writing_menu.Append(
            self._id_dictionary_status,
            self._menu_label("Dictionary &Status...", "tools.dictionary_status"),
        )
        tools_menu.AppendSubMenu(writing_menu, "&Writing and Language")

        read_aloud_menu = wx.Menu()
        read_aloud_menu.Append(
            self._id_read_aloud,
            self._menu_label("&Start / Pause", "tools.read_aloud_start_pause"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_stop,
            self._menu_label("S&top", "tools.read_aloud_stop"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_voice,
            self._menu_label("&Voice...", "tools.read_aloud_voice"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_settings,
            self._menu_label("Se&ttings...", "tools.read_aloud_settings"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_generate_audio,
            self._menu_label("Generate &Audio...", "tools.read_aloud_generate_audio"),
        )
        read_aloud_menu.Append(
            self._id_announcement_backend,
            self._menu_label("Announcement &Backend...", "tools.announcement_backend"),
        )
        backend_menu = wx.Menu()
        backend_menu.AppendRadioItem(
            self._id_announcement_backend_auto,
            "Automatic (Prism when available)",
        )
        backend_menu.AppendRadioItem(self._id_announcement_backend_prism, "Prism")
        backend_menu.AppendRadioItem(self._id_announcement_backend_status_only, "Status Bar Only")
        current_backend = self._announcement_engine.state().requested_backend
        backend_menu.Check(self._id_announcement_backend_auto, current_backend == "auto")
        backend_menu.Check(self._id_announcement_backend_prism, current_backend == "prism")
        backend_menu.Check(
            self._id_announcement_backend_status_only,
            current_backend == "status_only",
        )
        read_aloud_menu.AppendSubMenu(backend_menu, "Announcement Bac&kend")
        read_aloud_menu.AppendCheckItem(
            self._id_toggle_announcement_trace,
            "Capture Announcement &Trace in Diagnostics",
        )
        read_aloud_menu.Check(
            self._id_toggle_announcement_trace,
            self.settings.announcement_trace_enabled,
        )
        tools_menu.AppendSubMenu(read_aloud_menu, "Read &Aloud")

        dictation_menu = wx.Menu()
        dictation_menu.Append(
            self._id_dictation,
            self._menu_label("&Dictation", "tools.dictation_toggle"),
            "Press to start dictation, press again to stop and insert",
        )
        dictation_menu.AppendCheckItem(
            self._id_dictation_voice_commands,
            self._menu_label("&Hey QUILL Commands", "tools.dictation_voice_commands_toggle"),
        )
        dictation_menu.Check(
            self._id_dictation_voice_commands, self.settings.voice_commands_enabled
        )
        dictation_menu.AppendSeparator()
        dictation_menu.AppendCheckItem(
            self._id_watch_folder_toggle,
            self._menu_label("&Watch Folder Monitoring", "tools.watch_folder_toggle"),
        )
        dictation_menu.Check(
            self._id_watch_folder_toggle,
            bool(getattr(self.settings, "watch_folder_enabled", False))
            and self._watch_folder.is_running,
        )
        dictation_menu.Append(
            self._id_watch_folder_settings,
            self._menu_label("Watch Folder &Settings...", "tools.watch_folder_settings"),
        )
        dictation_menu.Append(
            self._id_watch_folder_status,
            self._menu_label("Watch Folder St&atus...", "tools.watch_folder_status"),
        )
        tools_menu.AppendSubMenu(dictation_menu, "D&ictation")

        integrations_menu = wx.Menu()
        integrations_menu.Append(
            self._id_ocr_image,
            self._menu_label("OCR &Image...", "tools.ocr_image"),
        )
        shell_menu = wx.Menu()
        shell_menu.Append(
            self._id_shell_install,
            self._menu_label("&Install Shell Integration...", "tools.shell_install"),
        )
        shell_menu.Append(
            self._id_shell_remove,
            self._menu_label("&Remove Shell Integration", "tools.shell_remove"),
        )
        integrations_menu.AppendSubMenu(shell_menu, "Sh&ell Integration")
        tools_menu.AppendSubMenu(integrations_menu, "&Integrations")

        intake_menu = wx.Menu()
        intake_menu.Append(
            self._id_document_intake_report,
            self._menu_label("&Document Intake Report...", "tools.document_intake_report"),
        )
        intake_menu.Append(
            self._id_review_extraction_quality,
            self._menu_label("&Review Extraction Quality...", "tools.review_extraction_quality"),
        )
        intake_menu.Append(
            self._id_report_bad_extraction,
            self._menu_label("R&eport Bad Extraction...", "tools.report_bad_extraction"),
        )
        tools_menu.AppendSubMenu(intake_menu, "Document &Intake")

        authoring_menu = wx.Menu()
        authoring_menu.Append(
            self._id_regex_helper,
            self._menu_label("Regex &Helper...", "tools.regex_helper"),
        )
        authoring_menu.Append(
            self._id_pandoc_wizard,
            self._menu_label("Pandoc Conversion &Wizard...", "tools.pandoc_wizard"),
        )
        authoring_menu.Append(
            self._id_external_tools,
            self._menu_label(
                "External Tools and Format &Support...",
                "tools.external_tools",
            ),
        )
        authoring_menu.Append(
            self._id_yaml_structure_editor,
            self._menu_label("&YAML Structure Editor...", "tools.yaml_structure_editor"),
        )
        ai_menu = wx.Menu()
        from quill.core.ai.model_manager import load_ai_enabled

        ai_menu.AppendCheckItem(self._id_ai_enabled, "Use Artificial &Intelligence")
        ai_menu.Check(self._id_ai_enabled, load_ai_enabled())
        ai_menu.AppendSeparator()
        ai_menu.Append(self._id_ai_status_badge, "AI Status: Not checked")
        ai_menu.Append(
            self._id_ai_status_detail, "AI Detail: Open AI Connection to verify settings"
        )
        ai_menu.Append(
            self._id_ai_hub,
            self._menu_label("AI &Hub...", "tools.ai_hub"),
        )
        ai_menu.Append(
            self._id_ask_quill_chat,
            self._menu_label("Ask Quill &Chat...", "tools.ask_quill_chat"),
        )
        ai_menu.Append(
            self._id_ai_model,
            self._menu_label("AI &Model && Connection...", "tools.ai_model"),
        )
        ai_menu.Append(
            self._id_ai_assistant,
            self._menu_label("&Writing Assistant...", "tools.ai_assistant"),
        )
        ai_menu.Append(
            self._id_ai_prompt_studio,
            self._menu_label("Prompt &Studio...", "tools.ai_prompt_studio"),
        )
        ai_menu.Append(
            self._id_ai_agent_center,
            self._menu_label("Agent &Center...", "tools.ai_agent_center"),
        )
        ai_menu.Append(
            self._id_ai_rewrite_selection,
            self._menu_label("&Rewrite Selection", "tools.ai_rewrite_selection"),
        )
        ai_menu.Append(
            self._id_ai_summarize_selection,
            self._menu_label("&Summarize Selection", "tools.ai_summarize_selection"),
        )
        ai_menu.Append(
            self._id_ai_continue_writing,
            self._menu_label("&Continue Writing", "tools.ai_continue_writing"),
        )
        ai_menu.Append(
            self._id_ai_fix_grammar,
            self._menu_label("Fix &Grammar", "tools.ai_fix_grammar"),
        )
        ai_menu.Append(
            self._id_train_style,
            self._menu_label("&Train Writing Style...", "tools.train_writing_style"),
        )
        speech_menu = wx.Menu()
        speech_menu.Append(
            self._id_ai_speech_start_pause,
            self._menu_label("Start / &Pause", "tools.read_aloud_start_pause"),
        )
        speech_menu.Append(
            self._id_ai_speech_stop,
            self._menu_label("S&top", "tools.read_aloud_stop"),
        )
        speech_menu.Append(
            self._id_ai_speech_voice,
            self._menu_label("&Voice...", "tools.read_aloud_voice"),
        )
        speech_menu.Append(
            self._id_ai_speech_settings,
            self._menu_label("Se&ttings...", "tools.read_aloud_settings"),
        )
        speech_menu.Append(
            self._id_ai_speech_generate_audio,
            self._menu_label("Generate &Audio...", "tools.read_aloud_generate_audio"),
        )
        if _vibevoice_feature_enabled():
            speech_menu.Append(
                self._id_ai_speech_download_vibevoice,
                self._menu_label("&Download VibeVoice Model...", "tools.download_vibevoice"),
            )
            speech_menu.Append(
                self._id_ai_speech_vibevoice_generate,
                self._menu_label("Generate with &VibeVoice...", "tools.generate_vibevoice_audio"),
            )
        ai_menu.AppendSubMenu(speech_menu, "&Speech")
        menu_bar.Append(ai_menu, "A&I")
        whisperer_menu = wx.Menu()
        whisperer_menu.Append(
            self._id_whisperer_about,
            self._menu_label("&About Whisperer (HTML Preview)...", "whisperer.about"),
        )
        whisperer_menu.Append(
            self._id_profile_onboarding,
            self._menu_label("&Startup Wizard...", "help.startup_wizard"),
        )
        menu_bar.Append(whisperer_menu, "&BITS Whisperer")
        glow_menu = wx.Menu()
        glow_menu.Append(
            self._id_glow_audit_document,
            self._menu_label("GLOW Audit Current &Document", "tools.glow_audit_document"),
        )
        glow_menu.Append(
            self._id_glow_audit_selection,
            self._menu_label("GLOW Audit &Selection", "tools.glow_audit_selection"),
        )
        glow_menu.AppendSeparator()
        glow_menu.Append(
            self._id_glow_fix_document,
            self._menu_label("&GLOW Fix Current Document", "tools.glow_fix_document"),
        )
        glow_menu.Append(
            self._id_glow_fix_selection,
            self._menu_label("GLOW Fix S&election", "tools.glow_fix_selection"),
        )
        authoring_menu.AppendSubMenu(glow_menu, "&GLOW")
        macro_menu = wx.Menu()
        macro_menu.Append(
            self._id_start_macro_recording,
            self._menu_label("&Start Recording", "tools.start_macro_recording"),
        )
        macro_menu.Append(
            self._id_stop_macro_recording,
            self._menu_label("S&top Recording", "tools.stop_macro_recording"),
        )
        macro_menu.Append(
            self._id_play_last_macro,
            self._menu_label("&Play Last Macro", "tools.play_last_macro"),
        )
        macro_menu.Append(
            self._id_manage_macros,
            self._menu_label("&Manage Macros...", "tools.manage_macros"),
        )
        authoring_menu.AppendSubMenu(macro_menu, "&Macros")
        convert_menu = wx.Menu()
        convert_menu.Append(
            self._id_sort_lines_ascending,
            self._menu_label("&Sort Lines Ascending", "edit.sort_lines_ascending"),
        )
        convert_menu.Append(
            self._id_sort_lines_descending,
            self._menu_label("Sort Lines &Descending", "edit.sort_lines_descending"),
        )
        convert_menu.Append(
            self._id_reverse_lines,
            self._menu_label("&Reverse Lines", "edit.reverse_lines"),
        )
        convert_menu.Append(
            self._id_remove_duplicate_lines,
            self._menu_label("Remove &Duplicate Lines", "edit.remove_duplicate_lines"),
        )
        convert_menu.AppendSeparator()
        convert_menu.Append(
            self._id_trim_trailing_whitespace,
            self._menu_label(
                "Trim Trailing &Whitespace",
                "edit.trim_trailing_whitespace",
            ),
        )
        convert_menu.Append(
            self._id_normalize_whitespace,
            self._menu_label("&Normalize Whitespace", "edit.normalize_whitespace"),
        )
        convert_menu.AppendSeparator()
        convert_menu.Append(
            self._id_convert_indentation_to_spaces,
            self._menu_label(
                "Convert Indentation to &Spaces",
                "edit.convert_indentation_to_spaces",
            ),
        )
        convert_menu.Append(
            self._id_convert_indentation_to_tabs,
            self._menu_label(
                "Convert Indentation to &Tabs",
                "edit.convert_indentation_to_tabs",
            ),
        )
        authoring_menu.AppendSubMenu(convert_menu, "Co&nvert")
        tools_menu.AppendSubMenu(authoring_menu, "Authoring && &Automation")

        compare_menu = wx.Menu()
        compare_menu.Append(self._id_compare_with_file, "Compare with &File...")
        compare_menu.Append(self._id_compare_open_documents, "Compare &Open Documents...")
        compare_menu.AppendSeparator()
        compare_menu.Append(self._id_compare_next_difference, "&Next Difference")
        compare_menu.Append(self._id_compare_previous_difference, "&Previous Difference")
        compare_menu.Append(self._id_compare_announce_difference, "&Announce Current Difference")
        compare_menu.Append(self._id_compare_difference_list, "Difference &List...")
        compare_menu.Append(self._id_compare_toggle_sync, "Toggle &Synchronized Navigation")
        compare_menu.Append(self._id_compare_options, "Compare O&ptions...")
        compare_menu.AppendSeparator()
        compare_menu.Append(self._id_compare_create_summary, "Create Difference &Summary")
        compare_menu.Append(self._id_compare_copy_current, "Copy &Current Difference")
        compare_menu.Append(self._id_compare_copy_all, "Copy A&ll Differences")
        tools_menu.AppendSubMenu(compare_menu, "&Compare Documents")

        accessibility_menu = wx.Menu()
        accessibility_menu.Append(self._id_accessibility_audit, "Accessibility A&udit...")
        accessibility_menu.Append(
            self._id_keyboard_trap_snapshot,
            "&Keyboard Trap && Tab-Order Snapshot...",
        )
        accessibility_menu.Append(self._id_validate_contrast, "&Validate Contrast...")
        accessibility_menu.Append(self._id_link_inventory, "Link Inventory && Alt-Text Catalo&g...")
        tools_menu.AppendSubMenu(accessibility_menu, "A&ccessibility")

        support_menu = wx.Menu()
        support_menu.Append(self._id_notifications, "Show &Notifications")
        support_menu.Append(self._id_report_bug, "&Report a Bug...")
        support_menu.Append(self._id_save_diagnostics, "Save &Diagnostics...")
        support_menu.Append(self._id_open_logs_folder, "Open &Logs Folder")
        support_menu.Append(
            self._id_open_diagnostics_folder,
            "Open &Diagnostics Folder",
        )
        support_menu.Append(self._id_check_updates, "Check for &Updates")
        tools_menu.AppendSubMenu(support_menu, "&Support")

        customize_menu = wx.Menu()
        customize_menu.Append(
            self._id_profiles_and_features,
            self._menu_label("&Profiles and Features...", "tools.profiles_and_features_settings"),
        )
        customize_menu.Append(self._id_status_bar_settings, "&Status Bar Layout...")
        customize_menu.AppendSeparator()
        customize_menu.Append(self._id_keymap_editor, "&Keymap Editor...")
        customize_menu.Append(self._id_export_keymap, "&Export Keymap...")
        customize_menu.Append(self._id_import_keymap, "&Import Keymap...")
        customize_menu.Append(self._id_reset_keymap, "&Reset Keymap")
        tools_menu.AppendSubMenu(customize_menu, "&Customize")
        menu_bar.Append(navigate_menu, "&Navigate")
        menu_bar.Append(format_menu, "F&ormat")
        menu_bar.Append(tools_menu, "&Tools")

        # The former top-level "Settings" menu is gone. Its contents now
        # live in Edit > Preferences and Tools > Customize, which is the
        # Windows/Office standard. Nothing references settings_menu after
        # this point; do not append it to the menu bar.

        help_menu = wx.Menu()
        help_menu.Append(
            self._id_context_help,
            self._menu_label("&What Can I Do Here?", "help.what_can_i_do_here"),
        )
        help_menu.Append(
            self._id_help_status_page,
            self._menu_label("Status &Page (HTML Preview)", "help.status_page"),
        )
        help_menu.Append(
            self._id_why_dont_i_see_feature,
            self._menu_label("&Why Don't I See a Feature?", "help.why_dont_i_see_feature"),
        )
        help_menu.AppendSeparator()
        self._id_open_user_guide = wx.NewIdRef()
        help_menu.Append(self._id_open_user_guide, "Open User &Guide")
        help_menu.Append(self._id_open_welcome_guide, "Open &Welcome Guide")
        help_menu.Append(self._id_open_keyboard_reference, "Open Keyboard &Reference")
        help_menu.Append(
            self._id_profile_onboarding,
            self._menu_label("&Startup Wizard...", "help.startup_wizard"),
        )
        help_menu.AppendSeparator()
        help_menu.Append(
            self._id_save_diagnostics,
            self._menu_label("Save &Diagnostics...", "help.save_diagnostics"),
        )
        help_menu.Append(
            self._id_report_bug,
            self._menu_label("Report a &Bug...", "help.report_bug"),
        )
        help_menu.AppendSeparator()
        profiles_menu = wx.Menu()
        profiles_menu.Append(
            self._id_switch_feature_profile,
            self._menu_label("&Switch Profile...", "help.switch_feature_profile"),
        )
        profiles_menu.Append(
            self._id_feature_profile_health_check,
            self._menu_label(
                "Profile &Health Check...",
                "help.feature_profile_health_check",
            ),
        )
        profiles_menu.AppendSeparator()
        profiles_menu.Append(
            self._id_undo_profile_change,
            self._menu_label("&Undo Last Profile Change", "help.undo_last_profile_change"),
        )
        profiles_menu.Append(
            self._id_reset_feature_profile,
            self._menu_label("Reset to &Essential Profile", "help.reset_feature_profile"),
        )
        help_menu.AppendSubMenu(profiles_menu, "Feature &Profiles")
        # "Check for Updates on Startup" lives in Settings now (removed the
        # duplicate Help-menu toggle).
        help_menu.Append(self._id_check_updates, "Check for &Updates...")
        help_menu.Append(self._id_about_quill, "&About Quill")
        menu_bar.Append(window_menu, "&Window")
        menu_bar.Append(help_menu, "&Help")

        self.frame.SetMenuBar(menu_bar)
        self._refresh_contextual_menu_items()
        self._apply_ai_menu_enabled()

        self.frame.Bind(wx.EVT_MENU, lambda _e: self.new_file(), id=self._id_new)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_file(), id=self._id_open)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_url(), id=self._id_open_url)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_file(), id=self._id_save)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_file_as(), id=self._id_save_as)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.close_current_document(),
            id=self._id_close_document,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_all_files(), id=self._id_save_all)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reload_from_disk(),
            id=self._id_reload_from_disk,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.restore_backup(),
            id=self._id_restore_backup,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_session(), id=self._id_save_session)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_session(), id=self._id_open_session)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.page_setup(), id=self._id_page_setup)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.print_document(), id=self._id_print)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.save_as_plain_text(),
            id=self._id_save_plain_text,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_palette(), id=self._id_palette)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_preferences(), id=self._id_preferences)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.exit_app(), id=self._id_exit)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_about_quill(), id=self._id_about_quill)
        # macOS routes the application-menu "About" to wx.ID_ABOUT — wire it to
        # the same custom dialog so the Apple-menu About shows the links too.
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_about_quill(), id=wx.ID_ABOUT)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_context_help(),
            id=self._id_context_help,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_help_status_page(),
            id=self._id_help_status_page,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_feature_explanation(),
            id=self._id_why_dont_i_see_feature,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.switch_feature_profile(),
            id=self._id_switch_feature_profile,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_feature_profile_health_check(),
            id=self._id_feature_profile_health_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.undo_last_profile_change(),
            id=self._id_undo_profile_change,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reset_feature_profile_to_essential(),
            id=self._id_reset_feature_profile,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.run_startup_wizard(),
            id=self._id_profile_onboarding,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_whisperer_about_page(),
            id=self._id_whisperer_about,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_hub(),
            id=self._id_ai_hub,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_writing_assistant(),
            id=self._id_ai_assistant,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_prompt_studio(),
            id=self._id_ai_prompt_studio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_agent_center(),
            id=self._id_ai_agent_center,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ask_quill_chat(),
            id=self._id_ask_quill_chat,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self._refresh_ai_status(),
            id=self._id_ai_status_badge,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_preferences(),
            id=self._id_ai_status_detail,
        )
        self.frame.Bind(wx.EVT_MENU, self._on_toggle_ai_enabled, id=self._id_ai_enabled)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_model_settings(),
            id=self._id_ai_model,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_preferences(),
            id=self._id_ai_connection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_rewrite_selection(),
            id=self._id_ai_rewrite_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_summarize_selection(),
            id=self._id_ai_summarize_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_continue_writing(),
            id=self._id_ai_continue_writing,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_fix_grammar(),
            id=self._id_ai_fix_grammar,
        )
        self._refresh_ai_status()
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.send_to_tray(), id=self._id_send_to_tray)
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_tray_mode,
            id=self._id_toggle_tray_mode,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_soft_wrap,
            id=self._id_toggle_soft_wrap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_auto_side_preview,
            id=self._id_toggle_auto_side_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_tab_control,
            id=self._id_toggle_tab_control,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_find_wrap,
            id=self._id_toggle_find_wrap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_title_full_path,
            id=self._id_toggle_title_full_path,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_auto_check_updates,
            id=self._id_toggle_auto_check_updates,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("text"),
            id=self._id_dirty_title_text,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("asterisk"),
            id=self._id_dirty_title_asterisk,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("asterisk_text"),
            id=self._id_dirty_title_asterisk_text,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_dark_mode,
            id=self._id_toggle_dark_mode,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_persistent_undo,
            id=self._id_toggle_persistent_undo,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_spellcheck_as_you_type,
            id=self._id_toggle_spellcheck_as_you_type,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_intellisense_as_you_type,
            id=self._id_toggle_intellisense_as_you_type,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.preview_in_app(),
            id=self._id_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_side_preview(),
            id=self._id_split_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.focus_preview(),
            id=self._id_focus_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.preview_in_browser(),
            id=self._id_browser_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_writing_assistant(),
            id=self._id_ai_assistant,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_train_writing_style(),
            id=self._id_train_style,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_start_with_no_document_open,
            id=self._id_start_with_no_document_open,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.next_document(), id=self._id_next_document)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.previous_document(),
            id=self._id_previous_document,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.insert_link(), id=self._id_insert_link)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.follow_link(), id=self._id_follow_link)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.select_line(), id=self._id_select_line)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_paragraph(),
            id=self._id_select_paragraph,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.select_block(), id=self._id_select_block)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_start_of_line(),
            id=self._id_select_to_start_of_line,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_end_of_line(),
            id=self._id_select_to_end_of_line,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_start_of_document(),
            id=self._id_select_to_start_of_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_end_of_document(),
            id=self._id_select_to_end_of_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.sort_lines_ascending(),
            id=self._id_sort_lines_ascending,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.sort_lines_descending(),
            id=self._id_sort_lines_descending,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.reverse_lines(), id=self._id_reverse_lines)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.remove_duplicate_lines(),
            id=self._id_remove_duplicate_lines,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.trim_trailing_whitespace(),
            id=self._id_trim_trailing_whitespace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.normalize_whitespace(),
            id=self._id_normalize_whitespace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.convert_indentation_to_spaces(),
            id=self._id_convert_indentation_to_spaces,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.convert_indentation_to_tabs(),
            id=self._id_convert_indentation_to_tabs,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.set_mark(), id=self._id_set_mark)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.pop_mark(), id=self._id_pop_mark)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.exchange_point_and_mark(),
            id=self._id_exchange_point_mark,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.list_marks(), id=self._id_list_marks)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.undo(), id=self._id_undo)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.redo(), id=self._id_redo)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_with_source(),
            id=self._id_copy_with_source,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_extend_selection_mode,
            id=self._id_toggle_extend_selection_mode,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_text(), id=self._id_find)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.replace_text(), id=self._id_replace)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.replace_all_text(), id=self._id_replace_all)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_line(), id=self._id_go_to_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_page(), id=self._id_go_to_page)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_back_location(),
            id=self._id_back_location,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_forward_location(),
            id=self._id_forward_location,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_heading(),
            id=self._id_next_heading,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_heading(),
            id=self._id_previous_heading,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_block(),
            id=self._id_next_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_block(),
            id=self._id_previous_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_outline_navigator(),
            id=self._id_outline_navigator,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_heading_organizer(),
            id=self._id_heading_organizer,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.match_bracket(),
            id=self._id_match_bracket,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_structure(),
            id=self._id_next_structure,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_structure(),
            id=self._id_previous_structure,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_region(),
            id=self._id_next_region,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_region(),
            id=self._id_previous_region,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.set_bookmark(), id=self._id_set_bookmark)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_bookmark(), id=self._id_go_to_bookmark)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.list_bookmarks(),
            id=self._id_list_bookmarks,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_next(), id=self._id_find_next)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_previous(), id=self._id_find_previous)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.find_all_matches(),
            id=self._id_find_all_matches,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.search_in_files(),
            id=self._id_search_in_files,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.replace_in_files(),
            id=self._id_replace_in_files,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_upper_case(), id=self._id_upper_case)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_lower_case(), id=self._id_lower_case)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_title_case(), id=self._id_title_case)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_sentence_case(),
            id=self._id_sentence_case,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_toggle_case(), id=self._id_toggle_case)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_toggle_line_comment(),
            id=self._id_toggle_line_comment,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_toggle_block_comment(),
            id=self._id_toggle_block_comment,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_indent(), id=self._id_indent)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_outdent(), id=self._id_outdent)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.move_line_up(), id=self._id_move_line_up)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.move_line_down(), id=self._id_move_line_down)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.duplicate_line(), id=self._id_duplicate_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.delete_line(), id=self._id_delete_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.join_lines(), id=self._id_join_lines)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_bold(), id=self._id_format_bold)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_italic(), id=self._id_format_italic)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(1), id=self._id_heading_1)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(2), id=self._id_heading_2)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(3), id=self._id_heading_3)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(4), id=self._id_heading_4)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(5), id=self._id_heading_5)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(6), id=self._id_heading_6)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.decrease_heading_level(),
            id=self._id_decrease_heading_level,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.increase_heading_level(),
            id=self._id_increase_heading_level,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.style_headings(), id=self._id_style_headings)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_bullet_list(),
            id=self._id_insert_bullet_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_numbered_list(),
            id=self._id_insert_numbered_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_task_list(),
            id=self._id_insert_task_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_list_manager(),
            id=self._id_open_list_manager,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_code_block(),
            id=self._id_insert_code_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_footnote(),
            id=self._id_insert_footnote,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_table(),
            id=self._id_insert_table,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.insert_html_tag(), id=self._id_insert_html_tag)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.insert_markdown_tag(),
            id=self._id_insert_markdown_tag,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.insert_snippet(),
            id=self._id_insert_snippet,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_snippets(),
            id=self._id_manage_snippets,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_word_prediction(),
            id=self._id_word_prediction,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_sticky_notes(),
            id=self._id_sticky_notes,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.create_sticky_note(),
            id=self._id_new_sticky_note,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_word_count(), id=self._id_word_count)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_spell_check_dialog(),
            id=self._id_spell_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.previous_misspelling(),
            id=self._id_previous_misspelling,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.next_misspelling(),
            id=self._id_next_misspelling,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_misspelling_list(),
            id=self._id_misspelling_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_thesaurus(),
            id=self._id_thesaurus,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_dictionary_status(),
            id=self._id_dictionary_status,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.ocr_image_file(), id=self._id_ocr_image)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_regex_helper(), id=self._id_regex_helper)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.toggle_read_aloud(), id=self._id_read_aloud)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_read_aloud(),
            id=self._id_read_aloud_stop,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_voice(),
            id=self._id_read_aloud_voice,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_settings(),
            id=self._id_read_aloud_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.generate_speech_audio(),
            id=self._id_read_aloud_generate_audio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_read_aloud(),
            id=self._id_ai_speech_start_pause,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_read_aloud(),
            id=self._id_ai_speech_stop,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_voice(),
            id=self._id_ai_speech_voice,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_settings(),
            id=self._id_ai_speech_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.generate_speech_audio(),
            id=self._id_ai_speech_generate_audio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.download_vibevoice_model(),
            id=self._id_ai_speech_download_vibevoice,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.generate_speech_with_vibevoice(),
            id=self._id_ai_speech_vibevoice_generate,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_announcement_backend(),
            id=self._id_announcement_backend,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("auto"),
            id=self._id_announcement_backend_auto,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("prism"),
            id=self._id_announcement_backend_prism,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("status_only"),
            id=self._id_announcement_backend_status_only,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_announcement_trace_capture(),
            id=self._id_toggle_announcement_trace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_dictation(),
            id=self._id_dictation,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_dictation_voice_commands(),
            id=self._id_dictation_voice_commands,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_watch_folder_monitoring(),
            id=self._id_watch_folder_toggle,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_watch_folder_settings(),
            id=self._id_watch_folder_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_watch_folder_status(),
            id=self._id_watch_folder_status,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_document_intake_report(),
            id=self._id_document_intake_report,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.review_extraction_quality(),
            id=self._id_review_extraction_quality,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.report_bad_extraction(),
            id=self._id_report_bad_extraction,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_pandoc_wizard(),
            id=self._id_pandoc_wizard,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_external_tools_dialog(),
            id=self._id_external_tools,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.install_shell_integration(),
            id=self._id_shell_install,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.remove_shell_integration(),
            id=self._id_shell_remove,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_notifications(),
            id=self._id_notifications,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.check_for_updates(),
            id=self._id_check_updates,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.validate_contrast(),
            id=self._id_validate_contrast,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_status_bar_settings(),
            id=self._id_status_bar_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_keymap_editor(),
            id=self._id_keymap_editor,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_profiles_and_features_settings(),
            id=self._id_profiles_and_features,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_link_inventory(),
            id=self._id_link_inventory,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_with_file(),
            id=self._id_compare_with_file,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_open_documents(),
            id=self._id_compare_open_documents,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_next_difference(),
            id=self._id_compare_next_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_previous_difference(),
            id=self._id_compare_previous_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_announce_difference(),
            id=self._id_compare_announce_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_compare_difference_list(),
            id=self._id_compare_difference_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_compare_synchronization(),
            id=self._id_compare_toggle_sync,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_compare_options(),
            id=self._id_compare_options,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.create_compare_summary_document(),
            id=self._id_compare_create_summary,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_current_difference(),
            id=self._id_compare_copy_current,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_all_differences(),
            id=self._id_compare_copy_all,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.start_macro_recording(),
            id=self._id_start_macro_recording,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_macro_recording(),
            id=self._id_stop_macro_recording,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.play_last_macro(),
            id=self._id_play_last_macro,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_macros(),
            id=self._id_manage_macros,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.export_keymap_file(),
            id=self._id_export_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.import_keymap_file(),
            id=self._id_import_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reset_keymap_defaults(),
            id=self._id_reset_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_welcome_guide(),
            id=self._id_open_welcome_guide,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_keyboard_reference(),
            id=self._id_open_keyboard_reference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_user_guide(),
            id=self._id_open_user_guide,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.save_diagnostics_bundle(),
            id=self._id_save_diagnostics,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.report_bug(),
            id=self._id_report_bug,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_logs_folder(),
            id=self._id_open_logs_folder,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_diagnostics_folder(),
            id=self._id_open_diagnostics_folder,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_yaml_structure_editor(),
            id=self._id_yaml_structure_editor,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_accessibility_audit(),
            id=self._id_accessibility_audit,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_document(),
            id=self._id_glow_audit_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_selection(),
            id=self._id_glow_audit_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_document(),
            id=self._id_glow_fix_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_selection(),
            id=self._id_glow_fix_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_keyboard_trap_snapshot(),
            id=self._id_keyboard_trap_snapshot,
        )
        self.frame.Bind(wx.EVT_MENU, self._on_open_recent)
        self.frame.Bind(wx.EVT_MENU, self._on_session_menu)
        self.frame.Bind(wx.EVT_MENU, self._on_recent_session_menu)
        self.frame.Bind(wx.EVT_MENU, self._on_menu_command_activity)

    def _apply_accelerators(self) -> None:
        wx = self._wx
        command_to_menu_id = self._command_to_menu_id_map()
        entries: list[object] = []
        for command_id, menu_id in command_to_menu_id.items():
            binding = self.commands.keybinding_for(command_id)
            parsed = self._parse_keybinding(binding)
            if parsed is None:
                continue
            flags, key_code = parsed
            entries.append(wx.AcceleratorEntry(flags, key_code, menu_id))
        entries.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_F4, self._id_close_document))

        self.frame.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _reload_global_hotkeys(self) -> None:
        if self._safe_mode:
            return
        self._unregister_global_hotkeys()
        binding = self._binding_for("tools.sticky_note_capture")
        parsed = self._parse_keybinding(binding)
        if parsed is None or not hasattr(self.frame, "RegisterHotKey"):
            return
        flags, key_code = parsed
        try:
            self.frame.RegisterHotKey(int(self._sticky_note_hotkey_id), flags, key_code)
        except Exception:
            self._set_status("Sticky note hotkey could not be registered")

    def _unregister_global_hotkeys(self) -> None:
        if not hasattr(self.frame, "UnregisterHotKey"):
            return
        try:
            self.frame.UnregisterHotKey(int(self._sticky_note_hotkey_id))
        except Exception:
            pass

    def _on_global_hotkey(self, event: object) -> None:
        if event.GetId() == int(self._sticky_note_hotkey_id):
            self.create_sticky_note()
            return
        event.Skip()

    def _command_to_menu_id_map(self) -> dict[str, int]:
        return {
            "file.new": self._id_new,
            "file.open": self._id_open,
            "file.save": self._id_save,
            "file.save_as": self._id_save_as,
            "file.close_document": self._id_close_document,
            "file.save_all": self._id_save_all,
            "file.reload_from_disk": self._id_reload_from_disk,
            "file.restore_backup": self._id_restore_backup,
            "file.page_setup": self._id_page_setup,
            "file.print": self._id_print,
            "window.next_document": self._id_next_document,
            "window.previous_document": self._id_previous_document,
            "view.send_to_tray": self._id_send_to_tray,
            "view.toggle_soft_wrap": self._id_toggle_soft_wrap,
            "view.toggle_find_wrap": self._id_toggle_find_wrap,
            "view.preview": self._id_preview,
            "view.split_preview": self._id_split_preview,
            "view.focus_preview": self._id_focus_preview,
            "view.browser_preview": self._id_browser_preview,
            "tools.read_aloud_generate_audio": self._id_read_aloud_generate_audio,
            "tools.ai_hub": self._id_ai_hub,
            "tools.download_vibevoice": self._id_ai_speech_download_vibevoice,
            "tools.generate_vibevoice_audio": self._id_ai_speech_vibevoice_generate,
            "tools.ai_assistant": self._id_ai_assistant,
            "tools.ai_prompt_studio": self._id_ai_prompt_studio,
            "tools.ai_agent_center": self._id_ai_agent_center,
            "tools.ask_quill_chat": self._id_ask_quill_chat,
            "tools.ai_model": self._id_ai_model,
            "tools.ai_connection": self._id_ai_connection,
            "tools.ai_rewrite_selection": self._id_ai_rewrite_selection,
            "tools.ai_summarize_selection": self._id_ai_summarize_selection,
            "tools.ai_continue_writing": self._id_ai_continue_writing,
            "tools.ai_fix_grammar": self._id_ai_fix_grammar,
            "tools.train_writing_style": self._id_train_style,
            "app.exit": self._id_exit,
            "app.command_palette": self._id_palette,
            "app.preferences": self._id_preferences,
            "edit.undo": self._id_undo,
            "edit.redo": self._id_redo,
            "edit.toggle_extend_selection_mode": self._id_toggle_extend_selection_mode,
            "edit.insert_link": self._id_insert_link,
            "edit.follow_link": self._id_follow_link,
            "edit.find": self._id_find,
            "edit.find_next": self._id_find_next,
            "edit.find_previous": self._id_find_previous,
            "edit.find_all_matches": self._id_find_all_matches,
            "edit.replace": self._id_replace,
            "edit.replace_all": self._id_replace_all,
            "edit.select_to_start_of_line": self._id_select_to_start_of_line,
            "edit.select_to_end_of_line": self._id_select_to_end_of_line,
            "edit.select_to_start_of_document": self._id_select_to_start_of_document,
            "edit.select_to_end_of_document": self._id_select_to_end_of_document,
            "edit.set_mark": self._id_set_mark,
            "edit.pop_mark": self._id_pop_mark,
            "edit.exchange_point_mark": self._id_exchange_point_mark,
            "edit.list_marks": self._id_list_marks,
            "navigate.go_to_line": self._id_go_to_line,
            "navigate.go_to_page": self._id_go_to_page,
            "navigate.list_bookmarks": self._id_list_bookmarks,
            "navigate.back_location": self._id_back_location,
            "navigate.forward_location": self._id_forward_location,
            "navigate.outline_navigator": self._id_outline_navigator,
            "navigate.heading_organizer": self._id_heading_organizer,
            "navigate.match_bracket": self._id_match_bracket,
            "navigate.next_structure": self._id_next_structure,
            "navigate.previous_structure": self._id_previous_structure,
            "navigate.next_region": self._id_next_region,
            "navigate.previous_region": self._id_previous_region,
            "tools.word_count": self._id_word_count,
            "tools.sticky_notes": self._id_sticky_notes,
            "tools.sticky_note_capture": self._id_new_sticky_note,
            "tools.spell_check_dialog": self._id_spell_check,
            "tools.previous_misspelling": self._id_previous_misspelling,
            "tools.next_misspelling": self._id_next_misspelling,
            "tools.misspelling_list": self._id_misspelling_list,
            "tools.thesaurus": self._id_thesaurus,
            "tools.dictionary_status": self._id_dictionary_status,
            "tools.announcement_backend": self._id_announcement_backend,
            "tools.announcement_trace_toggle": self._id_toggle_announcement_trace,
            "tools.watch_folder_toggle": self._id_watch_folder_toggle,
            "tools.watch_folder_settings": self._id_watch_folder_settings,
            "tools.watch_folder_status": self._id_watch_folder_status,
            "tools.document_intake_report": self._id_document_intake_report,
            "tools.review_extraction_quality": self._id_review_extraction_quality,
            "tools.report_bad_extraction": self._id_report_bad_extraction,
            "tools.pandoc_wizard": self._id_pandoc_wizard,
            "tools.external_tools": self._id_external_tools,
            "tools.compare_with_file": self._id_compare_with_file,
            "tools.compare_open_documents": self._id_compare_open_documents,
            "tools.compare_next_difference": self._id_compare_next_difference,
            "tools.compare_previous_difference": self._id_compare_previous_difference,
            "tools.compare_announce_difference": self._id_compare_announce_difference,
            "tools.compare_difference_list": self._id_compare_difference_list,
            "tools.compare_toggle_sync": self._id_compare_toggle_sync,
            "tools.compare_options": self._id_compare_options,
            "tools.compare_create_summary": self._id_compare_create_summary,
            "tools.compare_copy_current_difference": self._id_compare_copy_current,
            "tools.compare_copy_all_differences": self._id_compare_copy_all,
            "tools.start_macro_recording": self._id_start_macro_recording,
            "tools.stop_macro_recording": self._id_stop_macro_recording,
            "tools.play_last_macro": self._id_play_last_macro,
            "tools.manage_macros": self._id_manage_macros,
            "tools.glow_audit_document": self._id_glow_audit_document,
            "tools.glow_audit_selection": self._id_glow_audit_selection,
            "tools.glow_fix_document": self._id_glow_fix_document,
            "tools.glow_fix_selection": self._id_glow_fix_selection,
            "help.save_diagnostics": self._id_save_diagnostics,
            "help.report_bug": self._id_report_bug,
            "help.open_logs_folder": self._id_open_logs_folder,
            "help.open_diagnostics_folder": self._id_open_diagnostics_folder,
            "help.status_page": self._id_help_status_page,
            "help.startup_wizard": self._id_profile_onboarding,
            "whisperer.about": self._id_whisperer_about,
            "tools.yaml_structure_editor": self._id_yaml_structure_editor,
            "edit.copy_with_source": self._id_copy_with_source,
            "edit.select_line": self._id_select_line,
            "format.decrease_heading_level": self._id_decrease_heading_level,
            "format.increase_heading_level": self._id_increase_heading_level,
            "format.style_headings": self._id_style_headings,
            "format.bold": self._id_format_bold,
            "format.italic": self._id_format_italic,
            "format.upper_case": self._id_upper_case,
            "format.lower_case": self._id_lower_case,
            "format.heading_1": self._id_heading_1,
            "format.heading_2": self._id_heading_2,
            "format.heading_3": self._id_heading_3,
            "format.heading_4": self._id_heading_4,
            "format.heading_5": self._id_heading_5,
            "format.heading_6": self._id_heading_6,
            "format.toggle_line_comment": self._id_toggle_line_comment,
            "format.toggle_block_comment": self._id_toggle_block_comment,
            "format.indent": self._id_indent,
            "format.outdent": self._id_outdent,
            "format.move_line_up": self._id_move_line_up,
            "format.move_line_down": self._id_move_line_down,
            "format.duplicate_line": self._id_duplicate_line,
            "format.delete_line": self._id_delete_line,
            "format.insert_html_tag": self._id_insert_html_tag,
            "format.insert_markdown_tag": self._id_insert_markdown_tag,
            "format.insert_snippet": self._id_insert_snippet,
            "format.manage_snippets": self._id_manage_snippets,
            "edit.word_prediction": self._id_word_prediction,
        }

    def _on_command_run(self, command_id: str) -> None:
        self._record_macro_step(command_id)
        record_diagnostic_event("command", command_id)

    def _on_menu_command_activity(self, event: object) -> None:
        command_id = None
        command_by_menu_id = {
            menu_id: cid for cid, menu_id in self._command_to_menu_id_map().items()
        }
        get_id = getattr(event, "GetId", None)
        if callable(get_id):
            command_id = command_by_menu_id.get(get_id())
        if command_id is not None:
            self._record_macro_step(command_id)
        skip = getattr(event, "Skip", None)
        if callable(skip):
            skip()

    def _parse_keybinding(self, keybinding: str | None) -> tuple[int, int] | None:
        if not keybinding:
            return None
        wx = self._wx
        parts = [part.strip() for part in keybinding.split("+") if part.strip()]
        if not parts:
            return None

        flags = 0
        for modifier in parts[:-1]:
            lowered = modifier.lower()
            if lowered == "ctrl":
                flags |= wx.ACCEL_CTRL
            elif lowered == "shift":
                flags |= wx.ACCEL_SHIFT
            elif lowered == "alt":
                flags |= wx.ACCEL_ALT
            else:
                return None

        key_token = parts[-1].upper()
        if len(key_token) == 1:
            return flags, ord(key_token)

        function_keys: dict[str, int] = {
            f"F{index}": getattr(wx, f"WXK_F{index}") for index in range(1, 13)
        }
        named_keys: dict[str, int] = {
            "ENTER": wx.WXK_RETURN,
            "TAB": wx.WXK_TAB,
            "SPACE": wx.WXK_SPACE,
            "ESC": wx.WXK_ESCAPE,
            "ESCAPE": wx.WXK_ESCAPE,
            "DELETE": wx.WXK_DELETE,
            "BACKSPACE": wx.WXK_BACK,
            "HOME": wx.WXK_HOME,
            "END": wx.WXK_END,
            "LEFT": wx.WXK_LEFT,
            "RIGHT": wx.WXK_RIGHT,
        }
        if key_token in function_keys:
            return flags, function_keys[key_token]
        if key_token in named_keys:
            return flags, named_keys[key_token]
        return None

    def _bind_events(self) -> None:
        wx = self._wx
        if self._tab_control_visible:
            self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_notebook_page_changed)
            self.notebook.Bind(wx.EVT_CONTEXT_MENU, self._on_notebook_context_menu)
            self.notebook.Bind(wx.EVT_KEY_DOWN, self._on_notebook_key_down)
        self.statusbar.Bind(wx.EVT_CONTEXT_MENU, self._on_statusbar_context_menu)
        self.frame.Bind(wx.EVT_CONTEXT_MENU, self._on_frame_context_menu)
        self.frame.Bind(wx.EVT_CLOSE, self._on_close)
        self.frame.Bind(wx.EVT_ICONIZE, self._on_iconize)
        self.frame.Bind(wx.EVT_HOTKEY, self._on_global_hotkey)
        self._apply_soft_wrap(self.settings.soft_wrap)

    def _bind_editor_events(self, editor: object) -> None:
        binder = getattr(editor, "bind_editor_events", None)
        if callable(binder):
            binder(self)
            return
        wx = self._wx
        editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        editor.Bind(wx.EVT_KEY_DOWN, self._on_editor_key_down)
        editor.Bind(wx.EVT_KEY_UP, self._on_editor_key_up)
        editor.Bind(wx.EVT_LEFT_UP, self._on_editor_caret_activity)
        editor.Bind(wx.EVT_SET_FOCUS, self._on_editor_caret_activity)
        editor.Bind(wx.EVT_CONTEXT_MENU, self._on_editor_context_menu)

    def _create_document_tab(self, document: Document, select: bool = True) -> int:
        wx = self._wx
        panel = wx.Panel(self.notebook)
        # The editor lives in a splitter so a live preview can be shown to its
        # right (View → Preview Side by Side). It starts unsplit (editor only).
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE | wx.SP_3DSASH)
        splitter.SetMinimumPaneSize(160)
        editor = wx.TextCtrl(
            splitter,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_NOHIDESEL,
        )
        splitter.Initialize(editor)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        if document.text:
            editor.ChangeValue(document.text)
        self._bind_editor_events(editor)
        tab = _DocumentTab(panel=panel, editor=editor, document=document, splitter=splitter)
        self._document_tabs.append(tab)
        index = self.notebook.GetPageCount()
        self.notebook.AddPage(panel, document.name, select=select)
        if select:
            self._active_tab_index = index
            self.editor = editor
            self.document = document
            self._apply_statusbar_layout()
            self._refresh_title()
            self._maybe_auto_side_preview(tab)
        self._refresh_sessions_menu()
        return index

    def _create_tab_host(self, show_tab_control: bool) -> object:
        wx = self._wx
        if show_tab_control:
            return wx.Notebook(self._documents_panel)
        simplebook = getattr(wx, "Simplebook", None)
        if simplebook is not None:
            return simplebook(self._documents_panel)
        return wx.Notebook(self._documents_panel)

    def _rebuild_tab_host(self, show_tab_control: bool) -> None:
        if show_tab_control == self._tab_control_visible:
            return
        wx = self._wx
        old_host = self.notebook
        active_index = self._current_tab_index()
        self._documents_sizer.Detach(old_host)
        new_host = self._create_tab_host(show_tab_control)
        self.notebook = new_host
        self._tab_control_visible = show_tab_control
        for index, tab in enumerate(self._document_tabs):
            tab.panel.Reparent(new_host)
            new_host.AddPage(tab.panel, tab.document.name, select=False)
            self._set_tab_page_text(index, tab.document.name)
        self._documents_sizer.Add(new_host, 1, wx.EXPAND)
        old_host.Destroy()
        if self._tab_control_visible:
            new_host.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_notebook_page_changed)
            new_host.Bind(wx.EVT_CONTEXT_MENU, self._on_notebook_context_menu)
            new_host.Bind(wx.EVT_KEY_DOWN, self._on_notebook_key_down)
        if 0 <= active_index < len(self._document_tabs):
            self._select_tab(active_index)
        self._documents_panel.Layout()
        self.frame.Layout()

    def _set_tab_page_text(self, index: int, title: str) -> None:
        setter = getattr(self.notebook, "SetPageText", None)
        if callable(setter) and 0 <= index < self.notebook.GetPageCount():
            setter(index, title)

    def _tab_page_title(self, index: int) -> str:
        if index < 0 or index >= len(self._document_tabs):
            return "this tab"
        return self._document_tabs[index].document.name or "this tab"

    def _on_notebook_page_changed(self, event: object) -> None:
        selection = self.notebook.GetSelection()
        if selection != self._active_tab_index:
            self._activate_tab(selection)
        event.Skip()

    def _on_notebook_key_down(self, event: object) -> None:
        wx = self._wx
        key_code = event.GetKeyCode()
        return_keys = {
            getattr(wx, "WXK_RETURN", 13),
            getattr(wx, "WXK_NUMPAD_ENTER", 13),
            getattr(wx, "WXK_SPACE", 32),
        }
        if key_code in return_keys:
            selection = self.notebook.GetSelection()
            if selection != getattr(wx, "NOT_FOUND", -1):
                self._activate_tab(selection)
                self.editor.SetFocus()
                self._set_status(f"Focused document {self.document.name}")
                return
        tab_key = getattr(wx, "WXK_TAB", 9)
        if key_code == tab_key and not event.ShiftDown():
            self.editor.SetFocus()
            self._set_status(f"Focused document {self.document.name}")
            return
        event.Skip()

    def _activate_tab(self, index: int) -> None:
        if index < 0 or index >= len(self._document_tabs):
            return
        tab = self._document_tabs[index]
        self._active_tab_index = index
        self.editor = tab.editor
        self.document = tab.document
        if self.settings.persistent_undo:
            if self.document.path is not None:
                self._load_persistent_undo_state(self.document.path, self.editor.GetValue())
            else:
                self._persistent_undo_history = [self.editor.GetValue()]
                self._persistent_undo_index = 0
        self._apply_statusbar_layout()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._refresh_sessions_menu()
        self._maybe_auto_side_preview(tab)

    def _maybe_auto_side_preview(self, tab) -> None:
        """Auto-show the side-by-side preview for previewable (Markdown/HTML)
        documents when the setting is on, so the user doesn't have to ask each
        time. Plain text is left alone, and an explicit toggle still wins."""
        if not getattr(self.settings, "auto_side_preview", True):
            return
        splitter = getattr(tab, "splitter", None)
        if splitter is None or splitter.IsSplit():
            return
        text = tab.editor.GetValue()
        if guess_preview_kind(tab.document.path, text) == "plain":
            return
        # Defer so the splitter has its real size before we set the sash.
        self._wx.CallAfter(self._show_side_preview_for, tab)

    def _show_side_preview_for(self, tab) -> None:
        splitter = getattr(tab, "splitter", None)
        if splitter is None or splitter.IsSplit():
            return
        if tab.preview is None:
            from quill.ui.preview_dialog import SidePreview

            tab.preview = SidePreview(splitter, on_return=self._focus_editor_from_preview)
        sash = max(splitter.GetClientSize().x // 2, 200)
        splitter.SplitVertically(tab.editor, tab.preview.control, sash)
        self._update_side_preview(tab)

    def _start_ipc_poll(self) -> None:
        wx = self._wx
        timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER, self._on_ipc_timer, timer)
        timer.Start(800)
        self._ipc_timer = timer

    def _on_ipc_timer(self, _event: object) -> None:
        requests = drain_open_requests()
        if not requests:
            return
        for candidate in requests:
            if candidate is None:
                continue
            if candidate.exists() and candidate.is_file():
                self.open_file(candidate)
        self.frame.Show(True)
        self.frame.Raise()
        self.frame.RequestUserAttention()

    def _on_text_changed(self, _event: object) -> None:
        if self._voice_command_guard:
            return
        if (
            not self._snippet_expansion_guard
            and self.settings.snippet_trigger_expansion
            and self._expand_snippet_trigger_if_match()
        ):
            return
        self._sync_editor_change("Modified")

    def _sync_editor_change(self, status: str) -> None:
        self.document.set_text(self.editor.GetValue())
        if not self._suspend_persistent_undo:
            self._record_persistent_undo_state(self.document.text)
        if self.settings.spellcheck_as_you_type:
            self._announce_spellcheck_hint()
        if self._dictation.state == "listening" and self.settings.voice_commands_enabled:
            self._schedule_voice_command_scan()
        self._refresh_intellisense_popup()
        self._refresh_side_preview()
        self._refresh_browser_preview()
        self._maybe_autosave()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        # Quiet: this fires on every keystroke; speaking "Modified" each time is
        # noise for a screen reader (it already echoes the typed character).
        self._set_status_quiet(status)

    def _on_csv_surface_changed(self) -> None:
        self._sync_editor_change("Modified")

    def _expand_snippet_trigger_if_match(self) -> bool:
        if self.editor.GetSelection()[0] != self.editor.GetSelection()[1]:
            return False
        text = self.editor.GetValue()
        caret = self.editor.GetInsertionPoint()
        if caret <= 0 or caret > len(text):
            return False
        delimiter = text[caret - 1]
        if delimiter not in {" ", "\n", "\t", ".", ",", ";", ":", "!", "?", ")", "]", "}"}:
            return False
        token_end = caret - 1
        token_start = token_end
        while token_start > 0 and not text[token_start - 1].isspace():
            token_start -= 1
        token = text[token_start:token_end]
        if not token.startswith(";") or len(token) < 2:
            return False
        snippet = find_snippet_by_trigger(self._snippet_library.snippets, token)
        if snippet is None:
            return False
        rendered = self._render_snippet_with_prompts(snippet)
        if rendered is None:
            return False
        before = text[:token_start]
        after = text[token_end:]
        has_cursor_marker = "${cursor}" in snippet.body
        new_text = before + rendered.text + after
        new_caret = token_start + rendered.cursor
        if not has_cursor_marker:
            new_caret += 1
        if new_caret < 0:
            new_caret = 0
        if new_caret > len(new_text):
            new_caret = len(new_text)
        self._snippet_expansion_guard = True
        try:
            self.editor.ChangeValue(new_text)
            self.editor.SetInsertionPoint(new_caret)
            self.editor.SetSelection(new_caret, new_caret)
        finally:
            self._snippet_expansion_guard = False
        self.document.set_text(new_text)
        if not self._suspend_persistent_undo:
            self._record_persistent_undo_state(new_text)
        self._maybe_autosave()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._set_status(f'Expanded snippet trigger "{snippet.trigger}".')
        return True

    def _on_editor_caret_activity(self, event: object) -> None:
        self._refresh_statusbar()
        event.Skip()

    def _on_editor_key_up(self, event: object) -> None:
        wx = self._wx
        if event.GetKeyCode() == wx.WXK_INSERT:
            self._insert_key_down = False
        self._on_editor_caret_activity(event)

    def _on_editor_key_down(self, event: object) -> None:
        wx = self._wx
        if event.ControlDown() and event.ShiftDown() and event.GetKeyCode() in (ord("O"), ord("o")):
            self.open_outline_navigator()
            return
        f8_key = getattr(wx, "WXK_F8", None)
        if (
            f8_key is not None
            and event.GetKeyCode() == f8_key
            and self._compare_session is not None
        ):
            if event.ControlDown() and event.ShiftDown():
                self.open_compare_options()
                return
            if event.ControlDown() and event.AltDown():
                self.toggle_compare_synchronization()
                return
            if event.ControlDown():
                self.compare_announce_difference()
                return
            if event.AltDown():
                self.open_compare_difference_list()
                return
            if event.ShiftDown():
                self.compare_previous_difference()
                return
            self.compare_next_difference()
            return
        if event.GetKeyCode() == wx.WXK_INSERT:
            if not self._insert_key_down:
                self._overwrite_mode = not self._overwrite_mode
                self._insert_key_down = True
                self._refresh_statusbar()
            event.Skip()
            return
        if self._handle_intellisense_key_down(event):
            return
        return_keys = {
            key
            for key in (
                getattr(wx, "WXK_RETURN", None),
                getattr(wx, "WXK_NUMPAD_ENTER", None),
            )
            if key is not None
        }
        if (
            return_keys
            and event.GetKeyCode() in return_keys
            and not event.ControlDown()
            and not event.AltDown()
            and not event.ShiftDown()
        ):
            if self._handle_markdown_list_return():
                return
        tab_key = getattr(wx, "WXK_TAB", None)
        if tab_key is not None and event.GetKeyCode() == tab_key:
            if self._is_caret_on_markdown_list_item():
                if event.ShiftDown():
                    self.format_outdent()
                    self._set_status("Promoted list item")
                else:
                    self.format_indent()
                    self._set_status("Nested list item")
                return
            if event.ShiftDown():
                self.format_outdent()
            else:
                self.format_indent()
            return
        if (
            hasattr(self, "_dictation")
            and self._dictation.state == "listening"
            and event.GetKeyCode() == wx.WXK_ESCAPE
        ):
            self.toggle_dictation()
            return
        if self._extend_selection_mode and event.GetKeyCode() == wx.WXK_ESCAPE:
            caret = self.editor.GetInsertionPoint()
            self.toggle_extend_selection_mode(False)
            self.editor.SetSelection(caret, caret)
            return
        if not self._extend_selection_mode:
            event.Skip()
            return
        movement_keys = {
            wx.WXK_LEFT,
            wx.WXK_RIGHT,
            wx.WXK_UP,
            wx.WXK_DOWN,
            wx.WXK_HOME,
            wx.WXK_END,
            wx.WXK_PAGEUP,
            wx.WXK_PAGEDOWN,
        }
        if event.GetKeyCode() not in movement_keys:
            event.Skip()
            return
        if self._extend_selection_anchor is None:
            self._extend_selection_anchor = self.editor.GetInsertionPoint()
        if self._move_extend_selection_caret(event):
            self._apply_extend_selection()
            return
        event.Skip()

    def _handle_markdown_list_return(self) -> bool:
        if infer_markup_kind(self.document.path) not in {"markdown", "plain"}:
            return False
        start, end = self.editor.GetSelection()
        if start != end:
            return False
        continuation = continue_markdown_list(
            self.editor.GetValue(), self.editor.GetInsertionPoint()
        )
        if continuation is None:
            return False
        self._replace_document_text(continuation.text)
        self.document.set_text(continuation.text)
        self.editor.SetInsertionPoint(continuation.caret)
        self.editor.SetSelection(continuation.caret, continuation.caret)
        if continuation.exited_list:
            self._set_status("Exited list")
        else:
            self._set_status("Continued list item")
        return True

    def _is_caret_on_markdown_list_item(self) -> bool:
        if infer_markup_kind(self.document.path) not in {"markdown", "plain"}:
            return False
        selection_start, selection_end = self.editor.GetSelection()
        if selection_start != selection_end:
            return False
        text = self.editor.GetValue()
        line_start, line_end = line_span(text, self.editor.GetInsertionPoint())
        line = text[line_start:line_end].strip()
        return bool(re.match(r"^(?:[-+*]|\d+[.)])\s+", line))

    def _apply_extend_selection(self) -> None:
        if not self._extend_selection_mode or self._extend_selection_anchor is None:
            return
        caret = self.editor.GetInsertionPoint()
        start = min(self._extend_selection_anchor, caret)
        end = max(self._extend_selection_anchor, caret)
        self.editor.SetSelection(start, end)

    def _move_extend_selection_caret(self, event: object) -> bool:
        wx = self._wx
        text = self.editor.GetValue()
        caret = self.editor.GetInsertionPoint()
        key_code = event.GetKeyCode()
        line_starts = [0]
        for index, character in enumerate(text):
            if character == "\n":
                line_starts.append(index + 1)

        def line_index_for_position(position: int) -> int:
            for index in range(1, len(line_starts)):
                if line_starts[index] > position:
                    return index - 1
            return len(line_starts) - 1

        def line_limit(index: int) -> int:
            if index + 1 < len(line_starts):
                return line_starts[index + 1] - 1
            return len(text)

        def move_vertical(delta: int) -> bool:
            current_line = line_index_for_position(caret)
            target_line = max(0, min(current_line + delta, len(line_starts) - 1))
            if target_line == current_line:
                return False
            column = caret - line_starts[current_line]
            target = min(line_starts[target_line] + column, line_limit(target_line))
            self.editor.SetInsertionPoint(target)
            return True

        def move_word(reverse: bool) -> bool:
            if not text:
                return False
            target = caret
            if reverse:
                while target > 0 and text[target - 1].isspace():
                    target -= 1
                while target > 0 and not text[target - 1].isspace():
                    target -= 1
            else:
                while target < len(text) and not text[target].isspace():
                    target += 1
                while target < len(text) and text[target].isspace():
                    target += 1
            if target == caret:
                return False
            self.editor.SetInsertionPoint(target)
            return True

        target = caret
        if event.ControlDown() and key_code == wx.WXK_HOME:
            target = 0
        elif event.ControlDown() and key_code == wx.WXK_END:
            target = len(text)
        elif event.ControlDown() and key_code == wx.WXK_LEFT:
            return move_word(reverse=True)
        elif event.ControlDown() and key_code == wx.WXK_RIGHT:
            return move_word(reverse=False)
        elif key_code == wx.WXK_LEFT:
            target = max(0, caret - 1)
        elif key_code == wx.WXK_RIGHT:
            target = min(len(text), caret + 1)
        elif key_code == wx.WXK_UP:
            return move_vertical(-1)
        elif key_code == wx.WXK_DOWN:
            return move_vertical(1)
        elif key_code == wx.WXK_HOME:
            target = line_starts[line_index_for_position(caret)]
        elif key_code == wx.WXK_END:
            target = line_limit(line_index_for_position(caret))
        elif key_code == wx.WXK_PAGEUP:
            return move_vertical(-10)
        elif key_code == wx.WXK_PAGEDOWN:
            return move_vertical(10)
        else:
            return False
        if target == caret:
            return False
        self.editor.SetInsertionPoint(target)
        return True

    def _move_point(self, position: int) -> None:
        capped = max(0, min(position, len(self.editor.GetValue())))
        self.editor.SetInsertionPoint(capped)
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._apply_extend_selection()
        else:
            self.editor.SetSelection(capped, capped)

    def _on_editor_context_menu(self, event: object) -> None:
        wx = self._wx
        menu = wx.Menu()

        # Inspect current context so we can offer context-aware actions.
        text = self.editor.GetValue()
        caret = self.editor.GetInsertionPoint()
        sel_start, sel_end = self.editor.GetSelection()
        has_selection = sel_end > sel_start
        link_target = find_link_at_cursor(text, caret) if text else None

        # --- Link actions appear first when the caret sits on a link. ---
        if link_target:
            open_link_id = wx.NewIdRef()
            copy_link_id = wx.NewIdRef()
            display_target = link_target if len(link_target) <= 60 else link_target[:57] + "..."
            menu.Append(open_link_id, f'Open Link  "{display_target}"')
            menu.Append(copy_link_id, "Copy Link Address")
            menu.AppendSeparator()
            menu.Bind(wx.EVT_MENU, lambda _e: self.follow_link(), id=open_link_id)
            menu.Bind(
                wx.EVT_MENU,
                lambda _e, target=link_target: (
                    self._copy_text_to_clipboard(target),
                    self._set_status(f"Copied link: {target}"),
                ),
                id=copy_link_id,
            )

        undo_id = wx.NewIdRef()
        redo_id = wx.NewIdRef()
        cut_id = wx.NewIdRef()
        copy_id = wx.NewIdRef()
        copy_source_id = wx.NewIdRef()
        paste_id = wx.NewIdRef()
        select_all_id = wx.NewIdRef()
        select_line_id = wx.NewIdRef()
        spell_id = wx.NewIdRef()
        next_spell_id = wx.NewIdRef()

        menu.Append(undo_id, self._menu_label("Undo", "edit.undo"))
        menu.Append(redo_id, self._menu_label("Redo", "edit.redo"))
        menu.AppendSeparator()
        cut_item = menu.Append(cut_id, "Cut")
        copy_item = menu.Append(copy_id, "Copy")
        copy_source_item = menu.Append(
            copy_source_id, self._menu_label("Copy With Source", "edit.copy_with_source")
        )
        menu.Append(paste_id, "Paste")
        menu.AppendSeparator()
        menu.Append(select_all_id, "Select All")
        menu.Append(select_line_id, "Select Line")

        # Disable selection-only actions when there is no selection.
        if not has_selection:
            cut_item.Enable(False)
            copy_item.Enable(False)
            copy_source_item.Enable(False)

        # --- Transform submenu (case + lines). Always available; some items
        #     are only meaningful with a selection but still safe to invoke. ---
        transform_menu = wx.Menu()
        upper_id = wx.NewIdRef()
        lower_id = wx.NewIdRef()
        title_id = wx.NewIdRef()
        sentence_id = wx.NewIdRef()
        toggle_case_id = wx.NewIdRef()
        sort_asc_id = wx.NewIdRef()
        sort_desc_id = wx.NewIdRef()
        transform_menu.Append(upper_id, "UPPER CASE")
        transform_menu.Append(lower_id, "lower case")
        transform_menu.Append(title_id, "Title Case")
        transform_menu.Append(sentence_id, "Sentence case")
        transform_menu.Append(toggle_case_id, "Toggle Case")
        transform_menu.AppendSeparator()
        transform_menu.Append(sort_asc_id, "Sort Lines Ascending")
        transform_menu.Append(sort_desc_id, "Sort Lines Descending")
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.format_upper_case(), id=upper_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.format_lower_case(), id=lower_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.format_title_case(), id=title_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.format_sentence_case(), id=sentence_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.format_toggle_case(), id=toggle_case_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.sort_lines_ascending(), id=sort_asc_id)
        transform_menu.Bind(wx.EVT_MENU, lambda _e: self.sort_lines_descending(), id=sort_desc_id)
        menu.AppendSubMenu(transform_menu, "Transform")

        # --- Line submenu. ---
        line_menu = wx.Menu()
        dup_id = wx.NewIdRef()
        del_id = wx.NewIdRef()
        move_up_id = wx.NewIdRef()
        move_down_id = wx.NewIdRef()
        join_id = wx.NewIdRef()
        line_menu.Append(dup_id, self._menu_label("Duplicate Line", "edit.duplicate_line"))
        line_menu.Append(del_id, self._menu_label("Delete Line", "edit.delete_line"))
        line_menu.Append(move_up_id, self._menu_label("Move Line Up", "edit.move_line_up"))
        line_menu.Append(move_down_id, self._menu_label("Move Line Down", "edit.move_line_down"))
        line_menu.Append(join_id, "Join With Next Line")
        line_menu.Bind(wx.EVT_MENU, lambda _e: self.duplicate_line(), id=dup_id)
        line_menu.Bind(wx.EVT_MENU, lambda _e: self.delete_line(), id=del_id)
        line_menu.Bind(wx.EVT_MENU, lambda _e: self.move_line_up(), id=move_up_id)
        line_menu.Bind(wx.EVT_MENU, lambda _e: self.move_line_down(), id=move_down_id)
        line_menu.Bind(wx.EVT_MENU, lambda _e: self.join_lines(), id=join_id)
        menu.AppendSubMenu(line_menu, "Line")

        glow_menu = wx.Menu()
        glow_audit_document_id = wx.NewIdRef()
        glow_audit_selection_id = wx.NewIdRef()
        glow_fix_document_id = wx.NewIdRef()
        glow_fix_selection_id = wx.NewIdRef()
        glow_menu.Append(glow_audit_document_id, "GLOW Audit Current Document")
        glow_menu.Append(glow_audit_selection_id, "GLOW Audit Selection / Paragraph")
        glow_menu.AppendSeparator()
        glow_menu.Append(glow_fix_document_id, "GLOW Fix Current Document")
        glow_menu.Append(glow_fix_selection_id, "GLOW Fix Selection / Paragraph")
        glow_menu.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_document(),
            id=glow_audit_document_id,
        )
        glow_menu.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_selection(),
            id=glow_audit_selection_id,
        )
        glow_menu.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_document(),
            id=glow_fix_document_id,
        )
        glow_menu.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_selection(),
            id=glow_fix_selection_id,
        )
        menu.AppendSubMenu(glow_menu, "GLOW")

        menu.AppendSeparator()
        menu.Append(spell_id, self._menu_label("Spell Check...", "tools.spell_check_dialog"))
        menu.Append(next_spell_id, self._menu_label("Next Misspelling", "tools.next_misspelling"))

        # --- Thesaurus lookup (when on/within a word). ---
        if thesaurus_engine.is_available():
            thes_id = wx.NewIdRef()
            menu.Append(thes_id, "Look Up in Thesaurus")
            menu.Bind(wx.EVT_MENU, lambda _e: self.show_thesaurus(), id=thes_id)

        dictionary = self._spell_dictionary()
        misspelling = misspelling_at_position(text, caret, dictionary)
        if misspelling is not None:
            spelling_menu = wx.Menu()
            suggestions = suggest_words(misspelling.word, dictionary)
            if suggestions:
                for suggestion in suggestions:
                    item_id = wx.NewIdRef()
                    spelling_menu.Append(item_id, suggestion)

                    def _apply_replacement(
                        _event,
                        replacement: str = suggestion,
                        start: int = misspelling.start,
                        end: int = misspelling.end,
                        original: str = misspelling.word,
                    ) -> None:
                        self.editor.Replace(start, end, replacement)
                        self.document.set_text(self.editor.GetValue())
                        self._set_status(f'Replaced "{original}" with "{replacement}"')

                    spelling_menu.Bind(
                        wx.EVT_MENU,
                        _apply_replacement,
                        id=item_id,
                    )
            else:
                empty_id = wx.NewIdRef()
                item = spelling_menu.Append(empty_id, "(No suggestions)")
                item.Enable(False)
            spelling_menu.AppendSeparator()
            add_menu = wx.Menu()
            personal_id = wx.NewIdRef()
            document_id = wx.NewIdRef()
            project_id = wx.NewIdRef()
            add_menu.Append(personal_id, "Personal dictionary")
            add_menu.Append(document_id, "Document dictionary")
            add_menu.Append(project_id, "Project dictionary")
            add_menu.Bind(
                wx.EVT_MENU,
                lambda _e, word=misspelling.word: self._add_word_to_dictionary_scope(word, 0),
                id=personal_id,
            )
            add_menu.Bind(
                wx.EVT_MENU,
                lambda _e, word=misspelling.word: self._add_word_to_dictionary_scope(word, 1),
                id=document_id,
            )
            add_menu.Bind(
                wx.EVT_MENU,
                lambda _e, word=misspelling.word: self._add_word_to_dictionary_scope(word, 2),
                id=project_id,
            )
            spelling_menu.AppendSubMenu(add_menu, "Add to dictionary")
            menu.AppendSubMenu(spelling_menu, "Spelling Suggestions")

        menu.AppendSeparator()
        # --- Navigation actions. ---
        go_line_id = wx.NewIdRef()
        bookmark_id = wx.NewIdRef()
        palette_id = wx.NewIdRef()
        menu.Append(go_line_id, self._menu_label("Go to Line...", "navigate.go_to_line"))
        menu.Append(bookmark_id, self._menu_label("Set Bookmark Here...", "navigate.set_bookmark"))
        menu.Append(palette_id, self._menu_label("Command Palette...", "app.command_palette"))

        menu.Bind(wx.EVT_MENU, lambda _e: self.undo(), id=undo_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.redo(), id=redo_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.editor.Cut(), id=cut_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.editor.Copy(), id=copy_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.copy_with_source(), id=copy_source_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.editor.Paste(), id=paste_id)
        menu.Bind(
            wx.EVT_MENU,
            lambda _e: self.editor.SetSelection(0, len(self.editor.GetValue())),
            id=select_all_id,
        )
        menu.Bind(wx.EVT_MENU, lambda _e: self.select_line(), id=select_line_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_spell_check_dialog(), id=spell_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.next_misspelling(), id=next_spell_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.go_to_line(), id=go_line_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.set_bookmark(), id=bookmark_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_palette(), id=palette_id)
        self._popup_context_menu(self.editor, menu, event)

    def _on_statusbar_context_menu(self, event: object) -> None:
        wx = self._wx
        menu = wx.Menu()
        dark_id = wx.NewIdRef()
        wrap_id = wx.NewIdRef()
        spell_id = wx.NewIdRef()
        layout_id = wx.NewIdRef()
        menu.AppendCheckItem(dark_id, "Dark Mode")
        menu.Check(dark_id, self.settings.theme == "dark")
        menu.AppendCheckItem(wrap_id, "Soft Wrap")
        menu.Check(wrap_id, self.settings.soft_wrap)
        menu.AppendCheckItem(spell_id, "Spell Check As You Type")
        menu.Check(spell_id, self.settings.spellcheck_as_you_type)
        menu.AppendSeparator()
        menu.Append(layout_id, "Status Bar Layout...")
        menu.Bind(wx.EVT_MENU, lambda _e: self.toggle_dark_mode(), id=dark_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.toggle_soft_wrap(), id=wrap_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.toggle_spellcheck_as_you_type(), id=spell_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_status_bar_settings(), id=layout_id)
        self._popup_context_menu(self.statusbar, menu, event)

    def _on_frame_context_menu(self, event: object) -> None:
        wx = self._wx
        menu = wx.Menu()
        new_id = wx.NewIdRef()
        open_id = wx.NewIdRef()
        save_id = wx.NewIdRef()
        palette_id = wx.NewIdRef()
        notifications_id = wx.NewIdRef()
        updates_id = wx.NewIdRef()
        menu.Append(new_id, self._menu_label("New", "file.new"))
        menu.Append(open_id, self._menu_label("Open...", "file.open"))
        menu.Append(save_id, self._menu_label("Save", "file.save"))
        menu.AppendSeparator()
        menu.Append(palette_id, self._menu_label("Command Palette...", "app.command_palette"))
        menu.Append(notifications_id, "Notifications...")
        menu.Append(updates_id, "Check for Updates...")
        menu.Bind(wx.EVT_MENU, lambda _e: self.new_file(), id=new_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_file(), id=open_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.save_file(), id=save_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_palette(), id=palette_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_notifications(), id=notifications_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.check_for_updates(), id=updates_id)
        self._popup_context_menu(self.frame, menu, event)

    def _on_notebook_context_menu(self, event: object) -> None:
        wx = self._wx
        if not self._document_tabs:
            event.Skip()
            return
        # Determine the tab under the cursor (if any).
        screen_pos = event.GetPosition()
        target_index = self._current_tab_index()
        try:
            client_pos = self.notebook.ScreenToClient(screen_pos)
            hit_index, _flags = self.notebook.HitTest(client_pos)
            if hit_index >= 0:
                target_index = hit_index
        except Exception:
            pass
        if target_index < 0 or target_index >= len(self._document_tabs):
            target_index = self._current_tab_index()
        tab_label = self._tab_page_title(target_index)

        menu = wx.Menu()
        close_id = wx.NewIdRef()
        close_others_id = wx.NewIdRef()
        close_right_id = wx.NewIdRef()
        copy_path_id = wx.NewIdRef()
        reveal_id = wx.NewIdRef()
        menu.Append(close_id, f'Close "{tab_label}"')
        menu.Append(close_others_id, "Close Other Tabs")
        menu.Append(close_right_id, "Close Tabs to the Right")
        menu.AppendSeparator()
        tab_document = self._document_tabs[target_index].document
        copy_item = menu.Append(copy_path_id, "Copy File Path")
        reveal_item = menu.Append(reveal_id, "Show in File Explorer")
        if tab_document.path is None:
            copy_item.Enable(False)
            reveal_item.Enable(False)
        if len(self._document_tabs) <= 1:
            close_others_id_item = menu.FindItemById(close_others_id)
            if close_others_id_item is not None:
                close_others_id_item.Enable(False)
        if target_index >= len(self._document_tabs) - 1:
            close_right_item = menu.FindItemById(close_right_id)
            if close_right_item is not None:
                close_right_item.Enable(False)

        menu.Bind(
            wx.EVT_MENU,
            lambda _e, idx=target_index: self._close_tab_at(idx),
            id=close_id,
        )
        menu.Bind(
            wx.EVT_MENU,
            lambda _e, idx=target_index: self._close_other_tabs(idx),
            id=close_others_id,
        )
        menu.Bind(
            wx.EVT_MENU,
            lambda _e, idx=target_index: self._close_tabs_to_right(idx),
            id=close_right_id,
        )
        if tab_document.path is not None:
            path_text = str(tab_document.path)
            menu.Bind(
                wx.EVT_MENU,
                lambda _e, text=path_text: (
                    self._copy_text_to_clipboard(text),
                    self._set_status(f"Copied path: {text}"),
                ),
                id=copy_path_id,
            )
            menu.Bind(
                wx.EVT_MENU,
                lambda _e, p=tab_document.path: self._reveal_in_explorer(p),
                id=reveal_id,
            )
        self._popup_context_menu(self.notebook, menu, event)

    def _close_tab_at(self, index: int) -> None:
        if index < 0 or index >= len(self._document_tabs):
            return
        previous_active = self._active_tab_index
        self._select_tab(index)
        if not self._prompt_to_save_active_document("closing"):
            self._select_tab(previous_active)
            self._set_status("Close cancelled")
            return
        self._close_tab(index)
        self._set_status("Closed document")

    def _close_other_tabs(self, keep_index: int) -> None:
        if keep_index < 0 or keep_index >= len(self._document_tabs):
            return
        keep_tab = self._document_tabs[keep_index]
        # Close from the end backwards so indices stay valid.
        closed = 0
        for index in range(len(self._document_tabs) - 1, -1, -1):
            if self._document_tabs[index] is keep_tab:
                continue
            self._select_tab(index)
            if not self._prompt_to_save_active_document("closing"):
                self._set_status("Close other tabs cancelled")
                # Restore focus to the tab we wanted to keep, if it still exists.
                if keep_tab in self._document_tabs:
                    self._select_tab(self._document_tabs.index(keep_tab))
                return
            self._close_tab(index)
            closed += 1
        if keep_tab in self._document_tabs:
            self._select_tab(self._document_tabs.index(keep_tab))
        self._set_status(f"Closed {closed} other tab(s)")

    def _close_tabs_to_right(self, anchor_index: int) -> None:
        if anchor_index < 0 or anchor_index >= len(self._document_tabs):
            return
        anchor_tab = self._document_tabs[anchor_index]
        closed = 0
        for index in range(len(self._document_tabs) - 1, anchor_index, -1):
            self._select_tab(index)
            if not self._prompt_to_save_active_document("closing"):
                self._set_status("Close tabs to the right cancelled")
                if anchor_tab in self._document_tabs:
                    self._select_tab(self._document_tabs.index(anchor_tab))
                return
            self._close_tab(index)
            closed += 1
        if anchor_tab in self._document_tabs:
            self._select_tab(self._document_tabs.index(anchor_tab))
        self._set_status(f"Closed {closed} tab(s) to the right")

    def _reveal_in_explorer(self, path: Path) -> None:
        import subprocess

        try:
            if not path.exists():
                self._set_status(f"Path no longer exists: {path}")
                return
            if path.is_dir():
                subprocess.Popen(["explorer", str(path)])  # noqa: S603,S607
                self._set_status(f"Opened {path.name} folder in Explorer")
                return
            # /select, highlights the file in Windows Explorer.
            subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603,S607
            self._set_status(f"Revealing {path.name} in Explorer")
        except OSError as error:
            self._set_status(f"Could not open Explorer: {error}")

    def open_logs_folder(self) -> None:
        logs_path = app_data_dir() / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        self._reveal_in_explorer(logs_path)

    def open_diagnostics_folder(self) -> None:
        diagnostics_path = app_data_dir() / "diagnostics"
        diagnostics_path.mkdir(parents=True, exist_ok=True)
        self._reveal_in_explorer(diagnostics_path)

    def _apply_editor_text(self, text: str, status: str) -> None:
        if text == self.editor.GetValue():
            self._set_status(status)
            return
        self.editor.ChangeValue(text)
        self.document.set_text(text)
        if not self._suspend_persistent_undo:
            self._record_persistent_undo_state(text)
        self._maybe_autosave()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._refresh_sessions_menu()
        self._set_status(status)

    def _popup_context_menu(self, widget: object, menu: object, event: object) -> None:
        wx = self._wx
        position = event.GetPosition()
        if isinstance(position, tuple):
            point = wx.Point(position[0], position[1])
        else:
            point = position
        if point == wx.DefaultPosition or (point.x == -1 and point.y == -1):
            widget.PopupMenu(menu)
        else:
            widget.PopupMenu(menu, widget.ScreenToClient(point))

    def _on_close(self, event: object) -> None:
        if self.settings.tray_enabled and not self._is_exiting:
            self._ensure_tray_icon()
            self.frame.Hide()
            self._set_status("Quill is running in the system tray")
            event.Veto()
            return
        if not self._can_close_all_documents():
            event.Veto()
            return
        self._watch_folder.stop()
        self._unregister_global_hotkeys()
        self._remove_tray_icon()
        save_settings(self.settings)
        self.flush_persistent_undo()
        mark_clean_exit(self.session_id)
        event.Skip()

    def _on_iconize(self, event: object) -> None:
        if self.settings.tray_enabled and event.IsIconized():
            self._ensure_tray_icon()
            self.frame.Hide()
            self._set_status("Minimized to system tray")
        event.Skip()

    def _on_toggle_tray_mode(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.tray_enabled = enabled
        if enabled:
            self._ensure_tray_icon()
            self._set_status("System tray mode enabled")
            return
        self._remove_tray_icon()
        self._set_status("System tray mode disabled")

    def _on_toggle_soft_wrap(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_soft_wrap(enabled)

    def _on_toggle_auto_side_preview(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.auto_side_preview = enabled
        save_settings(self.settings)
        if enabled:
            tab = self._active_tab()
            if tab is not None:
                self._maybe_auto_side_preview(tab)
            self._set_status("Auto side-by-side preview on")
        else:
            self._set_status("Auto side-by-side preview off")

    def _on_toggle_tab_control(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_tab_control(enabled)

    def _on_toggle_find_wrap(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_find_wrap(enabled)

    def _on_toggle_title_full_path(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.title_bar_path_mode = "full_path" if enabled else "name"
        save_settings(self.settings)
        self._refresh_title()
        self._set_status("Title bar shows full path" if enabled else "Title bar shows file name")

    def _on_toggle_auto_check_updates(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.auto_check_updates = enabled
        save_settings(self.settings)
        self._set_status(
            "Check for updates on startup on" if enabled else "Check for updates on startup off"
        )

    def _on_toggle_dark_mode(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_dark_mode(enabled)

    def _on_toggle_persistent_undo(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_persistent_undo(enabled)

    def _on_toggle_spellcheck_as_you_type(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_spellcheck_as_you_type(enabled)

    def _on_toggle_intellisense_as_you_type(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_intellisense_as_you_type(enabled)

    def _on_toggle_start_with_no_document_open(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.start_with_no_document_open = enabled
        save_settings(self.settings)
        self._set_status(
            "Start with no document open on" if enabled else "Start with no document open off"
        )

    def _on_toggle_extend_selection_mode(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_extend_selection_mode(enabled)

    def _offer_crash_recovery(self) -> None:
        if not self._recovery_offers:
            return
        wx = self._wx
        offer = self._recovery_offers[0]
        logs_path = app_data_dir() / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        dialog = wx.Dialog(self.frame, title="Crash Recovery", size=(780, 360))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Quill detected an unclean exit. Restore the latest autosave snapshot, "
                    "open the logs folder, or save diagnostics before continuing."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        root.Add(wx.StaticText(panel, label="Logs folder"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        logs_field = wx.TextCtrl(panel, style=wx.TE_READONLY)
        logs_field.SetValue(str(logs_path))
        root.Add(logs_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        restore_button = wx.Button(panel, id=wx.ID_YES, label="Restore Latest Snapshot")
        open_logs_button = wx.Button(panel, label="Open Logs Folder")
        save_diagnostics_button = wx.Button(panel, label="Save Diagnostics...")
        skip_button = wx.Button(panel, id=wx.ID_NO, label="Skip Recovery")
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(restore_button, 0, wx.RIGHT, 6)
        buttons.Add(open_logs_button, 0, wx.RIGHT, 6)
        buttons.Add(save_diagnostics_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(skip_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)

        restore_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_YES))
        open_logs_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_APPLY))
        save_diagnostics_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_SAVE))
        skip_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_NO))
        dialog.SetDefaultItem(restore_button)
        dialog.SetEscapeId(wx.ID_NO)
        restore_button.SetFocus()

        while True:
            result = self._show_modal_dialog(dialog, "Crash Recovery")
            if result == wx.ID_APPLY:
                self.open_logs_folder()
                continue
            if result == wx.ID_SAVE:
                self.save_diagnostics_bundle()
                continue
            if result != wx.ID_YES:
                mark_recovery_offer_dismissed(offer)
                record_diagnostic_event(
                    "recovery",
                    "offer-dismissed",
                    detail=f"session={offer.session_id}; snapshot={offer.snapshot}",
                )
                self._set_status("Skipped crash recovery")
                self._record_notification("Crash recovery offer dismissed", "recovery")
                return
            try:
                recovered_text = read_recovery_snapshot(offer.snapshot)
            except OSError as error:
                record_diagnostic_event(
                    "recovery",
                    "snapshot-read-failed",
                    detail=f"session={offer.session_id}; snapshot={offer.snapshot}; error={error}",
                )
                self._show_message_box(
                    f"Could not restore snapshot: {error}",
                    "Crash Recovery",
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Crash recovery failed")
                return
            self._create_document_tab(
                Document(text=recovered_text, path=None, modified=True),
                select=True,
            )
            mark_recovery_offer_recovered(offer)
            record_diagnostic_event(
                "recovery",
                "snapshot-recovered",
                detail=f"session={offer.session_id}; snapshot={offer.snapshot}",
            )
            self._location_ring = LocationRing()
            self._location_ring.record(0)
            self._refresh_title()
            self._set_status("Recovered latest autosave snapshot")
            self._record_notification("Recovered autosave snapshot", "recovery")
            return

    def _apply_theme(self, theme: str) -> None:
        wx = self._wx
        if theme == "dark":
            foreground = wx.Colour(230, 230, 230)
            background = wx.Colour(30, 30, 30)
            chrome_background = wx.Colour(45, 45, 45)
        elif theme == "system" and is_high_contrast_enabled():
            foreground = wx.Colour(0, 0, 0)
            background = wx.Colour(255, 255, 255)
            chrome_background = wx.Colour(255, 212, 0)
        else:
            foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            chrome_background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
        self.editor.SetForegroundColour(foreground)
        self.editor.SetBackgroundColour(background)
        self.frame.SetForegroundColour(foreground)
        self.frame.SetBackgroundColour(chrome_background)
        self.statusbar.SetForegroundColour(foreground)
        self.statusbar.SetBackgroundColour(chrome_background)
        self.editor.Refresh()
        self.frame.Refresh()

    def _binding_for(self, command_id: str) -> str | None:
        binding = self.keymap.get(command_id)
        if binding is None:
            return DEFAULT_KEYMAP.get(command_id)
        cleaned = binding.strip()
        if not cleaned:
            return None
        return cleaned

    def _menu_label(self, title: str, command_id: str) -> str:
        binding = self.commands.keybinding_for(command_id)
        label = title
        if binding is None:
            return label
        return f"{label}\t{binding}"

    def _refresh_recent_menu(self) -> None:
        while self._recent_menu.GetMenuItemCount() > 0:
            item = self._recent_menu.FindItemByPosition(0)
            if item is None:
                break
            self._recent_menu.DestroyItem(item)
        self._recent_menu_ids.clear()
        if not self.recent_files:
            item = self._recent_menu.Append(self._wx.ID_ANY, "(No recent files)")
            item.Enable(False)
            self._recent_menu.AppendSeparator()
            self._recent_menu.Append(self._id_clear_recent, "C&lear Recent Files")
            return
        for path in self.recent_files:
            menu_id = self._wx.NewIdRef()
            self._recent_menu.Append(menu_id, str(path))
            self._recent_menu_ids[int(menu_id)] = path
        self._recent_menu.AppendSeparator()
        self._recent_menu.Append(self._id_clear_recent, "C&lear Recent Files")

    def _refresh_sessions_menu(self) -> None:
        if not hasattr(self, "_sessions_menu") or not hasattr(self, "_wx"):
            return
        try:
            while self._sessions_menu.GetMenuItemCount() > 0:
                item = self._sessions_menu.FindItemByPosition(0)
                if item is None:
                    break
                self._sessions_menu.DestroyItem(item)
            while self._open_documents_menu.GetMenuItemCount() > 0:
                item = self._open_documents_menu.FindItemByPosition(0)
                if item is None:
                    break
                self._open_documents_menu.DestroyItem(item)
            while self._recent_sessions_menu.GetMenuItemCount() > 0:
                item = self._recent_sessions_menu.FindItemByPosition(0)
                if item is None:
                    break
                self._recent_sessions_menu.DestroyItem(item)
        except RuntimeError:
            return
        self._session_menu_ids.clear()
        self._recent_session_menu_ids.clear()
        self._sessions_menu.Append(
            self._id_save_session,
            self._menu_label("Save Workspace &Snapshot...", "file.save_session"),
        )
        self._sessions_menu.Append(
            self._id_open_session,
            self._menu_label("&Open Workspace Snapshot...", "file.open_session"),
        )
        self._sessions_menu.AppendSubMenu(
            self._recent_sessions_menu,
            "Recent Workspace &Snapshots",
        )
        self._sessions_menu.AppendSeparator()
        self._sessions_menu.AppendSubMenu(
            self._open_documents_menu,
            "Open &Documents in Current Workspace",
        )
        self._refresh_recent_sessions_menu()
        if not self._document_tabs:
            item = self._open_documents_menu.Append(
                self._wx.ID_ANY, "(No open documents in workspace)"
            )
            item.Enable(False)
            return
        for index, tab in enumerate(self._document_tabs):
            menu_id = self._wx.NewIdRef()
            label = tab.document.name
            if index == self._active_tab_index:
                label = f"{label} (active)"
            self._open_documents_menu.Append(menu_id, label)
            self._session_menu_ids[int(menu_id)] = index

    def _refresh_recent_sessions_menu(self) -> None:
        if not hasattr(self, "_recent_sessions_menu") or not hasattr(self, "_wx"):
            return
        while self._recent_sessions_menu.GetMenuItemCount() > 0:
            item = self._recent_sessions_menu.FindItemByPosition(0)
            if item is None:
                break
            self._recent_sessions_menu.DestroyItem(item)
        self._recent_session_menu_ids.clear()
        recent_sessions = load_recent_sessions()
        self._recent_sessions = recent_sessions
        if not recent_sessions:
            item = self._recent_sessions_menu.Append(
                self._wx.ID_ANY, "(No saved workspace snapshots)"
            )
            item.Enable(False)
            self._recent_sessions_menu.AppendSeparator()
            self._recent_sessions_menu.Append(
                self._id_clear_recent_sessions,
                "C&lear Recent Workspace Snapshots",
            )
            return
        for path in recent_sessions:
            payload = load_session(path)
            label = session_title(payload, path.stem)
            menu_id = self._wx.NewIdRef()
            self._recent_sessions_menu.Append(menu_id, label)
            self._recent_session_menu_ids[int(menu_id)] = path
        self._recent_sessions_menu.AppendSeparator()
        self._recent_sessions_menu.Append(
            self._id_clear_recent_sessions,
            "C&lear Recent Workspace Snapshots",
        )

    def _on_session_menu(self, event: object) -> None:
        menu_id = event.GetId()
        index = self._session_menu_ids.get(menu_id)
        if index is None:
            event.Skip()
            return
        self._select_tab(index)

    def _on_recent_session_menu(self, event: object) -> None:
        menu_id = event.GetId()
        if menu_id == int(self._id_clear_recent_sessions):
            clear_recent_sessions()
            self._recent_sessions = []
            self._refresh_sessions_menu()
            self._set_status("Cleared recent sessions")
            return
        path = self._recent_session_menu_ids.get(menu_id)
        if path is None:
            event.Skip()
            return
        self.open_session(path)

    def _clear_document_tabs(self) -> None:
        for index in range(len(self._document_tabs) - 1, -1, -1):
            self.notebook.DeletePage(index)
        self._document_tabs.clear()
        self._active_tab_index = -1

    def _open_documents_from_session(self, documents: list[Document], active_index: int) -> None:
        self._clear_document_tabs()
        for document in documents:
            self._create_document_tab(document, select=False)
        if not self._document_tabs:
            self._create_document_tab(Document(), select=True)
            self._location_ring = LocationRing()
            self._location_ring.record(0)
            self._refresh_sessions_menu()
            return
        active_index = max(0, min(active_index, len(self._document_tabs) - 1))
        self._select_tab(active_index)
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._refresh_sessions_menu()

    def save_session(self, path: Path | None = None) -> None:
        wx = self._wx
        default_name = (
            f"{self.document.name}.quill-session.json"
            if self.document.name
            else "quill-session.json"
        )
        target = path
        if target is None:
            wildcard = (
                "Quill session files (*.quill-session.json)|*.quill-session.json|"
                "JSON files (*.json)|*.json|All files (*.*)|*.*"
            )
            with wx.FileDialog(
                self.frame,
                "Save session",
                wildcard=wildcard,
                defaultFile=default_name,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as dialog:
                if self._show_modal_dialog(dialog, "Save Session") != wx.ID_OK:
                    self._set_status("Save session cancelled")
                    return
                target = Path(dialog.GetPath())
        if target is None:
            return
        session_title_text = target.name
        for suffix in (".quill-session.json", ".json"):
            if session_title_text.endswith(suffix):
                session_title_text = session_title_text[: -len(suffix)]
                break
        session_title_text = session_title_text.strip() or "Quill Session"
        payload = build_session_payload(
            title=session_title_text,
            active_index=self._current_tab_index(),
            documents=[tab.document for tab in self._document_tabs],
        )
        save_session_file(target, payload)
        self._recent_sessions = load_recent_sessions()
        self._refresh_sessions_menu()
        self._set_status(f"Saved workspace snapshot to {target.name}")

    def open_session(self, path: Path | None = None) -> None:
        wx = self._wx
        target = path
        if target is None:
            wildcard = (
                "Quill session files (*.quill-session.json)|*.quill-session.json|"
                "JSON files (*.json)|*.json|All files (*.*)|*.*"
            )
            with wx.FileDialog(
                self.frame,
                "Open session",
                wildcard=wildcard,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as dialog:
                if self._show_modal_dialog(dialog, "Open Session") != wx.ID_OK:
                    self._set_status("Open session cancelled")
                    return
                target = Path(dialog.GetPath())
        if target is None or not target.exists():
            self._set_status("Session file not found")
            return
        if not self._can_close_all_documents():
            self._set_status("Open session cancelled")
            return
        payload = load_session(target)
        documents = documents_from_session(payload)
        active_index = active_index_from_session(payload, len(documents))
        self._open_documents_from_session(documents, active_index)
        self._recent_sessions = add_recent_session(target, self.settings.recent_files_limit)
        self._refresh_sessions_menu()
        self._set_status(f"Opened workspace snapshot {target.name}")

    def _on_open_recent(self, event: object) -> None:
        menu_id = event.GetId()
        path = self._recent_menu_ids.get(menu_id)
        if menu_id == int(self._id_clear_recent):
            self.clear_recent_files()
            return
        if path is None:
            event.Skip()
            return
        self.open_file(path)

    def _refresh_title(self) -> None:
        modified_suffix = self._dirty_title_suffix()
        self.frame.SetTitle(f"{self._title_subject()}{modified_suffix} - Quill")
        if self._active_tab_index >= 0 and self._active_tab_index < self.notebook.GetPageCount():
            page_title = f"{self.document.name}{modified_suffix}"
            self._set_tab_page_text(self._active_tab_index, page_title)
        self._refresh_statusbar()

    def _title_subject(self) -> str:
        if getattr(self.settings, "title_bar_path_mode", "name") == "full_path":
            if self.document.path is not None:
                return str(self.document.path)
        return self.document.name

    def _dirty_title_suffix(self) -> str:
        if not self.document.modified:
            return ""
        style = getattr(self.settings, "dirty_title_style", "text")
        if style == "asterisk":
            return " *"
        if style == "asterisk_text":
            return " * [modified]"
        return " [modified]"

    def _current_markup_context(self) -> str:
        path = self.document.path
        if path is not None:
            suffix = path.suffix.lower()
            if suffix in {".md", ".markdown", ".mdown", ".mkd"}:
                return "markdown"
            if suffix in {".html", ".htm", ".xhtml"}:
                return "html"
        sample = self.editor.GetValue()[:4000]
        if re.search(
            r"<\s*(html|head|body|div|span|p|h[1-6]|section|article)\b", sample, re.IGNORECASE
        ):
            return "html"
        markdown_hits = 0
        if re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", sample):
            markdown_hits += 1
        if re.search(r"(?m)^\s{0,3}(-|\*|\+)\s+\S", sample):
            markdown_hits += 1
        if re.search(r"\[[^\]]+\]\([^)]+\)", sample):
            markdown_hits += 1
        if re.search(r"(?m)^```", sample):
            markdown_hits += 1
        if markdown_hits >= 2:
            return "markdown"
        return "plain"

    def _refresh_contextual_menu_items(self) -> None:
        get_menu_bar = getattr(self.frame, "GetMenuBar", None)
        if not callable(get_menu_bar):
            return
        menu_bar = get_menu_bar()
        if menu_bar is None:
            return
        context = self._current_markup_context()
        html_only = context == "html"
        markdown_ready = context in {"markdown", "plain"}
        active_surface = self._active_markup_surface()
        structured_markup_ready = active_surface in {"markdown", "html"}
        markdown_ids = tuple(
            item_id
            for item_id in (
                self._id_insert_markdown_tag,
                self._id_heading_1,
                self._id_heading_2,
                self._id_heading_3,
                self._id_heading_4,
                self._id_heading_5,
                self._id_heading_6,
                getattr(self, "_id_style_headings", None),
                self._id_insert_bullet_list,
                self._id_insert_numbered_list,
                self._id_insert_task_list,
                getattr(self, "_id_open_list_manager", None),
                self._id_insert_code_block,
                self._id_insert_footnote,
            )
            if item_id is not None
        )
        structured_markup_ids = (self._id_insert_table,)
        html_ids = (self._id_insert_html_tag,)
        for item_id in markdown_ids:
            menu_item = menu_bar.FindItemById(item_id)
            if menu_item is not None:
                menu_item.Enable(markdown_ready)
        for item_id in structured_markup_ids:
            menu_item = menu_bar.FindItemById(item_id)
            if menu_item is not None:
                menu_item.Enable(structured_markup_ready)
        for item_id in html_ids:
            menu_item = menu_bar.FindItemById(item_id)
            if menu_item is not None:
                menu_item.Enable(html_only)

    def _set_status(self, message: str) -> None:
        self._status_message = message
        self._refresh_statusbar()
        announce(message)

    def _set_status_quiet(self, message: str) -> None:
        """Update the status bar text WITHOUT speaking it. Used for per-keystroke
        states like "Modified" so the screen reader doesn't repeat it on every
        character (it already echoes what you type)."""
        self._status_message = message
        self._refresh_statusbar()

    def _feature_enabled(self, feature_id: str) -> bool:
        feature_manager = getattr(self, "features", None)
        if feature_manager is None:
            return True
        return feature_manager.is_enabled(feature_id)

    def _record_notification(self, message: str, category: str = "info") -> None:
        self._notifications = add_notification(message, category)

    def _announce(self, message: str) -> None:
        self._status_message = message
        self._refresh_statusbar()
        backend_error = self._announcement_engine.announce(message)
        if backend_error and backend_error != self._announcement_error_reported:
            self._announcement_error_reported = backend_error
            self._record_notification(backend_error, "accessibility")

    def _statusbar_items(self) -> list[str]:
        allowed = set(STATUS_BAR_ITEMS)
        ordered = [item for item in self.settings.status_bar_order if item in allowed]
        hidden = {item for item in self.settings.status_bar_hidden if item in allowed}
        visible = [item for item in ordered if item not in hidden]
        if (
            getattr(self.settings, "title_bar_path_mode", "name") == "full_path"
            and "file_path" in visible
        ):
            visible = [item for item in visible if item != "file_path"]
        document = getattr(self, "document", None)
        if document is not None and document.path is not None:
            for item in ("encoding", "line_endings"):
                if item not in visible:
                    visible.append(item)
        last_find_query = getattr(self, "_last_find_query", "")
        if last_find_query and "search_term" not in visible:
            visible.append("search_term")
        notifications = getattr(self, "_notifications", [])
        if notifications and "notifications" not in visible:
            visible.append("notifications")
        read_aloud = getattr(self, "_read_aloud", None)
        read_aloud_state = getattr(read_aloud, "state", "idle")
        if read_aloud_state != "idle" and "read_aloud" not in visible:
            visible.append("read_aloud")
        if read_aloud_state != "idle" and "background_tasks" not in visible:
            visible.append("background_tasks")
        if getattr(self.settings, "spellcheck_as_you_type", False) and "spell_check" not in visible:
            visible.append("spell_check")
        editor = getattr(self, "editor", None)
        if editor is None:
            return visible or ["message"]
        selection_start, selection_end = editor.GetSelection()
        if selection_end > selection_start and "selection" not in visible:
            visible.append("selection")
        if not visible:
            return ["message"]
        if "message" not in visible:
            visible.insert(0, "message")
        return visible

    def _statusbar_text_for_item(self, item: str) -> str:
        feature_id = self._STATUS_BAR_FEATURES.get(item)
        feature_manager = getattr(self, "features", None)
        if (
            feature_id is not None
            and feature_manager is not None
            and not feature_manager.is_enabled(feature_id)
        ):
            return "Unavailable in current profile"
        read_aloud = getattr(self, "_read_aloud", None)
        read_aloud_state = getattr(read_aloud, "state", "idle")
        notifications = getattr(self, "_notifications", [])
        autosave_interval = getattr(self, "_autosave_interval", timedelta(seconds=30))
        if item == "message":
            message = getattr(self, "_status_message", "Ready")
            if message == "Modified" and self._dirty_title_suffix():
                return "Ready"
            return message
        if item == "file_path":
            document = getattr(self, "document", None)
            if document is None or document.path is None:
                return "Unsaved"
            return document.path.name
        if item == "line_column":
            editor = getattr(self, "editor", None)
            document = getattr(self, "document", None)
            if editor is None or document is None:
                return ""
            line, column = line_column_for_position(
                editor.GetValue(),
                editor.GetInsertionPoint(),
            )
            return f"Ln {line}, Col {column}"
        if item == "word_count":
            editor = getattr(self, "editor", None)
            if editor is None:
                return ""
            stats = compute_document_stats(editor.GetValue())
            return f"{stats.words:,} words"
        if item == "mode":
            return "OVR" if getattr(self, "_overwrite_mode", False) else "INS"
        if item == "selection":
            editor = getattr(self, "editor", None)
            if editor is not None and hasattr(editor, "GetSelection"):
                start, end = editor.GetSelection()
                length = max(0, end - start)
                return f"Sel {length}"
            return "Sel 0"
        if item == "encoding":
            document = getattr(self, "document", None)
            return getattr(document, "encoding", "")
        if item == "line_endings":
            document = getattr(self, "document", None)
            if getattr(document, "line_ending", "\n") == "\r\n":
                return "CRLF"
            return "LF"
        if item == "spell_check":
            return "On" if getattr(self.settings, "spellcheck_as_you_type", False) else "Off"
        if item == "background_tasks":
            count = getattr(self, "_background_task_count", 0)
            if count > 0:
                return f"{count} active"
            if read_aloud_state == "speaking":
                return "Read aloud"
            if notifications:
                return "Notifications"
            return "Idle"
        if item == "notifications":
            count = len(notifications)
            if count == 0:
                return "No new messages"
            return f"{count} message(s)"
        if item == "read_aloud":
            if read_aloud_state == "paused":
                return "Paused"
            if read_aloud_state == "speaking":
                return "Speaking"
            return "Stopped"
        if item == "autosave":
            seconds = int(autosave_interval.total_seconds())
            if seconds <= 0:
                return "Autosave off"
            if seconds % 60 == 0:
                minutes = seconds // 60
                return f"Autosave: {minutes} min"
            return f"Autosave: {seconds} s"
        if item == "search_term":
            last_find_query = getattr(self, "_last_find_query", "")
            if last_find_query:
                return f'Find: "{last_find_query}"'
            return "No search term"
        return ""

    def _statusbar_button_label(self, item: str) -> str:
        label = self._STATUS_BAR_LABELS.get(item, item)
        value = self._statusbar_text_for_item(item)
        if item == "message":
            return value or label
        if value:
            return f"{label}: {value}"
        return label

    def _statusbar_help_text(self, item: str) -> str:
        feature_id = self._STATUS_BAR_FEATURES.get(item)
        feature_manager = getattr(self, "features", None)
        if (
            feature_id is not None
            and feature_manager is not None
            and not feature_manager.is_enabled(feature_id)
        ):
            return (
                f"{self._STATUS_BAR_LABELS.get(item, item)} is unavailable in the current profile"
            )
        labels = {
            "message": "Open notifications",
            "line_column": "Go to line",
            "word_count": "Show document statistics",
            "mode": "Toggle overwrite mode",
            "selection": "Show selection statistics",
            "encoding": "Choose document encoding",
            "line_endings": "Toggle line endings",
            "spell_check": "Open spell check dialog",
            "background_tasks": "Open notifications",
            "notifications": "Open notifications",
            "read_aloud": "Start or pause read aloud",
            "autosave": "Cycle autosave interval",
            "search_term": "Reopen Find",
            "file_path": "Open containing folder",
        }
        return labels.get(item, self._STATUS_BAR_LABELS.get(item, item))

    def _build_statusbar_cells(self) -> None:
        if not hasattr(self, "_wx") or not hasattr(self, "statusbar"):
            return
        wx = self._wx
        context_menu_event = getattr(wx, "EVT_CONTEXT_MENU", None)
        self._statusbar_sizer.Clear(delete_windows=True)
        self._statusbar_cells = []
        items = self._statusbar_items()
        if "message" not in items:
            items = ["message"] + items
        for item in items:
            button = wx.Button(
                self.statusbar,
                label=self._statusbar_button_label(item),
                style=wx.BU_EXACTFIT,
            )
            button.SetName(self._STATUS_BAR_LABELS.get(item, item))
            button.SetHelpText(self._statusbar_help_text(item))
            button.Bind(wx.EVT_BUTTON, lambda _e, cell=item: self._activate_statusbar_cell(cell))
            button.Bind(
                wx.EVT_KEY_DOWN, lambda event, cell=item: self._on_statusbar_key_down(event, cell)
            )
            button.Bind(
                wx.EVT_SET_FOCUS,
                lambda event, cell=item: self._on_statusbar_cell_focus(event, cell),
            )
            if context_menu_event is not None:
                button.Bind(
                    context_menu_event,
                    lambda event, cell=item: self._on_statusbar_cell_context_menu(event, cell),
                )
            self._statusbar_sizer.Add(
                button,
                1 if item == "message" else 0,
                wx.EXPAND | wx.ALL,
                2,
            )
            self._statusbar_cells.append(_StatusBarCell(item=item, button=button))
        self.statusbar.Layout()

    def _apply_statusbar_layout(self) -> None:
        if not hasattr(self, "_wx") or not hasattr(self, "statusbar"):
            self._refresh_legacy_statusbar()
            return
        self._build_statusbar_cells()
        if self._statusbar_cells:
            self._active_statusbar_cell_index = min(
                self._active_statusbar_cell_index,
                len(self._statusbar_cells) - 1,
            )
            self._refresh_statusbar()

    def _refresh_statusbar(self) -> None:
        if not hasattr(self, "_statusbar_cells") or not hasattr(self, "_wx"):
            self._refresh_legacy_statusbar()
            return
        if not self._statusbar_cells:
            self._build_statusbar_cells()
        for cell in self._statusbar_cells:
            item = cell.item
            cell.button.SetLabel(self._statusbar_button_label(item))
            cell.button.SetHelpText(self._statusbar_help_text(item))
            cell.button.SetName(self._STATUS_BAR_LABELS.get(item, item))
            try:
                cell.button.SetMinSize((-1, -1))
                if item != "message":
                    width = self._STATUS_BAR_WIDTHS.get(item, 120)
                    cell.button.SetMinSize((width, -1))
            except Exception:
                pass
        self.statusbar.Layout()

    def _refresh_legacy_statusbar(self) -> None:
        if not hasattr(self, "statusbar"):
            return
        items = self._statusbar_items()
        texts = [self._statusbar_text_for_item(item) for item in items]
        if hasattr(self.statusbar, "SetFieldsCount"):
            self.statusbar.SetFieldsCount(len(items))
        if hasattr(self.statusbar, "SetStatusWidths"):
            widths = [self._STATUS_BAR_WIDTHS.get(item, 120) for item in items]
            self.statusbar.SetStatusWidths(widths)
        if hasattr(self.statusbar, "SetStatusText"):
            for index, text in enumerate(texts):
                self.statusbar.SetStatusText(text, index)

    def _statusbar_cell_index(self, item: str) -> int:
        for index, cell in enumerate(self._statusbar_cells):
            if cell.item == item:
                return index
        return 0

    def _focus_statusbar_cell(self, index: int | None = None) -> None:
        if not self._statusbar_cells:
            return
        target_index = self._active_statusbar_cell_index if index is None else index
        target_index = max(0, min(target_index, len(self._statusbar_cells) - 1))
        self._active_statusbar_cell_index = target_index
        self._statusbar_cells[target_index].button.SetFocus()

    def _on_statusbar_cell_focus(self, event: object, item: str) -> None:
        index = self._statusbar_cell_index(item)
        self._active_statusbar_cell_index = index
        self._announce_statusbar_item(item)
        event.Skip()

    def _announce_statusbar_item(self, item: str) -> None:
        label = self._STATUS_BAR_LABELS.get(item, item)
        value = self._statusbar_text_for_item(item)
        if value:
            announce(f"Status bar, {label}, {value}")
        else:
            announce(f"Status bar, {label}")

    def _on_statusbar_key_down(self, event: object, item: str) -> None:
        wx = self._wx
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_LEFT:
            self._focus_statusbar_cell(self._statusbar_cell_index(item) - 1)
            return
        if key_code == wx.WXK_RIGHT:
            self._focus_statusbar_cell(self._statusbar_cell_index(item) + 1)
            return
        if key_code == wx.WXK_HOME:
            self._focus_statusbar_cell(0)
            return
        if key_code == wx.WXK_END:
            self._focus_statusbar_cell(len(self._statusbar_cells) - 1)
            return
        if key_code == wx.WXK_ESCAPE:
            self.editor.SetFocus()
            self._active_region_index = 0
            self._region_tracker.exit("Status Bar")
            self._region_tracker.enter("Editor")
            announce("Returned to editor")
            return
        if key_code == wx.WXK_TAB:
            step = -1 if event.ShiftDown() else 1
            self._focus_statusbar_cell(self._statusbar_cell_index(item) + step)
            return
        if key_code in {wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE}:
            self._activate_statusbar_cell(item)
            return
        event.Skip()

    def _activate_statusbar_cell(self, item: str) -> None:
        feature_id = self._STATUS_BAR_FEATURES.get(item)
        feature_manager = getattr(self, "features", None)
        if (
            feature_id is not None
            and feature_manager is not None
            and not feature_manager.is_enabled(feature_id)
        ):
            self._set_status(
                f"{self._STATUS_BAR_LABELS.get(item, item)} is unavailable in this profile"
            )
            return
        actions: dict[str, Callable[[], None]] = {
            "message": self.open_notifications,
            "line_column": self.go_to_line,
            "word_count": self.show_word_count,
            "mode": self.toggle_overwrite_mode,
            "selection": self.show_word_count,
            "encoding": self.choose_document_encoding,
            "line_endings": self.toggle_line_endings,
            "spell_check": self.open_spell_check_dialog,
            "background_tasks": self.open_notifications,
            "notifications": self.open_notifications,
            "read_aloud": self.toggle_read_aloud,
            "autosave": self.cycle_autosave_interval,
            "search_term": self.find_text,
            "file_path": self.open_containing_folder,
        }
        action = actions.get(item)
        if action is None:
            self._set_status(self._statusbar_text_for_item(item))
            return
        action()

    def _hide_statusbar_cell(self, item: str) -> None:
        if item == "message":
            self._set_status("Status Message cannot be hidden")
            return
        hidden = set(getattr(self.settings, "status_bar_hidden", []))
        hidden.add(item)
        ordered_hidden = [entry for entry in self.settings.status_bar_order if entry in hidden]
        self.settings.status_bar_hidden = ordered_hidden
        save_settings(self.settings)
        self._apply_statusbar_layout()
        label = self._STATUS_BAR_LABELS.get(item, item)
        self._set_status(f"Hid {label} from status bar")

    def _restore_default_statusbar_layout(self) -> None:
        defaults = Settings()
        self.settings.status_bar_order = list(defaults.status_bar_order)
        self.settings.status_bar_hidden = list(defaults.status_bar_hidden)

    def _on_statusbar_cell_context_menu(self, event: object, item: str) -> None:
        wx = self._wx
        menu = wx.Menu()
        activate_id = wx.NewIdRef()
        hide_id = wx.NewIdRef()
        settings_id = wx.NewIdRef()
        menu.Append(activate_id, "Activate")
        menu.Append(hide_id, "Hide this item")
        menu.Append(settings_id, "Status bar settings...")
        menu.Bind(wx.EVT_MENU, lambda _e: self._activate_statusbar_cell(item), id=activate_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self._hide_statusbar_cell(item), id=hide_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.open_status_bar_settings(), id=settings_id)
        if item == "message":
            hide_item = menu.FindItemById(hide_id)
            if hide_item is not None:
                hide_item.Enable(False)
        popup_target = None
        for cell in self._statusbar_cells:
            if cell.item == item:
                popup_target = cell.button
                break
        if popup_target is None:
            popup_target = self.statusbar
        self._popup_context_menu(popup_target, menu, event)

    def _show_modal_dialog(self, dialog: object, label: str) -> int:
        self._region_tracker.enter(label)
        announce(f"Entered {label} dialog")
        try:
            result = dialog.ShowModal()
        finally:
            announce(f"Exited {label} dialog")
            self._region_tracker.exit(label)
        return result

    def _show_message_box(self, message: str, caption: str, style: int) -> int:
        self._region_tracker.enter(caption)
        announce(f"Entered {caption} dialog")
        try:
            result = self._wx.MessageBox(message, caption, style)
        finally:
            announce(f"Exited {caption} dialog")
            self._region_tracker.exit(caption)
        return result

    def _prompt_untrusted_location(self, folder: Path) -> bool | None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Untrusted Location")
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(f"{folder} is not trusted yet. Open this file anyway?"),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        trust_folder = wx.CheckBox(panel, label="Trust this folder for future opens")
        root.Add(trust_folder, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        root.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)
        dialog.SetAffirmativeId(wx.ID_OK)
        dialog.SetEscapeId(wx.ID_CANCEL)
        if self._show_modal_dialog(dialog, "Untrusted Location") != wx.ID_OK:
            return None
        return trust_folder.GetValue()

    def _prompt_unsaved_changes_action(
        self,
        title: str,
        message: str,
        affirmative_label: str,
        negative_label: str,
    ) -> int:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title=title)
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(wx.StaticText(panel, label=message), 0, wx.ALL | wx.EXPAND, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        save_button = wx.Button(panel, id=wx.ID_YES, label=affirmative_label)
        save_button.SetDefault()
        discard_button = wx.Button(panel, id=wx.ID_NO, label=negative_label)
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")
        buttons.AddStretchSpacer(1)
        buttons.Add(save_button, 0, wx.RIGHT, 6)
        buttons.Add(discard_button, 0, wx.RIGHT, 6)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        panel.SetSizer(root)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        dialog.SetSizerAndFit(outer)
        if hasattr(dialog, "SetAffirmativeId"):
            dialog.SetAffirmativeId(wx.ID_YES)
        if hasattr(dialog, "SetEscapeId"):
            dialog.SetEscapeId(wx.ID_CANCEL)

        def _on_char_hook(event: object) -> None:
            key_code = event.GetKeyCode()
            if key_code == wx.WXK_ESCAPE:
                dialog.EndModal(wx.ID_CANCEL)
                return
            if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                dialog.EndModal(wx.ID_YES)
                return
            event.Skip()

        dialog.Bind(wx.EVT_CHAR_HOOK, _on_char_hook)
        try:
            return self._show_modal_dialog(dialog, title)
        finally:
            dialog.Destroy()

    def _confirm_discard_changes(self) -> bool:
        wx = self._wx
        result = self._prompt_unsaved_changes_action(
            "Unsaved changes",
            "You have unsaved changes. Reload and discard them?",
            "Reload",
            "Keep Editing",
        )
        return result == wx.ID_YES

    def _run_background_task(
        self,
        label: str,
        work: Callable[[Callable[[str, int, int], None]], object],
        on_success: Callable[[object], None],
        *,
        notify_on_success: bool = False,
        notify_on_error: bool = False,
        notification_category: str = "info",
    ) -> None:
        self._background_task_count = getattr(self, "_background_task_count", 0) + 1
        task_id = self._track_background_task_start(label)
        self._set_status(f"{label} started")

        def progress(message: str, current: int, total: int) -> None:
            self._wx.CallAfter(
                self._track_background_task_progress,
                task_id,
                message,
                current,
                total,
            )
            self._wx.CallAfter(self._set_status, f"{label}: {current}/{total} - {message}")

        def worker() -> None:
            try:
                result = work(progress)
            except Exception as error:  # surfaced to the user on the UI thread
                self._wx.CallAfter(
                    self._finish_background_task,
                    label,
                    error,
                    None,
                    on_success,
                    task_id,
                    notify_on_success,
                    notify_on_error,
                    notification_category,
                )
                return
            self._wx.CallAfter(
                self._finish_background_task,
                label,
                None,
                result,
                on_success,
                task_id,
                notify_on_success,
                notify_on_error,
                notification_category,
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_background_task(
        self,
        label: str,
        error: Exception | None,
        result: object,
        on_success: Callable[[object], None],
        task_id: int,
        notify_on_success: bool,
        notify_on_error: bool,
        notification_category: str,
    ) -> None:
        self._background_task_count = max(0, getattr(self, "_background_task_count", 1) - 1)
        if error is not None:
            self._track_background_task_finish(task_id, "failed", str(error))
            self._show_message_box(str(error), label, self._wx.ICON_ERROR | self._wx.OK)
            self._set_status(f"{label} failed")
            if notify_on_error:
                self._record_notification(f"{label} failed: {error}", notification_category)
            return
        self._track_background_task_finish(task_id, "completed", "Completed")
        on_success(result)
        if notify_on_success:
            self._record_notification(f"{label} completed", notification_category)

    def _track_background_task_start(self, label: str) -> int:
        self._background_task_sequence = int(getattr(self, "_background_task_sequence", 0)) + 1
        task_id = self._background_task_sequence
        tasks = getattr(self, "_background_tasks", [])
        tasks.append(
            {
                "id": task_id,
                "label": label,
                "status": "running",
                "progress": "Starting",
                "started_at": datetime.now(UTC).isoformat(),
                "finished_at": "",
            }
        )
        self._background_tasks = tasks[-100:]
        return task_id

    def _track_background_task_progress(
        self,
        task_id: int,
        message: str,
        current: int,
        total: int,
    ) -> None:
        tasks = getattr(self, "_background_tasks", [])
        for task in reversed(tasks):
            if int(task.get("id", -1)) != task_id:
                continue
            task["progress"] = f"{current}/{total} - {message}"
            break

    def _track_background_task_finish(self, task_id: int, status: str, detail: str) -> None:
        tasks = getattr(self, "_background_tasks", [])
        for task in reversed(tasks):
            if int(task.get("id", -1)) != task_id:
                continue
            task["status"] = status
            task["progress"] = detail
            task["finished_at"] = datetime.now(UTC).isoformat()
            break

    def _open_generated_tab(self, title: str, text: str) -> int:
        index = self._create_document_tab(
            Document(text=text, path=None, modified=False), select=True
        )
        self._document_tabs[index].editor.SetEditable(False)
        self._set_tab_page_text(index, title)
        return index

    def _current_tab_index(self) -> int:
        return self.notebook.GetSelection()

    def _find_tab_index(self, path: Path | None) -> int:
        if path is None:
            return -1
        resolved = path.resolve()
        for index, tab in enumerate(self._document_tabs):
            if tab.document.path is not None and tab.document.path.resolve() == resolved:
                return index
        return -1

    def _select_tab(self, index: int) -> None:
        if index < 0 or index >= len(self._document_tabs):
            return
        change_selection = getattr(self.notebook, "ChangeSelection", None)
        if callable(change_selection):
            change_selection(index)
        else:
            self.notebook.SetSelection(index)
        self._activate_tab(index)

    def _active_tab(self) -> _DocumentTab:
        index = self._current_tab_index()
        if index < 0:
            index = self._active_tab_index
        return self._document_tabs[index]

    def _close_tab(self, index: int) -> None:
        if index < 0 or index >= len(self._document_tabs):
            return
        self.notebook.DeletePage(index)
        del self._document_tabs[index]
        if not self._document_tabs:
            self._create_document_tab(Document(), select=True)
            self._refresh_sessions_menu()
            return
        next_index = min(index, len(self._document_tabs) - 1)
        self._select_tab(next_index)
        self._refresh_sessions_menu()

    def _prompt_to_save_active_document(self, action_label: str) -> bool:
        if not self.document.modified:
            return True
        wx = self._wx
        result = self._prompt_unsaved_changes_action(
            "Unsaved changes",
            f"You have unsaved changes. Save before {action_label}?",
            "Save",
            "Don't Save",
        )
        if result == wx.ID_CANCEL:
            return False
        if result == wx.ID_YES:
            self.save_file()
            return not self.document.modified
        return True

    def _can_close_all_documents(self) -> bool:
        for index in range(len(self._document_tabs) - 1, -1, -1):
            self._select_tab(index)
            if not self._prompt_to_save_active_document("closing"):
                return False
        return True

    def new_file(self) -> None:
        self._clear_empty_workspace_state()
        document = Document()
        self._create_document_tab(document, select=True)
        self._persistent_undo_history = [""]
        self._persistent_undo_index = 0
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._set_status("New document")

    def open_file(
        self,
        path: Path | None = None,
        record_recent: bool = True,
        refresh_existing: bool = False,
    ) -> None:
        self._clear_empty_workspace_state()
        wx = self._wx
        selected_path = path
        if selected_path is None:
            with wx.FileDialog(
                self.frame,
                "Open text file",
                wildcard=(
                    "Supported files (*.txt;*.md;*.html;*.htm;*.xhtml;*.json;*.yaml;*.yml;"
                    "*.toml;*.xml;*.csv;*.tsv;*.ipynb;*.sqlite;*.db;*.doc;*.docx;*.ppt;*.pptx;*.epub;*.pages;*.pdf;*.odt;*.rtf)|"
                    "*.txt;*.md;*.html;"
                    "*.htm;*.xhtml;*.json;*.yaml;*.yml;*.toml;*.xml;*.csv;*.tsv;"
                    "*.ipynb;*.sqlite;*.db;*.doc;*.docx;*.ppt;*.pptx;*.epub;*.pages;*.pdf;*.odt;*.rtf|All files (*.*)|*.*"
                ),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as dialog:
                if self._show_modal_dialog(dialog, "Open text file") != wx.ID_OK:
                    return
                selected_path = Path(dialog.GetPath())
        if selected_path is None:
            return
        existing_index = self._find_tab_index(selected_path)
        if existing_index >= 0 and not refresh_existing:
            self._select_tab(existing_index)
            if record_recent:
                self._record_recent(selected_path)
            self._set_status(f"Opened {selected_path.name}")
            return
        if not is_trusted_location(selected_path, self._trusted_locations):
            trust_folder = self._prompt_untrusted_location(selected_path.parent.resolve())
            if trust_folder is None:
                self._set_status("Open cancelled for untrusted location")
                return
            if trust_folder:
                self._trusted_locations.add(selected_path.parent.resolve())
                save_trusted_locations(self._trusted_locations)

        suffix = selected_path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            csv_mode = self._resolve_csv_open_mode(selected_path)
            if csv_mode == "grid":
                loaded = read_text_document(selected_path)
                loaded.source_metadata = {
                    "source_kind": suffix.lstrip("."),
                    "engine": "csv grid",
                    "quality_score": 100,
                    "csv_open_mode": "grid",
                }
            else:
                loaded = read_text_document(selected_path)
                loaded.source_metadata = {
                    "source_kind": suffix.lstrip("."),
                    "engine": "csv text",
                    "quality_score": 100,
                    "csv_open_mode": "text",
                }
        elif suffix in {".doc", ".docx"}:
            word_mode = self._resolve_word_open_mode(selected_path)
            from quill.io.structured import read_structured_document

            loaded = read_structured_document(selected_path)
            loaded.source_metadata["word_open_mode"] = word_mode
        elif suffix in {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".ipynb",
            ".sqlite",
            ".db",
            ".ppt",
            ".xlsx",
            ".xls",
            ".pptx",
            ".epub",
            ".pages",
            ".pdf",
            ".odt",
            ".rtf",
        }:
            from quill.io.structured import read_structured_document

            loaded = read_structured_document(selected_path)
        else:
            loaded = read_text_document(selected_path)
        if suffix == ".epub":
            from quill.core.epub import load_epub_book

            self._epub_book = load_epub_book(selected_path)
        else:
            self._epub_book = None
        if existing_index >= 0:
            tab = self._document_tabs[existing_index]
            tab.document = loaded
            tab.editor.ChangeValue(loaded.text)
            self._load_persistent_undo_state(selected_path, loaded.text)
            self._select_tab(existing_index)
        else:
            if loaded.source_metadata.get("csv_open_mode") == "grid":
                self._create_csv_document_tab(loaded, select=True)
            elif loaded.source_metadata.get("word_open_mode") == "structured":
                self._create_word_document_tab(loaded, select=True)
            else:
                self._create_document_tab(loaded, select=True)
            self._load_persistent_undo_state(selected_path, loaded.text)
            self._location_ring = LocationRing()
            self._location_ring.record(0)
        if record_recent:
            self._record_recent(selected_path)
        self._refresh_title()
        self._last_intake_report = build_intake_report(loaded)
        self._set_status(build_intake_summary(loaded))

    def _resolve_csv_open_mode(self, path: Path) -> str:
        if not self._experimental_structured_surfaces_enabled():
            return "text"
        mode = getattr(self.settings, "csv_open_mode", "prompt")
        if mode in {"grid", "text"}:
            return mode
        return self._prompt_csv_open_mode(path)

    def _resolve_word_open_mode(self, path: Path) -> str:
        if not self._experimental_structured_surfaces_enabled():
            return "text"
        mode = getattr(self.settings, "word_open_mode", "prompt")
        if mode in {"structured", "text"}:
            return mode
        return self._prompt_word_open_mode(path)

    def _experimental_structured_surfaces_enabled(self) -> bool:
        # Release safety default: keep structured Word and CSV grid surfaces in
        # the repository, but disable them unless explicitly enabled for
        # internal verification.
        raw = os.environ.get("QUILL_ENABLE_EXPERIMENTAL_SURFACES", "").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def _prompt_csv_open_mode(self, path: Path) -> str:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title=f"Open {path.name}")
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    f"{path.name} can open in the special CSV grid or in the normal text editor."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        grid_choice = wx.RadioButton(panel, label="Open in special CSV grid", style=wx.RB_GROUP)
        text_choice = wx.RadioButton(panel, label="Open in normal text editor")
        grid_choice.SetValue(True)
        root.Add(grid_choice, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(text_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        remember_choice = wx.CheckBox(panel, label="Remember this choice for CSV files")
        root.Add(remember_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        root.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)
        dialog.SetAffirmativeId(wx.ID_OK)
        dialog.SetEscapeId(wx.ID_CANCEL)
        if self._show_modal_dialog(dialog, "CSV Open Choice") != wx.ID_OK:
            return "text"
        mode = "grid" if grid_choice.GetValue() else "text"
        if remember_choice.GetValue():
            self.settings.csv_open_mode = mode
            save_settings(self.settings)
        return mode

    def _prompt_word_open_mode(self, path: Path) -> str:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title=f"Open {path.name}")
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    f"{path.name} can open in a structured Word view or in the normal text editor."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        structured_choice = wx.RadioButton(
            panel, label="Open in structured Word view", style=wx.RB_GROUP
        )
        text_choice = wx.RadioButton(panel, label="Open in normal text editor")
        structured_choice.SetValue(True)
        root.Add(structured_choice, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(text_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        remember_choice = wx.CheckBox(panel, label="Remember this choice for Word files")
        root.Add(remember_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        root.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)
        dialog.SetAffirmativeId(wx.ID_OK)
        dialog.SetEscapeId(wx.ID_CANCEL)
        if self._show_modal_dialog(dialog, "Word Open Choice") != wx.ID_OK:
            return "text"
        mode = "structured" if structured_choice.GetValue() else "text"
        if remember_choice.GetValue():
            self.settings.word_open_mode = mode
            save_settings(self.settings)
        return mode

    def _create_csv_document_tab(self, document: Document, select: bool = True) -> int:
        wx = self._wx
        surface = CsvGridSurface(wx, self.notebook, document, self._on_csv_surface_changed)
        panel = surface.panel
        self._bind_editor_events(surface)
        tab = _DocumentTab(panel=panel, editor=surface, document=document)
        self._document_tabs.append(tab)
        index = self.notebook.GetPageCount()
        self.notebook.AddPage(panel, document.name, select=select)
        if select:
            self._active_tab_index = index
            self.editor = surface
            self.document = document
            self._apply_statusbar_layout()
            self._refresh_title()
        self._refresh_sessions_menu()
        return index

    def _create_word_document_tab(self, document: Document, select: bool = True) -> int:
        wx = self._wx
        surface = WordDocumentSurface(wx, self.notebook, document, self._sync_editor_change)
        panel = surface.panel
        self._bind_editor_events(surface)
        tab = _DocumentTab(panel=panel, editor=surface, document=document)
        self._document_tabs.append(tab)
        index = self.notebook.GetPageCount()
        self.notebook.AddPage(panel, document.name, select=select)
        if select:
            self._active_tab_index = index
            self.editor = surface
            self.document = document
            self._apply_statusbar_layout()
            self._refresh_title()
        self._refresh_sessions_menu()
        return index

    def next_document(self) -> None:
        self._switch_document(reverse=False)

    def previous_document(self) -> None:
        self._switch_document(reverse=True)

    def close_current_document(self) -> None:
        if not self._prompt_to_save_active_document("Close"):
            self._set_status("Close cancelled")
            return
        closing_index = self._current_tab_index()
        self._close_tab(closing_index)
        self._set_status("Closed document")

    def _switch_document(self, reverse: bool) -> None:
        if len(self._document_tabs) < 2:
            self._set_status("No other open document to switch to")
            return
        current_index = self._current_tab_index()
        step = -1 if reverse else 1
        target_index = (current_index + step) % len(self._document_tabs)
        self._select_tab(target_index)
        self._set_status(f"Switched to {self.document.name}")

    def send_to_tray(self) -> None:
        self._ensure_tray_icon()
        self.settings.tray_enabled = True
        self.frame.Hide()
        self._set_status("Sent Quill to system tray")

    def toggle_soft_wrap(self, enabled: bool | None = None) -> None:
        next_state = (not self.settings.soft_wrap) if enabled is None else enabled
        self.settings.soft_wrap = next_state
        self._apply_soft_wrap(next_state)
        self._set_status("Soft wrap on" if next_state else "Soft wrap off")

    def toggle_tab_control(self, enabled: bool | None = None) -> None:
        next_state = (not self._tab_control_visible) if enabled is None else enabled
        self.settings.show_tab_control = next_state
        save_settings(self.settings)
        self._rebuild_tab_host(next_state)
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is not None:
            item = menu_bar.FindItemById(self._id_toggle_tab_control)
            if item is not None:
                item.Check(next_state)
        self._set_status("Tab control shown" if next_state else "Tab control hidden")

    def toggle_find_wrap(self, enabled: bool | None = None) -> None:
        next_state = (not self.settings.wrap_find) if enabled is None else enabled
        self.settings.wrap_find = next_state
        save_settings(self.settings)
        self._set_status("Find wrap on" if next_state else "Find wrap off")

    def set_dirty_title_style(self, style: str) -> None:
        if style not in {"text", "asterisk", "asterisk_text"}:
            return
        self.settings.dirty_title_style = style
        save_settings(self.settings)
        self._refresh_title()
        label = {
            "text": "Dirty title style: text",
            "asterisk": "Dirty title style: asterisk",
            "asterisk_text": "Dirty title style: asterisk plus text",
        }[style]
        self._set_status(label)

    def toggle_dark_mode(self, enabled: bool | None = None) -> None:
        current = self.settings.theme == "dark"
        next_state = (not current) if enabled is None else enabled
        self.settings.theme = "dark" if next_state else "system"
        self._apply_theme(self.settings.theme)
        self._set_status("Dark mode on" if next_state else "Dark mode off")

    def toggle_persistent_undo(self, enabled: bool | None = None) -> None:
        next_state = (not self.settings.persistent_undo) if enabled is None else enabled
        self.settings.persistent_undo = next_state
        if self.document.path is not None:
            self._load_persistent_undo_state(self.document.path, self.editor.GetValue())
        else:
            self._persistent_undo_history = [self.editor.GetValue()]
            self._persistent_undo_index = 0
        self._set_status("Persistent undo on" if next_state else "Persistent undo off")

    def toggle_spellcheck_as_you_type(self, enabled: bool | None = None) -> None:
        next_state = (not self.settings.spellcheck_as_you_type) if enabled is None else enabled
        self.settings.spellcheck_as_you_type = next_state
        self._set_status(
            "Spell check as you type on" if next_state else "Spell check as you type off"
        )

    def toggle_intellisense_as_you_type(self, enabled: bool | None = None) -> None:
        next_state = (
            not getattr(self.settings, "intellisense_as_you_type", False)
            if enabled is None
            else enabled
        )
        self.settings.intellisense_as_you_type = next_state
        if not next_state:
            self._hide_intellisense_popup()
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is not None:
            item = menu_bar.FindItemById(self._id_toggle_intellisense_as_you_type)
            if item is not None:
                item.Check(next_state)
        self._set_status(
            "Word prediction as you type on" if next_state else "Word prediction as you type off"
        )

    def toggle_extend_selection_mode(self, enabled: bool | None = None) -> None:
        next_state = (not self._extend_selection_mode) if enabled is None else enabled
        self._extend_selection_mode = next_state
        self._extend_selection_anchor = self.editor.GetInsertionPoint() if next_state else None
        self._set_status(
            "Extend selection mode on (F8)" if next_state else "Extend selection mode off"
        )

    def toggle_overwrite_mode(self, enabled: bool | None = None) -> None:
        next_state = (not self._overwrite_mode) if enabled is None else enabled
        self._overwrite_mode = next_state
        self._refresh_statusbar()
        self._set_status("Overwrite mode on" if next_state else "Insert mode on")

    def choose_document_encoding(self) -> None:
        wx = self._wx
        choices = ["utf-8", "utf-16", "cp1252", "latin-1"]
        current_index = (
            choices.index(self.document.encoding) if self.document.encoding in choices else 0
        )
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose document encoding:",
            "Encoding",
            choices,
        ) as dialog:
            dialog.SetSelection(current_index)
            if self._show_modal_dialog(dialog, "Encoding") != wx.ID_OK:
                self._set_status("Encoding selection cancelled")
                return
            selected = dialog.GetSelection()
        if selected < 0 or selected >= len(choices):
            return
        self.document.encoding = choices[selected]
        self._refresh_statusbar()
        self._set_status(f"Encoding set to {choices[selected]}")

    def toggle_line_endings(self) -> None:
        self.document.line_ending = "\n" if self.document.line_ending == "\r\n" else "\r\n"
        self._refresh_statusbar()
        self._set_status(
            "Line endings set to LF"
            if self.document.line_ending == "\n"
            else "Line endings set to CRLF"
        )

    def cycle_autosave_interval(self) -> None:
        choices = [
            timedelta(seconds=15),
            timedelta(seconds=30),
            timedelta(seconds=60),
            timedelta(minutes=5),
            timedelta(0),
        ]
        try:
            index = choices.index(self._autosave_interval)
        except ValueError:
            index = 1
        next_interval = choices[(index + 1) % len(choices)]
        self._autosave_interval = next_interval
        self._refresh_statusbar()
        if next_interval.total_seconds() == 0:
            self._set_status("Autosave off")
            return
        seconds = int(next_interval.total_seconds())
        if seconds >= 60 and seconds % 60 == 0:
            self._set_status(f"Autosave every {seconds // 60} min")
            return
        self._set_status(f"Autosave every {seconds} s")

    def open_containing_folder(self) -> None:
        if self.document.path is None:
            self.save_file_as()
            return
        os.startfile(str(self.document.path.parent))
        self._set_status(f"Opened folder for {self.document.name}")

    def undo(self) -> None:
        if self.settings.persistent_undo:
            self._step_persistent_undo(-1)
            return
        if hasattr(self.editor, "CanUndo") and self.editor.CanUndo():
            self.editor.Undo()
            self._set_status("Undo")
            return
        self._set_status("Nothing to undo")

    def redo(self) -> None:
        if self.settings.persistent_undo:
            self._step_persistent_undo(1)
            return
        if hasattr(self.editor, "CanRedo") and self.editor.CanRedo():
            self.editor.Redo()
            self._set_status("Redo")
            return
        self._set_status("Nothing to redo")

    def _apply_soft_wrap(self, enabled: bool) -> None:
        wx = self._wx
        style = self.editor.GetWindowStyleFlag()
        if enabled:
            style = style & ~wx.TE_DONTWRAP
        else:
            style = style | wx.TE_DONTWRAP
        self.editor.SetWindowStyleFlag(style)

    def _load_persistent_undo_state(self, path: Path, text: str) -> None:
        history = load_undo_history(path)
        if not history:
            history = [text]
        elif history[-1] != text:
            history.append(text)
        self._persistent_undo_history = history[-100:]
        self._persistent_undo_index = len(self._persistent_undo_history) - 1
        if self.settings.persistent_undo:
            save_undo_history(path, self._persistent_undo_history)

    def _record_persistent_undo_state(self, text: str) -> None:
        if not self.settings.persistent_undo or self.document.path is None:
            return
        if (
            self._persistent_undo_history
            and self._persistent_undo_history[self._persistent_undo_index] == text
        ):
            return
        if self._persistent_undo_index < len(self._persistent_undo_history) - 1:
            self._persistent_undo_history = self._persistent_undo_history[
                : self._persistent_undo_index + 1
            ]
        self._persistent_undo_history.append(text)
        self._persistent_undo_history = self._persistent_undo_history[-100:]
        self._persistent_undo_index = len(self._persistent_undo_history) - 1
        # Persisting the full history JSON on every keystroke is wasteful (and
        # can write many MB per second on large documents). Throttle disk
        # writes; flush_persistent_undo() forces a write on save/close.
        self._persistent_undo_dirty = True
        self._maybe_flush_persistent_undo()

    def _maybe_flush_persistent_undo(self, force: bool = False) -> None:
        if not getattr(self, "_persistent_undo_dirty", False):
            return
        if self.document.path is None:
            return
        now = datetime.now(UTC)
        last = getattr(self, "_last_persistent_undo_write_at", None)
        interval = timedelta(seconds=3)
        if not force and last is not None and now - last < interval:
            return
        save_undo_history(self.document.path, self._persistent_undo_history)
        self._last_persistent_undo_write_at = now
        self._persistent_undo_dirty = False

    def flush_persistent_undo(self) -> None:
        self._maybe_flush_persistent_undo(force=True)

    def _step_persistent_undo(self, direction: int) -> None:
        if not self._persistent_undo_history:
            self._set_status("Nothing to undo")
            return
        target = self._persistent_undo_index + direction
        if target < 0 or target >= len(self._persistent_undo_history):
            self._set_status("Nothing to redo" if direction > 0 else "Nothing to undo")
            return
        text = self._persistent_undo_history[target]
        self._persistent_undo_index = target
        self._suspend_persistent_undo = True
        try:
            self.editor.ChangeValue(text)
        finally:
            self._suspend_persistent_undo = False
        self.document.set_text(text)
        self._refresh_title()
        self._set_status("Redo" if direction > 0 else "Undo")

    def _restore_from_tray(self) -> None:
        self.frame.Show(True)
        self.frame.Iconize(False)
        self.frame.Raise()
        self.frame.RequestUserAttention()
        self._set_status("Restored from system tray")

    def _on_tray_right_click(self, _event: object) -> None:
        wx = self._wx
        if self._tray_icon is None:
            return
        menu = wx.Menu()
        show_id = wx.NewIdRef()
        sticky_id = wx.NewIdRef()
        new_sticky_id = wx.NewIdRef()
        exit_id = wx.NewIdRef()
        menu.Append(show_id, "Show Quill")
        menu.AppendSeparator()
        menu.Append(sticky_id, "Sticky Notes...")
        menu.Append(new_sticky_id, "New Sticky Note...")
        menu.AppendSeparator()
        menu.Append(exit_id, "Exit Quill")
        menu.Bind(wx.EVT_MENU, lambda _e: self._restore_from_tray(), id=show_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.manage_sticky_notes(), id=sticky_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self.create_sticky_note(), id=new_sticky_id)
        menu.Bind(wx.EVT_MENU, lambda _e: self._exit_from_tray(), id=exit_id)
        self._tray_icon.PopupMenu(menu)
        menu.Destroy()

    def _exit_from_tray(self) -> None:
        self._is_exiting = True
        self.frame.Close()

    def _ensure_tray_icon(self) -> None:
        wx = self._wx
        if self._tray_icon is not None:
            return
        taskbar_icon = wx.adv.TaskBarIcon()
        icon = wx.ArtProvider.GetIcon(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16))
        taskbar_icon.SetIcon(icon, "Quill")
        taskbar_icon.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, lambda _e: self._restore_from_tray())
        taskbar_icon.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self._on_tray_right_click)
        self._tray_icon = taskbar_icon

    def _remove_tray_icon(self) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.RemoveIcon()
        self._tray_icon.Destroy()
        self._tray_icon = None

    def save_file(self) -> None:
        if self.document.path is None:
            self.save_file_as()
            return
        if self.document.modified:
            backup_document(self.document)
        write_text_document(self.document)
        self._record_persistent_undo_state(self.document.text)
        self.flush_persistent_undo()
        self._refresh_title()
        self._set_status(f"Saved {self.document.name}")

    def save_all_files(self) -> None:
        for index in range(len(self._document_tabs)):
            self._select_tab(index)
            if self.document.modified:
                self.save_file()
                if self.document.modified:
                    self._set_status("Save all cancelled")
                    return
        self._set_status("Saved all documents")

    def reload_from_disk(self) -> None:
        if self.document.path is None:
            self._set_status("No file to reload")
            return
        if self.document.modified and not self._confirm_discard_changes():
            self._set_status("Reload cancelled")
            return
        self.open_file(self.document.path, record_recent=False, refresh_existing=True)
        self._set_status(f"Reloaded {self.document.name}")

    def restore_backup(self) -> None:
        wx = self._wx
        if self.document.path is None:
            self._set_status("Open a file before restoring a backup")
            return
        backups = list_backups(self.document.path)
        if not backups:
            self._set_status("No backups available")
            return
        choices = [backup.name for backup in backups]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a backup to restore:",
            "Restore Backup",
            choices=choices,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Restore Backup") != wx.ID_OK:
                return
            selection = dialog.GetSelection()
        backup_path = backups[selection]
        restored_text = backup_path.read_text(encoding=self.document.encoding)
        self.document.set_text(restored_text)
        self._replace_document_text(restored_text)
        self._refresh_title()
        self._set_status(f"Restored backup {backup_path.name}")

    def _build_text_printout(self, title: str, text: str) -> object:
        wx = self._wx

        class _TextPrintout(wx.Printout):
            def __init__(self, print_title: str, print_text: str) -> None:
                super().__init__(print_title)
                self._text = print_text

            def OnPrintPage(self, _page: int) -> bool:
                dc = self.GetDC()
                if dc is None:
                    return False
                dc.SetFont(
                    wx.Font(
                        10,
                        wx.FONTFAMILY_TELETYPE,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL,
                    )
                )
                width, height = dc.GetSize()
                margin = 50
                y = margin
                line_height = dc.GetTextExtent("A")[1] + 2
                for line in self._text.splitlines() or [""]:
                    dc.DrawText(line, margin, y)
                    y += line_height
                    if y > height - margin:
                        break
                return True

            def HasPage(self, page: int) -> bool:
                return page == 1

            def GetPageInfo(self) -> tuple[int, int, int, int]:
                return (1, 1, 1, 1)

        return _TextPrintout(title, text)

    def page_setup(self) -> None:
        wx = self._wx
        dialog = wx.PageSetupDialog(self.frame, self._page_setup_data)
        try:
            if dialog.ShowModal() != wx.ID_OK:
                self._set_status("Page setup cancelled")
                return
            self._page_setup_data = dialog.GetPageSetupData()
            self._print_data = self._page_setup_data.GetPrintData()
            self._set_status("Page setup updated")
        finally:
            dialog.Destroy()

    def print_document(self) -> None:
        wx = self._wx
        text = self.editor.GetValue()
        printout = self._build_text_printout(self.document.name, text)
        printer = wx.Printer(wx.PrintDialogData(self._print_data))
        try:
            success = bool(printer.Print(self.frame, printout, True))
        except Exception as error:
            printout.Destroy()
            self._show_message_box(f"Printing failed: {error}", "Print", wx.ICON_ERROR | wx.OK)
            return
        if not success:
            read_last_error = getattr(printer, "GetLastError", None)
            last_error = read_last_error() if callable(read_last_error) else None
            cancelled_code = getattr(wx, "PRINTER_CANCELLED", None)
            no_error_code = getattr(wx, "PRINTER_NO_ERROR", None)
            if last_error == cancelled_code or last_error in {None, no_error_code}:
                self._set_status("Printing cancelled")
                printout.Destroy()
                return
            self._show_message_box("Printing failed.", "Print", wx.ICON_ERROR | wx.OK)
            printout.Destroy()
            return
        self._print_data = printer.GetPrintDialogData().GetPrintData()
        printout.Destroy()
        self._set_status("Printed document")

    def save_file_as(self) -> None:
        wx = self._wx
        with wx.FileDialog(
            self.frame,
            "Save file as",
            wildcard=(
                "Text files (*.txt)|*.txt|Markdown files (*.md)|*.md|"
                "HTML files (*.html;*.htm;*.xhtml)|*.html;*.htm;*.xhtml|All files (*.*)|*.*"
            ),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Save file as") != wx.ID_OK:
                return
            target = Path(dialog.GetPath())

        self.document.set_text(self.editor.GetValue())
        if self.document.modified and self.document.path is not None:
            backup_document(self.document)
        write_text_document(self.document, target)
        self._load_persistent_undo_state(target, self.document.text)
        self._record_recent(target)
        self._refresh_title()
        self._set_status(f"Saved as {target.name}")

    def save_as_plain_text(self) -> None:
        wx = self._wx
        with wx.FileDialog(
            self.frame,
            "Save as plain text",
            wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Save as plain text") != wx.ID_OK:
                return
            target = Path(dialog.GetPath())

        plain_doc = Document(
            text=self.editor.GetValue(),
            path=target,
            modified=True,
            encoding="utf-8",
            line_ending="\n",
        )
        write_text_document(plain_doc, target)
        self._record_recent(target)
        self._set_status(f"Saved plain text to {target.name}")

    def clear_recent_files(self) -> None:
        clear_recent_files()
        self.recent_files = []
        self._refresh_recent_menu()
        self._set_status("Cleared recent files")

    def open_url(self) -> None:
        wx = self._wx
        # Defer urllib import to avoid pulling 90+ ms of HTTP/SSL machinery
        # into cold startup for users who never open from URL.
        from urllib.error import HTTPError, URLError
        from urllib.parse import urlparse
        from urllib.request import Request, urlopen

        with wx.TextEntryDialog(
            self.frame,
            "Enter URL (http or https):",
            "Open from URL",
            value="https://",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Open from URL") != wx.ID_OK:
                return
            raw_url = dialog.GetValue().strip()
        if not raw_url:
            self._set_status("Open from URL cancelled")
            return
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"}:
            self._show_message_box(
                "Only http and https URLs are supported.",
                "Open from URL",
                wx.ICON_ERROR | wx.OK,
            )
            return
        requested_host = parsed.netloc or raw_url
        resolved_url = raw_url
        content_length: int | None = None

        try:
            request = Request(raw_url, method="HEAD")
            with urlopen(request, timeout=10) as response:
                resolved_url = response.geturl()
                content_length_header = response.headers.get("Content-Length")
                if content_length_header and content_length_header.isdigit():
                    content_length = int(content_length_header)
        except HTTPError as error:
            if error.code != 405:
                self._show_message_box(
                    f"Could not open URL: HTTP {error.code} from {requested_host}.",
                    "Open from URL",
                    wx.ICON_ERROR | wx.OK,
                )
                return
        except URLError as error:
            self._show_message_box(
                f"Could not open URL: {error.reason}",
                "Open from URL",
                wx.ICON_ERROR | wx.OK,
            )
            return

        if is_cross_host_redirect(raw_url, resolved_url):
            target_host = host_for_url(resolved_url)
            result = self._show_message_box(
                f"URL redirects from {requested_host} to {target_host}. Continue?",
                "Open from URL",
                wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
            )
            if result != wx.YES:
                self._set_status("Open from URL cancelled")
                return

        size_text = format_content_length(content_length)
        download_host = host_for_url(resolved_url) or requested_host
        result = self._show_message_box(
            f"Download from {download_host} ({size_text})?",
            "Open from URL",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Open from URL cancelled")
            return
        try:
            with urlopen(resolved_url, timeout=15) as response:
                body = response.read()
                resolved_url = response.geturl()
        except HTTPError as error:
            self._show_message_box(
                f"Could not open URL: HTTP {error.code} from {requested_host}.",
                "Open from URL",
                wx.ICON_ERROR | wx.OK,
            )
            return
        except URLError as error:
            self._show_message_box(
                f"Could not open URL: {error.reason}",
                "Open from URL",
                wx.ICON_ERROR | wx.OK,
            )
            return
        text = body.decode("utf-8", errors="replace")
        self._create_document_tab(Document(text=text, path=None, modified=False), select=True)
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._set_status(f"Opened URL: {resolved_url}")

    def _record_recent(self, path: Path) -> None:
        self.recent_files = add_recent_file(path, self.settings.recent_files_limit)
        self._refresh_recent_menu()

    def _maybe_autosave(self) -> None:
        if self._autosave_interval.total_seconds() <= 0:
            return
        now = datetime.now(UTC)
        if (
            self._last_autosave_at is not None
            and now - self._last_autosave_at < self._autosave_interval
        ):
            return
        # Skip snapshots when nothing has changed since the last one. This
        # avoids spinning up identical 10 MB autosave files for a document
        # that the user is just navigating through.
        revision = getattr(self.document, "revision", 0)
        last_revision = getattr(self, "_last_autosave_revision", None)
        if last_revision == revision:
            self._last_autosave_at = now
            return
        autosave_document(self.document, self.session_id)
        self._last_autosave_at = now
        self._last_autosave_revision = revision

    def open_palette(self) -> None:
        dialog = CommandPaletteDialog(self.frame, self.commands, self.features)
        dialog.show_modal_and_run()

    def create_sticky_note(self) -> None:
        if self._safe_mode:
            self._set_status("Sticky notes are unavailable in safe mode")
            return
        editor = StickyNoteEditorDialog(self.frame)
        body = editor.show_modal_and_get_body()
        if body is None:
            self._set_status("Sticky note cancelled")
            return
        note = save_sticky_note(body)
        self._set_status(f"Saved sticky note: {note.title}")

    def manage_sticky_notes(self) -> None:
        if self._safe_mode:
            self._set_status("Sticky notes are unavailable in safe mode")
            return
        StickyNotesVaultDialog(self.frame).show_modal()
        self._set_status("Closed sticky notes vault")

    def open_preferences(self) -> None:
        wx = self._wx
        options: list[tuple[str, Callable[[], None]]] = [
            ("General", self.open_general_preferences),
            ("Profiles and Features", self.open_profiles_and_features_settings),
            ("Status Bar Layout", self.open_status_bar_settings),
            ("Keymap Editor", self.open_keymap_editor),
            ("AI Connection", self.open_ai_preferences),
            ("Watch Folder Automation", self.open_watch_folder_settings),
            ("Install Starter Snippet Packs", self.install_starter_snippet_packs),
        ]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a settings area:",
            "Preferences",
            choices=[label for label, _handler in options],
        ) as dialog:
            dialog.SetSelection(0)
            if self._show_modal_dialog(dialog, "Preferences") != wx.ID_OK:
                self._set_status("Preferences cancelled")
                return
            selected = dialog.GetSelection()
        if selected < 0 or selected >= len(options):
            self._set_status("Preferences cancelled")
            return
        _label, handler = options[selected]
        handler()

    def open_general_preferences(self) -> None:
        wx = self._wx
        with wx.Dialog(self.frame, title="General Preferences") as dialog:
            panel = wx.Panel(dialog)
            root = wx.BoxSizer(wx.VERTICAL)
            panel_sizer = wx.BoxSizer(wx.VERTICAL)

            def _add_choice_row(label: str, control) -> None:
                row = wx.BoxSizer(wx.HORIZONTAL)
                row.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
                row.AddSpacer(8)
                row.Add(control, 1, wx.EXPAND)
                panel_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 8)

            theme_choice = wx.Choice(panel, choices=["System", "Light", "Dark"])
            theme_choice.SetStringSelection(self.settings.theme.capitalize())
            _add_choice_row("Theme", theme_choice)

            title_path_choice = wx.Choice(panel, choices=["File name only", "Full path"])
            title_path_choice.SetSelection(
                1 if getattr(self.settings, "title_bar_path_mode", "name") == "full_path" else 0
            )
            _add_choice_row("Title bar path", title_path_choice)

            dirty_style_choice = wx.Choice(panel, choices=["Text", "Asterisk", "Asterisk + text"])
            dirty_style_choice.SetSelection(
                {"text": 0, "asterisk": 1, "asterisk_text": 2}.get(
                    self.settings.dirty_title_style,
                    0,
                )
            )
            _add_choice_row("Dirty title style", dirty_style_choice)

            tray_mode = wx.CheckBox(panel, label="Enable system tray mode")
            tray_mode.SetValue(self.settings.tray_enabled)
            panel_sizer.Add(tray_mode, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            soft_wrap = wx.CheckBox(panel, label="Enable soft wrap")
            soft_wrap.SetValue(self.settings.soft_wrap)
            panel_sizer.Add(soft_wrap, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            show_tabs = wx.CheckBox(panel, label="Show tab control")
            show_tabs.SetValue(self.settings.show_tab_control)
            panel_sizer.Add(show_tabs, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            wrap_find = wx.CheckBox(panel, label="Wrap find searches")
            wrap_find.SetValue(self.settings.wrap_find)
            panel_sizer.Add(wrap_find, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            auto_updates = wx.CheckBox(panel, label="Check for updates on startup")
            auto_updates.SetValue(self.settings.auto_check_updates)
            panel_sizer.Add(auto_updates, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            beta_updates = wx.CheckBox(
                panel, label="Get beta updates (note: these may be unstable)"
            )
            beta_updates.SetValue(getattr(self.settings, "beta_updates", False))
            beta_updates.SetName("Get beta updates, note these may be unstable")
            panel_sizer.Add(beta_updates, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            def _on_beta_toggle(event: object, _cb=beta_updates) -> None:
                # Require the HTML consent gate before turning beta on.
                if _cb.GetValue() and not self._confirm_beta_channel():
                    _cb.SetValue(False)

            beta_updates.Bind(wx.EVT_CHECKBOX, _on_beta_toggle)

            persistent_undo = wx.CheckBox(panel, label="Enable persistent undo")
            persistent_undo.SetValue(self.settings.persistent_undo)
            panel_sizer.Add(persistent_undo, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            spellcheck = wx.CheckBox(panel, label="Spell check as you type")
            spellcheck.SetValue(self.settings.spellcheck_as_you_type)
            panel_sizer.Add(spellcheck, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            intellisense = wx.CheckBox(panel, label="Word prediction and tag IntelliSense")
            intellisense.SetValue(getattr(self.settings, "intellisense_as_you_type", False))
            panel_sizer.Add(intellisense, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            assistant_enabled = wx.CheckBox(panel, label="Enable writing assistant")
            assistant_enabled.SetValue(getattr(self.settings, "assistant_enabled", False))
            panel_sizer.Add(assistant_enabled, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            assistant_style = wx.Choice(
                panel,
                choices=["Balanced", "Concise", "Gentle", "Technical"],
            )
            assistant_style.SetSelection(
                {
                    "balanced": 0,
                    "concise": 1,
                    "gentle": 2,
                    "technical": 3,
                }.get(getattr(self.settings, "assistant_prompt_style", "balanced"), 0)
            )
            _add_choice_row("Assistant prompt style", assistant_style)

            browser_choice = wx.Choice(
                panel,
                choices=[option.label for option in available_browser_options()],
            )
            browser_choice.SetStringSelection(
                browser_choice_label_for_value(getattr(self.settings, "preview_browser", "system"))
            )
            _add_choice_row("Preview browser", browser_choice)

            snippet_expansion = wx.CheckBox(
                panel,
                label="Expand snippet triggers while typing",
            )
            snippet_expansion.SetValue(self.settings.snippet_trigger_expansion)
            panel_sizer.Add(snippet_expansion, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            start_empty = wx.CheckBox(panel, label="Start with no document open")
            start_empty.SetValue(self.settings.start_with_no_document_open)
            panel_sizer.Add(start_empty, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
            panel.SetSizer(panel_sizer)
            root.Add(panel, 1, wx.EXPAND | wx.ALL, 8)
            if buttons is not None:
                root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
            dialog.SetSizerAndFit(root)

            if self._show_modal_dialog(dialog, "General Preferences") != wx.ID_OK:
                self._set_status("Preferences cancelled")
                return

            values: dict[str, object] = {
                "theme": (theme_choice.GetStringSelection() or "System").lower(),
                "tray_enabled": bool(tray_mode.GetValue()),
                "soft_wrap": bool(soft_wrap.GetValue()),
                "show_tab_control": bool(show_tabs.GetValue()),
                "wrap_find": bool(wrap_find.GetValue()),
                "title_bar_path_mode": (
                    "full_path" if title_path_choice.GetSelection() == 1 else "name"
                ),
                "auto_check_updates": bool(auto_updates.GetValue()),
                "beta_updates": bool(beta_updates.GetValue()),
                "persistent_undo": bool(persistent_undo.GetValue()),
                "spellcheck_as_you_type": bool(spellcheck.GetValue()),
                "intellisense_as_you_type": bool(intellisense.GetValue()),
                "assistant_enabled": bool(assistant_enabled.GetValue()),
                "assistant_prompt_style": {
                    0: "balanced",
                    1: "concise",
                    2: "gentle",
                    3: "technical",
                }.get(assistant_style.GetSelection(), "balanced"),
                "preview_browser": browser_choice_value_for_label(
                    browser_choice.GetStringSelection() or "System default browser"
                ),
                "snippet_trigger_expansion": bool(snippet_expansion.GetValue()),
                "start_with_no_document_open": bool(start_empty.GetValue()),
                "dirty_title_style": {
                    0: "text",
                    1: "asterisk",
                    2: "asterisk_text",
                }.get(dirty_style_choice.GetSelection(), "text"),
            }
        theme = str(values.get("theme", self.settings.theme))
        self.set_theme(theme)
        self.settings.tray_enabled = bool(values.get("tray_enabled", self.settings.tray_enabled))
        self.settings.soft_wrap = bool(values.get("soft_wrap", self.settings.soft_wrap))
        self.settings.show_tab_control = bool(
            values.get("show_tab_control", self.settings.show_tab_control)
        )
        self.settings.wrap_find = bool(values.get("wrap_find", self.settings.wrap_find))
        self.settings.title_bar_path_mode = str(
            values.get("title_bar_path_mode", self.settings.title_bar_path_mode)
        )
        self.settings.auto_check_updates = bool(
            values.get("auto_check_updates", self.settings.auto_check_updates)
        )
        self.settings.beta_updates = bool(values.get("beta_updates", self.settings.beta_updates))
        self.settings.persistent_undo = bool(
            values.get("persistent_undo", self.settings.persistent_undo)
        )
        spellcheck_enabled = bool(
            values.get("spellcheck_as_you_type", self.settings.spellcheck_as_you_type)
        )
        self._set_spellcheck_mode(spellcheck_enabled)
        self.settings.intellisense_as_you_type = bool(
            values.get(
                "intellisense_as_you_type",
                getattr(self.settings, "intellisense_as_you_type", False),
            )
        )
        self.settings.assistant_enabled = bool(
            values.get("assistant_enabled", getattr(self.settings, "assistant_enabled", False))
        )
        self.settings.assistant_prompt_style = str(
            values.get(
                "assistant_prompt_style",
                getattr(self.settings, "assistant_prompt_style", "balanced"),
            )
        )
        self.settings.preview_browser = normalize_browser_choice(
            str(values.get("preview_browser", self.settings.preview_browser))
        )
        self.settings.snippet_trigger_expansion = bool(
            values.get("snippet_trigger_expansion", self.settings.snippet_trigger_expansion)
        )
        self._clear_navigation_issue_state()
        self.settings.start_with_no_document_open = bool(
            values.get(
                "start_with_no_document_open",
                self.settings.start_with_no_document_open,
            )
        )
        self.settings.dirty_title_style = str(
            values.get("dirty_title_style", self.settings.dirty_title_style)
        )
        save_settings(self.settings)
        self._apply_soft_wrap_setting()
        self._rebuild_tab_host(self.settings.show_tab_control)
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is not None:
            item = menu_bar.FindItemById(self._id_toggle_tab_control)
            if item is not None:
                item.Check(self.settings.show_tab_control)
            intellisense_item = menu_bar.FindItemById(self._id_toggle_intellisense_as_you_type)
            if intellisense_item is not None:
                intellisense_item.Check(getattr(self.settings, "intellisense_as_you_type", False))
        self._apply_dirty_title_style_setting()
        self._refresh_title()
        self._refresh_view_menu_checks()
        self._set_status("Updated general preferences")

    def open_ai_preferences(self) -> None:
        dialog = AssistantConnectionDialog(self.frame)
        if dialog.show_modal():
            self._set_ai_menu_status_badge(
                dialog.last_verification_ok,
                dialog.last_verification_message,
            )
            detail = self._compact_ai_status_detail(
                self._plain_language_ai_status_detail(dialog.last_verification_message)
            )
            if dialog.last_verification_ok:
                self._set_status(f"Updated AI connection settings. Ready. {detail}")
            else:
                self._set_status(f"Updated AI connection settings. Needs attention. {detail}")
        else:
            self._set_status("AI connection settings cancelled")

    def _set_ai_menu_status_badge(
        self, ready: bool | None, detail: str, badge: str | None = None
    ) -> None:
        if badge is not None:
            label = f"AI Status: {badge}"
        elif ready is True:
            label = "AI Status: Ready"
        elif ready is False:
            label = "AI Status: Needs attention"
        else:
            label = "AI Status: Not checked"

        menu_bar = self.frame.GetMenuBar()
        if menu_bar is None:
            return
        item = menu_bar.FindItemById(self._id_ai_status_badge)
        if item is not None:
            item.SetItemLabel(label)
            item.SetHelp(detail)
        detail_item = menu_bar.FindItemById(self._id_ai_status_detail)
        if detail_item is not None:
            compact = self._compact_ai_status_detail(detail, max_length=72)
            detail_item.SetItemLabel(f"AI Detail: {compact}")
            detail_item.SetHelp(detail)

    def _compact_ai_status_detail(self, detail: str, *, max_length: int = 96) -> str:
        compact = " ".join((detail or "Not checked").split())
        if len(compact) <= max_length:
            return compact
        return compact[: max_length - 3].rstrip() + "..."

    def _plain_language_ai_status_detail(self, detail: str) -> str:
        text = (detail or "").strip()
        lowered = text.lower()
        if not text:
            return "AI connection has not been checked yet."
        if "authentication failed" in lowered or "401" in lowered or "403" in lowered:
            return "Authentication failed. Check your API key and try again."
        if "timed out" in lowered:
            return "Connection timed out. Check your internet or host URL and try again."
        if "could not reach" in lowered or "failed to reach" in lowered:
            return "Could not reach the AI endpoint. Check the host URL and network connection."
        if "no models" in lowered:
            return "Connected, but no models were returned by the endpoint."
        if "verified" in lowered:
            return "Connection verified successfully."
        return text

    def _apply_announcement_trace_setting(self) -> None:
        trace_enabled = bool(self.settings.announcement_trace_enabled)
        if trace_enabled:
            trace_path = app_data_dir() / "diagnostics" / "announcement-trace.log"
            set_transcript_path(trace_path)
            enable_transcript_capture(True)
            return
        enable_transcript_capture(False)
        set_transcript_path(None)

    def _announce_backend_state_on_startup(self) -> None:
        state = self._announcement_engine.state()
        if state.requested_backend == "prism" and state.active_backend != "prism":
            self._record_notification(
                "Prism backend requested but unavailable; using status bar announcements.",
                "accessibility",
            )

    def _sync_announcement_backend_menu_state(self) -> None:
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is None:
            return
        requested = self.settings.announcement_backend
        item = menu_bar.FindItemById(self._id_announcement_backend_auto)
        if item is not None:
            item.Check(requested == "auto")
        item = menu_bar.FindItemById(self._id_announcement_backend_prism)
        if item is not None:
            item.Check(requested == "prism")
        item = menu_bar.FindItemById(self._id_announcement_backend_status_only)
        if item is not None:
            item.Check(requested == "status_only")
        item = menu_bar.FindItemById(self._id_toggle_announcement_trace)
        if item is not None:
            item.Check(self.settings.announcement_trace_enabled)

    def set_announcement_backend(self, requested_backend: str) -> None:
        state = self._announcement_engine.configure(requested_backend)
        self._announcement_error_reported = ""
        self.settings.announcement_backend = state.requested_backend
        save_settings(self.settings)
        self._sync_announcement_backend_menu_state()
        if state.active_backend == "prism":
            self._set_status(f"Announcement backend set to Prism ({state.backend_name})")
            return
        if state.requested_backend == "prism":
            self._set_status("Prism unavailable. Using status bar announcements.")
            return
        self._set_status("Announcement backend set to status bar")

    def choose_announcement_backend(self) -> None:
        wx = self._wx
        backend_order = ["auto", "prism", "status_only"]
        choices = [self._ANNOUNCEMENT_BACKEND_LABELS[item] for item in backend_order]
        current = self.settings.announcement_backend
        current_index = backend_order.index(current) if current in backend_order else 0
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose how Quill routes spoken announcements:",
            "Announcement Backend",
            choices=choices,
        ) as dialog:
            dialog.SetSelection(current_index)
            if self._show_modal_dialog(dialog, "Announcement Backend") != wx.ID_OK:
                self._set_status("Announcement backend selection cancelled")
                return
            selected = dialog.GetSelection()
        if selected < 0 or selected >= len(backend_order):
            return
        self.set_announcement_backend(backend_order[selected])

    def toggle_announcement_trace_capture(self) -> None:
        self.settings.announcement_trace_enabled = not self.settings.announcement_trace_enabled
        save_settings(self.settings)
        self._apply_announcement_trace_setting()
        self._sync_announcement_backend_menu_state()
        if self.settings.announcement_trace_enabled:
            self._set_status("Announcement trace capture enabled")
            return
        self._set_status("Announcement trace capture disabled")

    def _set_keyboard_pack(self, pack_name: str) -> None:
        self.settings.keyboard_pack = pack_name
        save_settings(self.settings)

    def _mark_keyboard_pack_custom(self) -> None:
        if self.settings.keyboard_pack == KEYBOARD_PACK_CUSTOM:
            return
        self._set_keyboard_pack(KEYBOARD_PACK_CUSTOM)

    def apply_keyboard_pack(self, pack_name: str) -> None:
        if pack_name == KEYBOARD_PACK_CUSTOM:
            self._set_status("Custom layouts are created from manual keymap edits")
            return
        self.keymap = build_keymap_for_pack(pack_name)
        save_keymap(self.keymap)
        self._set_keyboard_pack(pack_name)
        self._reload_shortcuts_from_keymap()
        self._set_status(f"Keyboard pack changed to {pack_name}")

    def export_keymap_file(self) -> None:
        wx = self._wx
        with wx.FileDialog(
            self.frame,
            "Export keymap",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Export keymap") != wx.ID_OK:
                return
            target = Path(dialog.GetPath())
        export_keymap(target, self.keymap)
        self._set_status(f"Exported keymap to {target.name}")

    def open_keymap_editor(self) -> None:
        wx = self._wx
        command_choices = [
            f"{command.title} ({command.id})"
            for command in self.commands.list()
            if not command.id.startswith("tools.keymap_editor")
        ]
        if not command_choices:
            self._set_status("No commands available for keymap editing")
            return
        command_ids: dict[str, str] = {
            choice: choice.rsplit("(", 1)[1].rstrip(")") for choice in command_choices
        }
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose command to rebind:",
            "Keymap Editor",
            choices=command_choices,
        ) as command_dialog:
            if self._show_modal_dialog(command_dialog, "Keymap Editor") != wx.ID_OK:
                return
            selected = command_dialog.GetStringSelection()
        command_id = command_ids[selected]
        current_binding = self._binding_for(command_id) or ""
        with wx.TextEntryDialog(
            self.frame,
            "Enter new keybinding (example: Ctrl+Shift+K):",
            "Keymap Editor",
            value=current_binding,
        ) as binding_dialog:
            if self._show_modal_dialog(binding_dialog, "Keymap Editor") != wx.ID_OK:
                return
            new_binding = binding_dialog.GetValue().strip()
        if not new_binding:
            self._show_message_box(
                "Keybinding cannot be blank.",
                "Keymap Editor",
                wx.ICON_ERROR | wx.OK,
            )
            return
        if self._parse_keybinding(new_binding) is None:
            self._show_message_box(
                "Keybinding format is invalid.",
                "Keymap Editor",
                wx.ICON_ERROR | wx.OK,
            )
            return
        conflict = find_keymap_conflict(self.keymap, command_id, new_binding)
        if conflict:
            self._show_message_box(
                f'Binding conflicts with "{conflict}". Choose a different keybinding.',
                "Keymap Editor",
                wx.ICON_WARNING | wx.OK,
            )
            self._set_status("Keymap edit cancelled")
            return
        self.keymap[command_id] = new_binding
        save_keymap(self.keymap)
        self._mark_keyboard_pack_custom()
        self._reload_shortcuts_from_keymap()
        self._set_status(f"Updated keybinding for {command_id}")

    def open_status_bar_settings(self) -> None:
        wx = self._wx
        item_order = list(self.settings.status_bar_order)
        hidden = set(self.settings.status_bar_hidden)
        dialog = wx.Dialog(self.frame, title="Status Bar Layout", size=(560, 420))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Choose visible status items and order. "
                    "Use Move Up/Down, or right-click for Move Left/Right and Hide/Show."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        chooser = wx.CheckListBox(
            panel,
            choices=[self._STATUS_BAR_LABELS.get(item, item) for item in item_order],
        )
        for index, item in enumerate(item_order):
            chooser.Check(index, item not in hidden)
        root.Add(chooser, 1, wx.ALL | wx.EXPAND, 8)
        controls = wx.BoxSizer(wx.HORIZONTAL)
        move_up = wx.Button(panel, label="Move Up")
        move_down = wx.Button(panel, label="Move Down")
        restore_defaults = wx.Button(panel, label="Restore Defaults")
        controls.Add(move_up, 0, wx.RIGHT, 8)
        controls.Add(move_down, 0, wx.RIGHT, 8)
        controls.Add(restore_defaults, 0, wx.RIGHT, 8)
        root.Add(controls, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        root.Add(dialog.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)
        restore_defaults_selected = False

        def swap_items(first: int, second: int) -> None:
            if first < 0 or second < 0:
                return
            if first >= len(item_order) or second >= len(item_order):
                return
            item_order[first], item_order[second] = item_order[second], item_order[first]
            first_checked = chooser.IsChecked(first)
            second_checked = chooser.IsChecked(second)
            first_label = self._STATUS_BAR_LABELS.get(item_order[first], item_order[first])
            second_label = self._STATUS_BAR_LABELS.get(item_order[second], item_order[second])
            chooser.SetString(first, first_label)
            chooser.SetString(second, second_label)
            chooser.Check(first, second_checked)
            chooser.Check(second, first_checked)
            chooser.SetSelection(second)

        def move_selected(offset: int) -> None:
            selected = chooser.GetSelection()
            if selected == wx.NOT_FOUND:
                return
            target = selected + offset
            if target < 0 or target >= len(item_order):
                return
            swap_items(selected, target)

        def on_move_up(_event: object) -> None:
            move_selected(-1)

        def on_move_down(_event: object) -> None:
            move_selected(1)

        def on_context_menu(event: object) -> None:
            selected = chooser.GetSelection()
            if selected == wx.NOT_FOUND:
                return
            menu = wx.Menu()
            move_left_id = wx.NewIdRef()
            move_right_id = wx.NewIdRef()
            toggle_id = wx.NewIdRef()
            menu.Append(move_left_id, "Move Left")
            menu.Append(move_right_id, "Move Right")
            menu.AppendSeparator()
            toggle_label = "Hide Item" if chooser.IsChecked(selected) else "Show Item"
            menu.Append(toggle_id, toggle_label)
            menu.Bind(wx.EVT_MENU, lambda _e: move_selected(-1), id=move_left_id)
            menu.Bind(wx.EVT_MENU, lambda _e: move_selected(1), id=move_right_id)
            menu.Bind(
                wx.EVT_MENU,
                lambda _e: chooser.Check(selected, not chooser.IsChecked(selected)),
                id=toggle_id,
            )
            self._popup_context_menu(chooser, menu, event)

        def on_restore_defaults(_event: object) -> None:
            nonlocal restore_defaults_selected
            restore_defaults_selected = True
            self._set_status("Status bar defaults selected")

        move_up.Bind(wx.EVT_BUTTON, on_move_up)
        move_down.Bind(wx.EVT_BUTTON, on_move_down)
        restore_defaults.Bind(wx.EVT_BUTTON, on_restore_defaults)
        chooser.Bind(wx.EVT_CONTEXT_MENU, on_context_menu)

        if self._show_modal_dialog(dialog, "Status Bar Layout") != wx.ID_OK:
            return
        if restore_defaults_selected:
            self._restore_default_statusbar_layout()
        else:
            self.settings.status_bar_order = list(item_order)
            self.settings.status_bar_hidden = [
                item for index, item in enumerate(item_order) if not chooser.IsChecked(index)
            ]
        save_settings(self.settings)
        self._apply_statusbar_layout()
        self._set_status("Status bar layout updated")

    def import_keymap_file(self) -> None:
        wx = self._wx
        with wx.FileDialog(
            self.frame,
            "Import keymap",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Import keymap") != wx.ID_OK:
                return
            source = Path(dialog.GetPath())
        self.keymap = import_keymap(source)
        self._mark_keyboard_pack_custom()
        self._reload_shortcuts_from_keymap()
        self._set_status(f"Imported keymap from {source.name}")

    def reset_keymap_defaults(self) -> None:
        wx = self._wx
        result = self._show_message_box(
            "Reset all keybindings to defaults?",
            "Reset Keymap",
            wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Reset keymap cancelled")
            return
        self.keymap = reset_keymap()
        self._set_keyboard_pack(KEYBOARD_PACK_DEFAULT)
        self._reload_shortcuts_from_keymap()
        self._set_status("Reset keymap to defaults")

    def _reload_shortcuts_from_keymap(self) -> None:
        self.commands = CommandRegistry()
        self._build_commands()
        self._refresh_voice_command_aliases()
        self._build_menu()
        self._apply_accelerators()
        self._reload_global_hotkeys()

    def open_welcome_guide(self) -> None:
        self._create_document_tab(
            Document(text=build_welcome_guide(self.features), path=None, modified=False),
            select=True,
        )
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._set_status("Opened welcome guide")

    def open_keyboard_reference(self) -> None:
        reference = build_keyboard_reference(self.commands.list(), self.features)
        self._create_document_tab(
            Document(text=reference, path=None, modified=False),
            select=True,
        )
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._set_status("Opened keyboard reference")

    def open_user_guide(self) -> None:
        """Open the bundled user guide as a new document tab.

        Searches a small set of candidate locations so the command works in
        the dev tree, an installed package, and a packaged Windows build.
        Falls back to the in-app welcome guide if the markdown file cannot
        be located on disk.
        """
        candidates = [
            Path(__file__).resolve().parent.parent.parent / "docs" / "userguide.md",
            Path(__file__).resolve().parent.parent / "docs" / "userguide.md",
            Path.cwd() / "docs" / "userguide.md",
        ]
        guide_path: Path | None = None
        for candidate in candidates:
            try:
                if candidate.is_file():
                    guide_path = candidate
                    break
            except OSError:
                continue
        if guide_path is None:
            self.open_welcome_guide()
            self._set_status("User guide file not found; opened welcome guide instead.")
            return
        try:
            text = guide_path.read_text(encoding="utf-8")
        except OSError as error:
            self._set_status(f"Could not read user guide: {error}")
            self.open_welcome_guide()
            return
        self._create_document_tab(
            Document(text=text, path=None, modified=False),
            select=True,
        )
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._set_status("Opened user guide")

    # Org links shown in the About dialog.
    _ABOUT_LINKS: tuple[tuple[str, str], ...] = (
        ("Community Access", "https://community-access.org"),
        ("Blind Information Technology Solutions (BITS)", "https://bits-acb.org"),
        ("Techopolis", "https://techopolis.app"),
        ("GLOW (Community Access)", "https://letitglow.app"),
    )

    # Contributor / project profiles on GitHub.
    _ABOUT_GITHUB_LINKS: tuple[tuple[str, str], ...] = (
        ("Community Access on GitHub", "https://github.com/Community-Access"),
        ("Taylor Arndt on GitHub", "https://github.com/taylorarndt"),
        ("Michael Doise on GitHub", "https://github.com/mikedoise"),
        ("Becky K on GitHub", "https://github.com/BeckyK102125"),
    )

    # Open-source projects Quill is built with (credited in About).
    _ABOUT_ACKNOWLEDGMENTS: str = (
        "Quill is built with these open-source projects, with gratitude:\n\n"
        "• wxPython / wxWidgets — application UI toolkit\n"
        "• Prism (prismatoid) — screen-reader speech bridge (Windows)\n"
        "• pyttsx3 — system text-to-speech\n"
        "• llama.cpp / llama-cpp-python — on-device AI (Windows and Linux)\n"
        "• pyenchant / Hunspell — spell checking\n"
        "• SpeechRecognition — dictation\n"
        "• keynote-parser and MarkItDown — document import\n"
        "• pyobjc and py2app — macOS integration and packaging\n"
        "• WordNet (Princeton University) — thesaurus data\n"
        "• words_alpha — English word list\n"
        "• DECtalk and Piper — bundled speech engines\n"
        "• eSpeak NG — phoneme generation used by Piper\n"
        "• Kokoro and VibeVoice — additional neural speech voices\n\n"
        "On macOS, on-device AI uses Apple Foundation Models.\n"
        "Each project is owned by its respective authors and used under its own license."
    )

    def _about_markdown(self) -> str:
        def md_links(links: tuple[tuple[str, str], ...]) -> str:
            return "\n".join(f"- [{name}]({url})" for name, url in links)

        # Reuse the acknowledgments text as a markdown list.
        acks = "\n".join(
            (f"- {line[2:]}" if line.startswith("• ") else line)
            for line in self._ABOUT_ACKNOWLEDGMENTS.splitlines()
        )
        return (
            f"# Quill 0.1 Beta\n\n"
            f"Version {__version__}\n\n"
            "Quill 0.1 Beta is a screen-reader-first writing and document environment "
            "for Windows and Mac from Blind Information Technology Solutions (BITS) "
            "and Community Access.\n\n"
            "With sincere thanks to our contributors and beta testers: "
            "Techopolis, Taylor Arndt, Michael Doise, Kayla Bentas, "
            "Shane Popplestone, and Becky K.\n\n"
            "## Links\n\n" + md_links(self._ABOUT_LINKS) + "\n\n"
            "## Contributors on GitHub\n\n" + md_links(self._ABOUT_GITHUB_LINKS) + "\n\n"
            "## Open-source acknowledgments\n\n" + acks + "\n\n"
            "Copyright (c) Blind Information Technology Solutions (BITS) and Community Access"
        )

    def show_about_quill(self) -> None:
        # Reuse the same WebView preview surface as the document preview/chat:
        # render the About content (with all links) and open links in the browser.
        from quill.core.browser_preview import render_preview_body
        from quill.ui.preview_dialog import MarkdownPreviewDialog

        body = render_preview_body(self._about_markdown(), "markdown")
        MarkdownPreviewDialog(self.frame, "About Quill", body, open_links_externally=True).show()
        self._set_status("Opened About Quill")

    def show_whisperer_about_page(self) -> None:
        index = self._open_generated_tab(
            "About BITS Whisperer",
            self._build_whisperer_about_html(),
        )
        self._select_tab(index)
        if 0 <= index < len(self._document_tabs):
            self._show_side_preview_for(self._document_tabs[index])
        self._set_status("Opened About BITS Whisperer")

    def _build_whisperer_about_html(self) -> str:
        roadmap_rows = [
            (
                "Provider and feature-flag gating",
                "Mature feature flag service and staged rollout controls",
                "Phase 1",
                "Introduce opt-in experiments and safe launch toggles in Quill.",
            ),
            (
                "Audio intake and watch-folder workflows",
                "Reliable automatic job intake and background transcription flow",
                "Phase 1",
                "Apply to document/audio intake and asynchronous assistant pipelines.",
            ),
            (
                "Rich export and transformation pipeline",
                "Multiple output formats and conversion strategy patterns",
                "Phase 2",
                "Expand Quill exports and structured conversion workflows.",
            ),
            (
                "Model/provider orchestration",
                "Multi-provider manager abstraction with graceful fallback",
                "Phase 2",
                "Align with Quill AI + speech backends for reliability and control.",
            ),
            (
                "Plugin and extension surfaces",
                "Extensible plugin architecture for advanced integrations",
                "Phase 3",
                "Open controlled extension points in Quill once core stability is proven.",
            ),
        ]
        roadmap_html = "".join(
            (
                "<tr>"
                f"<td>{html.escape(capability)}</td>"
                f"<td>{html.escape(from_bw)}</td>"
                f"<td>{html.escape(phase)}</td>"
                f"<td>{html.escape(notes)}</td>"
                "</tr>"
            )
            for capability, from_bw, phase, notes in roadmap_rows
        )

        principles_rows = [
            (
                "Accessibility first",
                "Screen-reader-first design with clear headings and keyboard flow.",
            ),
            ("Offline-friendly", "Strong local capabilities before cloud dependencies."),
            ("Safe rollout", "Feature flags and staged onboarding for predictable adoption."),
            ("Transparent status", "Status pages and notifications for every async operation."),
        ]
        principles_html = "".join(
            f"<tr><th scope='row'>{html.escape(name)}</th><td>{html.escape(detail)}</td></tr>"
            for name, detail in principles_rows
        )

        return (
            "<h1 id='whisperer-about'>BITS Whisperer and Quill</h1>"
            "<p>The future is bright. BITS Whisperer patterns are being evaluated for selective adoption "
            "inside Quill to improve accessibility, reliability, and creative flow.</p>"
            "<h2 id='what-is-coming'>What Is Coming</h2>"
            "<p>Quill will progressively absorb proven ideas from BITS Whisperer in focused phases, "
            "while preserving Quill's writing-first experience.</p>"
            "<h2 id='roadmap'>Integration Roadmap</h2>"
            "<table>"
            "<caption>Planned feature pull-through from BITS Whisperer into Quill</caption>"
            "<thead><tr>"
            "<th scope='col'>Capability</th>"
            "<th scope='col'>Whisperer Source</th>"
            "<th scope='col'>Phase</th>"
            "<th scope='col'>Quill Plan</th>"
            "</tr></thead>"
            f"<tbody>{roadmap_html}</tbody>"
            "</table>"
            "<h2 id='experience-principles'>Experience Principles</h2>"
            "<table>"
            "<caption>User experience principles guiding the integration</caption>"
            "<thead><tr><th scope='col'>Principle</th><th scope='col'>How it applies</th></tr></thead>"
            f"<tbody>{principles_html}</tbody>"
            "</table>"
            "<h2 id='next-steps'>Next Steps</h2>"
            "<ol>"
            "<li>Use Startup Wizard to configure profile, AI, and speech foundation.</li>"
            "<li>Use Status Page to monitor tasks, speech downloads, and feature state.</li>"
            "<li>Iterate in small, accessible milestones with clear release notes.</li>"
            "</ol>"
            "<p>It all starts with a whisper that glows and writes with a magical Quill.</p>"
        )

    def show_external_tools_dialog(self) -> None:
        wx = self._wx
        statuses = get_external_tool_statuses()
        dialog = wx.Dialog(
            self.frame,
            title="External Tools and Format Support",
            size=(860, 620),
        )
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Quill can grow with optional external tools. Each tool below explains what "
                    "it unlocks, how Quill uses it, and how to install it safely if you want it."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        choices = [status.name for status in statuses]
        chooser = wx.ListBox(panel, choices=choices)
        chooser.SetSelection(0 if choices else wx.NOT_FOUND)
        details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        copy_button = wx.Button(panel, label="Copy Install Command")
        website_button = wx.Button(panel, label="Open Website")
        wizard_button = wx.Button(panel, label="Open Wizard")
        close_button = wx.Button(panel, id=wx.ID_OK, label="Close")

        touch_points = {
            "pandoc": (
                "Pandoc Conversion Wizard",
                "Document conversion into Markdown, HTML, or plain text tabs",
            ),
            "tesseract": (
                "OCR Image",
                "Scanned-image and screenshot text recovery",
            ),
            "libreoffice": (
                "Future office conversion fallback",
                "Difficult legacy office imports and format repair",
            ),
            "ghostscript": (
                "Future PDF conversion pipeline",
                "Print-oriented and PostScript-heavy workflows",
            ),
            "tidy_html5": (
                "Future HTML validation",
                "Check HTML exports and authoring output before handoff",
            ),
            "xmllint": (
                "Future XML and XHTML validation",
                "Check EPUB internals and structured markup for well-formedness",
            ),
            "pymarkdownlnt": (
                "Future Markdown validation",
                "Lint Markdown structure and style without Node.js or Java",
            ),
        }

        def selected_status() -> object | None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return None
            return statuses[selection]

        def refresh_details() -> None:
            status = selected_status()
            if status is None:
                details.SetValue("No external tools are registered.")
                copy_button.Enable(False)
                website_button.Enable(False)
                wizard_button.Enable(False)
                return
            touch_lines = touch_points.get(status.tool_id, ())
            lines = [status.definition.description, ""]
            lines.append(f"Category: {status.definition.category}")
            if status.installed:
                lines.append(f"Status: installed via {status.source}")
                if status.path:
                    lines.append(f"Path: {status.path}")
                if status.version:
                    lines.append(f"Version: {status.version}")
            else:
                lines.append("Status: not installed yet")
                lines.append("Install command:")
                lines.append(status.definition.install_command)
            lines.extend(["", "What this unlocks in Quill:"])
            lines.extend(f"- {item}" for item in status.definition.capabilities)
            if touch_lines:
                lines.extend(["", "Suggested first touch points:"])
                lines.extend(f"- {item}" for item in touch_lines)
            if status.definition.category == "validation":
                lines.extend(
                    [
                        "",
                        "Why Quill recommends this:",
                        "- It adds validation value without pulling in Node.js or Java.",
                    ]
                )
            lines.extend(["", f"Learn more: {status.definition.website_url}"])
            details.SetValue("\n".join(lines))
            copy_button.Enable(True)
            website_button.Enable(True)
            wizard_button.Enable(status.tool_id == "pandoc")

        def copy_install_command() -> None:
            status = selected_status()
            if status is None:
                return
            if not self._copy_to_clipboard(copyable_install_command(status.tool_id)):
                self._set_status("Clipboard is unavailable")
                return
            self._set_status(f"Copied install command for {status.name}")

        def open_website() -> None:
            status = selected_status()
            if status is None:
                return
            webbrowser.open(status.definition.website_url)
            self._set_status(f"Opened website for {status.name}")

        def open_wizard() -> None:
            status = selected_status()
            if status is None or status.tool_id != "pandoc":
                return
            dialog.EndModal(wx.ID_OK)
            self.open_pandoc_wizard()

        chooser.Bind(wx.EVT_LISTBOX, lambda _e: refresh_details())
        copy_button.Bind(wx.EVT_BUTTON, lambda _e: copy_install_command())
        website_button.Bind(wx.EVT_BUTTON, lambda _e: open_website())
        wizard_button.Bind(wx.EVT_BUTTON, lambda _e: open_wizard())
        close_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))

        root.Add(chooser, 0, wx.ALL | wx.EXPAND, 8)
        root.Add(details, 1, wx.ALL | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(copy_button, 0, wx.RIGHT, 6)
        buttons.Add(website_button, 0, wx.RIGHT, 6)
        buttons.Add(wizard_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(close_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        refresh_details()
        self._show_modal_dialog(dialog, "External Tools and Format Support")

    def open_pandoc_wizard(self) -> None:
        wx = self._wx
        status = get_external_tool_status("pandoc")
        if not status.installed:
            result = self._show_message_box(
                (
                    "Pandoc is not installed yet. Quill can guide you, but the conversion wizard "
                    "needs Pandoc first. Copy the install command now?"
                ),
                "Pandoc Conversion Wizard",
                wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT,
            )
            if result == wx.YES and self._copy_to_clipboard(copyable_install_command("pandoc")):
                self._set_status("Copied Pandoc install command")
            else:
                self._set_status("Pandoc wizard unavailable until Pandoc is installed")
            return

        request = self._prompt_pandoc_conversion_request()
        if request is None:
            self._set_status("Pandoc wizard cancelled")
            return
        source_path, output_kind = request
        self._set_status(f"Running Pandoc on {source_path.name}...")
        try:
            result = convert_document_with_pandoc(source_path, output_kind, tool_status=status)
        except (PandocUnavailableError, PandocConversionError, ValueError) as error:
            self._show_message_box(
                f"Pandoc conversion failed: {error}",
                "Pandoc Conversion Wizard",
                wx.ICON_ERROR | wx.OK,
            )
            self._set_status("Pandoc conversion failed")
            return
        document = Document(
            text=result.text,
            path=None,
            modified=False,
            source_metadata={
                "source_kind": output_kind,
                "engine": "pandoc",
                "quality_score": 100,
                "source_file": source_path.name,
                "pandoc_path": result.pandoc_path,
            },
        )
        index = self._create_document_tab(document, select=True)
        self._set_tab_page_text(index, f"Pandoc - {source_path.stem} ({output_kind})")
        self._set_status(f"Opened {source_path.name} as {output_kind} via Pandoc")

    def _prompt_pandoc_conversion_request(self) -> tuple[Path, str] | None:
        wx = self._wx
        wildcard = (
            "Pandoc-friendly files "
            "(*.docx;*.md;*.markdown;*.html;*.htm;*.epub;*.odt;*.rst;*.txt)|"
            "*.docx;*.md;*.markdown;*.html;*.htm;*.epub;*.odt;*.rst;*.txt|"
            "All files (*.*)|*.*"
        )
        dialog = wx.Dialog(self.frame, title="Pandoc Conversion Wizard", size=(760, 360))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Choose a source file and output format. Quill will convert it with Pandoc "
                    "and open the converted text in a new tab."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        source_row = wx.BoxSizer(wx.HORIZONTAL)
        source_label = wx.StaticText(panel, label="Source file")
        source_field = wx.TextCtrl(panel)
        browse_button = wx.Button(panel, label="Browse...")
        source_row.Add(source_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        source_row.Add(source_field, 1, wx.RIGHT | wx.EXPAND, 8)
        source_row.Add(browse_button, 0)
        root.Add(source_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        format_row = wx.BoxSizer(wx.HORIZONTAL)
        format_label = wx.StaticText(panel, label="Output format")
        format_choice = wx.Choice(
            panel,
            choices=[
                "Markdown (.md)",
                "HTML (.html)",
                "Plain text (.txt)",
            ],
        )
        format_choice.SetSelection(0)
        format_row.Add(format_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        format_row.Add(format_choice, 1, wx.EXPAND)
        root.Add(format_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        validation_text = wx.StaticText(panel, label="")
        root.Add(validation_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        convert_button = wx.Button(panel, id=wx.ID_OK, label="Convert and Open")
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")
        buttons.AddStretchSpacer(1)
        buttons.Add(convert_button, 0, wx.RIGHT, 6)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        dialog_result: dict[str, object] = {}

        def browse_source() -> None:
            with wx.FileDialog(
                dialog,
                "Choose a source document for Pandoc",
                wildcard=wildcard,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as file_dialog:
                if self._show_modal_dialog(file_dialog, "Pandoc Source File") == wx.ID_OK:
                    source_field.SetValue(file_dialog.GetPath())
                    validation_text.SetLabel("")

        def submit() -> None:
            raw_path = source_field.GetValue().strip()
            if not raw_path:
                validation_text.SetLabel("Choose a source file before continuing.")
                source_field.SetFocus()
                return
            candidate = Path(raw_path)
            if not candidate.exists() or not candidate.is_file():
                validation_text.SetLabel("The selected source file was not found.")
                source_field.SetFocus()
                return
            output_options = ["markdown", "html", "plain"]
            selection = format_choice.GetSelection()
            if selection < 0 or selection >= len(output_options):
                validation_text.SetLabel("Choose an output format before continuing.")
                format_choice.SetFocus()
                return
            dialog_result["source_path"] = candidate
            dialog_result["output_kind"] = output_options[selection]
            dialog.EndModal(wx.ID_OK)

        browse_button.Bind(wx.EVT_BUTTON, lambda _e: browse_source())
        convert_button.Bind(wx.EVT_BUTTON, lambda _e: submit())
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))
        if self._show_modal_dialog(dialog, "Pandoc Conversion Wizard") != wx.ID_OK:
            return None
        source_path = dialog_result.get("source_path")
        output_kind = dialog_result.get("output_kind")
        if not isinstance(source_path, Path) or not isinstance(output_kind, str):
            return None
        return source_path, output_kind

    def save_diagnostics_bundle(self) -> None:
        wx = self._wx
        include_paths = self._review_diagnostics_export()
        if include_paths is None:
            self._set_status("Diagnostics export cancelled")
            return
        default_name = f"quill-diagnostics-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.zip"
        with wx.FileDialog(
            self.frame,
            "Save diagnostics bundle",
            wildcard="ZIP archives (*.zip)|*.zip|All files (*.*)|*.*",
            defaultFile=default_name,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Save Diagnostics") != wx.ID_OK:
                self._set_status("Diagnostics export cancelled")
                return
            target = Path(dialog.GetPath())

        detection = detect_screen_reader()
        bundle_path = write_diagnostics_bundle(
            target,
            settings=self.settings,
            keymap=self.keymap,
            notifications=self._notifications,
            current_document=self.document,
            include_file_paths=include_paths,
            extra_environment={
                "screen_reader": detection.name,
                "wx_version": self._wx.version(),
                **self._announcement_engine.diagnostics_environment(),
            },
        )
        self._record_notification(f"Saved diagnostics to {bundle_path.name}", "diagnostics")
        self._set_status(f"Saved diagnostics bundle to {bundle_path.name}")

    def report_bug(self) -> None:
        review = self._review_bug_report()
        if review is None:
            self._set_status("Bug report cancelled")
            return
        payload, issue_url = review
        diagnostics_path = getattr(self, "_last_bug_report_diagnostics_path", None)
        clipboard_text = payload["body"]
        if isinstance(diagnostics_path, Path):
            clipboard_text = f"{clipboard_text}\n\nDiagnostics bundle path:\n{diagnostics_path}"
        self._copy_to_clipboard(clipboard_text)
        webbrowser.open(issue_url)
        self._record_notification("Opened support-hub bug report form", "support")
        if isinstance(diagnostics_path, Path):
            self._set_status(
                "Opened bug report form, copied report, and prepared diagnostics bundle path"
            )
        else:
            self._set_status("Opened bug report form and copied environment summary to clipboard")

    def _review_diagnostics_export(self) -> bool | None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Review Diagnostics Export", size=(780, 560))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        include_paths = wx.CheckBox(panel, label="Include plain file paths in the bundle")
        review = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        copy_button = wx.Button(panel, label="Copy Summary")
        continue_button = wx.Button(panel, id=wx.ID_OK, label="Continue")
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")

        def refresh() -> None:
            detection = detect_screen_reader()
            review.SetValue(
                build_diagnostics_review_text(
                    settings=self.settings,
                    keymap=self.keymap,
                    notifications=self._notifications,
                    current_document=self.document,
                    include_file_paths=include_paths.GetValue(),
                    extra_environment={
                        "screen_reader": detection.name,
                        "wx_version": self._wx.version(),
                        **self._announcement_engine.diagnostics_environment(),
                    },
                )
            )

        include_paths.Bind(wx.EVT_CHECKBOX, lambda _e: refresh())
        copy_button.Bind(
            wx.EVT_BUTTON,
            lambda _e: self._copy_to_clipboard(review.GetValue()),
        )
        continue_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Review what Quill will include before writing the diagnostics zip. "
                    "Nothing leaves your machine from this step."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        root.Add(wx.StaticText(panel, label="Logs folder"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        logs_field = wx.TextCtrl(panel, style=wx.TE_READONLY)
        logs_field.SetValue(str(app_data_dir() / "logs"))
        root.Add(logs_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        root.Add(
            wx.StaticText(panel, label="Diagnostics folder"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            8,
        )
        diagnostics_field = wx.TextCtrl(panel, style=wx.TE_READONLY)
        diagnostics_field.SetValue(str(app_data_dir() / "diagnostics"))
        root.Add(diagnostics_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        root.Add(include_paths, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        root.Add(review, 1, wx.ALL | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(copy_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(continue_button, 0, wx.RIGHT, 6)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        refresh()
        if self._show_modal_dialog(dialog, "Review Diagnostics Export") != wx.ID_OK:
            return None
        return include_paths.GetValue()

    def _review_bug_report(self) -> tuple[dict[str, str], str] | None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Report a Bug", size=(860, 720))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        announcement_engine = getattr(self, "_announcement_engine", None)
        announcement_environment = (
            announcement_engine.diagnostics_environment() if announcement_engine is not None else {}
        )
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Describe the issue, then open the support form. Quill can create a "
                    "diagnostics bundle in this wizard so you can attach it to the issue."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        summary_label = wx.StaticText(panel, label="Summary")
        summary_field = wx.TextCtrl(panel)
        summary_field.SetValue(f"Bug report: {self.document.name}")
        root.Add(summary_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(summary_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        happened_label = wx.StaticText(panel, label="What happened")
        happened_field = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        root.Add(happened_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(happened_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        expected_label = wx.StaticText(panel, label="What you expected")
        expected_field = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        root.Add(expected_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(expected_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        steps_label = wx.StaticText(panel, label="Steps to reproduce")
        steps_field = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        root.Add(steps_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(steps_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        include_diagnostics = wx.CheckBox(
            panel,
            label="Create diagnostics bundle in this wizard",
        )
        include_diagnostics.SetValue(True)
        include_paths = wx.CheckBox(panel, label="Include plain file paths in diagnostics")
        include_paths.SetValue(False)
        diagnostics_path_field = wx.TextCtrl(panel, style=wx.TE_READONLY)
        root.Add(include_diagnostics, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(include_paths, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        root.Add(wx.StaticText(panel, label="Diagnostics bundle path"), 0, wx.LEFT | wx.RIGHT, 8)
        root.Add(diagnostics_path_field, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        preview_label = wx.StaticText(panel, label="Report preview")
        review = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        root.Add(preview_label, 0, wx.LEFT | wx.RIGHT, 8)
        root.Add(review, 1, wx.ALL | wx.EXPAND, 8)
        validation_text = wx.StaticText(panel, label="")
        root.Add(validation_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        copy_button = wx.Button(panel, label="Copy Preview")
        open_button = wx.Button(panel, id=wx.ID_OK, label="Open Support Form")
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")
        dialog_result: dict[str, object] = {}

        def build_payload(
            diagnostics_note: str | None = None,
        ) -> tuple[dict[str, str], str]:
            payload = build_bug_report_payload(
                current_document=self.document,
                extra_environment={
                    "screen_reader": detect_screen_reader().name,
                    "wx_version": self._wx.version(),
                    **announcement_environment,
                },
                summary_override=summary_field.GetValue().strip(),
                happened=happened_field.GetValue().strip(),
                expected=expected_field.GetValue().strip(),
                steps=steps_field.GetValue().strip(),
                diagnostics_note=diagnostics_note,
            )
            issue_url = build_support_issue_url(
                payload,
                source_app="Quill",
                version=__version__,
                platform_label=str(collect_environment_info()["platform"]),
                diagnostics_note=diagnostics_note,
            )
            return payload, issue_url

        def refresh_preview() -> None:
            diagnostics_note = None
            path_text = diagnostics_path_field.GetValue().strip()
            if path_text:
                diagnostics_note = (
                    "Diagnostics bundle created by Quill. Please attach this zip in the issue: "
                    f"{path_text}"
                )
            elif include_diagnostics.GetValue():
                diagnostics_note = (
                    "Quill will create a diagnostics bundle when you continue. Attach the "
                    "generated zip file to the issue."
                )
            payload, issue_url = build_payload(diagnostics_note=diagnostics_note)
            review.SetValue(
                f"Summary: {payload['summary']}\n\n{payload['body']}\n\nDestination:\n{issue_url}"
            )

        def confirm_preflight() -> bool:
            include_diag = include_diagnostics.GetValue()
            include_plain_paths = include_paths.GetValue() if include_diag else False
            lines = [
                "You are about to prepare this report with:",
                "",
                f"- Diagnostics bundle: {'Yes' if include_diag else 'No'}",
                (
                    f"- Plain file paths in diagnostics: {'Yes' if include_plain_paths else 'No'}"
                    if include_diag
                    else "- Plain file paths in diagnostics: N/A (diagnostics disabled)"
                ),
                "- Report summary and details shown in preview",
                "",
                "Continue?",
            ]
            with wx.MessageDialog(
                dialog,
                "\n".join(lines),
                "Report a Bug preflight",
                style=wx.OK | wx.CANCEL | wx.ICON_QUESTION,
            ) as preflight:
                return self._show_modal_dialog(preflight, "Report a Bug Preflight") == wx.ID_OK

        def submit_report() -> None:
            if not confirm_preflight():
                validation_text.SetLabel("Report submission cancelled from preflight summary.")
                return
            diagnostics_path: Path | None = None
            if include_diagnostics.GetValue():
                try:
                    diagnostics_path = self._create_diagnostics_bundle_for_report(
                        include_paths.GetValue()
                    )
                except OSError as error:
                    validation_text.SetLabel(f"Could not write diagnostics bundle: {error}")
                    return
                diagnostics_path_field.SetValue(str(diagnostics_path))
            diagnostics_note = None
            if diagnostics_path is not None:
                diagnostics_note = (
                    "Diagnostics bundle created by Quill. Please attach this zip in the issue: "
                    f"{diagnostics_path}"
                )
            elif include_diagnostics.GetValue():
                diagnostics_note = (
                    "Diagnostics bundle requested, but no local bundle path is available."
                )
            payload, issue_url = build_payload(diagnostics_note=diagnostics_note)
            dialog_result["payload"] = payload
            dialog_result["issue_url"] = issue_url
            dialog_result["diagnostics_path"] = diagnostics_path
            dialog.EndModal(wx.ID_OK)

        copy_button.Bind(wx.EVT_BUTTON, lambda _e: self._copy_to_clipboard(review.GetValue()))
        open_button.Bind(wx.EVT_BUTTON, lambda _e: submit_report())
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))

        def on_toggle_include_diagnostics() -> None:
            include_paths.Enable(include_diagnostics.GetValue())
            refresh_preview()

        include_diagnostics.Bind(wx.EVT_CHECKBOX, lambda _e: on_toggle_include_diagnostics())
        include_paths.Bind(wx.EVT_CHECKBOX, lambda _e: refresh_preview())
        summary_field.Bind(wx.EVT_TEXT, lambda _e: refresh_preview())
        happened_field.Bind(wx.EVT_TEXT, lambda _e: refresh_preview())
        expected_field.Bind(wx.EVT_TEXT, lambda _e: refresh_preview())
        steps_field.Bind(wx.EVT_TEXT, lambda _e: refresh_preview())
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(copy_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(open_button, 0, wx.RIGHT, 6)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        include_paths.Enable(include_diagnostics.GetValue())
        refresh_preview()
        if self._show_modal_dialog(dialog, "Review Bug Report") != wx.ID_OK:
            return None
        payload = dialog_result.get("payload")
        issue_url = dialog_result.get("issue_url")
        diagnostics_path = dialog_result.get("diagnostics_path")
        if isinstance(diagnostics_path, Path):
            self._last_bug_report_diagnostics_path = diagnostics_path
        else:
            self._last_bug_report_diagnostics_path = None
        if not isinstance(payload, dict) or not isinstance(issue_url, str):
            return None
        return payload, issue_url

    def _create_diagnostics_bundle_for_report(self, include_file_paths: bool) -> Path:
        detection = detect_screen_reader()
        announcement_engine = getattr(self, "_announcement_engine", None)
        announcement_environment = (
            announcement_engine.diagnostics_environment() if announcement_engine is not None else {}
        )
        target = (
            app_data_dir()
            / "diagnostics"
            / (f"quill-diagnostics-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.zip")
        )
        bundle_path = write_diagnostics_bundle(
            target,
            settings=self.settings,
            keymap=self.keymap,
            notifications=self._notifications,
            current_document=self.document,
            include_file_paths=include_file_paths,
            extra_environment={
                "screen_reader": detection.name,
                "wx_version": self._wx.version(),
                **announcement_environment,
            },
        )
        self._record_notification(f"Saved diagnostics to {bundle_path.name}", "diagnostics")
        return bundle_path

    def show_keyboard_trap_snapshot(self) -> None:
        wx = self._wx
        snapshot = self._region_tracker.snapshot()
        report = render_snapshot(snapshot)
        self._show_message_box(report, "Keyboard Trap Audit", wx.ICON_INFORMATION | wx.OK)
        self._set_status(
            "Keyboard trap audit: potential trap detected"
            if snapshot.has_keyboard_trap
            else "Keyboard trap audit: no trap detected"
        )

    def show_accessibility_audit(self) -> None:
        wx = self._wx
        snapshot = self._region_tracker.snapshot()
        detection = detect_screen_reader()
        report = build_accessibility_audit_report(snapshot, detection.name)
        self._show_message_box(report, "Accessibility Audit", wx.ICON_INFORMATION | wx.OK)
        self._set_status("Accessibility audit complete")

    def _create_named_scratch_tab(self, title: str, text: str) -> None:
        index = self._create_document_tab(
            Document(text=text, path=None, modified=False),
            select=True,
        )
        self._set_tab_page_text(index, title)

    def _glow_scope(self) -> tuple[str, int, int, str]:
        start, end = self.editor.GetSelection()
        if start != end:
            return self.editor.GetRange(start, end), start, end, "selection"
        cursor = self.editor.GetInsertionPoint()
        text = self.editor.GetValue()
        start, end = paragraph_span(text, cursor)
        scope = self.editor.GetRange(start, end)
        if not scope.strip():
            start, end = line_span(text, cursor)
            scope = self.editor.GetRange(start, end)
            return scope, start, end, "current line"
        return scope, start, end, "current paragraph"

    def glow_audit_document(self) -> None:
        markup = self._current_markup_context()
        text = self.editor.GetValue()
        report = build_audit_report(self.document.name, text, markup, "current document")
        self._create_named_scratch_tab(f"GLOW Audit - {self.document.name}", report)
        self._set_status(f"Opened GLOW audit for {self.document.name}")

    def glow_audit_selection(self) -> None:
        text, _start, _end, scope_label = self._glow_scope()
        markup = self._current_markup_context()
        report = build_audit_report(self.document.name, text, markup, scope_label)
        self._create_named_scratch_tab(f"GLOW Audit - {scope_label.title()}", report)
        self._set_status(f"Opened GLOW audit for {scope_label}")

    def glow_fix_document(self) -> None:
        original = self.editor.GetValue()
        markup = self._current_markup_context()
        result = fix_text(original, markup)
        if result.text == original:
            report = build_fix_report(self.document.name, result, markup, "current document")
            self._create_named_scratch_tab(f"GLOW Fix Report - {self.document.name}", report)
            self._set_status("No deterministic GLOW fixes were available")
            return
        preview_title = f"{self.document.name} - GLOW Fix Preview"
        index = self._create_document_tab(
            Document(text=result.text, path=None, modified=False),
            select=True,
        )
        self._set_tab_page_text(index, preview_title)
        report = build_fix_report(self.document.name, result, markup, "current document")
        self._record_notification(report.splitlines()[0], "glow")
        self._start_compare_session([(self.document.name, original), (preview_title, result.text)])
        self._set_status(
            f"Opened GLOW fix preview with {len(result.fixes)} changes and started compare"
        )

    def glow_fix_selection(self) -> None:
        text, start, end, scope_label = self._glow_scope()
        markup = self._current_markup_context()
        result = fix_text(text, markup)
        if result.text == text:
            self._set_status(f"No deterministic GLOW fixes were available for {scope_label}")
            return
        self.editor.Replace(start, end, result.text)
        self.editor.SetSelection(start, start + len(result.text))
        self.document.set_text(self.editor.GetValue())
        report = build_fix_report(self.document.name, result, markup, scope_label)
        self._record_notification(report.splitlines()[0], "glow")
        self._set_status(f"Applied {len(result.fixes)} GLOW fixes to {scope_label}")

    def go_to_line(self) -> None:
        wx = self._wx
        with wx.TextEntryDialog(
            self.frame,
            "Enter line or line,column:",
            "Go To Line",
            value="1",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Go To Line") != wx.ID_OK:
                return
            raw_line = dialog.GetValue().strip()

        try:
            target_line, target_column = parse_line_column(raw_line)
        except ValueError:
            self._show_message_box(
                "Use a line number or line,column (for example: 12 or 12,4).",
                "Go To Line",
                wx.ICON_ERROR | wx.OK,
            )
            return
        if target_line < 1:
            self._show_message_box(
                "Line number must be at least 1.",
                "Go To Line",
                wx.ICON_ERROR | wx.OK,
            )
            return
        if target_column is not None and target_column < 1:
            self._show_message_box(
                "Column number must be at least 1.",
                "Go To Line",
                wx.ICON_ERROR | wx.OK,
            )
            return

        text = self.editor.GetValue()
        line_starts = [0]
        for index, char in enumerate(text):
            if char == "\n":
                line_starts.append(index + 1)

        if target_line > len(line_starts):
            self._show_message_box(
                f"Document has only {len(line_starts)} lines.",
                "Go To Line",
                wx.ICON_ERROR | wx.OK,
            )
            return

        line_start = line_starts[target_line - 1]
        if target_line < len(line_starts):
            line_end = line_starts[target_line] - 1
        else:
            line_end = len(text)
        if target_column is None:
            insertion_point = line_start
        else:
            insertion_point = min(line_start + target_column - 1, line_end)
        self._record_location_before_jump()
        self._move_point(insertion_point)
        self.editor.SetFocus()
        self._location_ring.record(insertion_point)
        if target_column is None:
            self._set_status(f"Moved to line {target_line}")
        else:
            self._set_status(f"Moved to line {target_line}, column {target_column}")

    def go_to_page(self) -> None:
        wx = self._wx
        text = self.editor.GetValue()
        starts = page_starts(text)
        with wx.TextEntryDialog(
            self.frame,
            f"Enter a page number (1-{len(starts)}):",
            "Go To Page",
            value="1",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Go To Page") != wx.ID_OK:
                return
            raw_value = dialog.GetValue().strip()
        try:
            page_number = int(raw_value)
        except ValueError:
            self._show_message_box(
                "Page number must be a number.",
                "Go To Page",
                wx.ICON_ERROR | wx.OK,
            )
            return
        target = page_start_for_number(text, page_number)
        if target is None:
            self._show_message_box(
                f"Document has only {len(starts)} page(s).",
                "Go To Page",
                wx.ICON_ERROR | wx.OK,
            )
            return
        self._record_location_before_jump()
        self._move_point(target)
        self.editor.SetFocus()
        self._location_ring.record(target)
        self._set_status(f"Moved to page {page_number}")

    def navigate_back_location(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        target = self._location_ring.back(cursor)
        if target is None:
            self._set_status("No earlier location")
            return
        self._move_point(target)
        self.editor.SetFocus()
        self._set_status("Moved back")

    def navigate_forward_location(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        target = self._location_ring.forward(cursor)
        if target is None:
            self._set_status("No later location")
            return
        self._move_point(target)
        self.editor.SetFocus()
        self._set_status("Moved forward")

    def navigate_next_heading(self) -> None:
        self._navigate_heading(reverse=False)

    def navigate_previous_heading(self) -> None:
        self._navigate_heading(reverse=True)

    def _navigate_heading(self, reverse: bool) -> None:
        markup_kind = infer_markup_kind(self.document.path)
        if markup_kind not in {"markdown", "html"}:
            self._set_status("Heading navigation is available in Markdown or HTML documents")
            return
        cursor = self.editor.GetInsertionPoint()
        if reverse:
            target = previous_heading_start(self.editor.GetValue(), cursor, markup_kind)
            if target is None:
                self._set_status("No previous heading")
                return
            label = "previous heading"
        else:
            target = next_heading_start(self.editor.GetValue(), cursor, markup_kind)
            if target is None:
                self._set_status("No next heading")
                return
            label = "next heading"
        self._record_location_before_jump()
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        self.editor.SetFocus()
        self._location_ring.record(target)
        self._set_status(f"Moved to {label}")

    def navigate_next_block(self) -> None:
        self._navigate_block(reverse=False)

    def navigate_previous_block(self) -> None:
        self._navigate_block(reverse=True)

    def _navigate_block(self, reverse: bool) -> None:
        cursor = self.editor.GetInsertionPoint()
        if reverse:
            target = previous_block_start(self.editor.GetValue(), cursor)
            if target is None:
                self._set_status("No previous block")
                return
            label = "previous block"
        else:
            target = next_block_start(self.editor.GetValue(), cursor)
            if target is None:
                self._set_status("No next block")
                return
            label = "next block"
        self._record_location_before_jump()
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        self.editor.SetFocus()
        self._location_ring.record(target)
        self._set_status(f"Moved to {label}")

    def open_outline_navigator(self) -> None:
        if self.document.path is not None and self.document.path.suffix.lower() == ".epub":
            self.open_epub_navigator()
            return
        markup_kind = infer_markup_kind(self.document.path)
        if markup_kind == "plain":
            self._set_status("Outline is not available for plain text files")
            return
        action_label = "Jump to Key" if markup_kind == "yaml" else "Jump to Heading"
        nodes = self._build_outline_navigator_nodes(action_label=action_label)
        if not nodes:
            if markup_kind == "yaml":
                self._set_status("No YAML structure found")
            else:
                self._set_status("No outline headings found")
            return
        title = "YAML Navigator" if markup_kind == "yaml" else "Outline Navigator"
        root_label = "Keys" if markup_kind == "yaml" else "Headings"
        selected = self._show_tree_navigator(
            title=title,
            root_label=root_label,
            nodes=nodes,
        )
        if not isinstance(selected, OutlineEntry):
            self._set_status("Outline navigation cancelled")
            return
        self._jump_to(selected.position, "Moved to heading")

    def open_heading_organizer(self) -> None:
        markup_kind = infer_markup_kind(self.document.path)
        if markup_kind not in {"markdown", "html"}:
            self._set_status("Heading Organizer is only available for Markdown or HTML documents")
            return
        text = self.editor.GetValue()
        headings = parse_heading_blocks(text, markup_kind)
        if not headings:
            self._set_status("No headings found for Heading Organizer")
            return
        updated = self._show_heading_organizer_dialog(markup_kind, headings)
        if updated is None:
            self._set_status("Heading Organizer cancelled")
            return
        transformed = apply_heading_organizer_edits(text, markup_kind, updated)
        if transformed == text:
            self._set_status("Heading Organizer closed without changes")
            return
        self._apply_editor_text(transformed, "Applied heading organizer changes")

    def _show_heading_organizer_dialog(
        self,
        markup_kind: str,
        headings: list[HeadingBlock],
    ) -> list[HeadingBlock] | None:
        wx = self._wx
        dialog = wx.Dialog(
            self.frame,
            title="Heading Organizer",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(920, 620),
        )
        working = [replace(heading) for heading in headings]
        source_text = self.editor.GetValue()
        originals = {heading.source_index: heading for heading in headings}
        selected_index = 0
        list_box = wx.ListBox(dialog)
        preview = wx.TextCtrl(dialog, style=wx.TE_MULTILINE | wx.TE_READONLY)
        instructions = wx.StaticText(
            dialog,
            label=(
                "Arrow through headings. Tab demotes, Shift+Tab promotes. "
                "Use Move Up/Down to reorder sections and Rename to edit heading text."
            ),
        )
        promote_button = wx.Button(dialog, label="Promote")
        demote_button = wx.Button(dialog, label="Demote")
        move_up_button = wx.Button(dialog, label="Move Up")
        move_down_button = wx.Button(dialog, label="Move Down")
        rename_button = wx.Button(dialog, label="Rename...")
        validate_button = wx.Button(dialog, label="Validate")
        apply_button = wx.Button(dialog, id=wx.ID_OK, label="Apply")
        cancel_button = wx.Button(dialog, id=wx.ID_CANCEL, label="Cancel")

        def labels() -> list[str]:
            return [
                f"Heading {entry.level}: {entry.title or '(empty heading)'}" for entry in working
            ]

        def refresh() -> None:
            nonlocal selected_index
            list_box.Set(labels())
            if not working:
                preview.ChangeValue("No headings found.")
                return
            selected_index = max(0, min(selected_index, len(working) - 1))
            list_box.SetSelection(selected_index)
            update_preview()

        def selected() -> HeadingBlock | None:
            if not working:
                return None
            current = list_box.GetSelection()
            if current == wx.NOT_FOUND:
                return None
            return working[current]

        def set_selected(entry: HeadingBlock) -> None:
            nonlocal selected_index
            current = list_box.GetSelection()
            if current == wx.NOT_FOUND:
                return
            working[current] = entry
            selected_index = current
            refresh()

        def update_preview() -> None:
            entry = selected()
            if entry is None:
                preview.ChangeValue("No heading selected.")
                return
            origin = originals.get(entry.source_index)
            if origin is None:
                preview.ChangeValue(entry.title)
                return
            section = source_text[origin.section_start : origin.section_end].strip()
            preview.ChangeValue(section or entry.title)

        def promote() -> None:
            entry = selected()
            if entry is None:
                return
            if entry.level <= 1:
                self._set_status("Heading already at level 1")
                return
            set_selected(replace(entry, level=entry.level - 1))
            self._set_status(f"{entry.title or '(empty heading)'} is now Heading {entry.level - 1}")

        def demote() -> None:
            entry = selected()
            if entry is None:
                return
            if entry.level >= 6:
                self._set_status("Heading already at level 6")
                return
            set_selected(replace(entry, level=entry.level + 1))
            self._set_status(f"{entry.title or '(empty heading)'} is now Heading {entry.level + 1}")

        def move(delta: int) -> None:
            nonlocal selected_index
            current = list_box.GetSelection()
            if current == wx.NOT_FOUND:
                return
            target = current + delta
            if target < 0 or target >= len(working):
                return
            working[current], working[target] = working[target], working[current]
            selected_index = target
            refresh()
            self._set_status("Moved heading")

        def rename() -> None:
            entry = selected()
            if entry is None:
                return
            with wx.TextEntryDialog(
                dialog,
                "Enter heading text:",
                "Rename Heading",
                value=entry.title,
            ) as rename_dialog:
                if self._show_modal_dialog(rename_dialog, "Rename Heading") != wx.ID_OK:
                    return
                new_title = rename_dialog.GetValue().strip()
            set_selected(replace(entry, title=new_title))
            self._set_status("Renamed heading")

        def validate(show_success: bool = False) -> bool:
            issues = validate_heading_sequence(working)
            if not issues:
                if show_success:
                    self._show_message_box(
                        "Heading order passed accessibility checks.",
                        "Heading Organizer",
                        wx.OK | wx.ICON_INFORMATION,
                    )
                return True
            self._show_message_box(
                "Fix these heading issues before applying:\n\n"
                + "\n".join(f"- {issue}" for issue in issues),
                "Heading Organizer",
                wx.OK | wx.ICON_WARNING,
            )
            return False

        def on_key(event: object) -> None:
            key_code = event.GetKeyCode()
            if key_code == wx.WXK_TAB:
                if event.ShiftDown():
                    promote()
                else:
                    demote()
                return
            if key_code in (wx.WXK_ADD, wx.WXK_NUMPAD_ADD):
                demote()
                return
            if key_code in (wx.WXK_SUBTRACT, wx.WXK_NUMPAD_SUBTRACT):
                promote()
                return
            event.Skip()

        body = wx.BoxSizer(wx.HORIZONTAL)
        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(instructions, 0, wx.ALL | wx.EXPAND, 8)
        main.Add(list_box, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        main.Add(
            wx.StaticText(dialog, label="Preview of selected heading section:"),
            0,
            wx.LEFT | wx.RIGHT,
            8,
        )
        main.Add(preview, 1, wx.ALL | wx.EXPAND, 8)
        actions = wx.BoxSizer(wx.VERTICAL)
        actions.Add(promote_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(demote_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(move_up_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(move_down_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(rename_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(validate_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.AddStretchSpacer(1)
        actions.Add(apply_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        actions.Add(cancel_button, 0, wx.EXPAND)
        body.Add(main, 1, wx.EXPAND)
        body.Add(actions, 0, wx.ALL | wx.EXPAND, 8)
        dialog.SetSizer(body)

        list_box.Bind(wx.EVT_LISTBOX, lambda _e: update_preview())
        list_box.Bind(wx.EVT_CHAR_HOOK, on_key)
        promote_button.Bind(wx.EVT_BUTTON, lambda _e: promote())
        demote_button.Bind(wx.EVT_BUTTON, lambda _e: demote())
        move_up_button.Bind(wx.EVT_BUTTON, lambda _e: move(-1))
        move_down_button.Bind(wx.EVT_BUTTON, lambda _e: move(1))
        rename_button.Bind(wx.EVT_BUTTON, lambda _e: rename())
        validate_button.Bind(wx.EVT_BUTTON, lambda _e: validate(show_success=True))
        apply_button.Bind(
            wx.EVT_BUTTON,
            lambda _e: dialog.EndModal(wx.ID_OK) if validate() else None,
        )
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))

        refresh()
        if self._show_modal_dialog(dialog, "Heading Organizer") != wx.ID_OK:
            return None
        return working

    def open_yaml_structure_editor(self) -> None:
        if infer_markup_kind(self.document.path) != "yaml":
            self._set_status("YAML structure editing is only available for YAML files")
            return
        updated_text = self._show_yaml_structure_editor()
        if updated_text is None:
            self._set_status("YAML structure editor cancelled")
            return
        if updated_text == self.editor.GetValue():
            self._set_status("YAML structure editor closed without changes")
            return
        self._apply_editor_text(updated_text, "Updated YAML structure")

    def match_bracket(self) -> None:
        target = find_matching_bracket(self.editor.GetValue(), self.editor.GetInsertionPoint())
        if target is None:
            self._set_status("No matching bracket found")
            return
        self._jump_to(target, "Moved to matching bracket")

    def navigate_next_structure(self) -> None:
        self._navigate_structure(reverse=False)

    def navigate_previous_structure(self) -> None:
        self._navigate_structure(reverse=True)

    def _navigate_structure(self, reverse: bool) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        markup_kind = infer_markup_kind(self.document.path)
        if reverse:
            target = previous_structure_position(text, cursor, markup_kind)
            if target is None:
                self._set_status("No previous structure")
                return
            label = "Moved to previous structure"
        else:
            target = next_structure_position(text, cursor, markup_kind)
            if target is None:
                self._set_status("No next structure")
                return
            label = "Moved to next structure"
        self._jump_to(target, label)

    def navigate_next_region(self) -> None:
        self._cycle_region(reverse=False)

    def navigate_previous_region(self) -> None:
        self._cycle_region(reverse=True)

    def _cycle_region(self, reverse: bool) -> None:
        if not self._focus_regions:
            return
        current = self._active_region_index
        step = -1 if reverse else 1
        next_index = (current + step) % len(self._focus_regions)
        if next_index == current:
            return
        current_label = self._focus_regions[current]
        next_label = self._focus_regions[next_index]
        self._region_tracker.exit(current_label)
        self._region_tracker.enter(next_label)
        self._active_region_index = next_index
        if next_label == "Editor":
            self.editor.SetFocus()
        elif next_label == "Status Bar":
            self.statusbar.SetFocus()
        else:
            self.frame.SetFocus()
        self._set_status(f"Focused {next_label} region")

    def _outline_entries(self) -> list[OutlineEntry]:
        markup_kind = infer_markup_kind(self.document.path)
        return extract_outline_entries(self.editor.GetValue(), markup_kind)

    def _build_yaml_structure_navigator_nodes(self) -> list[_NavigatorNode]:
        nodes = extract_yaml_nodes(self.editor.GetValue())
        roots: list[_NavigatorNode] = []
        for node in nodes:
            roots.append(self._build_yaml_structure_node(node))
        return roots

    def _build_yaml_structure_node(self, node: YamlNode) -> _NavigatorNode:
        preview = self._yaml_node_preview(node)
        return _NavigatorNode(
            label=f"{node.label or '(item)'} (Ln {node.line_no + 1})",
            preview=preview,
            payload=node,
            action_label="Edit Node",
            children=[self._build_yaml_structure_node(child) for child in node.children],
        )

    def _yaml_node_preview(self, node: YamlNode, text: str | None = None) -> str:
        source = text if text is not None else self.editor.GetValue()
        lines = source.splitlines()
        if not lines or node.line_no >= len(lines):
            return node.label or "(item)"
        end_line = min(node.end_line, len(lines) - 1)
        excerpt = "\n".join(lines[node.line_no : end_line + 1]).strip()
        return excerpt or (node.label or "(item)")

    def _yaml_node_accepts_children(self, node: YamlNode) -> bool:
        return not node.value.strip()

    def _show_yaml_structure_editor(self) -> str | None:
        wx = self._wx
        working_text = self.editor.GetValue()
        dialog = wx.Dialog(self.frame, title="YAML Structure Editor", size=(1020, 700))
        splitter = wx.SplitterWindow(dialog, style=wx.SP_LIVE_UPDATE)
        tree = wx.TreeCtrl(
            splitter,
            style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HAS_VARIABLE_ROW_HEIGHT,
        )
        preview = wx.TextCtrl(splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
        splitter.SplitVertically(tree, preview, 360)
        splitter.SetMinimumPaneSize(240)

        item_payloads: dict[object, YamlNode] = {}
        selected_node: YamlNode | None = None
        root = tree.AddRoot("YAML Structure")

        def build_tree(preferred_line_no: int | None = None) -> None:
            nonlocal selected_node, root
            nodes = extract_yaml_nodes(working_text)
            item_payloads.clear()
            tree.DeleteAllItems()
            root = tree.AddRoot("YAML Structure")

            def append_nodes(parent: object, children: list[YamlNode]) -> object | None:
                first_item = None
                for node in children:
                    label = f"{node.label or '(item)'} (Ln {node.line_no + 1})"
                    item = tree.AppendItem(parent, label)
                    item_payloads[item] = node
                    if first_item is None:
                        first_item = item
                    append_nodes(item, node.children)
                return first_item

            first_item = append_nodes(root, nodes)
            tree.Expand(root)
            selected_node = None
            target_item = first_item
            if preferred_line_no is not None:
                for item, node in item_payloads.items():
                    if node.line_no == preferred_line_no:
                        target_item = item
                        break
            if target_item is not None:
                selected_node = item_payloads.get(target_item)
                if selected_node is not None:
                    preview.ChangeValue(self._yaml_node_preview(selected_node, working_text))
                tree.SelectItem(target_item)
            else:
                preview.ChangeValue("No YAML structure found")
                return

        def current_node() -> YamlNode | None:
            return selected_node

        def refresh_preview(node: YamlNode | None) -> None:
            if node is None:
                preview.ChangeValue("No YAML structure found")
                return
            preview.ChangeValue(self._yaml_node_preview(node, working_text))

        def prompt_kind(default_kind: str) -> YamlNodeKind | None:
            with wx.SingleChoiceDialog(
                dialog,
                "Choose the YAML structure kind to insert:",
                "Insert YAML Node",
                choices=["Mapping key", "List item"],
            ) as choice:
                choice.SetSelection(0 if default_kind == "mapping" else 1)
                if self._show_modal_dialog(choice, "Insert YAML Node Kind") != wx.ID_OK:
                    return None
                return "mapping" if choice.GetSelection() == 0 else "sequence"

        def prompt_label(title: str, default_value: str = "") -> str | None:
            with wx.TextEntryDialog(
                dialog,
                "Enter the YAML label or item text:",
                title,
                value=default_value,
            ) as entry:
                if self._show_modal_dialog(entry, title) != wx.ID_OK:
                    return None
                value = entry.GetValue().strip()
                return value or None

        def select_node_from_event(event: object) -> None:
            nonlocal selected_node
            node = item_payloads.get(event.GetItem())
            selected_node = node
            refresh_preview(node)
            event.Skip()

        def perform_update(action: str, update: str, preferred_line_no: int | None = None) -> None:
            nonlocal working_text
            working_text = update
            build_tree(preferred_line_no)
            node = current_node()
            if node is not None:
                refresh_preview(node)
            self._set_status(action)

        def add_child() -> None:
            node = current_node()
            if node is None:
                return
            if not self._yaml_node_accepts_children(node):
                self._show_message_box(
                    "This YAML node already has a scalar value, so it cannot accept children.",
                    "YAML Structure Editor",
                    wx.ICON_WARNING | wx.OK,
                )
                return
            kind = prompt_kind("mapping" if node.kind == "mapping" else "sequence")
            if kind is None:
                return
            label = prompt_label("Add YAML Child")
            if label is None:
                return
            try:
                updated = add_yaml_child(working_text, node.line_no, kind, label)
            except ValueError as error:
                self._show_message_box(str(error), "YAML Structure Editor", wx.ICON_ERROR | wx.OK)
                return
            perform_update("Added YAML child", updated, node.end_line + 1)

        def add_sibling() -> None:
            node = current_node()
            if node is None:
                return
            kind = prompt_kind("mapping" if node.kind == "mapping" else "sequence")
            if kind is None:
                return
            label = prompt_label("Add YAML Sibling")
            if label is None:
                return
            try:
                updated = add_yaml_sibling(working_text, node.line_no, kind, label)
            except ValueError as error:
                self._show_message_box(str(error), "YAML Structure Editor", wx.ICON_ERROR | wx.OK)
                return
            perform_update("Added YAML sibling", updated, node.end_line + 1)

        def rename_node() -> None:
            node = current_node()
            if node is None:
                return
            label = prompt_label("Rename YAML Node", node.label)
            if label is None:
                return
            try:
                updated = rename_yaml_node(working_text, node.line_no, label)
            except ValueError as error:
                self._show_message_box(str(error), "YAML Structure Editor", wx.ICON_ERROR | wx.OK)
                return
            perform_update("Renamed YAML node", updated, node.line_no)

        def delete_node() -> None:
            node = current_node()
            if node is None:
                return
            confirm = self._show_message_box(
                f"Delete '{node.label or '(item)'}' and its children?",
                "Delete YAML Node",
                wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
            )
            if confirm != wx.YES:
                return
            try:
                updated = delete_yaml_node(working_text, node.line_no)
            except ValueError as error:
                self._show_message_box(str(error), "YAML Structure Editor", wx.ICON_ERROR | wx.OK)
                return
            perform_update("Deleted YAML node", updated, max(node.line_no - 1, 0))

        buttons = wx.BoxSizer(wx.VERTICAL)
        add_child_button = wx.Button(dialog, label="Add Child...")
        add_sibling_button = wx.Button(dialog, label="Add Sibling...")
        rename_button = wx.Button(dialog, label="Rename...")
        delete_button = wx.Button(dialog, label="Delete")
        apply_button = wx.Button(dialog, id=wx.ID_OK, label="Apply Changes")
        cancel_button = wx.Button(dialog, id=wx.ID_CANCEL, label="Close")
        buttons.Add(add_child_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        buttons.Add(add_sibling_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        buttons.Add(rename_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        buttons.Add(delete_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(apply_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        buttons.Add(cancel_button, 0, wx.EXPAND)

        controls = wx.BoxSizer(wx.VERTICAL)
        controls.Add(
            wx.StaticText(
                dialog,
                label=(
                    "Use the structure tree to add, rename, and delete YAML keys or list items. "
                    "Child insertions stay indented to match the current node."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        controls.Add(splitter, 1, wx.ALL | wx.EXPAND, 8)
        content = wx.BoxSizer(wx.HORIZONTAL)
        content.Add(controls, 1, wx.EXPAND)
        content.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        dialog.SetSizer(content)

        tree.Bind(wx.EVT_TREE_SEL_CHANGED, select_node_from_event)
        add_child_button.Bind(wx.EVT_BUTTON, lambda _e: add_child())
        add_sibling_button.Bind(wx.EVT_BUTTON, lambda _e: add_sibling())
        rename_button.Bind(wx.EVT_BUTTON, lambda _e: rename_node())
        delete_button.Bind(wx.EVT_BUTTON, lambda _e: delete_node())
        apply_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))

        build_tree()
        if self._show_modal_dialog(dialog, "YAML Structure Editor") != wx.ID_OK:
            return None
        return working_text

    def _build_outline_navigator_nodes(
        self,
        *,
        action_label: str = "Jump to Heading",
    ) -> list[_NavigatorNode]:
        entries = self._outline_entries()
        if not entries:
            return []
        text = self.editor.GetValue()
        roots: list[_NavigatorNode] = []
        stack: list[tuple[int, _NavigatorNode]] = []
        for index, entry in enumerate(entries):
            end = entries[index + 1].position if index + 1 < len(entries) else len(text)
            preview = text[entry.position : end].strip() or entry.title
            node = _NavigatorNode(
                label=entry.title,
                preview=preview,
                payload=entry,
                action_label=action_label,
                children=[],
            )
            while stack and stack[-1][0] >= entry.level:
                stack.pop()
            if stack:
                stack[-1][1].children.append(node)
            else:
                roots.append(node)
            stack.append((entry.level, node))
        return roots

    def _build_epub_navigator_nodes(self, book: EpubBook) -> list[_NavigatorNode]:
        roots: list[_NavigatorNode] = []
        for chapter_index, chapter in enumerate(book.chapters):
            chapter_node = _NavigatorNode(
                label=chapter.title,
                preview=self._render_epub_chapter_text(chapter),
                payload=_EpubNavigatorTarget(chapter_index=chapter_index),
                action_label="Open Chapter",
                children=[],
            )
            heading_stack: list[tuple[int, _NavigatorNode]] = []
            for heading_index, heading in enumerate(chapter.headings):
                heading_node = _NavigatorNode(
                    label=heading.title,
                    preview=self._render_epub_heading_preview(chapter, heading.title),
                    payload=_EpubNavigatorTarget(
                        chapter_index=chapter_index,
                        heading_index=heading_index,
                    ),
                    action_label="Jump to Heading",
                    children=[],
                )
                while heading_stack and heading_stack[-1][0] >= heading.level:
                    heading_stack.pop()
                if heading_stack:
                    heading_stack[-1][1].children.append(heading_node)
                else:
                    chapter_node.children.append(heading_node)
                heading_stack.append((heading.level, heading_node))
            roots.append(chapter_node)
        return roots

    def _render_epub_chapter_text(self, chapter: EpubChapter) -> str:
        return f"# {chapter.title}\n\n{chapter.text}\n"

    def _render_epub_heading_preview(self, chapter: EpubChapter, heading_title: str) -> str:
        return f"# {chapter.title}\n\n## {heading_title}\n\n{chapter.text}\n"

    def _build_misspelling_navigator_nodes(
        self,
        misspellings: list[Misspelling],
    ) -> list[_NavigatorNode]:
        text = self.editor.GetValue()
        nodes: list[_NavigatorNode] = []
        for item in misspellings:
            line, column = line_column_for_position(text, item.start)
            line_start = text.rfind("\n", 0, item.start) + 1
            line_end = text.find("\n", item.end)
            if line_end == -1:
                line_end = len(text)
            excerpt = text[line_start:line_end].strip() or item.word
            nodes.append(
                _NavigatorNode(
                    label=f"{item.word} (Ln {line}, Col {column})",
                    preview=f"Line {line}, Column {column}\n\n{excerpt}",
                    payload=item,
                    action_label="Jump to Occurrence",
                    children=[],
                )
            )
        return nodes

    def _show_tree_navigator(
        self,
        *,
        title: str,
        root_label: str,
        nodes: list[_NavigatorNode],
    ) -> object | None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title=title, size=(900, 620))
        splitter = wx.SplitterWindow(dialog, style=wx.SP_LIVE_UPDATE)
        tree = wx.TreeCtrl(splitter, style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT)
        preview = wx.TextCtrl(splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
        splitter.SplitVertically(tree, preview, 300)
        splitter.SetMinimumPaneSize(200)

        item_payloads: dict[object, object] = {}
        root = tree.AddRoot(root_label)

        def append_nodes(parent: object, children: list[_NavigatorNode]) -> object | None:
            first_item = None
            for node in children:
                item = tree.AppendItem(parent, node.label)
                item_payloads[item] = node.payload
                if first_item is None:
                    first_item = item
                append_nodes(item, node.children)
            return first_item

        first_item = append_nodes(root, nodes)
        tree.Expand(root)
        if first_item is not None:
            tree.SelectItem(first_item)
            preview.ChangeValue(nodes[0].preview)

        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        ok_button = None
        if buttons is not None:
            ok_button = buttons.FindWindowById(wx.ID_OK)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(splitter, 1, wx.EXPAND | wx.ALL, 8)
        if buttons is not None:
            layout.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        dialog.SetSizer(layout)

        node_by_payload: dict[object, _NavigatorNode] = {}

        def collect(children: list[_NavigatorNode]) -> None:
            for node in children:
                node_by_payload[node.payload] = node
                collect(node.children)

        collect(nodes)
        selected_payload = nodes[0].payload if nodes else None
        if ok_button is not None and nodes:
            ok_button.SetLabel(nodes[0].action_label)

        def on_select(event: object) -> None:
            nonlocal selected_payload
            item = event.GetItem()
            payload = item_payloads.get(item)
            if payload in node_by_payload:
                selected_payload = payload
                node = node_by_payload[payload]
                preview.ChangeValue(node.preview)
                if ok_button is not None:
                    ok_button.SetLabel(node.action_label)
            event.Skip()

        tree.Bind(wx.EVT_TREE_SEL_CHANGED, on_select)
        result = self._show_modal_dialog(dialog, title)
        if result != wx.ID_OK:
            return None
        return selected_payload

    def _jump_to(self, position: int, message: str) -> None:
        self._record_location_before_jump()
        self._move_point(position)
        self.editor.SetFocus()
        self._location_ring.record(position)
        self._set_status(message)

    def _record_location_before_jump(self) -> None:
        self._location_ring.record(self.editor.GetInsertionPoint())

    def set_bookmark(self) -> None:
        wx = self._wx
        default_name = f"Bookmark {len(self._bookmarks) + 1}"
        with wx.TextEntryDialog(
            self.frame,
            "Enter bookmark name (named jump point):",
            "Set Bookmark",
            value=default_name,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Set Bookmark") != wx.ID_OK:
                return
            name = dialog.GetValue().strip()
        if not name:
            self._set_status("Set bookmark cancelled")
            return
        position = self.editor.GetInsertionPoint()
        self._bookmarks = set_bookmark(self._bookmarks, name, position)
        self._set_status(f'Set bookmark "{name}"')

    def go_to_bookmark(self) -> None:
        wx = self._wx
        names = bookmark_names(self._bookmarks)
        if not names:
            self._set_status("No bookmarks available. Bookmarks are named jump points.")
            return
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose bookmark (named jump point):",
            "Go To Bookmark",
            choices=names,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Go To Bookmark") != wx.ID_OK:
                return
            name = dialog.GetStringSelection()
        target = bookmark_position(self._bookmarks, name)
        if target is None:
            self._set_status("Bookmark was not found")
            return
        self._move_point(target)
        self.editor.SetFocus()
        self._set_status(f'Jumped to bookmark "{name}"')

    def list_bookmarks(self) -> None:
        names = bookmark_names(self._bookmarks)
        if not names:
            self._set_status("No bookmarks available. Bookmarks are named jump points.")
            return
        text = self.editor.GetValue()
        nodes: list[_NavigatorNode] = []
        for name in names:
            position = self._bookmarks[name]
            line, column = line_column_for_position(text, position)
            nodes.append(
                _NavigatorNode(
                    label=f"{name} (Ln {line}, Col {column})",
                    preview=f"Bookmark: {name}\n\nLine {line}, Column {column}",
                    payload=name,
                    action_label="Jump to Bookmark",
                    children=[],
                )
            )
        selected = self._show_tree_navigator(
            title="List Bookmarks",
            root_label="Bookmarks (Named Jump Points)",
            nodes=nodes,
        )
        if not isinstance(selected, str):
            self._set_status("Bookmark list cancelled")
            return
        target = bookmark_position(self._bookmarks, selected)
        if target is None:
            self._set_status("Bookmark was not found")
            return
        self._move_point(target)
        self.editor.SetFocus()
        self._set_status(f'Jumped to bookmark "{selected}"')

    def show_word_count(self) -> None:
        wx = self._wx
        stats = compute_document_stats(self.editor.GetValue())
        message = f"Words: {stats.words}\nLines: {stats.lines}\nCharacters: {stats.characters}"
        self._show_message_box(message, "Word Count", wx.ICON_INFORMATION | wx.OK)
        self._set_status(f"Word count: {stats.words} words")

    def show_dictionary_status(self) -> None:
        wx = self._wx
        project_root = Path.cwd()
        personal_count = len(load_scope_dictionary("personal", self.document.path, project_root))
        document_count = len(load_scope_dictionary("document", self.document.path, project_root))
        project_count = len(load_scope_dictionary("project", self.document.path, project_root))
        personal_path = app_data_dir() / "dictionaries" / "personal.json"
        document_path = (
            self.document.path.with_suffix(self.document.path.suffix + ".quill-dict.json")
            if self.document.path is not None
            else None
        )
        project_path = project_root / ".quill-dictionary.json"
        backend = spellcheck_backend_info()
        thesaurus_status = "installed" if thesaurus_engine.is_available() else "not installed"
        if personal_path.exists():
            personal_line = f"- Personal: {personal_count} (stored at {personal_path})"
        else:
            personal_line = (
                f"- Personal: {personal_count} "
                f"(not created yet; add a word to create {personal_path})"
            )
        if document_path is None:
            document_line = (
                f"- Document: {document_count} (not available until the current document is saved)"
            )
        elif document_path.exists():
            document_line = f"- Document: {document_count} (stored at {document_path})"
        else:
            document_line = (
                f"- Document: {document_count} (not created yet for this document: {document_path})"
            )
        if project_path.exists():
            project_line = f"- Project: {project_count} (stored at {project_path})"
        else:
            project_line = (
                f"- Project: {project_count} (not created yet in this folder: {project_path})"
            )
        lines = [
            f"Spell-check backend: {backend.name} — {backend.detail}",
            f"Thesaurus data: {thesaurus_status} ({thesaurus_engine.data_path()})",
            "",
            "User dictionary entries:",
            personal_line,
            document_line,
            project_line,
        ]
        self._show_message_box("\n".join(lines), "Dictionary Status", wx.ICON_INFORMATION | wx.OK)
        self._set_status(
            f"Spell check: {backend.name}; user dictionaries: personal={personal_count}, "
            f"document={document_count}, project={project_count}"
        )

    def open_spell_check_dialog(self) -> None:
        wx = self._wx
        dictionary = self._spell_dictionary()
        text = self.editor.GetValue()
        misspellings = list_misspellings(text, dictionary)
        if not misspellings:
            self._set_status("No misspellings found")
            return
        selection = self._choose_misspelling_with_context(misspellings, text, dictionary)
        if selection == wx.NOT_FOUND:
            return
        item = misspellings[selection]
        suggestions = suggest_words(item.word, dictionary)
        if suggestions:
            with wx.SingleChoiceDialog(
                self.frame,
                f'Suggestions for "{item.word}":',
                "Spell Check",
                choices=suggestions,
            ) as suggestion_dialog:
                if self._show_modal_dialog(suggestion_dialog, "Spell Check") == wx.ID_OK:
                    replacement = suggestion_dialog.GetStringSelection()
                    if replacement:
                        self.editor.Replace(item.start, item.end, replacement)
                        self.document.set_text(self.editor.GetValue())
                        self._set_status(f'Replaced "{item.word}" with "{replacement}"')
                        return
        else:
            # Announce explicitly so screen-reader users aren't surprised
            # when the dialog jumps straight to "Add to dictionary".
            self._set_status(f'No suggestions for "{item.word}"')
            self._announce(f"No suggestions for {item.word}")
        scopes = ["Personal dictionary", "Document dictionary", "Project dictionary"]
        with wx.SingleChoiceDialog(
            self.frame,
            f'No suggestions found. Add "{item.word}" to dictionary scope?'
            if not suggestions
            else f'Add "{item.word}" to dictionary scope:',
            "Spell Check",
            choices=scopes,
        ) as scope_dialog:
            if self._show_modal_dialog(scope_dialog, "Spell Check") != wx.ID_OK:
                self._set_status("Spell check reviewed")
                return
            scope = scope_dialog.GetSelection()
        if scope == wx.NOT_FOUND:
            self._set_status("Spell check reviewed")
            return
        self._add_word_to_dictionary_scope(item.word, scope)

    def _choose_misspelling_with_context(
        self,
        misspellings: list[Misspelling],
        text: str,
        dictionary: set[str],
    ) -> int:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Spell Check", size=(860, 520))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Choose misspelled word. Tab to Context to read the nearby sentence before "
                    "continuing. Use Speak Word to hear the word and spelling."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        choices = []
        for item in misspellings:
            line, column = line_column_for_position(text, item.start)
            choices.append(f"{item.word} (Ln {line}, Col {column})")
        chooser = wx.ListBox(panel, choices=choices)
        chooser.SetSelection(0 if choices else wx.NOT_FOUND)
        root.Add(chooser, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 8)
        root.Add(wx.StaticText(panel, label="Context"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        context_field = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
        )
        root.Add(context_field, 1, wx.ALL | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        speak_button = wx.Button(panel, label="Speak Word")
        review_button = wx.Button(panel, id=wx.ID_OK, label="Review Word")
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")
        buttons.Add(speak_button, 0, wx.RIGHT, 8)
        buttons.Add(review_button, 0, wx.RIGHT, 8)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)

        def refresh_context() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                context_field.SetValue("")
                return
            item = misspellings[selection]
            context_field.SetValue(self._misspelling_context_text(text, item))

        chooser.Bind(wx.EVT_LISTBOX, lambda _event: refresh_context())
        speak_button.Bind(
            wx.EVT_BUTTON,
            lambda _event: (
                self._speak_spellcheck_word(
                    misspellings[chooser.GetSelection()].word,
                    suggest_words(misspellings[chooser.GetSelection()].word, dictionary),
                )
                if chooser.GetSelection() != wx.NOT_FOUND
                else self._set_status("Select a misspelling to speak")
            ),
        )
        review_button.Bind(wx.EVT_BUTTON, lambda _event: dialog.EndModal(wx.ID_OK))
        cancel_button.Bind(wx.EVT_BUTTON, lambda _event: dialog.EndModal(wx.ID_CANCEL))
        refresh_context()
        result = self._show_modal_dialog(dialog, "Spell Check")
        selection = chooser.GetSelection()
        dialog.Destroy()
        if result != wx.ID_OK:
            return wx.NOT_FOUND
        return selection

    def _misspelling_context_text(self, text: str, item: Misspelling) -> str:
        if not text:
            return item.word
        boundaries = ".!?\n"
        start = item.start
        end = item.end
        sentence_start = 0
        for marker in boundaries:
            position = text.rfind(marker, 0, start)
            if position > sentence_start:
                sentence_start = position
        if sentence_start > 0:
            sentence_start += 1
        sentence_end = len(text)
        for marker in boundaries:
            position = text.find(marker, end)
            if position != -1:
                sentence_end = min(sentence_end, position + 1)
        sentence = text[sentence_start:sentence_end].strip()
        if not sentence:
            window = 80
            excerpt_start = max(0, start - window)
            excerpt_end = min(len(text), end + window)
            sentence = text[excerpt_start:excerpt_end].strip()
            if excerpt_start > 0:
                sentence = f"...{sentence}"
            if excerpt_end < len(text):
                sentence = f"{sentence}..."
        return sentence or item.word

    def _speak_spellcheck_word(self, word: str, suggestions: list[str]) -> None:
        single_suggestion = suggestions[0] if len(suggestions) == 1 else None
        message = self._spellcheck_speech_message(word, single_suggestion)
        self._speak_with_announcement_backend(message)
        if single_suggestion is None:
            self._set_status(f'Spoke misspelling "{word}" and spelling')
        else:
            self._set_status(
                f'Spoke misspelling "{word}" and single suggestion "{single_suggestion}"'
            )

    def _spellcheck_speech_message(self, word: str, single_suggestion: str | None = None) -> str:
        parts = [
            f'Misspelled word: "{word}".',
            f"Spelling: {self._spell_word_for_speech(word)}.",
        ]
        if single_suggestion is not None:
            parts.append(f'Only suggestion: "{single_suggestion}".')
            parts.append(f"Suggestion spelling: {self._spell_word_for_speech(single_suggestion)}.")
        return " ".join(parts)

    def _spell_word_for_speech(self, word: str) -> str:
        if not word:
            return "empty"
        spoken_letters: list[str] = []
        for character in word:
            if character == "-":
                spoken_letters.append("dash")
            elif character == "_":
                spoken_letters.append("underscore")
            elif character == "'":
                spoken_letters.append("apostrophe")
            elif character.isspace():
                spoken_letters.append("space")
            else:
                spoken_letters.append(character.upper())
        return ", ".join(spoken_letters)

    def _speak_with_announcement_backend(self, message: str) -> None:
        backend = getattr(self, "_announcement_engine", None)
        if backend is not None:
            backend_error = backend.announce(message)
            if backend_error and backend_error != self._announcement_error_reported:
                self._announcement_error_reported = backend_error
                self._record_notification(backend_error, "accessibility")
            if backend_error is None and backend.state().active_backend in {"prism", "speech"}:
                return
        announce(message)

    def open_misspelling_list(self) -> None:
        dictionary = self._spell_dictionary()
        misspellings = list_misspellings(self.editor.GetValue(), dictionary)
        if not misspellings:
            self._set_status("No misspellings found")
            return
        nodes = self._build_misspelling_navigator_nodes(misspellings)
        selected = self._show_tree_navigator(
            title="Misspelling List",
            root_label="Misspellings",
            nodes=nodes,
        )
        if not isinstance(selected, Misspelling):
            self._set_status("Misspelling list cancelled")
            return
        self._record_location_before_jump()
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._move_point(selected.start)
        else:
            self.editor.SetInsertionPoint(selected.start)
            self.editor.SetSelection(selected.start, selected.end)
        self.editor.SetFocus()
        self._location_ring.record(selected.start)
        self._set_status(f'Jumped to misspelling "{selected.word}"')

    def next_misspelling(self) -> None:
        dictionary = self._spell_dictionary()
        cursor = self.editor.GetInsertionPoint()
        item = find_next_misspelling(self.editor.GetValue(), cursor, dictionary)
        if item is None:
            self._set_status("No next misspelling")
            return
        self._record_location_before_jump()
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._move_point(item.start)
        else:
            self.editor.SetInsertionPoint(item.start)
            self.editor.SetSelection(item.start, item.end)
        self.editor.SetFocus()
        self._set_status(f'Next misspelling: "{item.word}"')

    def previous_misspelling(self) -> None:
        dictionary = self._spell_dictionary()
        cursor = self.editor.GetInsertionPoint()
        item = find_previous_misspelling(self.editor.GetValue(), cursor, dictionary)
        if item is None:
            self._set_status("No previous misspelling")
            return
        self._record_location_before_jump()
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._move_point(item.start)
        else:
            self.editor.SetInsertionPoint(item.start)
            self.editor.SetSelection(item.start, item.end)
        self.editor.SetFocus()
        self._set_status(f'Previous misspelling: "{item.word}"')

    def show_thesaurus(self) -> None:
        """Open the thesaurus for the selected word or the word under the caret."""
        wx = self._wx
        if not thesaurus_engine.is_available():
            message = (
                "The thesaurus data file is not installed.\n\n"
                f"Expected location:\n  {thesaurus_engine.data_path()}\n\n"
                "To enable the thesaurus, install the optional English thesaurus "
                "data file (LibreOffice MyThes en_US, ~18 MB). Reinstall Quill "
                "with the thesaurus component, or copy 'th_en_US_v2.dat' into "
                "the data folder shown above."
            )
            self._show_message_box(message, "Thesaurus Not Installed", wx.ICON_INFORMATION | wx.OK)
            self._set_status("Thesaurus data not installed")
            return

        # Determine the word to look up: selection takes priority, else the
        # word at the caret.
        text = self.editor.GetValue()
        sel_start, sel_end = self.editor.GetSelection()
        word: str | None = None
        word_start: int | None = None
        word_end: int | None = None
        if sel_end > sel_start:
            candidate = text[sel_start:sel_end].strip()
            if candidate and all(ch.isalpha() or ch == "'" for ch in candidate):
                word = candidate
                word_start = sel_start
                word_end = sel_end
        if word is None:
            located = thesaurus_engine.word_at(text, self.editor.GetInsertionPoint())
            if located is not None:
                word, word_start, word_end = located

        if not word:
            with wx.TextEntryDialog(
                self.frame,
                "Look up word in thesaurus:",
                "Thesaurus",
                value="",
            ) as dialog:
                if self._show_modal_dialog(dialog, "Thesaurus") != wx.ID_OK:
                    return
                word = dialog.GetValue().strip()
                if not word:
                    self._set_status("Thesaurus: no word entered")
                    return

        entry = thesaurus_engine.lookup(word)
        if entry is None:
            self._set_status(f'No thesaurus entry for "{word}"')
            self._show_message_box(
                f'No thesaurus entries were found for "{word}".',
                "Thesaurus",
                wx.ICON_INFORMATION | wx.OK,
            )
            return

        # Build a flat choice list grouped by part of speech so screen
        # readers announce the grouping naturally.
        choices: list[str] = []
        choice_words: list[str] = []
        for meaning in entry.meanings:
            pos = meaning.part_of_speech or "other"
            for synonym in meaning.synonyms:
                choices.append(f"[{pos}] {synonym}")
                choice_words.append(synonym)

        if not choices:
            self._set_status(f'No synonyms available for "{word}"')
            return

        replace_allowed = word_start is not None and word_end is not None
        prompt = f'Synonyms for "{word}":\n\nChoose one to copy to the clipboard' + (
            " or replace the word in the editor." if replace_allowed else "."
        )

        with wx.SingleChoiceDialog(
            self.frame,
            prompt,
            "Thesaurus",
            choices=choices,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Thesaurus") != wx.ID_OK:
                self._set_status("Thesaurus closed")
                return
            selection = dialog.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        chosen = choice_words[selection]

        if replace_allowed:
            actions = ["Replace word in editor", "Copy to clipboard"]
            with wx.SingleChoiceDialog(
                self.frame,
                f'Use "{chosen}":',
                "Thesaurus",
                choices=actions,
            ) as action_dialog:
                if self._show_modal_dialog(action_dialog, "Thesaurus") != wx.ID_OK:
                    return
                action = action_dialog.GetSelection()
        else:
            action = 1  # copy to clipboard

        if action == 0 and replace_allowed:
            # Preserve the original word's leading capitalisation.
            replacement = chosen
            if word[:1].isupper():
                replacement = chosen[:1].upper() + chosen[1:]
            self.editor.Replace(word_start, word_end, replacement)
            self.document.set_text(self.editor.GetValue())
            self._set_status(f'Replaced "{word}" with "{replacement}"')
        else:
            self._copy_text_to_clipboard(chosen)
            self._set_status(f'Copied "{chosen}" to clipboard')

    def _copy_text_to_clipboard(self, text: str) -> bool:
        wx = self._wx
        clipboard = wx.TheClipboard
        if not clipboard.Open():
            self._set_status("Clipboard is unavailable")
            return False
        try:
            clipboard.SetData(wx.TextDataObject(text))
            # Flush so the data survives if the app exits soon after.
            try:
                clipboard.Flush()
            except Exception:
                pass
            return True
        finally:
            clipboard.Close()

    def _announce_spellcheck_hint(self) -> None:
        dictionary = self._spell_dictionary()
        cursor = self.editor.GetInsertionPoint()
        item = find_next_misspelling(self.editor.GetValue(), cursor - 1, dictionary)
        if item is None or item.start != cursor:
            self._last_live_misspelling_feedback = None
            return
        key = (item.word.lower(), item.start, item.end)
        now = time.monotonic()
        if (
            self._last_live_misspelling_feedback == key
            and now - self._last_live_misspelling_feedback_at < 0.75
        ):
            return
        self._last_live_misspelling_feedback = key
        self._last_live_misspelling_feedback_at = now
        bell = getattr(self._wx, "Bell", None)
        if callable(bell):
            bell()
        self._set_status(f'Possible misspelling: "{item.word}"')

    def _spell_dictionary(self) -> set[str]:
        # Cache the combined dictionary keyed by (document path, project root).
        # Reading + parsing the three JSON scope files on every keystroke (via
        # "spell check as you type") is wasteful; we invalidate the cache when
        # a word is added or the active document changes.
        project_root = Path.cwd()
        cache_key = (self.document.path, project_root)
        cached = getattr(self, "_spell_dictionary_cache", None)
        if cached is not None and cached[0] == cache_key:
            return cached[1]
        dictionary = load_combined_dictionary(self.document.path, project_root)
        self._spell_dictionary_cache = (cache_key, dictionary)
        return dictionary

    def _invalidate_spell_dictionary_cache(self) -> None:
        self._spell_dictionary_cache = None

    def _add_word_to_dictionary_scope(self, word: str, scope_index: int) -> None:
        if scope_index == 0:
            add_word_to_scope(word, "personal", self.document.path, Path.cwd())
        elif scope_index == 1:
            add_word_to_scope(word, "document", self.document.path, Path.cwd())
        elif scope_index == 2:
            add_word_to_scope(word, "project", self.document.path, Path.cwd())
        else:
            return
        self._invalidate_spell_dictionary_cache()
        self._set_status(f'Added "{word}" to dictionary')

    def open_epub_navigator(self) -> None:
        if self.document.path is None or self.document.path.suffix.lower() != ".epub":
            self._set_status("Open an EPUB file to use EPUB Navigator")
            return
        from quill.core.epub import load_epub_book

        book = self._epub_book or load_epub_book(self.document.path)
        nodes = self._build_epub_navigator_nodes(book)
        if not nodes:
            self._set_status("EPUB has no navigable chapters")
            return
        selected = self._show_tree_navigator(
            title=f"Navigator - {book.title}",
            root_label=book.title,
            nodes=nodes,
        )
        if not isinstance(selected, _EpubNavigatorTarget):
            self._set_status("Closed EPUB Navigator")
            return
        chapter_index = selected.chapter_index
        if chapter_index < 0 or chapter_index >= len(book.chapters):
            self._set_status("Closed EPUB Navigator")
            return
        chapter = book.chapters[chapter_index]
        chapter_text = self._render_epub_chapter_text(chapter)
        self._create_document_tab(
            Document(text=chapter_text, path=None, modified=False),
            select=True,
        )
        target_position = 0
        status = f'Opened chapter "{chapter.title}" from EPUB navigator'
        if selected.heading_index is not None and 0 <= selected.heading_index < len(
            chapter.headings
        ):
            heading = chapter.headings[selected.heading_index]
            target_position = self._find_heading_position(
                chapter_text,
                heading.title,
                selected.heading_index,
            )
            status = f'Jumped to heading "{heading.title}" in chapter "{chapter.title}"'
        self.editor.SetInsertionPoint(target_position)
        self.editor.SetSelection(target_position, target_position)
        self.editor.SetFocus()
        self._refresh_title()
        self._set_status(status)

    def _find_heading_position(
        self,
        chapter_text: str,
        heading_title: str,
        heading_index: int,
    ) -> int:
        occurrences = 0
        search_from = 0
        while True:
            position = chapter_text.find(heading_title, search_from)
            if position == -1:
                return 0
            if occurrences == heading_index:
                return position
            occurrences += 1
            search_from = position + len(heading_title)

    def toggle_read_aloud(self) -> None:
        wx = self._wx
        state = self._read_aloud.state
        if state == "playing":
            self._read_aloud.pause()
            self._set_status("Read aloud paused")
            return
        text = self.editor.GetValue()
        if state == "paused":
            start = self._read_aloud.cursor
            end = None
        else:
            start, end = self.editor.GetSelection()
            if start == end:
                start = self.editor.GetInsertionPoint()
                end = None
        try:
            read_aloud_engine = self.settings.read_aloud_engine.strip().lower() or "pyttsx3"
            self._read_aloud.start(
                text,
                start,
                self.settings.read_aloud_voice,
                engine_name=read_aloud_engine,
                rate=self.settings.read_aloud_rate,
                volume=self.settings.read_aloud_volume / 100.0,
                pitch=self.settings.read_aloud_pitch,
                dectalk_executable=self.settings.read_aloud_dectalk_executable,
                dectalk_voice=self.settings.read_aloud_dectalk_voice,
                dectalk_rate=self.settings.read_aloud_dectalk_rate,
                dectalk_dictionary=self.settings.read_aloud_dectalk_dictionary,
                end=end,
                piper_executable=self.settings.read_aloud_piper_executable,
                piper_model=self.settings.read_aloud_piper_model,
                kokoro_voice=self.settings.read_aloud_kokoro_voice,
                kokoro_speed=self.settings.read_aloud_kokoro_speed,
                vibevoice_executable=self.settings.read_aloud_vibevoice_executable,
                vibevoice_voice=self.settings.read_aloud_vibevoice_voice,
                espeak_executable=self.settings.read_aloud_espeak_executable,
                espeak_voice=self.settings.read_aloud_espeak_voice,
                espeak_rate=self.settings.read_aloud_espeak_rate,
                rhvoice_executable=self.settings.read_aloud_rhvoice_executable,
                rhvoice_voice=self.settings.read_aloud_rhvoice_voice,
                rhvoice_rate=self.settings.read_aloud_rhvoice_rate,
                melotts_executable=self.settings.read_aloud_melotts_executable,
                melotts_voice=self.settings.read_aloud_melotts_voice,
                melotts_rate=self.settings.read_aloud_melotts_rate,
                chatterbox_executable=self.settings.read_aloud_chatterbox_executable,
                chatterbox_voice=self.settings.read_aloud_chatterbox_voice,
                chatterbox_rate=self.settings.read_aloud_chatterbox_rate,
                openvoice_executable=self.settings.read_aloud_openvoice_executable,
                openvoice_voice=self.settings.read_aloud_openvoice_voice,
                openvoice_rate=self.settings.read_aloud_openvoice_rate,
                openvoice_consent=self.settings.read_aloud_openvoice_consent,
                on_progress=lambda progress_start, progress_end: self._wx.CallAfter(
                    self._on_read_aloud_progress,
                    progress_start,
                    progress_end,
                ),
                on_state_change=lambda next_state: self._wx.CallAfter(
                    self._on_read_aloud_state_change,
                    next_state,
                ),
                on_error=lambda error: self._wx.CallAfter(self._on_read_aloud_error, error),
            )
        except ReadAloudUnavailableError as exc:
            self._show_message_box(
                str(exc),
                "Read Aloud",
                wx.ICON_INFORMATION | wx.OK,
            )
            return
        self._set_status("Read aloud started")

    def stop_read_aloud(self) -> None:
        self._read_aloud.stop()
        self._set_status("Read aloud stopped")

    def _voice_is_english(self, engine: str, voice: VoiceOption) -> bool:
        engine_name = (engine or "").strip().lower()
        voice_id = (voice.id or "").strip().lower()
        voice_name = (voice.name or "").strip().lower()

        if engine_name in {
            "dectalk",
            "kokoro",
            "espeak",
            "rhvoice",
            "melotts",
            "chatterbox",
            "openvoice",
        }:
            return True

        if engine_name == "pyttsx3":
            english_markers = ("english", "en-", " en", "_en", "en_us", "en_gb", "enu")
            return any(marker in voice_id or marker in voice_name for marker in english_markers)

        if engine_name == "piper":
            return (
                "en" in voice_id
                or "english" in voice_id
                or "en" in voice_name
                or "english" in voice_name
            )

        if engine_name == "vibevoice":
            if voice_id == "default":
                return True
            return "en" in voice_id or "english" in voice_name

        return True

    def _english_only_voices(self, engine: str, voices: list[VoiceOption]) -> list[VoiceOption]:
        return [voice for voice in voices if self._voice_is_english(engine, voice)]

    # ------------------------------------------------------------------
    # Voice preview and settings – all 6 engines
    # ------------------------------------------------------------------

    _PREVIEW_TEXT = "Hello, this is a voice preview. The quick brown fox jumps over the lazy dog."

    def _preview_voice(self, engine: str, voice_id: str) -> None:
        """Play a short preview of *voice_id* through *engine* on a background thread."""
        import tempfile as _tmpfile
        from pathlib import Path as _Path

        sample = self._PREVIEW_TEXT
        s = self.settings

        def _work(_progress: Callable[[str, int, int], None]) -> object:
            with _tmpfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
                wav = _Path(fh.name)
            try:
                if engine == "pyttsx3":
                    synthesize_to_file_with_pyttsx3(
                        sample,
                        wav,
                        voice=voice_id,
                        rate=s.read_aloud_rate,
                        volume=s.read_aloud_volume / 100.0,
                    )
                elif engine == "dectalk":
                    exe = discover_dectalk_executable(s.read_aloud_dectalk_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("DECtalk executable not configured")
                    synthesize_to_file_with_dectalk(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_dectalk_rate,
                    )
                elif engine == "piper":
                    exe = discover_piper_executable(s.read_aloud_piper_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("Piper executable not configured")
                    synthesize_with_piper(
                        sample,
                        wav,
                        executable_path=exe,
                        model_path=_Path(voice_id),
                    )
                elif engine == "kokoro":
                    synthesize_with_kokoro(
                        sample,
                        wav,
                        voice=voice_id,
                        speed=s.read_aloud_kokoro_speed,
                    )
                elif engine == "vibevoice":
                    exe = discover_vibevoice_executable(s.read_aloud_vibevoice_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("VibeVoice executable not configured")
                    synthesize_with_vibevoice(sample, wav, executable_path=exe, voice=voice_id)
                elif engine == "espeak":
                    exe = discover_espeak_executable(s.read_aloud_espeak_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("eSpeak-NG not found")
                    synthesize_with_espeak(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_espeak_rate,
                    )
                elif engine == "rhvoice":
                    exe = discover_rhvoice_executable(s.read_aloud_rhvoice_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("RHVoice executable not configured")
                    synthesize_with_rhvoice(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_rhvoice_rate,
                    )
                elif engine == "melotts":
                    exe = discover_melotts_executable(s.read_aloud_melotts_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("MeloTTS executable not configured")
                    synthesize_with_melotts(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_melotts_rate,
                    )
                elif engine == "chatterbox":
                    exe = discover_chatterbox_executable(s.read_aloud_chatterbox_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("Chatterbox executable not configured")
                    synthesize_with_chatterbox(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_chatterbox_rate,
                    )
                elif engine == "openvoice":
                    if not s.read_aloud_openvoice_consent:
                        raise ReadAloudUnavailableError(
                            "OpenVoice requires explicit consent in Read Aloud Settings"
                        )
                    exe = discover_openvoice_executable(s.read_aloud_openvoice_executable)
                    if exe is None:
                        raise ReadAloudUnavailableError("OpenVoice executable not configured")
                    synthesize_with_openvoice(
                        sample,
                        wav,
                        executable_path=exe,
                        voice=voice_id,
                        rate=s.read_aloud_openvoice_rate,
                    )
                else:
                    raise ReadAloudUnavailableError(f"Unknown engine: {engine}")
                # Play via the existing read-aloud controller so pause/stop work
                import threading as _threading

                done = _threading.Event()

                def _on_state(st: str) -> None:
                    if st in ("idle", "error"):
                        done.set()

                self._read_aloud.start(
                    sample,
                    0,
                    voice_id,
                    engine_name=engine,
                    dectalk_executable=s.read_aloud_dectalk_executable,
                    dectalk_voice=voice_id if engine == "dectalk" else s.read_aloud_dectalk_voice,
                    dectalk_rate=s.read_aloud_dectalk_rate,
                    dectalk_dictionary=s.read_aloud_dectalk_dictionary,
                    piper_executable=s.read_aloud_piper_executable,
                    piper_model=voice_id if engine == "piper" else s.read_aloud_piper_model,
                    kokoro_voice=voice_id if engine == "kokoro" else s.read_aloud_kokoro_voice,
                    kokoro_speed=s.read_aloud_kokoro_speed,
                    vibevoice_executable=s.read_aloud_vibevoice_executable,
                    vibevoice_voice=voice_id
                    if engine == "vibevoice"
                    else s.read_aloud_vibevoice_voice,
                    espeak_executable=s.read_aloud_espeak_executable,
                    espeak_voice=voice_id if engine == "espeak" else s.read_aloud_espeak_voice,
                    espeak_rate=s.read_aloud_espeak_rate,
                    rhvoice_executable=s.read_aloud_rhvoice_executable,
                    rhvoice_voice=voice_id if engine == "rhvoice" else s.read_aloud_rhvoice_voice,
                    rhvoice_rate=s.read_aloud_rhvoice_rate,
                    melotts_executable=s.read_aloud_melotts_executable,
                    melotts_voice=voice_id if engine == "melotts" else s.read_aloud_melotts_voice,
                    melotts_rate=s.read_aloud_melotts_rate,
                    chatterbox_executable=s.read_aloud_chatterbox_executable,
                    chatterbox_voice=voice_id
                    if engine == "chatterbox"
                    else s.read_aloud_chatterbox_voice,
                    chatterbox_rate=s.read_aloud_chatterbox_rate,
                    openvoice_executable=s.read_aloud_openvoice_executable,
                    openvoice_voice=voice_id
                    if engine == "openvoice"
                    else s.read_aloud_openvoice_voice,
                    openvoice_rate=s.read_aloud_openvoice_rate,
                    openvoice_consent=s.read_aloud_openvoice_consent,
                    on_state_change=lambda st: done.set() if st in ("idle", "error") else None,
                )
                done.wait(timeout=15)
            finally:
                try:
                    wav.unlink(missing_ok=True)
                except OSError:
                    pass
            return None

        self._run_background_task(
            f"Previewing {engine} voice",
            _work,
            lambda _r: self._set_status("Preview finished"),
        )

    def choose_read_aloud_voice(self) -> None:  # noqa: PLR0912
        wx = self._wx
        engine = self.settings.read_aloud_engine.strip().lower() or "pyttsx3"

        if engine == "dectalk":
            voices = list_dectalk_voices()
            current_voice_id = self.settings.read_aloud_dectalk_voice
        elif engine == "piper":
            voices = list_piper_voices(self.settings.read_aloud_piper_model_dir)
            current_voice_id = self.settings.read_aloud_piper_model
        elif engine == "kokoro":
            voices = list_kokoro_voices()
            current_voice_id = self.settings.read_aloud_kokoro_voice
        elif engine == "vibevoice":
            voices = list_vibevoice_voices(self.settings.read_aloud_vibevoice_executable)
            current_voice_id = self.settings.read_aloud_vibevoice_voice
        elif engine == "espeak":
            voices = list_espeak_english_voices()
            current_voice_id = self.settings.read_aloud_espeak_voice
        elif engine == "rhvoice":
            voices = list_rhvoice_english_voices()
            current_voice_id = self.settings.read_aloud_rhvoice_voice
        elif engine == "melotts":
            voices = list_melotts_english_voices()
            current_voice_id = self.settings.read_aloud_melotts_voice
        elif engine == "chatterbox":
            voices = list_chatterbox_english_voices()
            current_voice_id = self.settings.read_aloud_chatterbox_voice
        elif engine == "openvoice":
            voices = list_openvoice_english_voices()
            current_voice_id = self.settings.read_aloud_openvoice_voice
        else:
            voices = list_voices()
            current_voice_id = self.settings.read_aloud_voice

        voices = self._english_only_voices(engine, voices)

        if not voices:
            self._show_message_box(
                "No English voices were found for this engine.",
                "Read Aloud Voice",
                wx.ICON_INFORMATION | wx.OK,
            )
            return

        dialog = wx.Dialog(self.frame, title="Read Aloud Voice", size=(640, 460))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=f"Choose an English voice for {engine}. Use Preview before confirming.",
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            8,
        )
        choices = [v.name for v in voices]
        list_box = wx.ListBox(panel, choices=choices, style=wx.LB_SINGLE)
        current_index = next((i for i, v in enumerate(voices) if v.id == current_voice_id), 0)
        if choices:
            list_box.SetSelection(current_index)
        root.Add(list_box, 1, wx.EXPAND | wx.ALL, 8)
        button_row = wx.BoxSizer(wx.HORIZONTAL)
        preview_btn = wx.Button(panel, label="&Preview")
        ok_btn = wx.Button(panel, id=wx.ID_OK)
        cancel_btn = wx.Button(panel, id=wx.ID_CANCEL)
        button_row.Add(preview_btn, 0, wx.RIGHT, 8)
        button_row.Add(ok_btn, 0, wx.RIGHT, 8)
        button_row.Add(cancel_btn, 0)
        root.Add(button_row, 0, wx.ALIGN_RIGHT | wx.ALL, 8)
        panel.SetSizer(root)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        dialog.SetSizerAndFit(outer)

        def _selected_index() -> int:
            return list_box.GetSelection()

        def _on_preview(_evt: wx.CommandEvent) -> None:
            idx = _selected_index()
            if 0 <= idx < len(voices):
                self._preview_voice(engine, voices[idx].id)

        preview_btn.Bind(wx.EVT_BUTTON, _on_preview)
        try:
            if self._show_modal_dialog(dialog, "Read Aloud Voice") != wx.ID_OK:
                self._set_status("Read aloud voice selection cancelled")
                return
            selected = _selected_index()
        finally:
            dialog.Destroy()

        if selected < 0 or selected >= len(voices):
            return
        if engine == "dectalk":
            self.settings.read_aloud_dectalk_voice = voices[selected].id
        elif engine == "piper":
            self.settings.read_aloud_piper_model = voices[selected].id
        elif engine == "kokoro":
            self.settings.read_aloud_kokoro_voice = voices[selected].id
        elif engine == "vibevoice":
            self.settings.read_aloud_vibevoice_voice = voices[selected].id
        elif engine == "espeak":
            self.settings.read_aloud_espeak_voice = voices[selected].id
        elif engine == "rhvoice":
            self.settings.read_aloud_rhvoice_voice = voices[selected].id
        elif engine == "melotts":
            self.settings.read_aloud_melotts_voice = voices[selected].id
        elif engine == "chatterbox":
            self.settings.read_aloud_chatterbox_voice = voices[selected].id
        elif engine == "openvoice":
            self.settings.read_aloud_openvoice_voice = voices[selected].id
        else:
            self.settings.read_aloud_voice = voices[selected].id
        save_settings(self.settings)
        self._set_status(f"Selected voice: {voices[selected].name}")

    def choose_read_aloud_settings(self) -> None:  # noqa: PLR0912,PLR0915
        wx = self._wx
        _TITLE = "Read Aloud Settings"
        engine_choices = [
            "Pyttsx3 (System TTS)",
            "DECtalk",
            "Piper (neural, offline)",
            "Kokoro (neural, offline)",
            "eSpeak-NG (English variants)",
            "RHVoice (accessibility-focused, offline)",
            "MeloTTS (multilingual add-on, English mode)",
            "Chatterbox (high-fidelity read/export)",
            "OpenVoice (advanced style module)",
        ]
        # NOTE: VibeVoice is intentionally NOT a read-aloud engine — it's an
        # offline "generate a speech file" tool (see vibevoice-cpu), not a live
        # voice. It's exposed as a file-export action, never in this picker.
        engine_values = [
            "pyttsx3",
            "dectalk",
            "piper",
            "kokoro",
            "espeak",
            "rhvoice",
            "melotts",
            "chatterbox",
            "openvoice",
        ]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose read-aloud engine:",
            _TITLE,
            choices=engine_choices,
        ) as engine_dialog:
            current_engine = self.settings.read_aloud_engine.strip().lower() or "pyttsx3"
            current_index = (
                engine_values.index(current_engine) if current_engine in engine_values else 0
            )
            engine_dialog.SetSelection(current_index)
            if self._show_modal_dialog(engine_dialog, _TITLE) != wx.ID_OK:
                self._set_status("Read aloud settings cancelled")
                return
            selected_engine = engine_values[engine_dialog.GetSelection()]
        self.settings.read_aloud_engine = selected_engine

        def _ask_text(prompt: str, current: str) -> str | None:
            with wx.TextEntryDialog(self.frame, prompt, _TITLE, value=current) as d:
                if self._show_modal_dialog(d, _TITLE) != wx.ID_OK:
                    return None
                return d.GetValue().strip()

        def _ask_int(prompt: str, current: int, lo: int, hi: int) -> int | None:
            val = _ask_text(f"{prompt} ({lo}–{hi}):", str(current))
            if val is None:
                return None
            try:
                return max(lo, min(hi, int(val)))
            except ValueError:
                return current

        def _ask_float(prompt: str, current: float, lo: float, hi: float) -> float | None:
            val = _ask_text(f"{prompt} ({lo:.1f}–{hi:.1f}):", f"{current:.2f}")
            if val is None:
                return None
            try:
                return max(lo, min(hi, float(val)))
            except ValueError:
                return current

        # ---- per-engine settings ----
        if selected_engine == "pyttsx3":
            v = _ask_int("Speaking rate (words per minute)", self.settings.read_aloud_rate, 80, 450)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_rate = v
            v2 = _ask_int("Volume (0–100)", self.settings.read_aloud_volume, 0, 100)
            if v2 is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_volume = v2
            v3 = _ask_int("Pitch (0–100)", self.settings.read_aloud_pitch, 0, 100)
            if v3 is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_pitch = v3

        elif selected_engine == "dectalk":
            exe = _ask_text(
                "Path to DECtalk speak.exe:", self.settings.read_aloud_dectalk_executable
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_dectalk_executable = exe
            dic = _ask_text(
                "Optional path to dtalk_us.dic (leave blank to auto-detect):",
                self.settings.read_aloud_dectalk_dictionary,
            )
            if dic is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_dectalk_dictionary = dic
            v = _ask_int("Speaking rate", self.settings.read_aloud_dectalk_rate, 75, 650)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_dectalk_rate = v

        elif selected_engine == "piper":
            exe = _ask_text("Path to piper.exe:", self.settings.read_aloud_piper_executable)
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_piper_executable = exe
            model_dir = _ask_text(
                "Directory containing Piper .onnx model files (for voice list):",
                self.settings.read_aloud_piper_model_dir,
            )
            if model_dir is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_piper_model_dir = model_dir

        elif selected_engine == "kokoro":
            v = _ask_float(
                "Speaking speed multiplier", self.settings.read_aloud_kokoro_speed, 0.5, 2.0
            )
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_kokoro_speed = v

        elif selected_engine == "vibevoice":
            exe = _ask_text("Path to vibevoice.exe:", self.settings.read_aloud_vibevoice_executable)
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_vibevoice_executable = exe

        elif selected_engine == "espeak":
            exe = _ask_text(
                "Path to espeak-ng.exe (leave blank to use PATH):",
                self.settings.read_aloud_espeak_executable,
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_espeak_executable = exe
            v = _ask_int(
                "Speaking rate (words per minute)", self.settings.read_aloud_espeak_rate, 80, 450
            )
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_espeak_rate = v

        elif selected_engine == "rhvoice":
            exe = _ask_text(
                "Path to RHVoice executable:", self.settings.read_aloud_rhvoice_executable
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_rhvoice_executable = exe
            v = _ask_int("Speaking rate", self.settings.read_aloud_rhvoice_rate, 80, 450)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_rhvoice_rate = v

        elif selected_engine == "melotts":
            exe = _ask_text(
                "Path to MeloTTS executable:", self.settings.read_aloud_melotts_executable
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_melotts_executable = exe
            v = _ask_int("Speaking rate", self.settings.read_aloud_melotts_rate, 80, 450)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_melotts_rate = v

        elif selected_engine == "chatterbox":
            exe = _ask_text(
                "Path to Chatterbox executable:", self.settings.read_aloud_chatterbox_executable
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_chatterbox_executable = exe
            v = _ask_int("Speaking rate", self.settings.read_aloud_chatterbox_rate, 80, 450)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_chatterbox_rate = v

        elif selected_engine == "openvoice":
            exe = _ask_text(
                "Path to OpenVoice executable:", self.settings.read_aloud_openvoice_executable
            )
            if exe is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_openvoice_executable = exe
            v = _ask_int("Speaking rate", self.settings.read_aloud_openvoice_rate, 80, 450)
            if v is None:
                self._set_status("Read aloud settings cancelled")
                return
            self.settings.read_aloud_openvoice_rate = v
            consent = self._show_message_box(
                "OpenVoice can apply advanced voice style transforms. Enable this only if you consent\n"
                "to advanced style processing workflows for this machine.",
                _TITLE,
                wx.YES_NO | wx.ICON_QUESTION,
            )
            self.settings.read_aloud_openvoice_consent = consent == wx.YES

        # Always offer a preview of the current voice with new settings
        current_voice = {
            "pyttsx3": self.settings.read_aloud_voice,
            "dectalk": self.settings.read_aloud_dectalk_voice,
            "piper": self.settings.read_aloud_piper_model,
            "kokoro": self.settings.read_aloud_kokoro_voice,
            "vibevoice": self.settings.read_aloud_vibevoice_voice,
            "espeak": self.settings.read_aloud_espeak_voice,
            "rhvoice": self.settings.read_aloud_rhvoice_voice,
            "melotts": self.settings.read_aloud_melotts_voice,
            "chatterbox": self.settings.read_aloud_chatterbox_voice,
            "openvoice": self.settings.read_aloud_openvoice_voice,
        }.get(selected_engine, "")
        with wx.MessageDialog(
            self.frame,
            f"Settings saved for {engine_choices[engine_values.index(selected_engine)]}.\n\n"
            "Would you like to hear a preview with the current voice?",
            _TITLE,
            wx.YES_NO | wx.ICON_QUESTION,
        ) as confirm:
            save_settings(self.settings)
            if self._show_modal_dialog(confirm, _TITLE) == wx.ID_YES:
                self._preview_voice(selected_engine, current_voice)
        engine_label = engine_choices[engine_values.index(selected_engine)]
        self._set_status(f"Read aloud engine set to {engine_label}")

    def download_vibevoice_model(self) -> None:
        """Download the VibeVoice speech model + reference voices from the GUI.

        VibeVoice is an offline speech-FILE generator (not a live read-aloud
        voice). This fetches the model and voices via the vibevoice-cpu library
        in the background so the user never touches a terminal.
        """
        def work(progress: Callable[[str, int, int], None]) -> object:
            try:
                from vibevoice_cpu.download import DEFAULT_MODEL, ensure_model
                from vibevoice_cpu.system import ram_warning
                from vibevoice_cpu.voices import ensure_voices
            except ImportError as exc:  # noqa: BLE001
                raise RuntimeError(
                    "VibeVoice support isn't installed in this build "
                    "(the 'vibevoice-cpu' package)."
                ) from exc
            warning = ram_warning(DEFAULT_MODEL)
            progress("Downloading VibeVoice model (several GB, one time)", 0, 2)
            ensure_model(DEFAULT_MODEL)
            progress("Downloading VibeVoice reference voices", 1, 2)
            ensure_voices()
            progress("VibeVoice ready", 2, 2)
            return warning

        def on_success(result: object) -> None:
            message = "VibeVoice model and voices downloaded."
            if result:
                message += f" {result}"
            self._set_status(message)
            self._announce(message)

        self._run_background_task(
            "Downloading VibeVoice speech model and voices",
            work,
            on_success,
            notify_on_success=True,
            notify_on_error=True,
            notification_category="speech",
        )

    def generate_speech_with_vibevoice(self) -> None:
        """Generate a speech-audio FILE from the document using VibeVoice.

        VibeVoice is an offline file generator (CPU-native, GPU if available) via
        the vibevoice-cpu library — not a live read-aloud voice. The selection
        (or whole document) is synthesized to a WAV in the background.
        """
        wx = self._wx
        _TITLE = "Generate Speech with VibeVoice"
        if not self._document_tabs:
            self._set_status("No document open")
            return
        text = self.editor.GetStringSelection().strip() or self.editor.GetValue().strip()
        if not text:
            self._set_status("Nothing to synthesize")
            return

        try:
            from vibevoice_cpu.voices import list_voices
        except ImportError:
            self._show_message_box(
                "VibeVoice isn't installed. Install the model stack "
                "(vibevoice-cpu[model]) and try again, or use AI > Speech > "
                "Download VibeVoice Model first.",
                _TITLE,
                wx.ICON_ERROR | wx.OK,
            )
            return

        # Use already-downloaded voices if present; otherwise the worker resolves
        # and downloads one. Don't hit the network on the UI thread.
        voices = list_voices(download=False) or ["Alice"]
        voice = voices[0]
        if len(voices) > 1:
            with wx.SingleChoiceDialog(
                self.frame, "Choose a VibeVoice voice:", _TITLE, choices=voices
            ) as voice_dialog:
                if self._show_modal_dialog(voice_dialog, _TITLE) == wx.ID_OK:
                    voice = voices[voice_dialog.GetSelection()]

        with wx.FileDialog(
            self.frame,
            _TITLE,
            wildcard="Wave file (*.wav)|*.wav|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if self._show_modal_dialog(dlg, _TITLE) != wx.ID_OK:
                self._set_status("Speech generation cancelled")
                return
            output_path = Path(dlg.GetPath())
        if output_path.suffix.lower() != ".wav":
            output_path = output_path.with_suffix(".wav")

        text_snap = text
        voice_snap = voice

        def work(progress: Callable[[str, int, int], None]) -> object:
            from vibevoice_cpu import synthesize
            from vibevoice_cpu.download import DEFAULT_MODEL
            from vibevoice_cpu.system import ram_warning

            warning = ram_warning(DEFAULT_MODEL)
            progress("Generating speech with VibeVoice (slow on CPU)", 0, 1)
            synthesize(text_snap, output_path, voice=voice_snap)
            progress("Speech file ready", 1, 1)
            return warning

        def on_success(result: object) -> None:
            message = f"Saved speech audio to {output_path.name}"
            if result:
                message += f" ({result})"
            self._set_status(message)
            self._announce(message)

        self._run_background_task(
            "Generating speech with VibeVoice",
            work,
            on_success,
            notify_on_success=True,
            notify_on_error=True,
            notification_category="speech",
        )

    def generate_speech_audio(self) -> None:  # noqa: PLR0912,PLR0915
        wx = self._wx
        _TITLE = "Generate Speech Audio"
        if not self._document_tabs:
            self._set_status("No document open")
            return
        text = self.editor.GetStringSelection().strip() or self.editor.GetValue().strip()
        if not text:
            self._set_status("Nothing to synthesize")
            return

        with wx.FileDialog(
            self.frame,
            _TITLE,
            wildcard="Wave file (*.wav)|*.wav|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if self._show_modal_dialog(dlg, _TITLE) != wx.ID_OK:
                self._set_status("Speech generation cancelled")
                return
            output_path = Path(dlg.GetPath())
        if output_path.suffix.lower() != ".wav":
            output_path = output_path.with_suffix(".wav")

        engine = self.settings.read_aloud_engine.strip().lower() or "pyttsx3"
        s = self.settings

        # Resolve / prompt for engine-specific paths before background work
        if engine == "piper":
            exe = discover_piper_executable(s.read_aloud_piper_executable)
            if exe is None:
                with wx.TextEntryDialog(
                    self.frame, "Path to piper.exe:", _TITLE, value=s.read_aloud_piper_executable
                ) as d:
                    if self._show_modal_dialog(d, _TITLE) != wx.ID_OK:
                        self._set_status("Speech generation cancelled")
                        return
                    exe = discover_piper_executable(d.GetValue().strip())
                if exe is None:
                    self._show_message_box(
                        "Piper executable not found.", _TITLE, wx.ICON_ERROR | wx.OK
                    )
                    self._set_status("Speech generation cancelled")
                    return
                s.read_aloud_piper_executable = str(exe)
            model = Path(s.read_aloud_piper_model).expanduser()
            if not s.read_aloud_piper_model or not model.exists():
                with wx.FileDialog(
                    self.frame,
                    "Select Piper model (.onnx)",
                    wildcard="Piper model (*.onnx)|*.onnx|All files (*.*)|*.*",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                ) as d:
                    if self._show_modal_dialog(d, _TITLE) != wx.ID_OK:
                        self._set_status("Speech generation cancelled")
                        return
                    model = Path(d.GetPath())
                s.read_aloud_piper_model = str(model)
            piper_exe_snap = exe
            piper_model_snap = model

        elif engine == "dectalk":
            exe = discover_dectalk_executable(s.read_aloud_dectalk_executable)
            if exe is None:
                self._show_message_box(
                    "DECtalk executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            dectalk_exe_snap = exe

        elif engine == "vibevoice":
            exe = discover_vibevoice_executable(s.read_aloud_vibevoice_executable)
            if exe is None:
                self._show_message_box(
                    "VibeVoice executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            vibevoice_exe_snap = exe

        elif engine == "espeak":
            exe = discover_espeak_executable(s.read_aloud_espeak_executable)
            if exe is None:
                self._show_message_box(
                    "eSpeak-NG not found. Install it or configure the path in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            espeak_exe_snap = exe

        elif engine == "rhvoice":
            exe = discover_rhvoice_executable(s.read_aloud_rhvoice_executable)
            if exe is None:
                self._show_message_box(
                    "RHVoice executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            rhvoice_exe_snap = exe

        elif engine == "melotts":
            exe = discover_melotts_executable(s.read_aloud_melotts_executable)
            if exe is None:
                self._show_message_box(
                    "MeloTTS executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            melotts_exe_snap = exe

        elif engine == "chatterbox":
            exe = discover_chatterbox_executable(s.read_aloud_chatterbox_executable)
            if exe is None:
                self._show_message_box(
                    "Chatterbox executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            chatterbox_exe_snap = exe

        elif engine == "openvoice":
            if not s.read_aloud_openvoice_consent:
                self._show_message_box(
                    "OpenVoice requires explicit consent in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            exe = discover_openvoice_executable(s.read_aloud_openvoice_executable)
            if exe is None:
                self._show_message_box(
                    "OpenVoice executable not found. Configure it in Read Aloud Settings.",
                    _TITLE,
                    wx.ICON_ERROR | wx.OK,
                )
                self._set_status("Speech generation cancelled")
                return
            openvoice_exe_snap = exe

        save_settings(s)
        task_label = f"Generating speech audio ({output_path.name}) via {engine}"

        # Capture settings snapshot for the background thread
        _engine = engine
        _voice = s.read_aloud_voice
        _rate = s.read_aloud_rate
        _vol = s.read_aloud_volume / 100.0
        _dectalk_voice = s.read_aloud_dectalk_voice
        _dectalk_rate = s.read_aloud_dectalk_rate
        _kokoro_voice = s.read_aloud_kokoro_voice
        _kokoro_speed = s.read_aloud_kokoro_speed
        _vibevoice_voice = s.read_aloud_vibevoice_voice
        _espeak_voice = s.read_aloud_espeak_voice
        _espeak_rate = s.read_aloud_espeak_rate
        _rhvoice_voice = s.read_aloud_rhvoice_voice
        _rhvoice_rate = s.read_aloud_rhvoice_rate
        _melotts_voice = s.read_aloud_melotts_voice
        _melotts_rate = s.read_aloud_melotts_rate
        _chatterbox_voice = s.read_aloud_chatterbox_voice
        _chatterbox_rate = s.read_aloud_chatterbox_rate
        _openvoice_voice = s.read_aloud_openvoice_voice
        _openvoice_rate = s.read_aloud_openvoice_rate
        _out = output_path

        def work(progress: Callable[[str, int, int], None]) -> object:
            progress(f"Starting {_engine}", 0, 1)
            if _engine == "pyttsx3":
                synthesize_to_file_with_pyttsx3(
                    _out_text, _out, voice=_voice, rate=_rate, volume=_vol
                )
            elif _engine == "dectalk":
                synthesize_to_file_with_dectalk(
                    _out_text,
                    _out,
                    executable_path=dectalk_exe_snap,
                    voice=_dectalk_voice,
                    rate=_dectalk_rate,
                )
            elif _engine == "piper":
                synthesize_with_piper(
                    _out_text,
                    _out,
                    executable_path=piper_exe_snap,
                    model_path=piper_model_snap,
                )
            elif _engine == "kokoro":
                synthesize_with_kokoro(_out_text, _out, voice=_kokoro_voice, speed=_kokoro_speed)
            elif _engine == "vibevoice":
                synthesize_with_vibevoice(
                    _out_text,
                    _out,
                    executable_path=vibevoice_exe_snap,
                    voice=_vibevoice_voice,
                )
            elif _engine == "espeak":
                synthesize_with_espeak(
                    _out_text,
                    _out,
                    executable_path=espeak_exe_snap,
                    voice=_espeak_voice,
                    rate=_espeak_rate,
                )
            elif _engine == "rhvoice":
                synthesize_with_rhvoice(
                    _out_text,
                    _out,
                    executable_path=rhvoice_exe_snap,
                    voice=_rhvoice_voice,
                    rate=_rhvoice_rate,
                )
            elif _engine == "melotts":
                synthesize_with_melotts(
                    _out_text,
                    _out,
                    executable_path=melotts_exe_snap,
                    voice=_melotts_voice,
                    rate=_melotts_rate,
                )
            elif _engine == "chatterbox":
                synthesize_with_chatterbox(
                    _out_text,
                    _out,
                    executable_path=chatterbox_exe_snap,
                    voice=_chatterbox_voice,
                    rate=_chatterbox_rate,
                )
            elif _engine == "openvoice":
                synthesize_with_openvoice(
                    _out_text,
                    _out,
                    executable_path=openvoice_exe_snap,
                    voice=_openvoice_voice,
                    rate=_openvoice_rate,
                )
            progress("Finalizing output", 1, 1)
            return str(_out)

        _out_text = text

        def on_success(result: object) -> None:
            self._set_status(f"Speech generation complete: {Path(str(result)).name}")

        self._run_background_task(
            task_label,
            work,
            on_success,
            notify_on_success=True,
            notify_on_error=True,
            notification_category="speech",
        )

    def ocr_image_file(self) -> None:
        wx = self._wx
        # Defer the OCR pipeline import (pulls in tesseract bindings + PIL)
        # until the user actually picks an image. Saves ~30–50 ms at cold
        # start for anyone who never uses OCR.
        from quill.io.ocr import (
            OcrCancelledError,
            OcrFailedError,
            OcrUnavailableError,
            ocr_image,
        )

        with wx.FileDialog(
            self.frame,
            "OCR image",
            wildcard=(
                "Image files (*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp)|"
                "*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp|All files (*.*)|*.*"
            ),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if self._show_modal_dialog(dialog, "OCR Image") != wx.ID_OK:
                self._set_status("OCR cancelled")
                return
            image_path = Path(dialog.GetPath())
        result = self._show_message_box(
            "Run OCR on this image locally with Tesseract?",
            "OCR Image",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("OCR cancelled")
            return
        progress_state = {
            "message": "Starting OCR...",
            "done": False,
            "error": None,
            "result": None,
        }
        cancel_requested = threading.Event()

        def run_ocr() -> None:
            try:
                progress_state["result"] = ocr_image(
                    image_path,
                    on_progress=lambda message: progress_state.__setitem__("message", message),
                    cancel_requested=cancel_requested.is_set,
                )
            except OcrCancelledError as exc:
                progress_state["error"] = exc
            except (OcrUnavailableError, OcrFailedError) as exc:
                progress_state["error"] = exc
            finally:
                progress_state["done"] = True

        worker = threading.Thread(target=run_ocr, name="ocr-image", daemon=True)
        worker.start()
        progress = wx.ProgressDialog(
            "OCR Image",
            progress_state["message"],
            maximum=100,
            parent=self.frame,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT,
        )
        try:
            step = 10
            while not progress_state["done"]:
                keep_going, _ = progress.Update(step, progress_state["message"])
                if not keep_going:
                    cancel_requested.set()
                wx.YieldIfNeeded()
                time.sleep(0.1)
                step = min(90, step + 4)
            worker.join()
            error = progress_state["error"]
            if isinstance(error, OcrCancelledError):
                self._set_status("OCR cancelled")
                return
            if isinstance(error, OcrUnavailableError):
                self._show_message_box(str(error), "OCR Image", wx.ICON_INFORMATION | wx.OK)
                self._set_status("OCR unavailable")
                return
            if isinstance(error, OcrFailedError):
                self._show_message_box(str(error), "OCR Image", wx.ICON_ERROR | wx.OK)
                self._set_status("OCR failed")
                return
            ocr_result = progress_state["result"]
            if ocr_result is None:
                self._set_status("OCR failed")
                return
            progress.Update(90, "Opening OCR result")
            self.new_file()
            self._replace_document_text(ocr_result.text)
            self.document.set_text(ocr_result.text)
            self._refresh_title()
            self._set_status(f"OCR completed with {ocr_result.engine}")
            progress.Update(100, "Done")
        finally:
            cancel_requested.set()
            worker.join(timeout=0.5)
            progress.Destroy()

    def _on_read_aloud_progress(self, start: int, end: int) -> None:
        self.editor.SetSelection(start, end)
        self.editor.SetFocus()
        self._set_status("Read aloud speaking")

    def _on_read_aloud_state_change(self, state: str) -> None:
        if state == "paused":
            self._set_status("Read aloud paused")
        elif state == "error":
            self._set_status("Read aloud failed")
        else:
            self._set_status("Read aloud finished")

    def _on_read_aloud_error(self, error: str) -> None:
        self._set_status(f"Read aloud error: {error}")

    def toggle_dictation(self) -> None:
        wx = self._wx
        state = self._dictation.state
        if state == "listening":
            self._cancel_voice_command_scan()
            self._voice_command_baseline_text = ""
            self._dictation.stop()
            self._set_status("Windows dictation stopped")
            return

        self.editor.SetFocus()
        self._voice_command_baseline_text = self.editor.GetValue()
        try:
            self._dictation.start(DictationSettings())
        except DictationUnavailableError:
            self._show_message_box(
                "Windows dictation is unavailable on this system.",
                "Dictation",
                wx.ICON_INFORMATION | wx.OK,
            )
            self._voice_command_baseline_text = ""
            return
        if self.settings.voice_commands_enabled:
            self._set_status(
                'Windows dictation started. Say "Hey QUILL" plus a command to trigger Quill.'
            )
        else:
            self._set_status("Windows dictation started. Speak into the editor.")

    def toggle_dictation_voice_commands(self) -> None:
        self.settings.voice_commands_enabled = not self.settings.voice_commands_enabled
        save_settings(self.settings)
        item = self.frame.GetMenuBar().FindItemById(self._id_dictation_voice_commands)
        if item is not None:
            item.Check(self.settings.voice_commands_enabled)
        if self.settings.voice_commands_enabled and self._dictation.state == "listening":
            self._voice_command_baseline_text = self.editor.GetValue()
            self._schedule_voice_command_scan()
            self._set_status('Hey QUILL commands enabled. Say "Hey QUILL" plus a command.')
        elif self.settings.voice_commands_enabled:
            self._set_status("Hey QUILL commands enabled. Start dictation to use them.")
        else:
            self._cancel_voice_command_scan()
            self._voice_command_baseline_text = ""
            self._set_status("Hey QUILL commands disabled")

    def _watch_folder_config(self) -> WatchFolderConfig:
        return WatchFolderConfig(
            enabled=bool(getattr(self.settings, "watch_folder_enabled", False)),
            folder_path=str(getattr(self.settings, "watch_folder_path", "")),
            include_subfolders=bool(
                getattr(self.settings, "watch_folder_include_subfolders", False)
            ),
            process_existing=bool(getattr(self.settings, "watch_folder_process_existing", False)),
            auto_start=bool(getattr(self.settings, "watch_folder_auto_start", False)),
            poll_interval_seconds=int(
                getattr(self.settings, "watch_folder_poll_interval_seconds", 5)
            ),
        ).normalized()

    def _apply_watch_folder_menu_state(self) -> None:
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is None:
            return
        item = menu_bar.FindItemById(self._id_watch_folder_toggle)
        if item is None:
            return
        enabled = bool(getattr(self.settings, "watch_folder_enabled", False))
        item.Check(enabled and self._watch_folder.is_running)

    def _maybe_start_watch_folder(self) -> None:
        config = self._watch_folder_config()
        if not config.enabled or not config.auto_start:
            self._apply_watch_folder_menu_state()
            return
        self._start_watch_folder_monitoring(config, announce=False)

    def _start_watch_folder_monitoring(
        self, config: WatchFolderConfig | None = None, *, announce: bool = True
    ) -> bool:
        if not self._feature_enabled("core.watch_folder"):
            if announce:
                self._set_status("Watch folder is unavailable in this profile")
            return False
        candidate = self._watch_folder_config() if config is None else config.normalized()
        if not candidate.enabled:
            if announce:
                self._set_status("Enable watch folder monitoring first")
            return False
        if not candidate.folder_path:
            if announce:
                self._set_status("Set a watch folder path before starting monitoring")
            return False
        try:
            started = self._watch_folder.start(candidate)
        except ValueError as error:
            if announce:
                self._show_message_box(
                    str(error),
                    "Watch Folder",
                    self._wx.ICON_WARNING | self._wx.OK,
                )
                self._set_status("Watch folder start failed")
            self._apply_watch_folder_menu_state()
            return False
        if not started:
            self._apply_watch_folder_menu_state()
            return False
        self.settings.watch_folder_enabled = True
        save_settings(self.settings)
        self._apply_watch_folder_menu_state()
        if announce:
            self._set_status("Watch folder monitoring started")
            self._record_notification("Watch folder monitoring started", "speech")
        return True

    def _stop_watch_folder_monitoring(self, *, announce: bool = True) -> None:
        self._watch_folder.stop()
        self._apply_watch_folder_menu_state()
        if announce:
            self._set_status("Watch folder monitoring stopped")
            self._record_notification("Watch folder monitoring stopped", "speech")

    def toggle_watch_folder_monitoring(self) -> None:
        if self._watch_folder.is_running:
            self.settings.watch_folder_enabled = False
            save_settings(self.settings)
            self._stop_watch_folder_monitoring()
            return
        if not str(getattr(self.settings, "watch_folder_path", "")).strip():
            self.open_watch_folder_settings()
            if not str(getattr(self.settings, "watch_folder_path", "")).strip():
                self._apply_watch_folder_menu_state()
                return
        self.settings.watch_folder_enabled = True
        save_settings(self.settings)
        self._start_watch_folder_monitoring()

    def show_watch_folder_status(self) -> None:
        config = self._watch_folder_config()
        running = "Running" if self._watch_folder.is_running else "Stopped"
        folder = config.folder_path or "(not set)"
        state = (
            "Watch Folder Status\n\n"
            f"State: {running}\n"
            f"Path: {folder}\n"
            f"Poll interval: {config.poll_interval_seconds} seconds\n"
            f"Include subfolders: {'Yes' if config.include_subfolders else 'No'}\n"
            f"Process existing files on start: {'Yes' if config.process_existing else 'No'}\n"
            f"Auto-start on launch: {'Yes' if config.auto_start else 'No'}"
        )
        self._show_message_box(
            state, "Watch Folder Status", self._wx.ICON_INFORMATION | self._wx.OK
        )

    def open_watch_folder_settings(self) -> None:  # noqa: PLR0915
        wx = self._wx
        with wx.Dialog(self.frame, title="Watch Folder Settings") as dialog:
            panel = wx.Panel(dialog)
            root = wx.BoxSizer(wx.VERTICAL)
            panel_sizer = wx.BoxSizer(wx.VERTICAL)

            config = self._watch_folder_config()

            enabled = wx.CheckBox(panel, label="Enable watch folder monitoring")
            enabled.SetValue(config.enabled)
            enabled.SetName("Enable watch folder monitoring")
            panel_sizer.Add(enabled, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 8)

            path_row = wx.BoxSizer(wx.HORIZONTAL)
            path_label = wx.StaticText(panel, label="Watch folder path")
            path_label.SetName("Watch folder path label")
            path_input = wx.TextCtrl(panel, value=config.folder_path)
            path_input.SetName("Watch folder path")
            browse_button = wx.Button(panel, label="Browse...")
            browse_button.SetName("Browse for watch folder")
            path_row.Add(path_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            path_row.Add(path_input, 1, wx.EXPAND | wx.RIGHT, 8)
            path_row.Add(browse_button, 0)
            panel_sizer.Add(path_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            include_subfolders = wx.CheckBox(panel, label="Include subfolders")
            include_subfolders.SetValue(config.include_subfolders)
            include_subfolders.SetName("Include subfolders")
            panel_sizer.Add(include_subfolders, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            process_existing = wx.CheckBox(
                panel, label="Process existing supported files on startup"
            )
            process_existing.SetValue(config.process_existing)
            process_existing.SetName("Process existing supported files on startup")
            panel_sizer.Add(process_existing, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            auto_start = wx.CheckBox(panel, label="Start monitoring automatically on launch")
            auto_start.SetValue(config.auto_start)
            auto_start.SetName("Start monitoring automatically on launch")
            panel_sizer.Add(auto_start, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            interval_row = wx.BoxSizer(wx.HORIZONTAL)
            interval_label = wx.StaticText(panel, label="Poll interval (seconds)")
            interval_input = wx.SpinCtrl(
                panel, min=2, max=300, initial=config.poll_interval_seconds
            )
            interval_input.SetName("Watch folder poll interval in seconds")
            interval_row.Add(interval_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            interval_row.Add(interval_input, 0)
            panel_sizer.Add(interval_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            def _browse_folder(_event: object) -> None:
                with wx.DirDialog(
                    dialog,
                    "Choose watch folder",
                    defaultPath=path_input.GetValue().strip(),
                    style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
                ) as picker:
                    if self._show_modal_dialog(picker, "Watch Folder Settings") == wx.ID_OK:
                        path_input.SetValue(picker.GetPath())

            browse_button.Bind(wx.EVT_BUTTON, _browse_folder)

            panel.SetSizer(panel_sizer)
            buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
            root.Add(panel, 1, wx.EXPAND | wx.ALL, 8)
            if buttons is not None:
                root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
            dialog.SetSizerAndFit(root)

            if self._show_modal_dialog(dialog, "Watch Folder Settings") != wx.ID_OK:
                self._set_status("Watch folder settings cancelled")
                self._apply_watch_folder_menu_state()
                return

            self.settings.watch_folder_enabled = bool(enabled.GetValue())
            self.settings.watch_folder_path = path_input.GetValue().strip()
            self.settings.watch_folder_include_subfolders = bool(include_subfolders.GetValue())
            self.settings.watch_folder_process_existing = bool(process_existing.GetValue())
            self.settings.watch_folder_auto_start = bool(auto_start.GetValue())
            self.settings.watch_folder_poll_interval_seconds = int(interval_input.GetValue())
            save_settings(self.settings)

        if self.settings.watch_folder_enabled:
            started = self._start_watch_folder_monitoring(announce=False)
            if started:
                self._set_status("Updated watch folder settings and started monitoring")
            else:
                self._set_status("Updated watch folder settings")
        else:
            self._stop_watch_folder_monitoring(announce=False)
            self._set_status("Updated watch folder settings")
        self._apply_watch_folder_menu_state()

    def _show_watch_folder_onboarding(self, force: bool) -> None:
        wx = self._wx
        response = self._show_message_box(
            "Set up watch folder automation now?\n\n"
            "When enabled, Quill monitors one folder and opens new supported files "
            "automatically as they appear.",
            "Watch Folder Setup",
            wx.ICON_QUESTION | wx.YES_NO,
        )
        if response != wx.YES:
            if not force:
                mark_watch_folder_onboarding_complete()
            self._set_status("Watch folder setup skipped")
            return
        self.open_watch_folder_settings()
        mark_watch_folder_onboarding_complete()

    def _on_watch_folder_result(self, result: WatchFolderResult) -> None:
        self.open_file(result.source_path, record_recent=True, refresh_existing=False)
        self._record_notification(f"Watch folder opened {result.source_path.name}", "speech")
        self._set_status(f"Watch folder opened {result.source_path.name}")

    def _on_watch_folder_error(self, path: Path, message: str) -> None:
        self._record_notification(
            f"Watch folder failed for {path.name}: {message}",
            "speech",
        )
        self._set_status(f"Watch folder failed for {path.name}")

    def _on_watch_folder_state_change(self, running: bool) -> None:
        self._apply_watch_folder_menu_state()
        if running:
            self._set_status("Watch folder monitoring active")

    def _refresh_voice_command_aliases(self) -> None:
        self._voice_command_aliases = build_voice_command_aliases(
            self.commands.list(),
            {
                "new document": "file.new",
                "open document": "file.open",
                "open file": "file.open",
                "save document": "file.save",
                "save as": "file.save_as",
                "close document": "file.close_document",
                "close file": "file.close_document",
                "command palette": "app.command_palette",
                "read aloud": "tools.read_aloud",
                "stop read aloud": "tools.read_aloud_stop",
                "dictation": "tools.dictation_toggle",
                "toggle dictation": "tools.dictation_toggle",
                "hey quill commands": "tools.dictation_voice_commands_toggle",
                "voice commands": "tools.dictation_voice_commands_toggle",
            },
        )

    def _cancel_voice_command_scan(self) -> None:
        timer = self._voice_command_scan_timer
        if timer is not None:
            timer.cancel()
        self._voice_command_scan_timer = None

    def _schedule_voice_command_scan(self) -> None:
        if not self.settings.voice_commands_enabled or self._dictation.state != "listening":
            return
        self._cancel_voice_command_scan()

        def run() -> None:
            self._wx.CallAfter(self._process_voice_command_transcript)

        timer = threading.Timer(1.2, run)
        timer.daemon = True
        self._voice_command_scan_timer = timer
        timer.start()

    def _process_voice_command_transcript(self) -> None:
        self._voice_command_scan_timer = None
        if self._voice_command_guard:
            return
        if not self.settings.voice_commands_enabled or self._dictation.state != "listening":
            return
        baseline = self._voice_command_baseline_text
        current_text = self.editor.GetValue()
        if not baseline or current_text == baseline:
            return
        _prefix, inserted, _suffix = split_text_delta(baseline, current_text)
        if not inserted.strip():
            return
        match = resolve_voice_command(inserted, self._voice_command_aliases)
        if match is None:
            self._voice_command_baseline_text = current_text
            return
        command = self.commands.get(match.command_id)
        if command is None or not self._feature_enabled(command.feature_id):
            self._voice_command_baseline_text = current_text
            self._set_status("Hey QUILL command is unavailable in this profile")
            return
        self._voice_command_guard = True
        try:
            self._replace_document_text(baseline)
            self.document.set_text(baseline)
            if not self._suspend_persistent_undo:
                self._record_persistent_undo_state(baseline)
            self.editor.SetInsertionPoint(len(baseline))
            self.editor.SetSelection(len(baseline), len(baseline))
            self._refresh_browser_preview()
            self._maybe_autosave()
        finally:
            self._voice_command_guard = False
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._set_status(f"Hey QUILL: {command.title}")
        command.handler()
        self._voice_command_baseline_text = self.editor.GetValue()

    def _on_dictation_state_change(self, state: str) -> None:
        if state == "listening":
            if self.settings.voice_commands_enabled:
                self._set_status(
                    'Windows dictation started. Say "Hey QUILL" plus a command to trigger Quill.'
                )
            else:
                self._set_status("Windows dictation started. Speak into the editor.")
        else:
            self._cancel_voice_command_scan()
            self._voice_command_baseline_text = ""
            self._set_status("Windows dictation stopped")

    def _on_dictation_error(self, error_msg: str) -> None:
        self._cancel_voice_command_scan()
        self._voice_command_baseline_text = ""
        self._set_status("Windows dictation error")

    def install_shell_integration(self) -> None:
        wx = self._wx
        command = launcher_command()
        plan = build_shell_integration_plan(command)
        summary = "\n".join(entry.path for entry in plan[:8])
        result = self._show_message_box(
            "Install per-user Open-with associations and shell verbs for Quill?",
            "Shell Integration",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Shell integration install cancelled")
            return
        install_shell_integration(command)
        self._show_message_box(
            f"Installed shell integration for:\n{summary}",
            "Shell Integration",
            wx.ICON_INFORMATION | wx.OK,
        )
        self._set_status("Installed shell integration")

    def remove_shell_integration(self) -> None:
        wx = self._wx
        result = self._show_message_box(
            "Remove Quill shell integration from this user account?",
            "Shell Integration",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Shell integration removal cancelled")
            return
        remove_shell_integration()
        self._set_status("Removed shell integration")

    def open_notifications(self) -> None:
        wx = self._wx
        result = self._show_notifications_dialog()
        if result == wx.ID_CLEAR:
            clear_notifications()
            self._notifications = []
            self._set_status("Cleared notifications")
            return
        if self._notifications:
            self._set_status("Viewed notifications")
            return
        self._set_status("No notifications")

    def _show_notifications_dialog(self) -> int:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Notifications", size=(900, 520))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Quill notifications appear below. Selecting a row copies it to the clipboard, "
                    "or use Copy Selected."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        lines = [
            f"{entry.timestamp} [{entry.category}] {entry.message}"
            for entry in self._notifications[-200:]
        ]
        chooser = wx.ListBox(panel, choices=lines)
        root.Add(chooser, 1, wx.ALL | wx.EXPAND, 8)
        button_row = wx.BoxSizer(wx.HORIZONTAL)
        copy_button = wx.Button(panel, label="Copy Selected")
        clear_button = wx.Button(panel, id=wx.ID_CLEAR, label="Clear Notifications")
        close_button = wx.Button(panel, id=wx.ID_CLOSE, label="Close")
        button_row.Add(copy_button, 0, wx.RIGHT, 8)
        button_row.Add(clear_button, 0, wx.RIGHT, 8)
        button_row.AddStretchSpacer(1)
        button_row.Add(close_button, 0)
        root.Add(button_row, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)

        if lines:
            chooser.SetSelection(len(lines) - 1)
        else:
            chooser.Enable(False)
            copy_button.Enable(False)
            clear_button.Enable(False)

        def selected_line() -> str:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return ""
            return lines[selection]

        def copy_selected() -> None:
            value = selected_line()
            if not value:
                self._set_status("No notification selected")
                return
            if not self._copy_to_clipboard(value):
                self._set_status("Could not copy notification")
                return
            self._set_status("Copied notification to clipboard")

        chooser.Bind(wx.EVT_LISTBOX, lambda _e: copy_selected())
        copy_button.Bind(wx.EVT_BUTTON, lambda _e: copy_selected())
        clear_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CLEAR))
        close_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CLOSE))

        result = dialog.ShowModal()
        dialog.Destroy()
        return result

    def show_help_status_page(self) -> None:
        report_html = self._build_help_status_html()
        index = self._open_generated_tab("Application Status", report_html)
        self._select_tab(index)
        if 0 <= index < len(self._document_tabs):
            self._show_side_preview_for(self._document_tabs[index])
        self._set_status("Opened application status page in HTML preview")

    def _build_help_status_html(self) -> str:
        feature_rows: list[str] = []
        for feature_id, definition in sorted(FEATURE_DEFINITIONS.items()):
            state = self.features.state_for(feature_id)
            state_label = {
                "on": "Enabled",
                "quiet": "Quiet",
                "off": "Disabled",
            }.get(state, state)
            feature_rows.append(
                "<tr>"
                f"<td>{html.escape(feature_id)}</td>"
                f"<td>{html.escape(definition.name)}</td>"
                f"<td>{html.escape(definition.category)}</td>"
                f"<td>{html.escape(state_label)}</td>"
                "</tr>"
            )

        settings = self.settings
        speech_rows = [
            ("Engine", settings.read_aloud_engine),
            ("Voice (pyttsx3)", settings.read_aloud_voice or "(default system)"),
            ("DECtalk executable", settings.read_aloud_dectalk_executable or "Not configured"),
            ("DECtalk voice", settings.read_aloud_dectalk_voice),
            ("Piper executable", settings.read_aloud_piper_executable or "Not configured"),
            ("Piper model", settings.read_aloud_piper_model or "Not configured"),
            ("Kokoro voice", settings.read_aloud_kokoro_voice),
            ("VibeVoice executable", settings.read_aloud_vibevoice_executable or "Not configured"),
            ("VibeVoice voice", settings.read_aloud_vibevoice_voice),
            ("eSpeak executable", settings.read_aloud_espeak_executable or "PATH lookup"),
            ("eSpeak English voice", settings.read_aloud_espeak_voice),
            ("RHVoice executable", settings.read_aloud_rhvoice_executable or "Not configured"),
            ("RHVoice voice", settings.read_aloud_rhvoice_voice),
            ("MeloTTS executable", settings.read_aloud_melotts_executable or "Not configured"),
            ("MeloTTS voice", settings.read_aloud_melotts_voice),
            (
                "Chatterbox executable",
                settings.read_aloud_chatterbox_executable or "Not configured",
            ),
            ("Chatterbox voice", settings.read_aloud_chatterbox_voice),
            ("OpenVoice executable", settings.read_aloud_openvoice_executable or "Not configured"),
            ("OpenVoice voice", settings.read_aloud_openvoice_voice),
            (
                "OpenVoice consent",
                "Enabled" if settings.read_aloud_openvoice_consent else "Disabled",
            ),
        ]
        speech_table_rows = "".join(
            f"<tr><th scope='row'>{html.escape(name)}</th><td>{html.escape(str(value))}</td></tr>"
            for name, value in speech_rows
        )

        task_rows: list[str] = []
        for task in reversed(getattr(self, "_background_tasks", [])[-50:]):
            label = str(task.get("label", ""))
            status = str(task.get("status", ""))
            progress = str(task.get("progress", ""))
            started_at = str(task.get("started_at", ""))
            finished_at = str(task.get("finished_at", ""))
            task_rows.append(
                "<tr>"
                f"<td>{html.escape(label)}</td>"
                f"<td>{html.escape(status.title())}</td>"
                f"<td>{html.escape(progress)}</td>"
                f"<td>{html.escape(started_at)}</td>"
                f"<td>{html.escape(finished_at or 'Running')}</td>"
                "</tr>"
            )
        if not task_rows:
            task_rows.append(
                "<tr><td colspan='5'>No background tasks have run in this session.</td></tr>"
            )

        notification_count = len(getattr(self, "_notifications", []))
        active_tasks = int(getattr(self, "_background_task_count", 0))
        profile_name = self.features.active_profile.name

        return (
            "<h1 id='status-page'>Quill Application Status</h1>"
            "<p>This page reports current runtime status for features, speech setup, and background downloads/tasks.</p>"
            "<h2 id='runtime-overview'>Runtime Overview</h2>"
            "<table>"
            "<caption>Current runtime summary</caption>"
            "<thead><tr><th scope='col'>Item</th><th scope='col'>Value</th></tr></thead>"
            "<tbody>"
            f"<tr><th scope='row'>Version</th><td>{html.escape(__version__)}</td></tr>"
            f"<tr><th scope='row'>Active profile</th><td>{html.escape(profile_name)}</td></tr>"
            f"<tr><th scope='row'>Background tasks running</th><td>{active_tasks}</td></tr>"
            f"<tr><th scope='row'>Notifications queued</th><td>{notification_count}</td></tr>"
            "</tbody></table>"
            "<h2 id='speech-status'>Speech Status</h2>"
            "<table>"
            "<caption>Speech engine configuration and downloads</caption>"
            "<thead><tr><th scope='col'>Setting</th><th scope='col'>Value</th></tr></thead>"
            f"<tbody>{speech_table_rows}</tbody></table>"
            "<h2 id='background-tasks'>Background Tasks and Downloads</h2>"
            "<table>"
            "<caption>Recent asynchronous jobs (downloads, generation, indexing)</caption>"
            "<thead><tr>"
            "<th scope='col'>Task</th><th scope='col'>Status</th><th scope='col'>Progress</th>"
            "<th scope='col'>Started</th><th scope='col'>Finished</th>"
            "</tr></thead>"
            f"<tbody>{''.join(task_rows)}</tbody></table>"
            "<h2 id='features'>Feature Status</h2>"
            "<table>"
            "<caption>Enabled, quiet, and disabled features</caption>"
            "<thead><tr>"
            "<th scope='col'>Feature ID</th>"
            "<th scope='col'>Feature Name</th>"
            "<th scope='col'>Category</th>"
            "<th scope='col'>Status</th>"
            "</tr></thead>"
            f"<tbody>{''.join(feature_rows)}</tbody></table>"
            "<h2 id='recommended-actions'>Recommended Actions</h2>"
            "<ul>"
            "<li>Open AI &gt; Speech &gt; Settings to configure engine-specific paths.</li>"
            "<li>Open AI &gt; Speech &gt; Voice to preview voices and variants.</li>"
            "<li>Open AI &gt; Speech &gt; Generate Audio to run asynchronous speech output jobs.</li>"
            "<li>Open Tools &gt; Support &gt; Show Notifications for detailed alerts and outcomes.</li>"
            "</ul>"
        )

    def check_for_updates(self, silent_no_update: bool = False) -> None:
        wx = self._wx
        current_version = getattr(getattr(self, "_updates", None), "current_version", "")
        if not current_version:
            current_version = __version__ or "0.0.0"

        # Compatibility path: honor the signed manifest updater used by
        # earlier flows and tests before consulting GitHub Releases.
        try:
            manifest = fetch_update_manifest(
                "https://community-access.github.io/quill/updates/.quill-update-feed-v1.json"
            )
        except (URLError, ValueError, OSError):
            manifest = None
        if manifest is not None and is_newer_version(current_version, manifest.version):
            if silent_no_update:
                self._record_notification(
                    f"Update {manifest.version} found via manifest feed",
                    "update",
                )
                return
            download_now = self._show_message_box(
                (f"Update {manifest.version} is available.\n\nOpen the update download now?"),
                "Check for Updates",
                wx.ICON_INFORMATION | wx.YES_NO,
            )
            if download_now == wx.YES:
                self._open_update_download_flow(manifest)
            else:
                self._set_status("Update deferred")
                self._record_notification(
                    f"Update {manifest.version} deferred",
                    "update",
                )
            return

        beta = bool(getattr(self.settings, "beta_updates", False))
        self._set_status("Checking for updates...")
        try:
            releases = fetch_releases()
        except (URLError, ValueError, OSError) as error:
            if silent_no_update:
                self._record_notification(f"Update check failed: {error}", "update")
                self._set_status("Update check failed")
                return
            self._html_info(
                "Check for Updates",
                f"# Update check failed\n\nCould not check for updates:\n\n`{error}`",
            )
            self._set_status("Update check failed")
            self._record_notification("Update check failed", "update")
            return

        latest_any = select_latest(releases, include_prereleases=True)
        latest_stable = select_latest(releases, include_prereleases=False)

        # If the running build is itself a prerelease, the user is already a beta
        # tester — put them on the beta channel automatically (no consent needed).
        current_match = find_release(releases, current_version)
        if not beta and current_match is not None and current_match.prerelease:
            self.settings.beta_updates = True
            save_settings(self.settings)
            beta = True
            self._record_notification(
                "You're running a beta build, so beta updates are enabled.", "update"
            )

        # The release for the user's current channel.
        target = latest_any if beta else latest_stable
        if target is not None and is_newer_version(current_version, target.version):
            if silent_no_update:
                self._record_notification(f"Update {target.version} found; downloading", "update")
                self._download_update_release(target)
                return
            if self._show_update_available_dialog(current_version, target):
                self._download_update_release(target)
            else:
                self._set_status("Update deferred")
                self._record_notification(f"Update {target.version} deferred", "update")
            return

        # No update on the current channel. If a newer build exists but it's a
        # PRERELEASE and the user is on stable, route them to the beta channel.
        prerelease_available = (
            not beta
            and latest_any is not None
            and latest_any.prerelease
            and is_newer_version(current_version, latest_any.version)
        )
        if prerelease_available:
            if silent_no_update:
                self._record_notification(
                    f"A beta build {latest_any.version} is available. "
                    "Enable beta updates to install it.",
                    "update",
                )
                self._set_status("Beta update available")
                return
            self._route_prerelease_to_beta(current_version, latest_any)
            return

        # Genuinely up to date.
        if silent_no_update:
            self._record_notification("Update check found no newer version", "update")
            return
        self._set_status("No update available")
        self._record_notification("Update check found no newer version", "update")
        if beta:
            self._html_info(
                "Check for Updates",
                "# You're up to date\n\n"
                "You're on the **beta** channel and running the newest build.\n\n"
                f"**Current version:** {current_version}",
            )
        else:
            self._offer_beta_switch(current_version, latest_stable)

    def _route_prerelease_to_beta(self, current_version: str, release: GitHubRelease) -> None:
        """A prerelease is available while on stable — enroll in beta (with the
        consent gate), then offer the prerelease for download."""
        if not self._confirm_beta_channel(release):
            self._set_status("Stayed on the stable channel")
            return
        self.settings.beta_updates = True
        save_settings(self.settings)
        self._set_status("Switched to the beta update channel")
        self._announce("Beta updates enabled")
        if self._show_update_available_dialog(current_version, release):
            self._download_update_release(release)

    def _render_html(self, markdown_text: str) -> str:
        from quill.core.browser_preview import render_preview_body

        return render_preview_body(markdown_text, "markdown")

    def _html_info(self, title: str, markdown_text: str) -> None:
        """Show an informational message in the WebView dialog (with an OK button)."""
        from quill.ui.preview_dialog import HtmlMessageDialog

        HtmlMessageDialog(
            self.frame, title, self._render_html(markdown_text), [("OK", self._wx.ID_OK)]
        ).show_modal()

    def _show_update_available_dialog(self, current_version: str, release: GitHubRelease) -> bool:
        from quill.ui.preview_dialog import HtmlMessageDialog

        wx = self._wx
        channel = "Beta / prerelease" if release.prerelease else "Stable"
        notes = release.notes or "_(no release notes provided)_"
        body = self._render_html(
            f"# Update available: {release.version}\n\n"
            f"**Channel:** {channel}  \n"
            f"**Current version:** {current_version}\n\n"
            "## Release notes\n\n" + notes
        )
        result = HtmlMessageDialog(
            self.frame,
            "Check for Updates",
            body,
            [("Later", wx.ID_CANCEL), ("Download update", wx.ID_OK)],
        ).show_modal()
        return result == wx.ID_OK

    def _offer_beta_switch(
        self, current_version: str, stable_release: GitHubRelease | None
    ) -> None:
        from quill.ui.preview_dialog import HtmlMessageDialog

        wx = self._wx
        stable_line = (
            f"the latest stable release is {stable_release.version}"
            if stable_release is not None
            else "no stable release is published yet"
        )
        body = self._render_html(
            "# You're up to date\n\n"
            f"You're on the **stable** channel (current version {current_version}; "
            f"{stable_line}).\n\n"
            "Want earlier features sooner? The **beta** channel delivers prerelease "
            "builds as soon as they're published.\n"
        )
        result = HtmlMessageDialog(
            self.frame,
            "Check for Updates",
            body,
            [("Stay on stable", wx.ID_CANCEL), ("Switch to beta...", wx.ID_YES)],
        ).show_modal()
        if result == wx.ID_YES and self._confirm_beta_channel():
            self.settings.beta_updates = True
            save_settings(self.settings)
            self._set_status("Switched to the beta update channel")
            self._announce("Beta updates enabled")
            # Surface the latest prerelease right away so the user can install it,
            # even if its version matches the current build (they opted into beta).
            self._offer_latest_beta(current_version)

    def _offer_latest_beta(self, current_version: str) -> None:
        try:
            release = fetch_latest_release(include_prereleases=True)
        except (URLError, ValueError, OSError) as error:
            self._html_info(
                "Check for Updates",
                f"# Update check failed\n\nCould not check beta updates: {error}",
            )
            return
        if release is None:
            self._html_info(
                "Check for Updates",
                "# No beta build yet\n\nNo beta (prerelease) build is available yet.",
            )
            return
        if self._show_update_available_dialog(current_version, release):
            self._download_update_release(release)

    def _confirm_beta_channel(self, release: GitHubRelease | None = None) -> bool:
        """HTML consent gate the user must agree to before beta updates turn on."""
        from quill.ui.preview_dialog import HtmlMessageDialog

        wx = self._wx
        detected = (
            f"A beta build (**{release.version}**) is available.\n\n" if release is not None else ""
        )
        body = self._render_html(
            "# Enable beta updates?\n\n"
            f"{detected}"
            "Beta updates are **prerelease** builds. They get new features and fixes "
            "first, but they **may be unstable** — expect rough edges, and occasional "
            "bugs that could affect your documents.\n\n"
            "- Beta builds are published as GitHub prereleases.\n"
            "- You can switch back to stable anytime in Settings.\n"
            "- Keep backups of important documents.\n\n"
            "Do you understand and want to receive beta updates?"
        )
        result = HtmlMessageDialog(
            self.frame,
            "Beta updates",
            body,
            [("Cancel", wx.ID_CANCEL), ("I understand, enable beta", wx.ID_YES)],
        ).show_modal()
        return result == wx.ID_YES

    def _download_update_release(self, release: GitHubRelease) -> None:
        """Auto-download the release asset to <app data>/updates, off-thread.

        If the release has no downloadable asset, open its page instead.
        """
        import threading

        from quill.core.paths import app_data_dir

        url = release.download_url or ""
        if "/releases/download/" not in url:
            if url and webbrowser.open(url):
                self._set_status(f"Opened download page for {release.version}")
                self._record_notification(f"Opened update page for {release.version}", "update")
            else:
                self._set_status("No downloadable update asset found")
            return

        target_dir = app_data_dir() / "updates"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / (url.rsplit("/", 1)[-1] or f"quill-{release.version}")
        self._set_status(f"Downloading update {release.version}...")

        def worker() -> None:
            try:
                download_release_asset(url, target)
            except Exception as exc:  # noqa: BLE001
                self._wx.CallAfter(
                    self._record_notification, f"Update download failed: {exc}", "update"
                )
                self._wx.CallAfter(self._set_status, "Update download failed")
                return
            self._wx.CallAfter(
                self._record_notification,
                f"Update {release.version} downloaded to {target}",
                "update",
            )
            self._wx.CallAfter(self._set_status, f"Downloaded update {release.version}")
            self._wx.CallAfter(self._announce, f"Update {release.version} downloaded")

        threading.Thread(target=worker, daemon=True).start()

    def _open_update_download_flow(self, manifest: UpdateManifest) -> None:
        wx = self._wx
        close_now = self._show_message_box(
            (
                f"Quill installer update {manifest.version} requires the editor to close.\n\n"
                "Open the download page and close Quill now?"
            ),
            "Install Update",
            wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if close_now != wx.YES:
            opened = webbrowser.open(manifest.download_url)
            if opened:
                self._set_status(f"Opened download page for {manifest.version}")
                self._record_notification(
                    (
                        f"Opened update download for {manifest.version}. "
                        "Close Quill before running installer."
                    ),
                    "update",
                )
                return
            self._set_status("Could not open update download page")
            self._record_notification("Could not open update download page", "update")
            return
        if not self._can_close_all_documents():
            self._set_status("Update cancelled")
            self._record_notification(
                f"Update {manifest.version} cancelled before closing documents",
                "update",
            )
            return
        opened = webbrowser.open(manifest.download_url)
        if not opened:
            self._set_status("Could not open update download page")
            self._record_notification("Could not open update download page", "update")
            return
        self._record_notification(f"Opened update download for {manifest.version}", "update")
        self._set_status(f"Closing Quill for update {manifest.version}")
        self.exit_app()

    def validate_contrast(self) -> None:
        wx = self._wx
        checks = validate_theme_contrast(self.settings.theme)
        report = render_contrast_report(self.settings.theme, checks)
        self._show_message_box(report, "Contrast Validation", wx.ICON_INFORMATION | wx.OK)
        failed = [check for check in checks if not check.passes_normal_text]
        if failed:
            self._set_status("Contrast validation found failing pairs")
            self._record_notification("Contrast validation reported failures", "accessibility")
            return
        self._set_status("Contrast validation passed")
        self._record_notification("Contrast validation passed", "accessibility")

    def show_link_inventory(self) -> None:
        wx = self._wx
        inventory = collect_link_inventory(self.editor.GetValue())
        report = render_link_inventory_report(inventory)
        self._show_message_box(report, "Link Inventory", wx.ICON_INFORMATION | wx.OK)
        self._set_status(
            f"Link inventory: {len(inventory.links)} link(s), {len(inventory.images)} image(s)"
        )

    def compare_with_file(self) -> None:
        wx = self._wx
        with wx.FileDialog(
            self.frame,
            "Compare with file",
            wildcard=(
                "Text files (*.txt;*.md;*.html;*.htm;*.xhtml)|*.txt;*.md;*.html;*.htm;*.xhtml|"
                "All files (*.*)|*.*"
            ),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Compare with file") != wx.ID_OK:
                return
            target = Path(dialog.GetPath())
        other_document = read_text_document(target)
        source_documents = [
            (self.document.name, self.editor.GetValue()),
            (target.name, other_document.text),
        ]
        if not self._start_compare_session(source_documents):
            self._set_status(f"No differences from {target.name}")
            return
        current_name = self.document.name
        diff_text = build_unified_diff(
            self.editor.GetValue(),
            other_document.text,
            current_name,
            target.name,
        )
        max_chars = 12000
        if len(diff_text) > max_chars:
            diff_text = diff_text[:max_chars] + "\n... (truncated)\n"
        self._show_message_box(diff_text, "Compare with File", wx.ICON_INFORMATION | wx.OK)
        self._set_status(f"Compared with {target.name}")

    def compare_open_documents(self) -> None:
        if len(self._document_tabs) < 2:
            self._set_status("Open at least two documents to compare")
            return
        source_documents = [
            (tab.document.name, tab.editor.GetValue()) for tab in self._document_tabs
        ]
        if not self._start_compare_session(source_documents):
            self._set_status("No differences across open documents")
            return
        self._set_status(
            f"Compare session started. {len(source_documents)} documents. "
            f"{len(self._compare_session.groups)} differing line groups found."
        )

    def compare_next_difference(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        session.current_index = (session.current_index + 1) % len(session.groups)
        self.compare_announce_difference()

    def compare_previous_difference(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        session.current_index = (session.current_index - 1) % len(session.groups)
        self.compare_announce_difference()

    def compare_announce_difference(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        group = session.groups[session.current_index]
        if session.synchronized_navigation:
            self._focus_active_document_on_difference(group)
        self._set_status(self._render_compare_group(group, len(session.groups)))

    def open_compare_difference_list(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        wx = self._wx
        choices = [self._render_compare_choice(group) for group in session.groups]
        with wx.SingleChoiceDialog(
            self.frame,
            "Select a difference:",
            "Difference List",
            choices=choices,
        ) as dialog:
            dialog.SetSelection(session.current_index)
            if self._show_modal_dialog(dialog, "Difference List") != wx.ID_OK:
                return
            selection = dialog.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        session.current_index = selection
        self.compare_announce_difference()

    def toggle_compare_synchronization(self) -> None:
        session = self._compare_session
        if session is None:
            self._set_status("No active compare session")
            return
        session.synchronized_navigation = not session.synchronized_navigation
        state = "on" if session.synchronized_navigation else "off"
        self._set_status(f"Synchronized compare navigation {state}")

    def open_compare_options(self) -> None:
        wx = self._wx
        trailing = (
            self._show_message_box(
                "Ignore trailing spaces while comparing?",
                "Compare Options",
                wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
            )
            == wx.YES
        )
        endings = (
            self._show_message_box(
                "Ignore line-ending differences (CRLF vs LF)?",
                "Compare Options",
                wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
            )
            == wx.YES
        )
        self._compare_ignore_trailing_spaces = trailing
        self._compare_ignore_line_endings = endings
        session = self._compare_session
        if session is not None:
            self._start_compare_session(session.source_documents)
        self._set_status("Updated compare options")

    def create_compare_summary_document(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        summary = self._build_compare_summary_text(session)
        self._create_document_tab(
            Document(text=summary, path=None, modified=False),
            select=True,
        )
        self._set_status("Opened compare summary document")

    def copy_current_difference(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        group = session.groups[session.current_index]
        text = self._render_compare_group(group, len(session.groups))
        if not self._copy_to_clipboard(text):
            self._set_status("Could not copy current difference")
            return
        self._set_status("Copied current difference")

    def copy_all_differences(self) -> None:
        session = self._compare_session
        if session is None or not session.groups:
            self._set_status("No active compare session")
            return
        text = self._build_compare_summary_text(session)
        if not self._copy_to_clipboard(text):
            self._set_status("Could not copy all differences")
            return
        self._set_status("Copied all differences")

    def _start_compare_session(self, source_documents: list[tuple[str, str]]) -> bool:
        groups = self._build_compare_groups(source_documents)
        if not groups:
            self._compare_session = None
            return False
        self._compare_session = _CompareSession(source_documents=source_documents, groups=groups)
        self._set_status(
            f"Compare session started. {len(source_documents)} documents. "
            f"{len(groups)} differing line groups found. "
            "Press F8 for next difference, Shift+F8 for previous difference, "
            "Ctrl+F8 for current difference."
        )
        self.compare_announce_difference()
        return True

    def _build_compare_groups(
        self, source_documents: list[tuple[str, str]]
    ) -> list[_CompareDifferenceGroup]:
        if len(source_documents) < 2:
            return []
        split_lines = [text.splitlines() for _name, text in source_documents]
        max_lines = max((len(lines) for lines in split_lines), default=0)
        groups: list[_CompareDifferenceGroup] = []
        start_line: int | None = None

        def flush(end_line_exclusive: int) -> None:
            nonlocal start_line
            if start_line is None:
                return
            block_end = end_line_exclusive - 1
            groups.append(
                self._build_compare_group(
                    source_documents, split_lines, start_line, block_end, len(groups) + 1
                )
            )
            start_line = None

        for line_index in range(max_lines):
            normalized = [
                self._normalize_compare_line(lines[line_index]) if line_index < len(lines) else None
                for lines in split_lines
            ]
            baseline = normalized[0]
            same = all(value == baseline for value in normalized[1:])
            if same:
                flush(line_index)
                continue
            if start_line is None:
                start_line = line_index
        flush(max_lines)
        return groups

    def _build_compare_group(
        self,
        source_documents: list[tuple[str, str]],
        split_lines: list[list[str]],
        start_line: int,
        end_line: int,
        group_index: int,
    ) -> _CompareDifferenceGroup:
        blocks: list[_CompareLineBlock] = []
        for doc_index, (doc_name, _text) in enumerate(source_documents):
            lines = split_lines[doc_index]
            if start_line >= len(lines):
                blocks.append(_CompareLineBlock(doc_name, None, None, []))
                continue
            chunk = lines[start_line : min(end_line + 1, len(lines))]
            start = start_line + 1
            finish = start + len(chunk) - 1
            blocks.append(_CompareLineBlock(doc_name, start, finish, chunk))
        kind = self._classify_difference_kind(blocks)
        return _CompareDifferenceGroup(index=group_index, kind=kind, blocks=blocks)

    def _normalize_compare_line(self, line: str) -> str:
        normalized = line
        if self._compare_ignore_line_endings:
            normalized = normalized.rstrip("\r\n")
        if self._compare_ignore_trailing_spaces:
            normalized = normalized.rstrip()
        return normalized

    def _classify_difference_kind(self, blocks: list[_CompareLineBlock]) -> str:
        if len(blocks) != 2:
            return "changed"
        left_text = "\n".join(blocks[0].text)
        right_text = "\n".join(blocks[1].text)
        if not blocks[0].text and blocks[1].text:
            return "added"
        if blocks[0].text and not blocks[1].text:
            return "removed"
        if left_text == right_text:
            return "changed"
        if left_text.lower() == right_text.lower():
            return "case-only"
        left_compact = re.sub(r"\s+", "", left_text)
        right_compact = re.sub(r"\s+", "", right_text)
        if left_compact == right_compact:
            return "whitespace-only"
        left_punct = re.sub(r"[^\w\s]", "", left_text)
        right_punct = re.sub(r"[^\w\s]", "", right_text)
        if left_punct == right_punct:
            return "punctuation-only"
        if unicodedata.normalize("NFKC", left_text) == unicodedata.normalize("NFKC", right_text):
            return "unicode-only"
        return "changed"

    def _focus_active_document_on_difference(self, group: _CompareDifferenceGroup) -> None:
        active_name = self.document.name
        for block in group.blocks:
            if block.document_name != active_name or block.start_line is None:
                continue
            self._move_caret_to_line(block.start_line)
            return

    def _move_caret_to_line(self, line_number: int) -> None:
        if line_number < 1:
            return
        text = self.editor.GetValue()
        starts = [0]
        for line in text.splitlines(keepends=True):
            starts.append(starts[-1] + len(line))
        if line_number >= len(starts):
            position = starts[-1]
        else:
            position = starts[line_number - 1]
        self.editor.SetInsertionPoint(position)
        self.editor.SetSelection(position, position)

    def _render_compare_choice(self, group: _CompareDifferenceGroup) -> str:
        first = group.blocks[0]
        line_label = "line ?"
        if first.start_line is not None:
            line_label = f"line {first.start_line}"
        preview = ""
        if first.text:
            preview = first.text[0].strip()
        if preview:
            preview = f" {preview[:60]}"
        return f"Difference {group.index}: {group.kind} at {line_label}.{preview}"

    def _render_compare_group(self, group: _CompareDifferenceGroup, total: int) -> str:
        parts = [f"Difference {group.index} of {total}. {group.kind}."]
        for block in group.blocks:
            if block.start_line is None:
                parts.append(f"{block.document_name}: no corresponding lines.")
                continue
            if block.start_line == block.end_line:
                location = f"line {block.start_line}"
            else:
                location = f"lines {block.start_line}-{block.end_line}"
            preview = " ".join(block.text[:2]).strip()[:140] if block.text else "(empty)"
            parts.append(f"{block.document_name} {location}: {preview}")
        return " ".join(parts)

    def _build_compare_summary_text(self, session: _CompareSession) -> str:
        lines = [
            "Compare Summary",
            f"Documents: {', '.join(name for name, _text in session.source_documents)}",
            (
                "Options: "
                + (
                    "ignored trailing spaces"
                    if self._compare_ignore_trailing_spaces
                    else "kept trailing spaces"
                )
                + ", "
                + (
                    "ignored line endings"
                    if self._compare_ignore_line_endings
                    else "kept line endings"
                )
            ),
            "",
            f"{len(session.groups)} differences found.",
            "",
        ]
        for group in session.groups:
            lines.append(f"Difference {group.index}: {group.kind}")
            for block in group.blocks:
                if block.start_line is None:
                    lines.append(f"- {block.document_name}: no corresponding lines")
                    continue
                if block.start_line == block.end_line:
                    location = f"line {block.start_line}"
                else:
                    location = f"lines {block.start_line}-{block.end_line}"
                text = " | ".join(block.text[:3]).strip()
                lines.append(f"- {block.document_name} {location}: {text}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _prompt_search(
        self, title: str, replacement: bool = False
    ) -> tuple[str, str | None, SearchOptions] | None:
        wx = self._wx
        default_query = self._last_find_query or (
            self._search_history[0] if self._search_history else ""
        )
        dialog = wx.Dialog(self.frame, title=title, size=(460, 0))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(wx.StaticText(panel, label="Find text:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        query_ctrl = wx.TextCtrl(panel, value=default_query, style=wx.TE_PROCESS_ENTER)
        root.Add(query_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

        replacement_ctrl = None
        if replacement:
            root.Add(wx.StaticText(panel, label="Replace with:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
            replacement_ctrl = wx.TextCtrl(panel, value="", style=wx.TE_PROCESS_ENTER)
            root.Add(replacement_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

        mode_labels = ["Plain text", "Whole word", "Regular expression", "Wildcard"]
        root.Add(wx.StaticText(panel, label="Search mode:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        mode_choice = wx.Choice(panel, choices=mode_labels)
        mode_choice.SetSelection(0)
        root.Add(mode_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

        case_sensitive = wx.CheckBox(panel, label="Case sensitive")
        root.Add(case_sensitive, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
            ok_button = buttons.FindWindowById(wx.ID_OK)
            if ok_button is not None:
                ok_button.SetDefault()
        if hasattr(dialog, "SetAffirmativeId"):
            dialog.SetAffirmativeId(wx.ID_OK)
        if hasattr(dialog, "SetEscapeId"):
            dialog.SetEscapeId(wx.ID_CANCEL)

        panel.SetSizer(root)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        dialog.SetSizerAndFit(outer)

        def submit(_event: object) -> None:
            dialog.EndModal(wx.ID_OK)

        query_ctrl.Bind(wx.EVT_TEXT_ENTER, submit)
        if replacement_ctrl is not None:
            replacement_ctrl.Bind(wx.EVT_TEXT_ENTER, submit)

        def focus_query() -> None:
            query_ctrl.SetFocus()
            query_ctrl.SetSelection(0, len(default_query))

        if hasattr(wx, "CallAfter"):
            wx.CallAfter(focus_query)
        else:
            focus_query()

        def _on_char_hook(event: object) -> None:
            key_code = event.GetKeyCode()
            if key_code == wx.WXK_ESCAPE:
                dialog.EndModal(wx.ID_CANCEL)
                return
            if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                submit(event)
                return
            event.Skip()

        dialog.Bind(wx.EVT_CHAR_HOOK, _on_char_hook)
        try:
            if self._show_modal_dialog(dialog, title) != wx.ID_OK:
                return None
            query = query_ctrl.GetValue()
            if not query:
                return None
            mode = mode_choice.GetStringSelection() or mode_labels[0]
            options = SearchOptions(
                case_sensitive=case_sensitive.GetValue(),
                whole_word=mode == "Whole word",
                use_regex=mode == "Regular expression",
                wildcard=mode == "Wildcard",
            )
            replacement_value = (
                replacement_ctrl.GetValue() if replacement_ctrl is not None else None
            )
            return query, replacement_value, options
        finally:
            dialog.Destroy()

    def find_text(self) -> None:
        wx = self._wx
        prompt = self._prompt_search("Find")
        if prompt is None:
            self._set_status("Find cancelled")
            return
        query, _replacement, options = prompt
        self._last_find_query = query
        self._last_search_options = options
        self._search_history = add_search_term(query)

        text = self.editor.GetValue()
        try:
            matches = find_matches(text, query, options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Find", wx.ICON_ERROR | wx.OK)
            self._set_status("Find error")
            return
        if not matches:
            self._show_message_box("No matches found.", "Find", wx.ICON_INFORMATION | wx.OK)
            self._set_status("No matches found")
            return

        cursor = self.editor.GetInsertionPoint()
        chosen: tuple[int, int] | None = None
        for current_start, current_end in matches:
            if current_start >= cursor:
                chosen = (current_start, current_end)
                break
        wrapped = False
        if chosen is None and self.settings.wrap_find:
            chosen = matches[0]
            wrapped = True
        if chosen is None:
            self._set_status("No matches found from the current position")
            return
        start, end = chosen
        self.editor.SetFocus()
        self._ensure_extend_selection_anchor()
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._move_point(end)
        else:
            self.editor.SetSelection(start, end)
            self.editor.SetInsertionPoint(end)
        self._last_match = chosen
        wrap_suffix = " (wrapped)" if wrapped else ""
        self._set_status(f"Found at position {start + 1}{wrap_suffix}")

    def find_next(self) -> None:
        self._find_relative(reverse=False)

    def find_previous(self) -> None:
        self._find_relative(reverse=True)

    def _find_relative(self, reverse: bool) -> None:
        if not self._last_find_query:
            self.find_text()
            return

        text = self.editor.GetValue()
        try:
            matches = find_matches(text, self._last_find_query, self._last_search_options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Find", self._wx.ICON_ERROR | self._wx.OK)
            self._set_status("Find error")
            return
        if not matches:
            self._set_status("No matches found")
            return

        cursor = self.editor.GetInsertionPoint()
        selected_start, selected_end = self.editor.GetSelection()
        if selected_start != selected_end:
            cursor = selected_start if reverse else selected_end

        chosen: tuple[int, int] | None = None
        wrapped = False
        if reverse:
            for start, end in reversed(matches):
                if end <= cursor:
                    chosen = (start, end)
                    break
            if chosen is None and self.settings.wrap_find:
                chosen = matches[-1]
                wrapped = True
        else:
            for start, end in matches:
                if start >= cursor:
                    chosen = (start, end)
                    break
            if chosen is None and self.settings.wrap_find:
                chosen = matches[0]
                wrapped = True

        if chosen is None:
            self._set_status("No matches found from the current position")
            return

        start, end = chosen
        self.editor.SetFocus()
        self._ensure_extend_selection_anchor()
        if self._extend_selection_mode and self._extend_selection_anchor is not None:
            self._move_point(start if reverse else end)
        else:
            self.editor.SetSelection(start, end)
            self.editor.SetInsertionPoint(end)
        self._last_match = chosen
        direction = "previous" if reverse else "next"
        wrap_suffix = " (wrapped)" if wrapped else ""
        self._set_status(f"Found {direction} at position {start + 1}{wrap_suffix}")

    def _ensure_extend_selection_anchor(self) -> None:
        if not self._extend_selection_mode or self._extend_selection_anchor is not None:
            return
        selection_start, selection_end = self.editor.GetSelection()
        if selection_start != selection_end:
            self._extend_selection_anchor = selection_start
            return
        self._extend_selection_anchor = self.editor.GetInsertionPoint()

    def find_all_matches(self) -> None:
        wx = self._wx
        if not self._last_find_query:
            self.find_text()
            if not self._last_find_query:
                return

        text = self.editor.GetValue()
        try:
            matches = find_matches(text, self._last_find_query, self._last_search_options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Find All Matches", wx.ICON_ERROR | wx.OK)
            self._set_status("Find error")
            return
        if not matches:
            self._show_message_box(
                "No matches found.",
                "Find All Matches",
                wx.ICON_INFORMATION | wx.OK,
            )
            self._set_status("No matches found")
            return

        lines = text.splitlines(keepends=True)
        starts = [0]
        for line in lines:
            starts.append(starts[-1] + len(line))

        def locate(position: int) -> tuple[int, int]:
            line_number = 1
            for index in range(1, len(starts)):
                if starts[index] > position:
                    line_number = index
                    break
            else:
                line_number = max(1, len(starts) - 1)
            column = position - starts[line_number - 1] + 1
            return line_number, column

        details: list[str] = []
        for idx, (start, _end) in enumerate(matches[:25], start=1):
            line_number, column = locate(start)
            details.append(f"{idx}. Line {line_number}, Column {column}")
        more = ""
        if len(matches) > 25:
            more = f"\n...and {len(matches) - 25} more"

        self._show_message_box(
            f'Matches for "{self._last_find_query}": {len(matches)}\n\n'
            + "\n".join(details)
            + more,
            "Find All Matches",
            wx.ICON_INFORMATION | wx.OK,
        )
        self._set_status(f"Found {len(matches)} match(es)")

    def replace_text(self) -> None:
        wx = self._wx
        prompt = self._prompt_search("Replace", replacement=True)
        if prompt is None:
            self._set_status("Replace cancelled")
            return
        query, replacement, options = prompt
        if replacement is None:
            self._set_status("Replace cancelled")
            return
        self._search_history = add_search_term(query)
        self._last_find_query = query
        self._last_search_options = options

        text = self.editor.GetValue()
        try:
            matches = find_matches(text, query, options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Replace", wx.ICON_ERROR | wx.OK)
            self._set_status("Replace error")
            return
        if not matches:
            self._set_status("No replacements made")
            return

        cursor = self.editor.GetInsertionPoint()
        selected_start, selected_end = self.editor.GetSelection()
        if selected_start != selected_end:
            cursor = selected_end
        chosen: tuple[int, int] | None = None
        wrapped = False
        for start, end in matches:
            if start >= cursor:
                chosen = (start, end)
                break
        if chosen is None and self.settings.wrap_find:
            chosen = matches[0]
            wrapped = True
        if chosen is None:
            self._set_status("No replacements made from the current position")
            return

        start, end = chosen
        updated_text = text[:start] + replacement + text[end:]
        self._replace_document_text(updated_text)
        self.document.set_text(updated_text)
        replaced_end = start + len(replacement)
        self.editor.SetSelection(start, replaced_end)
        self.editor.SetInsertionPoint(replaced_end)
        self._last_match = (start, replaced_end)
        wrap_suffix = " (wrapped)" if wrapped else ""
        self._set_status(f"Replaced at position {start + 1}{wrap_suffix}")

    def replace_all_text(self) -> None:
        wx = self._wx
        prompt = self._prompt_search("Replace All", replacement=True)
        if prompt is None:
            self._set_status("Replace cancelled")
            return
        query, replacement, options = prompt
        if replacement is None:
            self._set_status("Replace cancelled")
            return
        self._search_history = add_search_term(query)
        self._last_find_query = query
        self._last_search_options = options

        text = self.editor.GetValue()
        try:
            matches = find_matches(text, query, options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Replace All", wx.ICON_ERROR | wx.OK)
            self._set_status("Replace error")
            return
        if not matches:
            self._set_status("No replacements made")
            return
        try:
            updated_text, replacements = replace_all(text, query, replacement, options)
        except SearchPatternError as error:
            self._show_message_box(str(error), "Replace All", wx.ICON_ERROR | wx.OK)
            self._set_status("Replace error")
            return
        if replacements == 0:
            self._set_status("No replacements made")
            return
        self._replace_document_text(updated_text)
        self.document.set_text(updated_text)
        self._set_status(f"Replaced {replacements} occurrence(s)")

    def _prompt_file_search(self, *, replace: bool) -> _FileSearchRequest | None:
        wx = self._wx
        default_root = self.document.path.parent if self.document.path is not None else Path.cwd()
        dialog_label = "Replace Across Files" if replace else "Search in Files"
        dialog = wx.Dialog(
            self.frame,
            title=dialog_label,
            size=(700, 0),
        )
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        form = wx.FlexGridSizer(0, 3, 8, 8)
        form.AddGrowableCol(1, 1)

        def add_row(label: str, control: object, button: object | None = None) -> None:
            form.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            form.Add(control, 1, wx.EXPAND)
            if button is None:
                form.AddSpacer(1)
            else:
                form.Add(button, 0)

        folder_picker = wx.DirPickerCtrl(panel, path=str(default_root))
        add_row("Starting folder", folder_picker)

        file_pattern_ctrl = wx.TextCtrl(panel, value="*")
        add_row("File pattern", file_pattern_ctrl)

        query_ctrl = wx.TextCtrl(panel, value="")
        add_row("Search text", query_ctrl)

        replacement_ctrl = None
        if replace:
            replacement_ctrl = wx.TextCtrl(panel, value="")
            add_row("Replacement", replacement_ctrl)

        mode_choice = wx.Choice(panel, choices=["Plain text", "Wildcard", "Regular expression"])
        mode_choice.SetSelection(0)
        add_row("Match mode", mode_choice)

        output_choice = wx.Choice(
            panel,
            choices=[
                "Filenames only",
                "Filenames with line numbers and counts",
                "Counts only",
                "Filename with line context",
            ],
        )
        output_choice.SetSelection(3)
        add_row("Output format", output_choice)

        case_sensitive = wx.CheckBox(panel, label="Case sensitive")
        whole_word = wx.CheckBox(panel, label="Whole word")
        root.Add(form, 0, wx.ALL | wx.EXPAND, 8)
        root.Add(case_sensitive, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        root.Add(whole_word, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        preview_before_replace = None
        if replace:
            preview_before_replace = wx.CheckBox(panel, label="Preview before replacing")
            preview_before_replace.SetValue(True)
            root.Add(preview_before_replace, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            root.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)
        dialog.SetSizerAndFit(root)
        query_ctrl.SetFocus()

        try:
            if self._show_modal_dialog(dialog, dialog_label) != wx.ID_OK:
                return None
            query = query_ctrl.GetValue().strip()
            if not query:
                self._show_message_box(
                    "Search text cannot be blank.",
                    dialog_label,
                    wx.ICON_ERROR | wx.OK,
                )
                return None
            mode = mode_choice.GetStringSelection()
            options = SearchOptions(
                case_sensitive=bool(case_sensitive.GetValue()),
                whole_word=bool(whole_word.GetValue()),
                use_regex=mode == "Regular expression",
                wildcard=mode == "Wildcard",
            )
            replacement_value = (
                replacement_ctrl.GetValue() if replacement_ctrl is not None else None
            )
            preview = (
                bool(preview_before_replace.GetValue())
                if preview_before_replace is not None
                else False
            )
            output_modes = (
                "filenames",
                "filenames_lines_counts",
                "counts",
                "context",
            )
            return _FileSearchRequest(
                root=Path(folder_picker.GetPath()),
                pattern=file_pattern_ctrl.GetValue().strip() or "*",
                query=query,
                replacement=replacement_value,
                options=options,
                output_mode=output_modes[
                    max(0, min(output_choice.GetSelection(), len(output_modes) - 1))
                ],
                preview_before_replace=preview,
            )
        finally:
            dialog.Destroy()

    def search_in_files(self) -> None:
        request = self._prompt_file_search(replace=False)
        if request is None:
            self._set_status("Search in files cancelled")
            return

        def work(progress: Callable[[str, int, int], None]) -> FileSearchReport:
            return search_files(
                request.root,
                request.pattern,
                request.query,
                request.options,
                progress=progress,
            )

        def on_success(result: object) -> None:
            report = result if isinstance(result, FileSearchReport) else None
            if report is None:
                return
            text = render_search_report(report, request.output_mode)
            self._open_generated_tab(f"Search - {request.pattern}", text)
            match_count = report.total_matches
            file_count = len(report.entries)
            self._set_status(f"Search complete: {match_count} match(es) in {file_count} file(s)")

        self._run_background_task("Searching files", work, on_success)

    def replace_in_files(self) -> None:
        request = self._prompt_file_search(replace=True)
        if request is None:
            self._set_status("Replace across files cancelled")
            return
        replacement = request.replacement or ""

        if not request.preview_before_replace:
            self._start_replace_files(request, replacement)
            return

        def preview_work(progress: Callable[[str, int, int], None]) -> FileSearchReport:
            return search_files(
                request.root,
                request.pattern,
                request.query,
                request.options,
                progress=progress,
            )

        def preview_done(result: object) -> None:
            report = result if isinstance(result, FileSearchReport) else None
            if report is None:
                return
            text = render_replace_preview(report, replacement)
            self._open_generated_tab(f"Replace Preview - {request.pattern}", text)
            if report.total_matches == 0:
                self._set_status("No matches found")
                return
            confirm = self._show_message_box(
                "Apply these replacements across files?",
                "Replace Across Files",
                self._wx.ICON_QUESTION | self._wx.YES_NO | self._wx.NO_DEFAULT,
            )
            if confirm == self._wx.YES:
                self._start_replace_files(request, replacement)
                return
            self._set_status("Replace across files cancelled")

        self._run_background_task("Previewing file replacements", preview_work, preview_done)

    def _start_replace_files(self, request: _FileSearchRequest, replacement: str) -> None:
        def work(progress: Callable[[str, int, int], None]) -> FileReplaceReport:
            return replace_files(
                request.root,
                request.pattern,
                request.query,
                replacement,
                request.options,
                progress=progress,
            )

        def on_success(result: object) -> None:
            report = result if isinstance(result, FileReplaceReport) else None
            if report is None:
                return
            text = render_replace_report(report)
            self._open_generated_tab(f"Replace Results - {request.pattern}", text)
            replacement_count = report.total_replacements
            file_count = len(report.entries)
            self._set_status(f"Replaced {replacement_count} occurrence(s) in {file_count} file(s)")

        self._run_background_task("Replacing files", work, on_success)

    def insert_link(self) -> None:
        wx = self._wx
        selected_text = self.editor.GetStringSelection()
        dialog = wx.Dialog(self.frame, title="Insert Link", size=(540, 0))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(wx.StaticText(panel, label="Display text:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        display_text_ctrl = wx.TextCtrl(panel, value=selected_text or "")
        root.Add(display_text_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
        root.Add(wx.StaticText(panel, label="URL:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        url_ctrl = wx.TextCtrl(panel, value="https://", style=wx.TE_PROCESS_ENTER)
        root.Add(url_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(root)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        dialog.SetSizerAndFit(outer)
        url_ctrl.Bind(wx.EVT_TEXT_ENTER, lambda _e: dialog.EndModal(wx.ID_OK))
        display_text_ctrl.Bind(wx.EVT_TEXT_ENTER, lambda _e: dialog.EndModal(wx.ID_OK))
        url_ctrl.SetFocus()
        try:
            if self._show_modal_dialog(dialog, "Insert Link") != wx.ID_OK:
                return
            url = url_ctrl.GetValue().strip()
            display_text = display_text_ctrl.GetValue()
        finally:
            dialog.Destroy()
        if not url:
            self._set_status("Insert link cancelled")
            return

        markup_kind = infer_markup_kind(self.document.path)
        snippet = build_link_text(markup_kind, display_text, url)
        result = InsertionResult(inserted_text=snippet, caret_offset=len(snippet))
        self._apply_insertion_result(result)
        self._set_status(f"Inserted link ({markup_kind})")

    def follow_link(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        target = find_link_at_cursor(text, cursor)
        if not target:
            self._set_status("No link at cursor")
            return
        if target.startswith("#"):
            self._set_status("Anchor links are not yet supported")
            return

        import webbrowser
        from urllib.parse import urlparse

        host = urlparse(target).netloc or target
        self._set_status(f"Opening {host}...")
        webbrowser.open(target)

    def preview_in_browser(self) -> None:
        if not self._document_tabs:
            self._set_status("No document open")
            return
        tab_index = (
            self._active_tab_index if self._active_tab_index >= 0 else self._current_tab_index()
        )
        if tab_index < 0 or tab_index >= len(self._document_tabs):
            self._set_status("No document open")
            return
        tab = self._document_tabs[tab_index]
        text = tab.editor.GetValue()
        kind = guess_preview_kind(tab.document.path, text)
        anchor = preview_anchor_for_text(text, tab.editor.GetInsertionPoint(), kind)
        title = f"{tab.document.name or 'Preview'} - Browser Preview"
        preview_dir = app_data_dir() / "browser-preview"
        preview_dir.mkdir(parents=True, exist_ok=True)
        safe_name = (
            re.sub(r"[^a-zA-Z0-9]+", "-", tab.document.name or "preview").strip("-") or "preview"
        )
        preview_path = preview_dir / f"{tab_index}-{safe_name}.html"
        payload = render_preview_html(title, text, kind, anchor)
        temp_path = preview_path.with_suffix(".tmp")
        temp_path.write_text(payload, encoding="utf-8")
        os.replace(temp_path, preview_path)
        browser_choice = normalize_browser_choice(self.settings.preview_browser)
        session = self._browser_preview_session
        if (
            session is None
            or session.tab_index != tab_index
            or session.preview_path != preview_path
            or session.browser_choice != browser_choice
        ):
            open_preview_url(preview_path.as_uri(), browser_choice)
            self._browser_preview_session = _BrowserPreviewSession(
                tab_index=tab_index,
                preview_path=preview_path,
                browser_choice=browser_choice,
                title=title,
            )
            self._set_status(
                f"Opened browser preview in {browser_choice_label_for_value(browser_choice)}"
            )
            return
        self._set_status("Refreshed browser preview")

    def preview_in_app(self) -> None:
        if not self._document_tabs:
            self._set_status("No document open")
            return
        tab_index = (
            self._active_tab_index if self._active_tab_index >= 0 else self._current_tab_index()
        )
        if tab_index < 0 or tab_index >= len(self._document_tabs):
            self._set_status("No document open")
            return
        tab = self._document_tabs[tab_index]
        text = tab.editor.GetValue()
        kind = guess_preview_kind(tab.document.path, text)
        anchor = preview_anchor_for_text(text, tab.editor.GetInsertionPoint(), kind)
        title = f"{tab.document.name or 'Preview'} - Preview"
        body = render_preview_body(text, kind)
        from quill.ui.preview_dialog import MarkdownPreviewDialog

        MarkdownPreviewDialog(self.frame, title, body, anchor).show()
        self._set_status("Opened preview")

    def _active_tab(self):
        index = self._active_tab_index if self._active_tab_index >= 0 else self._current_tab_index()
        if 0 <= index < len(self._document_tabs):
            return self._document_tabs[index]
        return None

    def toggle_side_preview(self) -> None:
        """Show / hide a live preview to the right of the editor (split view)."""
        tab = self._active_tab()
        if tab is None or getattr(tab, "splitter", None) is None:
            self._set_status("No document open")
            return
        splitter = tab.splitter
        if tab.preview is not None and splitter.IsSplit():
            splitter.Unsplit(tab.preview.control)
            self._set_status("Preview hidden")
            self.editor.SetFocus()
            return
        self._show_side_preview_for(tab)
        self._set_status("Preview shown on the right")

    def focus_preview(self) -> None:
        """Move focus into the preview pane (showing it first if needed).

        The editor is an edit field, so NVDA can't use browse-mode single-letter
        navigation there. The preview is a real web document, so once focus lands
        in it NVDA switches to browse mode and H / heading nav work natively.
        Press Escape or F6 in the preview to come back to the editor.
        """
        tab = self._active_tab()
        if tab is None or getattr(tab, "splitter", None) is None:
            self._set_status("No document open")
            return
        if tab.preview is None or not tab.splitter.IsSplit():
            self.toggle_side_preview()
        if tab.preview is not None and tab.splitter.IsSplit():
            tab.preview.control.SetFocus()
            self._set_status("Moved to preview. Press Escape or F6 to return to the editor.")

    def _focus_editor_from_preview(self) -> None:
        if self.editor is not None:
            self.editor.SetFocus()
            self._set_status("Back in the editor")

    def _refresh_side_preview(self) -> None:
        tab = self._active_tab()
        if tab is None or tab.preview is None:
            return
        splitter = getattr(tab, "splitter", None)
        if splitter is None or not splitter.IsSplit():
            return
        # Debounce: refresh shortly after typing pauses so each keystroke stays
        # snappy (re-rendering on every character can stutter the editor).
        timer = getattr(self, "_side_preview_timer", None)
        if timer is not None and timer.IsRunning():
            timer.Stop()
        self._side_preview_timer = self._wx.CallLater(250, self._update_side_preview, tab)

    def _update_side_preview(self, tab) -> None:
        text = tab.editor.GetValue()
        kind = guess_preview_kind(tab.document.path, text)
        tab.preview.update(render_preview_body(text, kind))

    def _refresh_browser_preview(self) -> None:
        session = self._browser_preview_session
        if session is None:
            return
        if session.tab_index != self._active_tab_index:
            return
        self.preview_in_browser()

    def _get_assistant(self) -> Assistant:
        assistant = getattr(self, "_assistant", None)
        if assistant is None:
            assistant = Assistant()
            self._assistant = assistant
            self._apply_style_to_assistant()
        return assistant

    def _apply_style_to_assistant(self) -> None:
        from quill.core.ai.style import load_style, style_preamble

        assistant = getattr(self, "_assistant", None)
        if assistant is not None:
            assistant.set_style_preamble(style_preamble(load_style()))

    def open_train_writing_style(self) -> None:
        from quill.core.ai.model_manager import load_ai_enabled

        if not load_ai_enabled():
            self._set_status(
                "AI is turned off. Enable 'Use Artificial Intelligence' in the AI menu."
            )
            return
        TrainStyleDialog(
            self.frame,
            self._get_assistant(),
            get_document=lambda: self.editor.GetValue(),
            announce=self._set_status,
        ).show()
        # Apply the (possibly updated) style to the assistant immediately.
        self._apply_style_to_assistant()

    def _on_toggle_ai_enabled(self, event: object) -> None:
        from quill.core.ai.model_manager import save_ai_enabled

        enabled = bool(event.IsChecked())
        save_ai_enabled(enabled)
        self._apply_ai_menu_enabled()
        self._refresh_ai_status()
        self._set_status("AI enabled" if enabled else "AI disabled")

    def _refresh_ai_status(self) -> None:
        """Check the active AI backend and update the AI Status badge (off-thread)."""
        from quill.core.ai.model_manager import load_ai_enabled

        if not load_ai_enabled():
            self._set_ai_menu_status_badge(None, "AI is turned off.", badge="Off")
            return
        self._set_ai_menu_status_badge(None, "Checking the AI backend...", badge="Checking...")

        def worker() -> None:
            try:
                from quill.core.ai.assistant import make_default_backend

                ok, reason = make_default_backend().is_available()
            except Exception as exc:  # noqa: BLE001
                ok, reason = False, str(exc)
            detail = "Ready." if ok else (reason or "Needs attention.")
            self._wx.CallAfter(self._set_ai_menu_status_badge, bool(ok), detail)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_ai_menu_enabled(self) -> None:
        """Enable/disable the AI menu items behind the 'Use Artificial Intelligence'
        toggle. The toggle and the status lines stay available so AI can be turned
        back on."""
        from quill.core.ai.model_manager import load_ai_enabled

        bar = self.frame.GetMenuBar()
        if bar is None:
            return
        enabled = load_ai_enabled()
        ai_item_ids = (
            self._id_ai_hub,
            self._id_ask_quill_chat,
            self._id_ai_model,
            self._id_ai_assistant,
            self._id_ai_prompt_studio,
            self._id_ai_agent_center,
            self._id_ai_rewrite_selection,
            self._id_ai_summarize_selection,
            self._id_ai_continue_writing,
            self._id_ai_fix_grammar,
            self._id_train_style,
        )
        for item_id in ai_item_ids:
            if bar.FindItemById(item_id) is not None:
                bar.Enable(item_id, enabled)

    def open_ask_quill_chat(self) -> None:
        from quill.core.ai.model_manager import load_ai_enabled

        if not load_ai_enabled():
            self._set_status(
                "AI is turned off. Enable 'Use Artificial Intelligence' in the AI menu."
            )
            return
        self._apply_style_to_assistant()
        tool_catalog = allowed_tools(self.commands, getattr(self, "features", None))
        dialog = AskQuillChatDialog(
            self.frame,
            self._get_assistant(),
            get_document=lambda: self.editor.GetValue(),
            get_selection=lambda: self.editor.GetStringSelection(),
            insert_text=self._ai_insert_text,
            replace_selection=self._ai_replace_selection,
            run_command=self._ai_run_command,
            tool_catalog=tool_catalog,
            announce=self._set_status,
        )
        dialog.show()

    def _ai_insert_text(self, text: str) -> None:
        self.editor.WriteText(text)

    def _ai_replace_selection(self, text: str) -> None:
        start, end = self.editor.GetSelection()
        if start != end:
            self.editor.Replace(start, end, text)
            self.editor.SetInsertionPoint(start + len(text))
        else:
            self.editor.WriteText(text)

    def _ai_run_command(self, command_id: str) -> None:
        self.commands.run(command_id)

    def open_ai_model_settings(self) -> None:
        # Combined AI Model & Connection — the model dialog hosts a button to the
        # connection settings, so there's one entry point for all AI setup.
        AIModelDialog(
            self.frame,
            announce=self._set_status,
            open_connection=self.open_ai_preferences,
        ).show()

    def open_ai_hub(self) -> None:
        dialog = AIHubDialog(
            self.frame,
            open_connection=self.open_ai_preferences,
            open_model_settings=self.open_ai_model_settings,
            open_writing_assistant=self.open_writing_assistant,
            open_prompt_studio=self.open_prompt_studio,
            open_agent_center=self.open_agent_center,
            announce=self._set_status,
        )
        dialog.show_modal()

    def open_writing_assistant(self, initial_prompt: str = "") -> None:
        dialog = WritingAssistantDialog(
            self.frame,
            self.commands,
            getattr(self, "features", None),
            open_python_tool=self.run_python_tool,
            selection_text=self._selected_text(),
            document_text=self.editor.GetValue(),
            initial_prompt=initial_prompt,
            assistant_enabled=getattr(self.settings, "assistant_enabled", False),
            prompt_style=getattr(self.settings, "assistant_prompt_style", "balanced"),
        )
        dialog.show_modal()

    def open_prompt_studio(self) -> None:
        dialog = PromptStudioDialog(
            self.frame,
            selection_text=self._selected_text(),
            document_text=self.editor.GetValue(),
            on_use_prompt=self.open_writing_assistant,
            announce=self._set_status,
        )
        dialog.show_modal()

    def open_agent_center(self) -> None:
        dialog = AgentCenterDialog(
            self.frame,
            selection_text=self._selected_text(),
            document_text=self.editor.GetValue(),
            on_use_prompt=self.open_writing_assistant,
            announce=self._set_status,
        )
        dialog.show_modal()

    def open_ai_rewrite_selection(self) -> None:
        self.open_writing_assistant(
            render_assistant_prompt(
                "rewrite",
                selection_text=self._selected_text(),
                document_text=self.editor.GetValue(),
            )
        )

    def open_ai_summarize_selection(self) -> None:
        self.open_writing_assistant(
            render_assistant_prompt(
                "summarize",
                selection_text=self._selected_text(),
                document_text=self.editor.GetValue(),
            )
        )

    def open_ai_continue_writing(self) -> None:
        self.open_writing_assistant(
            render_assistant_prompt(
                "continue",
                selection_text=self._selected_text() or self.editor.GetValue(),
                document_text=self.editor.GetValue(),
            )
        )

    def open_ai_fix_grammar(self) -> None:
        self.open_writing_assistant(
            render_assistant_prompt(
                "grammar",
                selection_text=self._selected_text(),
                document_text=self.editor.GetValue(),
            )
        )

    def run_python_tool(self) -> None:
        outline = [
            {"level": entry.level, "title": entry.title, "position": entry.position}
            for entry in self._outline_entries()
        ]
        dialog = RunPythonDialog(
            self.frame,
            document_text=self.editor.GetValue(),
            selection_text=self._selected_text(),
            outline=outline,
            apply_callback=self._apply_python_result,
        )
        dialog.show_modal()

    def _selected_text(self) -> str:
        start, end = self.editor.GetSelection()
        if start == end:
            return ""
        return self.editor.GetValue()[start:end]

    def _apply_python_result(self, updated_text: str) -> None:
        start, end = self.editor.GetSelection()
        current = self.editor.GetValue()
        if start != end:
            new_text = current[:start] + updated_text + current[end:]
            replace_start = start
        else:
            new_text = updated_text
            replace_start = 0
        self._replace_document_text(new_text)
        self.document.set_text(new_text)
        self._record_persistent_undo_state(new_text)
        if start != end:
            self.editor.SetSelection(replace_start, replace_start + len(updated_text))
            self.editor.SetInsertionPoint(replace_start + len(updated_text))
        else:
            self.editor.SetSelection(0, len(updated_text))
        self._maybe_autosave()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._set_status("Applied Python result")

    def select_line(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, end = line_span(text, cursor)
        self.editor.SetFocus()
        self.editor.SetSelection(start, end)
        self._set_status("Selected line")

    def select_paragraph(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, end = paragraph_span(text, cursor)
        self.editor.SetFocus()
        self.editor.SetSelection(start, end)
        self._set_status("Selected paragraph")

    def select_block(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, end = block_span(text, cursor)
        self.editor.SetFocus()
        self.editor.SetSelection(start, end)
        self._set_status("Selected block")

    def select_to_start_of_line(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, _end = line_span(text, cursor)
        self.editor.SetFocus()
        self.editor.SetSelection(start, cursor)
        self._set_status("Selected to start of line")

    def select_to_end_of_line(self) -> None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        _start, end = line_span(text, cursor)
        self.editor.SetFocus()
        self.editor.SetSelection(cursor, end)
        self._set_status("Selected to end of line")

    def select_to_start_of_document(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        self.editor.SetFocus()
        self.editor.SetSelection(0, cursor)
        self._set_status("Selected to start of document")

    def select_to_end_of_document(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        self.editor.SetFocus()
        self.editor.SetSelection(cursor, self.editor.GetLastPosition())
        self._set_status("Selected to end of document")

    def set_mark(self) -> None:
        position = self.editor.GetInsertionPoint()
        self._mark_ring.set_mark(position)
        line, column = line_column_for_position(self.editor.GetValue(), position)
        self._set_status(f"Mark ring point set at line {line}, column {column} (temporary jump)")

    def pop_mark(self) -> None:
        mark = self._mark_ring.pop_mark()
        if mark is None:
            self._set_status("No marks in ring. Marks are temporary jump points.")
            return
        self.editor.SetInsertionPoint(mark)
        self.editor.SetSelection(mark, mark)
        line, column = line_column_for_position(self.editor.GetValue(), mark)
        self._set_status(
            f"Popped to mark ring point at line {line}, column {column} (temporary jump)"
        )

    def exchange_point_and_mark(self) -> None:
        current = self.editor.GetInsertionPoint()
        target = self._mark_ring.exchange_point_and_mark(current)
        if target is None:
            self._set_status("No marks in ring. Marks are temporary jump points.")
            return
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        line, column = line_column_for_position(self.editor.GetValue(), target)
        self._set_status(f"Exchanged point and mark to line {line}, column {column}")

    def list_marks(self) -> None:
        wx = self._wx
        marks = self._mark_ring.list_marks()
        if not marks:
            self._set_status("No marks in ring. Marks are temporary jump points.")
            return
        lines: list[str] = []
        text = self.editor.GetValue()
        for index, position in enumerate(reversed(marks), start=1):
            line, column = line_column_for_position(text, position)
            lines.append(f"{index}. Line {line}, Column {column}")
        self._show_message_box(
            "\n".join(lines),
            "Mark Ring (Temporary Jump Points)",
            wx.ICON_INFORMATION | wx.OK,
        )
        self._set_status(f"Listed {len(marks)} mark(s)")

    def format_bold(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Bold is unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Bold is only available in Markdown or HTML documents")
            return
        selected_text = self.editor.GetStringSelection()
        if surface == "markdown":
            result = build_markdown_insertion("Bold", selected_text)
        else:
            result = build_html_insertion("strong", selected_text, {})
        self._apply_insertion_result(result)
        self._set_status(f"Applied bold ({surface})")

    def format_upper_case(self) -> None:
        self._transform_selection_or_document(to_upper, "Upper case")

    def format_lower_case(self) -> None:
        self._transform_selection_or_document(to_lower, "Lower case")

    def format_title_case(self) -> None:
        self._transform_selection_or_document(to_title, "Title case")

    def format_sentence_case(self) -> None:
        self._transform_selection_or_document(to_sentence_case, "Sentence case")

    def format_toggle_case(self) -> None:
        self._transform_selection_or_document(to_toggle_case, "Toggle case")

    def format_toggle_line_comment(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: toggle_line_comment(text, start, end, self.document.path),
            "Toggled line comment",
        )

    def format_toggle_block_comment(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: toggle_block_comment(text, start, end, self.document.path),
            "Toggled block comment",
        )

    def _indent_width(self) -> int:
        return max(1, int(getattr(self.settings, "indent_size", 4)))

    def _indent_unit(self) -> str:
        if bool(getattr(self.settings, "indent_with_tabs", False)):
            return "\t"
        return " " * self._indent_width()

    def format_indent(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: indent_lines(
                text,
                start,
                end,
                indent_unit=self._indent_unit(),
            ),
            "Indented lines",
        )

    def format_outdent(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: outdent_lines(
                text,
                start,
                end,
                indent_unit=self._indent_unit(),
            ),
            "Outdented lines",
        )

    def move_line_up(self) -> None:
        self._apply_line_operation(move_line_up, "Moved line up")

    def move_line_down(self) -> None:
        self._apply_line_operation(move_line_down, "Moved line down")

    def duplicate_line(self) -> None:
        self._apply_line_operation(duplicate_line, "Duplicated line")

    def delete_line(self) -> None:
        self._apply_line_operation(delete_line, "Deleted line")

    def join_lines(self) -> None:
        self._apply_line_operation(join_with_next_line, "Joined lines")

    def sort_lines_ascending(self) -> None:
        self._apply_text_block_operation(
            lambda text: sort_lines(text, descending=False),
            "Sorted lines ascending",
        )

    def sort_lines_descending(self) -> None:
        self._apply_text_block_operation(
            lambda text: sort_lines(text, descending=True),
            "Sorted lines descending",
        )

    def reverse_lines(self) -> None:
        self._apply_text_block_operation(reverse_lines, "Reversed lines")

    def remove_duplicate_lines(self) -> None:
        self._apply_text_block_operation(
            remove_duplicate_lines,
            "Removed duplicate lines",
        )

    def trim_trailing_whitespace(self) -> None:
        self._apply_text_block_operation(
            trim_trailing_whitespace,
            "Trimmed trailing whitespace",
        )

    def normalize_whitespace(self) -> None:
        self._apply_text_block_operation(normalize_whitespace, "Normalized whitespace")

    def convert_indentation_to_spaces(self) -> None:
        self._apply_text_block_operation(
            lambda text: convert_indentation_to_spaces(text, self._indent_width()),
            "Converted indentation to spaces",
        )

    def convert_indentation_to_tabs(self) -> None:
        self._apply_text_block_operation(
            lambda text: convert_indentation_to_tabs(text, self._indent_width()),
            "Converted indentation to tabs",
        )

    def format_italic(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Italic is unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Italic is only available in Markdown or HTML documents")
            return
        selected_text = self.editor.GetStringSelection()
        if surface == "markdown":
            result = build_markdown_insertion("Italic", selected_text)
        else:
            result = build_html_insertion("em", selected_text, {})
        self._apply_insertion_result(result)
        self._set_status(f"Applied italic ({surface})")

    def format_heading(self, level: int) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Heading tools are unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Headings are only available in Markdown or HTML documents")
            return
        selected_text = self.editor.GetStringSelection()
        if surface == "markdown":
            result = build_markdown_insertion(f"Heading {level}", selected_text)
        else:
            result = build_html_insertion(f"h{level}", selected_text, {})
        self._apply_insertion_result(result)
        self._set_status(f"Inserted heading {level} ({surface})")

    def decrease_heading_level(self) -> None:
        self._adjust_heading_level(-1)

    def increase_heading_level(self) -> None:
        self._adjust_heading_level(1)

    def style_headings(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Heading tools are unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Headings are only available in Markdown or HTML documents")
            return
        levels = self._prompt_heading_style_levels(surface)
        if levels is None:
            self._set_status("Heading styling cancelled")
            return
        style = self._prompt_heading_style()
        if style is None:
            self._set_status("Heading styling cancelled")
            return
        text = self.editor.GetValue()
        updated, changed = apply_heading_style(
            text, markup_kind=surface, style=style, levels=levels
        )
        if changed == 0:
            self._set_status("No headings matched the selected level")
            return
        self._replace_document_text(updated)
        self.document.set_text(updated)
        self._set_status(f"Styled {changed} heading{'s' if changed != 1 else ''}")

    def _prompt_heading_style_levels(self, surface: str) -> set[int] | None:
        options = ["All heading levels", "Current heading level"]
        choice = wx.GetSingleChoice(
            "Choose which headings to style.",
            "Style Headings",
            options,
            self.frame,
        )
        if not choice:
            return None
        if choice == "All heading levels":
            return set(range(1, 7))
        level = self._current_heading_level(surface)
        if level is None:
            self._set_status("Place the cursor on a heading line to style current level")
            return None
        return {level}

    def _current_heading_level(self, surface: str) -> int | None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, end = line_span(text, cursor)
        line_text = text[start:end].strip()
        if surface == "markdown":
            match = re.match(r"^(#{1,6})\s+", line_text)
            if match is None:
                return None
            return len(match.group(1))
        match = re.match(r"^<h([1-6])(?:\s[^>]*)?>", line_text, flags=re.IGNORECASE)
        if match is None:
            return None
        return int(match.group(1))

    def _prompt_heading_style(self) -> HeadingStyle | None:
        font_family = wx.GetTextFromUser(
            "Font family (leave blank to keep existing):",
            "Style Headings",
            parent=self.frame,
        )
        if font_family is None:
            return None
        size_text = wx.GetTextFromUser(
            "Font size in points (leave blank to keep existing):",
            "Style Headings",
            parent=self.frame,
        )
        if size_text is None:
            return None
        size_value: int | None = None
        cleaned_size = size_text.strip()
        if cleaned_size:
            try:
                parsed_size = int(cleaned_size)
            except ValueError:
                self._set_status("Heading style requires a whole-number font size")
                return None
            if parsed_size <= 0:
                self._set_status("Heading style requires a positive font size")
                return None
            size_value = parsed_size
        alignment_options = ["Keep existing", "Left", "Center", "Right", "Justify"]
        alignment_choice = wx.GetSingleChoice(
            "Text alignment:",
            "Style Headings",
            alignment_options,
            self.frame,
        )
        if not alignment_choice:
            return None
        align_value = None if alignment_choice == "Keep existing" else alignment_choice.lower()
        style = HeadingStyle(
            font_family=font_family.strip() or None,
            font_size_pt=size_value,
            text_align=align_value,
        )
        if not style.declarations():
            self._set_status("Specify at least one heading style option")
            return None
        return style

    def _adjust_heading_level(self, delta: int) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Heading tools are unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Headings are only available in Markdown or HTML documents")
            return
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        start, end = line_span(text, cursor)
        line_text = text[start:end]
        replacement: str | None = None
        old_level: int | None = None
        if surface == "markdown":
            match = re.match(r"^(#{1,6})\s+(.*)$", line_text)
            if match is not None:
                old_level = len(match.group(1))
                new_level = min(6, max(1, old_level + delta))
                if new_level == old_level:
                    direction = "minimum" if delta < 0 else "maximum"
                    self._set_status(f"Heading already at {direction} level")
                    return
                replacement = f"{'#' * new_level} {match.group(2)}"
        else:
            match = re.match(
                r"^\s*<h([1-6])([^>]*)>(.*)</h\1>\s*$",
                line_text,
                flags=re.IGNORECASE,
            )
            if match is not None:
                old_level = int(match.group(1))
                new_level = min(6, max(1, old_level + delta))
                if new_level == old_level:
                    direction = "minimum" if delta < 0 else "maximum"
                    self._set_status(f"Heading already at {direction} level")
                    return
                attributes = match.group(2)
                content = match.group(3)
                replacement = f"<h{new_level}{attributes}>{content}</h{new_level}>"
        if replacement is None:
            self._set_status("Place cursor on a heading line to adjust its level")
            return
        self.editor.SetSelection(start, end)
        self.editor.Replace(start, end, replacement)
        self.document.set_text(self.editor.GetValue())
        self._set_status("Adjusted heading level")

    def format_insert_bullet_list(self) -> None:
        self._insert_structure("Bullet List", "Inserted bullet list")

    def format_insert_numbered_list(self) -> None:
        self._insert_structure("Numbered List", "Inserted numbered list")

    def format_insert_task_list(self) -> None:
        self._insert_structure("Task List", "Inserted task list")

    def open_list_manager(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("List Manager is unavailable in this profile")
            return
        if infer_markup_kind(self.document.path) not in {"markdown", "plain"}:
            self._set_status("List Manager is only available in Markdown documents")
            return
        state = self._extract_list_manager_state()
        if state is None or not state.items:
            self._set_status("Place the cursor inside a Markdown list to open List Manager")
            return
        updated_text = self._show_list_manager_dialog(state)
        if updated_text is None:
            self._set_status("List Manager cancelled")
            return
        if updated_text == self.editor.GetValue():
            self._set_status("List Manager closed without changes")
            return
        self._replace_document_text(updated_text)
        self.document.set_text(updated_text)
        self._set_status("Applied list manager changes")

    def _extract_list_manager_state(self) -> _ListManagerState | None:
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        current_start, current_end = line_span(text, cursor)
        current_line = text[current_start:current_end]
        if self._parse_list_manager_line(current_line) is None:
            return None

        starts: list[int] = [0]
        for index, character in enumerate(text):
            if character == "\n":
                starts.append(index + 1)

        current_index = 0
        for index, start in enumerate(starts):
            if start <= current_start:
                current_index = index
            else:
                break

        def line_text(line_index: int) -> str:
            line_start = starts[line_index]
            line_end = starts[line_index + 1] if line_index + 1 < len(starts) else len(text)
            return text[line_start:line_end]

        top = current_index
        while top > 0 and self._parse_list_manager_line(line_text(top - 1)) is not None:
            top -= 1
        bottom = current_index
        while (
            bottom + 1 < len(starts)
            and self._parse_list_manager_line(line_text(bottom + 1)) is not None
        ):
            bottom += 1

        block_start = starts[top]
        block_end = starts[bottom + 1] if bottom + 1 < len(starts) else len(text)
        block_lines = [line_text(i) for i in range(top, bottom + 1)]
        parsed: list[tuple[str, str, str, bool, str]] = []
        indent_widths: list[int] = []
        for raw_line in block_lines:
            item = self._parse_list_manager_line(raw_line)
            if item is None:
                return None
            parsed.append(item)
            indent, _kind, _bullet, _checked, _body = item
            indent_widths.append(self._indent_measure(indent))
        if not parsed:
            return None

        base_indent_width = min(indent_widths)
        step_width = max(1, self._indent_width())
        items: list[_ListManagerItem] = []
        for indent, kind, bullet, checked, body in parsed:
            level = max(0, (self._indent_measure(indent) - base_indent_width) // step_width)
            items.append(
                _ListManagerItem(
                    kind=kind,
                    text=body,
                    level=level,
                    bullet=bullet or "-",
                    checked=checked,
                )
            )
        return _ListManagerState(
            start=block_start,
            end=block_end,
            trailing_newline=text[block_end - 1 : block_end] == "\n",
            base_indent=" " * base_indent_width,
            items=items,
        )

    def _parse_list_manager_line(self, line: str) -> tuple[str, str, str, bool, str] | None:
        text = line.rstrip("\r\n")
        match = re.match(
            r"^(?P<indent>[ \t]*)(?:(?P<number>\d+)(?P<number_sep>[.)])|(?P<bullet>[-+*]))"
            r"(?P<spacing>[ \t]+)(?:(?P<task>\[[ xX]\])(?P<task_spacing>[ \t]+))?"
            r"(?P<body>.*)$",
            text,
        )
        if match is None:
            return None
        indent = match.group("indent") or ""
        bullet = match.group("bullet") or "-"
        task = match.group("task")
        body = match.group("body") or ""
        if task is not None:
            return indent, "task", bullet, "x" in task.lower(), body
        if match.group("number") is not None:
            return indent, "ordered", ".", False, body
        return indent, "bullet", bullet, False, body

    def _indent_measure(self, indent: str) -> int:
        return len(indent.expandtabs(self._indent_width()))

    def _render_list_manager_block(self, state: _ListManagerState) -> str:
        lines: list[str] = []
        ordered_counters: dict[int, int] = {}
        for item in state.items:
            level = max(0, item.level)
            indent = f"{state.base_indent}{self._indent_unit() * level}"
            for key in list(ordered_counters):
                if key > level:
                    ordered_counters.pop(key, None)
            if item.kind == "ordered":
                ordered_counters[level] = ordered_counters.get(level, 0) + 1
                marker = f"{ordered_counters[level]}. "
            elif item.kind == "task":
                marker = f"{item.bullet} [{'x' if item.checked else ' '}] "
                ordered_counters[level] = 0
            else:
                marker = f"{item.bullet} "
                ordered_counters[level] = 0
            lines.append(f"{indent}{marker}{item.text}".rstrip())
        block_text = "\n".join(lines)
        if state.trailing_newline:
            block_text += "\n"
        return block_text

    def _show_list_manager_dialog(self, state: _ListManagerState) -> str | None:
        wx = self._wx
        working_items = [
            _ListManagerItem(
                kind=item.kind,
                text=item.text,
                level=item.level,
                bullet=item.bullet,
                checked=item.checked,
            )
            for item in state.items
        ]
        selected_index: int | None = 0 if working_items else None
        dialog = wx.Dialog(self.frame, title="List Manager", size=(1020, 700))
        splitter = wx.SplitterWindow(dialog, style=wx.SP_LIVE_UPDATE)
        tree = wx.TreeCtrl(
            splitter,
            style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HAS_VARIABLE_ROW_HEIGHT,
        )
        preview = wx.TextCtrl(splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
        splitter.SplitVertically(tree, preview, 420)
        splitter.SetMinimumPaneSize(260)
        item_indexes: dict[object, int] = {}
        root = tree.AddRoot("List Items")

        def list_preview(index: int | None) -> str:
            if index is None or index < 0 or index >= len(working_items):
                return "No list item selected."
            item = working_items[index]
            kind_label = {"bullet": "Bullet", "ordered": "Numbered", "task": "Task"}[item.kind]
            status = f"{kind_label} item at level {item.level + 1}"
            if item.kind == "task":
                status = f"{status} ({'checked' if item.checked else 'unchecked'})"
            return f"{status}\n\n{item.text or '(empty item)'}"

        def build_tree() -> None:
            nonlocal root, selected_index
            tree.DeleteAllItems()
            root = tree.AddRoot("List Items")
            item_indexes.clear()
            node_stack: list[tuple[int, object]] = []
            first_item = None
            selected_item = None
            for index, item in enumerate(working_items):
                label_prefix = (
                    "[ ]"
                    if item.kind == "task" and not item.checked
                    else "[x]"
                    if item.kind == "task"
                    else "1."
                    if item.kind == "ordered"
                    else item.bullet
                )
                label = f"{label_prefix} {item.text or '(empty item)'}"
                while node_stack and node_stack[-1][0] >= item.level:
                    node_stack.pop()
                parent = root if not node_stack else node_stack[-1][1]
                node = tree.AppendItem(parent, label)
                item_indexes[node] = index
                if first_item is None:
                    first_item = node
                if selected_index == index:
                    selected_item = node
                node_stack.append((item.level, node))
            tree.Expand(root)
            target = selected_item if selected_item is not None else first_item
            if target is not None:
                tree.SelectItem(target)
                selected_index = item_indexes.get(target)
            else:
                selected_index = None
            preview.ChangeValue(list_preview(selected_index))

        def subtree_bounds(index: int) -> tuple[int, int]:
            level = working_items[index].level
            end = index + 1
            while end < len(working_items) and working_items[end].level > level:
                end += 1
            return index, end

        def update_after_change(message: str, preferred_index: int | None) -> None:
            nonlocal selected_index
            if not working_items:
                selected_index = None
            elif preferred_index is None:
                selected_index = min(len(working_items) - 1, selected_index or 0)
            else:
                selected_index = max(0, min(preferred_index, len(working_items) - 1))
            build_tree()
            self._set_status(message)

        def require_selection() -> int | None:
            if selected_index is None or selected_index < 0 or selected_index >= len(working_items):
                return None
            return selected_index

        def move_up() -> None:
            index = require_selection()
            if index is None:
                return
            start, end = subtree_bounds(index)
            target = start - 1
            while target >= 0 and working_items[target].level != working_items[index].level:
                target -= 1
            if target < 0:
                return
            block = working_items[start:end]
            del working_items[start:end]
            insert_at = target
            working_items[insert_at:insert_at] = block
            update_after_change("Moved list item up", insert_at)

        def move_down() -> None:
            index = require_selection()
            if index is None:
                return
            start, end = subtree_bounds(index)
            target = end
            while (
                target < len(working_items)
                and working_items[target].level != working_items[index].level
            ):
                target += 1
            if target >= len(working_items):
                return
            next_start, next_end = subtree_bounds(target)
            block = working_items[start:end]
            del working_items[start:end]
            insert_at = next_end - len(block)
            working_items[insert_at:insert_at] = block
            update_after_change("Moved list item down", insert_at)

        def promote() -> None:
            index = require_selection()
            if index is None or working_items[index].level == 0:
                return
            start, end = subtree_bounds(index)
            for cursor in range(start, end):
                working_items[cursor].level = max(0, working_items[cursor].level - 1)
            update_after_change("Promoted list item", start)

        def demote() -> None:
            index = require_selection()
            if index is None or index == 0:
                return
            previous_level = working_items[index - 1].level
            if previous_level < working_items[index].level:
                return
            start, end = subtree_bounds(index)
            for cursor in range(start, end):
                working_items[cursor].level += 1
            update_after_change("Nested list item", start)

        def edit_item() -> None:
            index = require_selection()
            if index is None:
                return
            current = working_items[index]
            with wx.TextEntryDialog(
                dialog,
                "Edit list item text:",
                "Edit List Item",
                value=current.text,
            ) as entry:
                if self._show_modal_dialog(entry, "Edit List Item") != wx.ID_OK:
                    return
                current.text = entry.GetValue().strip()
            update_after_change("Updated list item", index)

        def add_item(as_child: bool) -> None:
            index = require_selection()
            if index is None:
                return
            current = working_items[index]
            with wx.TextEntryDialog(
                dialog,
                "Enter text for the new list item:",
                "Add List Item",
                value="",
            ) as entry:
                if self._show_modal_dialog(entry, "Add List Item") != wx.ID_OK:
                    return
                text_value = entry.GetValue().strip()
            level = current.level + 1 if as_child else current.level
            insert_at = subtree_bounds(index)[1] if as_child else subtree_bounds(index)[1]
            working_items.insert(
                insert_at,
                _ListManagerItem(
                    kind=current.kind,
                    text=text_value,
                    level=level,
                    bullet=current.bullet,
                    checked=False,
                ),
            )
            update_after_change("Added list item", insert_at)

        def delete_item() -> None:
            index = require_selection()
            if index is None:
                return
            start, end = subtree_bounds(index)
            del working_items[start:end]
            update_after_change("Deleted list item", start - 1 if start > 0 else 0)

        def on_select(event: object) -> None:
            nonlocal selected_index
            selected_index = item_indexes.get(event.GetItem())
            preview.ChangeValue(list_preview(selected_index))
            event.Skip()

        button_column = wx.BoxSizer(wx.VERTICAL)
        move_up_button = wx.Button(dialog, label="Move Up")
        move_down_button = wx.Button(dialog, label="Move Down")
        promote_button = wx.Button(dialog, label="Promote")
        demote_button = wx.Button(dialog, label="Demote")
        edit_button = wx.Button(dialog, label="Edit...")
        add_child_button = wx.Button(dialog, label="Add Child...")
        add_sibling_button = wx.Button(dialog, label="Add Sibling...")
        delete_button = wx.Button(dialog, label="Delete")
        apply_button = wx.Button(dialog, id=wx.ID_OK, label="Apply Changes")
        cancel_button = wx.Button(dialog, id=wx.ID_CANCEL, label="Close")

        for button in (
            move_up_button,
            move_down_button,
            promote_button,
            demote_button,
            edit_button,
            add_child_button,
            add_sibling_button,
            delete_button,
        ):
            button_column.Add(button, 0, wx.EXPAND | wx.BOTTOM, 6)
        button_column.AddStretchSpacer(1)
        button_column.Add(apply_button, 0, wx.EXPAND | wx.BOTTOM, 6)
        button_column.Add(cancel_button, 0, wx.EXPAND)

        controls = wx.BoxSizer(wx.VERTICAL)
        controls.Add(
            wx.StaticText(
                dialog,
                label=(
                    "Manage the current Markdown list as a tree. "
                    "Use Move/Promote/Demote to restructure without editing markers by hand."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        controls.Add(splitter, 1, wx.ALL | wx.EXPAND, 8)
        content = wx.BoxSizer(wx.HORIZONTAL)
        content.Add(controls, 1, wx.EXPAND)
        content.Add(button_column, 0, wx.ALL | wx.EXPAND, 8)
        dialog.SetSizer(content)

        tree.Bind(wx.EVT_TREE_SEL_CHANGED, on_select)
        move_up_button.Bind(wx.EVT_BUTTON, lambda _e: move_up())
        move_down_button.Bind(wx.EVT_BUTTON, lambda _e: move_down())
        promote_button.Bind(wx.EVT_BUTTON, lambda _e: promote())
        demote_button.Bind(wx.EVT_BUTTON, lambda _e: demote())
        edit_button.Bind(wx.EVT_BUTTON, lambda _e: edit_item())
        add_child_button.Bind(wx.EVT_BUTTON, lambda _e: add_item(as_child=True))
        add_sibling_button.Bind(wx.EVT_BUTTON, lambda _e: add_item(as_child=False))
        delete_button.Bind(wx.EVT_BUTTON, lambda _e: delete_item())
        apply_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))

        build_tree()
        if self._show_modal_dialog(dialog, "List Manager") != wx.ID_OK:
            return None

        block = self._render_list_manager_block(
            _ListManagerState(
                start=state.start,
                end=state.end,
                trailing_newline=state.trailing_newline,
                base_indent=state.base_indent,
                items=working_items,
            )
        )
        text = self.editor.GetValue()
        return text[: state.start] + block + text[state.end :]

    def format_insert_code_block(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Code Block is unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Code Block is only available in Markdown or HTML documents")
            return

        language_hint = self._prompt_code_language()
        if language_hint is None:
            self._set_status("Insert code block cancelled")
            return

        selected_text = self.editor.GetStringSelection()
        if surface == "markdown":
            result = build_markdown_code_block(selected_text, language_hint=language_hint)
        else:
            result = build_html_code_block(selected_text, language_hint=language_hint)
        self._apply_insertion_result(result)
        language_display = language_hint.strip() or "plain"
        self._set_status(f"Inserted code block ({surface}, {language_display})")

    def format_insert_footnote(self) -> None:
        self._insert_structure("Footnote", "Inserted footnote")

    def format_insert_table(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Table is unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status("Table is only available in Markdown or HTML documents")
            return

        table_shape = self._prompt_table_shape()
        if table_shape is None:
            self._set_status("Insert table cancelled")
            return
        rows, columns, include_header = table_shape
        if surface == "markdown":
            result = build_markdown_table(rows, columns, include_header=include_header)
        else:
            result = build_html_table(rows, columns, include_header=include_header)
        self._apply_insertion_result(result)
        self._set_status(f"Inserted {rows}x{columns} table ({surface})")

    def _insert_structure(self, kind: str, status: str) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status(f"{kind} is unavailable in this profile")
            return
        surface = self._active_markup_surface()
        if surface is None:
            self._set_status(
                f"{kind} is only available in Markdown or HTML documents",
            )
            return
        selected_text = self.editor.GetStringSelection()
        if surface == "markdown":
            result = build_markdown_insertion(kind, selected_text)
        else:
            result = self._build_html_structure(kind, selected_text)
        self._apply_insertion_result(result)
        self._set_status(f"{status} ({surface})")

    def _build_html_structure(self, kind: str, selected_text: str) -> InsertionResult:
        lines = [line.strip() for line in selected_text.splitlines() if line.strip()]
        if kind == "Bullet List":
            items = lines or ["item"]
            snippet = "<ul>\n" + "\n".join(f"  <li>{item}</li>" for item in items) + "\n</ul>"
            return InsertionResult(snippet, len(snippet))
        if kind == "Numbered List":
            items = lines or ["item"]
            snippet = "<ol>\n" + "\n".join(f"  <li>{item}</li>" for item in items) + "\n</ol>"
            return InsertionResult(snippet, len(snippet))
        if kind == "Task List":
            items = lines or ["task"]
            snippet = (
                "<ul>\n"
                + "\n".join(f'  <li><input type="checkbox" /> {item}</li>' for item in items)
                + "\n</ul>"
            )
            return InsertionResult(snippet, len(snippet))
        if kind == "Code Block":
            return build_html_code_block(selected_text)
        if kind == "Footnote":
            text = selected_text or "text"
            snippet = (
                f'{text}<sup id="fnref-1"><a href="#fn-1">1</a></sup>\n\n'
                f'<aside id="fn-1">Footnote text</aside>'
            )
            return InsertionResult(snippet, len(text) + 8)
        return InsertionResult(selected_text or "text", len(selected_text or "text"))

    def _prompt_table_shape(self) -> tuple[int, int, bool] | None:
        wx = self._wx

        def prompt_dimension(message: str, minimum: int, maximum: int) -> int | None:
            while True:
                with wx.TextEntryDialog(
                    self.frame,
                    message,
                    "Insert Table",
                    value="2",
                ) as dialog:
                    if self._show_modal_dialog(dialog, "Insert Table") != wx.ID_OK:
                        return None
                    raw_value = dialog.GetValue().strip()
                try:
                    value = int(raw_value)
                except ValueError:
                    self._show_message_box(
                        "Rows and columns must be whole numbers.",
                        "Insert Table",
                        wx.ICON_ERROR | wx.OK,
                    )
                    continue
                if value < minimum or value > maximum:
                    label = "Columns" if maximum == 12 else "Rows"
                    self._show_message_box(
                        f"{label} must be between {minimum} and {maximum}.",
                        "Insert Table",
                        wx.ICON_ERROR | wx.OK,
                    )
                    continue
                return value

        columns = prompt_dimension("Enter number of columns (1-12):", 1, 12)
        if columns is None:
            return None
        rows = prompt_dimension("Enter number of rows (1-50):", 1, 50)
        if rows is None:
            return None
        with wx.MessageDialog(
            self.frame,
            "Include a header row?",
            "Insert Table",
            wx.YES_NO | wx.ICON_QUESTION,
        ) as header_dialog:
            include_header = self._show_modal_dialog(header_dialog, "Insert Table") == wx.ID_YES
        return rows, columns, include_header

    def _prompt_code_language(self) -> str | None:
        wx = self._wx
        with wx.TextEntryDialog(
            self.frame,
            "Optional language hint (example: python, javascript, sql):",
            "Insert Code Block",
            value="",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Insert Code Block") != wx.ID_OK:
                return None
            return dialog.GetValue().strip()

    def _active_markup_surface(self) -> str | None:
        kind = infer_markup_kind(self.document.path)
        if kind in {"markdown", "html"}:
            return kind
        return None

    def _transform_selection_or_document(
        self,
        transform: Callable[[str], str],
        label: str,
    ) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status(f"{label} is unavailable in this profile")
            return
        text = self.editor.GetValue()
        start, end = self.editor.GetSelection()
        if start != end:
            original = text[start:end]
            updated = transform(original)
            self.editor.Replace(start, end, updated)
            self.editor.SetSelection(start, start + len(updated))
            self.document.set_text(self.editor.GetValue())
            self._set_status(f"{label} applied to selection")
            return

        word_span = self._current_word_span_at_caret(text, self.editor.GetInsertionPoint())
        if word_span is None:
            self._set_status("No current word to transform")
            return
        word_start, word_end = word_span
        updated = transform(text[word_start:word_end])
        self.editor.Replace(word_start, word_end, updated)
        self.editor.SetSelection(word_start, word_start + len(updated))
        self.document.set_text(self.editor.GetValue())
        self._set_status(f"{label} applied to current word")

    def _current_word_span_at_caret(self, text: str, caret: int) -> tuple[int, int] | None:
        if not text:
            return None
        caret = max(0, min(caret, len(text)))

        def is_word_char(character: str) -> bool:
            return character.isalnum() or character in {"_", "'"}

        if caret < len(text) and is_word_char(text[caret]):
            start = caret
            end = caret + 1
        elif caret > 0 and is_word_char(text[caret - 1]):
            start = caret - 1
            end = caret
        else:
            return None

        while start > 0 and is_word_char(text[start - 1]):
            start -= 1
        while end < len(text) and is_word_char(text[end]):
            end += 1
        if start == end:
            return None
        return start, end

    def _replace_document_text(self, updated_text: str) -> None:
        current_text = self.editor.GetValue()
        self.editor.Replace(0, len(current_text), updated_text)
        self.editor.SetSelection(0, len(updated_text))

    def _apply_selection_operation(
        self,
        operation: Callable[[str, int, int], tuple[str, int, int]],
        status: str,
    ) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status(f"{status} is unavailable in this profile")
            return
        text = self.editor.GetValue()
        start, end = self.editor.GetSelection()
        updated, new_start, new_end = operation(text, start, end)
        self._replace_document_text(updated)
        self.document.set_text(updated)
        if new_start == new_end:
            self.editor.SetInsertionPoint(new_start)
            self.editor.SetSelection(new_start, new_start)
        else:
            self.editor.SetSelection(new_start, new_end)
        self._set_status(status)

    def _apply_text_block_operation(
        self,
        transform: Callable[[str], str],
        status: str,
    ) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status(f"{status} is unavailable in this profile")
            return
        text = self.editor.GetValue()
        start, end = self.editor.GetSelection()
        if start == end:
            start, end = line_span(text, self.editor.GetInsertionPoint())
        else:
            start = line_span(text, start)[0]
            end = line_span(text, max(0, end - 1))[1]
        updated_block = transform(text[start:end])
        updated = text[:start] + updated_block + text[end:]
        self._replace_document_text(updated)
        self.document.set_text(updated)
        self.editor.SetSelection(start, start + len(updated_block))
        self._set_status(status)

    def _apply_line_operation(
        self,
        operation: Callable[[str, int], tuple[str, int]],
        status: str,
    ) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status(f"{status} is unavailable in this profile")
            return
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        updated, new_cursor = operation(text, cursor)
        self._replace_document_text(updated)
        self.document.set_text(updated)
        self.editor.SetInsertionPoint(new_cursor)
        self.editor.SetSelection(new_cursor, new_cursor)
        self._set_status(status)

    def _choose_searchable_option(
        self,
        *,
        title: str,
        prompt: str,
        dialog_label: str,
        initial_choices: list[str],
        search_callback: Callable[[str], list[str]],
        empty_search_examples: tuple[str, ...] = (),
    ) -> str | None:
        wx = self._wx
        with wx.Dialog(
            self.frame,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        ) as dialog:
            dialog.SetSize((560, 420))
            root = wx.BoxSizer(wx.VERTICAL)

            search = wx.SearchCtrl(dialog, style=wx.TE_PROCESS_ENTER)
            search.ShowSearchButton(True)
            search.SetDescriptiveText(prompt)
            root.Add(search, 0, wx.EXPAND | wx.ALL, 8)

            status = wx.StaticText(dialog, label="")
            root.Add(status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            results = wx.ListBox(dialog)
            root.Add(results, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
            if buttons is not None:
                root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            dialog.SetSizer(root)

            last_query = self._searchable_picker_queries.get(dialog_label, "")
            if last_query:
                search.SetValue(last_query)

            filtered = list(initial_choices)

            def _refresh() -> None:
                nonlocal filtered
                filtered = list(search_callback(search.GetValue()))
                results.Set(filtered)
                if filtered:
                    results.SetSelection(0)
                    status.SetLabel(f"{len(filtered)} match(es). Top match: {filtered[0]}")
                else:
                    if empty_search_examples:
                        examples = ", ".join(empty_search_examples)
                        status.SetLabel(f"No matching options. Try: {examples}")
                    else:
                        status.SetLabel("No matching options")

            def _announce_selected() -> None:
                selected = results.GetSelection()
                if selected == wx.NOT_FOUND:
                    return
                if selected < 0 or selected >= len(filtered):
                    return
                status.SetLabel(f"Selected: {filtered[selected]}")

            def _accept(_event: object) -> None:
                if results.GetCount() == 0:
                    return
                dialog.EndModal(wx.ID_OK)

            def _on_char_hook(event: object) -> None:
                key_code = event.GetKeyCode()
                if key_code == wx.WXK_ESCAPE:
                    dialog.EndModal(wx.ID_CANCEL)
                    return
                if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                    _accept(event)
                    return
                if key_code == wx.WXK_DOWN and results.GetCount() > 0:
                    results.SetSelection(0)
                    results.SetFocus()
                    _announce_selected()
                    return
                if key_code == wx.WXK_UP and results.GetCount() > 0:
                    results.SetSelection(results.GetCount() - 1)
                    results.SetFocus()
                    _announce_selected()
                    return
                event.Skip()

            search.Bind(wx.EVT_TEXT, lambda _event: _refresh())
            search.Bind(wx.EVT_TEXT_ENTER, _accept)
            results.Bind(wx.EVT_LISTBOX, lambda _event: _announce_selected())
            results.Bind(wx.EVT_LISTBOX_DCLICK, _accept)
            dialog.Bind(wx.EVT_CHAR_HOOK, _on_char_hook)
            _refresh()

            result = self._show_modal_dialog(dialog, dialog_label)
            self._searchable_picker_queries[dialog_label] = search.GetValue().strip()
            if result != wx.ID_OK:
                return None
            selected = results.GetSelection()
            if selected == wx.NOT_FOUND or selected < 0 or selected >= len(filtered):
                return None
            return filtered[selected]

    def insert_html_tag(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("HTML tag tools are unavailable in this profile")
            return
        tag = self._choose_searchable_option(
            title="Insert HTML Tag",
            prompt="Type to filter tags (for example: text, radio, button)",
            dialog_label="Insert HTML Tag",
            initial_choices=HTML_TAG_CHOICES,
            search_callback=search_html_tag_choices,
            empty_search_examples=("text", "radio", "button"),
        )
        if not tag:
            return

        wx = self._wx
        with wx.TextEntryDialog(
            self.frame,
            "Optional attributes (example: class=note; id=main; aria-label=Summary):",
            "Insert HTML Tag",
            value="",
        ) as attributes_dialog:
            if self._show_modal_dialog(attributes_dialog, "Insert HTML Tag") != wx.ID_OK:
                return
            attributes_raw = attributes_dialog.GetValue()

        selected_text = self.editor.GetStringSelection()
        attributes = parse_attribute_pairs(attributes_raw)
        result = build_html_insertion(tag, selected_text, attributes)
        self._apply_insertion_result(result)
        self._set_status(f"Inserted HTML tag <{tag}>")

    def insert_markdown_tag(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("Markdown tag tools are unavailable in this profile")
            return
        kind = self._choose_searchable_option(
            title="Insert Markdown Tag",
            prompt="Type to filter markdown tags/snippets",
            dialog_label="Insert Markdown Tag",
            initial_choices=MARKDOWN_TAG_CHOICES,
            search_callback=search_markdown_tag_choices,
            empty_search_examples=("heading", "link", "image"),
        )
        if not kind:
            return

        wx = self._wx
        link_target = ""
        if kind in {"Link", "Image"}:
            with wx.TextEntryDialog(
                self.frame,
                "Enter target URL:",
                f"Insert {kind}",
                value="https://",
            ) as url_dialog:
                if self._show_modal_dialog(url_dialog, f"Insert {kind}") != wx.ID_OK:
                    return
                link_target = url_dialog.GetValue().strip()

        selected_text = self.editor.GetStringSelection()
        result = build_markdown_insertion(kind, selected_text, link_target=link_target)
        self._apply_insertion_result(result)
        self._set_status(f"Inserted markdown {kind.lower()}")

    def _snippet_picker_label(self, snippet: Snippet) -> str:
        if snippet.description:
            return f"{snippet.name} ({snippet.trigger}) — {snippet.description}"
        return f"{snippet.name} ({snippet.trigger})"

    def _save_snippets(self) -> None:
        if self._safe_mode:
            return
        save_snippet_library(self._snippet_library)

    def _prompt_for_snippet(self, *, initial_query: str = "") -> Snippet | None:
        snippets = self._snippet_library.snippets
        if not snippets:
            return None
        by_label = {self._snippet_picker_label(snippet): snippet for snippet in snippets}
        initial_choices = [
            self._snippet_picker_label(snippet) for snippet in search_snippets(snippets, "")
        ]
        choice = self._choose_searchable_option(
            title="Insert Snippet",
            prompt="Type to filter snippets by name, trigger, or text",
            dialog_label="Insert Snippet",
            initial_choices=initial_choices,
            search_callback=lambda query: [
                self._snippet_picker_label(snippet) for snippet in search_snippets(snippets, query)
            ],
            empty_search_examples=("email", "bug", ";meeting"),
        )
        if not choice:
            return None
        return by_label.get(choice)

    def _render_snippet_with_prompts(self, snippet: Snippet) -> SnippetExpansionResult | None:
        wx = self._wx
        values: dict[str, str] = {}
        for placeholder in extract_placeholders(snippet.body):
            if placeholder.kind in {"cursor", "date", "time"}:
                continue
            if placeholder.kind == "choice":
                with wx.SingleChoiceDialog(
                    self.frame,
                    f"Choose a value for {placeholder.name}:",
                    f"Snippet: {snippet.name}",
                    choices=placeholder.options,
                ) as dialog:
                    if self._show_modal_dialog(dialog, f"Snippet: {snippet.name}") != wx.ID_OK:
                        return None
                    selected = dialog.GetSelection()
                if selected == wx.NOT_FOUND:
                    return None
                values[placeholder.token] = placeholder.options[selected]
                continue
            with wx.TextEntryDialog(
                self.frame,
                f"Value for {placeholder.name}:",
                f"Snippet: {snippet.name}",
                value="",
            ) as dialog:
                if self._show_modal_dialog(dialog, f"Snippet: {snippet.name}") != wx.ID_OK:
                    return None
                values[placeholder.token] = dialog.GetValue()
        return render_snippet(snippet.body, values)

    def insert_snippet(self) -> None:
        snippet = self._prompt_for_snippet()
        if snippet is None:
            self._set_status("No snippets available. Open Manage Snippets to add one.")
            return
        rendered = self._render_snippet_with_prompts(snippet)
        if rendered is None:
            self._set_status("Snippet insertion cancelled")
            return
        self._apply_insertion_result(
            InsertionResult(inserted_text=rendered.text, caret_offset=rendered.cursor)
        )
        self._set_status(f'Inserted snippet "{snippet.name}".')

    def show_word_prediction(self) -> None:
        if not self._feature_enabled("core.intellisense"):
            self._set_status("Word prediction is unavailable in this profile")
            return
        if not self._show_intellisense_popup(manual=True):
            self._set_status("No predictions available")

    def _show_intellisense_popup(self, *, manual: bool) -> bool:
        popup = getattr(self, "_intellisense_popup", None)
        if popup is None:
            return False
        if not manual and not getattr(self.settings, "intellisense_as_you_type", False):
            if popup.is_visible():
                self._hide_intellisense_popup()
            return False
        text = self.editor.GetValue()
        cursor = self.editor.GetInsertionPoint()
        dictionary = self._spell_dictionary() | collect_document_words(text)
        context, suggestions = build_intellisense_suggestions(
            text,
            cursor,
            dictionary,
            limit=8,
        )
        if not suggestions:
            if popup.is_visible():
                self._hide_intellisense_popup()
            self._intellisense_context = context
            self._intellisense_fragment_text = context.fragment if context is not None else ""
            self._intellisense_suggestions = []
            return False
        if not manual and context is not None and len(context.fragment.strip()) < 2:
            if self._intellisense_popup.is_visible():
                self._hide_intellisense_popup()
            return False
        self._intellisense_context = context
        self._intellisense_fragment_text = context.fragment if context is not None else ""
        self._intellisense_suggestions = suggestions
        status = f"{len(suggestions)} prediction(s). {suggestions[0].label}"
        was_visible = popup.is_visible()
        popup.update(suggestions, status)
        if not was_visible:
            editor_pos = self.editor.GetScreenPosition()
            popup.show((editor_pos.x + 20, editor_pos.y + 40))
            announce(status)
        return True

    def _refresh_intellisense_popup(self) -> None:
        if self._intellisense_guard:
            return
        popup = getattr(self, "_intellisense_popup", None)
        popup_visible = popup is not None and popup.is_visible()
        if not popup_visible and not getattr(self.settings, "intellisense_as_you_type", False):
            return
        self._show_intellisense_popup(manual=popup_visible)

    def _hide_intellisense_popup(self) -> None:
        popup = getattr(self, "_intellisense_popup", None)
        if popup is not None:
            popup.hide()
        self._intellisense_context = None
        self._intellisense_fragment_text = ""
        self._intellisense_suggestions = []

    def _apply_intellisense_selection(self) -> bool:
        popup = getattr(self, "_intellisense_popup", None)
        context = getattr(self, "_intellisense_context", None)
        if popup is None or context is None:
            return False
        suggestion = popup.selected_suggestion()
        if suggestion is None:
            return False
        self._intellisense_guard = True
        try:
            self.editor.Replace(
                context.replacement_start,
                context.replacement_end,
                suggestion.inserted_text,
            )
            caret = context.replacement_start + suggestion.caret_offset
            caret = max(0, min(caret, len(self.editor.GetValue())))
            self.editor.SetInsertionPoint(caret)
            self.editor.SetSelection(caret, caret)
        finally:
            self._intellisense_guard = False
        self._hide_intellisense_popup()
        self._set_status(f'Inserted prediction "{suggestion.label}".')
        return True

    def _handle_intellisense_key_down(self, event: object) -> bool:
        wx = self._wx
        space_key = getattr(wx, "WXK_SPACE", ord(" "))
        if event.ControlDown() and not event.AltDown() and not event.ShiftDown():
            if event.GetKeyCode() == space_key:
                if not self._feature_enabled("core.intellisense"):
                    self._set_status("Word prediction is unavailable in this profile")
                    return True
                self._show_intellisense_popup(manual=True)
                return True
        popup = getattr(self, "_intellisense_popup", None)
        if popup is None or not popup.is_visible():
            return False
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self._hide_intellisense_popup()
            return True
        if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_TAB):
            if self._apply_intellisense_selection():
                return True
            return False
        if key_code == wx.WXK_UP:
            popup.set_selection(popup.selection_index() - 1)
            selection = popup.selected_suggestion()
            if selection is not None:
                announce(selection.label)
            return True
        if key_code == wx.WXK_DOWN:
            popup.set_selection(popup.selection_index() + 1)
            selection = popup.selected_suggestion()
            if selection is not None:
                announce(selection.label)
            return True
        return False

    def _prompt_snippet_editor(self, existing: Snippet | None = None) -> Snippet | None:
        wx = self._wx
        name = existing.name if existing is not None else ""
        trigger = existing.trigger if existing is not None else ";"
        description = existing.description if existing is not None else ""
        body = existing.body if existing is not None else "${cursor}"
        with wx.TextEntryDialog(
            self.frame,
            "Snippet name:",
            "Edit Snippet" if existing is not None else "New Snippet",
            value=name,
        ) as name_dialog:
            if self._show_modal_dialog(name_dialog, "Snippet Name") != wx.ID_OK:
                return None
            name = name_dialog.GetValue().strip()
        if not name:
            self._set_status("Snippet name is required")
            return None
        with wx.TextEntryDialog(
            self.frame,
            "Trigger text (example: ;meeting):",
            "Snippet Trigger",
            value=trigger,
        ) as trigger_dialog:
            if self._show_modal_dialog(trigger_dialog, "Snippet Trigger") != wx.ID_OK:
                return None
            trigger = trigger_dialog.GetValue().strip()
        if not trigger:
            self._set_status("Snippet trigger is required")
            return None
        with wx.TextEntryDialog(
            self.frame,
            "Optional description:",
            "Snippet Description",
            value=description,
        ) as description_dialog:
            if self._show_modal_dialog(description_dialog, "Snippet Description") != wx.ID_OK:
                return None
            description = description_dialog.GetValue().strip()
        with wx.TextEntryDialog(
            self.frame,
            "Snippet body (supports ${input:name}, ${choice:a|b}, ${date}, ${time}, ${cursor}):",
            "Snippet Body",
            value=body,
            style=wx.OK | wx.CANCEL | wx.TE_MULTILINE,
        ) as body_dialog:
            if self._show_modal_dialog(body_dialog, "Snippet Body") != wx.ID_OK:
                return None
            body = body_dialog.GetValue()
        if not body:
            self._set_status("Snippet body is required")
            return None
        if existing is not None:
            snippet_id = existing.id
        else:
            snippet_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if not snippet_id:
            snippet_id = f"snippet-{int(time.time())}"
        return Snippet(
            id=snippet_id,
            name=name,
            trigger=trigger,
            body=body,
            description=description,
            tags=list(existing.tags or []) if existing is not None else [],
            enabled=True if existing is None else existing.enabled,
            source=existing.source if existing is not None else "user",
        )

    def install_starter_snippet_packs(self) -> None:
        wx = self._wx
        packs = starter_pack_names()
        with wx.MultiChoiceDialog(
            self.frame,
            "Choose starter snippet packs to install:",
            "Install Starter Snippet Packs",
            choices=packs,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Install Starter Snippet Packs") != wx.ID_OK:
                self._set_status("Starter snippet pack installation cancelled")
                return
            selections = dialog.GetSelections()
        if not selections:
            self._set_status("No starter snippet packs selected")
            return
        before = len(self._snippet_library.snippets)
        library = self._snippet_library
        for index in selections:
            if 0 <= index < len(packs):
                library = merge_starter_pack(library, packs[index])
        self._snippet_library = library
        self._save_snippets()
        added = max(0, len(library.snippets) - before)
        self._set_status(f"Installed {added} snippet(s) from starter packs.")

    def manage_snippets(self) -> None:
        wx = self._wx
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a snippet action:",
            "Manage Snippets",
            choices=[
                "Create snippet",
                "Edit snippet",
                "Delete snippet",
                "Import snippet library",
                "Export snippet library",
                "Install starter snippet packs",
            ],
        ) as action_dialog:
            action_dialog.SetSelection(0)
            if self._show_modal_dialog(action_dialog, "Manage Snippets") != wx.ID_OK:
                self._set_status("Manage snippets cancelled")
                return
            action = action_dialog.GetSelection()
        if action == 5:
            self.install_starter_snippet_packs()
            return
        if action == 3:
            with wx.FileDialog(
                self.frame,
                "Import snippet library",
                wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as dialog:
                if self._show_modal_dialog(dialog, "Import snippet library") != wx.ID_OK:
                    self._set_status("Snippet import cancelled")
                    return
                source = Path(dialog.GetPath())
            incoming = load_snippet_library(source)
            if not incoming.snippets:
                self._set_status("No snippets found in selected file")
                return
            by_id = {snippet.id: snippet for snippet in self._snippet_library.snippets}
            for snippet in incoming.snippets:
                by_id[snippet.id] = snippet
            self._snippet_library = SnippetLibrary(
                version=self._snippet_library.version,
                snippets=sorted(by_id.values(), key=lambda item: item.name.lower()),
            )
            self._save_snippets()
            self._set_status(f"Imported {len(incoming.snippets)} snippet(s).")
            return
        if action == 4:
            with wx.FileDialog(
                self.frame,
                "Export snippet library",
                wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as dialog:
                if self._show_modal_dialog(dialog, "Export snippet library") != wx.ID_OK:
                    self._set_status("Snippet export cancelled")
                    return
                destination = Path(dialog.GetPath())
            save_snippet_library(self._snippet_library, destination)
            self._set_status(f"Exported snippets to {destination.name}.")
            return
        if action == 0:
            created = self._prompt_snippet_editor()
            if created is None:
                self._set_status("Snippet creation cancelled")
                return
            if any(item.id == created.id for item in self._snippet_library.snippets):
                self._set_status("A snippet with that name already exists")
                return
            self._snippet_library.snippets.append(created)
            self._snippet_library.snippets.sort(key=lambda item: item.name.lower())
            self._save_snippets()
            self._set_status(f'Snippet "{created.name}" created.')
            return
        snippets = sorted(self._snippet_library.snippets, key=lambda item: item.name.lower())
        if not snippets:
            self._set_status("No snippets available")
            return
        labels = [self._snippet_picker_label(snippet) for snippet in snippets]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a snippet:",
            "Manage Snippets",
            choices=labels,
        ) as choose_dialog:
            if self._show_modal_dialog(choose_dialog, "Manage Snippets") != wx.ID_OK:
                self._set_status("Manage snippets cancelled")
                return
            selected = choose_dialog.GetSelection()
        if selected == wx.NOT_FOUND or selected < 0 or selected >= len(snippets):
            self._set_status("Manage snippets cancelled")
            return
        snippet = snippets[selected]
        if action == 2:
            confirm = self._show_message_box(
                f'Delete snippet "{snippet.name}"?',
                "Delete Snippet",
                wx.YES_NO | wx.ICON_WARNING,
            )
            if confirm != wx.YES:
                self._set_status("Snippet delete cancelled")
                return
            self._snippet_library.snippets = [
                item for item in self._snippet_library.snippets if item.id != snippet.id
            ]
            self._save_snippets()
            self._set_status(f'Snippet "{snippet.name}" deleted.')
            return
        if action != 1:
            self._set_status("Manage snippets cancelled")
            return
        edited = self._prompt_snippet_editor(snippet)
        if edited is None:
            self._set_status("Snippet edit cancelled")
            return
        updated: list[Snippet] = []
        for item in self._snippet_library.snippets:
            if item.id == snippet.id:
                updated.append(edited)
            else:
                updated.append(item)
        self._snippet_library.snippets = updated
        self._save_snippets()
        self._set_status(f'Snippet "{edited.name}" saved.')

    def _apply_insertion_result(self, result: InsertionResult) -> None:
        start, end = self.editor.GetSelection()
        self.editor.Replace(start, end, result.inserted_text)
        caret = start + result.caret_offset
        self.editor.SetInsertionPoint(caret)
        self.editor.SetFocus()

    def show_document_intake_report(self) -> None:
        report = build_intake_report(self.document)
        self._show_message_box(
            report, "Document Intake Report", self._wx.ICON_INFORMATION | self._wx.OK
        )

    def review_extraction_quality(self) -> None:
        report = build_extraction_quality_report(self.document)
        self._show_message_box(
            report, "Extraction Quality Review", self._wx.ICON_INFORMATION | self._wx.OK
        )

    def report_bad_extraction(self) -> None:
        wx = self._wx
        payload = build_bad_extraction_package(self.document, self.settings, __version__)
        with wx.FileDialog(
            self.frame,
            "Save extraction report",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Save extraction report") != wx.ID_OK:
                self._set_status("Bad extraction report cancelled")
                return
            target = Path(dialog.GetPath())
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._set_status(f"Saved extraction report to {target.name}")

    def show_context_help(self) -> None:
        report = build_context_help(
            self.document, bool(self.editor.GetSelection()[0] != self.editor.GetSelection()[1])
        )
        self._show_message_box(
            report, "What Can I Do Here?", self._wx.ICON_INFORMATION | self._wx.OK
        )

    def show_feature_explanation(self) -> None:
        wx = self._wx
        with wx.TextEntryDialog(
            self.frame,
            "Enter a feature name, command, or topic:",
            "Why Don't I See a Feature?",
            value="regex",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Why Don't I See a Feature?") != wx.ID_OK:
                return
            query = dialog.GetValue().strip()
        if not query:
            self._set_status("Feature lookup cancelled")
            return
        report = self.features.describe_feature(query)
        self._show_message_box(report, "Why Don't I See a Feature?", wx.ICON_INFORMATION | wx.OK)

    def _load_custom_profiles(self) -> dict[str, CustomProfile]:
        return load_custom_profiles()

    def _save_custom_profiles(self, profiles: dict[str, CustomProfile]) -> None:
        save_custom_profiles(profiles)

    def _combined_profile_entries(self) -> list[tuple[str, str, str]]:
        entries: list[tuple[str, str, str]] = [
            ("built_in", profile.id, profile.name) for profile in PROFILE_DEFINITIONS.values()
        ]
        for profile in self._load_custom_profiles().values():
            entries.append(("custom", profile.id, profile.name))
        return entries

    def _custom_profile_summary(self, profile: CustomProfile) -> str:
        raw_profile_data = profile.feature_profile_data
        active_profile_id = str(raw_profile_data.get("active_profile_id", PROFILE_ESSENTIAL))
        if active_profile_id not in PROFILE_DEFINITIONS:
            active_profile_id = PROFILE_ESSENTIAL
        overrides_raw = raw_profile_data.get("overrides")
        overrides = overrides_raw if isinstance(overrides_raw, dict) else {}
        base_states = PROFILE_DEFINITIONS[active_profile_id].states
        enabled = 0
        for feature_id, definition in FEATURE_DEFINITIONS.items():
            if definition.locked_on:
                enabled += 1
                continue
            override = overrides.get(feature_id)
            state = override if isinstance(override, str) else base_states.get(feature_id, "on")
            if state != "off":
                enabled += 1
        parent_name = PROFILE_DEFINITIONS.get(
            profile.parent_profile_id, PROFILE_DEFINITIONS[PROFILE_ESSENTIAL]
        ).name
        inheritance = (
            f"Inherits from {parent_name}."
            if profile.inherits_parent
            else "Starts from a bare-bones baseline."
        )
        return (
            f"Custom profile: {profile.name}\n\n"
            f"{profile.description or 'No description provided.'}\n\n"
            f"{inheritance}\nEnabled features: {enabled}\n"
            f"Keyboard bindings captured: {len(profile.keymap_data)}"
        )

    def _apply_custom_profile(self, profile: CustomProfile) -> None:
        self.features.import_profile_data(profile.feature_profile_data)
        merged_settings = asdict(self.settings)
        merged_settings.update(profile.settings_data)
        self.settings = Settings.from_dict(merged_settings)
        save_settings(self.settings)
        self.keymap = DEFAULT_KEYMAP.copy()
        self.keymap.update(profile.keymap_data)
        save_keymap(self.keymap)
        self._reload_shortcuts_from_keymap()
        self._apply_soft_wrap(self.settings.soft_wrap)
        self._rebuild_tab_host(self.settings.show_tab_control)
        self._apply_statusbar_layout()
        self._refresh_title()

    def switch_feature_profile(self) -> None:
        wx = self._wx
        entries = self._combined_profile_entries()
        if not entries:
            self._set_status("No profiles available")
            return
        choices = [
            name if kind == "built_in" else f"{name} (Custom)"
            for kind, _profile_id, name in entries
        ]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a feature profile:",
            "Switch Feature Profile",
            choices=choices,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Switch Feature Profile") != wx.ID_OK:
                return
            selection = dialog.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        kind, target_profile_id, target_name = entries[selection]
        if kind == "built_in" and target_profile_id == self.features.active_profile_id:
            self._set_status(f"Already using {self.features.active_profile.name}")
            return
        preview = self.features.change_profile_preview(target_profile_id)
        if kind == "custom":
            custom_profile = self._load_custom_profiles().get(target_profile_id)
            if custom_profile is None:
                self._set_status("Custom profile is no longer available")
                return
            preview = self._custom_profile_summary(custom_profile)
        with wx.MessageDialog(
            self.frame,
            preview + "\n\nSwitch profiles now?",
            "Switch Feature Profile",
            wx.YES_NO | wx.ICON_QUESTION,
        ) as confirm_dialog:
            if self._show_modal_dialog(confirm_dialog, "Switch Feature Profile") != wx.ID_YES:
                self._set_status("Profile switch cancelled")
                return
        if kind == "custom":
            custom_profile = self._load_custom_profiles().get(target_profile_id)
            if custom_profile is None:
                self._set_status("Custom profile is no longer available")
                return
            self._apply_custom_profile(custom_profile)
            self._set_status(f"Profile changed to {target_name}.")
            self._show_message_box(
                self._custom_profile_summary(custom_profile),
                "Feature Profile",
                wx.ICON_INFORMATION | wx.OK,
            )
        else:
            self.features.switch_profile(target_profile_id)
            profile = self.features.active_profile
            self._set_status(f"Profile changed to {profile.name}. Undo available.")
            self._show_message_box(
                self.features.profile_summary(),
                "Feature Profile",
                wx.ICON_INFORMATION | wx.OK,
            )
        self._apply_accelerators()

    def show_feature_profile_health_check(self) -> None:
        report = self.features.health_report(self.commands.list())
        self._show_message_box(
            report,
            "Feature Profile Health Check",
            self._wx.ICON_INFORMATION | self._wx.OK,
        )

    def _record_macro_step(self, command_id: str) -> None:
        macros = getattr(self, "macros", None)
        if macros is None:
            return
        if command_id in self._MACRO_CONTROL_COMMANDS:
            return
        macros.record(command_id)

    def start_macro_recording(self) -> None:
        wx = self._wx
        if self.macros.recording_name is not None:
            self._set_status(f"Already recording macro {self.macros.recording_name}")
            return
        with wx.TextEntryDialog(
            self.frame,
            "Enter a name for the new macro:",
            "Start Macro Recording",
            value="My Macro",
        ) as dialog:
            if self._show_modal_dialog(dialog, "Start Macro Recording") != wx.ID_OK:
                self._set_status("Macro recording cancelled")
                return
            name = dialog.GetValue().strip()
        if not name:
            self._set_status("Macro name cannot be empty")
            return
        try:
            self.macros.start_recording(name)
        except ValueError as error:
            self._set_status(str(error))
            return
        self._set_status(f"Recording macro {name}")

    def stop_macro_recording(self) -> None:
        macro = self.macros.stop_recording()
        if macro is None:
            self._set_status("No macro is being recorded")
            return
        self._set_status(f"Saved macro {macro.name} with {len(macro.steps)} step(s)")

    def play_last_macro(self) -> None:
        if self.macros.last_macro_name is None:
            self._set_status("No recorded macro to play")
            return
        try:
            self.macros.play_last_macro(self.commands.run)
        except KeyError:
            self._set_status("No recorded macro to play")
            return
        self._set_status(f"Played macro {self.macros.last_macro_name}")

    def manage_macros(self) -> None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Manage Macros", size=(720, 420))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(panel, label="Recorded macros are reusable command sequences."),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        names = list(self.macros.macros)
        chooser = wx.ListBox(panel, choices=names)
        details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        if names:
            chooser.SetSelection(0)

        def refresh_details() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                details.SetValue("No macros recorded yet.")
                return
            name = names[selection]
            macro = self.macros.macros[name]
            details.SetValue(
                f"Macro: {macro.name}\nSteps: {len(macro.steps)}\n\n"
                + "\n".join(f"{index + 1}. {step}" for index, step in enumerate(macro.steps))
            )

        def play_selected() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            name = names[selection]
            try:
                self.macros.play_macro(name, self.commands.run)
            except KeyError:
                self._set_status(f"Macro {name} is no longer available")
                return
            self._set_status(f"Played macro {name}")

        def rename_selected() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            old_name = names[selection]
            with wx.TextEntryDialog(
                dialog,
                "Enter a new macro name:",
                "Rename Macro",
                value=old_name,
            ) as rename_dialog:
                if self._show_modal_dialog(rename_dialog, "Rename Macro") != wx.ID_OK:
                    return
                new_name = rename_dialog.GetValue().strip()
            if not new_name:
                self._set_status("Macro name cannot be empty")
                return
            try:
                self.macros.rename_macro(old_name, new_name)
            except (KeyError, ValueError) as error:
                self._set_status(str(error))
                return
            names[selection] = new_name
            chooser.SetItems(names)
            chooser.SetSelection(selection)
            refresh_details()
            self._set_status(f"Renamed macro to {new_name}")

        def delete_selected() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            name = names[selection]
            if (
                self._show_message_box(
                    f"Delete macro {name}?",
                    "Delete Macro",
                    wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
                )
                != wx.YES
            ):
                return
            try:
                self.macros.delete_macro(name)
            except KeyError:
                self._set_status(f"Macro {name} is no longer available")
                return
            del names[selection]
            chooser.SetItems(names)
            chooser.SetSelection(0 if names else wx.NOT_FOUND)
            refresh_details()
            self._set_status(f"Deleted macro {name}")

        chooser.Bind(wx.EVT_LISTBOX, lambda _e: refresh_details())
        play_button = wx.Button(panel, label="Play")
        rename_button = wx.Button(panel, label="Rename")
        delete_button = wx.Button(panel, label="Delete")
        close_button = wx.Button(panel, id=wx.ID_OK, label="Close")
        play_button.Bind(wx.EVT_BUTTON, lambda _e: play_selected())
        rename_button.Bind(wx.EVT_BUTTON, lambda _e: rename_selected())
        delete_button.Bind(wx.EVT_BUTTON, lambda _e: delete_selected())
        close_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))

        root.Add(chooser, 1, wx.ALL | wx.EXPAND, 8)
        root.Add(details, 1, wx.ALL | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(play_button, 0, wx.RIGHT, 6)
        buttons.Add(rename_button, 0, wx.RIGHT, 6)
        buttons.Add(delete_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(close_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        refresh_details()
        self._show_modal_dialog(dialog, "Manage Macros")

    def open_profiles_and_features_settings(self) -> None:
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Profiles and Features", size=(820, 700))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Choose a feature profile, inspect what it changes, and import or export "
                    "profile data."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        chooser = wx.ListBox(panel, choices=[])
        entries: list[tuple[str, str, str]] = []
        summary = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        keyboard_pack_choices = keyboard_pack_names(include_custom=True)
        keyboard_pack_choice = wx.Choice(panel, choices=keyboard_pack_choices)
        current_pack = self.settings.keyboard_pack
        if current_pack not in keyboard_pack_choices:
            current_pack = KEYBOARD_PACK_DEFAULT
        keyboard_pack_choice.SetStringSelection(current_pack)
        indent_style_choice = wx.Choice(panel, choices=["Spaces", "Tabs"])
        indent_style_choice.SetStringSelection(
            "Tabs" if bool(getattr(self.settings, "indent_with_tabs", False)) else "Spaces"
        )
        indent_size_spin = wx.SpinCtrl(panel, min=1, max=8, initial=self._indent_width())
        keyboard_preview = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 160),
        )

        def refresh_profile_list(preferred_id: str | None = None) -> None:
            nonlocal entries
            entries = self._combined_profile_entries()
            labels = [
                name if kind == "built_in" else f"{name} (Custom)"
                for kind, _profile_id, name in entries
            ]
            chooser.Set(labels)
            selected_id = preferred_id or self.features.active_profile_id
            selected_index = 0
            for index, (_kind, profile_id, _name) in enumerate(entries):
                if profile_id == selected_id:
                    selected_index = index
                    break
            if entries:
                chooser.SetSelection(selected_index)

        def selected_entry() -> tuple[str, str, str] | None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND or selection < 0 or selection >= len(entries):
                return None
            return entries[selection]

        def refresh_summary() -> None:
            entry = selected_entry()
            if entry is None:
                summary.SetValue(self.features.profile_summary())
                return
            kind, profile_id, _name = entry
            if kind == "built_in":
                summary.SetValue(self.features.change_profile_preview(profile_id))
                return
            custom_profile = self._load_custom_profiles().get(profile_id)
            if custom_profile is None:
                summary.SetValue("Custom profile is no longer available.")
                return
            summary.SetValue(self._custom_profile_summary(custom_profile))

        def refresh_keyboard_preview() -> None:
            pack_name = keyboard_pack_choice.GetStringSelection() or KEYBOARD_PACK_DEFAULT
            description = keyboard_pack_description(pack_name)
            preview = keyboard_pack_preview(pack_name)
            if preview == description:
                keyboard_preview.SetValue(description)
                return
            keyboard_preview.SetValue(preview)

        def switch_selected() -> None:
            entry = selected_entry()
            if entry is None:
                return
            kind, profile_id, name = entry
            if kind == "built_in":
                if profile_id == self.features.active_profile_id:
                    self._set_status(f"Already using {name}")
                    return
                self.features.switch_profile(profile_id)
                self._set_status(f"Profile changed to {name}. Undo available.")
            else:
                custom_profile = self._load_custom_profiles().get(profile_id)
                if custom_profile is None:
                    self._set_status("Custom profile is no longer available")
                    refresh_profile_list()
                    refresh_summary()
                    return
                self._apply_custom_profile(custom_profile)
                self._set_status(f"Profile changed to {custom_profile.name}.")
            refresh_summary()
            self._refresh_title()

        def compare_selected() -> None:
            entry = selected_entry()
            if entry is None:
                return
            kind, profile_id, _name = entry
            if kind != "built_in":
                self._show_message_box(
                    "Profile comparison is available for built-in profiles.",
                    "Compare Profiles",
                    wx.ICON_INFORMATION | wx.OK,
                )
                return
            message = self.features.compare_profiles(self.features.active_profile_id, profile_id)
            self._show_message_box(message, "Compare Profiles", wx.ICON_INFORMATION | wx.OK)

        def undo_change() -> None:
            if self.features.undo_last_profile_change():
                self._set_status(f"Restored {self.features.active_profile.name}")
                refresh_summary()
                self._refresh_title()
                return
            self._set_status("No profile change to undo")

        def reset_essential() -> None:
            self.features.reset_to_essential_profile()
            refresh_profile_list(PROFILE_ESSENTIAL)
            refresh_summary()
            self._set_status("Reset to Essential profile")
            self._refresh_title()

        def create_custom_profile() -> None:
            with wx.TextEntryDialog(
                dialog,
                "Enter a name for the custom profile:",
                "Create Custom Profile",
                value="My Custom Profile",
            ) as name_dialog:
                if self._show_modal_dialog(name_dialog, "Create Custom Profile") != wx.ID_OK:
                    return
                name = name_dialog.GetValue().strip()
            if not name:
                self._set_status("Custom profile name cannot be empty")
                return
            with wx.TextEntryDialog(
                dialog,
                "Optional description:",
                "Create Custom Profile",
                value="",
            ) as description_dialog:
                if self._show_modal_dialog(description_dialog, "Create Custom Profile") != wx.ID_OK:
                    return
                description = description_dialog.GetValue().strip()
            built_in_profiles = list(PROFILE_DEFINITIONS.values())
            parent_labels = [self._profile_choice_label(profile) for profile in built_in_profiles]
            with wx.SingleChoiceDialog(
                dialog,
                "Choose the parent (global) profile:",
                "Create Custom Profile",
                choices=parent_labels,
            ) as parent_dialog:
                if self._show_modal_dialog(parent_dialog, "Create Custom Profile") != wx.ID_OK:
                    return
                parent_selection = parent_dialog.GetSelection()
            if parent_selection == wx.NOT_FOUND:
                return
            parent_profile = built_in_profiles[parent_selection]
            with wx.MessageDialog(
                dialog,
                (
                    "Inherit the selected parent profile's feature set?\n\n"
                    "Yes keeps inherited defaults. No starts from bare bones "
                    "(only locked core features remain enabled)."
                ),
                "Custom Profile Inheritance",
                wx.YES_NO | wx.ICON_QUESTION,
            ) as inherit_dialog:
                inherits_parent = (
                    self._show_modal_dialog(inherit_dialog, "Custom Profile Inheritance")
                    == wx.ID_YES
                )
            if not inherits_parent:
                self._show_message_box(
                    "Bare-bones mode selected. Most features are disabled until you turn them on.",
                    "Bare-Bones Profile",
                    wx.ICON_WARNING | wx.OK,
                )
            custom_profiles = self._load_custom_profiles()
            profile_id = generate_custom_profile_id(name, set(custom_profiles))
            if inherits_parent:
                feature_profile_data = build_parent_profile_data(parent_profile.id)
                settings_data = asdict(self.settings)
                keymap_data = dict(self.keymap)
            else:
                feature_profile_data = build_bare_bones_profile_data()
                settings_data = asdict(Settings())
                keymap_data = DEFAULT_KEYMAP.copy()
            custom_profiles[profile_id] = CustomProfile(
                id=profile_id,
                name=name,
                description=description,
                parent_profile_id=parent_profile.id,
                inherits_parent=inherits_parent,
                feature_profile_data=feature_profile_data,
                settings_data=settings_data,
                keymap_data=keymap_data,
            )
            self._save_custom_profiles(custom_profiles)
            refresh_profile_list(profile_id)
            refresh_summary()
            self._set_status(f"Created custom profile {name}")

        def update_selected_custom_profile() -> None:
            entry = selected_entry()
            if entry is None:
                return
            kind, profile_id, _name = entry
            if kind != "custom":
                self._set_status("Select a custom profile to update")
                return
            custom_profiles = self._load_custom_profiles()
            custom_profile = custom_profiles.get(profile_id)
            if custom_profile is None:
                self._set_status("Custom profile is no longer available")
                refresh_profile_list()
                refresh_summary()
                return
            custom_profile.feature_profile_data = self.features.export_profile_data()
            custom_profile.settings_data = asdict(self.settings)
            custom_profile.keymap_data = dict(self.keymap)
            custom_profiles[profile_id] = custom_profile
            self._save_custom_profiles(custom_profiles)
            refresh_summary()
            self._set_status(f"Updated custom profile {custom_profile.name} from current state")

        def delete_selected_custom_profile() -> None:
            entry = selected_entry()
            if entry is None:
                return
            kind, profile_id, name = entry
            if kind != "custom":
                self._set_status("Select a custom profile to delete")
                return
            confirm = self._show_message_box(
                f"Delete custom profile {name}?",
                "Delete Custom Profile",
                wx.YES_NO | wx.ICON_WARNING,
            )
            if confirm != wx.YES:
                return
            custom_profiles = self._load_custom_profiles()
            custom_profiles.pop(profile_id, None)
            self._save_custom_profiles(custom_profiles)
            refresh_profile_list()
            refresh_summary()
            self._set_status(f"Deleted custom profile {name}")

        def apply_selected_keyboard_pack() -> None:
            pack_name = keyboard_pack_choice.GetStringSelection() or KEYBOARD_PACK_DEFAULT
            if pack_name == KEYBOARD_PACK_CUSTOM:
                self._set_status("Custom layouts are managed by the keymap editor")
                return
            self.apply_keyboard_pack(pack_name)
            refresh_keyboard_preview()

        def reset_keyboard_pack() -> None:
            keyboard_pack_choice.SetStringSelection(KEYBOARD_PACK_DEFAULT)
            self.apply_keyboard_pack(KEYBOARD_PACK_DEFAULT)
            refresh_keyboard_preview()

        def customize_keymap() -> None:
            self.open_keymap_editor()
            current = self.settings.keyboard_pack
            if current not in keyboard_pack_choices:
                current = KEYBOARD_PACK_CUSTOM
            keyboard_pack_choice.SetStringSelection(current)
            refresh_keyboard_preview()

        def apply_indentation_settings() -> None:
            use_tabs = (indent_style_choice.GetStringSelection() or "Spaces") == "Tabs"
            indent_size = max(1, int(indent_size_spin.GetValue()))
            self.settings.indent_with_tabs = use_tabs
            self.settings.indent_size = indent_size
            save_settings(self.settings)
            mode = "tabs" if use_tabs else "spaces"
            self._set_status(f"Indentation set to {mode} ({indent_size})")

        def export_profile() -> None:
            with wx.FileDialog(
                dialog,
                message="Export profile data",
                wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as file_dialog:
                if self._show_modal_dialog(file_dialog, "Export Profile") != wx.ID_OK:
                    return
                target = Path(file_dialog.GetPath())
            target.write_text(
                json.dumps(self.features.export_profile_data(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._set_status(f"Exported profile data to {target.name}")

        def import_profile() -> None:
            with wx.FileDialog(
                dialog,
                message="Import profile data",
                wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as file_dialog:
                if self._show_modal_dialog(file_dialog, "Import Profile") != wx.ID_OK:
                    return
                source = Path(file_dialog.GetPath())
            raw = json.loads(source.read_text(encoding="utf-8"))
            warnings = self.features.import_profile_data(raw)
            for warning in warnings:
                self._record_notification(warning, "warning")
            refresh_profile_list(self.features.active_profile_id)
            refresh_summary()
            self._set_status(f"Imported profile data from {source.name}")
            self._refresh_title()

        chooser.Bind(wx.EVT_LISTBOX, lambda _e: refresh_summary())
        keyboard_pack_choice.Bind(wx.EVT_CHOICE, lambda _e: refresh_keyboard_preview())
        switch_button = wx.Button(panel, label="Switch Profile")
        compare_button = wx.Button(panel, label="Compare Profiles")
        undo_button = wx.Button(panel, label="Undo Last Change")
        reset_button = wx.Button(panel, label="Reset to Essential")
        create_custom_button = wx.Button(panel, label="Create Custom...")
        update_custom_button = wx.Button(panel, label="Update Custom from Current")
        delete_custom_button = wx.Button(panel, label="Delete Custom")
        export_button = wx.Button(panel, label="Export...")
        import_button = wx.Button(panel, label="Import...")
        apply_pack_button = wx.Button(panel, label="Apply Keyboard Pack")
        reset_pack_button = wx.Button(panel, label="Reset Keyboard Pack")
        customize_pack_button = wx.Button(panel, label="Customize Shortcuts...")
        apply_indent_button = wx.Button(panel, label="Apply Indentation")
        close_button = wx.Button(panel, id=wx.ID_OK, label="Close")
        switch_button.Bind(wx.EVT_BUTTON, lambda _e: switch_selected())
        compare_button.Bind(wx.EVT_BUTTON, lambda _e: compare_selected())
        undo_button.Bind(wx.EVT_BUTTON, lambda _e: undo_change())
        reset_button.Bind(wx.EVT_BUTTON, lambda _e: reset_essential())
        create_custom_button.Bind(wx.EVT_BUTTON, lambda _e: create_custom_profile())
        update_custom_button.Bind(wx.EVT_BUTTON, lambda _e: update_selected_custom_profile())
        delete_custom_button.Bind(wx.EVT_BUTTON, lambda _e: delete_selected_custom_profile())
        export_button.Bind(wx.EVT_BUTTON, lambda _e: export_profile())
        import_button.Bind(wx.EVT_BUTTON, lambda _e: import_profile())
        apply_pack_button.Bind(wx.EVT_BUTTON, lambda _e: apply_selected_keyboard_pack())
        reset_pack_button.Bind(wx.EVT_BUTTON, lambda _e: reset_keyboard_pack())
        customize_pack_button.Bind(wx.EVT_BUTTON, lambda _e: customize_keymap())
        apply_indent_button.Bind(wx.EVT_BUTTON, lambda _e: apply_indentation_settings())
        close_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))

        root.Add(chooser, 1, wx.ALL | wx.EXPAND, 8)
        root.Add(summary, 1, wx.ALL | wx.EXPAND, 8)
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Keyboard experience: choose a golden pack inspired by familiar editors, "
                    "or keep a fully custom layout."
                ),
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            8,
        )
        root.Add(keyboard_pack_choice, 0, wx.ALL | wx.EXPAND, 8)
        root.Add(keyboard_preview, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        root.Add(
            wx.StaticText(panel, label="Indentation: choose tabs or spaces and indentation width."),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            8,
        )
        indent_row = wx.BoxSizer(wx.HORIZONTAL)
        indent_row.Add(indent_style_choice, 1, wx.RIGHT, 8)
        indent_row.Add(indent_size_spin, 0)
        indent_row.Add(apply_indent_button, 0, wx.LEFT, 8)
        root.Add(indent_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(switch_button, 0, wx.RIGHT, 6)
        buttons.Add(compare_button, 0, wx.RIGHT, 6)
        buttons.Add(undo_button, 0, wx.RIGHT, 6)
        buttons.Add(reset_button, 0, wx.RIGHT, 6)
        buttons.Add(create_custom_button, 0, wx.RIGHT, 6)
        buttons.Add(update_custom_button, 0, wx.RIGHT, 6)
        buttons.Add(delete_custom_button, 0, wx.RIGHT, 6)
        buttons.Add(export_button, 0, wx.RIGHT, 6)
        buttons.Add(import_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(apply_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(reset_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(customize_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(close_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        refresh_profile_list()
        refresh_summary()
        refresh_keyboard_preview()
        self._show_modal_dialog(dialog, "Profiles and Features")

    def undo_last_profile_change(self) -> None:
        if self.features.undo_last_profile_change():
            self._set_status(f"Profile changed back to {self.features.active_profile.name}")
            self._refresh_title()
            return
        self._set_status("No profile change to undo")

    def reset_feature_profile_to_essential(self) -> None:
        wx = self._wx
        with wx.MessageDialog(
            self.frame,
            "Reset Quill to the Essential profile?",
            "Reset Feature Profile",
            wx.YES_NO | wx.ICON_QUESTION,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Reset Feature Profile") != wx.ID_YES:
                return
        self.features.reset_to_essential_profile()
        self._set_status("Reset to Essential profile")
        self._refresh_title()

    def run_startup_wizard(self) -> None:
        wx = self._wx
        self.show_startup_wizard_page()
        proceed = self._show_message_box(
            "The Startup Wizard overview opened in preview. Start guided setup now?\n\n"
            "This will walk through profile, AI, assistant, speech, and watch folder setup.",
            "Startup Wizard",
            wx.ICON_QUESTION | wx.YES_NO,
        )
        if proceed != wx.YES:
            self._set_status("Startup Wizard opened")
            return
        if not self._show_trust_consent_onboarding(force=True):
            self._set_status("Startup consent is required to continue setup.")
            return
        self._show_profile_onboarding(force=True)
        self._offer_ai_onboarding()
        self._show_assistant_onboarding(force=True)
        self._show_speech_onboarding(force=True)
        self._show_watch_folder_onboarding(force=True)
        self._set_status("Startup Wizard completed")

    def run_profile_onboarding(self) -> None:
        # Backward-compatible alias for older command IDs and automation scripts.
        self.run_startup_wizard()

    def _maybe_run_first_run_onboarding(self) -> None:
        if any(
            (
                getattr(self, "_first_run_trust_consent_prompt", False),
                getattr(self, "_first_run_profile_prompt", False),
                getattr(self, "_first_run_assistant_prompt", False),
                getattr(self, "_first_run_speech_prompt", False),
                getattr(self, "_first_run_watch_folder_prompt", False),
            )
        ):
            self.show_startup_wizard_page()
        if getattr(self, "_first_run_profile_prompt", False):
            self._show_profile_onboarding(force=False)
            self._first_run_profile_prompt = False
            self._offer_ai_onboarding()
        if getattr(self, "_first_run_assistant_prompt", False):
            self._show_assistant_onboarding(force=False)
            self._first_run_assistant_prompt = False
        if getattr(self, "_first_run_speech_prompt", False):
            self._show_speech_onboarding(force=False)
            self._first_run_speech_prompt = False
        if getattr(self, "_first_run_watch_folder_prompt", False):
            self._show_watch_folder_onboarding(force=False)
            self._first_run_watch_folder_prompt = False

    def show_startup_wizard_page(self) -> None:
        index = self._open_generated_tab(
            "Startup Wizard",
            self._build_startup_wizard_html(),
        )
        self._select_tab(index)
        if 0 <= index < len(self._document_tabs):
            self._show_side_preview_for(self._document_tabs[index])
        self._set_status("Opened Startup Wizard overview")

    def _show_trust_consent_onboarding(self, force: bool) -> bool:
        wx = self._wx
        message = (
            "Trust, Privacy, and Responsible AI Use\n\n"
            "By selecting Yes, you confirm that:\n"
            "1. You are responsible for how AI outputs are used, reviewed, and shared.\n"
            "2. Cloud AI requests are user-initiated and subject to provider terms.\n"
            "3. Quill does not persist chat session transcripts from AI interactions.\n"
            "4. API keys are stored in Windows Credential Manager when available, "
            "with DPAPI-encrypted fallback storage.\n\n"
            "Do you accept and want to continue?"
        )
        accepted = (
            self._show_message_box(
                message,
                "Trust and Privacy Consent",
                wx.ICON_QUESTION | wx.YES_NO,
            )
            == wx.YES
        )
        if accepted:
            mark_trust_consent_complete()
            return True
        if force:
            return False
        return False

    def _build_startup_wizard_html(self) -> str:
        status_rows = [
            (
                "Trust and privacy consent",
                "Completed" if load_trust_consent_complete() else "Pending",
                "Acknowledge responsible AI use, data handling, and user accountability.",
            ),
            (
                "Profile setup",
                "Completed" if load_onboarding_complete() else "Pending",
                "Choose how Quill starts and what features are surfaced.",
            ),
            (
                "Writing assistant setup",
                "Completed" if load_assistant_onboarding_complete() else "Pending",
                "Enable assistant defaults and prompt style.",
            ),
            (
                "Speech setup",
                "Completed" if load_speech_onboarding_complete() else "Pending",
                "Configure engines, paths, voices, and downloads.",
            ),
            (
                "Watch folder setup",
                "Completed" if load_watch_folder_onboarding_complete() else "Pending",
                "Automatically open new supported files dropped into one folder.",
            ),
        ]
        status_html = "".join(
            (
                "<tr>"
                f"<td>{html.escape(step)}</td>"
                f"<td>{html.escape(state)}</td>"
                f"<td>{html.escape(detail)}</td>"
                "</tr>"
            )
            for step, state, detail in status_rows
        )

        flow_steps = [
            "Step 1: Review and accept trust, privacy, and responsible AI terms.",
            "Step 2: Choose your startup profile.",
            "Step 3: Decide whether AI should be enabled now.",
            "Step 4: Configure writing assistant defaults.",
            "Step 5: Configure speech engines and download optional runtimes.",
            "Step 6: Set up watch folder automation for supported document intake.",
            "Step 7: Confirm settings and start writing.",
        ]
        flow_html = "".join(f"<li>{html.escape(step)}</li>" for step in flow_steps)

        return (
            "<h1 id='startup-wizard'>Startup Wizard</h1>"
            "<p>This guided setup prepares Quill for your preferred writing, AI, and speech experience.</p>"
            "<h2 id='progress'>Current Setup Progress</h2>"
            "<table>"
            "<caption>Wizard setup status</caption>"
            "<thead><tr>"
            "<th scope='col'>Setup area</th>"
            "<th scope='col'>Status</th>"
            "<th scope='col'>What this controls</th>"
            "</tr></thead>"
            f"<tbody>{status_html}</tbody>"
            "</table>"
            "<h2 id='guided-flow'>Guided Flow</h2>"
            f"<ol>{flow_html}</ol>"
            "<h2 id='accessibility-notes'>Accessibility Notes</h2>"
            "<ul>"
            "<li>Every step uses keyboard-first dialogs with clear announcements.</li>"
            "<li>You can cancel any step and rerun Startup Wizard from the Help menu.</li>"
            "<li>No speech downloads occur without explicit confirmation.</li>"
            "</ul>"
            "<h2 id='where-next'>After Wizard</h2>"
            "<p>Open Help > Status Page (HTML Preview) to monitor task activity, feature state, and speech setup health.</p>"
        )

    def _offer_ai_onboarding(self) -> None:
        """First run: ask whether to use AI; if yes, set up the model."""
        from quill.core.ai.llama_cpp_backend import LlamaCppBackend
        from quill.core.ai.model_manager import existing_model, save_ai_enabled

        wx = self._wx
        use_ai = self._show_message_box(
            "Do you want to use Quill's built-in artificial intelligence (Ask Quill)?\n\n"
            "It runs entirely on your computer. You can turn it on or off later from the "
            "AI menu.",
            "Use Artificial Intelligence?",
            wx.ICON_QUESTION | wx.YES_NO,
        )
        enabled = use_ai == wx.YES
        save_ai_enabled(enabled)
        self._sync_ai_enabled_menu(enabled)
        if not enabled:
            self._set_status("AI is off. You can enable it later from the AI menu.")
            return
        # Foundation Models (macOS) needs no download; only llama.cpp does.
        assistant = self._get_assistant()
        if (
            isinstance(assistant.backend, LlamaCppBackend)
            and assistant.is_available()[0]
            and not existing_model()
        ):
            AIModelDialog(self.frame, announce=self._set_status).show()
        else:
            self._set_status("AI is ready.")

    def _sync_ai_enabled_menu(self, enabled: bool) -> None:
        menu_bar = self.frame.GetMenuBar()
        if menu_bar is not None and hasattr(self, "_id_ai_enabled"):
            item = menu_bar.FindItemById(self._id_ai_enabled)
            if item is not None:
                item.Check(enabled)

    def _show_profile_onboarding(self, force: bool) -> None:
        wx = self._wx
        profiles = list(PROFILE_DEFINITIONS.values())
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose how Quill should start:",
            "Profile Onboarding",
            choices=self._profile_choice_labels(profiles),
        ) as dialog:
            if self._show_modal_dialog(dialog, "Profile Onboarding") != wx.ID_OK:
                if not force:
                    mark_onboarding_complete()
                if force:
                    self._set_status("Profile onboarding skipped")
                return
            selection = dialog.GetSelection()
        if selection == wx.NOT_FOUND:
            if not force:
                mark_onboarding_complete()
            return
        profile = profiles[selection]
        self.features.switch_profile(profile.id)
        mark_onboarding_complete()
        self._set_status(f"Quill starts in the {profile.name} profile")
        self._refresh_title()

    def _show_assistant_onboarding(self, force: bool) -> None:
        wx = self._wx
        with wx.Dialog(
            self.frame,
            title="Writing Assistant Onboarding",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        ) as dialog:
            panel = wx.Panel(dialog)
            root = wx.BoxSizer(wx.VERTICAL)
            panel_sizer = wx.BoxSizer(wx.VERTICAL)

            panel_sizer.Add(
                wx.StaticText(
                    panel,
                    label=(
                        "Quill can seed the writing assistant with a few focused prompt styles. "
                        "You can change this later in General Preferences."
                    ),
                ),
                0,
                wx.EXPAND | wx.ALL,
                8,
            )

            assistant_enabled = wx.CheckBox(panel, label="Enable the writing assistant by default")
            assistant_enabled.SetValue(getattr(self.settings, "assistant_enabled", False))
            panel_sizer.Add(assistant_enabled, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            prompt_style = wx.Choice(panel, choices=["Balanced", "Concise", "Gentle", "Technical"])
            prompt_style.SetSelection(
                {
                    "balanced": 0,
                    "concise": 1,
                    "gentle": 2,
                    "technical": 3,
                }.get(getattr(self.settings, "assistant_prompt_style", "balanced"), 0)
            )
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.Add(wx.StaticText(panel, label="Prompt style"), 0, wx.ALIGN_CENTER_VERTICAL)
            row.AddSpacer(8)
            row.Add(prompt_style, 1, wx.EXPAND)
            panel_sizer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            panel.SetSizer(panel_sizer)
            buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
            root.Add(panel, 1, wx.EXPAND | wx.ALL, 8)
            if buttons is not None:
                root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
            dialog.SetSizerAndFit(root)

            if self._show_modal_dialog(dialog, "Writing Assistant Onboarding") != wx.ID_OK:
                if not force:
                    mark_assistant_onboarding_complete()
                return

            self.settings.assistant_enabled = bool(assistant_enabled.GetValue())
            self.settings.assistant_prompt_style = {
                0: "balanced",
                1: "concise",
                2: "gentle",
                3: "technical",
            }.get(prompt_style.GetSelection(), "balanced")
            save_settings(self.settings)
            mark_assistant_onboarding_complete()
            self._set_status("Configured writing assistant onboarding")

    def _show_speech_onboarding(self, force: bool) -> None:  # noqa: PLR0912
        wx = self._wx
        start_setup = self._show_message_box(
            "Set up speech engines now?\n\n"
            "You can download/configure DECtalk, eSpeak-NG, Piper, Kokoro, VibeVoice, RHVoice, MeloTTS, Chatterbox, and OpenVoice.\n"
            "You can always change these later in AI > Speech > Settings.",
            "Speech Setup",
            wx.ICON_QUESTION | wx.YES_NO,
        )
        if start_setup != wx.YES:
            if not force:
                mark_speech_onboarding_complete()
            self._set_status("Speech setup skipped")
            return

        choices = [
            "Download and configure DECtalk runtime (recommended)",
            "Configure eSpeak-NG path and English variant",
            "Configure Piper executable and English model folder",
            "Configure Kokoro English voice defaults",
            "Download VibeVoice model and voices (speech-file generator)",
            "Configure RHVoice executable and English voice",
            "Configure MeloTTS executable and English voice",
            "Configure Chatterbox executable and English voice",
            "Configure OpenVoice executable, English voice, and consent",
            "Open speech setup docs",
        ]
        with wx.MultiChoiceDialog(
            self.frame,
            "Select the speech setup steps you want to run now:",
            "Speech Setup",
            choices=choices,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Speech Setup") != wx.ID_OK:
                if not force:
                    mark_speech_onboarding_complete()
                self._set_status("Speech setup cancelled")
                return
            selected = set(dialog.GetSelections())

        def _ask_text(prompt: str, value: str) -> str | None:
            with wx.TextEntryDialog(self.frame, prompt, "Speech Setup", value=value) as td:
                if self._show_modal_dialog(td, "Speech Setup") != wx.ID_OK:
                    return None
                return td.GetValue().strip()

        if 0 in selected:
            speech_root = app_data_dir() / "speech" / "dectalk"

            def work(progress: Callable[[str, int, int], None]) -> object:
                progress("Downloading DECtalk runtime", 0, 1)
                exe = download_dectalk_runtime(speech_root)
                progress("Finalizing DECtalk runtime", 1, 1)
                return str(exe)

            def on_success(result: object) -> None:
                self.settings.read_aloud_dectalk_executable = str(result)
                save_settings(self.settings)
                self._set_status("DECtalk runtime downloaded and configured")

            self._run_background_task(
                "Downloading DECtalk speech runtime",
                work,
                on_success,
                notify_on_success=True,
                notify_on_error=True,
                notification_category="speech",
            )

        if 1 in selected:
            path = _ask_text(
                "Path to espeak-ng.exe (leave blank to use PATH):",
                self.settings.read_aloud_espeak_executable,
            )
            if path is not None:
                self.settings.read_aloud_espeak_executable = path
            voices = list_espeak_english_voices()
            if voices:
                voice_names = [voice.name for voice in voices]
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default eSpeak English voice:",
                    "Speech Setup",
                    choices=voice_names,
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_espeak_voice = voices[idx].id

        if 2 in selected:
            exe = _ask_text("Path to piper.exe:", self.settings.read_aloud_piper_executable)
            if exe is not None:
                self.settings.read_aloud_piper_executable = exe
            model_dir = _ask_text(
                "Folder containing English Piper .onnx models:",
                self.settings.read_aloud_piper_model_dir,
            )
            if model_dir is not None:
                self.settings.read_aloud_piper_model_dir = model_dir

        if 3 in selected:
            voices = list_kokoro_voices()
            if voices:
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default Kokoro English voice:",
                    "Speech Setup",
                    choices=[voice.name for voice in voices],
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_kokoro_voice = voices[idx].id

        if 4 in selected:
            # VibeVoice is an offline speech-FILE generator (not a live read-aloud
            # voice). Download its model + voices via the GUI (no terminal); the
            # same action is available any time at AI > Speech > Download VibeVoice.
            self.download_vibevoice_model()

        if 5 in selected:
            exe = _ask_text(
                "Path to RHVoice executable:", self.settings.read_aloud_rhvoice_executable
            )
            if exe is not None:
                self.settings.read_aloud_rhvoice_executable = exe
            voices = list_rhvoice_english_voices()
            if voices:
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default RHVoice English voice:",
                    "Speech Setup",
                    choices=[voice.name for voice in voices],
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_rhvoice_voice = voices[idx].id

        if 6 in selected:
            exe = _ask_text(
                "Path to MeloTTS executable:", self.settings.read_aloud_melotts_executable
            )
            if exe is not None:
                self.settings.read_aloud_melotts_executable = exe
            voices = list_melotts_english_voices()
            if voices:
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default MeloTTS English voice:",
                    "Speech Setup",
                    choices=[voice.name for voice in voices],
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_melotts_voice = voices[idx].id

        if 7 in selected:
            exe = _ask_text(
                "Path to Chatterbox executable:", self.settings.read_aloud_chatterbox_executable
            )
            if exe is not None:
                self.settings.read_aloud_chatterbox_executable = exe
            voices = list_chatterbox_english_voices()
            if voices:
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default Chatterbox English voice:",
                    "Speech Setup",
                    choices=[voice.name for voice in voices],
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_chatterbox_voice = voices[idx].id

        if 8 in selected:
            exe = _ask_text(
                "Path to OpenVoice executable:", self.settings.read_aloud_openvoice_executable
            )
            if exe is not None:
                self.settings.read_aloud_openvoice_executable = exe
            voices = list_openvoice_english_voices()
            if voices:
                with wx.SingleChoiceDialog(
                    self.frame,
                    "Choose default OpenVoice English voice:",
                    "Speech Setup",
                    choices=[voice.name for voice in voices],
                ) as voice_dialog:
                    if self._show_modal_dialog(voice_dialog, "Speech Setup") == wx.ID_OK:
                        idx = voice_dialog.GetSelection()
                        if 0 <= idx < len(voices):
                            self.settings.read_aloud_openvoice_voice = voices[idx].id
            consent = self._show_message_box(
                "Enable OpenVoice advanced style module on this machine?\n\n"
                "This feature is optional and remains disabled unless you explicitly consent.",
                "Speech Setup",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            self.settings.read_aloud_openvoice_consent = consent == wx.YES

        if 9 in selected:
            docs_path = app_data_dir().parent / "Quill" / "docs" / "userguide.md"
            webbrowser.open(str(docs_path))

        save_settings(self.settings)
        mark_speech_onboarding_complete()
        self._set_status("Speech setup complete")

    def _profile_choice_labels(self, profiles: list[object]) -> list[str]:
        return [self._profile_choice_label(profile) for profile in profiles]

    def _profile_choice_label(self, profile: object) -> str:
        name = str(getattr(profile, "name", "Profile")).strip()
        description = " ".join(str(getattr(profile, "description", "")).split())
        if not description:
            return name
        return f"{name} — {description}"

    def show_regex_helper(self) -> None:
        report = (
            "Regex helper\n\n"
            r"\d any digit"
            "\n"
            r"\w any word character"
            "\n"
            r"\s whitespace"
            "\n"
            r"^ start of line"
            "\n"
            r"$ end of line"
            "\n"
            r"+ one or more"
            "\n"
            r"* zero or more"
            "\n"
            r"? optional"
            "\n"
            r"(text) capture group"
            "\n"
            r"(?P<name>text) named group"
            "\n"
            "Use the search mode selector to choose plain text, whole word, "
            "regular expression, or wildcard."
        )
        self._show_message_box(report, "Regex Helper", self._wx.ICON_INFORMATION | self._wx.OK)

    def copy_with_source(self) -> None:
        start, end = self.editor.GetSelection()
        if start == end:
            start, end = line_span(self.editor.GetValue(), self.editor.GetInsertionPoint())
        selection = self.editor.GetRange(start, end)
        if not selection.strip():
            self._set_status("Nothing selected to copy")
            return
        source = build_source_reference(
            self.document, self.editor.GetInsertionPoint(), self.editor.GetValue()
        )
        payload = f"{selection}\n\n{source}"
        if not self._copy_to_clipboard(payload):
            self._set_status("Could not copy with source")
            return
        self._set_status("Copied selection with source")

    def _copy_to_clipboard(self, text: str) -> bool:
        wx = self._wx
        data_object = wx.TextDataObject(text)
        clipboard = wx.TheClipboard
        if not clipboard.Open():
            return False
        try:
            clipboard.SetData(data_object)
        finally:
            clipboard.Close()
        return True

    def exit_app(self) -> None:
        self._is_exiting = True
        self.frame.Close()


def run_app(
    startup_paths: list[Path] | None = None,
    safe_mode: bool = False,
    diagnostics_mode: bool = False,
) -> None:
    import wx

    app = wx.App(False)
    mark_wx_main_thread()
    if diagnostics_mode or should_trace_memory():
        start_memory_tracing()
    frame = MainFrame(safe_mode=safe_mode)
    heartbeat_state = HeartbeatState()
    frame._stability_heartbeat_state = heartbeat_state
    frame._stability_heartbeat_timer = WxHeartbeatTimer(frame.frame, heartbeat_state)
    frame._stability_watchdog = WxHeartbeatWatchdog(heartbeat_state)
    frame._stability_watchdog.start()
    for path in startup_paths or []:
        if path.exists() and path.is_file():
            frame.open_file(path)
    frame.show()
    try:
        app.MainLoop()
    finally:
        timer = getattr(frame, "_stability_heartbeat_timer", None)
        if timer is not None:
            timer.stop()
        watchdog = getattr(frame, "_stability_watchdog", None)
        if watchdog is not None:
            watchdog.stop()
