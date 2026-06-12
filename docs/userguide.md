# Quill User Guide

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

Quill is a screen-reader-first writing and reading environment for Windows. It is designed to feel calm, predictable, deeply keyboard-friendly, and respectful of your focus. It is also ambitious. Quill is not only a place to write plain text. It is a place to open difficult documents, inspect structure, navigate long material, compare revisions, prepare content for Markdown or HTML, and work with accessibility and extraction issues without leaving the editor.

This guide is aligned to Quill 0.1.5 Beta, built by Blind Information Technology Solutions (BITS) together with Community Access.

This guide is written as a companion, not a reference wall. Read it from the beginning if you are new to Quill. Dip into the sections that matter most if you already know what kind of work you want to do.

Quill is also in beta. Expect polish, depth, and real daily utility. Also expect rough edges, unfinished flows, and the occasional surprise. If you find something confusing or broken, that is useful information. Quill is becoming stronger because real people are trying it on real work.

## Table of Contents

- [Start Here](#start-here)
- [What Quill Feels Like](#what-quill-feels-like)
- [Your First Session](#your-first-session)
- [Getting Around QUILL](#getting-around-quill)
- [Command-Line Launching](#command-line-launching)
- [The Main Window](#the-main-window)
- [The Menu Bar Reference](#the-menu-bar-reference)
- [Writing and Editing](#writing-and-editing)
- [Search, Replace, and Deep Navigation](#search-replace-and-deep-navigation)
- [QUILL Quick Nav Mode](#quill-quick-nav-mode)
- [Formatting and Markup Work](#formatting-and-markup-work)
- [Tools for Reading, Review, and Inspection](#tools-for-reading-review-and-inspection)
- [GLOW Workflows Inside Quill](#glow-workflows-inside-quill)
- [Accessibility and Low-Vision Features](#accessibility-and-low-vision-features)
- [Quill on macOS](#quill-on-macos)
- [Profiles, Keyboard Packs, and Customization](#profiles-keyboard-packs-and-customization)
- [Trust, Recovery, Sessions, and Safety](#trust-recovery-sessions-and-safety)
- [Working with Different Document Types](#working-with-different-document-types)
  - [Plain text](#plain-text)
  - [Markdown](#markdown)
  - [HTML](#html)
  - [RTF](#rtf)
  - [CSV and TSV](#csv-and-tsv)
  - [Word (.docx and .doc)](#word-docx-and-doc)
  - [EPUB](#epub)
  - [PowerPoint (.pptx and .ppt)](#powerpoint-pptx-and-ppt)
  - [Excel-style spreadsheets (.xlsx and .xls)](#excel-style-spreadsheets-xlsx-and-xls)
  - [PDF and OCR-derived text](#pdf-and-ocr-derived-text)
  - [Remote files (FTP, SFTP, HTTPS, WebDAV, S3)](#remote-files-ftp-sftp-https-webdav-s3)
  - [GitHub Remote Files](#github-remote-files)
- [Help, Learning, and Daily Confidence](#help-learning-and-daily-confidence)
  - [Context-Sensitive Help (F1)](#context-sensitive-help-f1)
  - [Personalising QUILL](#personalising-quill)
- [Translation and Community Localization](#translation-and-community-localization)
  - [How the Translation Pipeline Works](#how-the-translation-pipeline-works)
  - [Contributing Translations](#contributing-translations)
  - [Translation Roles and Responsibilities](#translation-roles-and-responsibilities)
  - [Speech String Guidelines](#speech-string-guidelines)
- [Checking for Updates](#checking-for-updates)
- [Beta Feedback and Bug Reporting](#beta-feedback-and-bug-reporting)
- [A Fast Shortcut Tour](#a-fast-shortcut-tour)
- [Control Reference](#control-reference)

## Start Here

If you only have five minutes, do this:

1. The first time QUILL starts, the **Personalise QUILL** wizard offers to set up your keyboard layout, profile, and optional features in about two minutes. Complete it or dismiss it; you can re-run it from **Help → Personalise QUILL** at any time.
2. Press `Ctrl+N` to create a new document, or press `Ctrl+O` to open one.
3. Type a few lines.
4. Press `Ctrl+Shift+P` to open the Command Palette. Type `guide`, `spell`, `compare`, or `glow` and notice how quickly Quill turns intent into action.
5. Press `F6` to move into the status bar and hear how Quill treats even the bottom of the window as a working surface.
6. Press `F7` for spell check, `Ctrl+F` to search, or `Ctrl+K` to insert a link.
7. Press `F1` on any control to hear what it does and see its keyboard shortcuts.

If you ever feel lost, press `F1` for immediate help on the focused control, or use **Help → What Can I Do Here?** for document-context guidance. Think of those commands as the editor quietly putting a mentor beside you.

## What Quill Feels Like

Quill is built around a few promises.

- The keyboard is never second-class.
- Screen readers are not an afterthought.
- Every major action is reachable from the menu, the palette, and the command system.
- Documents open locally and stay local unless you explicitly choose a network-aware action.
- The editor should tell you what changed, where you are, and what is possible next.

In practice, that means Quill spends a lot of attention on focus movement, meaningful status updates, discoverable commands, and native Windows controls. It also means Quill tries to reduce fear. When you open a recovered draft, compare two files, inspect extraction quality, or apply a deterministic GLOW fix, the point is not to feel clever. The point is to feel safe.

## Your First Session

Imagine your first meaningful visit to Quill.

You launch the app. There is no splash screen. The window appears quickly, with a menu bar, an editor, and a status bar. If Quill detects a screen reader, it adjusts its hints and announcement style. If Quill notices an earlier crash or autosave state, it offers recovery instead of silently hoping you forgot.

From there, a natural first session looks like this:

1. Open a file with `Ctrl+O` or create one with `Ctrl+N`.
2. Read or write in the editor.
3. Use `Ctrl+Shift+P` to explore commands without memorizing everything.
4. Use the **Navigate** menu to jump by line, heading, block, region, or page.
5. Use the **Tools** menu for spelling, word count, extraction review, compare, macros, regex help, and GLOW workflows.
6. Open **Help → Open Keyboard Reference** to see the exact shortcuts that exist in your current configuration, including your keyboard pack and any custom bindings.

That first session matters because it teaches the most important Quill habit: you do not need to hunt. If an action exists, Quill wants you to be able to reach it from where you already are.

## Getting Around QUILL

QUILL is designed so you never need to memorize an action to reach it.

### F1 — help on the focused control

Press `F1` on any focusable control — a dialog field, a button, a menu item, the editor itself — and a small help dialog opens. It tells you what the control does and what keyboard shortcuts apply to it. The full text lands in one read-only field so your screen reader announces everything in one pass when the dialog opens.

- `F1` — help on the focused control
- `Ctrl+F1` — open the full User Guide
- `Shift+F1` — open "What Can I Do Here?" for the active document context

See [Context-Sensitive Help (F1)](#context-sensitive-help-f1) for full details.

### The QUILL key

The **QUILL key** is `Ctrl+Shift+Grave` (the key above Tab). Press it once to arm a one-shot prefix, then follow with a second key to perform a command. Press it twice to lock QUILL Quick Nav mode until `Esc`.

Common QUILL-key chords:

| Chord | Command |
|-------|---------|
| QUILL key, then `N` | Enter Quick Nav browse mode |
| QUILL key, then `G` | Open Go to Anything |
| QUILL key, then `M` | Paste HTML clipboard as Markdown |
| QUILL key, then `R` | Open file from remote |
| QUILL key, then `A` | Selection actions |
| QUILL key, then `?` | Show the QUILL key cheat sheet |
| QUILL key, then `Esc` | Cancel the prefix |

### Command Palette

`Ctrl+Shift+P` opens the Command Palette — a searchable list of every registered command. Type any part of a command name to filter. Press Enter to run it. This is the fastest way to reach any action without memorizing its key or menu path. Searching `guide`, `spell`, `compare`, or `glow` from the palette is a good first practice.

### Navigation anchors

The status bar (`F6` to focus it) is a working surface, not decoration. Each cell announces meaningful information and most cells open a related dialog when you press Enter or click. `Shift+F6` moves focus back to the editor.

Reach any menu from the keyboard: `Alt+F` for File, `Alt+E` for Edit, `Alt+V` for View, `Alt+T` for Tools, `Alt+H` for Help. All menu items have keyboard mnemonics.

The Navigate menu groups document-level movement: go to line, go to heading, go to entry in notebook, heading organizer, outline navigator, back and forward location history, and structural next/previous. When you need to move across a large document, start there.

## Command-Line Launching

Quill supports command-line startup options for scripted workflows and direct navigation.

Supported options:

- `--help`: show command help and exit.
- `--version`: print QUILL version and exit without launching the UI.
- `--safe-mode`: launch with optional state disabled.
- `--reset-profile`: reset feature profile store before launch.
- `--diagnostics`: start with diagnostics tracing enabled.
- `--dump-stacks`: write a thread-stack dump and exit.
- `--line N`: 1-based line for the first startup file.
- `--column M`: 1-based column for the first startup file.
- `--new-window`: force a new process instead of forwarding to an existing instance.
- `--wait`: when forwarding to an existing instance, wait for that instance to close.

Examples:

- `python -m quill --version`
- `python -m quill notes.md --line 40 --column 5`
- `python -m quill --new-window notes.md`

## The Main Window

Quill keeps its main window intentionally simple.

### Menu bar

The menu bar follows the Windows and Office order you likely expect:

- File
- Edit
- View
- Insert
- Format
- Navigate
- Search
- Tools
- Window
- Help

The menu bar is exhaustive rather than decorative. If Quill can do something, there is almost certainly a menu path for it.

### Editor surface

The editor is the heart of Quill. It is where writing happens, where extracted text lands, where reports open as ordinary tabs, and where GLOW previews and compare summaries feel like first-class documents rather than pop-ups.

The editor supports:

- plain text writing
- Markdown-aware authoring
- HTML-aware authoring
- structural navigation
- selection helpers
- text cleanup
- spell and thesaurus workflows
- link insertion and link following
- compare-driven review

### Tabs and document switching

Quill is multi-document. Each open file lives in a notebook tab. You can:

- move between documents with `Ctrl+Tab` and `Ctrl+Shift+Tab`
- close the active document with `Ctrl+W`
- use the tab context menu to close one tab, close other tabs, or close tabs to the right
- reveal a saved document in File Explorer directly from the tab context menu

Quill also opens generated artifacts as tabs. The welcome guide, keyboard reference, compare summary, GLOW audit report, and GLOW fix preview all feel like normal working tabs. That is deliberate. Artifacts should stay close to the work that created them.

### Status bar

The status bar is interactive. It is not just a strip of passive text.

Use `F6` to move into it. Once there, you can move between cells and activate them. Depending on your layout and current state, the status bar can surface:

- current message
- line and column
- word count
- insert or overwrite mode
- selection size
- encoding
- line endings
- spell-check state
- background task state
- notifications
- read-aloud state
- autosave timing
- current search term
- file path or unsaved state

You can reorder or hide status items through **Tools → Customize & Support → Status Bar Layout...**.
Right-click a focused status cell to **Activate**, **Hide this item**, or open **Status bar settings...**.
Use **Restore Defaults** in status bar settings to reset visibility and order.
When title mode is set to full path, Quill automatically hides the duplicate file-path status cell.

### Region cycling

Use `F6` and `Shift+F6` to move between major regions. Quill treats region movement as a first-class accessibility feature. If you write, inspect, and navigate entirely from the keyboard, this becomes second nature quickly.

## The Menu Bar Reference

This section walks the entire menu bar in the order you will encounter it.

### File

The **File** menu is the full document lifecycle.

- **New** creates a blank document.
- **Open...** opens a document from disk.
- **Open Recent** returns quickly to recently used files.
- **Open from URL...** downloads a document or text resource through an explicit safety flow that confirms host and expected size.
- **Open from Remote**, **Save to Remote**, **Save Copy to Remote**, and **Manage Remote Sites...** (in the *Open from Remote* submenu) open, save, and administer saved sites over **FTP, SFTP, HTTPS, WebDAV, and Amazon S3 (or any S3-compatible service)**. Each remote operation is explicit, runs over a verified TLS context, announces host and expected size, and never writes to disk before you confirm.
- **Snapshots** lets you save and reopen groups of documents as a single workspace snapshot, similar to lightweight workspaces in Visual Studio Code.
- **New from Clipboard** opens a new document seeded with the current clipboard text.
- **Save** writes the current document.
- **Save As...** writes to a new path, converting the document to the file type you choose in the dialog. Quill keeps your text as portable Markdown-style markup, so picking **Rich Text Format (\*.rtf)** writes real RTF, **HTML (\*.html)** writes a standalone web page, and **Text (\*.txt)** writes clean prose with the markup removed. Choosing **Markdown (\*.md)** keeps the markup verbatim. The file's extension always decides the format; if you type a name without an extension, the selected type supplies one. When Save As changes the format, Quill can reload the file so the editing surface matches it — for example, opening a freshly saved `.rtf` in the Rich text editor. By default it asks first with a Yes/No prompt (reloading replaces the editor contents with the saved file); set **Settings → Editing → Reload after Save As to match the format** to *Reload automatically* or *Keep current surface* to skip the prompt.
- **Save All** writes every modified open document.
- **Save As Plain Text...** exports a clean plain-text version. Because plain text has no links, **Settings → Editing → Links in plain-text export** controls how Markdown links are written: keep the link text and its URL (the default, so you never lose where a link pointed), the link text only, the URL only, or the original Markdown link. This setting also applies whenever Save As writes a `.txt` file.
- **Reload from Disk** throws away in-memory edits and reloads the file from storage after confirmation.
- **Restore Backup...** lets you restore a saved backup version.
- **Page Setup...** and **Print...** support paper and print workflows.
- **Run Current File** executes the saved file with its associated tool, and **Open Target at Cursor** opens the path or link under the caret.
- **Rename Current File...** and **Delete Current File...** manage the file on disk from inside the editor.
- **Close Document** closes the current tab.
- **Exit** closes the application.

The File menu is also where Quill quietly proves that it respects risk. Reload is explicit. Backup restore is explicit. URL opening is explicit. Nothing important is hidden behind a side effect.

### Edit

The **Edit** menu is where writing muscles live.

Standard clipboard commands are here:

- Undo
- Redo
- Cut
- Copy
- Paste
- Copy With Source
- Select All

Quill then goes further with selection- and navigation-aware editing:

- **Find...**, **Replace...**, **Find Next**, **Find Previous**, and **Find All Matches** all live here. Replace includes a **Replace All** action in its dialog, so bulk replacement stays in one place.
- **Word Prediction...** opens inline word and tag suggestions.
- **Extend Selection Mode** turns selection growth into a dedicated mode.
- **Selection** submenu includes Select Line, Select Paragraph, Select Block, Select to Start or End of Line, Select to Start or End of Document, and a nested **Recent Marks (Ring)** group (set a temporary mark, jump to previous marks, swap cursor and mark, list recent marks).
- **Follow Link** opens the link under the caret. (Link *insertion* now lives in the **Insert** menu.)
- **Paste HTML as Markdown** converts rich clipboard HTML to Markdown as it pastes.
- The deletion group — **Delete to Line Start**, **Delete to Line End**, **Delete to Document Top**, **Delete to Document Bottom**, and **Delete Paragraph** — removes text relative to the cursor.

**Preferences...** and **Customize Menus...** live with the rest of Quill's configuration under **Tools -> Customize & Support**.

### View

The **View** menu controls how Quill presents your document on screen without changing your content.

- **Toggle Soft Wrap** changes line wrapping without modifying the file.
- **Auto Side-by-Side Preview** opens a live preview beside the editor automatically.
- **Show Tab Control** toggles the visible document tab strip.
- **Wrap Find Searches** controls whether Find wraps past the end of the document.
- **Start With No Document Open** makes Quill open into an empty workspace instead of a starter document.
- **Preview...**, **Preview Side by Side**, **Focus Preview**, and **Browser Preview...** open rendered views of the current document.

Preference-style toggles that used to live here — theme/dark mode, system-tray mode, title-bar path style, dirty-title style, persistent undo, spell-check-as-you-type, and word-prediction-as-you-type — now live in the registry-driven **Settings** dialog (**Tools -> Customize & Support -> Preferences...**), where they are persisted in one place.

### Insert

The **Insert** menu adds structured content at the cursor.

- **Insert Link...** creates a format-aware link.
- **Heading** submenu: insert Heading 1 through 6, **Decrease Level** / **Increase Level**, and **Style Headings...** (font, size, alignment) for the current level or all levels.
- **List** submenu: **Bullet**, **Numbered**, **Task**, and **List Manager...**.
- **Insert Code Block**, **Insert Footnote**, **Insert Table...**, **Insert HTML Tag...**, and **Insert Markdown Tag...**.
- **Insert Snippet...** and **Manage Snippets...** for reusable text with placeholders.
- **Special Character...**, **Date and Time**, **Calculated Date...**, and **File Content...** insert symbols, timestamps, computed dates, and the contents of another file.

Quill treats Markdown and HTML as working surfaces, not special-purpose export formats, so tag insertion lives here beside the structural inserts.

#### Word prediction and snippets

Quill separates live prediction from snippet insertion so the hotkeys feel like a modern editor:

1. Press `Ctrl+Space` to open **Word Prediction** (also on **Edit -> Word Prediction...**).
2. Type to surface matching document words, HTML tags, and Markdown tags.
3. Use arrow keys to choose a result and press Enter to insert it.

For setup and maintenance:

- Press `Ctrl+Alt+Space` for **Insert Snippet**.
- Press `Ctrl+Alt+Shift+Space` for **Manage Snippets** (create, edit, delete, import, export, and starter packs).
- Open **Preferences -> Install Starter Snippet Packs** to install sample libraries for daily writing, developer flow, and support/accessibility notes.
- In **General Preferences**, toggle **Word prediction and tag IntelliSense** or **Expand snippet triggers while typing** as needed.

Snippets support placeholders such as `${input:name}`, `${choice:a|b}`, `${date}`, `${time}`, and `${cursor}`.

### Format

The **Format** menu handles presentation and markup-aware editing of existing text.

Case operations live in the **Change Case** submenu:

- Upper Case
- Lower Case
- Title Case
- Sentence Case
- Toggle Case

Comment and indentation tools:

- Toggle Line Comment
- Toggle Block Comment
- Indent
- Outdent

Line operations:

- Move Line Up
- Move Line Down
- Duplicate Line
- Delete Line
- Join Lines

Inline emphasis:

- Bold
- Italic

The **Transform Lines** submenu gathers every line and text transform in one place: **Number Lines...**, **Hard-Wrap Lines...**, **Sort Lines Ascending**, **Sort Lines Descending**, **Reverse Lines**, **Remove Duplicate Lines**, **Trim Trailing Whitespace**, **Normalize Whitespace**, **Convert Indentation to Spaces**, and **Convert Indentation to Tabs**.

### Navigate

The **Navigate** menu is one of Quill's strongest differentiators. It assumes you may need to move through large, dense, or extracted material without visual scanning.

Core location commands:

- **Go To Line...**
- **Go To Page...**
- **Back Location**
- **Forward Location**

Structural movement commands:

- **Next Heading**
- **Previous Heading**
- **Next Block**
- **Previous Block**
- **Outline Navigator...**
- **Heading Organizer...** (`Ctrl+Alt+Shift+H`) for heading-level edits, section reorder, and heading validation
- **Match Bracket**
- **Next Structure**
- **Previous Structure**
- **Next Region**
- **Previous Region**

Bookmark and position commands:

- **Set Bookmark...**
- **Go To Bookmark...**
- **List Bookmarks...**
- **Go to Percent...**
- **First Non-Blank**
- **Last Non-Blank**

If your work involves transcripts, legal text, long Markdown notes, HTML source, or extracted PDFs, spend time here. This is the menu that turns Quill from a text box into a navigable workspace. (Find Next, Find Previous, and Find All Matches now live in **Edit**, beside Find and Replace.)

### Search

The **Search** menu is the across-files and pattern hub. In-document Find and Replace live in **Edit**; this menu covers multi-file and regular-expression work.

- **Search in Files...** and **Replace Across Files...** search and replace across a folder of documents.
- **Count Regex Matches...** and **Extract Regex Matches...** report or pull out every match of a regular expression.
- **Lines in First Block Only** and **Lines Common to Both Blocks** filter lines by block membership (set operations between two marked blocks).

### Tools

The **Tools** menu is Quill's workshop. It contains high-value actions that are not best understood as raw editing.

#### Discovery and command access

- **Command Palette...**

The palette is one of the fastest ways to learn Quill. It supports query modes:

- normal search or `>` for general command search
- `:` to search command IDs
- `?` to favor bound commands
- `~` to emphasize recently used commands

The palette also learns from usage. Commands you use more often rise naturally.

#### Writing and language

- **Word Count...**
- **Spell Check...**
- **Next Misspelling**
- **Thesaurus...**
- **Dictionary Status...**
- **AI Hub...**
- **Writing Assistant...**
- **Prompt Studio...**
- **Agent Center...**
- **Rewrite Selection**
- **Summarize Selection**
- **Continue Writing**
- **Fix Grammar**
- **Run Python...**

The Writing Assistant shell ranks Quill commands from your prompt, offers preset prompts for rewrite/summarize/continue/grammar flows, and Run Python executes a sandboxed transform against the current document text and selection. Prompt Studio lets you build reusable custom prompts with template variables, and Agent Center generates guided task plans that you can review before sending to the Writing Assistant.

The quick writing actions work with or without a selection:

- **Rewrite Selection** and **Fix Grammar** act on your selection if you have one; otherwise they use the paragraph at the cursor.
- **Summarize Selection** acts on your selection if you have one; otherwise it summarizes the whole document.
- **Continue Writing** uses your selection as the lead-in if you have one; otherwise it continues from the full document.
- Quill announces the scope it chose, for example "Rewrite paragraph (42 words)", so you always know what the action will change.
- If there is nothing to act on, Quill says so (for example "Nothing to rewrite") instead of sending an empty request.
- If AI is turned off, these actions announce "AI is turned off. Enable 'Use Artificial Intelligence' in Tools > AI Assistant." and do nothing else.

Use **Tools -> AI Assistant -> AI Hub...** for a single control surface that links provider verification, model discovery, Prompt Studio, Agent Center, and Writing Assistant.

Trust and privacy baseline:

- On first run, Quill shows a trust and privacy consent acknowledgement.
- Quill does not persist AI chat session transcripts by default.
- Cloud requests happen only when you explicitly invoke an AI action.
- API keys are stored in Windows Credential Manager when available, with DPAPI-encrypted fallback storage.

AI connection flow:

1. Open **AI Hub** and choose provider (`Ollama (local)`, `OpenAI`, `Claude`, `OpenRouter`, `Google Gemini`, `Microsoft Azure OpenAI`, `Ollama Cloud`, or `Custom OpenAI-compatible`).
2. Confirm host URL and model.
3. Enter key only when your endpoint requires authentication.
4. Use **Verify Connection** to test endpoint and credentials.
5. Use **List Models** to fetch endpoint models, then use the search box to filter quickly.
6. Use **Recommend Model** to pick a model profile aligned to your hardware/task framing.
7. Save settings. Quill auto-runs verification and updates the AI status line in Tools > AI Assistant.

Most cloud providers are pre-configured with default host URLs so setup is key-first, not URL-first. For advanced OpenAI-compatible endpoints, use Custom and override host/model explicitly.

Quill stores optional keys in the Windows Credential Manager, with a DPAPI-encrypted file as a fallback, and announces the verification result in plain language for immediate screen-reader feedback.

Connection status messages tell you exactly what to do next:

- "Authentication failed. Check your API key." means the key was rejected (HTTP 401). Re-enter the key.
- "Access denied. Your API key is valid but lacks permission for this model or region." means the key works but is not allowed for that model, region, or billing tier (HTTP 403). Check the provider's model access, billing, or quota.
- "The AI provider is warming up. Try again in a moment." means the model is still loading. Quill retries briefly on its own before reporting this.
- "The local AI server is not running. Start Ollama and try again." means Quill could not reach your local endpoint.
- "Rate limited by the AI provider. Wait a moment and try again." means you sent requests too quickly.
- "Your saved API key could not be unlocked on this device. Open AI Connection and enter the key again." appears in the AI status line when a saved key cannot be decrypted, which can happen after moving a portable install to a different Windows account or machine. Open AI Connection and re-enter the key.

For policy details, see the repository's `PRIVACY.md` and `RESPONSIBLE_AI_USE.md`.

These help you stay inside the editor instead of breaking flow for small writing chores.

### Ask Quill Chat setup (on-device AI)

Ask Quill Chat (`Tools -> AI Assistant -> Ask Quill Chat...`) is a message-style assistant that can answer, draft text, propose edits, and run Quill commands with approval before changes are applied.

Runtime backends:

- Windows and Linux: `llama.cpp` (`llama-cpp-python`, GGUF model)
- macOS (Apple Silicon, macOS 26+): Apple Foundation Models

Setup:

1. Install dependencies: `pip install -r requirements.txt`
2. Put a `.gguf` model in `%APPDATA%\\Quill\\models\\` (Windows) or set `QUILL_LLAMA_MODEL` to a full path.
3. Open `Tools -> AI Assistant -> Ask Quill Chat...` and send a prompt.

Accessibility:

- The whole conversation renders as an accessible WebView document: each turn is a heading (speaker) you can jump between, new replies are announced automatically, and the message box lives inside the page. Press `Escape` to close the chat. Verified in NVDA, JAWS, and VoiceOver.
- You can also connect optional providers (Ollama local/cloud, or a custom endpoint) instead of the on-device model.

Behavior notes:

- The assistant answers in chat by default; greetings and questions are never turned into document edits.
- Proposed actions (insert, replace, run a command) use an explicit `Approve` or `Discard` step before anything changes your document.
- If model/runtime is unavailable, Quill reports this clearly and does not apply destructive changes.
- **Train Writing Style** (`Tools -> AI Assistant -> Train Writing Style...`) lets you teach the assistant your own writing style from samples or the current document.

### Writing Assistant and AI Hub setup

For release-safe beta validation, Word and CSV open in the normal plain-text editor surface. AI connection and chat flows remain available.

Provider setup:

1. Open `Tools -> AI Assistant -> AI Hub...` (or `Tools -> AI Assistant -> AI Model & Connection...`).
2. Choose provider: `Ollama (local)`, `OpenAI`, `Claude`, `OpenRouter`, `Google Gemini`, `Microsoft Azure OpenAI`, `Ollama Cloud`, or `Custom OpenAI-compatible`.
3. Enter host and model (cloud defaults are prefilled; Azure requires your resource hostname).
4. Enter API key only if required.
5. Use `Verify Connection`.
6. Use `List Models` to select from endpoint-reported models with search filtering.
7. Use `Recommend Model` for guided picks tuned for local hardware or cloud framing.
8. Save settings. Quill auto-verifies and updates AI status/detail lines.
9. Use `Prompt Studio` to save reusable templates and `Agent Center` to generate guided task prompts.

Ollama Cloud onboarding remains available here as well. Users with API keys can use the free personal-use tier, which has lower usage limits.

After save, Quill announces plain-language verification feedback (for example, ready, auth failure, timeout, or endpoint unreachable).

#### Reading & Dictation

- **Read Aloud** submenu for start or pause, stop, and voice selection
- **Stop Reading** stops current read-aloud immediately
- **Say Selected** reads the current selection aloud
- **Read All** reads from the cursor to the end of the document
- **Dictation** submenu for Windows dictation, plus an opt-in **Hey QUILL Commands** toggle that lets dictation phrases trigger Quill commands instead of inserting text.
- **OCR Image...** converts an image to text via optical character recognition.

#### Watch Folder

- **Watch Folder Monitoring (in Settings)...** toggles automatic opening of supported files dropped into a configured folder.
- **Watch Folder Profiles...** configures folder path, subfolders, startup behavior, and polling behavior.
- **Watch Folder Queue...** shows current runtime state and active configuration.

When BITS Whisperer is enabled (QUILL 2.0), Watch Folder also appears in the BITS Whisperer submenu alongside Dictation.

Speech model selection intentionally follows a two-mode flow:

- **Recommended mode**: Quill selects a whisper model using machine-aware guidance (RAM/GPU profile).
- **Manual mode**: You pick a specific whisper model yourself.

In this phase, model infrastructure and download workflows are enabled while deeper runtime wiring remains staged.

Provider setup follows the same phased safety model:

- Use **Provider Center** for guided local-first or cloud-first setup choices.
- Use **Provider Status** to understand readiness and next steps.
- Providers are staged for rollout planning first; live provider routing remains gated in this phase.

Status Page behavior:

- **Help -> Status Page (HTML Preview)** now updates live while open.
- It surfaces asynchronous speech generation and BITS Whisperer download/provider status so users can monitor progress without blocking dialogs.
- In **Preferences -> General**, you can enable **Auto-open Status Page when BITS Whisperer model downloads start** (default off).
- In **Preferences -> General**, set **Status page refresh announcements** to **Quiet**, **Normal**, or **Verbose** to control screen-reader announcement cadence.
- In **Preferences -> General**, use **Use Artificial Intelligence** to mirror the Tools > AI Assistant toggle from one place.
- In **Preferences -> General**, enable **BITS Whisperer safe mode lock** to block download/retry actions while keeping status and onboarding surfaces available.

Startup Wizard now includes a BITS Whisperer rollout setup step that applies safe defaults without enabling runtime routing changes.

Read Aloud is particularly useful for proofreading by ear. OCR Image handles image-to-text work with an explicit consent and progress flow.
Dictation uses Windows' own speech input. When Hey QUILL Commands is enabled, Quill stays silent and only listens while dictation is active, then runs the matching action after the wake phrase.
Watch Folder automation is best for "drop and open" workflows: copy supported files into one
folder and let Quill open them in the background.

BITS Whisperer phased rollout note:

- Quill is adopting BITS Whisperer speech capabilities in phases.
- Phase 1 focuses on machine-aware speech model management and safer setup guidance.
- Additional BITS Whisperer transcription runtime features, including expanded model execution paths,
  will be delivered incrementally in future phases.

#### GLOW

- **Audit Current Document**
- **Audit Selection**
- **Fix Current Document**
- **Fix Selection**

GLOW inside Quill is a guided layout and output workflow for deterministic text review. Today it focuses on plain text, Markdown, and HTML. It looks for issues such as:

- missing spaces after Markdown heading markers
- heading-level jumps
- generic link text
- missing HTML language metadata
- missing HTML image alt attributes
- tables without HTML header cells
- dense paragraphs and plain-language friction

The key design choice is how GLOW feels inside Quill. Audit results open as readable Quill tabs. Fixing the current document opens a named preview tab and immediately starts a compare session against the original. Selection fixes apply in place to the current selection, paragraph, or line. That keeps GLOW close to the writing experience instead of making it feel like a detached compliance tool.

#### Comparison

- **Compare with File...**
- **Compare Open Documents**
- **Next Difference** / **Previous Difference**
- **Announce Current Difference**
- **Difference List...**
- **Toggle Synchronized Navigation**
- **Compare Options...**
- **Create Difference Summary**
- **Copy Current Difference** / **Copy All Differences**

Quill's compare model is practical and local. It supports file-to-file review, multi-document review, summary generation, and synchronized movement through differences.

#### Power Tools

Power Tools is the expanded home for automation utilities, developer tools, and editor-behavior power toggles.

**Editor utilities:**

- **Toggle Read-Only Guard** — prevents accidental edits to a document you are reviewing.
- **Toggle Clipboard Collector** / **Collect Clipboard Now** — accumulates clipboard entries into a running log.
- **Toggle Key Describer** — announces key names instead of performing actions; useful for documenting keystrokes.
- **Toggle Indentation Announcements** / **Infer Indentation...** — announces indentation level changes as you navigate.

**Macros:**

- **Start Recording** / **Stop Recording** — capture a sequence of editing commands.
- **Play Last Macro** — replay the last recorded sequence.
- **Manage Macros...** — name, edit, and organize saved macros.

Macros are ideal for repetitive cleanup: record once, replay as many times as needed.

**Authoring utilities:**

- **Regex Helper...** — full accessible dialog with recipe presets, plain-language pattern explanations, editable sample text, match previews with offsets, and one-step copy-to-Find-Replace.
- **Pandoc Conversion Wizard...** — converts supported source files into Markdown, HTML, or plain text that opens directly as a Quill tab.
- **External Tools and Format Support...** — explains what each supported helper unlocks, whether Quill can already see it, and the best first-touch setup path.
- **YAML Structure Editor...** — inspects and edits YAML front matter and structure files.

**Document Intake:**

- **Document Intake Report...** — answers how good an extraction was and whether the source likely contained structure that did not survive.
- **Review Extraction Quality...** — walks through extraction quality signals interactively.
- **Report Bad Extraction...** — escalates a source for manual cleanup or re-extraction.

These commands matter when Quill is acting as a trusted reader for imported formats. They help answer questions like: Is this document safe to quote from directly? Do I need to escalate for manual cleanup?

**Shell Integration:**

- **Install Shell Integration...** — registers Quill as a shell context-menu handler and protocol handler.
- **Remove Shell Integration** — unregisters shell extensions.

#### Accessibility

- **Accessibility Audit...**
- **Keyboard Trap & Tab-Order Snapshot...**
- **Validate Contrast...**
- **Link Inventory & Alt-Text Catalog...**
- **Speak Cursor Address**, **Speak Document Status**, and **Speak Selection Length** announce the caret position, document state, and selection size to your screen reader.

These tools help review the editor experience itself, the current document's link surface, and low-vision presentation issues.

#### Customize & Support

- **Preferences...**
- **Customize Menus...**
- **Profiles and Features...**
- **Status Bar Layout...**
- **Export and Back Up...** / **Import or Restore...**
- **Keymap Editor...** / **Export Keymap...** / **Import Keymap...** / **Reset Keymap**
- **Show Notifications**
- **Report a Bug...**
- **Save Diagnostics...**
- **Open Logs Folder** / **Open Diagnostics Folder**
- **Check for Updates**

Customize & Support merges the former separate Support and Customize submenus. All configuration and support paths live in one place, which is where both users and support staff expect to find them.

### Window

The **Window** menu is small but useful.

- **Next Document**
- **Previous Document**
- **Send to System Tray**

When you are juggling multiple notes, extracted files, and audit previews, these commands keep the workspace feeling controlled.

### Help

The **Help** menu is where Quill becomes a guide.

- **Open User Guide** opens this guide as an in-app document.
- **Open Welcome Guide** opens a lighter, profile-aware getting-started document.
- **Open Keyboard Reference** generates the current live shortcut reference from the active command registry.
- **Save Diagnostics...** writes a local diagnostics bundle you can review before sharing.
- **Report a Bug...** opens an in-app review screen, copies the environment summary to the clipboard, and then opens the Community Access support-hub issue form.
- **What Can I Do Here?** gives context-aware assistance.
- **Why Don't I See a Feature?** explains profile-driven feature visibility.
- **Feature Profiles** commands let you switch profile, run health checks, undo the last profile change, reset to Essential, and run onboarding.
- **Startup Wizard...** can be rerun at any time and now includes watch-folder setup.
- **Check for Updates...** verifies the signed update manifest, opens the installer download page, and can close Quill so setup can run immediately.
- **About Quill** shows version, publisher details, and linked third-party dependency attribution with license and version metadata.
- **Open Third-Party Notices** opens a full notices document with dependency tables and bundled license texts.

If you only remember one thing about Help, remember this: it is a working surface, not a dead-end menu. The welcome guide teaches the basics, the keyboard reference reflects your live bindings, the user guide gives the full map, diagnostics package the current state, and the bug-report action turns that state into a support-ready starting point.

Menu stability note: Quill now defers internal menu-state updates while native menus are open, then applies them after menu close. This prevents rapid-arrow navigation churn and keeps Help menu navigation stable.

### How to report a problem from inside Quill

Use this path when Quill is behaving unexpectedly or when you want to send the team a feature request.

1. Open **Help -> Report a Bug...**.
2. Read the in-app report summary Quill prepares for you.
3. Choose whether to include diagnostics, and whether to include plain file paths.
4. If diagnostics are included, save the diagnostics bundle to a location you can find again easily.
5. Choose **Open Support Form**.
6. When the Community Access support page opens, describe the problem, what you expected, and what actually happened.
7. Attach the diagnostics zip if it is relevant to the issue.

This unified flow keeps support reporting in one place. If you only need diagnostics, **Help -> Save Diagnostics...** remains available as a standalone export command.

## Writing and Editing

Quill's editing model is fast once you stop thinking of it as only a textbox.

### Everyday editing

Use the familiar commands first:

- `Ctrl+Z` to undo
- `Ctrl+Y` to redo
- `Ctrl+X`, `Ctrl+C`, `Ctrl+V` to move text
- `Ctrl+A` to select everything

Quill adds two especially useful ideas on top of that.

### Copy Tray

Copy Tray is **twelve** independently addressable clipboard slots that survive application restarts. Each slot holds text you copy there explicitly. Unlike the system clipboard — shared across every application and reset on every copy — Copy Tray slots belong exclusively to QUILL and hold their contents until you replace or clear them.

**Pasting from a slot is a single chord: hold `Ctrl+Shift` and press a number key.**

| Key | What happens |
| --- | --- |
| `Ctrl+Shift+1` through `Ctrl+Shift+9` | Paste from slots 1–9 |
| `Ctrl+Shift+0` | Paste from slot 10 |
| `Ctrl+Shift+-` | Paste from slot 11 |
| `Ctrl+Shift+=` | Paste from slot 12 |

**Copying to a slot uses the QUILL key prefix followed by the same key with Shift:**

| Key | What happens |
| --- | --- |
| `Ctrl+Shift+Grave, Shift+1` through `Shift+9` | Copy selection to slots 1–9 |
| `Ctrl+Shift+Grave, Shift+0` | Copy selection to slot 10 |
| `Ctrl+Shift+Grave, Shift+-` | Copy selection to slot 11 |
| `Ctrl+Shift+Grave, Shift+=` | Copy selection to slot 12 |

**Multi-press paste.** Press the paste chord multiple times quickly:

- **Single press** — paste the slot's content at the cursor (standard behaviour).
- **Double press** — peek: QUILL announces the slot's content without pasting it. Useful to check what a slot holds before committing to a paste.
- **Triple press** — open the Copy Tray dialog directly, focused on that slot.

**Copy to Next Empty Slot.** `Edit > Copy Tray > Copy to Next Empty Slot` copies the selection to the first unoccupied (and unpinned) slot in order 1–12 and announces which one: "Copied to slot 4 (first empty)." If all twelve slots are occupied, QUILL tells you rather than silently overwriting anything.

**Search Tray Slots.** `Edit > Copy Tray > Search Tray Slots...` opens a small search dialog. Type any word or phrase; QUILL searches all slot text and labels and announces matching slots. Press the corresponding digit key to paste that slot directly, or Escape to cancel.

**Pinned slots.** From the Copy Tray dialog, any slot can be marked Pinned. Pinned slots:

- Are never overwritten by "Copy to Next Empty Slot" routing.
- Are announced with a "pinned" prefix: "Slot 1 (pinned — signature)".
- Persist the pin flag in `copy_tray.json` across restarts.

To pin or unpin a slot, open the Copy Tray dialog (`Ctrl+Shift+Grave, X`), select the slot, and use the Pin/Unpin button.

**Paste submenu slot labels.** The `Edit > Copy Tray > Paste from Tray` submenu shows the label and a text preview for every occupied slot: "1  signature — Hi, I wanted to follow..." Screen readers hear both the label and the preview when navigating the submenu.

**Open the tray dialog:** `Ctrl+Shift+Grave, X` (or `Edit > Copy Tray > Open Copy Tray...`).

The dialog lists all twelve slots. Each row shows the slot number, an optional label, and a preview of the stored text. Navigate with arrow keys. Buttons:

- **Paste** — insert the selected slot's text at the cursor. Also activated by double-clicking or pressing Enter on a row.
- **Paste from Clipboard** — store the system clipboard into the selected slot.
- **Pin / Unpin** — toggle the pin state for the selected slot.
- **Save Changes** — save edits made directly in the content area.
- **Clear Slot** — empty the selected slot.
- **Close** — close without pasting.

**Status bar.** The `Slots: X/12` cell in the status bar shows how many of the twelve slots are occupied. Click the cell to open the Copy Tray dialog. Add the cell via `App > Preferences > Status Bar` if it is not visible.

**Tray icon access.** The system tray icon menu also includes a Copy Tray submenu listing all occupied slots. Click any slot entry to paste its content into the active editor. This makes QUILL's clipboard available from the tray without bringing the window to the front.

**Tips.**

- Keep a signature, disclaimer, or standard heading in slot 1 and pin it. One chord pastes it anywhere and "Copy to Next Empty Slot" will never overwrite it.
- Use labelled slots for a research session: slot 1 "intro quote", slot 2 "methodology note", slot 3 "source URL". Copy one fragment per slot as you read, then paste in order when drafting.
- Double-press any paste chord to hear what is in that slot without pasting — useful when navigating your tray by memory.
- Slots survive restarts. Build a small library of recurring fragments you reach for daily.
- All bindings are reassignable in the Keymap Editor (`App > Preferences > Keyboard`).

### Abbreviation Expansion

Abbreviation Expansion is a TextExpander-style feature. You type a short trigger word followed by any delimiter character (space, period, comma, and so on) and QUILL silently replaces the trigger with the full text.

**Example:** type `btw ` (note the trailing space) and QUILL replaces it with `by the way `.

QUILL ships with fifteen built-in abbreviations covering common shorthand. You can add, edit, and disable any abbreviation, including the built-in ones.

**Built-in abbreviations.**

| Abbreviation | Expansion |
| --- | --- |
| `afaik` | as far as I know |
| `afaict` | as far as I can tell |
| `asap` | as soon as possible |
| `atm` | at the moment |
| `btw` | by the way |
| `fwiw` | for what it's worth |
| `imo` | in my opinion |
| `imho` | in my humble opinion |
| `irl` | in real life |
| `omw` | on my way |
| `tbh` | to be honest |
| `tbc` | to be confirmed |
| `tbd` | to be determined |
| `ttyl` | talk to you later |
| `wrt` | with regard to |

**Enabling and disabling.** Abbreviation expansion is on by default. To toggle it:

- Press `Ctrl+Shift+Grave, E` — or use `Insert > Toggle Abbreviation Expansion`.
- Click the **ABR: On / ABR: Off** cell in the status bar (if visible; add it via status bar settings).
- Change **Abbreviation expansion** in `App > Preferences > Editing`.

**Managing abbreviations.** Open `Insert > Manage Abbreviations...` (or press `Ctrl+Shift+Grave, Shift+A`) to add, edit, and organise your abbreviations. Each abbreviation has:

- **Abbreviation** — the short trigger word, e.g. `btw`.
- **Expansion** — the full text to substitute, e.g. `by the way`.
- **Description** — optional note for your own reference.
- **Case sensitive** — when checked, only the exact-case trigger matches; otherwise any capitalisation of the trigger fires.
- **Enabled** — toggle individual abbreviations without deleting them.

The manager dialog includes a **Search** field at the top. Type any part of a trigger word or expansion text to filter the list in real time. Disabled abbreviations appear with a "(disabled)" suffix.

The manager also has **Import** and **Export** buttons for JSON round-trips. Export saves your full library to a file. Import merges a file into your library; abbreviations with duplicate IDs are skipped. QUILL announces how many were added on import.

**Manual trigger.** Press `Ctrl+Shift+Grave, A` (or `Insert > Expand Abbreviation`) to expand the word immediately before the cursor without typing a delimiter character. Useful when you want expansion mid-word or at end-of-document.

**Variables in expansions.** Expansions support these placeholders:

| Placeholder | Inserts |
| --- | --- |
| `${cursor}` | Places the cursor here after expansion |
| `${date}` | Current date (e.g. June 11, 2026) |
| `${time}` | Current time (e.g. 02:30 PM) |
| `${clipboard}` | Current system clipboard text |

**Multi-press window.** The double/triple press detection window is configurable in `App > Preferences > Editing` as **Multi-press window (ms)** (default 400 ms; range 100–1000 ms). A larger window helps if you press keys slowly; a smaller window prevents accidental double-fires for fast typists.

**Sound feedback.** Optional: enable **Play sound on abbreviation expansion** in `App > Preferences > Editing` and optionally point **Abbreviation expansion sound file** to a `.wav` file. Leave the path blank for the default system beep.

**Tips.**

- Use `${cursor}` to drop the cursor inside a template. For example, the abbreviation `sig` expanding to `Best regards,${cursor}Jeff` positions the cursor right after the comma.
- Use case-sensitive abbreviations sparingly — most triggers are lowercase and case sensitivity is rarely needed.
- Abbreviations fire before snippet expansion. If a word matches both, the abbreviation wins.
- Export your library regularly as a backup and to share abbreviations between machines.

### Copy With Source

`Ctrl+Shift+C` copies the current selection, then appends a source reference that captures document context. If nothing is selected, Quill uses the current line. This is excellent for notes, review workflows, and evidence gathering.

### Selection bindings

**F8-based anchor selection (EdSharp model)**

Quill uses an anchor-based selection model compatible with EdSharp:

| Key | Command | Purpose |
| --- | --- | --- |
| F8 | Start selection | Sets an invisible anchor at the cursor. |
| Shift+F8 | Complete selection | Selects from anchor to cursor and announces the span. |
| Ctrl+Shift+F8 | Reselect | Restores the most recent committed selection. |
| Alt+Shift+F8 | Go to start of selection | Moves the cursor to the selection start without changing it. |
| Ctrl+F8 | Copy all | Copies the full document. |
| Ctrl+Shift+A | Unselect all | Collapses the selection to the cursor. |
| Alt+F8 | Read all | Reads the document from the beginning. |

**Structural selection**

| Key | Command | Purpose |
| --- | --- | --- |
| Ctrl+Alt+P | Select paragraph | Selects the paragraph at the cursor; announces scope and word count. |
| Ctrl+Shift+B | Select block | Selects the indented block at the cursor. |
| Alt+Shift+Up | Expand selection | Grows the selection to the next structural unit (line to paragraph to block to document). |
| Alt+Shift+Down | Shrink selection | Reverses the last expand step. |

**Extend Selection Mode**

Extend Selection Mode makes movement commands extend the selection rather than move the cursor. Toggle it from the Selection menu (no default key; assign one in Preferences > Keyboard). When active, an **EXT** badge appears in the status bar.

**Mark ring**

The mark ring is a rolling stack of temporary jump points for in-session back-and-forth navigation:

| Key | Command | Purpose |
| --- | --- | --- |
| Ctrl+Shift+M | Set mark | Places a temporary mark at the cursor. |
| Ctrl+M | Pop mark | Jumps to the most recent mark and removes it from the ring. |
| Ctrl+Shift+X | Exchange point and mark | Swaps the cursor and the top mark position. |
| Alt+M | List marks | Shows all marks with line and column positions. |

**Named marks and review buffer**

Named marks are persistent within a session. Reach them via **Selection > Named Marks**:

- **Set Named Mark**: names and stores the current cursor position; announces line and column.
- **Jump to Named Mark**: choose from a list showing each mark's name and position; jumps on selection.
- **Open Review Buffer**: opens the active selection in a read-only dialog for non-destructive screen-reader paging. Requires a selection.

None of these have default key bindings. Assign them in Preferences > Keyboard, or use the Selection menu.

### Links

`Ctrl+K` inserts a format-aware link. `Ctrl+Enter` follows the link under the caret. In Markdown and HTML, this makes citation and cross-referencing much less tedious.

## Search, Replace, and Deep Navigation

Quill's search tools are both straightforward and layered.

### Standard search

- `Ctrl+F` opens search.
- `F3` finds next.
- `Shift+F3` finds previous.
- `Alt+F3` opens a find-all matches summary.
- `Ctrl+Shift+H` opens Replace.

### Search modes

Quill supports plain text, whole-word, wildcard, and regular-expression search. The Regex Helper explains the syntax when you need it. Search history is also preserved, so recurring search jobs get easier over time.

### Navigation that understands documents

Quill is excellent for large documents because it supports:

- line and page jumps
- block and heading movement
- bracket matching
- structural next and previous
- back and forward location history
- outline navigation
- bookmarks

When you combine this with marks and compare sessions, long-form review starts to feel much less fragile.

## QUILL Quick Nav Mode

QUILL Quick Nav mode is a browse-style, cursor-only navigation layer for long documents.

Enter the mode with `Ctrl+Shift+Grave`.

While the mode is active:

- `H` moves to the next heading.
- `Shift+H` moves to the previous heading.
- `1` through `6` move to the next heading at that specific level.
- `Shift+1` through `Shift+6` move to the previous heading at that specific level.
- `A` and `Shift+A` move by link anchor.
- `L` and `Shift+L` move by list container.
- `I` and `Shift+I` move by list item.
- `T` and `Shift+T` move by table.
- `Q` and `Shift+Q` move by block quote.
- `B` and `Shift+B` move by bookmark.
- `'` and `Shift+'` move by code block.
- `C` opens table of contents (Outline Navigator).
- `P` and `Shift+P` move by paragraph.
- `S` and `Shift+S` move by sentence.
- `Tab` and `Shift+Tab` move by block.
- `.` (period) repeats the last browse action.
- `]` jumps to the next line after the current list or table.
- `[` jumps to the line above the current list or table.
- `Esc` exits QUILL Quick Nav mode.

Behavior rules:

- This mode does not edit text.
- It only changes cursor location.
- If a target does not exist for the active surface, Quill announces that clearly.
- Find and replace commands return you to normal command flow automatically.
- In `Preferences -> General`, **Preload QUILL browse cache in background** is on by default. If you turn it off, Quill builds the cache the first time you use Quick Nav.

How Quill tracks headings, lists, list items, paragraphs, and sentences:

- Quill creates a navigation index for the active document and reuses it until content or surface type changes.
- The index key is document text plus markup type, so unchanged documents do not pay repeated parse cost.
- Headings are parsed from Markdown and HTML heading structure.
- List-item anchors come from Markdown list markers and HTML `<li>` tags.
- Paragraph anchors come from blank-line boundaries in text/Markdown and block-level tags in HTML.
- Sentence anchors come from sentence-ending punctuation patterns.
- Table anchors come from Markdown table starts and HTML `<table>` tags.
- Block-quote anchors come from Markdown `>` quote starts and HTML `<blockquote>` tags.
- Code-block anchors come from Markdown fenced code boundaries and HTML `<pre>` or `<code>` tags.
- Bookmark anchors come from your in-memory bookmark positions.
- The index is invalidated after edits, full document replacement operations, and tab/document switches.

Performance note:

- Quick Nav avoids reparsing on every key press by caching artifact anchors.
- This keeps movement responsive on long Markdown and HTML files.

### QUILL key prefix actions

Pressing the QUILL key (`Ctrl+Shift+Grave`) once arms a short prefix. Follow it with:

- `N` to enter browse/Quick Nav mode (press the QUILL key again to lock it until `Esc`).
- `G` to open Go to Anything (Quick Nav search).
- `M` to **paste HTML clipboard content as Markdown** at the cursor. Quill reads the
  clipboard's rich HTML (the `HTML Format` flavour copied from web pages and word
  processors), converts headings, lists, links, bold/italic, code, and block quotes to
  Markdown, and inserts the result. If no rich HTML is present, the plain-text clipboard
  is treated as HTML. The active read-only guard is respected, so a read-only document is
  never modified.
- `A` for selection actions when text is selected.
- `?` to show the QUILL key cheat sheet, or `Esc` to cancel the prefix.

## Formatting and Markup Work

Quill understands that many users work in plain text while still caring deeply about exported structure.

### Markdown and HTML awareness

Quill detects whether the current surface looks like Markdown, HTML, or plain text. It uses that to guide insertion helpers and enable the commands that make sense in context.

### Headings and lists

The heading tools do more than insert decoration. They help you maintain usable structure. The list tools speed up common authoring patterns without forcing you into a separate composer.

Markdown list editing now follows editor-standard behavior: `Enter` continues the current bullet/numbered/task item, and `Enter` on an empty list marker exits the list. When the caret is on a list item, `Tab` nests it and `Shift+Tab` promotes it. For larger reorganizations, use **Format -> List -> List Manager...** (`Ctrl+Alt+L`) to move, promote/demote, add, edit, and delete list items from a tree view.

For heading presentation control, open **Insert -> Heading -> Style Headings...**. You can style either all heading levels or the current heading level, then set font family, point size, and alignment. In Markdown documents, styled headings are written as HTML heading tags so the formatting is preserved.

For structure editing, open **Navigate -> Heading Organizer...** (`Ctrl+Alt+Shift+H`). The organizer lists each heading as level + title, supports keyboard promotion/demotion (`Tab` and `Shift+Tab`), lets you move sections up/down, rename headings, and validates heading order (start level, skipped levels, empty headings) before apply.

### Tables, code blocks, and tags

Quill includes guided insertion for tables, code blocks, HTML tags, and Markdown snippets. This is especially useful for users who want structure but do not want to hand-type every opening and closing marker correctly every time.

### Cleanup and normalization

The cleanup commands under **Tools → Convert** are ideal for pasted material, transcripts, exports, and migration work. Use them when you need to turn messy text into something more stable and readable.

## Tools for Reading, Review, and Inspection

Quill earns trust by making difficult files readable and inspectable.

### Read Aloud

Read Aloud uses local voices with a deterministic support policy. DECtalk and eSpeak NG are bundled for immediate local playback. Piper and Kokoro are available as explicit downloads from Speech Center so base installs stay smaller. You can start, pause, stop, preview, and choose a voice. Speech onboarding announces current availability and recommended next actions before any download starts.

### EPUB Navigator

When you open an EPUB, the navigator gives you chapter-aware movement rather than forcing you to scroll blindly through one long extraction.

### OCR Image

OCR is explicit and local. You choose the image, confirm the action, and receive progress updates. This keeps OCR useful without making it invisible or surprising.

### Document intake and extraction quality

These commands are where Quill feels especially mature for accessibility-minded reading work. Rather than assuming every import is trustworthy, Quill gives you tools to ask whether the extraction is good enough, what may have been lost, and whether you should quote from the result directly.

## GLOW Workflows Inside Quill

Glow in Quill is about guided confidence. It is not trying to turn the editor into a giant compliance dashboard. It is trying to make accessibility-aware review and safe deterministic fixes feel ordinary.

### Audit flows

Use document audit when you want the whole file reviewed. Use selection audit when you only care about the paragraph, block, or snippet in front of you.

Audit results open as normal Quill tabs. You can read them, search them, compare them, or keep them open alongside the source.

### Fix flows

Use selection fix for quick cleanup in place. Use document fix when you want Quill to generate a preview and immediately compare original versus fixed output.

This is where the native integration matters most. GLOW does not pull you away from your working context. It creates another working context beside it.

### What GLOW is best at today

The first native slice is strongest with:

- plain text review
- Markdown cleanup
- HTML accessibility-aware cleanup
- link-text review
- heading spacing and heading-level sanity
- lightweight readability guidance

The 1.0 roadmap expands this into findings navigation, export-readiness workflows, and richer extraction-aware review for PDF and EPUB.

## Accessibility and Low-Vision Features

Quill is designed so accessibility is visible, not hidden.

### Region model

Use `F6` and `Shift+F6` to move between editor and other major regions. Quill announces those region transitions consistently.

### Keyboard trap and accessibility audit

The keyboard trap snapshot and accessibility audit commands are there to help verify the interface itself. This is useful both for users and for testers helping improve the product.

### Contrast and theme behavior

You can validate contrast, switch dark mode, and align with system behavior. This matters for users who need a predictable low-vision experience rather than a single visual theme.

### Status bar as an accessible control surface

Quill's status bar is navigable and interactive. This is a subtle but important design decision. It keeps useful information close while still making it reachable from the keyboard.

## Quill on macOS

Quill runs on **macOS** as well as Windows, from one codebase, with feature parity as the goal.

- **VoiceOver-first.** On macOS, Quill routes its announcements to **VoiceOver** and never speaks over it. Headings, regions, and result messages behave the way they do on Windows with NVDA/JAWS.
- **On-device AI.** Ask Quill uses **Apple Foundation Models** (Apple Intelligence) on a supported Mac — no model download and no cloud. The on-device GGUF/llama.cpp picker is hidden on macOS because Apple's model is used instead; you can still connect Ollama or a cloud endpoint if you prefer.
- **Standard Mac behaviors.** Preferences and About use the standard macOS menu locations (`Quill -> Settings`, `Quill -> About Quill`).
- **Signed and notarized.** Release Mac builds are code-signed with a Developer ID certificate and notarized by Apple, so Gatekeeper opens them without warnings. The app ships as a `.app` (and disk image).
- **The accessible WebView** that powers the chat, the Markdown/HTML preview, the About box, and the update dialogs reads correctly under VoiceOver, just as it does under NVDA and JAWS on Windows.

## Profiles, Keyboard Packs, and Customization

Quill is customizable, but it tries to keep customization coherent.

### Feature profiles

Profiles shape which feature clusters are on, quiet, or off. This helps Quill stay calm for new users without stripping power from advanced users.

Use **Profiles and Features...** to:

- switch profiles
- quick-switch profiles from anywhere with `Alt+Shift+P`
- compare profiles
- undo the last profile change
- reset to Essential
- import and export profile data
- create custom profiles
- update a custom profile from your current feature/settings/keymap state
- delete custom profiles

Custom profiles support an explicit inheritance choice:

- **Inherit parent profile** keeps the selected built-in profile as the starting point.
- **Bare-bones start** opts out of inherited features and starts with only locked core safety features enabled.

### Keyboard packs

Quill now supports golden keyboard packs so the editor can feel familiar from day one. Available packs include:

- Quill Default
- Quill Writer
- Quill Navigation
- Quill Review
- Windows Notepad
- Notepad++
- VS Code
- Microsoft Word

Choose a pack in **Profiles and Features...**. If you later hand-edit shortcuts or import a custom keymap, Quill automatically switches the pack label to **Custom**.

### Keymap editor

Use the keymap editor when you want to rebind a single command. Quill detects conflicts and warns you before reassigning a binding already in use.

### Keyboard manager for QUILL Quick Nav

QUILL Quick Nav actions appear in Keymap Editor as dedicated entries:

- `QUILL Quick Nav: Link`
- `QUILL Quick Nav: List`
- `QUILL Quick Nav: List Item`
- `QUILL Quick Nav: Table`
- `QUILL Quick Nav: Block Quote`
- `QUILL Quick Nav: Bookmark`
- `QUILL Quick Nav: Code Block`
- `QUILL Quick Nav: Table of Contents`
- `QUILL Quick Nav: Paragraph`
- `QUILL Quick Nav: Sentence`
- `QUILL Quick Nav: Heading`
- `QUILL Quick Nav: Block`

Exact rebinding examples:

1. Open `Tools -> Customize & Support -> Keymap Editor...`.
2. Choose `QUILL Quick Nav: Link`.
3. Enter `K` if you want link jumps on `K` instead of `A`.
4. Choose `QUILL Quick Nav: Code Block`.
5. Enter `\`` (grave) if you prefer grave instead of apostrophe.

Notes:

- Conflicts are blocked by the keymap editor before saving.
- Quick Nav keys are interpreted only while QUILL Quick Nav mode is active.

### Status bar settings

If the current status bar is too busy or not informative enough, change it. You can reorder items and choose which ones stay visible.

### Settings you can change today

Quill's current settings and customization surface covers the things you are most likely to want to tune every day.

- theme behavior, including dark mode
- soft wrap
- recent files limit
- system tray mode
- persistent undo
- spell check as you type
- line-number visibility
- whether Quill starts with no document open
- read-aloud voice selection
- active feature profile
- active keyboard pack
- custom keybindings through the keymap editor
- status-bar order and status-bar visibility

Some of these live in the View menu for quick toggling; the preference-style toggles now live in the **Settings** dialog (**Tools -> Customize & Support -> Preferences...**). Others live in **Profiles and Features...**, **Status Bar Layout...**, **Keymap Editor...**, and the related customization commands under **Tools -> Customize & Support**.

## Trust, Recovery, Sessions, and Safety

Quill is serious about recovery and user control.

### Notebooks

A **Notebook** is a named collection of documents that belong together — a novel's chapters, a research project's notes, a software project's specs. Notebooks live in a single `.quillnotebook` file and keep track of which files are entries, where you left each caret, any goals you have set, and saved snapshots of which entries were open.

**Creating a Notebook.** Use **File > Notebook > New Notebook** to create an empty notebook and give it a name. Use **File > Notebook > New from Folder** to import an entire folder at once — Quill walks the folder recursively and creates one entry per supported file. You can filter by extension (the default set covers Markdown, plain text, HTML, and source code).

**Opening and navigating entries.** Once a Notebook is open, **Navigate > Go to Entry in Notebook** opens the tree navigator, which groups entries by subdirectory. Select an entry and press Enter (or click "Open Entry") to open that file. For headings, **Navigate > Go to Heading in Notebook** scans every entry file and presents a two-level tree.

**Entries panel.** Toggle **View > Show Entries Panel** to slide a docked panel into the left side of the window. The panel shows the notebook name, today's goal progress, a live filter field, and the full entries list. Type in the filter field to narrow by title.

**Goals.** Each Notebook can carry a daily word-count goal stored in its `.quillnotebook` file. When the goal is enabled, the **Notebook Goal** status-bar cell shows progress (for example, "1,234 / 500 words"). Reaching the target changes the label to "Goal reached."

**Snapshots.** A Snapshot is a named point-in-time record of which entries were open. Use **File > Notebook > Save Snapshot** to save one, and **File > Notebook > Manage Snapshots** to rename or delete saved snapshots. Snapshots are different from autosave recovery — they are explicit saves you make yourself, like commit checkpoints for your writing session.

**Snapshots vs Sessions.** The **File > Snapshots** menu (formerly "Workspace Snapshots") saves and restores the set of open documents in the editor — a lightweight workspace for any files, not tied to a Notebook. Notebook Snapshots store the open-entry state within a single Notebook.

### Sessions

Sessions in Quill are best understood as **workspace snapshots**. A session captures your currently open documents and active tab, then lets you reopen that exact working set later.

If you are familiar with VS Code workspaces, think of Quill sessions as a simpler, document-focused version of that idea:

- save your current workspace state
- reopen it from Recent Snapshots
- quickly switch among open documents in the current workspace group

This is useful when one writing task spans notes, references, drafts, and generated reports.

### Marks vs bookmarks (and the ring)

Quill has two jump systems on purpose:

- **Bookmarks** are named jump points. They are explicit, easy to list, and best for durable places you want to revisit by name.
- **Marks** are temporary jump points in a **ring**. The ring is a rolling stack of recent mark locations for fast back-and-forth movement while editing.

Use bookmarks for long-lived anchors; use marks when you are actively traversing and reshaping text.

### Autosave and backups

Quill autosaves at a timed interval and keeps backup snapshots. It avoids unnecessary duplicate autosave writes and keeps state management efficient.

### Recovery

If Quill closes unexpectedly, it can offer a recovery snapshot on the next launch. That is not a dramatic feature. It is a humane one.

### Persistent undo

When enabled, persistent undo stores undo history for saved files across sessions. Quill now throttles those writes so the feature stays practical on large documents.

### Trusted locations

Trusted locations reduce repeated prompts when you regularly work from the same folders. This is especially useful in document-review and institutional workflows.

### Safe mode

Safe mode opens Quill with optional state turned off. If you are troubleshooting a bad session or strange startup behavior, safe mode is a good first step.

### Notifications and updates

Quill keeps an internal notification center for update and workflow events. Update checks verify a signed manifest before offering a download.

## Working with Different Document Types

Quill is strongest today with plain text, Markdown, HTML, RTF, EPUB, and extracted text workflows. It also has intake and extraction review features for imported material such as PDF/OCR sources and structured import support for Office-style formats.

### Plain text

Plain text stays plain. Quill does not force hidden formatting into it.

### Markdown

Markdown gets structure-aware commands, list helpers, heading helpers, links, code blocks, and GLOW review.

### HTML

HTML gets tag insertion, structure-aware editing help, link handling, and GLOW review focused on language metadata, image alt text, heading order, and table headers.

### RTF

RTF documents can use Quill's optional **Rich text lens**, a screen-reader-first rich editing surface. It is **off by default**: the standard plain-text editor stays Quill's writing path unless you opt in under Settings, Editing (the "Editor surface" choice). Turn it on and `.rtf` files open in the Rich text lens, which renders bold, italic, headings, bullets, and links natively. Your document text stays Quill Markdown underneath, so search, outline, metrics, autosave, and persistent undo keep working exactly as in plain-text mode. Press the editing-lens shortcut (`Ctrl+Shift+` ` then `K`) to switch losslessly between the rich view and the Markdown lens; no words are lost and the document is not marked changed by switching. When an RTF file contains unsafe embedded content (such as OLE objects) Quill strips it on open and tells you; remote fields are flagged for your consent rather than fetched silently.

### CSV and TSV

CSV and TSV files open through a choice flow: special CSV grid mode or normal text editor mode. You can remember your preferred default and still switch modes from inside the tab at any time. Grid mode is keyboard-friendly and designed for screen-reader users who need cell-level table editing without leaving Quill.

### Word (.docx and .doc)

Word documents open through a choice flow: structured Word view or normal text editor mode. You can remember your preferred default and still switch modes inside the tab.

Structured Word view is optimized for accessibility: it prioritizes readable structure and linearized table narration (headers and rows) for screen readers. Normal text mode keeps full Quill editing behavior for direct edits.

### EPUB

EPUB gets navigator support and chapter-oriented reading.

### PowerPoint (.pptx and .ppt)

PowerPoint imports are structure-aware: slide titles become headings, slide bullets become nested list items, tables are rendered into tab-friendly text tables, and speaker notes are included when present.

### Excel-style spreadsheets (.xlsx and .xls)

Spreadsheet intake is text-first and structure-aware. Quill extracts sheets into readable table-oriented text so you can inspect and review content quickly. If optional converters are installed, extraction quality improves for legacy and mixed-format files.

### PDF and OCR-derived text

PDF and OCR work are where Quill's extraction review commands matter most. Treat those commands as quality checks, not optional extras.

### Remote files (FTP, SFTP, HTTPS, WebDAV, S3)

Quill can open, save, and copy to remote hosts the same way it works with local files. Remote I/O is explicit, audible, and reversible:

- **Open from Remote...** lists every site you have saved, lets you browse a remote directory, and downloads a file you choose. The download is announced with the host and expected size, lands in a temp file, and opens in a normal tab titled with a `(from site:path)` suffix. The document is **read-only** until you save it back through **Save Copy to Remote...** or copy it to local storage.
- **Save to Remote** writes the active document to a remote path you choose, on a site you have configured, with a tilde-backup next to the original. **Save Copy to Remote...** lets you keep the local file and write a copy without changing the source.
- **Manage Remote Sites...** adds, edits, and deletes saved sites for the five supported protocols. Each site's password is stored in **Windows Credential Manager** when available, then in a DPAPI-protected JSON file, with a macOS Keychain facade for cross-platform parity.
- All remote traffic uses a **verified TLS context**. Cloud endpoints (S3, HTTPS, WebDAV over HTTPS) must be HTTPS; FTP is allowed because the user opted in for LAN or legacy hosts.
- All remote operations are wired to the **network egress audit** (`quill/tools/network_egress_audit.py`) with explicit rationales, and S3 and WebDAV XML responses are parsed through `quill.core.safe_xml.fromstring` so an attacker cannot reach an external-entity expansion through a crafted listing.

Default keys: **QUILL key, then `R`** opens from remote; **QUILL key, then `Shift+R`** saves to remote; **QUILL key, then `M`** opens the site manager. All are remappable from Preferences > Keyboard.

### GitHub Remote Files

QUILL can browse GitHub repositories, open files from them, and save changes back to GitHub — all without installing Git, the GitHub CLI, or GitHub Desktop.

**Getting started**

The first time you open a GitHub feature, QUILL asks you to confirm that it may connect to GitHub. This is a one-time prompt. After that, QUILL remembers your choice.

You do not need a GitHub account to browse public repositories. For private repositories, you need a Personal Access Token (PAT).

**Creating a Personal Access Token**

1. Go to github.com and sign in.
2. Open Settings > Developer settings > Personal access tokens > Tokens (classic).
3. Click Generate new token.
4. Give it a name such as "QUILL" and select the `repo` scope (or `public_repo` if you only need public repositories).
5. Copy the token. You will only see it once.

QUILL stores your token securely in **Windows Credential Manager**. It is never saved in a text file.

**Opening the repository browser**

Open **File > Open from Remote > GitHub Repository...**

The browser has these parts:

- **Account** — shows your GitHub username, or "Anonymous" if no token is stored.
- **Repository** — type an owner/repo name such as `microsoft/vscode` and press Enter or click Load.
- **Branch or tag** — choose which version of the repository to browse. Defaults to the repository's default branch.
- **Current path** — shows where you are in the folder tree.
- **File list** — lists folders and files. Folders appear first.
- **Status** — shows progress messages and item counts.

Navigation:
- Press Enter on a folder to open it.
- Press Enter on a file to open it (same as clicking Open File).
- Press Backspace to go up one level.
- Press F5 to refresh the current folder.
- Tab through the buttons: **Open File**, **Go Up**, **Refresh**, **Copy URL**, **Cancel**.

**Opening a file by URL**

If you have a GitHub file URL (for example from a colleague), use **File > Open from Remote > GitHub File URL...**

Paste a URL in the form `https://github.com/owner/repo/blob/branch/path/to/file` and press Enter. QUILL fetches the file directly.

**Saving back to GitHub**

After you have opened a file from GitHub and made edits, use **File > Open from Remote > Save to GitHub...**

QUILL will ask for a commit message. Type a short description of your changes and press Enter. QUILL commits your changes to the same repository, branch, and file path using the GitHub API.

Notes:
- You need a token with write permission (`repo` scope) to save back.
- If the file was changed on GitHub since you opened it, QUILL will tell you to refresh and try again.
- This command does not run automatically when you press Save. You must choose it deliberately.

**Managing your GitHub account**

Use **File > Open from Remote > Manage GitHub Accounts...** to:

- See your current GitHub identity.
- Add or replace a token.
- Sign out and clear your stored token.

**File size limit**

GitHub's file API is limited to 1 MB. Files larger than that must be downloaded manually from github.com.

**Enabling the feature**

GitHub remote access is controlled by the feature flag `core.github_remote`. If it is not visible, open **File > Open from Remote** and check whether the GitHub items appear. If PyGithub is not installed, QUILL shows a message explaining how to install it: `pip install "quill[github]"`.

## Help, Learning, and Daily Confidence

Quill includes several layers of help because confidence does not come from memorizing everything.

- **F1** — context-sensitive help for the focused control. Works anywhere in the application.
- **Ctrl+F1** — opens this User Guide.
- **Shift+F1** — opens the document-context "What Can I Do Here?" panel.
- **Open Welcome Guide** when you want a lighter orientation.
- **Open User Guide** when you want the full map.
- **Open Keyboard Reference** when you want exact current bindings.
- **What Can I Do Here?** when you need immediate, contextual guidance.
- **Why Don't I See a Feature?** when a command seems to have disappeared.

That last command matters more than it first appears. It turns feature visibility from a mystery into an explanation.

### Context-Sensitive Help (F1)

Press `F1` on any focusable control in QUILL and a small dialog opens that describes:

1. **The dialog you are in** (when you are inside a dialog box) — the dialog name and a plain-language summary of what it does, so you always know your context.
2. **The focused control** — what the control is, how it works, and what keyboard shortcuts apply to it.

The entire text is in one read-only field so your screen reader announces everything in a single pass when the dialog opens, without you having to navigate past heading elements.

From the help dialog you can:

- Press **Escape** or **Enter on Close** to dismiss and return to where you were.
- Press **Tab to Open User Guide** to jump to the full documentation section for this control.

**How the three Help keys work together:**

| Key | What it does |
|-----|--------------|
| `F1` | Help on the currently focused control (context-sensitive) |
| `Ctrl+F1` | Open the full User Guide |
| `Shift+F1` | Open "What Can I Do Here?" for the active document context |

**Tips:**

- In the main editor, F1 shows editor shortcuts and writing tips.
- In dialogs (Preferences, Find/Replace, Spell Check, etc.), F1 identifies both the dialog and the specific setting.
- In the Personalise QUILL wizard, F1 on each control explains what each setting does and what you can change later.
- After using a menu and returning to the editor, QUILL remembers which control had focus last, so F1 still refers to the right control.

### Personalising QUILL

The **Personalise QUILL** wizard runs automatically the first time QUILL starts. You can re-run it at any time from **Help → Personalise QUILL**.

The wizard walks you through eight short pages:

1. **Welcome** — an introduction to what the wizard covers.
2. **Keyboard and Sound** — choose a keyboard pack and whether QUILL plays audio cues. QUILL auto-detects your screen reader and sets accessible defaults.
3. **Feature Profile** — choose a starting profile: Essential (minimal), Standard (recommended for most users), Power User (all features on), or Accessibility Focus (screen-reader optimised). You can switch profiles later.
4. **Remote Access** — enable or hide FTP, SFTP, WebDAV, and S3 remote file commands. Disabling this removes the remote-site menu items entirely, keeping the File menu clean.
5. **AI Assistance** — turn the AI writing assistant on or off. You can add an API key later; QUILL will prompt you when you first use an AI feature.
6. **Reading and Accessibility** — configure read-aloud behaviour and screen-reader announcement style.
7. **Writing Tools** — enable or disable spell-check-as-you-type, abbreviation expansion, and the Copy Tray.
8. **Startup Behaviour** — choose what QUILL opens when it starts and whether to check for updates automatically.
9. **Summary** — review all your choices before they are applied. Use Back to revise any page. Nothing changes in QUILL until you press Finish.

**Important:** The wizard is transactional. Your choices are held in memory until you press Finish. If you close or cancel the wizard, no settings are changed.

**Profiles explained:**

| Profile | Best for |
|---------|----------|
| Essential | New users, light daily writing, low-distraction setup |
| Standard | Most users — balanced feature set with AI and tools available |
| Power User | All features on; suited to advanced writing, extraction, and GLOW workflows |
| Accessibility Focus | Screen-reader primary; maximises keyboard coverage and announcements |

You can switch profiles at any time from **Tools → Customize & Support → Profiles and Features...** or by pressing `Alt+Shift+P`.

## Translation and Community Localization

QUILL uses a standard GNU gettext pipeline (`POT → PO → MO`) for all user-visible strings, aligned with the model used by NV Access for NVDA. This means QUILL translation work feels familiar to anyone who has contributed to NVDA, JAWS scripts, or other accessibility-focused open-source software.

### How the Translation Pipeline Works

1. **Source strings are marked in code** with `_()` for regular strings, `ngettext()` for plural forms, and `lazy_gettext()` for strings that must be translated at display time rather than at import time.
2. **The POT file** (`quill/locale/quill.pot`) is the master template, generated automatically by `pybabel extract`. It contains every translatable string in the application.
3. **PO files** (`quill/locale/<lang>/LC_MESSAGES/quill.po`) contain the actual translations for each language. Translators work in PO files.
4. **MO files** are compiled from PO files by `pybabel compile` and are the binary files QUILL loads at runtime.
5. **QUILL selects the active language** at startup from your `language` setting (BCP 47 tag, e.g., `fr`, `es`, `pt-BR`). If blank, QUILL follows the operating-system language.

Speech strings — text that will be read aloud by a screen reader rather than displayed visually — are marked with a `# SPEECH:` comment in the source code. Translators should preserve the natural spoken rhythm of these strings, not just their semantic meaning.

### Contributing Translations

To contribute a translation:

1. **Fork the QUILL repository** and create a branch named `l10n/<lang>` (e.g., `l10n/fr`).
2. **Copy `quill.pot` to your language folder:** `quill/locale/fr/LC_MESSAGES/quill.po`
3. **Translate each `msgid` into a `msgstr`.** Leave `msgstr` empty for strings you have not yet translated; the English fallback will be used.
4. **Run the CI translation check** to verify placeholder integrity and completeness: `python -m quill.tools.check_translation`
5. **Open a pull request.** The Translation Coordinator reviews and merges approved translations.

**Tools that help:**

- [Poedit](https://poedit.net/) — free, accessible PO file editor with spell check.
- [Virtaal](https://virtaal.translatehouse.org/) — lightweight alternative.
- Crowdin (when QUILL's project is live) — browser-based collaborative translation with a review queue.

**Do not translate:**

- Placeholder tokens: `{name}`, `%(count)s`, `{path}` — leave these exactly as they are in the `msgid`.
- ARIA role names: `"dialog"`, `"button"`, `"listbox"` — these are passed to platform accessibility APIs unchanged.
- Internal command identifiers: `"file.open"`, `"glow.audit"` — these are not user-visible.
- File extensions and format names: `.docx`, `EPUB`, `PDF`.

### Translation Roles and Responsibilities

QUILL follows a four-tier model aligned with NV Access community practice:

| Role | Responsibilities |
|------|----------------|
| **Translator** | Translate strings from English into the target language. |
| **Proofreader** | Review translations for accuracy, tone, and natural language flow. |
| **Language Coordinator** | Own quality for one language; approve or request changes from translators and proofreaders. |
| **Translation Coordinator** | Oversee the whole translation project, manage Crowdin, coordinate string freeze, credit contributors. |

To become a translator or proofreader: open a GitHub issue with the label `translation` and state the language you want to work on.

### Speech String Guidelines

QUILL marks screen-reader-targeted strings with `# SPEECH:` in the source code. When translating these strings:

- **Prioritise spoken clarity over literal accuracy.** A string that reads well when spoken aloud is more important than a string that is grammatically perfect but awkward when heard.
- **Match the rhythm.** Short speech strings should stay short. QUILL's screen-reader users hear these strings dozens of times per session; brevity is a form of accessibility.
- **Preserve emphasis signals.** Where the English string uses word order or phrasing to signal importance (e.g., the key word comes first), try to mirror that in translation.
- **Test with a screen reader.** If possible, test your translated strings with NVDA or JAWS before submitting.
- **Ask if unsure.** Open a GitHub issue tagged `translation` and `speech` if you are uncertain how a speech string should be adapted.

String freeze happens before each release candidate. No new strings are added after freeze, and translators have a two-week window to complete their language before the release is built.

## Checking for Updates

Quill can check for and install updates automatically while you work.

### Manual update check

To check for updates now:

1. Press Alt+H to open the **Help** menu.
2. Press U for **Check for Updates**.
3. If a newer version is available, Quill will announce it and ask for permission to download.
4. If you accept, Quill downloads the update in the background and announces when it is ready.
5. The next time you close and reopen Quill, the update is applied automatically.

### Automatic update checks

You can enable Quill to check for updates on startup:

1. Press Alt+E to open the **Edit** menu.
2. Press Shift+S for **Settings**.
3. In the **Updates** section, enable **Check for updates on startup**.

When automatic checks are on, Quill will notify you quietly if a new version is available, and you can choose to download it when you are ready.

### Update size and speed

Quill uses incremental updates ("micro-updates"), which are much smaller than full reinstalls. Patches often download in seconds rather than minutes, and your settings, documents, and preferences are preserved.

### Staying on a release channel

By default, Quill checks the stable update channel and only offers released versions. To opt into beta versions and test new features early, enable **Beta channel** in **Settings → Updates**.

## Beta Feedback and Bug Reporting

Quill is ready for serious beta use, and Quill 0.1.5 Beta now ships a real in-app support starting point.

### What exists today

Today, Quill already has the foundations for careful support work:

- recovery state
- notifications
- extraction review
- bad-extraction package export for extraction-related issues
- a general-purpose **Save Diagnostics...** command that writes a local bundle
- a **Report a Bug...** command that lets you review the report in-app and then opens the Community Access support-hub form with environment context
- a diagnostics runbook and PRD-backed support model in the documentation set

### What still needs to improve

Today, Quill still does **not** yet ship a polished no-login secure upload path directly from the desktop app, and the support handoff still depends on a browser form after the in-app review step.

### Best beta-launch recommendation

Before the broadest public rollout, publish one secure feedback route that does not require GitHub login. The best release-quality path is still:

1. a BITS-controlled HTTPS feedback form
2. optional upload of a user-reviewed diagnostics bundle
3. a plain-language bug template with environment summary and reproduction steps
4. the current **Help -> Report a Bug...** handoff kept as the guided in-app bridge until the fuller route is live

Until that exists, use the current Help-menu path as the practical bridge. The important improvement in Quill 0.1.5 Beta is that Quill now helps users gather diagnostics locally, review what is being shared, and start a structured support report without forcing them to begin outside the tool.

## A Fast Shortcut Tour

If you want a compact set of shortcuts to remember first, start here:

- `Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`
- `Ctrl+Shift+P` for the Command Palette
- `Ctrl+F`, `F3`, `Shift+F3`, `Alt+F3`
- `Ctrl+G` and `Ctrl+Shift+G`
- `Ctrl+K` and `Ctrl+Enter`
- `Ctrl+Alt+L` for List Manager
- `F7`, `Alt+F7`, `Shift+F7`
- `Ctrl+Shift+W` for Word Count
- `Ctrl+Tab` and `Ctrl+Shift+Tab`
- `F6` and `Shift+F6`
- `Alt+Z` for soft wrap

Then open **Help → Open Keyboard Reference** and let Quill teach you the rest from your actual active layout.

## Closing Thought

The best way to understand Quill is to use it on something real: a note you care about, an extracted PDF that needs trust review, an EPUB chapter you want to navigate, a Markdown file you want to clean up, or an HTML document you want to make more usable.

Quill is trying to feel like a skilled guide sitting just beside the editor, not standing in front of it. If it succeeds, you will notice something simple: you spend less time wondering what the application can do, and more time deciding what you want to do next.

## Quillins: Sandboxed Extensions

Quill supports **Quillins** — small, sandboxed extensions that add new commands, snippets, and menu items to the editor without requiring a full app restart.

### Bundled Quillins
Quill ships with several trusted, first-party Quillins enabled by default. These provide common utilities that would otherwise clutter the core editor:

- **Text Tools**: Provides advanced text transformations and analysis, including:
  - **Line Numbering**: Prefix lines with sequential numbers.
  - **Hard Wrap**: Wrap text at a specific character width.
  - **Regex Tools**: Count or extract patterns across the document.
  - **Block Filtering**: Find lines that are common to two blocks or exist only in the first.
- **Insert Tools**: Provides smart placeholders for quick insertion, such as the current **Date** and **Date/Time**.

### The Quillins Manager

Open via **Tools > Quillins**. The Manager lets you:

- See every installed Quillin and its current status (enabled or disabled).
- Select a Quillin to review its manifest: name, version, author, description, and declared capabilities.
- Enable or disable a Quillin without removing it.
- Remove a Quillin entirely (confirmation required).
- **Install from Folder** — press this button to select a local folder containing a Quillin. QUILL reads its `manifest.json`, validates it, copies the folder into your per-user extensions directory, and enables it immediately. If a Quillin with the same id is already installed it is replaced. This is the supported path for installing third-party Quillins.

When you select a Quillin, the panel shows all declared capabilities (for example `fs.read` or `net`). Review these before enabling an extension from an unknown source.

### Authoring Quillins
For developers, Quillins are designed to be "screen-reader-first." They follow a strict capability model: a Quillin must declare the minimum set of permissions it needs, and any sensitive action (like writing to a file) is consent-gated at runtime.

---

## AI Assistant

QUILL includes a built-in AI assistant that works with OpenRouter, OpenAI, and Ollama. All three are optional; QUILL detects which keys you have configured and only shows providers that are available. API keys are stored in the Windows Credential Manager by default and never written to disk in plain text.

### Setting up an AI provider

Open **App > Preferences > AI** to configure your provider.

- **OpenRouter** — paste your API key into the OpenRouter API Key field. OpenRouter gives you access to many models (Claude, GPT-4o, Gemini, and more) with a single key.
- **OpenAI** — paste your OpenAI API key.
- **Ollama** — no key needed. Install Ollama on your machine (`ollama serve`) and QUILL detects it automatically at `http://localhost:11434`. Change the Ollama Base URL setting if you run Ollama on a different port or machine.

### Portable mode and key storage

By default QUILL stores AI provider keys in the **Windows Credential Manager**, which ties them to your Windows user account. If you run QUILL from a self-contained folder — for example on a network share or an external drive — you can switch to **portable mode** so all keys live in that same folder alongside your other QUILL data.

**Activating portable mode.** Set the environment variable `QUILL_PORTABLE=1` before starting QUILL. You can do this for the current session:

```powershell
$env:QUILL_PORTABLE = "1"
python -m quill
```

Or add it permanently to your user environment via System Properties > Environment Variables.

When portable mode is on, keys are stored in a file called `keys.enc` inside the QUILL data directory. The file is encrypted with Windows DPAPI, so it is protected by your Windows user-account key.

**Limitations.** The encrypted file is tied to the Windows account that created it. Moving it to a different machine or a different Windows account will fail to decrypt; you will need to re-enter your keys there. Portable mode gives you a self-contained folder on the same machine — it does not give you cross-machine portability.

**Environment-variable overrides (for CI and developers).** You can supply keys directly via environment variables regardless of which mode is active. These always win and are never stored to disk:

| Provider | Environment variable |
| --- | --- |
| OpenRouter | `QUILL_OPENROUTER_KEY` |
| OpenAI | `QUILL_OPENAI_KEY` |
| Ollama Cloud | `QUILL_OLLAMA_KEY` |
| AI Assistant | `QUILL_ASSISTANT_KEY` |

You can also set a **Default model for prompt runs** (`ai_prompt_default_model`). Leave it blank to share the same model across Ask AI and the Prompt Library, or set a different model here if you want a more capable model for prompt-library work.

### Ask AI (Alt+Q)

`Tools > AI Assistant > Ask AI...` opens a dialog where you type a question and read the answer without leaving QUILL.

- **Provider** and **Model** choices are pre-filled with the last values you used.
- If a provider and model are already configured, focus lands directly in the Prompt field so you can start typing immediately. If not yet configured, focus starts on the Provider choice to guide you through setup.
- Press **Ctrl+Enter** or the **Send** button to submit. QUILL announces "Sending..." and disables the button while the request is in flight.
- The response opens in a read-only dialog. Use cursor keys to read it, and **Copy to Clipboard** to copy the full text. Closing the response returns you to the Ask AI dialog so you can ask a follow-up.
- **Clear** resets the prompt field and refocuses it.

### Check Grammar with AI

`Edit > Grammar > Check Grammar with AI` sends the selected text (or the full document if nothing is selected) to your AI model with a grammar-review prompt. The response dialog lists corrections in the form "original phrase → corrected phrase — reason". No changes are applied automatically; you apply corrections yourself.

The default grammar instruction is: review the text and list only the corrections needed; do not rewrite the passage. If you want a different instruction, open the Prompt Library, find the "Check Grammar" built-in prompt, and edit its text — the command picks up your version automatically.

### Prompt Library

`Tools > AI Assistant > Prompt Library...` opens the full prompt management dialog.

**What it shows.** A searchable list of all prompts on the left (type in the search field to filter by name or category). The selected prompt's instruction text on the right. An optional input text field where you can type or paste text to use as the selection context.

**Running a prompt.**
1. Select a prompt from the list (or type in the search field to find it).
2. Optionally paste text into the input field. If blank, QUILL uses the current editor selection or full document.
3. Press **Run with AI**. The result opens in the AI Response dialog.

**Managing prompts.**

- **New Prompt** — opens a small dialog: enter a name, choose a category, and write the instruction text. Use `{selection}` where you want QUILL to insert the text.
- **Edit** — modify the name, category, or instruction of a selected user prompt. Built-in prompts can have their text overridden (the override is saved; the original is never deleted).
- **Disable/Enable** — hides or shows a prompt in the list without deleting it. Useful for built-ins you never use.
- **Delete** — removes a user-created prompt. Built-in prompts cannot be deleted.

**Importing and exporting prompt packs.**

QUILL uses `.pqp` (Prompt Quill Pack) files to share prompt collections.

- **Import .pqp** — opens a file picker; imports all prompts from the file. Prompts whose names already exist in your library are skipped.
- **Export .pqp** — saves all your user-defined prompts to a `.pqp` file you can share or back up.

A `.pqp` file is plain JSON with a human-readable structure:

```json
{
  "schema": "quill.prompt-pack/1",
  "name": "My Writing Prompts",
  "prompts": [
    {
      "name": "Make Punchy",
      "text": "Rewrite this as a punchy one-liner: {selection}",
      "category": "Editing"
    }
  ]
}
```

**Built-in prompts.** QUILL ships 12 built-in prompts across five categories. These are always present and fully editable; they cannot be deleted.

| Category | Prompt names |
| --- | --- |
| Editing | Check Grammar, Improve Clarity, Fix Grammar, Make Concise, Active Voice, Formal Tone, Conversational Tone |
| Writing | Continue from Here |
| Structure | Convert to Bullet Points |
| Research | Define This Term, Find Counterarguments |

**Quillin-contributed prompts.** Quillins can ship a `prompts.json` file that adds prompts to the library. The bundled `ai-writing-prompts` Quillin contributes 7 additional prompts (Expand This, Vary Sentence Rhythm, Make More Vivid, Write a Title, Generate Outline, Suggest Supporting Evidence, Plain Language). These appear in the list and can be run like any other prompt; they are not persisted to your library file.

### Skill Library (.sqp skills)

Skills are multi-step AI workflows. Where a prompt is one instruction, a skill is a sequence of steps where each step can use the output of the step before it.

`Tools > AI Assistant > Skill Library...` opens the Skill Library dialog.

**What a skill looks like.** A skill has a name, a description, and a list of steps. Before running, QUILL shows a parameter dialog if the skill declares any parameters (such as tone, target reading level, or output format). Each step runs in order, sends its prompt to the AI, and stores the response for the next step to use.

**Bundled skills.** QUILL ships four skills in the `ai-writing-skills` Quillin:

- **Accessible Rewrite** — Analyses your text for plain-language issues (long sentences, passive voice, jargon), then produces a targeted rewrite. You choose the target reading level (Grade 6, 8, or 10). The rewritten text replaces the selection when you Accept.
- **Research and Draft** — Extracts the central topic from your selection, gathers five supporting facts, then drafts a paragraph at your chosen tone and length.
- **Meeting Notes to Action Items** — Reads meeting notes, extracts every action item with owner and deadline, checks for missed items, and produces a clean follow-up summary. Output goes to clipboard.
- **Argument Strengthener** — Identifies your argument's logical structure, finds weaknesses and counterarguments, then produces a strengthened version tailored to your chosen audience.

**Running a skill.**
1. Open `Tools > AI Assistant > Skill Library...`
2. Select a skill from the list.
3. Press **Run**. If the skill has parameters, a small dialog appears — fill in the choices and press OK.
4. QUILL announces "Running step 1 of N..." as each step executes.
5. When complete, the result dialog appears. Read the output, then press **Accept** to apply it (if the skill places output in the document) or **Copy** to copy to clipboard.

**No streaming.** Each step sends a complete prompt and waits for the full response before the next step begins. This makes step outputs reliable and readable between steps.

**Authoring and sharing skills.** A skill is a `.sqp` (Skill Quill Pack) file — a plain Markdown document with YAML front matter. Open any `.sqp` file in QUILL to read and edit it. Share skills by sharing the file. See `docs/scripting.md` §20 for the full authoring reference, and `docs/skills-tutorial.md` for a guided walkthrough.

**Validating a skill file.** Run `python -m quill.tools.sqp_validator yourskill.sqp` to check for errors before sharing or shipping.

## Control Reference

The Control Reference is a full listing of every focusable control in QUILL, organized by section. For each control it shows: what the control does, what keyboard shortcuts apply to it, and which section of this guide covers it in depth.

See [docs/CONTROL_REFERENCE.md](CONTROL_REFERENCE.md) for the full reference.

The reference is auto-generated from `quill/core/help/topics.json`. To regenerate it after adding new topics:

```powershell
python -m quill.tools.build_docs
```
