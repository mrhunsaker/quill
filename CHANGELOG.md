# Changelog

## Security Hardening and UX Delight (1.0 Release Pass)

This section records the 13 HIGH-severity security fixes, 16 UX delight features, and the LOW/NIT fixes applied during the pre-1.0 code review. All items below were open in `issues.md` before this pass and are now closed.

### HIGH security and reliability fixes (all 13 closed)

- **H-SAFE-1 / H-1-tests — Safe Mode now enforced in all load-bearing paths.** `--safe-mode` / `QUILL_SAFE_MODE=1` disables AI responses, the watch folder, and Quillin contributions. Covered by `test_safe_mode_blocks_assistant_network_calls`.
- **H-1 — Subprocess args no longer logged in full.** `redaction.py::format_args_for_log` redacts every argument; only the executable basename and arg count are preserved. Covered by `test_run_subprocess_safely_does_not_log_secrets`.
- **H-2 — Crash bundle redacts secrets before shipping.** `build_diagnostic_bundle` runs `redact_text_for_bundle_with_stats` on every text file. Covered by `test_diagnostic_bundle_redacts_secrets_and_paths`.
- **H-3 — `recent_commands` sanitized before embedding in diagnostic bundle.** `filter_recent_commands` validates every item against the command-id grammar and drops anything invalid.
- **H-4-core — `recovery.py` state mutations serialized.** `begin_session`, `mark_clean_exit`, and `_record_offer_outcome` are now protected by a `threading.RLock` (in-process) and `msvcrt.locking` / `fcntl.flock` (cross-process). Covered by `test_concurrent_begin_session_serialize_via_lock`.
- **H-1-core — `QUILL_DATA_DIR` gated on `_DEV_BUILD`.** Release builds ignore the env var entirely. Dev builds additionally require the path to be under `Path.home()`. Covered by `tests/unit/core/test_paths.py` (4 tests).
- **H-2-core — External engine executable allowlist.** `configure_engine` and `probe_engine` validate the executable basename against `_ENGINE_EXECUTABLE_BASENAMES` before any I/O. Covered by `test_configure_engine_rejects_unallowed_executable` and `test_probe_engine_rejects_unallowed_executable`.
- **H-3-core — SSH uses `RejectPolicy` by default.** `paramiko.AutoAddPolicy` is only available when `trust_first_use=True` is passed explicitly. System host keys are always loaded first. Covered by 4 tests in `test_ssh_client.py`.
- **H-4-core-2 — IPC queue append serialized in-process.** `enqueue_open_request` acquires a module-level `threading.Lock` before opening the JSONL file. Covered by `test_concurrent_enqueue_serializes_via_lock`.
- **H-1-ui / H-2-ui — Quillin consent and remove-confirm dialogs use the modal contract.** Both `quillin_consent` and `on_remove` now route through `_show_modal_dialog` + `apply_modal_ids`. Covered by `test_quillin_consent_uses_modal_contract` and `test_on_remove_uses_modal_contract`.
- **H-3-ui — Watch Queue Monitor properly cleaned up on close.** `_on_close` explicitly destroys the monitor dialog and clears all references before the watch service stops.
- **H-1-platform / H-2-platform — `pyttsx3` engine is a process-wide singleton.** Initialization happens once; a `_pyttsx3_engine_failed` gate prevents repeated failure. `reset_pyttsx3_engine_for_tests()` helper added for test isolation.
- **H-3-platform — `Windows.Media.Ocr` import wrapped.** `winsdk` imports are wrapped in `try/except ImportError`; `_WINSDK_AVAILABLE` flag prevents crashes on non-Windows builds. Covered by `test_module_imports_without_winsdk`.
- **H-4-platform — macOS VoiceOver errors now logged.** The `except Exception: pass` branch is now `logger.warning(...)`. Covered by `test_macos_announce_error_logged`.

### Magic / UX delight (all 16 closed — §8)

