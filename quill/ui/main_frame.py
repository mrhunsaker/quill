from __future__ import annotations

import json
import os
import re
import threading
import time
import unicodedata
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:  # imports kept out of cold-start path
    from quill.core.epub import EpubBook

from quill import __version__
from quill.core import thesaurus as thesaurus_engine
from quill.core.a11y_regions import (
    RegionTracker,
    build_accessibility_audit_report,
    render_snapshot,
)
from quill.core.autosave import autosave_document
from quill.core.backups import backup_document, list_backups
from quill.core.bookmarks import bookmark_names, bookmark_position, set_bookmark
from quill.core.commands import CommandRegistry
from quill.core.contrast import render_contrast_report, validate_theme_contrast
from quill.core.diagnostics import (
    build_bug_report_payload,
    build_diagnostics_review_text,
    build_support_issue_url,
    collect_environment_info,
    record_diagnostic_event,
    write_diagnostics_bundle,
)
from quill.core.diffing import build_unified_diff
from quill.core.document import Document
from quill.core.external_tools import (
    copyable_install_command,
    get_external_tool_status,
    get_external_tool_statuses,
)
from quill.core.features import (
    PROFILE_DEFINITIONS,
    FeatureManager,
    features_path,
)
from quill.core.format_ops import (
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
from quill.core.intake import (
    build_bad_extraction_package,
    build_context_help,
    build_extraction_quality_report,
    build_intake_report,
    build_intake_summary,
    build_source_reference,
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
from quill.core.outline import OutlineEntry, extract_outline_entries
from quill.core.paths import app_data_dir, ensure_app_directories
from quill.core.read_aloud import (
    ReadAloudController,
    ReadAloudUnavailableError,
    list_voices,
)
from quill.core.recent import add_recent_file, clear_recent_files, load_recent_files
from quill.core.recovery import begin_session, mark_clean_exit, read_recovery_snapshot
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
from quill.core.settings import STATUS_BAR_ITEMS, load_settings, save_settings
from quill.core.spellcheck import (
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
)
from quill.core.transforms import to_lower, to_sentence_case, to_title, to_toggle_case, to_upper
from quill.core.trust import is_trusted_location, load_trusted_locations, save_trusted_locations
from quill.core.undo_store import load_undo_history, save_undo_history
from quill.core.updates import DEFAULT_UPDATE_MANIFEST_URL, fetch_update_manifest, is_newer_version
from quill.core.url_ops import format_content_length, host_for_url, is_cross_host_redirect
from quill.io.pandoc import (
    PandocConversionError,
    PandocUnavailableError,
    convert_document_with_pandoc,
)
from quill.io.text import read_text_document, write_text_document
from quill.platform.windows.high_contrast import is_high_contrast_enabled
from quill.platform.windows.shell_integration import (
    build_shell_integration_plan,
    install_shell_integration,
    launcher_command,
    remove_shell_integration,
)
from quill.platform.windows.sr_announce import announce, set_announce_handler
from quill.platform.windows.sr_detect import detect_screen_reader
from quill.ui.palette import CommandPaletteDialog


@dataclass(slots=True)
class _DocumentTab:
    panel: object
    editor: object
    document: Document


@dataclass(slots=True)
class _NavigatorNode:
    label: str
    preview: str
    payload: object
    children: list[_NavigatorNode]


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


class MainFrame:
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
        self._first_run_profile_prompt = not safe_mode and not features_path().exists()
        self.features = FeatureManager.load(persistent=not safe_mode)
        self.macros = MacroManager.load(persistent=not safe_mode)
        self.settings = load_settings()
        if safe_mode:
            self.settings.theme = "system"
            self.settings.tray_enabled = False
            self.settings.persistent_undo = False
            self.settings.spellcheck_as_you_type = False
            self.settings.start_with_no_document_open = False
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
        self._extend_selection_mode = False
        self._extend_selection_anchor: int | None = None
        self._epub_book: EpubBook | None = None
        self._bookmarks: dict[str, int] = {}
        self._tray_icon: object | None = None
        self._is_exiting = False
        self._ipc_timer: object | None = None
        self._status_message = "Ready"
        self._last_intake_report = ""
        self._startup_deferred_ran = False
        self._compare_session: _CompareSession | None = None
        self._compare_ignore_trailing_spaces = True
        self._compare_ignore_line_endings = True
        self._empty_workspace_active = False
        self._read_aloud = ReadAloudController()
        self._overwrite_mode = False
        self._insert_key_down = False
        self._print_data = wx.PrintData()
        self._page_setup_data = wx.PageSetupDialogData(self._print_data)
        self.commands = CommandRegistry()
        self.commands.set_run_listener(self._on_command_run)
        self._recent_menu_ids: dict[int, Path] = {}
        self._recent_session_menu_ids: dict[int, Path] = {}
        self._session_menu_ids: dict[int, int] = {}
        self._recent_sessions = [] if safe_mode else load_recent_sessions()

        self.frame = wx.Frame(None, title="Untitled - Quill", size=(1000, 700))
        self.notebook = wx.Notebook(self.frame)
        self._document_tabs: list[_DocumentTab] = []
        self._active_tab_index = -1
        self._statusbar_cells: list[_StatusBarCell] = []
        self._active_statusbar_cell_index = 0
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.notebook, 1, wx.EXPAND)
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
        self._build_menu()
        self._refresh_sessions_menu()
        self._apply_accelerators()
        self._bind_events()
        self._apply_startup_document_preference()

        set_announce_handler(self._announce)
        if safe_mode:
            self._set_status("Safe mode enabled. Optional state is disabled.")
        else:
            self._set_status("Ready. Tip: press Ctrl+Shift+P for Command Palette.")
        self._refresh_title()

    def show(self) -> None:
        self.frame.Show(True)
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
        self._offer_crash_recovery()
        self._maybe_run_first_run_onboarding()

    def _apply_startup_document_preference(self) -> None:
        if not self.settings.start_with_no_document_open:
            return
        if len(self._document_tabs) != 1:
            return
        if self.document.path is not None or self.document.modified or self.editor.GetValue():
            return
        self._empty_workspace_active = True
        self.editor.SetEditable(False)
        self.notebook.SetPageText(0, "Start")
        self._set_status("No document open. Use File > New or File > Open.")

    def _clear_empty_workspace_state(self) -> None:
        if not self._empty_workspace_active:
            return
        self._empty_workspace_active = False
        self.editor.SetEditable(True)
        self.notebook.SetPageText(self._current_tab_index(), self.document.name)

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
            "file.print_preview",
            "Print Preview...",
            self.print_preview,
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
            "tools.word_count",
            "Word Count...",
            self.show_word_count,
            self._binding_for("tools.word_count"),
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
            "tools.epub_navigator",
            "EPUB Navigator...",
            self.open_epub_navigator,
            self._binding_for("tools.epub_navigator"),
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
            "help.run_profile_onboarding",
            "Run Profile Onboarding",
            self.run_profile_onboarding,
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
            "help.what_can_i_do_here",
            "What Can I Do Here?",
            self.show_context_help,
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
            "edit.find_all_matches",
            "Find All Matches",
            self.find_all_matches,
            self._binding_for("edit.find_all_matches"),
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
        self._id_print_preview = wx.NewIdRef()
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
        file_menu.AppendSubMenu(self._sessions_menu, "Ses&sions")
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
        file_menu.Append(self._id_print_preview, "Print Pre&view...")
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
        self._id_replace_all = wx.NewIdRef()
        self._id_insert_link = wx.NewIdRef()
        self._id_follow_link = wx.NewIdRef()
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
            self._menu_label("&Set Mark", "edit.set_mark"),
        )
        mark_ring_menu.Append(
            self._id_pop_mark,
            self._menu_label("&Pop Mark", "edit.pop_mark"),
        )
        mark_ring_menu.Append(
            self._id_exchange_point_mark,
            self._menu_label(
                "&Exchange Point and Mark",
                "edit.exchange_point_mark",
            ),
        )
        mark_ring_menu.Append(
            self._id_list_marks,
            self._menu_label("&List Marks", "edit.list_marks"),
        )
        selection_menu.AppendSeparator()
        selection_menu.AppendSubMenu(mark_ring_menu, "Mark &Ring")
        edit_menu.AppendSubMenu(selection_menu, "&Selection")
        edit_menu.AppendSeparator()
        edit_menu.Append(self._id_find, self._menu_label("&Find...", "edit.find"))
        edit_menu.Append(
            self._id_replace_all,
            self._menu_label("Rep&lace All...", "edit.replace_all"),
        )
        edit_menu.AppendSeparator()
        edit_menu.Append(
            self._id_preferences,
            self._menu_label("Pre&ferences...", "app.preferences"),
        )
        menu_bar.Append(edit_menu, "&Edit")

        self._id_send_to_tray = wx.NewIdRef()
        self._id_toggle_tray_mode = wx.NewIdRef()
        self._id_toggle_soft_wrap = wx.NewIdRef()
        self._id_toggle_dark_mode = wx.NewIdRef()
        self._id_toggle_persistent_undo = wx.NewIdRef()
        self._id_toggle_spellcheck_as_you_type = wx.NewIdRef()
        self._id_toggle_show_line_numbers = wx.NewIdRef()
        self._id_start_with_no_document_open = wx.NewIdRef()
        view_menu = wx.Menu()
        view_menu.AppendCheckItem(self._id_toggle_tray_mode, "Enable System Tray &Mode")
        view_menu.Check(self._id_toggle_tray_mode, self.settings.tray_enabled)
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(
            self._id_toggle_soft_wrap,
            self._menu_label("Toggle Soft &Wrap", "view.toggle_soft_wrap"),
        )
        view_menu.Check(self._id_toggle_soft_wrap, self.settings.soft_wrap)
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
            self._id_toggle_show_line_numbers,
            "Show &Line Numbers",
        )
        view_menu.Check(
            self._id_toggle_show_line_numbers,
            self.settings.show_line_numbers,
        )
        view_menu.AppendCheckItem(
            self._id_start_with_no_document_open,
            "Start With &No Document Open",
        )
        view_menu.Check(
            self._id_start_with_no_document_open,
            self.settings.start_with_no_document_open,
        )
        menu_bar.Append(view_menu, "&View")

        navigate_menu = wx.Menu()
        self._id_go_to_line = wx.NewIdRef()
        self._id_find_next = wx.NewIdRef()
        self._id_find_previous = wx.NewIdRef()
        self._id_find_all_matches = wx.NewIdRef()
        self._id_set_bookmark = wx.NewIdRef()
        self._id_go_to_bookmark = wx.NewIdRef()
        self._id_go_to_page = wx.NewIdRef()
        self._id_back_location = wx.NewIdRef()
        self._id_forward_location = wx.NewIdRef()
        self._id_next_heading = wx.NewIdRef()
        self._id_previous_heading = wx.NewIdRef()
        self._id_next_block = wx.NewIdRef()
        self._id_previous_block = wx.NewIdRef()
        self._id_outline_navigator = wx.NewIdRef()
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
        navigate_menu.AppendSeparator()
        navigate_menu.Append(
            self._id_find_next,
            self._menu_label("Find &Next", "edit.find_next"),
        )
        navigate_menu.Append(
            self._id_find_previous,
            self._menu_label("Find &Previous", "edit.find_previous"),
        )
        navigate_menu.Append(
            self._id_find_all_matches,
            self._menu_label("Find &All Matches", "edit.find_all_matches"),
        )
        self._id_insert_html_tag = wx.NewIdRef()
        self._id_insert_markdown_tag = wx.NewIdRef()
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
        format_menu.AppendSubMenu(heading_menu, "Insert &Heading")
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
        format_menu.AppendSubMenu(list_menu, "Insert &List")
        format_menu.Append(
            self._id_insert_code_block,
            self._menu_label("Insert Code &Block", "format.insert_code_block"),
        )
        format_menu.Append(
            self._id_insert_footnote,
            self._menu_label("Insert &Footnote", "format.insert_footnote"),
        )
        format_menu.Append(
            self._id_insert_table,
            self._menu_label("Insert &Table...", "format.insert_table"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(
            self._id_insert_html_tag,
            self._menu_label("Insert &HTML Tag...", "format.insert_html_tag"),
        )
        format_menu.Append(
            self._id_insert_markdown_tag,
            self._menu_label("Insert &Markdown Tag...", "format.insert_markdown_tag"),
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
        self._id_spell_check = wx.NewIdRef()
        self._id_next_misspelling = wx.NewIdRef()
        self._id_dictionary_status = wx.NewIdRef()
        self._id_epub_navigator = wx.NewIdRef()
        self._id_ocr_image = wx.NewIdRef()
        self._id_regex_helper = wx.NewIdRef()
        self._id_pandoc_wizard = wx.NewIdRef()
        self._id_external_tools = wx.NewIdRef()
        self._id_read_aloud = wx.NewIdRef()
        self._id_read_aloud_stop = wx.NewIdRef()
        self._id_read_aloud_voice = wx.NewIdRef()
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
        self._id_context_help = wx.NewIdRef()
        self._id_why_dont_i_see_feature = wx.NewIdRef()
        self._id_switch_feature_profile = wx.NewIdRef()
        self._id_feature_profile_health_check = wx.NewIdRef()
        self._id_undo_profile_change = wx.NewIdRef()
        self._id_reset_feature_profile = wx.NewIdRef()
        self._id_profile_onboarding = wx.NewIdRef()
        self._id_keyboard_trap_snapshot = wx.NewIdRef()
        self._id_accessibility_audit = wx.NewIdRef()
        tools_menu = wx.Menu()
        # --- Discovery ---
        tools_menu.Append(
            self._id_palette,
            self._menu_label("&Command Palette...", "app.command_palette"),
        )
        tools_menu.AppendSeparator()
        # --- Writing aids ---
        tools_menu.Append(
            self._id_word_count,
            self._menu_label("&Word Count...", "tools.word_count"),
        )
        tools_menu.Append(
            self._id_spell_check,
            self._menu_label("&Spell Check...", "tools.spell_check_dialog"),
        )
        tools_menu.Append(
            self._id_next_misspelling,
            self._menu_label("Next &Misspelling", "tools.next_misspelling"),
        )
        self._id_thesaurus = wx.NewIdRef()
        tools_menu.Append(
            self._id_thesaurus,
            self._menu_label("&Thesaurus...", "tools.thesaurus"),
        )
        tools_menu.Append(
            self._id_dictionary_status,
            self._menu_label("Dictionary &Status...", "tools.dictionary_status"),
        )
        tools_menu.AppendSeparator()
        # --- Reading aids ---
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
        tools_menu.AppendSubMenu(read_aloud_menu, "Read &Aloud")
        tools_menu.Append(
            self._id_epub_navigator,
            self._menu_label("EPUB &Navigator...", "tools.epub_navigator"),
        )
        tools_menu.Append(
            self._id_ocr_image,
            self._menu_label("OCR &Image...", "tools.ocr_image"),
        )
        tools_menu.AppendSeparator()
        # --- Document intake ---
        tools_menu.Append(
            self._id_document_intake_report,
            self._menu_label("&Document Intake Report...", "tools.document_intake_report"),
        )
        tools_menu.Append(
            self._id_review_extraction_quality,
            self._menu_label("&Review Extraction Quality...", "tools.review_extraction_quality"),
        )
        tools_menu.Append(
            self._id_report_bad_extraction,
            self._menu_label("R&eport Bad Extraction...", "tools.report_bad_extraction"),
        )
        tools_menu.AppendSeparator()
        # --- Power tools ---
        tools_menu.Append(
            self._id_regex_helper,
            self._menu_label("Regex &Helper...", "tools.regex_helper"),
        )
        tools_menu.Append(
            self._id_pandoc_wizard,
            self._menu_label("Pandoc Conversion &Wizard...", "tools.pandoc_wizard"),
        )
        tools_menu.Append(
            self._id_external_tools,
            self._menu_label(
                "External Tools and Format &Support...",
                "tools.external_tools",
            ),
        )
        glow_menu = wx.Menu()
        glow_menu.Append(
            self._id_glow_audit_document,
            self._menu_label("Audit Current &Document", "tools.glow_audit_document"),
        )
        glow_menu.Append(
            self._id_glow_audit_selection,
            self._menu_label("Audit &Selection", "tools.glow_audit_selection"),
        )
        glow_menu.AppendSeparator()
        glow_menu.Append(
            self._id_glow_fix_document,
            self._menu_label("&Fix Current Document", "tools.glow_fix_document"),
        )
        glow_menu.Append(
            self._id_glow_fix_selection,
            self._menu_label("Fix S&election", "tools.glow_fix_selection"),
        )
        tools_menu.AppendSubMenu(glow_menu, "&GLOW")
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
        tools_menu.AppendSubMenu(macro_menu, "&Macros")
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
        tools_menu.AppendSubMenu(convert_menu, "Co&nvert")
        tools_menu.AppendSeparator()
        # --- Compare ---
        tools_menu.Append(self._id_compare_with_file, "Compare with &File...")
        compare_menu = wx.Menu()
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
        tools_menu.AppendSubMenu(compare_menu, "Compare &Documents")
        tools_menu.AppendSeparator()
        # --- Accessibility & inspection ---
        tools_menu.Append(self._id_accessibility_audit, "Accessibility A&udit...")
        tools_menu.Append(
            self._id_keyboard_trap_snapshot,
            "&Keyboard Trap && Tab-Order Snapshot...",
        )
        tools_menu.Append(self._id_validate_contrast, "&Validate Contrast...")
        tools_menu.Append(self._id_link_inventory, "Link Inventory && Alt-Text Catalo&g...")
        tools_menu.AppendSeparator()
        # --- System integration & notifications ---
        tools_menu.Append(self._id_notifications, "Notif&ications...")
        shell_menu = wx.Menu()
        shell_menu.Append(
            self._id_shell_install,
            self._menu_label("&Install Shell Integration...", "tools.shell_install"),
        )
        shell_menu.Append(
            self._id_shell_remove,
            self._menu_label("&Remove Shell Integration", "tools.shell_remove"),
        )
        tools_menu.AppendSubMenu(shell_menu, "Sh&ell Integration")
        tools_menu.AppendSeparator()
        # --- Customize (replaces former Settings top-level menu) ---
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
            self._id_why_dont_i_see_feature,
            self._menu_label("&Why Don't I See a Feature?", "help.why_dont_i_see_feature"),
        )
        help_menu.AppendSeparator()
        self._id_open_user_guide = wx.NewIdRef()
        help_menu.Append(self._id_open_user_guide, "Open User &Guide")
        help_menu.Append(self._id_open_welcome_guide, "Open &Welcome Guide")
        help_menu.Append(self._id_open_keyboard_reference, "Open Keyboard &Reference")
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
        profiles_menu.Append(
            self._id_profile_onboarding,
            self._menu_label("&Run Profile Onboarding", "help.run_profile_onboarding"),
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
        help_menu.AppendSeparator()
        help_menu.Append(self._id_check_updates, "Check for &Updates...")
        help_menu.Append(self._id_about_quill, "&About Quill")
        menu_bar.Append(window_menu, "&Window")
        menu_bar.Append(help_menu, "&Help")

        self.frame.SetMenuBar(menu_bar)
        self._refresh_contextual_menu_items()

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
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.print_preview(),
            id=self._id_print_preview,
        )
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
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_context_help(),
            id=self._id_context_help,
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
            lambda _e: self.run_profile_onboarding(),
            id=self._id_profile_onboarding,
        )
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
            self._on_toggle_show_line_numbers,
            id=self._id_toggle_show_line_numbers,
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
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_next(), id=self._id_find_next)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_previous(), id=self._id_find_previous)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.find_all_matches(),
            id=self._id_find_all_matches,
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
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_word_count(), id=self._id_word_count)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_spell_check_dialog(),
            id=self._id_spell_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.next_misspelling(),
            id=self._id_next_misspelling,
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
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_epub_navigator(),
            id=self._id_epub_navigator,
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
            "file.print_preview": self._id_print_preview,
            "file.print": self._id_print,
            "window.next_document": self._id_next_document,
            "window.previous_document": self._id_previous_document,
            "view.send_to_tray": self._id_send_to_tray,
            "view.toggle_soft_wrap": self._id_toggle_soft_wrap,
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
            "navigate.back_location": self._id_back_location,
            "navigate.forward_location": self._id_forward_location,
            "navigate.outline_navigator": self._id_outline_navigator,
            "navigate.match_bracket": self._id_match_bracket,
            "navigate.next_structure": self._id_next_structure,
            "navigate.previous_structure": self._id_previous_structure,
            "navigate.next_region": self._id_next_region,
            "navigate.previous_region": self._id_previous_region,
            "tools.word_count": self._id_word_count,
            "tools.spell_check_dialog": self._id_spell_check,
            "tools.next_misspelling": self._id_next_misspelling,
            "tools.thesaurus": self._id_thesaurus,
            "tools.dictionary_status": self._id_dictionary_status,
            "tools.epub_navigator": self._id_epub_navigator,
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
            "edit.copy_with_source": self._id_copy_with_source,
            "edit.select_line": self._id_select_line,
            "format.decrease_heading_level": self._id_decrease_heading_level,
            "format.increase_heading_level": self._id_increase_heading_level,
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
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_notebook_page_changed)
        self.notebook.Bind(wx.EVT_CONTEXT_MENU, self._on_notebook_context_menu)
        self.statusbar.Bind(wx.EVT_CONTEXT_MENU, self._on_statusbar_context_menu)
        self.frame.Bind(wx.EVT_CONTEXT_MENU, self._on_frame_context_menu)
        self.frame.Bind(wx.EVT_CLOSE, self._on_close)
        self.frame.Bind(wx.EVT_ICONIZE, self._on_iconize)
        self._apply_soft_wrap(self.settings.soft_wrap)

    def _bind_editor_events(self, editor: object) -> None:
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
        editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_NOHIDESEL,
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(editor, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        if document.text:
            editor.ChangeValue(document.text)
        self._bind_editor_events(editor)
        tab = _DocumentTab(panel=panel, editor=editor, document=document)
        self._document_tabs.append(tab)
        index = self.notebook.GetPageCount()
        self.notebook.AddPage(panel, document.name, select=select)
        if select:
            self._active_tab_index = index
            self.editor = editor
            self.document = document
            self._apply_statusbar_layout()
            self._refresh_title()
        self._refresh_sessions_menu()
        return index

    def _on_notebook_page_changed(self, event: object) -> None:
        selection = self.notebook.GetSelection()
        if selection != self._active_tab_index:
            self._activate_tab(selection)
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
            if candidate.exists() and candidate.is_file():
                self.open_file(candidate)
        self.frame.Show(True)
        self.frame.Raise()
        self.frame.RequestUserAttention()

    def _on_text_changed(self, _event: object) -> None:
        self.document.set_text(self.editor.GetValue())
        if not self._suspend_persistent_undo:
            self._record_persistent_undo_state(self.document.text)
        if self.settings.spellcheck_as_you_type:
            self._announce_spellcheck_hint()
        self._maybe_autosave()
        self._refresh_title()
        self._refresh_contextual_menu_items()
        self._set_status("Modified")

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
        event.Skip()
        wx.CallAfter(self._apply_extend_selection)

    def _apply_extend_selection(self) -> None:
        if not self._extend_selection_mode or self._extend_selection_anchor is None:
            return
        caret = self.editor.GetInsertionPoint()
        start = min(self._extend_selection_anchor, caret)
        end = max(self._extend_selection_anchor, caret)
        self.editor.SetSelection(start, end)

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
        tab_label = self.notebook.GetPageText(target_index) or "this tab"

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
        if not self._prompt_to_save_active_document("Close"):
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
            if not self._prompt_to_save_active_document("Close"):
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
            if not self._prompt_to_save_active_document("Close"):
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
            # /select, highlights the file in Windows Explorer.
            subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603,S607
            self._set_status(f"Revealing {path.name} in Explorer")
        except OSError as error:
            self._set_status(f"Could not open Explorer: {error}")

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

    def _on_toggle_dark_mode(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_dark_mode(enabled)

    def _on_toggle_persistent_undo(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_persistent_undo(enabled)

    def _on_toggle_spellcheck_as_you_type(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.toggle_spellcheck_as_you_type(enabled)

    def _on_toggle_show_line_numbers(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.show_line_numbers = enabled
        self._refresh_statusbar()
        self._set_status("Line numbers on" if enabled else "Line numbers off")

    def _on_toggle_start_with_no_document_open(self, event: object) -> None:
        enabled = bool(event.IsChecked())
        self.settings.start_with_no_document_open = enabled
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
        result = self._show_message_box(
            "Quill detected an unclean exit. Restore the latest autosave snapshot?",
            "Crash Recovery",
            wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Skipped crash recovery")
            self._record_notification("Crash recovery offer dismissed", "recovery")
            return
        recovered_text = read_recovery_snapshot(offer.snapshot)
        self._create_document_tab(
            Document(text=recovered_text, path=None, modified=True),
            select=True,
        )
        self._location_ring = LocationRing()
        self._location_ring.record(0)
        self._refresh_title()
        self._set_status("Recovered latest autosave snapshot")
        self._record_notification("Recovered autosave snapshot", "recovery")

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
        state = self.features.state_for_command(command_id)
        if state == "quiet":
            label = f"{label} [quiet]"
        elif state == "off":
            label = f"{label} [off]"
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
            self._menu_label("Save &Session...", "file.save_session"),
        )
        self._sessions_menu.Append(
            self._id_open_session,
            self._menu_label("&Open Session...", "file.open_session"),
        )
        self._sessions_menu.AppendSubMenu(self._recent_sessions_menu, "Recent &Sessions")
        self._sessions_menu.AppendSeparator()
        self._sessions_menu.AppendSubMenu(self._open_documents_menu, "Open &Documents")
        self._refresh_recent_sessions_menu()
        if not self._document_tabs:
            item = self._open_documents_menu.Append(self._wx.ID_ANY, "(No open documents)")
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
            item = self._recent_sessions_menu.Append(self._wx.ID_ANY, "(No saved sessions)")
            item.Enable(False)
            self._recent_sessions_menu.AppendSeparator()
            self._recent_sessions_menu.Append(
                self._id_clear_recent_sessions,
                "C&lear Recent Sessions",
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
            "C&lear Recent Sessions",
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
        self._set_status(f"Saved session to {target.name}")

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
        self._set_status(f"Opened session {target.name}")

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
        modified_suffix = " [modified]" if self.document.modified else ""
        self.frame.SetTitle(f"{self.document.name}{modified_suffix} - Quill")
        if self._active_tab_index >= 0 and self._active_tab_index < self.notebook.GetPageCount():
            page_title = f"{self.document.name}{modified_suffix}"
            self.notebook.SetPageText(self._active_tab_index, page_title)
        self._refresh_statusbar()

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
        markdown_ids = (
            self._id_insert_markdown_tag,
            self._id_heading_1,
            self._id_heading_2,
            self._id_heading_3,
            self._id_heading_4,
            self._id_heading_5,
            self._id_heading_6,
            self._id_insert_bullet_list,
            self._id_insert_numbered_list,
            self._id_insert_task_list,
            self._id_insert_code_block,
            self._id_insert_footnote,
            self._id_insert_table,
        )
        html_ids = (self._id_insert_html_tag,)
        for item_id in markdown_ids:
            menu_item = menu_bar.FindItemById(item_id)
            if menu_item is not None:
                menu_item.Enable(markdown_ready)
        for item_id in html_ids:
            menu_item = menu_bar.FindItemById(item_id)
            if menu_item is not None:
                menu_item.Enable(html_only)

    def _set_status(self, message: str) -> None:
        self._status_message = message
        self._refresh_statusbar()
        announce(message)

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

    def _statusbar_items(self) -> list[str]:
        allowed = set(STATUS_BAR_ITEMS)
        ordered = [item for item in self.settings.status_bar_order if item in allowed]
        hidden = {item for item in self.settings.status_bar_hidden if item in allowed}
        visible = [item for item in ordered if item not in hidden]
        if not getattr(self.settings, "show_line_numbers", True):
            visible = [item for item in visible if item != "line_column"]
        document = getattr(self, "document", None)
        if document is not None and document.path is not None:
            for item in ("encoding", "line_endings", "file_path"):
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
            return getattr(self, "_status_message", "Ready")
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

    def _confirm_discard_changes(self) -> bool:
        wx = self._wx
        result = self._show_message_box(
            "You have unsaved changes. Close without saving?",
            "Unsaved changes",
            wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
        )
        return result == wx.YES

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
        result = self._show_message_box(
            f"You have unsaved changes. {action_label} without saving?",
            "Unsaved changes",
            wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
        )
        return result == wx.YES

    def _can_close_all_documents(self) -> bool:
        for index in range(len(self._document_tabs) - 1, -1, -1):
            self._select_tab(index)
            if not self._prompt_to_save_active_document("Close"):
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
                    "*.toml;*.xml;*.csv;*.tsv;*.ipynb;*.sqlite;*.db;*.docx;*.epub;*.pdf;*.odt;*.rtf)|"
                    "*.txt;*.md;*.html;"
                    "*.htm;*.xhtml;*.json;*.yaml;*.yml;*.toml;*.xml;*.csv;*.tsv;"
                    "*.ipynb;*.sqlite;*.db;*.docx;*.epub;*.pdf;*.odt;*.rtf|All files (*.*)|*.*"
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
            result = self._show_message_box(
                "This location is not trusted yet. Open file anyway?",
                "Untrusted Location",
                wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
            )
            if result != wx.YES:
                self._set_status("Open cancelled for untrusted location")
                return
            trust_result = self._show_message_box(
                "Trust this folder for future opens?",
                "Untrusted Location",
                wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
            )
            if trust_result == wx.YES:
                self._trusted_locations.add(selected_path.parent.resolve())
                save_trusted_locations(self._trusted_locations)

        structured_extensions = {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".csv",
            ".tsv",
            ".ipynb",
            ".sqlite",
            ".db",
            ".docx",
            ".epub",
            ".pdf",
            ".odt",
            ".rtf",
        }
        if selected_path.suffix.lower() in structured_extensions:
            from quill.io.structured import read_structured_document

            loaded = read_structured_document(selected_path)
        else:
            loaded = read_text_document(selected_path)
        if selected_path.suffix.lower() == ".epub":
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
            self._create_document_tab(loaded, select=True)
            self._load_persistent_undo_state(selected_path, loaded.text)
            self._location_ring = LocationRing()
            self._location_ring.record(0)
        if record_recent:
            self._record_recent(selected_path)
        self._refresh_title()
        self._last_intake_report = build_intake_report(loaded)
        self._set_status(build_intake_summary(loaded))

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
        exit_id = wx.NewIdRef()
        menu.Append(show_id, "Show Quill")
        menu.AppendSeparator()
        menu.Append(exit_id, "Exit Quill")
        menu.Bind(wx.EVT_MENU, lambda _e: self._restore_from_tray(), id=show_id)
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
        self.editor.ChangeValue(restored_text)
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

    def print_preview(self) -> None:
        wx = self._wx
        text = self.editor.GetValue()
        printout1 = self._build_text_printout(self.document.name, text)
        printout2 = self._build_text_printout(self.document.name, text)
        preview = wx.PrintPreview(printout1, printout2, self._print_data)
        if not preview.IsOk():
            self._show_message_box("Print preview failed.", "Print Preview", wx.ICON_ERROR | wx.OK)
            return
        frame = wx.PreviewFrame(preview, self.frame, "Print Preview", size=(700, 500))
        frame.Initialize()
        frame.Show()
        self._set_status("Opened print preview")

    def print_document(self) -> None:
        wx = self._wx
        text = self.editor.GetValue()
        printout = self._build_text_printout(self.document.name, text)
        printer = wx.Printer(wx.PrintDialogData(self._print_data))
        if not printer.Print(self.frame, printout, True):
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

    def open_preferences(self) -> None:
        self.open_profiles_and_features_settings()

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
            result = self._show_message_box(
                f'Binding conflicts with "{conflict}". Reassign anyway?',
                "Keymap Editor",
                wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT,
            )
            if result != wx.YES:
                self._set_status("Keymap edit cancelled")
                return
            self.keymap[conflict] = ""
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
        controls.Add(move_up, 0, wx.RIGHT, 8)
        controls.Add(move_down, 0, wx.RIGHT, 8)
        root.Add(controls, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        root.Add(dialog.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        panel.SetSizer(root)

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

        move_up.Bind(wx.EVT_BUTTON, on_move_up)
        move_down.Bind(wx.EVT_BUTTON, on_move_down)
        chooser.Bind(wx.EVT_CONTEXT_MENU, on_context_menu)

        if self._show_modal_dialog(dialog, "Status Bar Layout") != wx.ID_OK:
            return
        self.settings.status_bar_order = list(item_order)
        self.settings.status_bar_hidden = [
            item for index, item in enumerate(item_order) if not chooser.IsChecked(index)
        ]
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
        self._build_menu()
        self._apply_accelerators()

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

    def show_about_quill(self) -> None:
        wx = self._wx
        info = wx.adv.AboutDialogInfo()
        info.SetName("Quill")
        info.SetVersion(__version__)
        info.SetDescription(
            "Quill 0.1 Beta is a screen-reader-first writing and document environment "
            "for Windows from Blind Information Technology Solutions (BITS) and Community Access."
        )
        info.SetCopyright(
            "Copyright (c) Blind Information Technology Solutions (BITS) and Community Access"
        )
        info.SetDevelopers(
            [
                "Blind Information Technology Solutions (BITS)",
                "Community Access",
            ]
        )
        wx.adv.AboutBox(info)
        self._set_status("Opened About Quill")

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

        with wx.FileDialog(
            self.frame,
            "Choose a source document for Pandoc",
            wildcard=(
                "Pandoc-friendly files "
                "(*.docx;*.md;*.markdown;*.html;*.htm;*.epub;*.odt;*.rst;*.txt)|"
                "*.docx;*.md;*.markdown;*.html;*.htm;*.epub;*.odt;*.rst;*.txt|"
                "All files (*.*)|*.*"
            ),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as file_dialog:
            if self._show_modal_dialog(file_dialog, "Pandoc Conversion Wizard") != wx.ID_OK:
                self._set_status("Pandoc wizard cancelled")
                return
            source_path = Path(file_dialog.GetPath())

        choices = [
            "Open as Markdown in Quill",
            "Open as HTML in Quill",
            "Open as Plain Text in Quill",
        ]
        output_map = {
            choices[0]: "markdown",
            choices[1]: "html",
            choices[2]: "plain",
        }
        with wx.SingleChoiceDialog(
            self.frame,
            (
                "Choose the format Quill should generate for reading, editing, "
                "or GLOW handoff:"
            ),
            "Pandoc Conversion Wizard",
            choices=choices,
        ) as format_dialog:
            if self._show_modal_dialog(format_dialog, "Pandoc Conversion Wizard") != wx.ID_OK:
                self._set_status("Pandoc wizard cancelled")
                return
            selection = format_dialog.GetStringSelection()

        output_kind = output_map[selection]
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
        self.notebook.SetPageText(index, f"Pandoc - {source_path.stem} ({output_kind})")
        self._set_status(f"Opened {source_path.name} as {output_kind} via Pandoc")

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
        clipboard_text = payload["body"]
        self._copy_to_clipboard(clipboard_text)
        webbrowser.open(issue_url)
        self._record_notification("Opened support-hub bug report form", "support")
        self._set_status(
            "Opened bug report form and copied environment summary to clipboard"
        )

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
        payload = build_bug_report_payload(
            current_document=self.document,
            extra_environment={
                "screen_reader": detect_screen_reader().name,
                "wx_version": self._wx.version(),
            },
        )
        issue_url = build_support_issue_url(
            payload,
            source_app="Quill",
            version=__version__,
            platform_label=str(collect_environment_info()["platform"]),
        )
        wx = self._wx
        dialog = wx.Dialog(self.frame, title="Review Bug Report", size=(780, 560))
        panel = wx.Panel(dialog)
        root = wx.BoxSizer(wx.VERTICAL)
        review = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        review.SetValue(
            f"Summary: {payload['summary']}\n\n{payload['body']}\n\nDestination:\n{issue_url}"
        )
        copy_button = wx.Button(panel, label="Copy Summary")
        open_button = wx.Button(panel, id=wx.ID_OK, label="Open Support Form")
        cancel_button = wx.Button(panel, id=wx.ID_CANCEL, label="Cancel")
        copy_button.Bind(wx.EVT_BUTTON, lambda _e: self._copy_to_clipboard(payload["body"]))
        open_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_OK))
        cancel_button.Bind(wx.EVT_BUTTON, lambda _e: dialog.EndModal(wx.ID_CANCEL))
        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Review the support report before Quill opens the Community Access "
                    "support form in your browser."
                ),
            ),
            0,
            wx.ALL | wx.EXPAND,
            8,
        )
        root.Add(review, 1, wx.ALL | wx.EXPAND, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(copy_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(open_button, 0, wx.RIGHT, 6)
        buttons.Add(cancel_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
        if self._show_modal_dialog(dialog, "Review Bug Report") != wx.ID_OK:
            return None
        return payload, issue_url

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
        self.notebook.SetPageText(index, title)

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
        self.notebook.SetPageText(index, preview_title)
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
        self.editor.SetInsertionPoint(insertion_point)
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
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        self.editor.SetFocus()
        self._location_ring.record(target)
        self._set_status(f"Moved to page {page_number}")

    def navigate_back_location(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        target = self._location_ring.back(cursor)
        if target is None:
            self._set_status("No earlier location")
            return
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        self.editor.SetFocus()
        self._set_status("Moved back")

    def navigate_forward_location(self) -> None:
        cursor = self.editor.GetInsertionPoint()
        target = self._location_ring.forward(cursor)
        if target is None:
            self._set_status("No later location")
            return
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
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
        nodes = self._build_outline_navigator_nodes()
        if not nodes:
            self._set_status("No outline headings found")
            return
        selected = self._show_tree_navigator(
            title="Outline Navigator",
            root_label="Headings",
            nodes=nodes,
            open_label="Jump to Heading",
        )
        if not isinstance(selected, OutlineEntry):
            self._set_status("Outline navigation cancelled")
            return
        self._jump_to(selected.position, "Moved to heading")

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

    def _build_outline_navigator_nodes(self) -> list[_NavigatorNode]:
        entries = self._outline_entries()
        if not entries:
            return []
        text = self.editor.GetValue()
        roots: list[_NavigatorNode] = []
        stack: list[tuple[int, _NavigatorNode]] = []
        for index, entry in enumerate(entries):
            end = entries[index + 1].position if index + 1 < len(entries) else len(text)
            preview = text[entry.position:end].strip() or entry.title
            node = _NavigatorNode(
                label=entry.title,
                preview=preview,
                payload=entry,
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
        return [
            _NavigatorNode(
                label=chapter.title,
                preview=f"# {chapter.title}\n\n{chapter.text}\n",
                payload=index,
                children=[],
            )
            for index, chapter in enumerate(book.chapters)
        ]

    def _show_tree_navigator(
        self,
        *,
        title: str,
        root_label: str,
        nodes: list[_NavigatorNode],
        open_label: str,
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
        if buttons is not None:
            ok = buttons.FindWindowById(wx.ID_OK)
            if ok is not None:
                ok.SetLabel(open_label)
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

        def on_select(event: object) -> None:
            nonlocal selected_payload
            item = event.GetItem()
            payload = item_payloads.get(item)
            if payload in node_by_payload:
                selected_payload = payload
                preview.ChangeValue(node_by_payload[payload].preview)
            event.Skip()

        tree.Bind(wx.EVT_TREE_SEL_CHANGED, on_select)
        result = self._show_modal_dialog(dialog, title)
        if result != wx.ID_OK:
            return None
        return selected_payload

    def _jump_to(self, position: int, message: str) -> None:
        self._record_location_before_jump()
        self.editor.SetInsertionPoint(position)
        self.editor.SetSelection(position, position)
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
            "Enter bookmark name:",
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
            self._set_status("No bookmarks available")
            return
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose bookmark:",
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
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        self.editor.SetFocus()
        self._set_status(f'Jumped to bookmark "{name}"')

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
        document_exists = document_path is not None and document_path.exists()
        document_status = "found" if document_exists else "missing"
        if document_path is not None:
            document_line = f"- Document: {document_count} ({document_status}: {document_path})"
        else:
            document_line = (
                f"- Document: {document_count} "
                f"({document_status}: unavailable for unsaved document)"
            )
        personal_status = "found" if personal_path.exists() else "missing"
        project_status = "found" if project_path.exists() else "missing"
        lines = [
            f"Spell-check backend: {backend.name} — {backend.detail}",
            f"Thesaurus data: {thesaurus_status} ({thesaurus_engine.data_path()})",
            "",
            "User dictionary entries:",
            f"- Personal: {personal_count} ({personal_status}: {personal_path})",
            document_line,
            f"- Project: {project_count} ({project_status}: {project_path})",
        ]
        self._show_message_box("\n".join(lines), "Dictionary Status", wx.ICON_INFORMATION | wx.OK)
        self._set_status(
            f"Spell check: {backend.name}; user dictionaries: personal={personal_count}, "
            f"document={document_count}, project={project_count}"
        )

    def open_spell_check_dialog(self) -> None:
        wx = self._wx
        dictionary = self._spell_dictionary()
        misspellings = list_misspellings(self.editor.GetValue(), dictionary)
        if not misspellings:
            self._set_status("No misspellings found")
            return
        choices = []
        for item in misspellings:
            line, column = line_column_for_position(self.editor.GetValue(), item.start)
            choices.append(f"{item.word} (Ln {line}, Col {column})")
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose misspelled word:",
            "Spell Check",
            choices=choices,
        ) as dialog:
            if self._show_modal_dialog(dialog, "Spell Check") != wx.ID_OK:
                return
            selection = dialog.GetSelection()
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

    def next_misspelling(self) -> None:
        dictionary = self._spell_dictionary()
        cursor = self.editor.GetInsertionPoint()
        item = find_next_misspelling(self.editor.GetValue(), cursor, dictionary)
        if item is None:
            self._set_status("No next misspelling")
            return
        self._record_location_before_jump()
        self.editor.SetInsertionPoint(item.start)
        self.editor.SetSelection(item.start, item.end)
        self.editor.SetFocus()
        self._set_status(f'Next misspelling: "{item.word}"')

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
            return
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
            open_label="Open Chapter in Editor",
        )
        if not isinstance(selected, int) or selected < 0 or selected >= len(book.chapters):
            self._set_status("Closed EPUB Navigator")
            return
        chapter = book.chapters[selected]
        chapter_text = f"# {chapter.title}\n\n{chapter.text}\n"
        self._create_document_tab(
            Document(text=chapter_text, path=None, modified=False),
            select=True,
        )
        self.editor.SetInsertionPoint(0)
        self.editor.SetSelection(0, 0)
        self.editor.SetFocus()
        self._refresh_title()
        self._set_status(f'Opened chapter "{chapter.title}" from EPUB navigator')

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
            self._read_aloud.start(
                text,
                start,
                self.settings.read_aloud_voice,
                end=end,
                on_progress=lambda progress_start, progress_end: self._wx.CallAfter(
                    self._on_read_aloud_progress,
                    progress_start,
                    progress_end,
                ),
                on_state_change=lambda next_state: self._wx.CallAfter(
                    self._on_read_aloud_state_change,
                    next_state,
                ),
            )
        except ReadAloudUnavailableError:
            self._show_message_box(
                "Read aloud requires the pyttsx3 backend.",
                "Read Aloud",
                wx.ICON_INFORMATION | wx.OK,
            )
            return
        self._set_status("Read aloud started")

    def stop_read_aloud(self) -> None:
        self._read_aloud.stop()
        self._set_status("Read aloud stopped")

    def choose_read_aloud_voice(self) -> None:
        wx = self._wx
        voices = list_voices()
        if not voices:
            self._show_message_box(
                "No speech voices were found.",
                "Read Aloud Voice",
                wx.ICON_INFORMATION | wx.OK,
            )
            return
        choices = [voice.name for voice in voices]
        current_index = next(
            (
                index
                for index, voice in enumerate(voices)
                if voice.id == self.settings.read_aloud_voice
            ),
            0,
        )
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a read-aloud voice:",
            "Read Aloud Voice",
            choices=choices,
        ) as dialog:
            dialog.SetSelection(current_index)
            if self._show_modal_dialog(dialog, "Read Aloud Voice") != wx.ID_OK:
                self._set_status("Read aloud voice selection cancelled")
                return
            selected = dialog.GetSelection()
        if selected < 0 or selected >= len(voices):
            return
        self.settings.read_aloud_voice = voices[selected].id
        save_settings(self.settings)
        self._set_status(f"Selected read-aloud voice: {voices[selected].name}")

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
            self.editor.SetValue(ocr_result.text)
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
        else:
            self._set_status("Read aloud finished")

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
        if not self._notifications:
            self._show_message_box(
                "No notifications.",
                "Notifications",
                wx.ICON_INFORMATION | wx.OK,
            )
            return
        lines = [
            f"{entry.timestamp} [{entry.category}] {entry.message}"
            for entry in self._notifications[-25:]
        ]
        self._show_message_box(
            "\n".join(lines),
            "Notifications",
            wx.ICON_INFORMATION | wx.OK,
        )
        result = self._show_message_box(
            "Clear all notifications?",
            "Notifications",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Viewed notifications")
            return
        clear_notifications()
        self._notifications = []
        self._set_status("Cleared notifications")

    def check_for_updates(self) -> None:
        wx = self._wx
        from urllib.error import URLError

        self._set_status("Checking for updates...")
        try:
            manifest = fetch_update_manifest(DEFAULT_UPDATE_MANIFEST_URL)
        except (URLError, ValueError) as error:
            self._show_message_box(
                f"Could not verify update manifest: {error}",
                "Check for Updates",
                wx.ICON_ERROR | wx.OK,
            )
            self._set_status("Update check failed")
            self._record_notification("Update check failed", "update")
            return
        if not is_newer_version(__version__, manifest.version):
            self._show_message_box(
                f"You're up to date.\nCurrent: {__version__}\nAvailable: {manifest.version}",
                "Check for Updates",
                wx.ICON_INFORMATION | wx.OK,
            )
            self._set_status("No update available")
            self._record_notification("Update check found no newer version", "update")
            return
        notes = manifest.notes or "(no release notes provided)"
        result = self._show_message_box(
            (
                f"Current version: {__version__}\n"
                f"Available version: {manifest.version}\n\n"
                f"Release notes:\n{notes}\n\n"
                "Open download page now?"
            ),
            "Check for Updates",
            wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Update deferred")
            self._record_notification(f"Update {manifest.version} deferred", "update")
            return
        import webbrowser

        webbrowser.open(manifest.download_url)
        self._set_status(f"Opened download page for {manifest.version}")
        self._record_notification(f"Opened update download for {manifest.version}", "update")

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
        with wx.TextEntryDialog(
            self.frame,
            "Enter text to find:" if not replacement else "Find text:",
            title,
            value=default_query,
        ) as query_dialog:
            if self._show_modal_dialog(query_dialog, title) != wx.ID_OK:
                return None
            query = query_dialog.GetValue()
        if not query:
            return None

        mode_labels = ["Plain text", "Whole word", "Regular expression", "Wildcard"]
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose search mode:",
            title,
            mode_labels,
        ) as mode_dialog:
            mode_dialog.SetSelection(0)
            if self._show_modal_dialog(mode_dialog, title) != wx.ID_OK:
                return None
            mode = mode_dialog.GetStringSelection()

        result = self._show_message_box(
            "Case sensitive search?",
            title,
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        case_sensitive = result == wx.YES
        options = SearchOptions(
            case_sensitive=case_sensitive,
            whole_word=mode == "Whole word",
            use_regex=mode == "Regular expression",
            wildcard=mode == "Wildcard",
        )
        replacement_value: str | None = None
        if replacement:
            with wx.TextEntryDialog(
                self.frame,
                "Replace with:",
                title,
                value="",
            ) as replacement_dialog:
                if self._show_modal_dialog(replacement_dialog, title) != wx.ID_OK:
                    return None
                replacement_value = replacement_dialog.GetValue()
        return query, replacement_value, options

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
        start, end = matches[0]
        for current_start, current_end in matches:
            if current_start >= cursor:
                start, end = current_start, current_end
                break
        self.editor.SetFocus()
        self.editor.SetSelection(start, end)
        self.editor.SetInsertionPoint(end)
        self._last_match = (start, end)
        self._set_status(f"Found at position {start + 1}")

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
            if chosen is None:
                chosen = matches[-1]
                wrapped = True
        else:
            for start, end in matches:
                if start >= cursor:
                    chosen = (start, end)
                    break
            if chosen is None:
                chosen = matches[0]
                wrapped = True

        if chosen is None:
            self._set_status("No matches found")
            return

        start, end = chosen
        self.editor.SetFocus()
        self.editor.SetSelection(start, end)
        self.editor.SetInsertionPoint(end)
        self._last_match = chosen
        direction = "previous" if reverse else "next"
        wrap_suffix = " (wrapped)" if wrapped else ""
        self._set_status(f"Found {direction} at position {start + 1}{wrap_suffix}")

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
        preview_lines = []
        for index, (start, end) in enumerate(matches[:10], start=1):
            line_text = text[start:end]
            preview_lines.append(f"{index}. {line_text}")
        preview = "\n".join(preview_lines)
        result = self._show_message_box(
            f"Apply {len(matches)} replacement(s)?\n\nPreview:\n{preview}",
            "Replace All",
            wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
        )
        if result != wx.YES:
            self._set_status("Replace cancelled")
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
        self.editor.SetValue(updated_text)
        self.document.set_text(updated_text)
        self._set_status(f"Replaced {replacements} occurrence(s)")

    def insert_link(self) -> None:
        wx = self._wx
        selected_text = self.editor.GetStringSelection()
        with wx.TextEntryDialog(
            self.frame,
            "Enter URL:",
            "Insert Link",
            value="https://",
        ) as url_dialog:
            if self._show_modal_dialog(url_dialog, "Insert Link") != wx.ID_OK:
                return
            url = url_dialog.GetValue().strip()
        if not url:
            self._set_status("Insert link cancelled")
            return

        with wx.TextEntryDialog(
            self.frame,
            "Display text:",
            "Insert Link",
            value=selected_text or "",
        ) as text_dialog:
            if self._show_modal_dialog(text_dialog, "Insert Link") != wx.ID_OK:
                return
            display_text = text_dialog.GetValue()

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
        self._set_status(f"Mark set at line {line}, column {column}")

    def pop_mark(self) -> None:
        mark = self._mark_ring.pop_mark()
        if mark is None:
            self._set_status("No marks in ring")
            return
        self.editor.SetInsertionPoint(mark)
        self.editor.SetSelection(mark, mark)
        line, column = line_column_for_position(self.editor.GetValue(), mark)
        self._set_status(f"Popped to mark at line {line}, column {column}")

    def exchange_point_and_mark(self) -> None:
        current = self.editor.GetInsertionPoint()
        target = self._mark_ring.exchange_point_and_mark(current)
        if target is None:
            self._set_status("No marks in ring")
            return
        self.editor.SetInsertionPoint(target)
        self.editor.SetSelection(target, target)
        line, column = line_column_for_position(self.editor.GetValue(), target)
        self._set_status(f"Exchanged point and mark to line {line}, column {column}")

    def list_marks(self) -> None:
        wx = self._wx
        marks = self._mark_ring.list_marks()
        if not marks:
            self._set_status("No marks in ring")
            return
        lines: list[str] = []
        text = self.editor.GetValue()
        for index, position in enumerate(reversed(marks), start=1):
            line, column = line_column_for_position(text, position)
            lines.append(f"{index}. Line {line}, Column {column}")
        self._show_message_box("\n".join(lines), "Mark Ring", wx.ICON_INFORMATION | wx.OK)
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

    def format_indent(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: indent_lines(text, start, end),
            "Indented lines",
        )

    def format_outdent(self) -> None:
        self._apply_selection_operation(
            lambda text, start, end: outdent_lines(text, start, end),
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
            lambda text: convert_indentation_to_spaces(text, 4),
            "Converted indentation to spaces",
        )

    def convert_indentation_to_tabs(self) -> None:
        self._apply_text_block_operation(
            lambda text: convert_indentation_to_tabs(text, 4),
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
        with wx.TextEntryDialog(
            self.frame,
            "Enter number of columns (1-12):",
            "Insert Table",
            value="2",
        ) as columns_dialog:
            if self._show_modal_dialog(columns_dialog, "Insert Table") != wx.ID_OK:
                return None
            columns_raw = columns_dialog.GetValue().strip()
        with wx.TextEntryDialog(
            self.frame,
            "Enter number of rows (1-50):",
            "Insert Table",
            value="2",
        ) as rows_dialog:
            if self._show_modal_dialog(rows_dialog, "Insert Table") != wx.ID_OK:
                return None
            rows_raw = rows_dialog.GetValue().strip()
        with wx.MessageDialog(
            self.frame,
            "Include a header row?",
            "Insert Table",
            wx.YES_NO | wx.ICON_QUESTION,
        ) as header_dialog:
            include_header = self._show_modal_dialog(header_dialog, "Insert Table") == wx.ID_YES

        try:
            columns = int(columns_raw)
            rows = int(rows_raw)
        except ValueError:
            self._show_message_box(
                "Rows and columns must be whole numbers.",
                "Insert Table",
                wx.ICON_ERROR | wx.OK,
            )
            return None
        if columns < 1 or columns > 12:
            self._show_message_box(
                "Columns must be between 1 and 12.",
                "Insert Table",
                wx.ICON_ERROR | wx.OK,
            )
            return None
        if rows < 1 or rows > 50:
            self._show_message_box(
                "Rows must be between 1 and 50.",
                "Insert Table",
                wx.ICON_ERROR | wx.OK,
            )
            return None
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
        start, end = self.editor.GetSelection()
        if start != end:
            original = self.editor.GetRange(start, end)
            updated = transform(original)
            self.editor.Replace(start, end, updated)
            self.editor.SetSelection(start, start + len(updated))
            self._set_status(f"{label} applied to selection")
            return

        original_document = self.editor.GetValue()
        updated_document = transform(original_document)
        self.editor.SetValue(updated_document)
        self.document.set_text(updated_document)
        self._set_status(f"{label} applied to document")

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
        self.editor.SetValue(updated)
        self.document.set_text(updated)
        if new_start == new_end:
            self.editor.SetInsertionPoint(new_start)
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
        self.editor.SetValue(updated)
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
        self.editor.SetValue(updated)
        self.document.set_text(updated)
        self.editor.SetInsertionPoint(new_cursor)
        self._set_status(status)

    def insert_html_tag(self) -> None:
        if not self._feature_enabled("core.format"):
            self._set_status("HTML tag tools are unavailable in this profile")
            return
        wx = self._wx
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose an HTML tag:",
            "Insert HTML Tag",
            choices=HTML_TAG_CHOICES,
        ) as tag_dialog:
            if self._show_modal_dialog(tag_dialog, "Insert HTML Tag") != wx.ID_OK:
                return
            tag = tag_dialog.GetStringSelection()

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
        wx = self._wx
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose a markdown tag/snippet:",
            "Insert Markdown Tag",
            choices=MARKDOWN_TAG_CHOICES,
        ) as kind_dialog:
            if self._show_modal_dialog(kind_dialog, "Insert Markdown Tag") != wx.ID_OK:
                return
            kind = kind_dialog.GetStringSelection()

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

    def switch_feature_profile(self) -> None:
        wx = self._wx
        choices = [profile.name for profile in PROFILE_DEFINITIONS.values()]
        profile_ids = list(PROFILE_DEFINITIONS.keys())
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
        target_profile_id = profile_ids[selection]
        if target_profile_id == self.features.active_profile_id:
            self._set_status(f"Already using {self.features.active_profile.name}")
            return
        preview = self.features.change_profile_preview(target_profile_id)
        with wx.MessageDialog(
            self.frame,
            preview + "\n\nSwitch profiles now?",
            "Switch Feature Profile",
            wx.YES_NO | wx.ICON_QUESTION,
        ) as confirm_dialog:
            if self._show_modal_dialog(confirm_dialog, "Switch Feature Profile") != wx.ID_YES:
                self._set_status("Profile switch cancelled")
                return
        self.features.switch_profile(target_profile_id)
        profile = self.features.active_profile
        self._set_status(f"Profile changed to {profile.name}. Undo available.")
        self._show_message_box(
            self.features.profile_summary(), "Feature Profile", wx.ICON_INFORMATION | wx.OK
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
        profiles = list(PROFILE_DEFINITIONS.values())
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
        chooser = wx.ListBox(panel, choices=[profile.name for profile in profiles])
        current_index = 0
        for index, profile in enumerate(profiles):
            if profile.id == self.features.active_profile_id:
                current_index = index
                break
        chooser.SetSelection(current_index)
        summary = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        keyboard_pack_choices = keyboard_pack_names(include_custom=True)
        keyboard_pack_choice = wx.Choice(panel, choices=keyboard_pack_choices)
        current_pack = self.settings.keyboard_pack
        if current_pack not in keyboard_pack_choices:
            current_pack = KEYBOARD_PACK_DEFAULT
        keyboard_pack_choice.SetStringSelection(current_pack)
        keyboard_preview = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 160),
        )

        def refresh_summary() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                summary.SetValue(self.features.profile_summary())
                return
            profile = profiles[selection]
            summary.SetValue(self.features.change_profile_preview(profile.id))

        def refresh_keyboard_preview() -> None:
            pack_name = keyboard_pack_choice.GetStringSelection() or KEYBOARD_PACK_DEFAULT
            description = keyboard_pack_description(pack_name)
            preview = keyboard_pack_preview(pack_name)
            if preview == description:
                keyboard_preview.SetValue(description)
                return
            keyboard_preview.SetValue(preview)

        def switch_selected() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            profile = profiles[selection]
            if profile.id == self.features.active_profile_id:
                self._set_status(f"Already using {profile.name}")
                return
            self.features.switch_profile(profile.id)
            refresh_summary()
            self._set_status(f"Profile changed to {profile.name}. Undo available.")
            self._refresh_title()

        def compare_selected() -> None:
            selection = chooser.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            profile = profiles[selection]
            message = self.features.compare_profiles(self.features.active_profile_id, profile.id)
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
            chooser.SetSelection(0)
            refresh_summary()
            self._set_status("Reset to Essential profile")
            self._refresh_title()

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
            current_index = 0
            for index, profile in enumerate(profiles):
                if profile.id == self.features.active_profile_id:
                    current_index = index
                    break
            chooser.SetSelection(current_index)
            refresh_summary()
            self._set_status(f"Imported profile data from {source.name}")
            self._refresh_title()

        chooser.Bind(wx.EVT_LISTBOX, lambda _e: refresh_summary())
        keyboard_pack_choice.Bind(wx.EVT_CHOICE, lambda _e: refresh_keyboard_preview())
        switch_button = wx.Button(panel, label="Switch Profile")
        compare_button = wx.Button(panel, label="Compare Profiles")
        undo_button = wx.Button(panel, label="Undo Last Change")
        reset_button = wx.Button(panel, label="Reset to Essential")
        export_button = wx.Button(panel, label="Export...")
        import_button = wx.Button(panel, label="Import...")
        apply_pack_button = wx.Button(panel, label="Apply Keyboard Pack")
        reset_pack_button = wx.Button(panel, label="Reset Keyboard Pack")
        customize_pack_button = wx.Button(panel, label="Customize Shortcuts...")
        close_button = wx.Button(panel, id=wx.ID_OK, label="Close")
        switch_button.Bind(wx.EVT_BUTTON, lambda _e: switch_selected())
        compare_button.Bind(wx.EVT_BUTTON, lambda _e: compare_selected())
        undo_button.Bind(wx.EVT_BUTTON, lambda _e: undo_change())
        reset_button.Bind(wx.EVT_BUTTON, lambda _e: reset_essential())
        export_button.Bind(wx.EVT_BUTTON, lambda _e: export_profile())
        import_button.Bind(wx.EVT_BUTTON, lambda _e: import_profile())
        apply_pack_button.Bind(wx.EVT_BUTTON, lambda _e: apply_selected_keyboard_pack())
        reset_pack_button.Bind(wx.EVT_BUTTON, lambda _e: reset_keyboard_pack())
        customize_pack_button.Bind(wx.EVT_BUTTON, lambda _e: customize_keymap())
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
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(switch_button, 0, wx.RIGHT, 6)
        buttons.Add(compare_button, 0, wx.RIGHT, 6)
        buttons.Add(undo_button, 0, wx.RIGHT, 6)
        buttons.Add(reset_button, 0, wx.RIGHT, 6)
        buttons.Add(export_button, 0, wx.RIGHT, 6)
        buttons.Add(import_button, 0, wx.RIGHT, 6)
        buttons.AddStretchSpacer(1)
        buttons.Add(apply_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(reset_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(customize_pack_button, 0, wx.RIGHT, 6)
        buttons.Add(close_button, 0)
        root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)
        panel.SetSizer(root)
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

    def run_profile_onboarding(self) -> None:
        self._show_profile_onboarding(force=True)

    def _maybe_run_first_run_onboarding(self) -> None:
        if not getattr(self, "_first_run_profile_prompt", False):
            return
        self._show_profile_onboarding(force=False)
        self._first_run_profile_prompt = False

    def _show_profile_onboarding(self, force: bool) -> None:
        wx = self._wx
        profiles = list(PROFILE_DEFINITIONS.values())
        with wx.SingleChoiceDialog(
            self.frame,
            "Choose how Quill should start:",
            "Profile Onboarding",
            choices=[profile.name for profile in profiles],
        ) as dialog:
            if self._show_modal_dialog(dialog, "Profile Onboarding") != wx.ID_OK:
                if force:
                    self._set_status("Profile onboarding skipped")
                return
            selection = dialog.GetSelection()
        if selection == wx.NOT_FOUND:
            return
        profile = profiles[selection]
        self.features.switch_profile(profile.id)
        self._set_status(f"Quill starts in the {profile.name} profile")
        self._refresh_title()

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


def run_app(startup_paths: list[Path] | None = None, safe_mode: bool = False) -> None:
    import wx

    app = wx.App(False)
    frame = MainFrame(safe_mode=safe_mode)
    for path in startup_paths or []:
        if path.exists() and path.is_file():
            frame.open_file(path)
    frame.show()
    app.MainLoop()
