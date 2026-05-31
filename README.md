# QUILL

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

## What Quill is

Quill is a screen-reader-first Windows writing and document environment focused on practical keyboard workflows, stable editing, and accessible diagnostics/support flows.

Quill is designed to stay focused and useful:

- **Quality** -- dependable, polished, and serious enough for real work.
- **Usable** -- built around practical keyboard, screen reader, and low-friction editing needs.
- **Inclusive** -- designed from the beginning for blind users, screen reader users, keyboard users, and people with different skill levels.
- **Lightweight** -- fast, focused, not bloated, and friendly to people who just want to write or edit.
- **Literate** -- about words, code, Markdown, documents, learning, and thoughtful communication.

## Current release line

Current release line: **0.1.2**

Highlights in 0.1.2 include:

- Insert menu with searchable Markdown/HTML insertion.
- Word Prediction with `Ctrl+Space` plus HTML/Markdown tag IntelliSense.
- New snippet system with `Ctrl+Alt+Space` insertion, trigger expansion, and starter packs.
- Release-safety default for 0.1.2 testing: Word and CSV open in the normal plain-text editor surface.
- Structured Word view and CSV grid code paths remain in-repo behind an internal gate for continued verification.
- Expanded structured intake for `.doc`/`.docx`, `.ppt`/`.pptx`, `.xlsx`/`.xls`, `.pages`, and low-confidence PDF fallback via MarkItDown when available.
- Writing Assistant shell with prompt presets, generated tool suggestions, and a sandboxed Python runner.
- AI Connection workflow from both Preferences and the AI menu, with provider-aware host defaults.
- Verify Connection, List Models, and Recommend Model actions in AI Connection settings.
- AI menu status line with plain-language detail (`Ready` or `Needs attention`) and immediate accessible feedback.
- Optional Ollama cloud key mode over HTTPS (no local Ollama required for cloud endpoint access).
- Browser Preview with `Ctrl+Shift+V` and a selectable preview browser.
- Heading styling tools to apply font family, size, and alignment to current-level or all headings in Markdown/HTML.
- Heading Organizer (`Ctrl+Alt+Shift+H`) with keyboard-driven heading level changes, section reordering, and accessibility validation.
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

Snippet workflow quick start:

1. Press `Ctrl+Alt+Space` to open **Insert Snippet**.
2. Type to filter by snippet name, trigger, or body text.
3. Use arrow keys to choose, press Enter to insert, and fill placeholders when prompted.

Related commands:

- `Ctrl+Space`: Word Prediction (words, HTML tags, Markdown tags).
- `Ctrl+Alt+Shift+Space`: Manage snippets (create, edit, delete, import/export, starter packs).
- `Preferences -> Install Starter Snippet Packs`: install sample packs for writing, developer flow, and accessibility/support notes.

## Project layout

- `quill/` -- application code.
  - `quill/core/` -- core logic and document operations.
  - `quill/ui/` -- wxPython interface and dialogs.
  - `quill/platform/windows/` -- Windows integration points.
- `docs/` -- product docs and generated artifacts.
  - `QUILL-PRD.md` (+ `.html`, `.epub`)
  - `userguide.md` (+ `.html`, `.epub`)
  - `announcement-beta.md` (+ `.html`, `.epub`) -- published on GitHub Pages
  - `engineering/` -- implementation-facing docs surfaced on GitHub Pages
- `tests/` -- unit/integration/accessibility/performance tests.
- `scripts/` -- release, validation, and maintenance helpers.

## Run Quill locally

1. Install Python 3.12.
2. Install dependencies:
   - `pip install -e ".[ui,dev]"`
3. Launch:
   - `python -m quill`

Optional launch flags:

- `--safe-mode`
- `--reset-profile`

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

Run the full 0.1.2 readiness flow:

- `python scripts/release_readiness.py`

This runs:

1. Lint (`ruff check .`)
2. Tests (`pytest -q`)
3. Docs rebuild for `docs/*.md` (HTML + EPUB)
4. Docs artifact parity check
5. Release corpus verification

## CI and release automation

- CI workflow: `.github/workflows/accessibility-ci.yml`
- Windows release workflow: `.github/workflows/windows-release.yml`
- Docs site workflow: `.github/workflows/github-pages.yml` (publishes the docs hub and updates feed)

## Support and issue reporting

Use **Help -> Report a Bug** inside Quill. The flow supports diagnostics bundle generation, report preview, clipboard copy, and browser handoff to support submission.

## License

MIT. See `LICENSE`.