- **Key cheatsheet (`Alt+Shift+/`).** `open_key_cheatsheet()` opens a searchable dialog listing every command and its keybinding.
- **Go to anything (`Ctrl+Shift+Grave, G`).** `GoToAnythingDialog` in `quill/ui/palette.py` searches commands (`>` prefix) and headings (`#` prefix). Activating a heading calls `go_to_line_number(lineno)` on `MainFrame`.
- **Earcons.** `_play_quill_sound()` fires at mode-entry transitions, queued separately from TTS so it does not interrupt screen-reader output.
- **"Why Don't I See a Feature?" (`Alt+F1`).** `explain_unavailable_feature()` announces the reason a command is unavailable.
- **Live contrast checker (`Ctrl+Shift+Grave, Shift+C`).** `announce_contrast_ratio()` computes the WCAG 2.1 relative-luminance ratio for the current theme and announces it. Also fires automatically after `_apply_theme()`.
- **Magic Paste (`Ctrl+Alt+V`).** `magic_paste()` inspects the clipboard for a URL, Markdown block, or base64 image and presents a picker before inserting.
- **Recovery diff UX.** `_offer_crash_recovery()` now includes a 30-line read-only snapshot preview so users can review content before deciding to restore.
- **Status bar context help (`Alt+H`).** `show_context_help()` announces the most useful keys for the current mode in priority order.
- **Soft error recovery link.** `_show_error_with_hint()` is used for file-open, export, and import errors. A "What to try next..." toggle reveals a `wx.TE_READONLY` area with contextual guidance.
- **TTS fallback announcement.** `_check_tts_fallback_on_startup()` fires at startup and announces "Screen reader fallback active. F8 to retry TTS." when `pyttsx3` could not be initialised. `retry_tts_init()` exposed in `prism_bridge.py`.
- **Recovery `had_replacements` note.** `read_recovery_snapshot()` returns `(text, had_replacements)`; the recovery dialog shows a warning when replacement characters are detected.
- **Annisuggestion.** `top_suggestion()` in `quill/core/palette.py` surfaces the most-used recent command (≥3 uses, within 1 hour) as a `suggestion` status-bar cell. Activating the cell runs the command.
- **Crash-recovery loop fix (M-28).** `RecoveryOffer.dismissal_count` adapts the dialog text and relabels the skip button "Discard and Continue" after 3 dismissals.
- **File-context summary (`Alt+I`).** `show_document_summary()` announces word count, line count, heading count, last-saved time, and recovery snapshot presence.
- **A11Y live indicator.** `"sr_name"` status-bar cell shows which screen reader is detected, populated by `detect_screen_reader()` from `sr_detect.py`.
- **"Resume from where I left off".** Caret position is saved per autosave cycle (`save_cursor_position()` in `recovery.py`) and per workspace snapshot (`caret_positions_from_session()` in `sessions.py`). Both are restored on next open.

### LOW and NIT fixes (§6 and §7 continued)

