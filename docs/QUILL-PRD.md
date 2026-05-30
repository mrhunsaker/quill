# Quill: Product Requirements Document

## A magical, screen-reader-first writing and document environment, built in wxPython.

Status: Quill 1.0 PRD aligned with Quill 0.1.1 Beta
Owner: Blind Information Technology Solutions (BITS) and Community Access
Target platform: Windows 10 and Windows 11
Target screen readers: NVDA (primary), JAWS, Narrator
UI framework: wxPython (wxWidgets 3.2 or newer)
Language: Python 3.11 or newer

---

## 1. Vision

Quill is a focused writing and document-reading workstation for blind and low-vision users. It opens almost anything, turns it into clean, navigable text in a familiar Windows edit field, and gives the writer a quiet, predictable place to think.

1. **Open by default.** Free, open source, with no proprietary scripting layer required. Works first class with NVDA out of the box, and equally well with JAWS or Narrator.
2. **Screen-reader-native.** Every surface is a standard Windows control (`wx.TextCtrl` multiline, `wx.ListBox`, `wx.Dialog`) so MSAA, UIA, IAccessible2 and braille routing all just work. No custom drawn controls in the writing path.
3. **Magical, not flashy.** "Magic" means the right thing happens without ceremony. PDFs become readable. Bookmarks survive edits. Backups are automatic. The command palette knows what you mean. Nothing surprises the screen reader.
4. **Local first, cloud optional.** Heavy lifting (PDF extraction, OCR, layout repair, spell checking) runs locally when possible. Cloud assistance is opt-in per action, transparent, and never silent.

If a sighted person watched a Quill user work, they would see almost nothing on screen. That is the point.

---

## 2. Goals and non-goals

### 2.1 Goals

- Provide a dependable plain-text writing surface that NVDA, JAWS and Narrator can read without quirks.
- Open a wide range of document formats and present them as editable text in a standard edit field.
- Preserve the original source file. Extracted or rendered text saves through "Save As" so originals are never overwritten.
- Offer practical writer tools: find and replace, bookmarks that survive edits, magical spell check, word count, page navigation, multiple documents, backups, recent files.
- Offer a discoverable command palette modelled on Visual Studio Code so users do not need to memorise every shortcut.
- Let every shortcut be reassigned through a friendly keymap editor.
- Offer optional, transparent AI assistance for awkward PDFs, scanned images and broken layouts.
- Integrate cleanly with Windows: file associations, "Open with", jump lists, taskbar.
- Be themable for low vision (high contrast, large fonts) without breaking screen-reader behaviour.

### 2.2 Non-goals

- Not a visual word processor. No bold, italic, fonts, colour styling in the writing surface for v1.
- Not a desktop publishing tool.
- Not a replacement for Microsoft Word or LibreOffice Writer.
- Not a book reader with pagination and reflow. Quill renders documents as editable text.
- Not an AI chat product. AI is used only to repair reading order or extract text.

---

## 3. Target users and primary scenarios

### 3.1 Personas

1. **Mira, blind university student.** Reads PDF lecture notes daily. Needs them to make sense linearly, with reliable search and bookmarks she can name.
2. **Ade, blind technical writer.** Writes long Markdown and HTML. Wants to write in a quiet edit field, preview structure in a browser, and export cleanly.
3. **Pat, blind admin assistant.** Opens invoices and Word documents from email. Wants to copy reference numbers and totals quickly.
4. **Sam, low-vision novelist.** Uses Narrator with a large font and high contrast. Writes long manuscripts, restores from yesterday's backup occasionally.
5. **Jamie, blind sysadmin.** Edits INI, JSON, log and config files. Wants a calm editor that does not fight tooling.

### 3.2 Primary scenarios

- Open a 30-page PDF invoice, find the payment reference, copy it.
- Start a blank document, write a 2000-word article in Markdown, preview it in the browser, export to Word.
- Open a DOCX from a colleague, read it, save the extracted text as a `.txt` for archival without touching the original.
- Open a scanned receipt, ask Quill to OCR it through a cloud service, get a plain text rendering.
- Restore the version of `chapter-7.md` from two saves ago.
- Reassign `Ctrl+G` from Go To Line to Go To Bookmark because the user prefers a different convention.

---

## 4. Product principles

1. **The edit field is sacred.** The writing surface is a standard multi-line `wx.TextCtrl`. Nothing exotic. Screen readers see plain text. Always.
2. **Predictable keyboard.** Shortcuts match Windows conventions where they exist. New shortcuts are documented, discoverable, and reassignable.
3. **Speak the result, not the process.** After every meaningful action, Quill announces a short, useful result through the screen reader.
4. **Originals are read-only by default.** Anything rendered or extracted saves through Save As. Plain-text formats save in place.
5. **No silent network calls.** Any cloud assistance asks first, shows progress, and reports the outcome.
6. **Quiet by default.** No surprise toasts. No animated UI. No tabs that announce themselves on every switch.
7. **Recoverable.** Backups happen on save. Crash recovery on launch. Nothing the user wrote should ever be lost.
8. **Discoverable.** A searchable command palette lists every action with its current binding.

---

## 5. Functional requirements

### 5.1 Application shell

- Single window per running instance, with multiple documents inside.
- Three primary regions, always present: **menu bar** (5.1a), **central editor**, **status bar** (5.1b).
- Window title shows `document-name [modified] – Quill`. The word "modified" appears only when the document has unsaved changes.
- Tray icon optional, off by default.
- No splash screen.
- **Single-instance mode** is on by default. A second launch with a path opens that path in the existing window and brings it to the foreground. A setting allows multi-instance for advanced users.
- **F6 region cycling** moves keyboard focus through the three regions in order (editor → menu bar → status bar → editor). `Shift+F6` cycles in reverse. The region name is announced on entry ("Status bar"). If the Outline Navigator (5.16) is pinned, it joins the cycle between editor and menu bar.
- All regions are stock wx controls (`wx.MenuBar`, `wx.TextCtrl`, `wx.StatusBar` with a custom layout) so MSAA/UIA expose them correctly without scripts.

### 5.1a The magical menu bar

The menu bar is standards-based, predictable, and exhaustive. Every menu item is also a command in the palette, every item shows its current keybinding to the right of its label, and the displayed binding updates live when the user rebinds it. No menu item is hidden; disabled items remain visible with a short tooltip explaining why they are disabled in the current context.

Menu structure:

- **File**: New/Open/Open Recent/Open from URL, **Workspace Snapshots**, Save/Save As/Save All/Save as plain text, Reload/Restore backup, print flows, close/exit.
- **Edit**: Undo/redo, clipboard, selection helpers, link insertion/follow, and **Recent Marks (Ring)** with plain-language labels.
- **Search**: Find/Replace flows plus Next/Previous/All matches.
- **View**: shell behavior toggles, title style options, theme and visual controls.
- **Navigate**: line/page/bookmark movement, heading/block/structure movement, outline, bracket match, region movement.
- **Format**: case/comment/indent/line transforms plus rich text and heading controls.
- **Insert**: table/list/code/footnote/tag insertion helpers.
- **Tools**: regrouped into discoverable submenus:
  - Writing and Language
  - Read Aloud
  - Integrations
  - Document Intake
  - Authoring and Automation
  - Compare Documents
  - Accessibility
  - Support
  - Customize
- **Window**: document/tab management actions.
- **Help**: contextual help, onboarding docs, feature profile support, updates, and About.

All menu strings are translatable. Every menu item has a unique mnemonic. The menu bar may be hidden via View; when hidden, pressing `Alt` reveals it temporarily and `Esc` dismisses it again, matching Windows convention.

### 5.1b The magical status bar

The status bar is not a passive label strip. It is a fully keyboard-navigable row of items that any user can reach with `F6` and arrow through with Left and Right. Each item is a small interactive cell, and `Enter` on a cell either toggles a state, opens a chooser, or runs a related command. This is modelled on Visual Studio Code's status bar, adapted for screen-reader-first interaction.

Design rules:

- **Container**: a custom layout inside `wx.StatusBar` composed of small `wx.Window`-derived focusable buttons (`wx.lib.agw.AquaButton` style is rejected; we use plain `wx.Button` with flat styling). Each cell exposes itself as an MSAA button with name, role, value, and description so NVDA, JAWS, and Narrator read it as a real interactive control.
- **Reachable**: `F6` from the editor moves focus into the status bar at the cell the user last interacted with (or the leftmost cell on first entry). Left/Right arrow moves between cells with wrap-around. `Home`/`End` jump to first/last. `Esc` returns focus to the editor. Tab and Shift+Tab also move between cells inside the status bar.
- **Announced**: when focus enters the status bar, the region name and the focused cell are announced ("Status bar, Line 12, Column 7, button"). Cells announce their value when arrowed to.
- **Activated**: `Enter` or `Space` triggers the cell's primary action. `Shift+F10` or the Application key opens a context menu of related actions for that cell. Right-clicking is equivalent.
- **Live updates**: cell values update without stealing focus. Updates marshal via `wx.CallAfter` and use a debounced single accessibility event per cell per 200 ms to avoid speech spam.
- **Hideable per cell**: a context menu item "Hide this item" tucks any cell behind an overflow group. Overflow is reached at the right end ("More items, button"); Enter opens a small list of hidden cells, any of which can be restored.
- **Plugin-extensible** (v1.1): plugins may register status-bar cells with the same MSAA contract.

Cells shipped in v1.0, in left-to-right order:

| Cell | Default value | Primary action (Enter) | Context menu |
| --- | --- | --- | --- |
| **Document name** | `chapter-7.md` or `Untitled 1` | Opens Quick Switcher (palette `~`) | Switch document, Reveal in Explorer, Copy Path, Close |
| **Modified state** | `Modified` / `Saved` | Save | Save, Save As, Reload From Disk, Restore Backup |
| **Line / Column** | `Line 12, Column 7` | Opens Go To Line | Go To Line, Go To Page, Go To Bookmark |
| **Selection** | `Selection: 3 lines, 47 words` or hidden when no selection | Opens Document Statistics on selection | Statistics on selection, Convert case…, Sort selected lines |
| **Word count** | `1,248 words` | Opens Document Statistics on document | Statistics, Configure reading rate |
| **Page** | `Page 4 of 23` (only when document has page markers) | Opens Go To Page | Next page, Previous page, Page list |
| **Search term** | `Find: "reading order"` (only when a search term is set) | Opens Find with the term pre-filled | Find Next, Find Previous, Find All, Clear Search |
| **Encoding** | `UTF-8` | Opens Reload With Encoding | Reload With Encoding, Save With Encoding, Auto-detect |
| **Line endings** | `LF` / `CRLF` / `CR` | Cycles to the next style and prompts to confirm | Choose explicitly, Convert on save |
| **Indent** | `Spaces: 4` / `Tabs` | Opens indent settings | Convert to tabs, Convert to spaces, Set width |
| **Language** | `en-GB + tech + personal` (the active spell-check dictionary stack) | Opens dictionary stack chooser | Add dictionary, Pin to document, Per-paragraph (v1.2) |
| **Spell check** | `Spell check on` / `Spell check off`. When errors exist: `3 errors` | Toggles as-you-type spell check | Run spell check, Jump to next misspelling, Reset learning |
| **Read aloud** | `Read aloud: ready` or `Read aloud: speaking` | Toggles read-aloud playback | Voice…, Speed…, Read selection, Read document |
| **Accessibility audit** | `Audit: clean` or `Audit: 2 warnings` (only after a manual or auto audit) | Opens the Issues panel | Run audit, Configure rules, Ignore for this document |
| **AI status** | `AI: off` or `AI: ready (OpenAI)` | Opens AI provider settings | Cancel current task, Switch provider, View last response |
| **Background tasks** | `Idle` or `Extracting PDF, 42%` | Opens a small Tasks dialog listing in-flight operations with Cancel | Cancel all, Show task log |
| **Notifications** | `No new messages` or `2 messages` | Opens the Notifications dialog (release notes, available updates, backup recovery offers) | Dismiss all, Open Notifications |
| **Quill** (rightmost) | `Quill 1.0` | Opens About | Check for Updates, Release Notes |

Default visibility: Document name, Modified state, Line/Column, Word count, Encoding, Line endings, Spell check, Background tasks, Notifications. Other cells are present but tucked into overflow until first relevant use; they auto-surface when their context becomes relevant (for example Page appears as soon as a paged document is opened; Search term appears the moment a search term is set).

### 5.1c Trust and verification

Quill explains what it did, how confident it is, and how to recover if extraction looked wrong.

- **Document Intake Report**: every non-plain-text open announces a short, screen-reader-friendly summary and exposes a full report with format, engine, page/sheet/slide counts, OCR use, AI use, confidence, detected structures, and sidecar path.
- **Copy With Source**: selected text can be copied with source location appended (file, page/line/column, engine, confidence) and the source map stays available for future citations.
- **Extraction quality review**: PDF-derived documents expose page-by-page confidence warnings and allow retry/review flows.
- **Cleanup recipes**: deterministic review-and-apply transforms for OCR/PDF cleanup (dehyphenate, remove headers/footers, normalize ligatures, line reflow).
- **Report Bad Extraction**: creates a support package with version, metadata, and no document content unless the user explicitly opts in.
- **What Can I Do Here?**: context-sensitive help for the current surface, available from the Help menu and command palette.
- **Safe mode**: a startup-safe mode disables plugins, custom keymaps, AI, recent docs, themes, and other optional state for troubleshooting.
- **Portable mode clarity**: portable builds can store settings locally next to Quill.exe or in AppData, with a first-run choice and an independence command.
- **Golden document corpus**: release testing includes a canonical corpus of PDFs, DOCX, XLSX, PPTX, EPUB, Markdown, HTML, and OCR samples with expected extraction and announcement snapshots.

### 5.1f Profile safety and recovery

Feature profiles must be safe, explainable, reversible, and recoverable.

- **Why don’t I see this?** explains why a named feature is hidden, quiet, unavailable, or gated by the current profile.
- **Profile switch preview** shows visible, quiet, and off features before applying a profile change.
- **Undo last profile change** is available from Notifications after a profile switch.
- **Emergency reset to Essential** is available from launch and from the recovery flow.
- **Profile health check** validates feature IDs, dependencies, visibility paths, and profile JSON integrity.
- **Feature-coverage gate** fails CI when commands, menus, cells, pages, or help topics lack a valid feature ID.
- **Profile-aware keyboard reference** can filter to current profile, quiet features, off features, or diff views.
- **Profile-aware welcome guide** adapts onboarding to the active profile.
- **Privacy and network labels** declare local-only, external-helper, metadata-only, and network-sending features.
- **Feature maturity labels** distinguish core, stable, advanced, helper-required, and unavailable features.
- **Profile import safety** schema-validates profiles and prevents silent enablement of recovery-sensitive features.
- **Show what changed** produces a plain-text summary after profile switches.

### 5.1g Feature registry and user profiles

Quill’s feature-profile system is a first-class product surface, not a cosmetic preference layer.

- **Feature Registry**: a central registry assigns every feature an id, category, description, default state, dependencies, conflicts, privacy impact, network impact, accessibility notes, and profile tags.
- **Profile layering**: user overrides sit above custom profiles, shipped profiles, default registry state, and locked safety rules.
- **Shipped profiles**: Essential, Writer, Reader and Student, Office and Admin, Accessibility Professional, Developer and Power Text, Low Vision, Braille and Screen Reader Power User, Full Quill, and Custom.
- **Settings UI**: Profiles and Features page with search, feature table, explain/related commands, compare profiles, and profile management actions.
- **Onboarding**: first run asks how Quill should start and chooses a profile.
- **Command/menu/status/help integration**: feature IDs govern command palette, menus, status-bar cells, settings rows, help topics, and format handlers.
- **Dependency enforcement**: enabling a feature can enable required dependencies; disabling a feature warns about affected features.
- **Storage**: feature flags and profiles are stored locally as JSON and can be imported/exported safely.
- **Safety rules**: locked-on features cannot be disabled by shipped profiles, custom profiles, imported profiles, plugins, or user overrides.
- **Feature metadata**: each feature declares risk, maturity, privacy, and network labels for use in settings and help.

### 5.1d Power search, regex, and special characters

Search and Unicode cleanup are first-class accessibility features, not power-user extras.

- **Search modes**: Find, Find All, Replace, Replace All, Find in Selection, and saved search recipes support plain text, whole word, regular expression, and wildcard modes.
- **Regex helper**: a screen-reader-friendly helper surfaces common tokens, explanations, and try-on-document previews.
- **Plain-English errors**: regex errors are reported in single-sentence form with character positions and no traceback.
- **Match review**: users can review captured groups for a match, including named groups.
- **Replace preview**: Replace All shows a preview before applying, with undo as one step.
- **Saved searches**: common search/replace recipes can be stored with mode, scope, and description.
- **Special characters**: the Find dialog can insert special search tokens for tabs, line endings, non-breaking spaces, zero-width characters, smart quotes, ellipses, bullets, and Unicode character classes.
- **Character Inspector**: reports the character under the cursor by name, code point, category, and common encodings.
- **Invisible character view**: users can switch to an inspection view that describes invisible characters textually.
- **Unicode cleanup**: normalization and cleanup commands remove or rewrite common noisy characters with a preview first.

### 5.1e Feature flags and profiles

Quill should stay calm by default and unlock power features intentionally.

- **Feature states**: `on`, `quiet`, `off`, `locked on`, `locked off`.
- **Core stays locked on**: editor, open/save, backups, crash recovery, help, accessibility announcements, settings.
- **Advanced features can be quiet/off**: regex search, regex helper, saved searches, OCR, AI repair, document intake reports, extraction review, character tools, compare/diff helpers, diagnostics, plugin surfaces.
- **Profiles**: Essential, Writer, Reader and Student, Office and Admin, Accessibility Professional, Developer and Power Text, Low Vision, Braille and Screen Reader Power User, Full Quill, Custom.
- **Settings**: a Profiles and Features page lets the user switch profiles, compare them, and expose quiet features when desired.
- **Command/menu gating**: menus, palette entries, status-bar cells, help topics, and settings pages only surface features appropriate to the active profile.

### 5.2 Documents and the editor

- The editor is a multi-line `wx.TextCtrl` with `wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_NOHIDESEL | wx.TE_AUTO_URL`. `wx.TE_RICH2` is used only for selection and undo behaviour, not styling.
- UTF-8 internally. Line endings preserved on open, normalised to platform default on new documents.
- Soft wrap on by default; toggle with `Alt+Z`.
- Standard editing: cursor movement, selection, clipboard, undo and redo, all via the native edit control.
- `Ctrl+Delete` deletes the next word; `Ctrl+Backspace` deletes the previous word; result announced.
- Case conversion: `Ctrl+U` upper, `Ctrl+L` lower, `Ctrl+Shift+T` title. Selection if present, otherwise whole document.
- Multiple documents: `Ctrl+Tab` and `Ctrl+Shift+Tab` cycle. Switching announces document name only.
- Close current document: `Ctrl+W` or `Ctrl+F4`. Prompt to save if modified.
- Exit: `Alt+F4` or `Ctrl+Q`. Prompts for each modified document.
- Quill does not restore previous documents on launch by default. Opt-in setting available.

### 5.3 File operations

