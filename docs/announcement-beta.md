# Announcing Quill 0.1.5 Beta

Quill 0.1.5 Beta is a major expansion of the QUILL experience.

QUILL stands for Quality, Usable, Inclusive, Lightweight, Literate. This release doubles down on that promise with a broad set of user-facing capabilities for writing, reviewing, reading, conversion, accessibility, and local-first AI workflows on Windows.

This announcement is a complete map of what you can do in Quill 0.1.5 Beta today.

## What Quill is

Quill is a screen-reader-first, keyboard-first writing and document-intelligence environment for Windows.

It is designed to feel calm and predictable for everyday editing, while still supporting advanced workflows:

- long-document navigation
- deterministic cleanup and accessibility fixes
- In-App Preview and Side-by-Side Preview workflows
- compare and review sessions
- format conversion and extraction quality review
- local-first AI and automation helpers

## Complete capability map for 0.1.5 Beta

The sections below list user-facing features by workflow so you can quickly understand the full product surface.

### Core editor and workspace

Quill includes a full multi-document editor shell with:

- tabbed document workflows
- command palette with fast filtering and command discovery
- interactive status bar with actionable cells and customizable layout
- region cycling and focus movement designed for screen-reader users
- title/path behavior tuned to avoid duplicate information noise
- startup behavior controls, including opening with no document

File and workspace operations include:

- new, open, open recent, save, save as, save all
- save as plain text export
- reload from disk and backup restore
- page setup and print
- open from URL with trust and safety checks
- workspace snapshots and session restore patterns

### Writing and editing tools

Everyday editing includes:

- undo and redo
- cut, copy, paste, select all
- copy with source context where relevant
- insert and overwrite mode support
- selection growth and structural selection helpers
- mark ring and bookmark navigation helpers

Line and structure editing includes:

- move line up and down
- duplicate line
- delete line
- join lines
- indent and outdent
- toggle line and block comments
- trimming and cleanup helpers for consistent text quality

### Search, replace, and navigation

Quill supports both simple and advanced search flows:

- find, find next, find previous
- replace and replace all
- wildcard and regex search modes
- search history and repeated search workflows
- find all matches summary reporting

Navigation features include:

- go to line and page
- previous and next location jumps
- heading navigation
- block and structure navigation
- outline navigator for fast structural movement
- bracket matching
- next and previous region movement

### Formatting, markup, and authoring

Quill is strong in plain text and markup authoring:

- case conversion tools
- format-aware insertion workflows for headings, lists, links, tables, and code blocks
- link insertion and follow link
- heading insertion and level controls
- heading style controls (font, size, alignment)
- heading organizer for level repair, reorder, and validation
- list insertion and management
- code block insertion
- table insertion
- dedicated Markdown and HTML tag assist tools

### Word prediction and snippets

0.1.5 expands composition speed features:

- word prediction and tag IntelliSense via Ctrl+Space
- insert snippet via Ctrl+Alt+Space
- manage snippet library via Ctrl+Alt+Shift+Space
- snippet trigger expansion support
- snippet placeholders, choices, date/time tokens, and cursor anchors
- starter snippet pack install flows from settings

### Preview and reading flows

Quill supports multiple preview paths:

- In-App Preview
- Side-by-Side Preview
- Focus Preview command and keyboard flow
- automatic preview behavior for supported documents

Read workflows include:

- Read Aloud with controls and voice handling
- EPUB navigation and rendering support
- sticky notes and note vault workflows for review sessions

### Compare and review workflows

Compare tools include:

- compare document against file
- compare with clipboard
- compare options tuning
- synchronization and difference group traversal
- spoken and keyboard-friendly difference review

These features are designed for revision-heavy editing and content QA.

### GLOW workflows

GLOW is built directly into the editor for deterministic text quality and accessibility checks.

Current GLOW capability includes:

- full-document and selection audit reports
- fix preview generation before applying changes
- deterministic fixes for common structural and accessibility issues
- comparison between original and fixed output
- direct apply flows after review

Quill positions GLOW as an integral writing workflow, not a separate compliance afterthought.

### AI and automation

Quill 0.1.5 includes an expanded local-first AI surface:

- AI Hub as the central AI launch point
- Writing Assistant panel and quick prompt flows
- Prompt Studio for reusable custom prompts
- Agent Center for guided task planning prompts
- Ask Quill Chat workflows
- AI model settings and AI connection settings
- rewrite selection, summarize selection, continue writing, and grammar-fix entry points
- explicit approval model for operations that change document text
- clear status and detail feedback in menu and UI
- plain-language verification results with screen-reader announcements
- startup trust/privacy/responsible-AI consent acknowledgement

Connection workflows include:

- verify connection
- list models with a search filter for fast narrowing
- guided model recommendations based on local hardware and task framing
- provider selection across local, cloud, and OpenAI-compatible endpoints
- optional secret handling with platform protection where available
- no persisted AI chat transcript storage by default

AI Connection now includes first-class setup for OpenAI, Claude, OpenRouter, Google Gemini, and Microsoft Azure OpenAI alongside Ollama local/cloud. Most providers ship with smart default hosts so users can focus on key + model selection. Advanced OpenAI-compatible services remain available through custom endpoint mode.

Automation support includes:

- run-python action for controlled text transformations
- command execution integration from assistant flows
- review-first prompt and agent flows wired back into Writing Assistant

### Accessibility and low-vision capability

Accessibility is a first-class surface throughout Quill:

