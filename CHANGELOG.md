# Changelog

## QUILL Brand Identity

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

## Quill 0.1.5 Beta

Quill 0.1.5 Beta focuses on safe rollout surfaces for BITS Whisperer, clearer preference parity, and more accessible status monitoring without changing core editor behavior.

### Added and improved in 0.1.5

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