- **L-2** — `core/lexical.py`: added `logger.debug("Lexical provider %s failed: %s", ...)` inside the broad `except` so provider regressions surface in diagnostic logs.
- **L-3** — `core/ai/assistant.py`: added `logger.warning(...)` inside the Foundation Models backend probe `except` so probe failures appear in the diagnostic bundle.
- **L-4** — `core/lexical_preload.py`: added `logger.debug(...)` inside the preload `except` so non-fatal warm-up failures are visible in debug logs.
- **L-6** — `core/watch_queue.py`: documented why `threading.RLock` is required (`_dequeue_item` re-enters `_try_flush` under the same lock; plain `Lock` would deadlock).
- **L-14** — `tools/check_banned_patterns.py`: enriched the unregistered-dialog-surface violation message to hint that stock `wx` dialogs should be added to `_NATIVE_WX_DIALOGS` in `dialog_inventory.py`.
- **L-16 / N-5** — `tools/ui_surface.py`: wrapped the bare `next(...)` call in `try/except StopIteration` and raised `SystemExit` with a clear message when `MainFrame` cannot be found (e.g. after a rename).
- **M-27** — `pyproject.toml`: added `"Operating System :: MacOS"` classifier to match the documented macOS support.
- **L-1** — `core/paths.py`: on Windows, missing `APPDATA` now raises `RuntimeError` with a clear message instead of silently falling back to the hidden `~/.quill` directory. Non-Windows still uses `~/.quill` as before. New test `test_windows_raises_when_appdata_missing` locks this in.
- **L-7** — `core/glow.py`: narrowed the `ImportError`-only case in `_load_glow_core`; all other broad `except Exception` sites in the GLOW backend now log `logger.warning(...)` before returning the safe fallback.
- **L-10** — `io/ocr.py`: narrowed `except Exception` to `except ImportError` in `_import_windows_ocr` so non-import errors are not silently swallowed.
- **L-21** — `stability/*.py`: all stability modules already carry `Implements: ROADMAP ...` docstrings — confirmed and closed.
- **L-22** — `tests/unit/tools/test_bundled_quillin_lint.py`: added `test_bad_quillin_fixture_is_rejected` negative test with a `fixtures/bad_quillin/manifest.json` that fails schema validation (missing `id`, invalid `version`).
- **N-10** — `dialogs.md`: safe mode flag already referenced at lines 280-305 — confirmed and closed.
- **N-3** — `stability/crash_report.py`: bundle filename now uses ISO-8601 (`YYYYMMDDTHHMMSSZ`) instead of a raw 19-digit nanosecond epoch, making bundles human-inspectable in Explorer and sorted correctly by name.
- **L-11** — `io/structured.py`: duplicate of M-11 (low because there is an existing fallback); closed as a reference item — will be addressed with M-11.

- **L-8** — `updates.py`: removed unnecessary `getattr` guard around `response.headers.get("Content-Length")`.
- **L-12** — `safe_mode.py`: deleted unused `safe_mode_message()` export.
- **L-15** — `network_egress_audit.py`: duplicate egress-site key now raises `ValueError` at scan time so no new egress site can be silently dropped.
- **N-1** — `stability/__init__.py`: re-exported `build_diagnostic_bundle`, `configure_logging`, and `run_subprocess_safely` for ergonomic call sites.
- **N-4** — `module_size_budgets.json`: `_comment` / `_rebaseline_*` keys are now stripped before the budget map is read.
- **N-7** — `quillin_lint.py`: `_JSON_TYPES` is now `types.MappingProxyType({...})` for immutability.
- **N-8** — `dialog_button_contract.py`: `_FLAG_TO_ID` reverse-lookup dict used by `_collect_button_ids`; `# noqa: dialog_button_contract` opt-out added.
- **N-9** — `feature_contracts.py`: `requires_timeout: bool | None = None` moved to end of dataclass for default-value ordering.
- **N-11** — `external_engine.py`: `configure_engine` docstring documents POSIX-style shell-command format and `shlex.split` semantics.
- **N-12** — `recovery.py`: `_validate_session_id()` helper replaces three `UUID(session_id)` side-effect calls.
- **N-15** — `dictation.py`: `try/except ImportError` block carries explicit Windows-only intent comment.
- **N-16** — `announcements.py`: `format_progress` docstring states its pure-function, no-I/O, thread-safe contract.
- **M-1** — `core/watch_actions.py`: added `_humanize_action_error(action_id, error)` and routed the 8 broad `except Exception` sites (`OpenAction`, `MoveAction`, `CopyAction`, `ConvertAction`, `RunMacroAction`, `RunPythonTransformAction`, `AiAction`, `OcrAction`) plus the registry's last-resort guard through it. Screen-reader users now get plain-English messages such as `"Quill cannot complete the move. The folder is read-only or you lack permission — choose a folder you own."` instead of `"[Errno 13] Permission denied: 'C:\\…'"`. Coverage: `test_humanize_permission_error_is_actionable`, `test_humanize_file_not_found_mentions_reappear`, `test_humanize_generic_oserror_keeps_strerror`, `test_humanize_unrecognized_error_falls_back_to_str`, `test_move_action_permission_error_humanized`. Budget re-baselined (+57 lines).