- screen-reader-first UI behavior and announcements
- region navigation model
- keyboard trap checks and accessibility inspection helpers
- contrast and high-contrast-aware behavior
- status bar as an interactive control surface
- clear state messages for long-running or risky actions
- discoverable help, what-can-I-do-here guidance, and keyboard references

### Dictation and voice workflows

Voice support includes:

- Windows dictation integration
- dictation command toggles and control states
- voice-command interpretation support in supported paths
- watch-folder monitoring to auto-open newly dropped supported files
- watch-folder settings for folder path, subfolders, startup, and polling
- startup-wizard watch-folder onboarding for first-run automation setup

BITS Whisperer phased rollout note:

- Dictation and watch-folder controls are now surfaced under the top-level **BITS Whisperer** menu
	to align migration work from BITS Whisperer into Quill.
- Quill now includes a **Speech Models** manager under **BITS Whisperer** with machine-aware
	recommendations and phased model visibility.
- Speech model setup now supports a guided **Recommended** mode plus a **Manual** model-selection mode,
	while keeping runtime behavior stable during this phase.
- Provider onboarding now includes a guided **Provider Center** under **BITS Whisperer** with local-first
	and cloud-first planning flows, readiness checks, and staged provider selection.
- **Help -> Status Page (HTML Preview)** now refreshes live while open, including BITS Whisperer model
	download state and broader asynchronous speech/task status.
- Users can keep auto-open status behavior off by default and opt in from Preferences, plus tune
	screen-reader refresh cadence with Quiet/Normal/Verbose announcement modes.
- BITS Whisperer now includes rollout-safe insight tools: **Readiness Check**, **Capability Matrix**,
	and **Download Queue** controls for retry/cleanup/status workflows.
- General Preferences now includes a **Use Artificial Intelligence** toggle (mirrors the AI menu)
	and a **BITS Whisperer safe mode lock** option for guarded rollout operation.
- QUILL now ships robust command-line startup options, including `--help`, `--version`,
	`--line`, `--column`, `--new-window`, and `--wait`.
- The first phase focuses on safe model management and guidance, including faster-whisper engine
	checks, while deeper transcription runtime behavior will roll out gradually.

### External tools and conversion workflows

Quill supports optional external tooling with guided onboarding and capability discovery:

- Pandoc integration for conversion workflows
- OCR tooling pathways (for image and extraction support scenarios)
- extraction quality review and bad extraction reporting
- document intake reporting for confidence and auditability

### Structured intake and file-type support

Quill supports a broad mix of source formats and intake paths.

Primary writing and editing surfaces include:

- plain text
- Markdown
- HTML
- RTF

Additional intake and review flows include:

- CSV and TSV
- Word (.docx and .doc)
- EPUB
- PowerPoint (.pptx and .ppt)
- spreadsheet-style formats (.xlsx and .xls)
- PDF and OCR-assisted pathways
- Pages and related extraction bridges where available

Release-safety note for this beta cycle:

- Word and CSV/TSV currently default to opening in the normal plain-text editor surface.
- Structured Word and CSV grid code paths remain in the codebase behind an internal gate while validation continues.

### Profiles, keymaps, and customization

Customization features include:

- feature profiles (including minimal and fuller experiences)
- keyboard packs for different editing conventions
- keymap management and preview tools
- status bar settings with restore defaults
- view and behavior toggles (dark mode, soft wrap, spellcheck-as-you-type, persistent undo, tray mode, and more)

### Reliability, trust, and recovery

Quill includes stability and trust-focused features:

- autosave and backup workflows
- persistent undo support
- trusted locations and safe handling paths
- notification and update checks
- diagnostics creation and support handoff flows
- safe mode and recovery behaviors for problematic launches

### Packaging and installer experience

Current build and installer work includes:

- polished Windows distribution output
- Inno Setup integration
- executable-first launch shortcuts where possible (to reduce extra console windows)
- optional bundled component wiring for Pandoc in installer flows

## Why this matters

Quill 0.1.5 Beta is not a narrow patch. It is a broad capability release that makes Quill viable for:

- daily writing and editing
- markup-heavy technical authoring
- accessibility review and deterministic cleanup
- complex import and conversion workflows
- revision and comparison-heavy editing
- local-first AI-assisted drafting and refinement

## Translation process and community effort

QUILL's localization direction is community-first and modeled on a gettext catalog workflow (`POT -> PO -> MO`). The project is building translation as a release discipline, not as an afterthought.

For contributors, translation work starts with GitHub pull requests against locale catalogs and clear translator comments. As the contributor base grows, QUILL will add a dedicated translation portal flow while keeping gettext catalogs as the source of truth.

The contributor plan, release cadence, quality gates, and translator expectations live in the new planning doc:

- [QUILL Translation Contributor Plan](localization/translation-contributor-plan.md)

## What is still in beta

Quill is still a beta release, which means:

- some workflows are deeper than others
- some integrations depend on optional local tools
- behavior can still be tuned based on real-world feedback

But the feature surface is already substantial and practical for real work.

## How to get the most from 0.1.5

1. Start with the user guide to pick workflows that match your daily work.
2. Use the command palette to discover features quickly.
3. Try one advanced workflow at a time: compare, preview, GLOW, or assistant.
4. Report rough edges with diagnostics so the next release can harden where it matters most.

Quill 0.1.5 Beta is ready for serious use, and this release is intentionally built to make the full capability surface visible instead of hidden.
