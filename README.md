# QUILL

[![Contributors](https://contrib.rocks/image?repo=Community-Access/quill)](https://github.com/Community-Access/quill/graphs/contributors)

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

## What Quill is

Quill is a screen-reader-first writing and document environment for **Windows and macOS**, focused on practical keyboard workflows, stable editing, and accessible diagnostics/support flows.

Quill is designed to stay focused and useful:

- **Quality** -- dependable, polished, and serious enough for real work.
- **Usable** -- built around practical keyboard, screen reader, and low-friction editing needs.
- **Inclusive** -- designed from the beginning for blind users, screen reader users, keyboard users, and people with different skill levels.
- **Lightweight** -- fast, focused, not bloated, and friendly to people who just want to write or edit.
- **Literate** -- about words, code, Markdown, documents, learning, and thoughtful communication.

## Current release line

Current release line: **0.1.5**

Highlights in 0.1.5 include:

- Insert menu with searchable Markdown/HTML insertion.
- Word Prediction with `Ctrl+Space` plus HTML/Markdown tag IntelliSense.
- New snippet system with `Ctrl+Alt+Space` insertion, trigger expansion, and starter packs.
- Release-safety default for 0.1.5 testing: Word and CSV open in the normal plain-text editor surface.
- Structured Word view and CSV grid code paths remain in-repo behind an internal gate for continued verification.
- Expanded structured intake for `.doc`/`.docx`, `.ppt`/`.pptx`, `.xlsx`/`.xls`, `.pages`, and low-confidence PDF fallback via MarkItDown when available.
- Writing Assistant shell with prompt presets, generated tool suggestions, and a sandboxed Python runner.
- AI Connection workflow from both Preferences and the AI menu, with provider-aware host defaults.
- Verify Connection, List Models, and Recommend Model actions in AI Connection settings.
- AI menu status line with plain-language detail (`Ready` or `Needs attention`) and immediate accessible feedback.
- BITS Whisperer rollout surfaces for provider onboarding, readiness checks, status-page live updates, and guarded download queue controls.
- General Preferences controls for AI enable state, BW Safe Mode Lock, auto-open status behavior, and refresh cadence.
- Optional Ollama cloud key mode over HTTPS (no local Ollama required for cloud endpoint access).
- In-App Preview and Side-by-Side Preview with a dedicated Focus Preview command.
- Heading styling tools to apply font family, size, and alignment to current-level or all headings in Markdown/HTML.
- Heading Organizer (`Ctrl+Alt+Shift+H`) with keyboard-driven heading level changes, section reordering, and accessibility validation.
- Watch Folder automation under **Tools -> Dictation** to auto-open newly dropped supported files.
- Startup Wizard now includes a Watch Folder setup step so automation can be configured on first run.
- Search menu simplification with replace-all inside the Replace dialog.
- Unified diagnostics-backed support flow under **Help -> Report a Bug**.
- Menu IA refinement, including **Insert** before **View** and **Search** after **View**.
- Documentation refresh with regenerated Markdown/HTML/EPUB artifacts.

AI quick start:

1. Open `AI -> AI Connection...`.
2. Choose provider (`Ollama (local)`, `Ollama Cloud (API key)`, or `Custom HTTP`).
3. Enter host/model/key as needed.
4. Save settings; Quill auto-verifies and updates the AI status line.
5. Use **List Models** to choose a provider-returned model.

Ollama Cloud onboarding is available in this same flow. If you have an API key, Ollama Cloud offers a free personal-use tier with lower usage limits.

Snippet workflow quick start:

1. Press `Ctrl+Alt+Space` to open **Insert Snippet**.
2. Type to filter by snippet name, trigger, or body text.
3. Use arrow keys to choose, press Enter to insert, and fill placeholders when prompted.

Related commands:

- `Ctrl+Space`: Word Prediction (words, HTML tags, Markdown tags).
- `Ctrl+Alt+Shift+Space`: Manage snippets (create, edit, delete, import/export, starter packs).
- `Preferences -> Install Starter Snippet Packs`: install sample packs for writing, developer flow, and accessibility/support notes.

Watch Folder quick start:

1. Open `Help -> Startup Wizard...` and run the Watch Folder setup step, or open `Preferences -> Watch Folder Automation`.
2. Choose a folder where you will drop supported Quill files.
3. Enable watch folder monitoring.
4. Turn on auto-start if you want it running every launch.
5. Drop supported files into the folder; Quill opens them automatically.

## Platforms and on-device AI

- **Cross-platform.** Quill runs on **Windows and macOS** from one codebase. The macOS build ships as a signed, notarized `.app`; screen-reader announcements route to **VoiceOver** on macOS and to NVDA/JAWS/Narrator (via Prism) on Windows.
- **Ask Quill chat.** An on-device AI chat (**AI -> Ask Quill Chat**) rendered as a fully accessible WebView document: each turn is a heading you can navigate, new replies are announced, the message box lives in-page, and Escape closes it. Verified in **NVDA, JAWS, and VoiceOver**.
- **On-device AI, no cloud required.** macOS uses **Apple Foundation Models** (Apple Intelligence); Windows/Linux use **llama.cpp** (CPU, GGUF). You can optionally connect **Ollama (local)**, **Ollama Cloud (API key)**, or a custom HTTP endpoint. The assistant defaults to answering in chat and never edits your document without approval.
- **Accessible WebView, preview, and dialogs** are built on the open-source [`wx-accessible-webview`](https://github.com/Community-Access/wx-accessible-webview) library (extracted from Quill), which also powers the live Markdown/HTML preview, the About dialog, and the update/consent dialogs.
- **Train Writing Style** (**AI -> Train Writing Style...**) conditions the assistant on your own writing.

## Project layout

- `quill/` -- application code.
  - `quill/core/` -- core logic and document operations.
  - `quill/ui/` -- wxPython interface and dialogs.
  - `quill/platform/windows/` -- Windows integration points.
  - `quill/platform/macos/` -- macOS integration (VoiceOver announcements, Keychain, high-contrast, screen-reader detection).
  - `quill/core/ai/` -- on-device assistant backends (Apple Foundation Models, llama.cpp) and the Ask Quill agent.
- `docs/` -- product docs and generated artifacts.
  - `QUILL-PRD.md` (+ `.html`, `.epub`)
  - `userguide.md` (+ `.html`, `.epub`)
  - `announcement-beta.md` (+ `.html`, `.epub`) -- published on GitHub Pages
  - `engineering/` -- implementation-facing docs surfaced on GitHub Pages
- `tests/` -- unit/integration/accessibility/performance tests.
- `scripts/` -- release, validation, and maintenance helpers.

## Run Quill locally

Runs on **Windows and macOS** (Python 3.12).

1. Install Python 3.12.
2. Install dependencies:
   - `pip install -e ".[ui,dev]"`
   - On-device AI for Ask Quill: add `ai` on Windows/Linux (`pip install -e ".[ui,ai]"`, pulls llama.cpp). macOS uses Apple Foundation Models — no extra needed.
3. Launch:
   - `python -m quill`  (on Windows, `pythonw -m quill` for no console window)

To build a signed, notarized macOS app, see `scripts/build_macos.sh` and `docs/engineering/macos-build.md`.

Optional launch flags:

- `--safe-mode`
- `--reset-profile`
- `--version` (prints version and exits without launching UI)
- `--line N --column M` (place cursor for the first startup file)
- `--new-window` (force a new process instead of forwarding to existing instance)
- `--wait` (when forwarding to an existing instance, wait until it exits)
- `--diagnostics`
- `--dump-stacks`

Examples:

- `python -m quill --version`
- `python -m quill notes.md --line 120 --column 1`
- `python -m quill --new-window notes.md`

## Development checks

- Lint: `ruff check .`
- Tests: `pytest -q`

## Documentation workflow

Generate docs artifacts from `docs/*.md` with Pandoc:

- HTML: `pandoc docs\\<name>.md -f gfm -t html5 -s -o docs\\<name>.html`
- EPUB: `pandoc docs\\<name>.md -f gfm -t epub3 -o docs\\<name>.epub`

Artifact parity guard:

- `python scripts/check_docs_artifacts.py`

This fails when a `docs/*.md` source changed but matching `.html`/`.epub` files were not updated.
The installer ships the user-facing guides, while the GitHub Pages docs hub exposes the
PRD and engineering docs for anyone who wants the deeper implementation detail.

## One-command release readiness

Run the full 0.1.5 readiness flow:

- `python scripts/release_readiness.py`

This runs:

1. Lint (`ruff check .`)
2. Dependency audit (`pip-audit --strict`)
3. Tests (`pytest -q`)
4. Docs rebuild for `docs/*.md` (HTML + EPUB)
5. Docs artifact parity check
6. Release corpus verification

## CI and release automation

- CI workflow: `.github/workflows/accessibility-ci.yml`
- Security workflow: `.github/workflows/security-ci.yml`
- Windows release workflow: `.github/workflows/windows-release.yml`
- Docs site workflow: `.github/workflows/github-pages.yml` (publishes the docs hub and updates feed)

## Support and issue reporting

Use **Help -> Report a Bug** inside Quill. The flow supports diagnostics bundle generation, report preview, clipboard copy, and browser handoff to support submission.

## Contributing

Community contributions are welcome.

- Read **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, workflow, and PR expectations.
- Read **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** before participating.
- Read **[SECURITY.md](SECURITY.md)** for private vulnerability reporting.
- Read **[PRIVACY.md](PRIVACY.md)** for data handling and retention behavior.
- Read **[RESPONSIBLE_AI_USE.md](RESPONSIBLE_AI_USE.md)** for ethical and accountable AI use requirements.
- Read **[GOVERNANCE.md](GOVERNANCE.md)** for project decision model.
- Read **[MAINTAINERS.md](MAINTAINERS.md)** for maintainer responsibilities.
- Contributor graph: **[contrib.rocks / QUILL](https://contrib.rocks/image?repo=Community-Access/quill)**

## Community discussions

- Use GitHub Discussions for Q&A and feature ideation.
- Use GitHub Issues for confirmed bugs and scoped feature requests.

## Release governance

- Release process and branch policy: **[RELEASE.md](RELEASE.md)**
- Security advisory runbook: **[docs/engineering/security-advisory-workflow.md](docs/engineering/security-advisory-workflow.md)**

## License

MIT. See `LICENSE`.