---

## QUILL Brand Identity

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

## Cross-platform support and on-device AI

- **macOS support.** Quill now runs on macOS as well as Windows from one codebase. Announcements route to VoiceOver (never speaking over it); release Mac builds are code-signed with a Developer ID certificate and notarized by Apple.
- **Ask Quill chat.** An on-device AI chat rendered as a fully accessible WebView document — heading-navigable turns, announced replies, an in-page message box, and Escape to close. Verified in NVDA, JAWS, and VoiceOver.
- **On-device AI, no cloud required.** Apple Foundation Models on macOS; llama.cpp (CPU, GGUF) on Windows/Linux; optional Ollama (local/cloud) or a custom endpoint. The assistant answers in chat by default and never edits a document without approval.
- **Train Writing Style** conditions the assistant on your own writing.
- **Accessible WebView library.** The chat, preview, About box, and update/consent dialogs are built on the open-source `wx-accessible-webview` library (extracted from Quill).

## AI reliability and clarity (highlights)

- **Clearer AI connection messages.** Quill now tells the difference between a rejected API key ("Authentication failed. Check your API key.") and a valid key that lacks access to a model or region ("Access denied..."), and reports rate limiting, warm-up, and local-server-not-running states in plain language.
- **Warm-up retry.** When a model is still loading, Quill briefly retries before reporting it as warming up, instead of failing the first attempt.
- **No false 403s.** Connection status is matched on real HTTP status codes, so host ports like `localhost:11403` are never mistaken for an error.
- **Smarter quick writing actions.** Rewrite, Summarize, Continue Writing, and Fix Grammar now work with or without a selection, fall back to a sensible scope (paragraph or whole document), and announce the scope and word count.
- **AI-off guard everywhere.** The quick writing actions respect the AI-enabled setting from any entry point, including the command palette and keybindings.
- **Portable key recovery.** If a saved API key cannot be unlocked on the current device, the AI status line prompts you to re-enter it instead of showing a confusing authentication error.

## Quill 0.1.5 Beta

Quill 0.1.5 Beta focuses on safe rollout surfaces for BITS Whisperer, clearer preference parity, and more accessible status monitoring without changing core editor behavior.

### Added and improved in 0.1.5

- Added QUILL Quick Nav browse-style mode with `Ctrl+Shift+Grave`, cursor-only movement, and explicit non-editing behavior while active.
- Added mnemonic Quick Nav movement for links, lists, list items, tables, block quotes, bookmarks, code blocks, table of contents, headings, heading levels 1 through 6, paragraphs, sentences, and blocks, with `Shift` reversing direction where applicable.
- Added configurable Quick Nav wrap behavior and configurable Quick Nav feedback mode (`speech`, `sound`, `both`, `none`).
- Added document-surface-aware Quick Nav indexing for Markdown and HTML, including heading parsing, Markdown and HTML list-item anchors, paragraph anchors, and sentence anchors.
- Added Quick Nav cache invalidation on document edits, full-text replacement operations, and tab switches to preserve performance and correctness.
- Added BITS Whisperer provider onboarding, readiness checks, capability matrix, and guarded download queue controls.
- Added live Help status-page updates with quieter refresh announcements that only speak when tracked values change.
- Added Preferences controls for AI enable state, BITS Whisperer safe mode lock, auto-open status behavior, and refresh cadence.
- Added rollout-safe diagnostics snapshots and startup onboarding for BW setup defaults.
- Enabled Ruff markdown preview formatting so release docs can stay formatted consistently.
- Added robust command-line options, including `--help`, `--version`, startup cursor targeting (`--line`, `--column`), `--new-window`, and `--wait`.

## Quill 0.1.2 Beta

Quill 0.1.2 Beta expands Quill's writing flow with prediction, snippets, in-app preview, local assistant workflows, and packaging/onboarding polish.

### Added and improved in 0.1.2

