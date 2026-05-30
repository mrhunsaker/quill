# Quill

Quill is a screen-reader-first writing, reading, review, and document-intelligence environment for Windows.

Quill 0.1.1 Beta is being built by Blind Information Technology Solutions (BITS) together with Community Access.

It is being built for people who want an editor that feels calm, native, and deeply trustworthy from the keyboard. Quill is not only a place to type plain text. It is a place to open difficult documents, navigate structure, compare revisions, inspect extraction quality, run deterministic GLOW review, work with golden keyboard packs, and grow into richer workflows through optional external tools such as Pandoc and Tesseract.

## What Quill Already Does

The current implementation includes:

- a native wxPython editor shell with tabs, command palette, menus, and interactive status bar
- plain text, Markdown, HTML, EPUB, PDF, DOCX, ODT, RTF, JSON, XML, TOML, CSV, TSV, notebook, and SQLite reading surfaces
- formatting helpers for headings, lists, code blocks, tables, HTML tags, and Markdown snippets
- search, replace, outline navigation, bookmarks, compare workflows, and source-aware copy
- spell check, thesaurus, read aloud, OCR image intake, extraction review, and GLOW audit and fix actions
- feature profiles, keyboard packs, keymap editor, status-bar layout controls, and startup safety controls
- autosave, backups, recovery, trusted locations, notifications, update checks, and diagnostics export
- external tool onboarding, including a native Pandoc Conversion Wizard with labeled fields and browse controls when Pandoc is available

## Optional Tool Ecosystem

Quill treats optional tools as guided capability upgrades, not as hidden prerequisites.

Today Quill can detect or bundle tools such as:

- Pandoc for conversion into Markdown, HTML, or plain text workflows
- Tesseract OCR for local image-to-text workflows
- Prism/Prismatoid for unified screen-reader announcement routing
- LibreOffice for broader office conversion fallback planning
- Ghostscript for deeper PDF and PostScript pipeline work

The External Tools and Format Support dialog explains what each tool unlocks, whether Quill can already see it, and which wizard or workflow is the best first touch point.

## Feedback Path

The primary support and feedback route for Quill 0.1.1 Beta is inside Quill itself.

Start with **Help -> Report a Bug...**. The guided flow now includes optional diagnostics generation (including optional file paths), in-app report review, and the support-form handoff in one place.

**Help -> Save Diagnostics...** remains available as a standalone export command when you want diagnostics without filing a report.

## Update Feed and GitHub Pages

Quill's update checker reads a signed update feed from:

- `https://community-access.github.io/quill/updates/.quill-update-feed-v1.json`

The feed filename is intentionally non-obvious under `/updates/` and is deployed through GitHub Pages from `docs/site/`.

To regenerate the signed feed for a release:

```powershell
python scripts\generate_update_feed.py --version 0.1.1 --download-url https://github.com/Community-Access/quill/releases/latest --notes "Latest Quill release."
```

## Key Documents

User-facing and release-facing documentation lives in `docs/`:

- `docs/userguide.md` - the full guided user manual
- `docs/announcement-beta.md` - the beta announcement and feature story
- `docs/QUILL-PRD.md` - the product requirements document and current 1.0 roadmap

These documents are meant to work together:

- the README gives the product snapshot and packaging overview
- the user guide teaches daily use inside the app
- the announcement tells the feature story for evaluators and new testers
- the PRD records the broader 1.0 product intent, support model, and roadmap commitments

Engineering baseline docs are under `docs/engineering/`:

- architecture, contracts, runtime model, data layout, diagnostics runbook, quality gates, and roadmap mapping

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev,ui]
# Optional: install Prism bindings for enhanced announcement routing
pip install prismatoid
quill
```

## Packaging

Quill includes a Windows distribution builder that can generate a portable bundle and an Inno Setup installer. The packaging flow can:

- bundle embedded Python for a no-Python-required install
- stage the user guide and beta announcement into the portable bundle
- stage the PRD into the portable bundle
- optionally stage external tool directories such as Pandoc or Tesseract into `portable\tools\...`
- generate installer shortcuts for the README, user guide, announcement, and PRD

Example:

```powershell
python scripts\build_windows_distribution.py --bundle-python --pandoc-dir C:\Tools\Pandoc
```

## Test and Lint

```powershell
pytest
pytest tests\unit\io\test_text.py::test_read_text_document
ruff check .
mypy quill\core quill\io
```

## License

MIT. See `LICENSE`.