- `Ctrl+N` new blank document.
- `Ctrl+O` open via standard `wx.FileDialog`. Quill aims to be the most catholic accessible reader on Windows; the full supported list is in [section 5.3a](#53a-extended-format-support). The headline groups are:
  - **Plain text and config**: `txt`, `log`, `cue`, `ini`, `json`, `jsonc`, `json5`, `xml`, `csv`, `tsv`, `yaml`, `yml`, `toml`, `nfo`, `env`, `properties`, `conf`, `cfg`, `dotenv`.
  - **Markdown family**: `md`, `markdown`, `mdx`, `mdown`, `mdwn`, `mkd`, `mkdn`, `mkdown`, `ronn`, `qmd` (Quarto), `rmd` (R Markdown).
  - **Lightweight markup**: `rst` (reStructuredText), `adoc`/`asciidoc`, `textile`, `org` (Org-mode), `wiki`/`mediawiki`, `bbcode`, `tex`/`latex`, `bib`/`bibtex`, `typ` (Typst).
  - **HTML family**: `html`, `htm`, `xhtml`, `mhtml`/`mht`, `svg` (read as text + extracted `<text>` content).
  - **Office, modern**: `docx`, `docm`, `dotx`, `dotm`, `pptx`, `pptm`, `xlsx`, `xlsm`, `ods`, `odt`, `odp`, `odg`, `pages`, `key`, `numbers`.
  - **Office, legacy** (best-effort, with AI escalation): `doc`, `ppt`, `xls`, `wpd` (WordPerfect), `wps` (Works), `wri` (Windows Write), `sxw`/`sxc`/`sxi` (StarOffice).
  - **PDF and PostScript**: `pdf`, `ps`, `eps`, `xps`, `oxps`.
  - **E-books**: `epub`, `epub3`, `azw`, `azw3`, `mobi`, `kfx`, `fb2`, `lit`, `lrf`, `prc`, `pdb` (Palm), `tcr`, `cbz`/`cbr` (comic, text layers + OCR).
  - **Rich text**: `rtf`, `rtfd`.
  - **Subtitles and captions**: `srt`, `vtt`, `sbv`, `ass`/`ssa`, `sub`, `ttml`/`dfxp`, `scc`, `stl`, `cap`.
  - **Spreadsheets as text tables**: `csv`, `tsv`, `xlsx`, `xls`, `ods`, `numbers`, `parquet` (read-only), `feather` (read-only). Rendered as accessible plain-text tables with column headers, with `Ctrl+Shift+Right`/`Left` moving by column.
  - **Email and calendar**: `eml`, `msg` (Outlook), `mbox`, `pst` (one message at a time, with index), `ics` (calendar), `vcf` (contact card).
  - **Notes and journals**: `one` (OneNote, best-effort), `enex` (Evernote export), `note` (Apple Notes via iCloud export), `bear` (Bear export), `simplenote` JSON exports.
  - **Source code and scripts** (opened with syntax-aware tokenisation but presented as plain text): `py`, `pyw`, `pyi`, `js`, `mjs`, `cjs`, `ts`, `tsx`, `jsx`, `c`, `h`, `cpp`, `hpp`, `cs`, `java`, `kt`, `rs`, `go`, `rb`, `pl`, `pm`, `php`, `lua`, `swift`, `m`, `mm`, `r`, `jl`, `dart`, `scala`, `clj`, `cljs`, `ex`, `exs`, `erl`, `hs`, `fs`, `vb`, `ps1`, `psm1`, `psd1`, `bat`, `cmd`, `sh`, `bash`, `zsh`, `fish`, `sql`, `graphql`/`gql`, `proto`, `thrift`.
  - **Build, package and lock files**: `Makefile`, `CMakeLists.txt`, `*.gradle`, `*.sbt`, `package.json`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `Cargo.toml`, `go.mod`, `pom.xml`, `*.csproj`/`*.sln`, `Dockerfile`, `*.dockerfile`, `*.tf`/`*.tfvars`, `*.bicep`, `*.k8s.yaml`.
  - **Diff, patch and VCS artefacts**: `diff`, `patch`, `gitignore`, `gitattributes`, `gitmodules`, `gitconfig`, `gitlog` (text dumps), `hgrc`.
  - **Data and notebook**: `ipynb` (Jupyter, read as a linear cell-by-cell document with role headers), `qmd`/`rmd` rendered notebooks, `pickle`/`joblib` (refused with explanation), `sqlite`/`db` (schema + sampled rows view, read-only).
  - **Logs and trace**: `log`, `gz`/`zip`/`tar`/`7z` (auto-extract single-text-file archives), `evtx` (Windows Event Log, summarised), `etl` (limited), `journal` JSON.
  - **Web feeds**: `rss`, `atom`, `opml`, `json-feed`.
  - **Chat and transcript exports**: WhatsApp `.txt` exports, Telegram `.json`/`.html` exports, Slack export JSON, Discord JSON exports, Teams transcript `.docx`/`.vtt`, Zoom `.vtt`/`.txt`, Otter `.txt`, ChatGPT export `.json` (rendered as linear conversation).
  - **DAISY and accessible publishing**: `daisy` (2.02, 3), `nimas`, `bbeb`, `pef` (braille). Read as plain text with section markers.
  - **Braille files**: `brf`, `brl`, `pef`, `ueb` (with optional back-translation to print via liblouis).
  - **Audio with transcripts** (transcript only): pairs of `.mp3`/`.wav`/`.m4a`/`.opus` with a sibling `.vtt`/`.srt`/`.txt` are opened as the transcript with playback shortcuts via plugin.
  - **Image with OCR** (opt-in OCR, local by default via Tesseract, AI escalation available): `png`, `jpg`/`jpeg`, `tif`/`tiff`, `bmp`, `webp`, `heic`, `avif`, `gif`, `jp2`. Multi-page TIFF supported.
  - **Scanned documents**: `djvu`, `cbz`/`cbr`, multi-page TIFF, image-only PDFs (handled by the PDF pipeline).
  - **Subtitle bundles in containers**: `mkv`/`mp4` (extract embedded text tracks only; no media playback).
  - **Web archives**: `warc`, `wacz`, single-file `.html` saves from browsers, `webarchive` (Safari, best-effort).
  - **Code-block exchange**: GitHub Gist URLs and `.gist.json`, Pastebin `.txt`, snippet bundles.
- `Ctrl+S` saves. For editable text formats, saves in place. For rendered/extracted formats, opens Save As.
- `Ctrl+Shift+S` opens Save As directly.
- Recent files: last N (default 10, range 5 to 50). If empty, announce "No recent files."
- File Explorer integration: settings panel lets the user register Quill with Windows for chosen extensions and add an "Open with Quill" verb.

### 5.3a Extended format support

The table below lists every format family Quill adds, why each matters, and how Quill renders it. Every renderer follows the same rules: present text in a standard edit field, preserve the original file, escalate to the enhanced extractor or AI repair only when local extraction is poor and the user asks.

| Format family | Specific formats added | Why it matters | How Quill renders it |
| --- | --- | --- | --- |
| **Spreadsheets** | `xlsx`, `xlsm`, `xls`, `ods`, `numbers`, `csv`, `tsv` | Blind users routinely receive spreadsheet attachments; current accessible tooling forces Excel | Each sheet becomes a section. Tables are emitted as accessible plain-text columns with header row, `Ctrl+Shift+Right/Left` navigates by column, `Ctrl+Shift+Down` summarises totals |
| **OpenDocument** | `odt`, `odp`, `odg`, `ods` | Common in EU public sector and academia; Direct extractor via `odfpy`; structure preserved as headings, lists, tables |
| **Apple iWork** | `pages`, `key`, `numbers` | Cross-platform collaboration is increasingly common; iWork files arrive in email frequently | Local extractor via the iWork archive format; AI escalation for complex layouts |
| **Legacy office** | `ppt`, `xls`, `wpd`, `wps`, `wri`, `sxw`/`sxc`/`sxi` | Older institutional archives still circulate; Best-effort local readers; AI escalation by sending the original file when local reading fails |
| **E-books (proprietary)** | `azw`, `azw3`, `mobi`, `kfx`, `fb2`, `lit`, `lrf`, `prc`, `pdb`, `tcr` | EPUB-only support excludes most Kindle and older e-book libraries | Reuse Calibre's conversion engine where present (plugin in v1.1) or bundled minimal readers for the open formats |
| **Comics with text** | `cbz`, `cbr` | Educational comics and graphic textbooks ship in CBZ; Extract pages, OCR each, present per-page text with page navigation |
| **DjVu and XPS** | `djvu`, `xps`, `oxps` | Academic scans (DjVu) and Microsoft alternatives to PDF (XPS) are common in research | Local extractors; PDF-style page navigation |
| **PostScript** | `ps`, `eps` | Academic preprints and older typeset documents | Convert via Ghostscript to text + page markers |
| **TeX and Typst** | `tex`, `latex`, `bib`, `bibtex`, `typ` | Academic and scientific writing community is largely TeX-based; no accessible plain editor handles it gracefully | Plain-text editing with optional rendered preview to PDF/HTML via local engines; bibtex entries readable as structured records |
| **Lightweight markup** | `rst`, `adoc`/`asciidoc`, `textile`, `org`, `wiki`/`mediawiki`, `bbcode` | Documentation toolchains for Python, Ruby, Asciidoctor, Emacs Org-mode, wikis | Plain-text editing; preview via the appropriate renderer; export to HTML/DOCX |
| **DAISY and braille** | `daisy` 2.02/3, `nimas`, `brf`, `brl`, `pef`, `ueb` | Accessible publishing standards that ironically lack accessible editors. Braille files need round-trip print/braille translation | Linear text presentation with chapter/section navigation; liblouis for braille back-translation; export to BRF |
| **MHTML and web archives** | `mhtml`/`mht`, `warc`, `wacz`, browser "single file" saves, Safari `.webarchive` | Saved web pages are the second-most common research artefact after PDF | Extract the primary document; show resources list; allow Preview as HTML |
| **SVG** | `svg` | SVG is text; titles, descriptions, and `<text>` content carry semantic meaning often inaccessible elsewhere | Show as XML in edit field plus a "Reading View" that extracts titles, descriptions, and text in document order |
| **Subtitles (full set)** | `sbv`, `ass`/`ssa`, `sub`, `ttml`/`dfxp`, `scc`, `stl`, `cap` | broadcast and YouTube captioners need the rest | Render as plain text with optional timecode column; export between formats |
| **Email and mail archives** | `eml`, `msg`, `mbox`, `pst` | Email frequently arrives as standalone files (forwarded, archived, exported); `.msg` and `.pst` are pure Microsoft and historically painful | Headers as a labelled block, body as plain text, attachments listed with "Open in Quill" actions; `pst` and `mbox` get an index UI |
| **Calendar and contacts** | `ics`, `vcf` | Common attachments; today opened by heavy apps | Render events and contacts as structured plain text records |
| **Notes ecosystems** | `one`, `enex`, Apple Notes export, `bear`, Simplenote JSON | People have years of notes locked in proprietary apps | Read-only renderers; each note opens as its own document |
| **Source code and config** | Full polyglot list in 5.3 | Programmers and sysadmins use Quill for quick edits; the screen-reader story for VS Code is good but heavyweight | Syntax-aware tokeniser informs spell check and word navigation; presentation remains plain text |
| **Build, package, IaC** | `Dockerfile`, `*.tf`, `*.bicep`, `*.k8s.yaml`, `pyproject.toml`, etc. | DevOps work is text-heavy and benefits from a calm reader | Plain text with section folding via shortcut, schema-aware error reporting in the `!` palette mode |
| **Diff and patch** | `diff`, `patch`, `gitconfig`, `gitignore` | Code review and merge work | Hunks rendered with `+`/`-` summarised aloud; `Ctrl+]` next hunk |
| **Notebooks** | `ipynb`, `qmd`, `rmd` | Data science and research; notebooks are JSON and unreadable in basic editors | Linearised: each cell becomes a section with role header ("Code cell 3", "Markdown cell 4", "Output of cell 3"), outputs included where text |
| **Data files** | `sqlite`/`db`, `parquet`, `feather` | Researchers and analysts frequently inspect data files | Read-only schema view + first N rows as a table; refuses to edit and explains why |
| **Logs and trace** | `evtx`, gzipped logs, single-file archives | Sysadmin and support workflows | Auto-extract; render with timestamp column |
| **Web feeds** | `rss`, `atom`, `opml`, `json-feed` | Accessible feed consumption | Render as a list of articles, Enter to open one |
| **Chat exports** | WhatsApp, Telegram, Slack, Discord, Teams, Zoom, Otter, ChatGPT | People archive conversations and need to search them | Linearised conversation with speaker headers, timestamps optional |
| **Image OCR** | `png`, `jpg`, `tif` (multi-page), `bmp`, `webp`, `heic`, `avif`, `gif`, `jp2`, plus `djvu` and scanned PDFs | Photographed receipts, signage, scanned mail | Local Tesseract OCR by default; AI escalation for handwriting or poor scans |
| **Audio with transcript** | `.mp3`/`.wav`/`.m4a`/`.opus` paired with `.vtt`/`.srt`/`.txt` | Podcasts, lectures, interviews with transcripts | Opens the transcript; optional playback plugin syncs cursor to audio |
| **Code-block exchange** | Gist URLs, Pastebin URLs, snippet bundles | Developers share text via URLs daily | One-shot fetch + open as unsaved document |

Some renderers (notably KFX, PST, legacy proprietary office, and some iWork variants) require optional helper tools installed locally. Quill detects what is present at startup and the Open dialog only advertises formats it can actually read on this machine. The long-term design is a full Settings → Format Support page; the current beta already ships an External Tools and Format Support dialog that shows supported helpers, the capabilities they unlock, and copy-to-clipboard installation hints (never an automatic install).

#### Editable vs. read-only matrix

Not every format we open is something a user should edit. Quill is explicit about which formats round-trip in place vs. require Save As:

- **Save in place**: every plain-text and lightweight-markup format, source code, configs, subtitles, braille (BRF), SVG, JSON/XML/YAML/TOML, notebooks (when the user has explicitly chosen to keep notebook structure on save).
- **Save As only (originals protected)**: DOCX/DOC, PPTX/PPT, XLSX/XLS, ODT/ODP/ODS, Pages/Keynote/Numbers, PDF, PS/EPS, XPS, EPUB and other e-books, RTF, DjVu, comics, MHTML and web archives, email (`eml`, `msg`, `pst`, `mbox`), calendar and contact files, OneNote, data files (`sqlite`, `parquet`, `feather`), all image formats.
- **Read-only with explicit refusal-to-edit message**: PST archives, parquet/feather, evtx, AZW3/KFX, anything DRM-protected.

#### Plugin escalation

Where bundling a large dependency would balloon installer size (Calibre, Ghostscript, Tesseract trained-data packs, MeCab for Japanese, LibreOffice headless for legacy office), Quill ships a thin shim and offers a one-click plugin install from the Format Support page. Plugins announce their license clearly before installing.

### 5.4 PDF handling in v1.0

This section is the canonical, scoped statement of what Quill 1.0 does with PDF files. Anything not listed here is explicitly out of scope for v1.0 and tracked in the backlog ([section 17](#17-backlog-and-deferred-items)).

**What v1.0 ships**

1. **Tier 1, local extraction (automatic on open).** A layered pipeline runs `pdfplumber` and `pypdfium2` (with `pdfminer.six` as a third fallback) per page, scores each extraction for readability (line count, alphabetic ratio, average line length, presence of suspicious one-word-per-line patterns), and picks the best result per page. Pages are concatenated with explicit page markers so page navigation is exact.
2. **Page navigation.** `Page Up` / `Page Down` move to the previous/next page marker. `Ctrl+G` opens Go To Page when page markers exist. The status bar's Page cell shows `Page n of m`. Reaching the first or last page is announced.
3. **Embedded bookmarks.** Bookmarks (Adobe's outline) become Quill bookmarks for that document and appear in the Outline Navigator (5.16) under their original hierarchy. They are read-only with respect to the original PDF; renaming, adding, and deleting affect Quill's own bookmark store.
4. **Password-protected PDFs.** On open, Quill prompts for the password through a standard modal dialog. The password is used in-memory only and is never written to disk, never logged, never sent over the network.
5. **Editable rendering, protected original.** The extracted text is presented in the standard editor. `Ctrl+S` opens **Save As** so the original `.pdf` cannot be overwritten by extracted text. The Save dialog offers Text, Markdown, HTML, and All Files.
6. **Document metadata.** Author, title, subject, keywords, creation date, modification date, and page count are accessible via `File > Document Properties…` and announced in Where Am I when the document is a PDF.
7. **PDF document statistics.** Document Statistics (5.19) reports page count, image count per page (informational), tagged-structure presence, and language metadata.
8. **Accessibility audit, informational.** The Accessibility Audit (5.20) reports whether the PDF has tagged structure, whether it has embedded bookmarks, the image-only page count, language metadata, and password protection state. It does not modify the PDF.
9. **Tier 3, AI-assisted reading order (opt-in, manual).** `Tools > Improve Reading Order…` sends the PDF to the user-configured LLM provider (the user supplies the API key; nothing is bundled). The action **always** asks for confirmation before sending, shows the host name and approximate size in the confirmation dialog, announces progress every ~20 seconds during the request, and reports the outcome. Refuses, with a clear spoken message, if the PDF exceeds the configured page-count limit (default 40). Results open as a new unsaved document whose Save defaults to Save As.
10. **OCR for scanned PDFs.** When tier 1 yields no readable text on a page, Quill offers a one-click escalation to local OCR via the bundled Tesseract (English shipped, additional languages downloadable). For longer scanned PDFs the user may instead escalate to tier 3 AI rendering.
11. **Selection and copy.** Standard selection works in the extracted text. `Ctrl+C` copies as plain text. There is no copy-with-formatting target in v1.0 (the extracted text has none).
12. **Find, Outline, Bookmarks, Word Count, Document Statistics, Read Aloud, Accessibility Audit** all work over the extracted text exactly as they do for any other document.
13. **Compare** (`Tools > Compare With File…`) works against the extracted text representation; comparing two PDFs compares their extracted plain-text forms.

**What v1.0 does not ship (deferred to backlog)**

- **Tier 2 "enhanced local" extractor.** No pure-Python local layout analyser meets the v1.0 quality bar. v1.0 has tier 1 and tier 3 only.
- **Heading synthesis from font-size analysis** when no embedded bookmarks exist. Off by default; available as an opt-in experimental switch in Advanced settings, clearly labelled as experimental.
- **PDF form filling and signing.** Not in v1.0.
- **Writing back to PDF** (annotation, highlight, comment). Not in v1.0; original PDF is read-only by design.
- **Embedded media** (audio, video, 3D, attachments inside the PDF). Not in v1.0.
- **XFA forms.** Not in v1.0.
- **Tagged-structure tree editor.** Reading the structure summary is in; editing it is backlog.

### 5.5 Improve reading order

A general action under Tools and the command palette:

- For text-based documents, sends the current document text to the configured LLM for layout repair.
- For PDF and legacy DOC, sends the original file so text boxes and visual columns can be analysed.
- For PPTX, can send the file when local extraction is insufficient.
- Always asks first. Never used to answer questions about the document.
- Result opens as a new unsaved document; Save defaults to Save As.

### 5.6 HTML and Markdown

- HTML files open as plain text in the editor.
- `File > Preview as HTML` writes a temporary HTML file and opens the default browser.
- Markdown files open as plain text.
- `File > Preview Markdown as HTML` renders via `markdown-it-py` and opens the browser.
- `File > Export Markdown as HTML` saves a standalone HTML file.
- `File > Export Markdown as Word` produces a `.docx` via `python-docx`, preserving headings, lists, links, tables, code blocks.

### 5.7 Find and replace

Find in Quill is designed to feel like Microsoft editors and Visual Studio Code at the same time: F3 just works once a term is known, the search term is remembered everywhere it makes sense, and everything is announced.

**The search term, the central concept.** Quill maintains a single "current search term" per editor. The term is set by any of:

- typing in the Find dialog and pressing Enter,
- pressing `Ctrl+F3` with a selection (the selection becomes the search term),
- pressing `Ctrl+F3` with no selection (the word under the cursor becomes the search term),
- restoring it from session storage on launch (when enabled),
- arrow-selecting a previous term from the Find dialog's history dropdown.

The status bar's **Search term** cell (5.1b) displays the current search term and its options. `Enter` on the cell reopens Find pre-filled.

**Keystrokes**

- `Ctrl+F` opens Find. Pressing Enter searches forward, sets the search term, selects the match, and announces `Found on line 12: <line text>`.
- `Ctrl+Shift+F` opens Find anchored to backwards search.
- `F3` advances to the **next** occurrence of the current search term without opening any dialog. If no term is set, F3 opens Find with focus in the input. If a term is set, F3 simply selects the next match and announces line + context. At end of document, search wraps to the start (announced as "Wrapped to top").
- `Shift+F3` does the same in reverse, wrapping at the start to the end ("Wrapped to bottom").
- `Ctrl+F3` sets the current word or selection as the search term and advances. `Ctrl+Shift+F3` sets it and retreats. This is the Visual Studio convention.
- `Alt+F3` opens **Find All**: a list of every match with line number and context line, in a stock `wx.ListBox`. Enter jumps to a match; the dialog stays open so the user can iterate. The cell at the bottom shows `Match 3 of 17`.
- `Ctrl+H` opens Replace. Options: case sensitive, whole word, regex, **in selection** (pre-checked when a selection is present on open). Replace, Replace All, Find Next, Find Previous buttons. Replace All reports `Replaced 12 occurrences`. Undo is one step.
- `Esc` from any Find or Replace dialog closes it and returns focus to the editor at the previous cursor position (not at the last match unless the user pressed Enter).
- **"Not found"** is always spoken, never silent. After two consecutive not-found beeps, Quill suggests opening Find All to verify the term.

**History and persistence**

- Find and Replace remember the last 20 terms per session (in-memory) and the last 100 across sessions (on-disk, in `%APPDATA%\Quill\search-history.json`; cleared from a single button in Settings → Privacy). Replacement strings have their own parallel history.
- The dropdown arrow on the Find input opens history; Up/Down arrows in the input cycle through history when the input is empty.

**Incremental preview (opt-in, off by default)**

- A Settings switch `Editing → Incremental Find Preview` makes the editor preview the next match as the user types in the Find dialog (Notepad++ style). Escape returns the cursor to where it was before Find opened. Enter commits and closes. Off by default because preview-driven cursor movement can confuse screen readers; we expose it for users who prefer it.

**Predictable announcements**

- On every match Quill announces a structured one-liner: `Found on line N: <line text>`. The line text is truncated to 200 characters with an ellipsis to keep speech short. Long lines are abbreviated around the match so the matched text is always in the spoken slice.
- On wrap: `Wrapped to top` or `Wrapped to bottom`, followed by the match announcement.
- On Replace All: `Replaced N occurrences in document` or `Replaced N occurrences in selection`.
- On regex error: a single sentence, no traceback.

**Find in current selection.** When the editor has a non-empty selection at the moment Find or Replace is opened, the "In selection" checkbox is pre-checked; Replace All scopes its work to the selection. F3 and Shift+F3 continue to operate document-wide regardless, because muscle memory expects that.

**Find next while typing.** When the Find dialog is closed and the search term is set, typing in the editor does not interfere with F3; the search term is preserved until the user clears it (`Ctrl+Shift+\` or status-bar cell context menu → Clear Search).

**Project-wide Find (Find in Folder)** is deferred to v1.2.

### 5.8 Spell checking (magical, local-first)

This section was significantly expanded in v0.2 of this PRD. See [section 6](#6-spell-checking-deep-dive) for the full design and the decision rationale.

Quill ships **its own spell checking engine**, built on Hunspell dictionaries, designed from the ground up for screen-reader speed and predictability. It does **not** depend on TinySpell or any other external spell-checker process.

- `F7` opens the full Spell Check dialog (Word-style, but accessible).
- As-you-type checking is on by default. Misspellings are tracked in a sidecar model (not visual squiggles) and announced gently on word boundary if the user opts in.
- `Ctrl+;` jumps to the next misspelling and opens an inline suggestion popup (a small modal list, fully keyboard driven).
- Suggestions come from Hunspell plus an n-gram reranker trained on the user's writing for personalised top-3 suggestions.
- Personal dictionary persists per user; per-document dictionary persists in a sidecar file.
- Multiple simultaneous dictionaries: e.g. English (UK) plus a technical jargon list plus the document's own dictionary, merged with priority.
- All entirely local. No cloud round-trip ever for spell check.

### 5.9 Word count and navigation

- `Ctrl+Shift+W` reports words, characters, and paragraphs. Reports on selection if present.
- `Page Up` / `Page Down` navigate by real page markers (PDF). Announces page on move.
- `Ctrl+G` opens Go To Line, or Go To Page when page markers exist.

### 5.10 Bookmarks

- Bookmarks are **named jump points** intended for durable anchors a user wants to revisit by name.
- `Ctrl+B` sets a bookmark at the current position. Prompts for a name.
- Stored per bookmark: name, line number, column, ~120 characters of surrounding text, document path, ISO timestamp.
- `Ctrl+Shift+G` opens Bookmarks Manager.
- On jump: if the stored line still contains the surrounding text, go there. If not, search for the surrounding text and update the bookmark. If still not found, fall back to line number and announce "approximate position."
- Bookmarks for saved documents persist in `%APPDATA%\Quill\bookmarks\<hash>.json`.

### 5.11 Selection helpers and Where Am I

- `Ctrl+Shift+,` marks selection anchor; `Ctrl+Shift+.` extends selection.
- `Ctrl+Shift+I` Where Am I. In the editor: line, column, word count, modified state, page if available. In dialogs: structured description of the current field.

### 5.12 Command palette (Visual Studio Code style)

This is a centrepiece of v0.2. See [section 7](#7-command-palette-deep-dive) for the complete design.

- Single shortcut: `Ctrl+Shift+P` (also `F1`).
- Prefix-driven modes inside one input field, exactly like VS Code:
  - No prefix: command search.
  - `>` explicit command prefix (typing it is optional; a fresh palette starts in command mode).
  - `?` shows help for available prefixes.
  - `:` go to line.
  - `@` go to bookmark in current document.
  - `#` go to bookmark across all open documents.
  - `!` show warnings and errors (spell check issues, broken bookmarks, unsupported features used).
  - `<` open a recent file.
  - `~` switch open document.
  - `=` open a setting.
- Fuzzy matching with subsequence scoring, recency boost, and frequency boost (most-recently-used commands float to the top).
- Each row shows: command title, current keybinding, source (core or plugin), and a short hint.
- Right-arrow on a command edits its keybinding inline (see [section 8](#8-keymap-and-keystroke-reassignment)).
- Fully keyboard driven. Standard `wx.ListBox` underneath, with a `wx.SearchCtrl` on top. All accessible via stock screen-reader behaviour.

### 5.13 Document backups

- On every save of an existing file, the previous saved bytes are copied to `%APPDATA%\Quill\backups\<hash>\<iso-timestamp>.bak`.
- `File > Restore Document Backup` lists backups for the current document, newest first.
- Restore prompts for confirmation. Before overwriting the editor, the current buffer is backed up too.
- Restored text is marked modified; user saves with `Ctrl+S`.
- Retention: default keep last 50 per document, prune older than 90 days, never delete the most recent 5.
- Crash recovery: autosave snapshot every 30 seconds while a document is dirty; on launch, Quill offers to recover any orphan snapshots.

### 5.14 Settings

`Ctrl+,` opens Settings, organised in a `wx.Treebook`:

- **General**, **Editing**, **Reading**, **Spell check**, **PDF and AI**, **Files**, **Appearance**, **Backups**, **Keyboard** (see [section 8](#8-keymap-and-keystroke-reassignment)), **Privacy**.

### 5.15 Plugin system (v1.1)

- Plugins are Python packages discovered in `%APPDATA%\Quill\plugins`.
- Each plugin can register commands, file format readers and writers, settings pages, palette entries, and **default keybindings** (which the user can override).
- Plugin manifest must declare network and filesystem use.

### 5.16 Outline Navigator (heading tree)

One of Quill's signature productivity wins for readers and writers. Opens a tree of every heading in the current document, fully accessible, and lets the user jump anywhere in two keystrokes.

- `Ctrl+Shift+H` opens the Outline Navigator. The window contains a filter `wx.SearchCtrl`, a `wx.TreeCtrl` of headings, and standard OK/Cancel/Jump buttons. Everything stock; screen readers handle it natively.
- The outline is computed deterministically per format:
  - **Markdown**: ATX (`#`) and Setext (`===`, `---`) headings, parsed via `markdown-it-py` AST.
  - **HTML/XHTML/MHTML**: `<h1>`…`<h6>` and `<section><h*>` patterns via `beautifulsoup4`. ARIA `role="heading" aria-level="n"` is honoured.
  - **reStructuredText**: title underline conventions via `docutils`.
  - **AsciiDoc**: `=` through `======` lines.
  - **Org-mode**: `*` through `******` lines.
  - **LaTeX/Typst**: `\part`, `\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph`; Typst `= heading` syntax.
  - **DOCX**: paragraphs styled Heading 1–9 (via `python-docx`).
  - **EPUB**: `nav.xhtml` first, falling back to `toc.ncx`.
  - **PDF**: embedded document bookmarks (the same tree shown in Adobe Reader's bookmarks pane); also synthesised from font-size analysis when no bookmarks exist (opt-in, off by default).
  - **DAISY**: navigation document.
  - **Subtitle files**: chapter markers if present; otherwise time-bucketed sections every five minutes.
  - **Jupyter notebooks**: each Markdown heading inside Markdown cells, plus a synthetic node per cell.
  - **Generic fallback**: lines that look like headings (ALL CAPS short lines, numbered sections like `1.`, `1.1`) are offered as a flat list with a warning that the document has no real structure.
- Tree behaviour:
  - Up/Down arrow navigates between headings. Right Arrow expands; Left Arrow collapses. `*` (numpad or shift+8) expands all descendants of the focused node.
  - Typing in the filter field narrows the visible tree to headings whose text matches (substring, case-insensitive). The first match is announced. `Tab` returns focus to the tree.
  - `Enter` jumps the editor to the selected heading, closes the dialog, and announces `Jumped to heading level 2: <text>`.
  - `F2` renames the heading in place (editable formats only) and updates the document.
  - `Ctrl+C` copies the heading title; `Ctrl+Shift+C` copies the path (`Chapter 3 › Section 2 › Subsection 1`).
- The Outline Navigator also lives in the command palette under the `#` prefix when the current document has structure, so headings appear inline with document switching.
- Targets: build the tree for any text-based document up to 1 MB in under 50 ms; up to 10 MB in under 500 ms.

### 5.17 Jump-by-structure shortcuts

In-editor navigation by document structure, alongside the Outline dialog:

- `Ctrl+PgDn` / `Ctrl+PgUp`: next / previous heading of any level. Announces `Heading level 2: <text>`.
- `Ctrl+Alt+1` through `Ctrl+Alt+6`: next heading of level 1–6. `Ctrl+Alt+Shift+1–6` for previous.
- `Ctrl+Alt+0`: jump to the next paragraph that is not a heading (useful for skimming).
- `Ctrl+]` / `Ctrl+[`: next / previous block boundary (code fence, list, table, blockquote) in Markdown and HTML.
- `Ctrl+Alt+B`: jump to the start of the current logical block; `Ctrl+Alt+E` to the end.
- All shortcuts reassignable.

### 5.18 Line and block operations

VS Code-style editor productivity, all standard text-control operations:

- `Alt+Up` / `Alt+Down`: move the current line (or all selected lines) up or down. Announces the swap.
- `Ctrl+Shift+D`: duplicate the current line or selection.
- `Ctrl+Shift+K`: delete the entire current line.
- `Ctrl+L`: select the current line (repeat to extend by line).
- `Ctrl+J`: join the current and next line with a single space.
- `Tab` / `Shift+Tab` on a multi-line selection: indent or outdent.
- `Ctrl+/`: toggle line comment using the current document's comment marker (`#`, `//`, `<!-- -->`, etc.).
- `Ctrl+Shift+/`: toggle block comment where supported.
- **Tools menu**: Sort Selected Lines (ascending/descending, case-sensitive option, natural-numeric option), Remove Duplicate Lines, Reverse Lines, Trim Trailing Whitespace, Convert Indent (tabs↔spaces), Normalize Whitespace, Wrap to Column N.
- **Smart list continuation** (Markdown, opt-in): pressing Enter on a `- `, `* `, or `1. ` line continues the list and increments numeric markers; pressing Enter on an empty list item ends the list.
- **Bracket and quote auto-pair** (off by default; per-format toggle in Settings). Never enabled in plain text.

### 5.19 Document statistics and reading metrics

Local, instant, never sends content anywhere.

- `Ctrl+Alt+S` opens the Document Statistics dialog.
- Reports: characters with and without spaces, words, sentences, paragraphs, lines, headings per level, links, images, code blocks, tables, footnotes.
- Estimated reading time at a configurable rate (default 200 wpm) and speaking time (default 150 wpm).
- Readability scores: Flesch Reading Ease, Flesch–Kincaid Grade Level, Gunning Fog, SMOG, Automated Readability Index. Each line in the dialog is a separate `wx.StaticText` so screen readers can read them one at a time.
- Longest sentence (with click-to-jump), average sentence length, longest paragraph.
- If a selection exists, statistics report on the selection and the title says so explicitly.
- Status bar shows running word count for the current document or selection.

### 5.20 Accessibility auditor

Quill's audience is exactly the audience that needs to *produce* accessible documents. v1.0 ships a first-class auditor.

- `Ctrl+Alt+A` runs an Accessibility Audit on the current document and opens the Issues dialog. (The same list is reachable via the command palette `!` prefix.)
- **Markdown and HTML** checks: heading-level skips (h2 to h4), missing or empty `alt` text on images, `alt` text equal to the filename, generic link text (`click here`, `here`, `read more`, `link`), empty links, duplicate link text pointing to different targets, tables without header rows, deeply nested lists (>5), paragraphs longer than 500 words, missing `lang` attribute on `<html>`, missing page title.
- **DOCX** checks: missing alt text on inline images, heading-style skips, generic link text, tables without header rows, document language not set, missing title.
- **PDF** checks (informational): whether the PDF has any tagged structure, presence of embedded bookmarks, image-only page count, language metadata, password protection.
- **Markdown front-matter** checks: required keys present (configurable per project).
- Issues panel: list with severity (error/warning/info), location, message, and “Why this matters” explanation. `Enter` jumps to the issue, `Delete` dismisses for the session, `Ctrl+I` ignores the rule in this document (persisted in the document's sidecar).
- Two companion catalogs:
  - **Alt-text catalog** (`Ctrl+Alt+I`): every image with its current alt text, edit in place for editable formats, jump-to-source.
  - **Link inventory** (`Ctrl+Alt+L`): every link with target and accessible name; flags duplicates and internal-vs-external; copy URLs.
- Audit completes in under 200 ms for documents up to 100 KB; up to 5 s for documents up to 5 MB.

### 5.21 Table mode for Markdown and HTML tables

When the editor cursor enters a Markdown pipe table, a Markdown grid table, or an HTML `<table>`, Quill enters Table Mode and announces it.

- `Ctrl+Shift+Right` / `Ctrl+Shift+Left`: next or previous cell; the column header is announced first, then the cell content (`Column "Price": $4.99`).
- `Ctrl+Shift+Down` / `Ctrl+Shift+Up`: next or previous row in the same column.
- `F2`: open the current cell in a small editor dialog with the column header in the title.
- `Ctrl+Alt+T`: insert a row below; `Ctrl+Alt+Shift+T`: insert a column after.
- `Ctrl+Alt+R`: delete the current row; `Ctrl+Alt+C`: delete the current column. Both confirm.
- `Ctrl+Alt+H`: toggle the current row as the header row (Markdown only).
- Tables remain valid Markdown or HTML on save: Quill re-aligns pipes and pads columns on every edit so the underlying text stays readable as plain text.

### 5.22 Editor essentials

A group of small, individually unremarkable features whose absence would feel cheap. All ship in v1.0.

- **Encoding picker**: `File > Open With Encoding…`, `File > Reload With Encoding…`. Status bar shows the active encoding. Auto-detection on open via `charset-normalizer`; user can always override.
- **Line endings**: `File > Line Endings` (LF, CRLF, CR). Status bar shows the active style. “Convert on save” is an opt-in setting.
- **Reload from disk**: `Ctrl+Shift+R`. If the editor has unsaved changes, prompt.
- **External-change watcher**: detect when the file changes outside Quill; offer to reload (auto-reload if the editor is unmodified).
- **Insert date / time**: `Ctrl+Alt+D` (with a one-time format chooser that the user can re-open from Settings).
- **Templates**: `File > New From Template…`. Templates live in `%APPDATA%\Quill\templates\`. Ships with: Markdown article, Meeting notes, Daily journal, Letter, Issue report, README, Changelog, MIT license header, Markdown blog post with front-matter.
- **Snippets**: per-format snippet packs with trigger + Tab expansion. Off by default in prose, on by default in code. Editable in Settings.
- **Save options** (per document and per workspace): trim trailing whitespace on save, ensure final newline, normalise line endings on save.
- **Smart paste**: by default, strip rich-text formatting when pasting from sources that include it. `Ctrl+Shift+V` pastes the original payload.
- **Sessions**: `File > Save Session…` and `File > Open Session…` preserve the set of open documents and per-document cursor position.
- **Print**: `Ctrl+P` opens the system print dialog, preserving the editor font and encoding.
- **Extract to plain text**: `Tools > Save As Plain Text` works for any opened format and is the canonical way to harvest text from a non-editable source.
- **Compare two documents**: `Tools > Compare With File…` supports an interactive compare session and can also produce a unified-diff document in a new editor tab. Interactive compare mode moves the cursor between differing line groups, offers a difference list, and supports synchronized compare navigation. Diff hunks remain navigable with `Ctrl+]` / `Ctrl+[`.

### 5.23 Recent locations history (browser-style back/forward)

- `Ctrl+Alt+Left` moves back through cursor jump points; `Ctrl+Alt+Right` moves forward.
- Push triggers: Find match, F3/Shift+F3 jump, bookmark jump, outline jump, Go To Line, Go To Page, opening a document, switching documents.
- The ring holds up to 100 entries per editor, deduplicated when consecutive entries collapse to the same line.
- A small `Navigate → List Recent Locations…` dialog shows the ring as a list with document, line, and the line text; Enter jumps. Stock `wx.ListBox`.
- Each location remembers document path, line, column, and a hash of nearby text so jumps survive small edits exactly as bookmarks do (5.10).

### 5.24 Mark ring

A second, lighter-weight navigation system for power users. Inspired by Emacs but adapted to Windows muscle memory.
Marks are **temporary jump points**; bookmarks (5.10) are named and more durable.

- `Ctrl+`Space (overloaded carefully; the editor does not need plain Ctrl+Space) sets an anonymous mark at the cursor; status bar briefly announces `Mark set`.
- `Ctrl+Shift+`Space pops to the most recent mark; further presses walk back through the ring.
- `Ctrl+Alt+`Space exchanges point (cursor) and mark, useful for jumping to where the user was and back.
- `Edit → Mark Ring → List Marks…` shows the ring in a stock `wx.ListBox` with document, line, column, and surrounding text snippet.
- Up to 50 marks in a circular buffer per session. Marks do not persist across sessions in v1.0.
- All keystrokes reassignable. Default may be overridden by users for whom `Ctrl+Space` collides with screen-reader features; the conflict detector (8.4) flags the well-known cases at install time.

### 5.25 Read Aloud (secondary voice, not the screen reader)

Quill ships a read-aloud feature that uses a **secondary** voice the user picks from a list. It deliberately does not compete with the screen reader: the screen reader keeps doing its job while read-aloud plays, and the user can use a different voice for each so they are easy to tell apart.

- Backend: SAPI 5 voices and Windows OneCore voices via `pywin32`/`comtypes`. Detected at startup; the list is presented in `Settings → Read Aloud` and in the Read Aloud voice chooser.
- `Ctrl+Alt+P` starts/pauses read-aloud from the current cursor; `Ctrl+Alt+S` stops; `Ctrl+Alt+.` skips to the next sentence; `Ctrl+Alt+,` previous.
- Granularity: sentence by default; settings allow paragraph or word.
- Highlight follows: the editor cursor moves to the start of the currently spoken sentence so when read-aloud stops, the user is exactly where they last heard. The status bar's Read Aloud cell shows progress.
- Selection-only mode: when invoked with a selection, read-aloud reads only the selection and stops at the end.
- Voice, speed, pitch, volume all configurable. Three named profiles (Reading, Proofreading, Skim) save preferred values.
- The read-aloud voice never overrides the screen reader's announcements; if a screen reader speaks something while read-aloud is active, read-aloud continues but is briefly ducked.

### 5.26 Number lines and strip line numbers

A small tool that addresses a real recurring user request.

- `Tools → Number Lines…` opens a dialog with format options: `1.`, `[1]`, `1:`, `1)`, `001 `, and a custom Python `str.format` template using `{n}`.
- Start index, increment, zero-padding, and "only number non-blank lines" options.
- Applies to the whole document or selection.
- `Tools → Strip Line Numbers` reverses by regex; the regex used to add numbers is also the regex used to strip them.
- Undo is one step; the tool reports `Numbered 482 lines` or `Stripped numbers from 482 lines`.

### 5.27 Open from URL

- `Ctrl+Alt+O` opens a small dialog with a URL field. Accepts `http://`, `https://`, raw GitHub URLs, gist URLs, and Pastebin URLs.
- Quill downloads the resource to a per-session temp file, detects the format from the response `Content-Type` and the URL extension, and opens it with the appropriate reader.
- Network announcement: the dialog shows the host name and an estimate of bytes (where the server reports `Content-Length`) before download starts; the download is cancellable.
- The opened document has the URL as its display path, no associated file on disk; `Ctrl+S` opens Save As.
- Redirects are followed up to 5 hops; redirects to a different host prompt for confirmation.
- All TLS errors and 4xx/5xx responses are reported with a single readable sentence, no stack traces.

### 5.28 Format-aware bracket and quote navigation

- `Ctrl+]` and `Ctrl+[` already navigate by block in editor-mode (5.17); when inside a code-aware context (code file, Markdown code fence, HTML tag), they instead jump to the matching bracket, quote, fence, or HTML tag.
- `Ctrl+Shift+\` is the explicit "Match Bracket" command (also reachable from Navigate menu).
- `Ctrl+Shift+]` extends the selection from the cursor to the matching bracket.
- Bracket matching is language-aware: respects strings and comments in supported languages; Markdown respects fence boundaries.
- The match is announced as `Matched bracket on line N, column C` so screen-reader users do not lose context.

### 5.29 Format menu (text transforms, no styling)

A dedicated menu surfacing transforms that are otherwise reachable via Tools or shortcuts. The menu exists because discoverability matters more than purity.

- Capitalisation: Upper Case, Lower Case, Title Case, Sentence Case, Toggle Case.
- Lines: Move Line Up/Down, Duplicate Line, Delete Line, Join Lines, Toggle Line Comment, Toggle Block Comment.
- Indent: Indent, Outdent, Convert to Tabs, Convert to Spaces, Set Indent Width….
- Markdown helpers: Insert Heading (levels 1–6), Insert Bullet List, Insert Numbered List, Insert Task List, Insert Table…, Insert Link…, Insert Code Block, Insert Footnote.
- Magical tag helpers: Insert HTML Tag… (with attribute picker) and Insert Markdown Tag… (semantic snippet picker).
- Surface-aware formatting shortcuts (Markdown/HTML only): `Ctrl+B` bold, `Ctrl+I` italic, and heading levels `Ctrl+Alt+1` through `Ctrl+Alt+6`.
- Re-flow: Wrap to Column…, Re-flow Paragraph.

### 5.29a Magical HTML and Markdown tag picker

- `Format → Insert HTML Tag…` opens a keyboard-first picker of common tags (`section`, `article`, headings, list/table tags, inline emphasis, links, images, code).  
- After selecting a tag, Quill prompts for optional attributes in a compact `key=value; key2=value2` format and inserts valid tag text into the editor.
- If text is selected, Quill wraps the selection in the chosen non-void tag. If not selected, Quill inserts an opening/closing pair and places the cursor between them. Void tags (`img`, `br`, `hr`, `input`) are inserted self-closing.
- `Format → Insert Markdown Tag…` opens a semantic picker (`Bold`, `Italic`, `Inline Code`, `Code Block`, `Heading`, `List`, `Task List`, `Blockquote`, `Link`, `Image`, `Table`, `Footnote`) and inserts the matching markdown snippet.
- For Link and Image, Quill asks for the target URL and composes the final markdown in one action.
- All picker actions are mirrored in the command palette and are keybindable through the keymap system.
- `Edit → Insert Link…` (`Ctrl+K`) uses a format-aware inserter: markdown links in Markdown docs, `<a href>` in HTML docs, and `text (url)` form in plain text.

### 5.30 Bookmark export and import

- `Tools → Bookmarks → Export…` writes the bookmark set for the current document to a single JSON file alongside its hash so it round-trips cleanly.
- `Tools → Bookmarks → Import…` adds bookmarks from a file, with a preview dialog showing each bookmark and a per-row checkbox.
- Conflict resolution: on import, identical names produce a numbered suffix; identical positions are merged.
- A second action, `Tools → Bookmarks → Export All…`, writes every bookmark across every document the user has ever opened, useful for moving machines.

### 5.31 Trusted locations (Office-style)

- `Settings → Privacy → Trusted Locations` is a list of folders Quill opens without extra prompts.
- Files opened from outside trusted locations that are unusually large (default >25 MB), password-protected, or in a Grade B/C format show a one-time prompt: `Open <path>?` with Open, Open and Trust this folder, Cancel.
- Network-mounted folders are never auto-trusted; a setting must enable them explicitly.
- The trusted locations list is editable, exportable, and importable.

### 5.32 Jump List and shell integration

- Windows Taskbar Jump List shows Recent Files (last 10) and Pinned Files; Tasks include `New Document`, `Open File…`, and `Open from URL…`.
- Implementation via `pywin32`'s `ICustomDestinationList`.
- Shell context menu entries (registered from `Settings → Files`):
  - `Open with Quill` for every registered extension.
  - `Open with Quill (As Plain Text)` for every text-like extension, forcing the plain-text reader regardless of detected format.
  - **Open Folder With Quill** is deferred to v1.1 (it implies a folder-tree panel).
- All shell verbs install per-user (no admin elevation required) and uninstall cleanly.

### 5.33 Diagnostics and bug reporting

- `Help → Report a Bug…` is the unified support flow. It opens an in-app review screen with the report summary and destination URL, supports optional diagnostics zip generation, copies the environment summary to the clipboard, and then opens a pre-filled Community Access support-hub issue form in the default browser with no logs; the user reviews and submits manually.
- `Help → Save Diagnostics…` remains available for standalone diagnostics export and writes a zip with:
  - the last 7 days of logs (action names and outcomes only; no document content),
  - settings (with API keys redacted),
  - the active keymap,
  - the last 50 commands executed,
  - the screen-reader detection result and version (if available),
  - basic environment info (Windows build, Python build, wxPython build, locale).
- Nothing leaves the machine. The user chooses where to save the zip and what to do with it.

### 5.34 Welcome and Keyboard Reference

- **Welcome** opens a tutorial document in a new tab that walks new users through the editor, command palette, outline navigator, find/F3, spell check, and accessibility audit. The document is editable; users can save their own annotated copy.
- **Keyboard Reference** is auto-generated from the current keymap and opens as a Markdown document in the editor. It is grouped by menu, includes the "when" context for each binding, and updates the next time the user opens it after any rebind. Because it is just a document, users can search it with Find, jump with the Outline Navigator, and print it.
- **Tip of the Day** is off by default; when on, it appears once per launch as a small dismissible dialog with a single tip drawn from real palette actions, each tip a one-liner with a `Try it` button that runs the action.

### 5.35 Notifications centre

- The status bar's **Notifications** cell holds Quill's announcements: available updates, recovered autosave snapshots offered on launch, finished AI tasks, finished long-running OCR or extraction jobs, and any plugin messages.
- `Enter` on the cell opens a small Notifications dialog (stock `wx.ListBox` with timestamps); Delete dismisses individual entries; `Shift+Delete` dismisses all.
- Quill never raises toast or balloon notifications. All asynchronous events surface here and on the status bar's Background Tasks cell.

### 5.36 "What changed on save" (opt-in)

- Off by default. When on (`Settings → Reading → Announce save summary`), every successful save announces a one-liner: `Saved chapter-7.md, 4 lines changed, 38 words added`.
- Computed by diffing the previous saved bytes against the new bytes; cheap on documents up to 5 MB.
- Useful for ambient awareness during long editing sessions; trivially ignorable for users who prefer silence.

### 5.37 Link tools

A small family of related commands that make working with links comfortable for screen-reader users.

- **Insert link** (`Ctrl+K`): opens a small dialog with URL and display text fields. If a URL is on the clipboard, the URL field is pre-filled. If a selection exists, it becomes the display text. Enter inserts `[text](url)` in Markdown, `<a href="url">text</a>` in HTML, a plain URL in plain text, and a properly escaped link in reStructuredText, AsciiDoc, Org, and Textile. Cancel restores the cursor.
- **Insert quoted text** (`Ctrl+Shift+>`): indents the selection by one level of `>` for Markdown and email-style replies. `Ctrl+Shift+<` dedents one level. `Tools → Strip Quote Markers` removes them entirely. Idempotent: re-indenting a block already at level N goes to N+1, not back to 1.
- **Follow link** (`Ctrl+Enter`): when the cursor is on a Markdown link, HTML `href`, or a plain URL, opens it in the default browser. The status bar announces the destination host first (`Opening github.com…`) so the user always knows what they are about to open. Anchor links inside the current document jump in-editor instead.
- **Reveal link target** (`Ctrl+Shift+Enter`): announces the target without opening it (`Link target: https://example.com/path`).
- **Copy link target** (`Ctrl+Alt+K`): copies the URL of the link under the cursor.

### 5.38 Document properties and front-matter

- **Document properties dialog** (`File → Document Properties…`): edit document language (BCP-47 tag), title, author, description, keywords. For DOCX, EPUB, HTML, ODT these write into the document's metadata in place; for plain text, Markdown, reStructuredText, AsciiDoc, Org, and Typst they write into a sidecar `<filename>.quill.yml`. The document language drives the spell-check dictionary stack automatically.
- **Front-matter editor** (`Ctrl+Alt+F`): when the cursor is in or above YAML or TOML front-matter (Jekyll, Hugo, Zola, Quarto, Pandoc styles), opens a structured editor. Each key becomes a labelled `wx.StaticText` plus `wx.TextCtrl` pair. Save writes back as valid YAML or TOML, preserving comments and ordering wherever possible. New keys can be added; required keys (configurable per project) are highlighted.
- The front-matter editor recognises common keys (`title`, `date`, `author`, `tags`, `categories`, `draft`, `slug`, `description`, `lang`, `permalink`) and gives them sensible widgets (date picker for dates, multi-line for description, etc.). Unknown keys get a plain text field.

### 5.39 Autosave control and persistent undo

- **Autosave** is on by default at 30-second intervals. The status bar gains an **Autosave** cell showing `Autosave: 30 s` or `Autosave: off`. Enter cycles 15 s, 30 s, 60 s, 5 min, off. Settings dialog exposes the same plus a custom interval.
- **Persistent undo** keeps each document's undo stack alongside its autosave snapshots. Reopening a recently closed document restores up to 100 undo steps. Off by default for plain-text files larger than 5 MB. Stored in `%APPDATA%\Quill\undo\<hash>.undo`, atomically written, auto-pruned at 30 days.
- **Crash-safe autosave**: snapshots write to `…snap.tmp` and rename to `…snap` on flush so a power loss mid-write cannot corrupt the recovery store.

### 5.40 Paragraph, line, and footnote refinements

- **Join paragraph** (`Ctrl+Shift+J`): collapses a wrapped paragraph (the kind produced by plain-text email or older PDF extracts) into a single line, preserving sentence-internal spacing. Works on the current paragraph or selection. Idempotent.
- **Move line preserves selection**: `Alt+Up` / `Alt+Down` (line move, 5.18) keep the same logical selection range so the user does not lose context after moving.
- **Markdown heading auto-numbering** (`Tools → Toggle Heading Numbers`): adds `1.`, `1.1`, `1.1.1` prefixes across all headings, re-numbering in document order. Re-running removes them. Idempotent. Works in HTML, AsciiDoc, reStructuredText, Org, Typst as well.
- **Footnote helper**:
  - `Ctrl+Alt+. ` (period) inserts a Markdown footnote pair at the cursor and jumps the cursor into the definition block; pressing `Ctrl+Alt+.` again returns to the reference site.
  - `Tools → Renumber Footnotes` reorders footnote labels into document order (1, 2, 3…), updating both references and definitions.
  - The same command works for reStructuredText auto-numbered footnotes (`[#]_`) and Pandoc-style inline notes.

### 5.41 Search-and-replace preview and saved searches

- **Replace preview**: when a Replace All would change more than 25 occurrences (threshold configurable), Quill shows a preview dialog listing up to the first 50 changes with line numbers and before/after text. Buttons: Replace All, Cancel, Replace Selected (in case the user unticks rows). Always shows the total count.
- **Saved searches**: a search term plus its options (case, whole word, regex, in-selection) can be saved under a name via `Find → Save This Search…`. `Ctrl+Shift+F3` opens the saved-search picker (stock `wx.ListBox`); Enter runs it as if F3 had been pressed. Stored in `%APPDATA%\Quill\saved-searches.json`, exportable/importable.

### 5.42 Sort and transform details

`Tools → Sort Selected Lines…` and the related transforms (5.18) are spec'd here in full:

- Direction: ascending or descending.
- Case sensitivity: on or off.
- Numeric mode: lexicographic (`item10` before `item2`) or natural-numeric (`item2` before `item10`).
- Date-aware mode: parse leading ISO-8601 or `dd/mm/yyyy` dates; sort chronologically.
- Header row: preserved as the first line if checked.
- Stable sort always; equal lines preserve their relative order.
- Remove Duplicate Lines: optional "keep first" vs. "keep last"; reports `Removed 13 duplicate lines, 287 remain`.
- Reverse Lines: simple reverse, preserves blank lines.

### 5.43 Save All with conflict detection and per-file format memory

- **Save All** (`Ctrl+Alt+S` reserved; default is `Ctrl+Shift+Alt+S` so it doesn't clash with Document Statistics) saves every modified document. If the external watcher detects that one or more files changed on disk since they were opened, Save All opens a per-file resolution dialog: Keep Mine, Take Theirs, Open Diff. Defaults to Keep Mine with no destructive action until the user confirms.
- **Per-file format memory**: Quill remembers per-path the user's last choices for encoding, line endings, wrap, indent width, tabs-vs-spaces, and spell-check language. On reopening the file those settings are restored. Setting toggle: `Settings → Files → Remember per-file format choices` (on by default). Storage in `%APPDATA%\Quill\file-prefs.json`, keyed by SHA-1 of the path.

### 5.44 Per-document scratchpad

- `Ctrl+Alt+N` opens a small non-modal Scratchpad window tied to the current document. The Scratchpad is a second `wx.TextCtrl` with its own save and word count.
- Each scratchpad is persisted at `%APPDATA%\Quill\notes\<hash>.md` keyed by document path.
- When the underlying document is moved or renamed, Quill detects the orphan note next time the document is opened and offers `Re-attach note to current document?` (Yes / No / Show note).
- Scratchpads use the same spell-check stack as their parent document but are excluded from accessibility audits.

### 5.45 Section folding (announce-only)

A folding model designed for screen-reader users: folded ranges are summarised aloud and never visually hidden in a way that confuses the cursor.

- `Ctrl+Shift+[` folds the section starting at the heading on or above the current line into a single summary line: `Section "Background" — 14 lines hidden`.
- `Ctrl+Shift+]` unfolds the section at the cursor.
- `Ctrl+Shift+K Ctrl+Shift+0` folds all sections to a given level (chord sequence); `Ctrl+Shift+K Ctrl+Shift+J` unfolds all.
- Folding state is per-session and never written to file.
- Find still finds matches inside folded ranges and automatically unfolds on jump.
- Outline Navigator (5.16) is the primary navigation tool; folding is the in-editor companion.

### 5.46 Spell-check ignore directives and manual bilingual flag

- **Per-document ignore directives**. Quill honours a magic comment that lists words to ignore in this document only:
  - HTML / Markdown: `<!-- quill: ignore-spell "frobnicate", "wibble" -->`
  - Plain text and code (using the file's comment marker): `# quill: ignore-spell frobnicate, wibble`
  - YAML / TOML front-matter: `quill_ignore_spell: [frobnicate, wibble]`
- The ignore set is merged into the active dictionary stack as a transient per-document layer.
- **Manual bilingual paragraph flag** (`Ctrl+Alt+B`): toggles a per-paragraph language override. The user types or picks a BCP-47 tag; the paragraph is marked in the sidecar `.quill.yml`; the spell-check stack swaps for that paragraph. Per-paragraph auto-detection remains in the backlog; this manual flow is reliable today.

### 5.47 Word boundary mode, trailing whitespace, case-change announcement

- **Word boundary mode** (`Settings → Editing → Word Boundary Mode`):
  - **Default**: Unicode word breaks (UAX #29). Best for prose.
  - **Whitespace**: only whitespace separates words. Best for log files.
  - **Programmer**: also breaks on `_`, `-`, `.`, and case transitions (`getFoo` is three "words": `get`, `Foo`, plus the case boundary). Best for code.
- The mode affects `Ctrl+Left`/`Right`, `Ctrl+Delete`/`Backspace`, double-click selection, word count, and the spell-check tokeniser.
- **Trailing whitespace announcement**: when the cursor lands on a line that ends with trailing whitespace, the status bar's Line/Column cell appends `(trailing whitespace)` and a screen-reader-friendly hint is available via Where Am I. No visual highlight; no extra speech while typing.
- **Case-change announcement guard**: when `Ctrl+U`, `Ctrl+L`, or `Ctrl+Shift+T` apply to the whole document because nothing was selected, the announcement explicitly says so and reminds the user `Press Ctrl+Z to undo full-document case change`.

### 5.48 Multi-format export and reading view

- **Export panel** (`File → Export…`): one dialog with target format choices: HTML, DOCX, plain text, Markdown, reStructuredText, and PDF (via Markdown → HTML → system print-to-PDF). Per-format options inline (heading numbering, table-of-contents inclusion, embedded CSS yes/no, page size for PDF).
- **Reading view** (`View → Toggle Reading View`): toggles the editor between source view and a clean reading representation for HTML and Markdown. Still a `wx.TextCtrl` — same accessibility, just a different render: links unwrapped to `text (url)`, headings prefixed by their level, lists rendered with consistent markers, code blocks framed by a horizontal rule. Editing is disabled in reading view (the cell announces this); toggle off to edit.

### 5.49 Welcome-back snapshot

- On launch, if the user closed Quill cleanly with N documents open last time, a single prompt offers `Reopen the 3 documents from your last session?` with Yes / No / Show me.
- "Show me" opens a small list of the documents (paths, last cursor positions) and lets the user pick a subset.
- Always opt-in per launch; the global "restore session" setting is separate and stays off by default.

### 5.50 Per-document keymap override (with explicit consent)

- A document's sidecar `.quill.yml` may declare a `keymap_override` block.
- Quill never applies it silently. On opening such a document, the user sees a one-time confirmation: `This document requests a different keymap. Apply for this document only?` with Yes / No / Always for this document. The decision is remembered per-document path.
- Overrides are scoped: they only apply while the document has focus, never global.
- A small lock icon appears in the document name status-bar cell (announced as `keymap override active`) whenever an override is in effect.

### 5.51 Settings export, import, and partitioned reset

- `Settings → Export…` writes a single zip containing settings, keymap, templates, snippets, personal dictionary, saved searches, and bookmarks. API keys are excluded; the user is told so explicitly in the dialog.
- `Settings → Import…` previews every change in a stock `wx.ListBox` and requires Enter to commit. Conflicts (e.g. a keymap rebind that contradicts the current keymap) are flagged inline.
- `Settings → Reset to Defaults…` opens a partitioned reset dialog with checkboxes for: Keymap, Appearance, Spell-check learning, Templates and snippets, Recent files, Bookmarks, Everything. Never silent; every reset shows a confirmation listing what will be lost.

### 5.52 Document fingerprint

- Every saved document has a SHA-256 fingerprint of its bytes shown in `File → Document Properties…` and copyable from a button.
- Useful for accessibility certification workflows where the user must prove they reviewed a specific version, and for forensic comparison.
- The fingerprint also surfaces in the diagnostics bundle (5.33) for any open document, scrubbed of path.

### 5.53 Unicode insert

- `Ctrl+Alt+U` opens a search dialog over the Unicode name database (`unicodedata` from the standard library). Type any part of a character name; matching characters appear in a stock `wx.ListBox` with code point, name, and the literal character.
- Categories shown as one-line filters: Letters, Marks, Numbers, Punctuation, Symbols, Separators, Other. Click or type the category prefix to scope.
- Pinned favourites for common needs: em-dash, en-dash, ellipsis, smart quotes, currency symbols, mathematical operators.
- Recent characters list keeps the last 20.

### 5.54 Idle-time prefetch

- When the user opens a file from a folder, Quill background-extracts the next and previous files alphabetically into the in-memory document cache so opening them feels instant.
- Bounded by available memory and by a hard cap of 50 MB total prefetch.
- Cancelled immediately on any other extraction or AI task.
- Opt-out switch in `Settings → General → Prefetch neighbouring files`.

### 5.55 Atomic on-disk stores

- All Quill-managed JSON stores (bookmarks, settings, keymap, recent, saved searches, file prefs, notes index) write to `<store>.tmp` and rename atomically.
- A `<store>.bak` is kept of the last good version. On startup, if the primary store fails to parse, Quill renames it to `<store>.broken-<timestamp>.json`, falls back to the `.bak`, and announces `Recovered <store> from backup`.
- This eliminates the worst class of "my bookmarks vanished after a crash" bugs.

### 5.56 First-run onboarding

A five-step welcome flow the first time Quill launches. Each step is a normal modal page (no carousel, no animation). Skip is always available; the chosen values are written through the same Settings code path as any later change.

1. **Profile**: System, Word-like, Vim, Emacs.
2. **Theme**: System, Light, Dark, High Contrast.
3. **Spell-check languages**: multi-select from the bundled launch set; the active document language is added automatically when later opened.
4. **AI provider**: Off (default), OpenAI, Azure OpenAI, Anthropic, Ollama. If a provider is picked, the API-key dialog opens; the key is stored via DPAPI (10.11). Network is never used without explicit per-action consent.
5. **Telemetry**: confirms it stays off (default). A short plain-language sentence explains what telemetry would collect if turned on later.

The onboarding completion writes `%APPDATA%\Quill\onboarding-complete.json`. Re-running `Help → Run Onboarding Again` reopens the flow without resetting anything else.

### 5.57 Privacy summary

- A single-screen plain-language statement of what Quill does and does not send over the network. Linked from `Help → Privacy Summary` and shown once during onboarding.
- Content is audited by the cognitive-accessibility plain-language linter (9.8): Flesch ≥ 60, controlled vocabulary, one idea per sentence.
- Says explicitly: documents never leave the machine without an explicit per-action confirmation; the only outbound calls v1.0 makes without confirmation are the manual update check and the optional crash-report upload (5.71), both opt-in.

### 5.58 Licenses screen

- `Help → Licenses` opens `THIRD-PARTY-NOTICES.md` (auto-generated at build time, 10.2.4) in the editor.
- The file lists every bundled component, its version, its license text, and a one-line use justification.
- Required for procurement; required by some bundled licenses.

### 5.59 Crash recovery transparency

When Quill detects an autosave snapshot newer than the on-disk file on launch:

- The recovery dialog names the file, the snapshot timestamp, the byte count, and offers four actions: **Recover**, **Compare with on-disk**, **Discard snapshot**, **Cancel** (decide later).
- **Compare with on-disk** opens the diff view (5.22) immediately.
- The dialog is screen-reader-friendly first: every value is a separate labelled `wx.StaticText` so it reads cleanly.
- Choosing Recover writes the snapshot as a new unsaved document; the on-disk file is **never** overwritten without an explicit Save.

### 5.60 Read-only document mode

- `View → Read-Only Mode` (`Ctrl+Shift+L` by default) toggles the editor's editability without touching file permissions.
- Toggle state is per-document; announced when toggled (`Read-only mode on` / `off`).
- Status bar's **Modified state** cell shows `Read-only` while on; attempts to type are silently ignored and a single discreet announcement (`Editor is read-only; press Ctrl+Shift+L to allow editing`) fires the first time per session.
- All navigation, Find, Outline, Read Aloud, Statistics, and Accessibility Audit continue to work.

### 5.61 File-related menu helpers

- `File → Reveal in File Explorer` opens Explorer with the current file selected.
- `File → Copy Full Path`, `File → Copy File Name` copy the corresponding string to the clipboard with a confirmation announcement.
- `File → Show Containing Folder in Quill` is deferred to v1.1 (depends on the folder panel).

### 5.62 Open Recent enhancements

- `File → Open Recent` includes per-entry **Pin / Unpin** and a top-level **Open All Pinned** action.
- Pinned items are not subject to the recent-list cap (default 10) and appear at the top of the submenu.
- Pinned entries are persisted in `recent.json` and survive Clear Recent (which only clears unpinned entries).

### 5.63 Document timeline

- `Tools → Document Timeline…` opens a chronological list (stock `wx.ListBox`) of every backup and autosave snapshot for the current document, with timestamp, size, and source (save backup vs. autosave snapshot).
- Each row has **Open in new tab**, **Compare with current**, and **Restore** (with confirmation) actions.
- The backing store already exists (5.13 + 5.39); this is the unified UI on top.
- Per-document, never global.

### 5.64 Sentence and paragraph navigation

- `Ctrl+Up` / `Ctrl+Down` already navigate by paragraph (standard wx behaviour).
- `Alt+Right` / `Alt+Left` move to the next / previous **sentence** and announce the sentence text (truncated to 200 characters around the cursor for braille and speech).
- Sentence detection uses the `regex` Unicode word-boundary tables plus a per-language abbreviation list (`Mr.`, `Dr.`, `e.g.`, etc.) that ships with each Hunspell language pack and is user-extendable in Settings.
- `Ctrl+Shift+Alt+Right` / `Ctrl+Shift+Alt+Left` extend the selection by sentence.

### 5.65 Word-count goal per document

- `File → Document Properties…` gains a **Word goal** integer field (0 disables).
- The status bar's **Word count** cell appends `(243 of 1500)` when a goal is set; on crossing the threshold Quill announces `Word goal reached: 1500 words`.
- The goal is stored alongside other metadata in the document container or in the `.quill.yml` sidecar.

### 5.66 Reading position memory per document

- On close, Quill records cursor line/column and scroll offset for the current document.
- On reopen, the cursor is restored; the status bar announces `Restored to line N` on first focus into the editor.
- Storage keyed by the document's path SHA-1 in `file-prefs.json` (10.5).
- Setting toggle `Settings → Editing → Restore reading position` (on by default).
- Independent of Welcome-Back snapshot (5.49); works even when only a single document is opened directly from Explorer.

### 5.67 Compare with clipboard

- `Tools → Compare With Clipboard` runs the unified-diff machinery (5.22) with the current document as `before` and the clipboard contents as `after`.
- Useful when reviewing a single suggestion pasted from chat or email.
- Refuses if the clipboard is empty or larger than 5 MB; explains why.

### 5.68 Insert from file

- `File → Insert From File…` inserts another file's text at the current cursor without opening it as a separate document.
- Uses the same format detection as Open; for non-text formats Quill extracts plain text and confirms before inserting.
- Files over 1 MB show a confirmation dialog with the byte count and the first line of content.

### 5.69 Selection-statistics direct shortcut

- `Ctrl+Alt+Shift+S` runs Document Statistics scoped to the current selection without first opening the full-document dialog.
- Same dialog as 5.19 but with the title prefixed `Statistics — Selection`.
- Reassignable like any other binding.

### 5.70 Audio cue catalogue (opt-in)

- A small set of subtle, brief, screen-reader-respectful audio cues. Off by default; settings live in `Settings → Sounds`.
- Catalogue (v1.0):
  - **Save success** — 80 ms soft click at 600 Hz.
  - **Save failure** — 120 ms low descending pair.
  - **Find: no match** — 100 ms muted tick at 400 Hz.
  - **Autosave snapshot taken** — 60 ms whisper at 800 Hz (the quietest cue).
  - **Background task complete** — 120 ms two-tone chime.
- All cues are ≤ 120 ms, share a single low-default volume slider, and **duck** automatically while a screen reader is speaking (detected via the SR detection layer, 10.1).
- Cues are PCM data bundled with the app, played via `winsound.PlaySound` with `SND_ASYNC | SND_MEMORY` so they never block.
- Per-cue on/off in Settings.

### 5.71 Quiet mode

- `View → Quiet Mode` (`Ctrl+Alt+Q` by default) is a single toggle that:
  - hides the status bar (still reachable via F6 announcement only),
  - suppresses non-critical announcements (autosave summary, idle-prefetch chatter, Tip of the Day),
  - sets audio cues volume to zero for the session,
  - leaves all critical announcements intact (errors, save failures, AI completion).
- Announced on toggle (`Quiet mode on` / `off`).
- Useful for high-focus writing sessions; state is per-session and not persisted.

### 5.72 Temporary trust for untrusted-location opens

- The Trusted Locations prompt (5.31) gains a third button: **Open this time only**.
- The file opens; the folder is **not** added to trusted locations.
- Useful for one-off opens from Downloads or temp folders without expanding the trust footprint.

### 5.73 Settings search

- A search field at the top of the Settings dialog (`Ctrl+F` when focus is in Settings).
- Indexes setting key, label, description, and a synonym list maintained alongside each setting.
- As the user types, the tree filters to matching settings; the first match is announced.
- `Esc` clears the filter; `Tab` moves to the tree.
- The synonym list is gettext-translated alongside labels.

### 5.74 In-app changelog and update transparency

- `Help → Release Notes` opens a Markdown document with one section per version. Auto-generated from `CHANGELOG.md` at build time.
- The manual update dialog (5.34, 10.12) links to the release notes for the version it is offering.
- Past release notes remain reachable through the document's own outline (5.16).

### 5.75 Crash-report opt-in (per recovery)

- When Quill recovers from a crash, the recovery dialog includes an opt-in checkbox: **Send crash details to the Quill team (no document content)**.
- If checked, the diagnostics bundle (5.33) is uploaded over HTTPS to a host shown explicitly in the dialog before send; the upload is cancellable and shows a progress announcement.
- Off by default; the choice is **remembered per recovery session only**, never globally — this prevents accidental long-term opt-in.
- Crash reports include logs, environment, and the last 50 commands, never document content or API keys.

### 5.76 Interactive compare mode

Quill provides two complementary comparison workflows: an accessible interactive compare session and a generated diff report.

- **Compare commands**: `Tools → Compare Documents…`, `Tools → Compare With File…`, `Tools → Compare Open Documents…`, `Tools → Compare Selection With Clipboard`, plus `Tools → Compare Options…`.
- **Core navigation**: `F8` next difference, `Shift+F8` previous difference, `Ctrl+F8` announce current difference, `Alt+F8` open Difference List, `Ctrl+Alt+F8` toggle synchronized compare navigation.
- **Interactive session**: focus stays in the active editor; moving to a difference places the cursor on the changed line and announces both sides in plain language.
- **Difference List**: a stock list control containing all differences with document names, line numbers, type, and a short preview; Enter jumps to the selected difference.
- **Compare options**: ignore leading/trailing spaces, all whitespace, blank lines, line endings, case, punctuation, repeated spaces, Markdown heading markers, HTML tag differences, and normalized Unicode.
- **Difference summary**: users may create a plain-text summary document listing all differences, options used, and short before/after excerpts.
- **Diff report**: Quill may also generate a unified-diff document in a new editor tab. Diff hunks remain navigable with `Ctrl+]` and `Ctrl+[`.
- **Extracted document compare**: PDF, DOCX, EPUB, OCR, and repaired text compare against Quill’s extracted text representation, with a warning that extraction quality may affect results.
- **Feature profiles**: interactive compare is on in Writer, Reader and Student, Office and Admin, Accessibility Professional, Developer and Power Text, and Full Quill; it is quiet in Essential.

---

## 6. Spell checking deep dive

### 6.1 The TinySpell question

TinySpell is a small, fast Windows spell-checker that watches the clipboard or current input field and alerts on misspellings. It is genuinely useful for many users. So the question is: should Quill integrate tightly with TinySpell, or build its own engine?

We have chosen to **build our own engine**, tightly integrated into Quill, for the following reasons:

1. **Screen-reader fidelity.** TinySpell speaks through its own UI surfaces and conventions. Quill needs total control over how misspellings are announced, navigated, and corrected so that NVDA, JAWS, and Narrator hear the same predictable patterns. A loose integration would create a second source of speech that competes with our own.
2. **Document context.** TinySpell works across applications and therefore cannot use document-level context (heading structure, surrounding paragraph, language metadata, per-document dictionary). Quill knows exactly what document the cursor is in and can do much better.
3. **Per-document and per-paragraph language detection.** Multi-language documents need language switches mid-stream. An external tool will not know.
4. **Suggestion ranking that learns.** TinySpell's suggestion order is fixed. Quill ranks suggestions using the user's own writing and the surrounding sentence, which is the single biggest quality-of-life upgrade in modern spell check.
5. **Offline guarantee.** Quill commits to spell check working with zero network. An external dependency complicates that guarantee.
6. **Distribution.** Bundling TinySpell would create a licence and update story we do not control.
7. **Keymap and palette parity.** Every Quill action is in the palette and reassignable. Spell-check commands must be too.

We will, however, ship a small **TinySpell interop plugin** for v1.1 for users who already rely on TinySpell elsewhere and want a unified personal dictionary. That plugin imports/exports the personal dictionary file and otherwise stays out of the way.

### 6.2 Engine architecture: "Quill Spell"

Quill Spell is a layered local engine:

- **Layer 1: Tokeniser.** Unicode-aware word splitter that understands code (CamelCase, snake_case, kebab-case), contractions, hyphenation, URLs, emoji, file paths, and Markdown/HTML syntax tokens. It hands the next layer a stream of `(word, span, context_kind)` tuples where `context_kind` is one of `prose`, `code`, `identifier`, `url`, `markup`, `path`.
- **Layer 2: Dictionary stack.** A priority-ordered stack of dictionaries: per-document, per-project (if applicable), user personal, language-base (Hunspell), plus optional jargon packs (medical, legal, technical, scientific). The first dictionary that accepts the word wins.
- **Layer 3: Hunspell backend.** Bundled via `cyhunspell`. Dictionaries shipped: en-US, en-GB, en-CA, en-AU, es-ES, es-MX, fr-FR, de-DE, pt-BR, pl-PL, ja-JP (with MeCab). Others available via a one-click downloader.
- **Layer 4: Suggestion engine.** Combines Hunspell's edit-distance suggestions with a character-level n-gram model and a small contextual reranker (a tiny on-device transformer; runs on CPU in <10 ms per call). Top 5 suggestions, ranked by combined score.
- **Layer 5: Learning loop.** When the user accepts a suggestion, the engine increments its frequency. When the user adds a word, it goes to the appropriate dictionary (with a prompt asking which). When the user repeatedly rejects a suggestion in favour of another, the reranker learns the preference. Learning is 100 percent local and resettable.
- **Layer 6: Context awareness.** The tokeniser tells the engine when it is inside a code fence, an inline code span, a URL, or a Markdown link target. Those regions are skipped by default. Settings let the user enable code spell checking with a programming-aware dictionary.

### 6.3 User experience

- **Status indicator.** The status bar shows the active dictionary stack as a short label, for example `en-GB + tech + personal`.
- **F7 full review.** Modal Spell Check dialog with: misspelled word, surrounding sentence with the word highlighted and announced, suggestions list, replacement edit, Change, Change All, Ignore, Ignore All, Add to (with submenu for which dictionary), Finish, Cancel. The word is spoken and then spelled letter by letter.
- **Ctrl+; quick fix.** Jumps to the next misspelling, opens a small modal list of the top 5 suggestions. Numbers 1 through 5 accept the corresponding suggestion. Enter accepts the highlighted one. `A` adds to dictionary. `I` ignores once. `Esc` cancels.
- **Background pass.** A debounced background tokenise runs as the user types. Results live in a sidecar model. No visual squiggles. The screen reader is never interrupted by background work.
- **Mode toggle.** `Alt+F7` toggles as-you-type checking for the current document.
- **Per-document language.** A YAML-style sidecar (`<doc>.quill.yml`) can pin language and dictionaries. Detected automatically from a magic comment on the first line if present.
- **Magic touches.**
  - When you add a word, Quill says "Added <word> to your personal dictionary" or "Added <word> to this document's dictionary" so you always know where it went.
  - When you reject the same suggestion three times for the same misspelling, Quill quietly asks once whether you want to add the rejected word to your personal dictionary.
  - When pasting a large block of text, the spell pass is queued at a lower priority so the paste itself is instant.
  - When entering a code fence in Markdown, the engine switches automatically to identifier mode and stops complaining about variable names.

---

## 7. Command palette deep dive

The command palette is modelled directly on Visual Studio Code's, adapted for screen readers.

### 7.1 Opening and dismissing

- `Ctrl+Shift+P` opens the palette in command mode.
- `F1` does the same.
- Each prefix shortcut (below) opens the palette pre-seeded with that prefix.
- `Esc` closes without action.
- `Enter` runs the selected entry (and remembers it).
- `Tab` from the input moves into the list. `Shift+Tab` returns to the input.

### 7.2 Prefix modes

A single edit field, one list. The first character of the input may be a mode prefix:

| Prefix | Shortcut to open directly | Meaning |
| --- | --- | --- |
| (none) or `>` | `Ctrl+Shift+P` | Run a command |
| `?` | `Ctrl+Shift+?` | Show help for all prefixes |
| `:` | `Ctrl+G` (when no page markers) | Go to line |
| `@` | `Ctrl+R` | Jump to bookmark in current document |
| `#` | `Ctrl+T` | Jump to bookmark across all open documents |
| `!` | `Ctrl+Shift+M` | Show issues (spell check, bookmark, format) |
| `<` | `Ctrl+E` | Open a recent file |
| `~` | `Ctrl+Shift+O` | Switch open document |
| `=` | (palette only) | Open a setting |

These prefixes are themselves reassignable (see [section 8](#8-keymap-and-keystroke-reassignment)).

### 7.3 Matching

- Fuzzy subsequence match across the visible label.
- Each match scored by: subsequence tightness, prefix bonus, word-boundary bonus, recency, frequency.
- Top 100 results displayed, lazily.
- Ties broken alphabetically.

### 7.4 Rows

Each row in command mode shows three regions, all announced as one string by the screen reader (with internal punctuation chosen to read well):

```
<Command title> — <current keybinding or "unassigned"> — <source>
```

For example:

```
Improve Reading Order with AI — unassigned — Quill
Spell Check Document — F7 — Quill
Find Next — F3 — Quill
Pandoc: Convert to DOCX — Ctrl+Alt+P — Plugin: Pandoc Bridge
```

### 7.5 Inline keybinding edit

While the palette is open and a command is highlighted:

- `Right Arrow` enters keybinding edit mode for that command.
- A small inline edit prompt says "Press the new shortcut, or Escape to cancel, or Delete to unassign."
- The next keystroke (chord or sequence) becomes the binding.
- Conflicts are detected immediately and announced (see [section 8.4](#84-conflict-handling)).
- `Enter` commits, `Esc` cancels.

### 7.6 Recently used and pinned

- The most recently run 10 commands always appear at the top when the palette opens fresh, before any typing.
- Users can pin commands with `Shift+Enter` from the palette. Pinned commands always appear above recents.

### 7.7 Help

- `?` plus Enter, or `Ctrl+Shift+?`, shows a "How to use the Command Palette" topic in the palette itself: a list of prefixes, their meanings, and their shortcuts, each line runnable with Enter to invoke an example.
- Where Am I (`Ctrl+Shift+I`) in the palette announces: current mode, number of matches, selected entry, current binding.

### 7.8 Accessibility specifics

- The palette is a non-modal top-level `wx.Frame` over the main window with focus capture. Underlying widgets are a `wx.SearchCtrl` and a `wx.ListBox`. Both are stock controls, so all screen readers get correct announcements without scripts.
- Each list update fires a single accessibility event with the count of results; we do not spam announcements as the user types.
- Live region is set on the help/result line below the list for status messages such as "Keybinding updated" and "Conflict with Find Next."

---

## 8. Keymap and keystroke reassignment

Every Quill action is identified by a stable command id (`quill.editor.save`, `quill.palette.open`, `quill.spell.checkDocument`, etc.) and may have zero, one, or many keybindings.

### 8.1 Where keystrokes live

Three layers, in priority order:

1. **User keymap** (`%APPDATA%\Quill\keymap.json`). User edits win.
2. **Profile keymap** (optional, shipped alternatives). For example, "Word-like", "Vim-friendly", "Emacs-friendly". The user picks one as the base.
3. **Default keymap** (built into Quill).

The effective keymap is the merge of these three, with user > profile > default.

### 8.2 Keyboard settings page

`Ctrl+,` then "Keyboard" (or palette `=keyboard`).

The page contains:

- A **profile selector**: System (defaults), Word-like, Vim-friendly, Emacs-friendly, Custom.
- A **search field** that filters the table below.
- A **bindings table** (`wx.ListCtrl` in report mode, fully accessible) with columns:
  - Command title
  - When (context: editor, palette, dialog, global)
  - Keybinding
  - Source (default, profile, user)
  - Conflicts (a short marker if any)
- **Buttons**: Add, Change, Remove, Reset to default, Reset all to profile, Import, Export.
- A **"Press a key" capture field** for visual users who want to find what a chord does today.

### 8.3 Editing a single binding

Three equivalent ways:

1. From the command palette: highlight a command and press `Right Arrow`.
2. From the Keyboard settings page: select the row and press `Change` (or `Enter`).
3. From the menu bar: every menu item has a context-menu entry "Change keybinding".

In all three, the same small "Press the new shortcut" capture dialog appears. It:

- Captures any chord or two-key sequence (VS Code style, e.g. `Ctrl+K Ctrl+S`).
- Announces the captured keystroke as it is built.
- Refuses to capture purely modifier keys.
- Refuses to capture keystrokes reserved by the OS or by the active screen reader (NVDA, JAWS, Narrator) and explains which one it conflicts with.

### 8.4 Conflict handling

When a keystroke is already used:

- The dialog announces the conflict: "Ctrl+G is currently used by Go To Line in editor context."
- Three choices, each on its own button: **Replace** (the old command becomes unbound and the new one is bound), **Add** (both commands have this binding; the active "when" context disambiguates), **Cancel**.
- "Add" is only offered when contexts are distinct. Same-context dual binding is not allowed for safety.

### 8.5 "When" contexts

Each command declares which contexts it is valid in:

- `editor` — focus is in the main editor.
- `palette` — focus is in the command palette.
- `dialog` — focus is in any Quill dialog.
- `global` — anywhere in the app.
- `format:md` — editor focus, current document is Markdown.
- `format:pdf` — editor focus, current document was extracted from PDF.
- `selection` — there is a non-empty selection.

Contexts can be combined with `&&` in advanced editing.

### 8.6 Profiles in detail

- **System**: clean, modern Windows conventions (default).
- **Word-like**: brings Quill close to Microsoft Word for users migrating from there.
- **Vim-friendly**: a modal layer overlaid via plugin, off by default in the profile selector but available to install.
- **Emacs-friendly**: chord-heavy bindings (`Ctrl+X Ctrl+S` etc.), again via the chord engine.

### 8.7 Storage format

`keymap.json` is plain JSON, human readable, version controlled friendly:

```json
{
  "version": 1,
  "profile": "System",
  "bindings": [
    { "command": "quill.editor.save", "key": "Ctrl+S", "when": "editor" },
    { "command": "quill.palette.open", "key": "Ctrl+Shift+P", "when": "global" },
    { "command": "quill.spell.checkDocument", "key": "F7", "when": "editor" },
    { "command": "quill.editor.gotoLine", "key": "Ctrl+G", "when": "editor && !format:pdf" }
  ]
}
```

### 8.8 Import, export, sync

- Export the active keymap to a single JSON file.
- Import from a file (with a preview dialog showing every change).
- Sync via a user-chosen folder (OneDrive, Dropbox, Syncthing). Quill watches the file and reloads on change, announcing "Keymap reloaded from disk."

### 8.9 Safety net

- A "Reset all keybindings" button exists at the bottom of the Keyboard settings page.
- Recovery: if `keymap.json` is corrupt, Quill renames it to `keymap.broken-<timestamp>.json` and falls back to defaults, announcing what happened.

---

## 9. Accessibility, WCAG 2.2 AA conformance, and certification

Accessibility is not a feature set; it is the product's contract with its users. This section is the canonical reference for what "accessible" means for Quill, how it is engineered, how it is tested, how regressions are caught, and how a Voluntary Product Accessibility Template (VPAT) Accessibility Conformance Report (ACR) is generated for procurement.

### 9.1 Compliance posture and target standards

Quill targets the following standards in full at v1.0 release:

- **WCAG 2.2 Level AA** (W3C Recommendation, October 2023). All Level A and AA Success Criteria that apply to a native desktop application are conformed to.
- **WCAG 2.2 Level AAA** for criteria reasonably achievable in a text editor (contrast 7:1 in High Contrast theme; reading-level alternatives; consistent help).
- **US Section 508** (revised 2018 ICT Refresh, which incorporates WCAG 2.0 AA). Conformance is established by demonstrating WCAG 2.2 AA conformance, which is a superset.
- **EN 301 549 v3.2.1** (European harmonised standard, including chapters 5, 6, 7, 9, 11, and 12 as applicable).
- **ARIA 1.2 / WAI-ARIA Authoring Practices** patterns are honoured wherever Quill exposes ARIA-equivalent semantics through MSAA/UIA (combobox patterns for the palette, treeview patterns for the Outline Navigator, listbox patterns for issue panels).
- **Microsoft's Accessibility Insights for Windows** baseline (every CI build is run through Accessibility Insights and must produce zero errors and zero warnings on covered axes).

### 9.2 Conformance posture statement (will appear in the ACR)

> Quill 1.0 **supports** WCAG 2.2 Level A and Level AA across all functionality intended for end users. It **partially supports** Level AAA criteria 1.4.6 (Contrast Enhanced) and 2.4.10 (Section Headings). Quill does not include audio-only or video-only media; criteria specific to such media are **not applicable**.

### 9.3 WCAG 2.2 AA conformance matrix

The following matrix lists every Level A and AA Success Criterion, how Quill meets it, and where it is tested. Each row is a contract: a CI test exists for every “Tested by” entry, and a regression fails the build.

#### Principle 1: Perceivable

| SC | Title | Level | How Quill meets it | Tested by |
| --- | --- | --- | --- | --- |
| 1.1.1 | Non-text Content | A | Every icon-bearing button has a `wx.Window.SetName`/`SetHelpText` pair; the Accessibility Auditor (5.20) requires alt text on every image in user documents | UI a11y harness; auditor unit tests |
| 1.2.x | Time-based Media | A/AA | Not applicable; Quill ships no audio/video | n/a |
| 1.3.1 | Info and Relationships | A | Every label is associated with its control via parent-sizer convention plus explicit `SetLabel`; menu structure is exposed as MSAA tree; status-bar cells expose name+role+value+description | UI a11y harness verifies MSAA tree; snapshot tests |
| 1.3.2 | Meaningful Sequence | A | Tab order is explicit and deterministic per dialog; tested with `pywinauto` walking each dialog | Tab-order snapshot tests |
| 1.3.3 | Sensory Characteristics | A | No instruction uses shape, position, sound, or colour alone; all hints are text in tooltips and Where Am I | Manual checklist; copy review |
| 1.3.4 | Orientation | AA | Window orientation is user-controlled; no orientation lock | n/a (desktop) |
| 1.3.5 | Identify Input Purpose | AA | Settings fields use semantic `name` attributes mappable to autofill purposes where the OS supports them | Settings inventory |
| 1.4.1 | Use of Colour | A | Modified state is text (`[modified]`), not colour; issue severity uses prefix words (`Error:`, `Warning:`); diff hunks use `+`/`-` prefixes | Theme tests; copy review |
| 1.4.2 | Audio Control | A | Read Aloud has explicit start/pause/stop and a status cell; can be silenced at any time without affecting the SR | Manual + UI test |
| 1.4.3 | Contrast (Minimum) | AA | All bundled themes meet 4.5:1 for normal text, 3:1 for large text and UI components; verified by an automated contrast checker run against every theme | Contrast CI job |
| 1.4.4 | Resize Text | AA | Editor font 10–48pt via `Ctrl++`/`Ctrl+-`/`Ctrl+0`; dialog text scales with Windows DPI (100–400%) without loss of function or clipping | DPI smoke tests at 100/125/150/175/200/300/400 |
| 1.4.5 | Images of Text | AA | Quill never renders text as an image; all UI text is real text in stock controls | n/a |
| 1.4.10 | Reflow | AA | Window contents reflow to 320 CSS px equivalent (320 device-independent pixels); status-bar cells overflow into a roll-up; menu falls back to compact mode | Reflow tests at minimum window size |
| 1.4.11 | Non-text Contrast | AA | All UI components and graphical objects (focus rings, status-bar separators, toggle states) meet 3:1 against adjacent colours | Contrast CI job covers component states |
| 1.4.12 | Text Spacing | AA | Editor honours user spacing overrides (line height up to 1.5x, paragraph spacing up to 2x font size, letter spacing up to 0.12em, word spacing up to 0.16em) without truncation or overlap | Spacing test fixture |
| 1.4.13 | Content on Hover or Focus | AA | Tooltips are dismissible (Esc), hoverable, and persist until input moves away | Hover tests |

#### Principle 2: Operable

| SC | Title | Level | How Quill meets it | Tested by |
| --- | --- | --- | --- | --- |
| 2.1.1 | Keyboard | A | Every action is reachable from the keyboard; drag-and-drop is explicitly omitted from required flows | Keyboard parity matrix test |
| 2.1.2 | No Keyboard Trap | A | Every dialog has an Escape route; F6 cycles regions; modal dialogs have an explicit Cancel | Trap detection in pywinauto suite |
| 2.1.4 | Character Key Shortcuts | A | Single-character shortcuts (like F3) are bound only to commands that re-fire safely; users can rebind all of them; no single-letter shortcuts in editor focus | Keymap audit |
| 2.2.1 | Timing Adjustable | A | The only time-bound interaction is read-aloud, which the user controls; no idle timeouts in v1.0 | Manual review |
| 2.2.2 | Pause, Stop, Hide | A | Read Aloud has Pause/Stop; the only moving thing in the UI is a progress indicator that the user can cancel | Manual review |
| 2.3.1 | Three Flashes or Below Threshold | A | Quill has no flashing UI | n/a |
| 2.4.1 | Bypass Blocks | A | F6 region cycling, command palette, outline navigator | Navigation tests |
| 2.4.2 | Page Titled | A | Window title always identifies the active document and Quill | Title test |
| 2.4.3 | Focus Order | A | Focus order matches reading order; no surprise focus jumps; recent locations history surfaces movement | Tab-order snapshot tests |
| 2.4.4 | Link Purpose (In Context) | A | Insert Link dialog enforces meaningful display text; auditor flags generic link text | Auditor tests |
| 2.4.5 | Multiple Ways | AA | Outline Navigator, command palette `@`/`#`/`<`/`~`, Find, menu Navigate submenu | Navigation tests |
| 2.4.6 | Headings and Labels | AA | Settings tree and dialog sections use descriptive headings; auditor requires the same in user docs | Copy review; auditor tests |
| 2.4.7 | Focus Visible | AA | Native Windows focus indicators are preserved (no custom drawn focus); High Contrast theme amplifies the system focus ring | Focus visibility audit |
| 2.4.11 | Focus Not Obscured (Minimum) | AA (new in 2.2) | Quill does not float overlays that obscure focus; the palette and modal dialogs receive focus and are larger than the focused control | Focus-not-obscured check |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA | Same as 2.4.11; Quill conforms by construction | (auto) |
| 2.4.13 | Focus Appearance | AAA | Native Windows focus ring is honoured; High Contrast theme exceeds the 2px solid / 3:1 contrast target by relying on the OS focus rectangle | Manual verification |
| 2.5.1 | Pointer Gestures | A | No multi-point or path-based gestures required | n/a |
| 2.5.2 | Pointer Cancellation | A | Buttons activate on up-event; cancel by moving off before release | Native button behaviour |
| 2.5.3 | Label in Name | A | Accessible name begins with visible label text for every control | UI a11y harness |
| 2.5.4 | Motion Actuation | A | No motion-actuated functions | n/a |
| 2.5.7 | Dragging Movements | AA (new in 2.2) | No required drag; every drag-equivalent action has a keyboard alternative | Keyboard parity matrix |
| 2.5.8 | Target Size (Minimum) | AA (new in 2.2) | All clickable targets at least 24x24 CSS px including status-bar cells; verified per-theme | Layout tests |

#### Principle 3: Understandable

| SC | Title | Level | How Quill meets it | Tested by |
| --- | --- | --- | --- | --- |
| 3.1.1 | Language of Page | A | The application's UI language is declared via `wx.Locale` and exposed to MSAA | Locale tests |
| 3.1.2 | Language of Parts | AA | Per-document language metadata (5.38) and the spell-check language stack indicator (5.1b) expose document language to user and AT | Metadata tests |
| 3.2.1 | On Focus | A | Focus changes never trigger unexpected context changes | Focus tests |
| 3.2.2 | On Input | A | Form inputs require explicit confirmation; no auto-submit on change | Form tests |
| 3.2.3 | Consistent Navigation | AA | Menu structure, palette prefixes, and status-bar layout are identical across every document and dialog | Snapshot tests |
| 3.2.4 | Consistent Identification | AA | The same icon and label is used for the same action everywhere | Inventory test |
| 3.2.6 | Consistent Help | A (new in 2.2) | Help menu position and Help item names are identical across every window | Snapshot tests |
| 3.3.1 | Error Identification | A | Every error message names the field and the rule violated; never just a code | Error message inventory |
| 3.3.2 | Labels or Instructions | A | Every input has a visible label; complex fields include placeholder hints that are also exposed as MSAA description | Label inventory |
| 3.3.3 | Error Suggestion | AA | Field errors include the value the user typed and a concrete fix suggestion | Error message inventory |
| 3.3.4 | Error Prevention (Legal, Financial, Data) | AA | Destructive operations (Replace All > 25 occurrences, Restore Backup, Reset Settings) always show a confirmation; backups exist for restores | Confirmation matrix test |
| 3.3.7 | Redundant Entry | A (new in 2.2) | Previously entered values (search history, recent files, settings) are available without re-entry | Persistence tests |
| 3.3.8 | Accessible Authentication (Minimum) | AA (new in 2.2) | The only authentication is the AI provider API key, which is paste-and-store via DPAPI; no cognitive-test puzzle | n/a |

#### Principle 4: Robust

| SC | Title | Level | How Quill meets it | Tested by |
| --- | --- | --- | --- | --- |
| 4.1.1 | Parsing | A (obsolete in 2.2) | (Marked obsolete; included for completeness.) | n/a |
| 4.1.2 | Name, Role, Value | A | Every control exposes name, role, value, state, and where applicable description via MSAA and UIA. Custom status-bar cells implement this explicitly via `wx.Accessible` subclasses | UI a11y harness (Inspect.exe parity) |
| 4.1.3 | Status Messages | AA | All asynchronous announcements (saved, replaced N, found on line N, AI progress) are sent via the live-region pattern and through the SR-agnostic announcement channel (9.6) | Live region tests |

### 9.4 Screen-reader compatibility matrix

| Reader | Versions covered | Quill support level | Notes |
| --- | --- | --- | --- |
| NVDA | 2024.x, 2025.x, 2026.x stable + current beta | First-class (reference platform) | All flows fully announced; no required scripts |
| JAWS | 2024, 2025, 2026 latest | First-class | Small optional script provides live-region parity for non-standard status-bar cell updates; ships in the installer |
| Narrator | Windows 11 24H2 and later | First-class | Uses UIA path; covered by the standard MSAA wiring |
| Windows Magnifier | Current | Supported | Focus following works because of stock controls |
| ZoomText / Fusion | Current | Supported | Tested but not officially certified at v1.0 |
| Dolphin SuperNova | Current | Best effort | Tested at major releases; defects escalated |

### 9.5 Screen-reader announcement architecture

Quill speaks to the user through three independent channels, all of which deliver the same content. This is what "never goes quiet when you needed it to speak" means in code.

1. **Stock control announcements** — wx widgets carry their own MSAA/UIA semantics; the SR speaks them automatically on focus and value change.
2. **Live region channel** — a hidden `wx.StaticText` per top-level window acts as an ARIA-like live region. Quill sets its text, fires an MSAA `EVENT_OBJECT_LIVEREGIONCHANGED` and a UIA `Notification` event with kind `Other` and priority `Standard` or `High` as appropriate. NVDA and Narrator pick this up natively; JAWS reads it through the bundled optional script.
3. **Direct SR APIs (graceful degradation)** — when a detected SR is running, Quill may use its direct API for higher-priority announcements (NVDA's `nvdaControllerClient.dll` `nvdaController_speakText`, JAWS' `jfwapi.dll` `JFWSayString`, Narrator via UIA notification). This is used only when the live region path is too slow for time-sensitive feedback (find result during F3 chaining, spell-check next misspelling). The direct call is preferred only when (a) a registered SR is detected and (b) the user has not opted out in Settings → Reading.

All three channels are funnelled through a single `quill.a11y.announce(text, *, priority='normal', interruptible=True)` function, so there is exactly one code path to test.

Quill exposes an explicit announcement backend selector in Settings and command surfaces. Supported modes are `auto`, `legacy`, `prism`, and `sounds`, with `auto` as default. `auto` chooses the best backend for the current screen-reader/runtime context and falls back deterministically when a backend is unavailable.

### 9.5.1 Announcement backend provenance

The `prism` backend in Quill is derived from the architecture and behavior patterns published in the open-source Prism project:

- Source: <https://github.com/ethindp/prism>
- Scope borrowed: screen-reader announcement abstraction approach, backend-oriented dispatch model, and parity-focused announcement reliability goals.
- Quill adaptation: integrated into Quill's existing `quill.a11y.announce(...)` funnel and profile/feature controls, while preserving Quill's own command, diagnostics, and privacy conventions.

### 9.6 Keyboard accessibility gates

- **Keyboard parity matrix**: every menu item, every status-bar cell, every palette command, every dialog button has a keyboard equivalent. CI generates the matrix from the command registry and fails the build if any entry lacks an accessible keystroke.
- **No keyboard traps**: pytest-pywinauto test traverses every modal and non-modal window and asserts that Escape, Tab, and Shift+Tab always exit or cycle.
- **Single-character shortcut policy**: single-character shortcuts (F3, F7, etc.) are only bound to commands marked `repeatable`. Editor focus never binds a single printable character because that would steal typing.
- **Two-key chord policy**: the default keymap uses at most six two-key chords; profiles can use more; the user can rebind all.
- **Screen-reader chord guard** (5.8.4): when the user captures a new keystroke, Quill checks it against a curated static list of well-known NVDA, JAWS, and Narrator chords and refuses the capture with an explanation.

### 9.7 Visual accessibility gates

- **Themes**: System (follows Windows), Light, Dark, High Contrast (follows Windows High Contrast tokens), Custom (user-defined token map).
- **Contrast**: every theme is verified by an automated contrast checker (`a11y/contrast.py` using the WCAG relative-luminance formula) against every text/background and component-state pair; build fails on any pair below 4.5:1 text or 3:1 component.
- **Font scaling**: editor font 10–48pt; dialog text follows Windows DPI; all layouts tested at 100%, 125%, 150%, 175%, 200%, 300%, 400%.
- **Reflow**: minimum supported window size 800x600; all dialogs scrollable at that size; status-bar cells overflow into the roll-up cell.
- **Motion**: respects Windows “Show animations” setting; no animations in any case; progress indicators use a determinate or simple textual percentage.
- **Focus visibility**: native Windows focus rectangle is preserved; High Contrast theme amplifies; no custom-drawn focus.
- **Cursor**: caret blink rate respects Windows; thickness respects Windows; no custom carets.
- **Spacing**: 1.4.12 user overrides honoured (see matrix).
- **Target size**: every clickable target ≥ 24x24 device-independent pixels; status-bar cells ≥ 28x24.

### 9.8 Cognitive accessibility gates

- **Consistent vocabulary**: a controlled vocabulary document drives every string (e.g. "document" not "file" or "buffer"; "selection" not "highlight"); enforced by a linter over translation source files.
- **Plain-language baseline**: UI strings target a Flesch reading ease of 60 or higher; Tools (the Document Statistics engine) is used in CI to grade the UI string corpus.
- **Confirmations on destructive actions**: every destructive action prompts; default button is the safe option (Cancel, Keep Mine, etc.); the destructive button is never the default.
- **Undo for everything possible**: every editor mutation is undoable; settings and keymap changes support “Undo last change” for 30 seconds via a Notifications-cell message.
- **One-key escape**: Esc closes any palette or dialog without side effects.
- **Tooltips with intent, not jargon**: every button tooltip names the action and the result, not the implementation.
- **No autoplay**: no audio, video, or animation starts without explicit user action.

### 9.9 Accessibility testing pipeline

Three layers run on every PR and every release branch.

1. **Static / lint layer (every PR)**
   - Controlled-vocabulary linter over `*.po` translation sources.
   - Plain-language linter (Flesch ≥ 60) over UI strings.
   - Keymap audit (no editor-focus single printable letters; all commands have ids).
   - Theme contrast checker.
   - Tab-order snapshot diff (changes require an explicit reviewer approval).
   - Command registry coverage (every command has a name, description, default keybinding or explicit `unbound`, and a help topic).
2. **Headless UI layer (every PR, runs on a Windows runner)**
   - `pytest` + `pywinauto` boots the app and walks every dialog, modal, and palette mode.
   - Inspect.exe parity: a custom UIA dumper records the tree for each window; the dump is diffed against a golden snapshot.
   - Accessibility Insights for Windows CLI is run; build fails on any error.
   - DPI smoke tests at 100/150/200%.
3. **SR-in-the-loop layer (every release branch and nightly)**
   - A custom SAPI 5 speech driver records every utterance into a transcript file.
   - NVDA is launched with the recording driver via NVDA's command-line; Quill is driven through a scripted scenario set (open, find, F3 chain, palette, outline jump, spell check fix, keymap rebind, restore backup, AI confirm-and-cancel).
   - The recorded transcript is diffed against a golden transcript per scenario per SR. The harness is in v1.1 of the project plan but the scenario scripts and golden transcripts are produced manually for v1.0.
   - JAWS scenarios run separately when a JAWS-enabled runner is available; Narrator runs via UIA notifications.

No PR merges with any of these failing. A failure can be waived only by the accessibility lead, with an issue link and an expiry date.

### 9.10 VPAT / ACR generation

- The conformance matrix in 9.3 is the source of truth.
- A script (`tools/gen_vpat.py`) renders the matrix into an ITI VPAT 2.5 Rev INT form (the ICT industry-standard template) and a Word document, plus a markdown ACR for the website.
- The ACR is published with every release and links each row back to the corresponding test.
- VPATs cover WCAG 2.2, Section 508, and EN 301 549.

### 9.11 Certification path

- v1.0 self-certifies WCAG 2.2 AA, Section 508 (revised), and EN 301 549 v3.2.1 via the ACR.
- An independent third-party audit (target: TPGi, Deque, or Level Access) is commissioned for v1.0 release. Findings are tracked publicly in a `compliance/` folder of the repository.
- Outstanding findings have target dates and a public regression register.

### 9.12 Gated regressions (CI must-pass list)

A build is blocked when any of the following regresses:

- Any cell in the WCAG matrix transitions from passing to failing.
- Any tab-order snapshot diff is unreviewed.
- Any contrast pair drops below threshold in any bundled theme.
- Any command in the registry loses a name, description, or keymap entry.
- Any dialog gains a keyboard trap.
- Any user-facing string fails the controlled-vocabulary or plain-language linter without an explicit waiver.
- Any custom control is introduced into the editor or palette path without an `wx.Accessible` subclass that passes the Inspect.exe parity test.
- Any SR transcript diff exceeds tolerance.

---

## 10. Technical infrastructure

This section is the canonical engineering blueprint for Quill. It defines the module structure, every dependency (pinned, licensed, justified), the per-feature technical specifications, the threading and concurrency model, the data layout, the build and packaging pipeline, supply-chain integrity, observability, the plugin runtime, the update mechanism, the security architecture, the development workflow, and the coding standards.

### 10.1 Module map and responsibilities

```
quill/
  core/                       Pure-Python; no UI imports
    document.py               Document model: text buffer, line index, encoding, line endings, dirty state
    history.py                Undo/redo coalescing; persistent-undo serialisation
    bookmarks.py              Bookmark store with text re-anchoring
    locations.py              Recent locations ring + Mark ring
    backups.py                Backup manager, autosave, crash recovery
    settings.py               Settings load/save, schema validation, partitioned reset
    keymap.py                 Three-layer keymap (default · profile · user), chord engine, conflict detection
    commands.py               Command registry (id, title, description, when, default key, handler ref)
    palette.py                Palette scoring, prefix modes, recency/frequency
    sessions.py               Session save/restore, welcome-back snapshot
    fingerprint.py            SHA-256, atomic write helpers
    paths.py                  AppData layout helpers; sandbox roots
    events.py                 Internal event bus (sync; cross-thread queue)
    a11y/
      announce.py             Three-channel announcement funnel
      regions.py              Live region helpers
      transcript.py           In-process transcript capture (test-only)
    spell/
      engine.py               Public API: check_word, suggest, learn
      tokeniser.py            Unicode + code-aware tokeniser
      dictionary_stack.py     Priority stack (per-doc, per-project, personal, language, jargon)
      hunspell_backend.py     cyhunspell wrapper, thread-safe
      reranker.py             v1.1 experimental contextual reranker (interface only in v1.0)
      ignore.py               In-document ignore directives parser
  io/                         Format readers and writers; each module exports `read(path)`/`write(doc, path)`
    txt.py md.py html.py rst.py adoc.py org.py tex.py typst.py
    docx.py pptx.py xlsx.py odt.py odp.py ods.py rtf.py epub.py
    pdf.py                    Tier-1 pipeline + Tesseract fall-back
    subtitles.py              srt vtt sbv ass ttml scc stl cap
    code/                     One module per language family for tokenisation hints
    config/                   json yaml toml ini xml csv tsv
    email.py ics.py vcf.py rss.py atom.py opml.py jsonfeed.py
    daisy.py braille.py       BRF, BRL reading; back-translation deferred
    notebook.py               ipynb linearisation
    sqlite_view.py            Read-only schema + sample rows
    ocr.py                    Tesseract bridge
    detect.py                 Format auto-detect by magic + extension + sniff
  ai/
    base.py                   Provider interface
    openai.py azure.py anthropic.py ollama.py
    pipeline.py               PDF reading-order pipeline, document reading-order pipeline
    safety.py                 Per-action consent, size caps, redaction
  ui/                         wxPython shell
    app.py                    wx.App, single-instance, theme loader
    frame.py                  Main wx.Frame; F6 region cycler
    editor.py                 wx.TextCtrl host + line/column tracker + selection helpers
    statusbar.py              Custom-layout wx.StatusBar with focusable cells
    menubar.py                Menu construction; live keybinding labels
    palette.py                Command palette frame
    keymap_editor.py          Settings page + inline rebinding capture dialog
    outline.py                Outline Navigator (wx.TreeCtrl)
    audit.py                  Accessibility Audit panel
    table_mode.py             Markdown/HTML table navigation overlay
    spell_panel.py            Spell-check dialog + quick-fix popup
    settings.py               wx.Treebook settings root
    dialogs/                  Find, Replace, FindAll, GoToLine, Bookmarks, Backups, OpenURL, UnicodeInsert, etc.
    accessible/               wx.Accessible subclasses for custom regions
    themes/                   Bundled theme token maps
    locale/                   gettext .po / .mo bundles
  platform/
    windows/
      shell.py                File associations, Jump List, ICustomDestinationList
      dpapi.py                Windows DPAPI key storage
      sr_detect.py            Active screen-reader detection
      sr_announce.py          NVDA / JAWS / Narrator direct-API bridges
      single_instance.py      Named-mutex + IPC port
      high_contrast.py        Windows High Contrast token translation
      tts.py                  SAPI 5 + OneCore enumeration for Read Aloud
  plugins/                    v1.1 plugin loader, manifest, sandbox; v1.0 ships the loader skeleton only
    api.py                    Stable interface re-exports
    manifest.py               JSON schema validation
  tools/                      Internal CLI tools (not shipped to users)
    gen_keymap_reference.py   Builds the Keyboard Reference markdown
    gen_vpat.py               Builds the VPAT/ACR
    a11y_audit.py             Local accessibility audit runner
  tests/
    unit/  integration/  a11y/  perf/  fixtures/
```

### 10.2 Complete dependency manifest

Every direct dependency is listed below with the pinned version range Quill 1.0 will ship against, the license, the reason it is in the tree, and any constraints. Pins are tight in production builds and loose in development.

#### 10.2.1 Runtime, Python

| Package | Version | License | Role | Notes |
| --- | --- | --- | --- | --- |
| `python` | 3.12.x | PSF | Runtime | Frozen with PyInstaller; 3.13 supported as soon as wxPython publishes wheels |
| `wxPython` | 4.2.2+ | wxWindows Library Licence | UI toolkit | Stock controls only; no `wx.lib.agw` controls in the writing path |
| `pywin32` | 308+ | PSF-style | Windows shell, DPAPI, COM | Required for file associations, Jump List, DPAPI |
| `comtypes` | 1.4+ | MIT | UIA notifications, SAPI 5 | Used by `quill.platform.windows.sr_announce` and `tts` |
| `wxasync` | 0.49+ | MIT | asyncio + wx integration | Runs AI HTTP calls and background OCR without blocking UI |
| `httpx` | 0.27+ | BSD-3 | HTTP for AI providers and Open from URL | Async; respects per-action consent |
| `charset-normalizer` | 3.3+ | MIT | Encoding auto-detect | Used by `io.detect` and editor encoding picker |
| `python-docx` | 1.1+ | MIT | DOCX read/write | Round-trips heading styles for export |
| `mammoth` | 1.7+ | BSD | DOCX → HTML/Markdown extraction | Used as fall-back when python-docx output is too raw |
| `python-pptx` | 1.0+ | MIT | PPTX read | Slides + speaker notes |
| `openpyxl` | 3.1+ | MIT | XLSX read (as table) | Sheets become sections |
| `odfpy` | 1.4+ | LGPL-2.1+ | ODT/ODP/ODS read | LGPL is acceptable as a dynamically loaded library |
| `ebooklib` | 0.18+ | AGPL-3 with linking exception | EPUB read | Only used as library; no AGPL linkage concerns |
| `beautifulsoup4` | 4.12+ | MIT | HTML/XHTML/SVG parsing | With `lxml` parser |
| `lxml` | 5.2+ | BSD-3 | XML/HTML parsing backend | |
| `markdown-it-py` | 3.0+ | MIT | Markdown parsing & rendering | With `mdit-py-plugins` for tables, footnotes, deflists |
| `mdit-py-plugins` | 0.4+ | MIT | Markdown extensions | |
| `docutils` | 0.21+ | Public Domain / BSD | reStructuredText parsing & outline | |
| `pdfplumber` | 0.11+ | MIT | PDF text & layout, tier-1 path A | |
| `pypdfium2` | 4.30+ | Apache-2.0 / BSD | PDF text, tier-1 path B | Native PDFium binary |
| `pdfminer.six` | 20240706+ | MIT | PDF text fallback path C | Used when A and B both score badly |
| `pikepdf` | 9.0+ | MPL-2.0 | PDF metadata + password handling | Wraps QPDF |
| `pytesseract` | 0.3.10+ | Apache-2.0 | Tesseract OCR bridge | Tesseract binary bundled separately |
| `Pillow` | 10.4+ | HPND | Image handling for OCR and SVG raster fall-back | |
| `cyhunspell` | 2.0+ | MPL-2.0 | Hunspell binding for spell check | Hunspell dictionaries bundled per language |
| `regex` | 2024.7+ | Apache-2.0 / PSF | Unicode regex for find/replace | Replaces stdlib `re` where Unicode classes matter |
| `rapidfuzz` | 3.9+ | MIT | Palette and command fuzzy matching | |
| `unicodedata2` | 15.1+ | Apache-2.0 | Up-to-date Unicode tables | Powers Unicode Insert and tokeniser |
| `pyyaml` | 6.0+ | MIT | YAML read/write for sidecars and front-matter | `safe_load` only |
| `tomli` / `tomllib` | stdlib for read; `tomli-w` 1.0+ for write | MIT | TOML | |
| `jsonschema` | 4.23+ | MIT | Settings, keymap, plugin manifest validation | |
| `platformdirs` | 4.2+ | MIT | AppData/log directory discovery | |
| `keyring` | 25+ | MIT | Optional secondary credential storage | DPAPI is primary |
| `cryptography` | 43+ | Apache-2.0 / BSD | DPAPI fallback + signed manifest verification | |
| `pygments` | 2.18+ | BSD | Syntax tokenisation for code-aware spell check and tokeniser | Tokens only; no styling |
| `chardet` | 5.2+ | LGPL-2.1 | Encoding detection secondary | charset-normalizer is primary |
| `liblouis` (Python bindings) | 3.31+ | LGPL-2.1+ | Braille back-translation — deferred to v1.1 | Listed for reference |
| `python-magic` (or `puremagic`) | 0.4.27+ | MIT | Magic-number sniffing for `io.detect` | `puremagic` preferred (pure-Python) |

#### 10.2.2 Native binaries bundled

| Binary | Version | License | Use |
| --- | --- | --- | --- |
| Tesseract OCR | 5.4+ | Apache-2.0 | OCR for image PDFs and image documents |
| Hunspell dictionaries (en-US, en-GB, es-ES, fr-FR, de-DE, pt-BR, pl-PL, ja-JP) | latest | varies (mostly LGPL / Apache / public domain) | Spell-check dictionary stack |
| PDFium | bundled with `pypdfium2` | Apache-2.0 / BSD | PDF rendering and text |
| QPDF | bundled with `pikepdf` | Apache-2.0 / Clarified Artistic | PDF transformations |

LibreOffice, Calibre, Ghostscript, and unrar are **not** bundled; they are optional plugin dependencies (v1.1).

#### 10.2.3 Build and dev tooling

| Tool | Version | Role |
| --- | --- | --- |
| `uv` | 0.4+ | Fast dependency resolution; lockfile |
| `ruff` | 0.6+ | Lint + format |
| `mypy` | 1.11+ | Static type-checking (strict in core, gradual in ui) |
| `pytest` + `pytest-asyncio` | latest | Test runner |
| `pytest-wx` / custom fixtures | latest | wxPython test fixtures |
| `pywinauto` | 0.6.8+ | UI automation tests |
| `Accessibility Insights for Windows` (CLI) | latest | A11y audit in CI |
| `PyInstaller` | 6.10+ | Frozen build |
| `Inno Setup` | 6.3+ | Installer authoring |
| `signtool` (Windows SDK) | latest | EV code signing |
| `pip-audit` and `osv-scanner` | latest | Supply-chain vulnerability scan |
| `cibuildwheel` | latest | Multi-Python wheel builds for any C-extension we author |

#### 10.2.4 License posture

- Quill itself is **MIT-licensed** (default; final decision still tracked in Open Questions).
- LGPL components (`odfpy`, `chardet`, `liblouis`) are linked dynamically; we publish the license texts and a `THIRD-PARTY-NOTICES.md` in the installer.
- MPL-2.0 components (`cyhunspell`, `pikepdf`) are linked dynamically; modifications to those files (if any) are published.
- AGPL components (`ebooklib`) are used as a library; we do not host a network service that exposes their interface to end users, which keeps us outside the AGPL trigger.
- All licenses are aggregated automatically into `THIRD-PARTY-NOTICES.md` by `tools/gen_notices.py` at build time; the build fails if any new package lacks a license entry.

### 10.3 Per-feature technical specifications

Each feature in section 5 has an engineering spec here. The full table is large; the canonical form lives in `docs/engineering/` once development begins. The table below is the v1.0 commitment.

| Feature | Module(s) | Key APIs / Libraries | Threading | Storage | A11y wiring |
| --- | --- | --- | --- | --- | --- |
| Editor surface (5.2) | `ui.editor` | `wx.TextCtrl` with `wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_NOHIDESEL | wx.TE_AUTO_URL` | UI thread | In-memory document buffer | Native stock control; MSAA edit role |
| Outline Navigator (5.16) | `ui.outline`, `io.*` outline emitters | `wx.TreeCtrl`, `markdown-it-py`, `beautifulsoup4`, `docutils`, `python-docx`, `pdfplumber` outline, `ebooklib` nav, `pikepdf` outlines | Outline build on worker; `wx.CallAfter` to populate | Per-document outline cache `outline_cache/<hash>.json` | TreeCtrl exposes hierarchical structure to AT |
| Jump-by-structure (5.17) | `ui.editor`, `core.commands` | Same outline producers | UI thread (cheap) | n/a | Announces via `a11y.announce` |
| Line/block ops (5.18) | `ui.editor`, `core.history` | wx editor primitives | UI thread | Undo via `core.history` | Announcements per action |
| Statistics (5.19) | `core.document`, `core.metrics` | pure Python; `pyphen` optional for syllables (deferred) | Worker for large docs | n/a | Dialog with one `wx.StaticText` per metric |
| A11y Auditor (5.20) | `core.audit`, `io.*` audit emitters | `markdown-it-py` AST, `beautifulsoup4`, `python-docx`, `pikepdf` | Worker thread | Per-doc ignore list in sidecar | List dialog; severity prefix in text |
| Table Mode (5.21) | `ui.table_mode`, `io.md` table tokens | `markdown-it-py` tables, BS4 for HTML | UI thread | n/a | Announces column header on entry |
| Editor essentials (5.22) | `ui.editor`, `core.document` | `charset-normalizer`, stdlib `io` | I/O off-thread | Per-doc prefs in `file-prefs.json` | Encoding/EOL cells in status bar |
| Menu bar (5.1a) | `ui.menubar`, `core.commands` | `wx.MenuBar` | UI thread | n/a | Menu items show live keybindings; mnemonics |
| Status bar (5.1b) | `ui.statusbar`, `ui.accessible.statusbar_cell` | Custom `wx.StatusBar` layout with focusable buttons; `wx.Accessible` subclass | UI thread with debounced events | n/a | Each cell exposes name/role/value/description via MSAA + UIA |
| Command palette (§7) | `ui.palette`, `core.palette` | `wx.SearchCtrl` + `wx.ListBox`; `rapidfuzz` | Match on UI thread (≤30 ms) | Recents in `palette-recent.json` | Combobox-style; live region for status |
| Keymap (§8) | `core.keymap`, `ui.keymap_editor` | Custom chord engine; `wx.AcceleratorTable` per context | UI thread | `keymap.json`; `.tmp`+rename | Capture dialog announces every keystroke |
| Spell check (§6) | `core.spell.*` | `cyhunspell`, custom tokeniser | Background pass on worker; quick-fix on UI | `personal.dic`, `<doc>.quill.yml` | Dedicated panel + quick-fix popup |
| Find/Replace (5.7) | `ui.dialogs.find`, `core.document` | `regex` module | Worker for very large docs | `search-history.json` | Announces structured one-liner per match |
| Bookmarks (5.10) | `core.bookmarks` | pure Python; SHA-1 of path | UI thread | `bookmarks/<hash>.json` | List dialog; re-anchor on jump |
| Backups + autosave (5.13, 5.39) | `core.backups` | stdlib | I/O thread; debounced | `backups/`, `autosave/`, `.tmp`+rename | Recovery prompt at launch |
| Read Aloud (5.25) | `platform.windows.tts`, `ui.read_aloud` | SAPI 5 via `comtypes`; OneCore via Windows.Media.SpeechSynthesis WinRT | Background voice thread | n/a | Uses a *secondary* voice; never blocks SR |
| Open from URL (5.27) | `ui.dialogs.open_url`, `ai.safety` | `httpx` async | asyncio via `wxasync` | Temp file | Consent dialog announces host + size |
| AI reading-order (5.5, 5.4 tier 3) | `ai.pipeline`, `ai.openai/azure/anthropic/ollama`, `ai.safety` | `httpx` async; per-provider SDK shapes | asyncio via `wxasync` | Nothing stored | Progress announced every 20 s |
| OCR (5.4) | `io.ocr`, `pytesseract` | Tesseract binary | Worker process per page | n/a | Progress announced |
| Diff/Compare (5.22) | `core.diff` | stdlib `difflib`, `regex` | Worker | n/a | Diff opens as a normal document |
| Notifications centre (5.35) | `core.events`, `ui.notifications` | Internal event bus | UI thread | In-memory | Cell + dialog |
| Sessions (5.22, 5.49) | `core.sessions` | pure Python | I/O thread | `sessions/last.json` | Prompt at launch |
| Templates + snippets (5.22) | `core.templates` | pure Python | UI thread | `%APPDATA%\Quill\templates`, `snippets/` | List dialogs |
| Atomic stores (5.55) | `core.fingerprint`, `core.paths` | stdlib `os.replace` | All write paths | All JSON stores | Recovery announcements |
| Plugin loader skeleton (v1.0; full plugin runtime v1.1) | `plugins.api`, `plugins.manifest` | `importlib.metadata`, `jsonschema` | UI thread on load; isolated thread per task | `%APPDATA%\Quill\plugins\` | Manifest must declare UI surfaces |

### 10.4 Threading and concurrency model

- **UI thread**: owns all wx widgets and the editor buffer. Never blocks for more than 16 ms.
- **I/O thread pool** (`concurrent.futures.ThreadPoolExecutor`, default 4): file open, save, autosave, backup writes, settings persistence, bookmark writes, fingerprint compute.
- **Compute thread pool** (default 2): spell-check background pass, outline build for very large documents, document statistics for >1 MB, accessibility audit for >100 KB.
- **asyncio loop** (via `wxasync`): all HTTP I/O (AI providers, Open from URL, update check). Cancellable per task.
- **OCR worker process**: Tesseract runs in a child process per OCR job, isolated to avoid GIL contention and crash blast radius.
- **Marshalling**: any callback into wx uses `wx.CallAfter` or `wx.CallLater`. No direct cross-thread wx calls.
- **Cancellation**: every long-running task accepts a `quill.core.events.CancelToken`. Cancellation is checked at fixed safe points (every page, every 1 MB of read, every HTTP chunk).
- **Backpressure**: the I/O pool uses bounded queues; new tasks wait, never spawn-and-forget.
- **No threading.Lock around shared mutable state in `core`**. The document model is owned by the UI thread; workers receive snapshots and return new snapshots; `wx.CallAfter` merges. This invariant is enforced by lint (`ruff` custom rule) that flags `threading.Lock` outside `platform/`.

### 10.5 Data layout (canonical)

```
%APPDATA%\Quill\
  settings.json             Validated by jsonschema; .bak kept
  keymap.json               Validated; .bak kept; quarantine on corrupt
  recent.json               Last N files; default 10
  recent-locations.json     Per-session ring; ephemeral
  saved-searches.json       Saved search filters
  search-history.json       Last 100 search/replace terms; clearable
  file-prefs.json           Per-path encoding/EOL/wrap/indent/language memory
  sessions\
    last.json               Session restore data
    <name>.json             Named sessions
  bookmarks\
    <sha1-of-path>.json     Per-document bookmark store
  backups\
    <sha1-of-path>\
      <iso-timestamp>.bak   Save backups
  autosave\
    <session-id>\
      <doc-id>.snap         Crash recovery snapshots
      <doc-id>.snap.tmp     In-flight
  undo\
    <sha1-of-path>.undo     Persistent undo (opt-in)
  notes\
    <sha1-of-path>.md       Per-document scratchpad
  outline_cache\
    <sha1-of-path>.json     Cached outline; invalidated on document mtime change
  dictionaries\
    personal.dic
    <lang>.aff / <lang>.dic
    jargon\<name>.dic
  spell-learning\
    learning.sqlite         Per-user learning (frequencies, rejection counts)
  templates\<name>.tpl
  snippets\<lang>.json
  plugins\<plugin>\
  logs\quill-YYYY-MM-DD.log Rotating logs, 14-day retention
  diagnostics\               Output dir for Save Diagnostics
  trusted-locations.json
  notifications.json         Pending notifications
```

All JSON files validate against schemas in `quill/core/schemas/`. All writes are atomic (`tempfile.NamedTemporaryFile` in the same directory + `os.replace`).

### 10.6 Packaging, signing, supply chain

- **Frozen build**: PyInstaller with one-folder layout (faster start than one-file). UPX disabled (no compression; SmartScreen friendliness, debug symbols intact).
- **Installer**: Inno Setup 6 with per-user (`{userappdata}`) default, system-wide optional. Components: Core, Tesseract OCR (English by default; additional languages downloadable post-install), Hunspell dictionaries (launch-language set by default), JAWS script (optional). License screen lists `THIRD-PARTY-NOTICES.md`.
- **Portable zip**: identical layout without registry writes; uses `%APPDATA%` per Windows convention.
- **Signing**: EV code-signing certificate; `signtool` signs every `.exe`, `.dll`, and the installer; timestamps via DigiCert RFC 3161 timestamp server. SmartScreen reputation built before public launch.
- **Reproducible builds**: the build pipeline pins every dependency via `uv` lockfile; the lockfile is committed; the build container is pinned to a SHA-tagged Windows image.
- **SBOM**: a CycloneDX 1.5 SBOM is generated per build (`tools/gen_sbom.py` using `pip-audit --format=cyclonedx`) and attached to the GitHub release.
- **Supply-chain scanning**: every PR runs `pip-audit` and `osv-scanner`; CRITICAL or HIGH vulnerabilities fail the build.
- **Provenance**: GitHub Actions runs with OIDC; artefacts are signed with Sigstore `cosign` and the `cosign.bundle` is published next to each release artefact.
- **Update channel**: a signed JSON manifest (Ed25519 signature; key pinned in the app) lists current stable, beta, and security-only releases with SHA-256s. Quill checks on launch only when the user has opted in (manual `Check for Updates` is always available).
- **Footprint**: realistic target is 180–220 MB installed with English Tesseract data and English/UK + Spanish/French/German Hunspell dictionaries. A **Quill Lite** option ships at ~90 MB and downloads dictionaries and Tesseract on first use.

### 10.7 Build and dev environment

- **Python 3.12** pinned via `uv python install`.
- **Lockfile**: `uv.lock` committed; `uv sync` reproduces the dev environment exactly.
- **Dev install**: `uv sync --all-extras` plus `pre-commit install` for hooks.
- **Pre-commit**: ruff format, ruff lint, mypy on `core/` and `io/`, controlled-vocabulary linter, contrast checker, tab-order snapshot check, license-notice generator.
- **Local accessibility audit**: `python -m quill.tools.a11y_audit` launches Quill under pywinauto and runs the static + headless layers in under five minutes.
- **Local SR scenario**: `python -m quill.tools.sr_scenario --scenario find_chain --reader nvda` launches NVDA against Quill, replays a scenario, and writes a transcript to `out/`.

### 10.8 Continuous integration and delivery

- **Provider**: GitHub Actions.
- **Matrix**: Windows 10 22H2, Windows 11 24H2; Python 3.12; wxPython current stable.
- **Jobs**:
  1. **Lint** (ruff, mypy, jsonschema validation of bundled schemas).
  2. **Unit tests** (`pytest tests/unit -n auto`).
  3. **Integration tests** (`pytest tests/integration`); covers every format reader and writer against a fixture corpus stored in Git LFS.
  4. **A11y static** (controlled vocab, plain language, keymap audit, contrast checker, tab-order snapshot diff).
  5. **A11y headless** (`pytest tests/a11y` via pywinauto + Accessibility Insights CLI).
  6. **Perf smoke** (`pytest tests/perf`, asserts the targets in §11).
  7. **Build** (PyInstaller, Inno Setup, signtool, Sigstore cosign).
  8. **Supply chain** (pip-audit, osv-scanner, SBOM generation).
  9. **SR scenario nightly** (NVDA scenarios on a self-hosted runner).
- **Release branch**: `release/x.y` triggers a full build + sign + publish to GitHub Releases and the auto-update manifest.
- **Triage SLA**: SR transcript diffs reviewed within 24 hours.

### 10.9 Observability

- **Logging**: stdlib `logging`, rotating file handler, INFO level by default. Log records contain action name, outcome, duration; never document content; paths are hashed.
- **Crash handler**: a `faulthandler`-based hook writes a `quill-crash-YYYY-MM-DDTHHMMSS.dump` with the Python traceback and a redacted environment snapshot. On next launch Quill offers to include the crash in a diagnostics bundle for support; never auto-sends.
- **Metrics**: opt-in only; counters per feature use; transported by `httpx` to a self-hosted endpoint over TLS; cleartext example shown before opt-in.
- **Event bus**: an internal sync event bus (`core.events`) records the last 50 commands and notable lifecycle events; these are what Help → Save Diagnostics ships.

### 10.10 Plugin runtime (v1.0 surface, v1.1 full)

- **v1.0**: the plugin loader skeleton exists; only first-party plugins (JAWS script, additional Hunspell dictionaries) are loadable. The full third-party plugin runtime ships in v1.1.
- **Manifest** (`plugin.json`): id, name, version, license, capabilities (`commands`, `format_reader`, `format_writer`, `palette_entry`, `settings_page`, `keybinding_default`, `statusbar_cell`), requested permissions (`network: never|on_action`, `filesystem: read|write`, `subprocess: none|listed`).
- **Discovery**: `%APPDATA%\Quill\plugins\<id>\plugin.json` plus `entry_points` group `quill.plugins` (for pip-installed plugins).
- **Lifecycle**: load → register → enable; disabled plugins keep their settings.
- **Sandboxing (v1.1)**: each plugin runs in its own thread; network and subprocess calls require an explicit per-action consent or a setting that whitelists the plugin's manifest-declared hosts; UI surfaces created by plugins must pass the same accessibility static checks as core.
- **Versioning**: plugins declare the Quill API version they target; the loader rejects mismatched majors.

### 10.11 Security architecture

- **Secrets**: AI provider keys stored via DPAPI (`platform.windows.dpapi`); never in plain text on disk; never logged; never in diagnostics bundles.
- **Document data**: never leaves the machine without per-action consent.
- **Network calls**: an internal `ai.safety.consent(action, host, size_estimate)` gate is required before any network call; the call records what was sent (action name, host, size only) in the audit log.
- **Updates**: manifest signature verified with a pinned Ed25519 public key; artefact SHA-256 verified before install.
- **File handling**: file dialogs use the OS dialog (`wx.FileDialog`) so the user controls disclosure scope; the trusted-locations system (5.31) prevents silent opening of suspicious files.
- **Path traversal**: every settings/keymap/plugin path is normalised and validated; no `..` segments accepted.
- **JSON parsing**: bounded depth and size via custom decoder hooks; refuses to parse settings files over 10 MB or beyond depth 32.
- **YAML parsing**: `safe_load` only.
- **Subprocess**: limited to Tesseract and (post-v1.1) plugin-declared binaries; arguments are always passed as lists; no `shell=True`.
- **Threat model**: a malicious document might try to (a) crash the parser, (b) request a keymap override to bind dangerous keys, (c) trigger an outbound network request. (a) parsers are fuzz-tested with `atheris`; (b) keymap overrides require explicit consent (5.50); (c) network is gated.
- **Responsible disclosure**: a `SECURITY.md` file documents the disclosure email and PGP key.

### 10.12 Update mechanism

- v1.0 ships **manual update check**: `Help → Check for Updates…` fetches the signed manifest, verifies it, compares versions, offers to download the next stable.
- The download is verified (SHA-256) and Sigstore-attested; the installer is signed; the user runs it.
- A small in-app pre-update health check ensures the user's editor has no unsaved documents before launching the installer.
- Auto-update lands in v1.1 with a Squirrel-style delta channel.

### 10.13 Internationalisation infrastructure

- All UI strings flow through `gettext`; the `_()` callable is the sole permitted lookup.
- `.po` source files live under `quill/ui/locale/<lang>/LC_MESSAGES/quill.po`; `.mo` are compiled at build time.
- Pluralisation uses `ngettext`.
- Date/number formatting uses `babel`.
- Bidirectional text in user documents is rendered by the OS edit control; full RTL UI is v1.2.
- A translation portal (Weblate or Crowdin) is set up at v1.0 beta; community translators are credited in About.

### 10.14 Performance budgets and instrumentation

All performance targets in §11 are enforced by `tests/perf/`. Each test asserts against a budget; regressions over 15% fail the build. Microbenchmarks live next to the code they measure. Real-world startup time is measured by a stopwatch fixture that uses Windows' high-resolution timer.

### 10.15 Coding standards and review

- **Style**: ruff format (PEP 8 with relaxed line length 100).
- **Typing**: strict mypy in `core/` and `io/`; gradual in `ui/`; types required on all public functions.
- **Docstrings**: Google style; every public API has one.
- **Imports**: absolute; no wildcard imports; `wx` may only be imported from `quill.ui` and `quill.platform.windows`.
- **Public API stability**: `quill.core`, `quill.io`, `quill.plugins.api` follow semver; breaking changes require a major bump and a deprecation cycle of one minor version.
- **PR review**: two approvals required; one must be from a maintainer; any change to `ui/`, `core/a11y/`, or `core/keymap.py` additionally requires sign-off from the accessibility lead.
- **Issue triage SLA**: P0 (data loss, crash on launch, accessibility regression) within 24 h; P1 (function broken) within 5 business days; P2 within the next release.

### 10.16 Module ownership and SOLID boundaries

- `core/*` knows nothing about `wx`; tested without UI; can be reused by a future TUI or web front-end.
- `io/*` modules each export `read(path) -> Document`, optionally `write(doc, path)`, and `outline(doc) -> Outline | None`; no other contracts.
- `ui/*` modules consume the command registry and the document model; UI components never read from disk directly.
- `platform/windows/*` is the only place where `pywin32`, `comtypes`, or registry access is allowed.
- `ai/*` modules conform to a single `Provider` ABC with `complete`, `improve_reading_order`, `cancel`, `estimate_cost` methods.
- `plugins/api.py` is the only file plugins import from; everything else is internal.

### 10.17 Magic, by construction

The engineering choices above add up to the user-visible magic the product promises:

- Stock controls everywhere keep MSAA/UIA pristine; speech is correct without scripts.
- Atomic writes plus `.bak` plus autosave plus persistent undo make "I lost work" almost impossible.
- A single announcement funnel keeps speech behaviour identical across NVDA, JAWS, and Narrator.
- Pinned, audited dependencies and reproducible builds keep "works on my machine" out of the loop.
- A small command registry plus a three-layer keymap plus a discoverable palette mean every feature is reachable, learnable, and rebindable.
- A WCAG matrix wired to CI means accessibility cannot quietly regress; if it slips, the build fails.

---

## 11. Performance targets

- Cold start to blank document: under 1.5 seconds on a 2020-era laptop.
- Open a 200-page text-based PDF (local extraction): under 6 seconds.
- Open a 1 MB Markdown file: under 250 ms.
- Find first match in a 1 MB document: under 100 ms.
- Spell check full document (50 000 words, en-GB): under 1.2 seconds.
- Quick-fix suggestion ranking per misspelling: under 10 ms.
- Command palette open + first results visible: under 50 ms.
- Memory at idle with one empty document: under 150 MB.
- Autosave write: under 50 ms, non-blocking.

---

## 12. Privacy and security

- Local first. Nothing leaves the machine without an explicit per-action confirmation.
- AI provider keys stored via Windows DPAPI; never plain text.
- Logs never include document content. Logs include action names and outcomes only.
- Spell-check learning data stays on disk under the user profile and can be wiped from a single button.
- Crash reports are opt-in and scrubbed of paths and content.
- All file dialogs use the OS dialog so the user controls disclosure.
- Network calls show host, payload size, and estimated cost (where the provider supplies it) before sending.

---

## 13. Internationalisation and localisation

- All UI strings wrapped in `_()` from `gettext`.
- Initial languages: English (US), English (UK), Spanish, French, German, Brazilian Portuguese, Polish, Japanese.
- Right-to-left support deferred to v1.2.
- Spell-check dictionaries shipped for the initial languages plus a downloader for others.

---

## 14. Telemetry

- Off by default. The setting is presented in plain language, with an example payload shown verbatim before opt-in.
- If enabled, anonymised counters only: feature used, error counts.

---

## 15. Success metrics

- Time to open a typical PDF and reach the first searchable word.
- Number of screen-reader announcement regressions per release (target: zero).
- Crash-free sessions per week (target: 99.5 percent).
- User-reported "I lost work" incidents (target: zero, hard).
- Spell-check first-suggestion acceptance rate after 30 days of use (target: above 70 percent).
- Command palette task completion time vs menu navigation (target: at least 2x faster for top 20 commands).
- Adoption: monthly active users among the NVDA add-on community.
- Qualitative: 20+ unsolicited testimonials in the first 6 months saying "this feels calm."

---

## 16. Release plan

v1.0 is locked to features we can build and ship at the highest quality bar with no novel research dependencies and no fragile third-party requirements. Anything that requires unproven libraries, brittle parsers, ML training, or external binaries beyond the bundled set is deferred to the backlog in [section 17](#17-backlog-and-deferred-items).

Every v1.0 feature in the list below is **Confidence A**: a defined library exists, a known engineering path is mapped, accessibility behaviour is predictable, and a working prototype can be produced in a single sprint.

### 16.1 v0.9 alpha (internal, 6 weeks)

- Application shell, multi-document, menu bar, status bar.
- Editor with full standard editing, undo/redo, word delete, case conversion, line operations (5.18), smart paste.
- Open and save: `txt`, `md` and family, `html`/`htm`/`xhtml`, all source-code and config text formats, all subtitle text formats, `json`/`yaml`/`toml`/`xml`/`csv`/`tsv`, `rst`, `adoc`, `org`, `tex`, `bib`, `typ`.
- Recent files; Settings skeleton; Backups and autosave.
- Find and replace (case, whole word, regex) with announcement of context line.
- Command Palette with command and recent-files modes; keymap editor read-only.
- NVDA announcement plumbing; baseline JAWS and Narrator behaviour via stock controls.

### 16.2 v1.0 beta (8 weeks after 0.9)

Adds, in order of priority:

- **Quill Spell** with Hunspell baseline plus the dictionary stack (personal, per-document, per-language). Suggestion ranking is the Hunspell ranking. The contextual reranker is deferred to v1.1 experimental.
- Bookmarks with re-anchoring, Outline Navigator (5.16), jump-by-structure (5.17), Where Am I.
- DOCX read/write, XLSX read (as table), PPTX read, RTF read, ODT read, ODS read (as table), ODP read.
- EPUB read.
- PDF reading: **tier 1 local extraction only** (layered `pdfplumber` + `pypdfium2`, scored per page) plus PDF embedded bookmarks. Tier 2 "enhanced local" is removed from v1.0; tier 3 AI is moved to v1.0 release.
- Markdown preview-as-HTML, export to HTML, export to DOCX; HTML preview.
- Word count and document statistics (5.19); Accessibility Auditor (5.20); Table Mode (5.21); Editor Essentials (5.22).
- File associations and "Open with Quill" verb; Jump List integration (5.32).
- Full Command Palette with all prefixes; full Keymap editor with profiles and inline rebinding.
- Sessions, templates, snippets; Welcome-back snapshot (5.49).
- Encoding picker, EOL conversion, external-change watcher, reload from disk; per-file format memory (5.43).
- Compare with File (diff view); Save All with conflict detection (5.43).
- Link tools (5.37): Insert link `Ctrl+K`, Follow link `Ctrl+Enter`, quote indent/dedent.
- Search refinements (5.41): replace preview for >25 occurrences, saved searches.
- Recent locations history (5.23), Mark ring (5.24), Format-aware bracket nav (5.28), Format menu (5.29).
- Atomic on-disk stores (5.55) from day one.
- Onboarding flow (5.56), Privacy Summary (5.57), Licenses screen (5.58).
- Read-only mode (5.60); File menu helpers — Reveal in Explorer, Copy Path, Copy Name (5.61); Open Recent pin/unpin (5.62).
- Settings search (5.73); In-app changelog (5.74).

### 16.3 v1.0 release (4 weeks after beta)

Adds and hardens:

- DAISY 2.02 and 3 reading; BRF and BRL reading (no braille back-translation in v1.0; see backlog).
- SVG text mode; SQLite schema + sample row view (read-only).
- ICS, VCF, EML reading (RFC 822 standard email files); RSS, Atom, OPML, JSON Feed.
- Notebook (`.ipynb`) linearisation, read-only.
- Image OCR via local Tesseract (English by default; downloader for additional languages). Multi-page TIFF supported. Other image formats are deferred to plugins (see backlog).
- AI-assisted reading order (opt-in, requires user-supplied API key, transparent confirmations, progress announced).
- Optional JAWS script for live-region parity.
- Full localisation for launch languages: English (US), English (UK), Spanish, French, German, Brazilian Portuguese, Polish, Japanese.
- Signed Inno Setup installer plus portable zip. Manual update check with signed manifest (no auto-update in v1.0).
- Format Support settings page that lists every format, the engine handling it, the confidence grade (A/B/C), and whether a helper plugin can raise the grade.
- CI suite: unit tests for `quill.core`, integration tests for file readers/writers, accessibility checks for stock-control composition (no NVDA speech-viewer harness in v1.0; see backlog).
- Document Properties and front-matter editor (5.38); Document fingerprint (5.52).
- Read Aloud (5.25); Number Lines (5.26); Open from URL (5.27); Bookmark export/import (5.30); Trusted locations (5.31); Diagnostics and bug reporting (5.33); Welcome and Keyboard Reference (5.34); Notifications centre (5.35); What-changed-on-save (5.36, opt-in).
- Autosave control + persistent undo (5.39); Join paragraph + heading auto-numbering + footnote helper (5.40); Sort and transform details (5.42); Per-document scratchpad (5.44); Section folding announce-only (5.45); Spell-check ignore directives + manual bilingual flag (5.46); Word boundary mode + trailing whitespace + case-change announcement (5.47); Multi-format export + reading view (5.48); Per-document keymap override (5.50); Settings export/import/partitioned reset (5.51); Unicode insert (5.53); Idle-time prefetch (5.54).
- Crash recovery transparency (5.59); Document timeline (5.63); Sentence/paragraph nav (5.64); Word-count goal (5.65); Reading position memory (5.66); Compare with clipboard (5.67); Insert from file (5.68); Selection statistics shortcut (5.69); Audio cues opt-in (5.70); Quiet mode (5.71); Temporary trust (5.72); Crash-report opt-in (5.75).

### 16.4 v1.1

Plugin system; TinySpell interop plugin (dictionary sync only); additional AI providers; Pandoc bridge; Whisper transcription importer; LibreOffice headless bridge plugin (raises legacy `.doc`, `.ppt`, `.xls`, `.wpd`, iWork, OneNote quality from C to A); Calibre bridge plugin (raises `azw3`, `mobi`, `fb2`, `lit` to A); braille back-translation via liblouis; auto-update; spell-check contextual reranker (opt-in experimental); DjVu, comics, WARC, MSG/PST/MBOX.

### 16.5 v1.2

Right-to-left UI; additional languages; optional split view (still standard controls); reading-order learning per document; contextual reranker promoted to default; per-paragraph language detection; project workspaces and Find in Folder; chat-export readers (WhatsApp, Telegram, Slack, Discord, Teams, Zoom, Otter, ChatGPT) as plugins.

---

## 17. Backlog and deferred items

Everything below is intentionally out of v1.0. Each item is either yellow (achievable but requires more engineering than the v1.0 quality bar permits in time) or red (depends on unstable third-party formats, large native dependencies, or research-flavoured uplift we will not promise without measurement).

The organising principle is simple: **v1.0 ships only Confidence A. Confidence B and C land in v1.1–1.3 behind opt-in plugins and feature flags, with quality grades shown to the user.**

### 17.1 Format support deferred to plugins (v1.1+)

| Format | Why deferred | Target plugin |
| --- | --- | --- |
| Legacy Word `.doc`, PowerPoint `.ppt`, Excel `.xls` | Need headless LibreOffice for high quality; LibreOffice is a ~300 MB dependency | LibreOffice Bridge |
| WordPerfect `.wpd`, Works `.wps`, Windows Write `.wri`, StarOffice | Python bindings flaky on Windows; covered well by headless LibreOffice | LibreOffice Bridge |
| Apple iWork `.pages`, `.key`, `.numbers` | Modern iWork is a proprietary IWA archive; coverage is partial | iWork Bridge (best-effort) |
| OneNote `.one` | Closed format, no stable open library | OneNote Bridge via Microsoft Graph (requires sign-in) |
| Kindle `.azw3`, `.mobi`, FB2, LIT, LRF, PRC, PDB, TCR | Best handled by Calibre's conversion engine | Calibre Bridge |
| Kindle `.kfx` | DRM-protected by design; Quill will not break DRM | Calibre Bridge (user must already have a DRM-stripped copy) |
| DjVu | Native `djvulibre` dependency; installer weight | DjVu Plugin |
| Comics `cbz`, `cbr` | RAR (`cbr`) requires non-free `unrar.dll` | Comics Plugin |
| PostScript `ps`, `eps` | Needs Ghostscript native binary | PostScript Plugin |
| XPS, OXPS | Niche; needs additional reader | XPS Plugin |
| MSG, PST, MBOX | `libpff` works but coverage on encrypted/corporate PSTs is uneven | Mail Bridge |
| Web archives WARC, WACZ, `.webarchive` | Format zoo; useful but not ubiquitous | Web Archive Plugin |
| Parquet, Feather | Niche analyst use; large native deps | Data Files Plugin |
| EVTX, ETL | Native Windows log formats; niche audience | Logs Plugin |
| HEIC, AVIF, JP2 | Native binary dependencies (`pillow-heif`, `pillow-avif-plugin`) | Modern Images Plugin |
| Chat exports (WhatsApp, Telegram, Slack, Discord, Teams, Zoom, Otter, ChatGPT) | Export formats churn 2–4 times per year; requires ongoing maintenance | Chat Exports Plugin (independently versioned) |
| OneNote, Evernote `.enex`, Bear, Simplenote | Mixed formats; per-app quirks | Notes Bridge Plugin |
| Audio + transcript pair playback | Needs media playback; out of scope for core editor | Audio Transcript Plugin |

### 17.2 Features deferred

- **Spell-check contextual reranker.** Ships as opt-in experimental in v1.1 once measured uplift over Hunspell-alone is demonstrated on a labelled corpus.
- **Per-paragraph automatic language detection** for the spell-check dictionary stack. Short paragraphs and code-mixed text make this unreliable today.
- **Tier-2 "enhanced local" PDF extractor.** No pure-Python local layout analyser meets the bar. v1.0 ships tier 1 (local) and tier 3 (opt-in AI). A real tier 2 returns when there is a credible local model.
- **PDF heading synthesis from font-size analysis** when no embedded bookmarks exist. Available as an opt-in experimental switch but not promoted in v1.0.
- **Auto-update.** v1.0 ships manual update check with signed manifest. Squirrel-style auto-update lands in v1.1.
- **NVDA speech-viewer CI harness.** No supported automation API; we will build a test driver in v1.1.
- **Dynamic screen-reader shortcut introspection.** v1.0 uses a curated static list of well-known NVDA, JAWS, and Narrator chords; explains conflicts using that list. Dynamic introspection of user-customised SR bindings remains out of scope (no public API).
- **Right-to-left UI.** v1.2.
- **Project workspaces and Find in Folder.** v1.2.
- **Multi-cursor / column selection.** Not planned; conflicts with screen-reader navigation patterns.
- **History panel (visual undo stack).** Backlog.
- **Macro recording and playback.** Backlog.
- **Linked-notes / wikilink editor (Obsidian-style).** Backlog.
- **Per-file-class backup retention policy.** v1.0 ships a single global retention rule (5.13). v1.1 introduces per-format-class defaults (e.g. 100 backups for source code, 25 for long-form documents) once we have telemetry on user save patterns.
- **Single-line compose box mode.** A small, screen-reader-optimised composer dialog whose Enter sends back to the main editor at the cursor. Useful for slow-speech users; needs user testing to confirm it is worth the surface area. Backlog for v1.1.

### 17.4 Explicitly out of scope for Quill (any version unless re-evaluated)

Quill is opinionated about what it is *not*. The following are intentionally and permanently out of scope unless a future PRD revision re-opens the question.

- **Visual word-processor styling in the editor.** No bold/italic/colour as direct formatting. Quill is screen-reader-first; users who want WYSIWYG should use Word. Markdown supports inline emphasis textually.
- **Real-time collaborative editing.** Not in v1.x. The architecture does not preclude it; we are not committing to it.
- **Cloud-sync of documents.** Sync is for keymap and settings only (8.8). Document storage stays on the user's machine and chosen cloud-drive folder.
- **Mobile, web, macOS, or Linux ports.** Cross-platform is post-v2 at earliest. The `core/` layer has no `wx` so it remains *possible*, not *committed*.
- **Voice input / dictation.** Use Windows dictation; Quill does not reinvent it.
- **AI authoring assistant.** No autocomplete, no paragraph rewriting, no "continue my thought" in v1.0. The AI surface is strictly reading-order repair and OCR escalation — both opt-in, both gated.
- **Project workspaces and Find in Folder.** Deferred to v1.2 (see 17.2).
- **Embedded media playback inside documents.** Out of scope for the editor.
- **PDF form filling and signing.** Out of scope.
- **Macro recording and playback.** Out of scope for v1.x.
- **Bundled font installation.** Quill uses system fonts only.
- **Telemetry by default.** Telemetry is and remains opt-in, off out of the box.
- **Anything that breaks DRM.** Quill will not include or escalate to tooling that removes DRM from any file, including KFX.

### 17.3 Confidence grades shown to the user

The Format Support settings page displays a grade per format:

- **Grade A**: bundled engine, high coverage, extensively tested. (All v1.0 in-box formats.)
- **Grade B**: bundled engine with known edge cases, or plugin with a stable upstream. Quality is good, occasional fallbacks expected.
- **Grade C**: plugin required to read at all, or the upstream format itself is unstable. Best-effort.

Grade is displayed prominently in the Open dialog when the user picks a file of a non-A format, with one line of context (“Kindle `.azw3` requires the Calibre Bridge plugin; current grade B with Calibre installed”) so expectations are set before the user hits Enter.

---

## 18. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Custom wx behaviour breaks a screen reader on a Windows update | Strict policy of stock controls; CI accessibility tests; rapid patch process |
| PDF extraction quality varies wildly | Layered extractors with scoring; manual escalation tiers; opt-in AI repair |
| AI provider API drift or pricing change | Provider-agnostic interface; user supplies key |
| Plugins introduce accessibility regressions | Manifest must declare UI surfaces; review checklist; plugins disabled by default |
| Custom spell engine underperforms TinySpell/Word | Layered architecture; Hunspell baseline; learning loop; published benchmarks |
| Keymap conflicts with screen-reader shortcuts | Explicit detection at capture time; refuse to capture conflicting chords with clear explanation |
| Localisation lags | Ship English first; community translation site; per-language readiness gates |
| Users expect bold and italic | Clear positioning; markdown supports inline emphasis textually; v1.x evaluation only after stable base |

---

## 19. Open questions

1. License: MIT for maximum adoption, or GPL to keep derivatives open. Leaning MIT.
2. Branding: Quill is a placeholder. Final name to be chosen with community input.
3. Should the contextual reranker be opt-in given memory cost?
4. JAWS scripts: ship a small one for live-region parity, or rely on `wx.Accessible` alone?
5. Hosting model for the community plugin registry.
6. Two-key chord sequences in default keymap: how many should we ship by default, given screen-reader users often prefer single chords?

---

## 20. Why this can be magical

The magic is not in any single feature. It is in the absence of friction:

- The window opens and the cursor is in the right place.
- Save just works. Save As appears exactly when it should.
- A PDF that was unreadable an hour ago becomes a clean searchable document with one keystroke.
- A bookmark you set last week still lands on the right paragraph after the document grew by three pages.
- The command palette knows the word you half remembered, and it tells you which key triggers it so you can learn the keystroke next time.
- If a keystroke does not suit you, you change it from the same palette without leaving the flow.
- Spell check is fast, local, and gets better the longer you use it. It never sends your writing anywhere.
- The screen reader never says anything you did not need to hear, and never goes quiet when you needed it to speak.
- When the power dies, the next launch returns your work.

Quill aims to feel like a very good fountain pen: simple in the hand, faithful on the page, and quietly delightful every time you reach for it.

---

## 21. Project delivery TODO (living checklist)

Last updated: 2026-05-28

Todo counts: **160 total** | **160 completed** | **0 remaining**

This is the implementation checklist for v1.0.0 and immediate post-1.0 foundations. It is intentionally granular and will be updated in-place as work lands.

### 21.1 Application shell and document lifecycle

- [x] Bootstrap wxPython app shell with menu bar, editor, status bar.
- [x] Add optional system-tray mode (send to tray, restore, tray menu exit).
- [x] Implement true multi-document model (tabs/window document switcher).
- [x] Implement document close semantics (close tab, prompt/save/discard, frame-close handling).
- [x] Implement recent-document keyboard cycling (`Ctrl+Tab`, `Ctrl+Shift+Tab`) baseline.
- [x] Implement single-instance handoff IPC (open-in-existing-instance on second launch).
- [x] Implement F6/Shift+F6 region cycling across all declared regions.
- [x] Show live caret position in status bar (`Ln`, `Col`).
- [x] Add configurable status bar item layout (reorder + hide/show) through Status Bar Settings.
- [x] Show insert/overwrite mode in the status bar (`INS` / `OVR`).
- [x] Implement full status-bar interactive cell model from section 5.1b.
- [x] Add Save All command.
- [x] Add Reload from Disk command.
- [x] Add Restore Backup dialog with backup history selection.
- [x] Add sessions submenu for switching open documents.
- [x] Implement complete file menu set (sessions submenu, print/page setup).
- [x] Add Open Recent → Clear Recent Files action.
- [x] Add Save As Plain Text command.

### 21.2 Core editing and formatting

- [x] Open/save/save-as for plain text and markdown.
- [x] Soft-wrap toggle command and persisted preference.
- [x] Case transforms (upper/lower/title/sentence/toggle).
- [x] Line operations (move up/down, duplicate, delete, join).
- [x] TextMonkey-style cleanup transforms.
- [x] Sort selected lines ascending/descending.
- [x] Reverse lines.
- [x] Remove duplicate lines.
- [x] Trim trailing whitespace.
- [x] Normalize whitespace.
- [x] Convert indentation between tabs and spaces.
- [x] Markdown/HTML formatting commands: bold, italic, heading 1-6 with `Ctrl+Alt+1..6`.
- [x] Selection-aware tag wrapping (insert paired markers around highlighted text).
- [x] HTML tag picker with attribute entry.
- [x] Markdown tagging picker (code block, lists, link/image, table, footnote snippets).
- [x] Toggle line comment command.
- [x] Toggle block comment command.
- [x] Indent/outdent commands.
- [x] Insert list submenu commands (bullet/numbered/task) as dedicated menu actions.
- [x] Insert table workflow (guided table builder dialog).
- [x] Insert code block command with optional language hint support for Markdown/HTML.
- [x] Insert footnote command (baseline snippet insertion for Markdown/HTML).
- [x] Select line/paragraph/block and mark-ring operations.
- [x] Select to start/end of line and start/end of document commands.
- [x] Extend Selection mode toggle (`F8`) with movement-key range growth (Word-style shiftless selection).
- [x] Context menus in editor, status bar, and frame surface with right-click and Application/Menu-key invocation.
- [x] Add heading-level adjust commands (`Alt+Shift+Left` / `Alt+Shift+Right`) for Markdown/HTML headings.

### 21.3 Navigation, search, structure, and links

- [x] Go To Line with optional column target (`line,column`).
- [x] Go To Page baseline command (using form-feed page markers).
- [x] Find and Replace All.
- [x] Persistent search history.
- [x] Insert Link and Follow Link commands.
- [x] Set Bookmark and Go To Bookmark baseline commands.
- [x] Find Next / Find Previous command set (F3 / Shift+F3).
- [x] Find All Matches command (Alt+F3 baseline dialog).
- [x] Heading/block navigation commands.
- [x] Outline Navigator (tree model + jump + optional pinned mode).
- [x] Recent locations back/forward ring.
- [x] Match bracket and structural navigation.

### 21.4 Metrics, spell, and tools

- [x] Word count and baseline document stats.
- [x] Spell-check dialog and dictionary stack UX.
- [x] As-you-type spell check toggle + next misspelling flow.
- [x] Add-to-dictionary scopes (personal/document/project).
- [x] Accessibility Audit command and results panel.
- [x] Link inventory and alt-text catalog tools.
- [x] Compare-with-file diff workflow and interactive compare mode.
- [x] Read-aloud controls and voice selection.

### 21.4a Trust and verification

- [x] Document intake report on open.
- [x] Copy With Source command with source reference text.
- [x] Extraction quality review for PDF-derived documents.
- [x] Bad extraction support package command.
- [x] Context-sensitive "What Can I Do Here?" help.
- [x] Safe mode startup for troubleshooting.
- [x] Portable mode clarity and first-run storage choice.
- [x] Golden document corpus for release verification.

### 21.4b Power search

- [x] Plain text, whole word, regular expression, and wildcard search modes.
- [x] Plain-language regex error reporting.
- [x] Regex helper with common tokens and explanations.
- [x] Replace-all preview before apply.

### 21.5 Persistence, safety, and recovery

- [x] Persistent settings store.
- [x] Persistent keymap store.
- [x] Persistent recent files.
- [x] Backup snapshots on save.
- [x] Autosave snapshots.
- [x] Crash recovery flow at startup.
- [x] Persistent undo model (optional mode).
- [x] Trusted locations system and file trust prompts.
- [x] Notification center persistence model.

### 21.6 Command palette and keymap system

- [x] Command registry and command palette dialog.
- [x] Live keybinding labels in menu entries.
- [x] Runtime accelerator table generation from keymap.
- [x] Palette prefix modes (`>`, `?`, `:`, `~`) and scoped command sets.
- [x] Palette fuzzy ranking with frequency/recency tie-breakers.
- [x] Keymap editor UI with conflict detection and capture dialog.
- [x] Import/export/reset keymap workflows.

### 21.7 Format support and I/O coverage

- [x] Base text/markdown read-write path.
- [x] HTML read-write path.
- [x] DOCX read path (plus text-focused export path).
- [x] PDF tier-1 extraction path with quality scoring.
- [x] OCR bridge path and user-facing consent/progress UX.
- [x] EPUB/RTF/ODT baseline readers.
- [x] EPUB navigator dialog with chapter tree, preview pane, and chapter-open flow back into editor.
- [x] Config/data format readers (JSON/YAML/TOML/XML/CSV/TSV).
- [x] Notebook and SQLite read-only renderers.
- [x] Open from URL flow with safety checks.
- [x] Open from URL baseline (HTTP/HTTPS text fetch; advanced safety checks pending).

### 21.8 Accessibility and UX hardening

- [x] Screen-reader announcement bridge baseline.
- [x] Region entry/exit announcement consistency across all dialogs and panels.
- [x] Accessibility transcript capture for test harnesses.
- [x] Keyboard trap audit and tab-order snapshots.
- [x] Contrast and low-vision theme validation.
- [x] Controlled vocabulary + plain-language linting hooks.

### 21.9 Windows integration

- [x] Shell integration (Open With, file associations, jump list).
- [x] DPAPI key storage for provider credentials.
- [x] Screen-reader detection and adaptive hints.
- [x] High-contrast token mapping with Windows settings sync.
- [x] Installer flow (Inno Setup) and portable build variant.

### 21.10 AI, OCR, and optional network features (deferred to v1.1)

Deferred to v1.1:

- AI provider abstraction and per-provider adapters.
- Explicit consent-gated network action layer.
- Reading-order repair pipeline (opt-in).
- Task progress and cancellation UX for long-running operations.
- [x] Signed update manifest fetch and verification.

### 21.11 Engineering quality gates and release

- [x] Python project scaffold, lint/type/test tooling baseline.
- [x] Core unit-test suite for implemented modules.
- [x] Integration test corpus and runner wiring.
- [x] Accessibility test suite and CI automation.
- [x] Performance smoke suite aligned to section 11 thresholds.
- [x] SBOM generation, vulnerability scanning, and provenance artefacts.
- [x] Build/sign/release pipeline for Windows artefacts.
- [x] Third-party notices generation and license gate.

### 21.12 Documentation and readiness

- [x] Engineering docs baseline (`docs/engineering/*`).
- [x] Roadmap mapping and architecture/module contracts.
- [x] PRD updates for HTML/Markdown tag picker and formatting shortcuts.
- [x] User guide and keyboard reference auto-generation pipeline.
- [x] Accessibility conformance report (ACR/VPAT) generation toolchain.
- [x] Diagnostics bundle specification and support runbook.

### 21.13 Profile safety and recovery

- [x] Add a "Why Don’t I See a Feature?" help command.
- [x] Add profile switch preview and change summary text.
- [x] Add undo for the last profile change.
- [x] Add emergency reset to the Essential profile from launch and recovery.
- [x] Add profile health checks to Quill Doctor and diagnostics.
- [x] Add CI coverage gates for feature IDs across commands and surfaces.
- [x] Add profile-aware keyboard reference views.
- [x] Add profile-aware welcome guide content.
- [x] Add privacy, network, dependency, and maturity labels for features.
- [x] Add profile import safety validation and locked feature protection.
- [x] Add "Show what changed" reporting after profile switches.
- [x] Add feature-flag coverage tests for new commands and surfaces.

### 21.14 Feature registry and profiles

- [x] Add a central feature registry module with metadata and dependency graphs.
- [x] Add layered feature-profile loading and merging.
- [x] Add shipped profile definitions for Essential, Writer, Reader and Student, Office and Admin, Accessibility Professional, Developer and Power Text, Low Vision, Braille and Screen Reader Power User, and Full Quill.
- [x] Add a Profiles and Features settings page.
- [x] Add first-run profile selection onboarding.
- [x] Add command, menu, status-bar, settings, help, and format-handler feature ID gating.
- [x] Add dependency enforcement when enabling and disabling features.
- [x] Add profile import/export storage with schema validation.
- [x] Add locked safety rules that cannot be overridden by user profiles or imports.
- [x] Add feature metadata labels for risk, maturity, privacy, and network impact.
- [x] Add profile comparison preview in the Profiles and Features page.

### 21.15 Macro and compare expansion

- [x] Implement macro command capture across menu/shortcut/palette execution (excluding macro control commands and playback recursion).
- [x] Complete macro management UX and persistence polish for Start/Stop/Play/Manage workflows.
- [x] Expand interactive compare commands (next/previous/current/list/sync toggle/options) beyond diff-tab-only hunk navigation.
- [x] Add multi-document interactive compare support (3+ open docs) with structured announcements.
- [x] Add compare summary and copy/export actions (copy current/all differences, save markdown summary).
- [x] Audit transform/convert menu placement and command-ID consistency after Convert-menu migration.
- [x] Synchronize PRD checklist details with implemented macro and compare scope.
- [x] Run macro/compare regression suite and resolve resulting failures.