- Added **Word Prediction** with `Ctrl+Space`, including document-word, HTML tag, and Markdown tag suggestions.
- Moved **Insert Snippet** to `Ctrl+Alt+Space` and **Manage Snippets** to `Ctrl+Alt+Shift+Space` so snippet insertion no longer clashes with prediction.
- Added a **Word Prediction as you type** preference and View-menu toggle.
- Added **In-App Preview** and **Side-by-Side Preview** with keyboard-first focus movement.
- Added a local **Writing Assistant** menu surface with rewrite/summarize/continue/grammar quick actions and ranked command suggestions.
- Added a sandboxed **Run Python** transform tool for document/selection automation.
- Added first-run **Writing Assistant onboarding** plus **Preferences -> AI Connection** for provider, host, and model setup.
- Added secure optional API-key storage for AI endpoints using **Windows DPAPI**.
- Added AI provider support for **Ollama Cloud (API key)** and improved custom-endpoint handling.
- Added explicit **Ollama Cloud onboarding** guidance in AI Connection, including note that free personal-use access is available with lower usage limits.
- Added **Verify Connection**, **List Models**, and **Recommend Model** actions in AI connection settings.
- Added automatic AI-connection verification on save and an AI-menu status flow with **Ready / Needs attention / Not checked**.
- Added an AI-menu detail line with short verification reason text.
- Improved screen-reader behavior by announcing plain-language AI verification outcomes immediately.
- Improved Ask Quill chat accessibility by announcing incoming responses/proposals/errors as they arrive.
- Updated Windows packaging to stage an assistant setup guide and expose an optional `aiassistant` installer component.
- Added custom profile management with opt-in inheritance from a parent built-in profile or an explicit bare-bones start.
- Added profile quick picker hotkey **Alt+Shift+P** (`help.switch_feature_profile`).
- Updated profile switching so custom profiles can carry feature states, settings, and keymap bindings together.
- Added Markdown list editing flow updates: `Enter` continues list items, `Enter` on an empty marker exits the list, and `Tab`/`Shift+Tab` nest or promote list items.
- Added a **List Manager** (`Ctrl+Alt+L`) under Format -> List for tree-based list restructuring (move, promote/demote, add, edit, delete).
- Added structured **PowerPoint (.pptx) import** with slide titles as headings, bullet levels as nested lists, table extraction, and speaker-note extraction.
- Added **Style Headings...** under Insert -> Heading to apply font family, size, and alignment to current-level or all headings in Markdown/HTML.
- Added **Heading Organizer** (`Ctrl+Alt+Shift+H`) for keyboard-first heading promotion/demotion, section reordering, heading renaming, and accessibility validation before apply.
- Added release-safety fallback for beta testing: Word (`.doc`, `.docx`) and CSV/TSV now open in the standard plain-text editing surface by default.
- Kept structured Word and CSV grid implementations in-repo behind an internal gate for continued verification.
- Added **Watch Folder automation** under **Tools -> Dictation** to monitor a folder and auto-open newly detected supported files.
- Added **Watch Folder Settings** and **Watch Folder Status** commands for path, subfolder, startup, and polling control.
- Added **Watch Folder onboarding** to Startup Wizard and first-run setup flow.
- Removed duplicate path reporting by hiding the status-bar file path item when full path is already shown in the title bar.
- Fixed intermittent unit-test file-locking in UI navigation tests by isolating `QUILL_DATA_DIR` per test.
- Expanded docs and release notes for the complete 0.1.2 feature set.

## Quill 0.1.1 Beta

Quill 0.1.1 Beta advances the 0.1 baseline with update-path hardening, status-bar parity completion, menu/discoverability polish, and documentation alignment.

### Added and improved in 0.1.1

- Completed status-bar interaction parity: focused cell context actions now include **Activate**, **Hide this item**, and **Status bar settings**.
- Added **Restore Defaults** to Status Bar Settings and persisted layout changes.
- Hardened **Help -> Check for Updates...** with guided installer handoff, including close-now support for clean setup.
- Simplified the Search menu to a single **Replace...** entry; replace-all now lives in the Replace dialog and keeps the existing replace-all hotkey path.
- Clarified naming and discoverability around **Workspace Snapshots**, **Recent Marks (Ring)**, and status-bar terminology.
- Expanded regression coverage for search/extend-selection and no-selection transform behavior.
- Added About-dialog acknowledgments for contributors and beta testers.
- Added a full snippets workflow: searchable insert (`Ctrl+Space`), manage (`Ctrl+Alt+Space`), placeholder prompts, trigger expansion, and starter packs.
- Regenerated the signed update feed for `0.1.1`.

## Quill 0.1.0 Beta

Quill 0.1 Beta is the first broad, coherent release of Quill as a screen-reader-first writing, reading, review, and document-intelligence environment for Windows from Blind Information Technology Solutions (BITS) and Community Access.

### Highlights

- Native wxPython editor shell with command palette, tabs, menus, and interactive status bar
- Plain text, Markdown, HTML, EPUB, PDF, DOCX, ODT, RTF, JSON, XML, TOML, CSV, TSV, notebook, and SQLite reading surfaces
- Deterministic GLOW audit and fix workflows inside Quill for plain text, Markdown, and HTML
- Guided optional-tool onboarding for Pandoc, Tesseract OCR, LibreOffice, Ghostscript, HTML Tidy, XML Lint, and PyMarkdown
- Pandoc Conversion Wizard for opening supported source files as Markdown, HTML, or plain text tabs
- In-app diagnostics review before export and in-app bug-report review before launching the Community Access support form
- Autosave, backups, recovery, persistent undo, trusted locations, notifications, and signed update checks
- Windows packaging flow with embedded Python, portable bundle generation, and Inno Setup installer compilation

### What feels new in this release

The Help menu now acts like a real support surface instead of a dead end. Users can review diagnostics before Quill writes a zip, review a bug report before Quill opens the browser, and route support feedback into the shared Community Access support flow with more confidence and less guesswork.

Quill also now has a more practical format-bridge story. With Pandoc available, documents can move into stable text-centric workflows without pushing users into command-line tooling. The external-tools dialog explains what each helper unlocks and keeps the setup story transparent.

### Evening polish updates

- File > Sessions was clarified as **workspace snapshots** with clearer menu labels for saving, opening, recent snapshots, and current workspace documents.
- Mark Ring and Bookmarks language was clarified in-app to distinguish temporary jump points (mark ring) from named jump points (bookmarks).
- Tools menu information architecture was simplified into clear submenus: Writing and Language, Read Aloud, Integrations, Document Intake, Authoring and Automation, Compare Documents, Accessibility, Support, and Customize.
- Added a menu binding contract test so menu IDs and EVT_MENU handlers stay aligned as menus evolve.
- Completed status-bar parity details: focused cell context menu now offers Activate, Hide this item, and Status bar settings.
- Status Bar Settings now includes Restore Defaults and persists layout changes immediately.
- Help -> Check for Updates now includes a guided installer handoff that can close Quill before running setup.
- Version bumped to 0.1.1 for the next patch upgrade path.
- About Quill now includes a sincere thanks to contributors and beta testers: Techopolis, Taylor Arndt, Michael Doise, Kayla Bentas, Shane Popplestone, and Becky Knobb.

### Packaging and release quality

- Embedded Python runtime verification with pinned SHA-256 validation
- Runtime dependency bundling derived from project metadata for UI and spell-check support
- Compiled Windows installer output: `Quill-Setup-0.1.exe`
- Release provenance and SBOM generation support via `scripts/generate_release_artifacts.py`

### Support and feedback

Quill 0.1.1 Beta uses a unified Help-menu support flow. `Help -> Report a Bug...` now handles report preparation, optional diagnostics generation, in-app review, and support-form handoff in one guided path. `Help -> Save Diagnostics...` remains available for standalone diagnostics export.

### Notes

This is a beta release. The product direction is aligned with the Quill 1.0 PRD, while some workflows are still evolving toward that fuller 1.0 target.
