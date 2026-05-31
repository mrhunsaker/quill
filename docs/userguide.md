# Quill User Guide

**QUILL** stands for **Quality, Usable, Inclusive, Lightweight, Literate**.

**QUILL: A quality, usable, inclusive, lightweight, and literate editor built for everyone who writes, codes, learns, and creates.**

Quill is a screen-reader-first writing and reading environment for Windows. It is designed to feel calm, predictable, deeply keyboard-friendly, and respectful of your focus. It is also ambitious. Quill is not only a place to write plain text. It is a place to open difficult documents, inspect structure, navigate long material, compare revisions, prepare content for Markdown or HTML, and work with accessibility and extraction issues without leaving the editor.

This guide is aligned to Quill 0.1.2 Beta, built by Blind Information Technology Solutions (BITS) together with Community Access.

This guide is written as a companion, not a reference wall. Read it from the beginning if you are new to Quill. Dip into the sections that matter most if you already know what kind of work you want to do.

Quill is also in beta. Expect polish, depth, and real daily utility. Also expect rough edges, unfinished flows, and the occasional surprise. If you find something confusing or broken, that is useful information. Quill is becoming stronger because real people are trying it on real work.

## Table of Contents

- [Start Here](#start-here)
- [What Quill Feels Like](#what-quill-feels-like)
- [Your First Session](#your-first-session)
- [The Main Window](#the-main-window)
- [The Menu Bar Reference](#the-menu-bar-reference)
- [Writing and Editing](#writing-and-editing)
- [Search, Replace, and Deep Navigation](#search-replace-and-deep-navigation)
- [Formatting and Markup Work](#formatting-and-markup-work)
- [Tools for Reading, Review, and Inspection](#tools-for-reading-review-and-inspection)
- [GLOW Workflows Inside Quill](#glow-workflows-inside-quill)
- [Accessibility and Low-Vision Features](#accessibility-and-low-vision-features)
- [Profiles, Keyboard Packs, and Customization](#profiles-keyboard-packs-and-customization)
- [Trust, Recovery, Sessions, and Safety](#trust-recovery-sessions-and-safety)
- [Working with Different Document Types](#working-with-different-document-types)
- [Help, Learning, and Daily Confidence](#help-learning-and-daily-confidence)
- [Beta Feedback and Bug Reporting](#beta-feedback-and-bug-reporting)
- [A Fast Shortcut Tour](#a-fast-shortcut-tour)

## Start Here

If you only have five minutes, do this:

1. Press `Ctrl+N` to create a new document, or press `Ctrl+O` to open one.
2. Type a few lines.
3. Press `Ctrl+Shift+P` to open the Command Palette.
4. Type `guide`, `spell`, `compare`, or `glow` and notice how quickly Quill turns intent into action.
5. Press `F6` to move into the status bar and hear how Quill treats even the bottom of the window as a working surface.
6. Press `F7` for spell check, `Ctrl+F` to search, or `Ctrl+K` to insert a link.

If you ever feel lost, use **Help → What Can I Do Here?**. Think of that command as the editor quietly putting a mentor beside you.

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

## The Main Window

Quill keeps its main window intentionally simple.

### Menu bar

The menu bar follows the Windows and Office order you likely expect:

- File
- Edit
- Insert
- View
- Search
- Navigate
- Format
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

You can reorder or hide status items through **Tools → Customize → Status Bar Settings...**.
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
- **Workspace Snapshots** lets you save and reopen groups of documents as a single workspace snapshot, similar to lightweight workspaces in Visual Studio Code.
- **Save** writes the current document.
- **Save As...** writes to a new path.
- **Save All** writes every modified open document.
- **Save As Plain Text...** exports a clean plain-text version.
- **Reload from Disk** throws away in-memory edits and reloads the file from storage after confirmation.
- **Restore Backup...** lets you restore a saved backup version.
- **Page Setup...**, **Print Preview...**, and **Print...** support paper and print workflows.
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

Quill then goes further with selection and navigation-aware editing:

- **Extend Selection Mode** turns selection growth into a dedicated mode.
- **Selection** submenu includes Select Line, Select Paragraph, Select Block, Select to Start or End of Line, and Select to Start or End of Document.
- **Recent Marks (Ring)** commands let you set a temporary mark, jump to previous marks, swap cursor and mark, and list recent marks while you move through an editing flow.
- **Insert Link...** creates a format-aware link.
- **Follow Link** opens the link under the caret.
- **Find...** and **Replace...** sit here as expected.
- **Replace...** includes a **Replace All** action in the dialog, so bulk replacement stays in one place.
- **Preferences...** opens the broader customization surface.

### View

The **View** menu controls how Quill behaves on screen without changing your content.

- **Enable System Tray Mode** lets Quill minimize into the tray instead of exiting.
- **Toggle Soft Wrap** changes line wrapping without modifying the file.
- **Toggle Dark Mode** switches between system and dark presentation.
- **Enable Persistent Undo** stores undo history across sessions for saved files.
- **Spell Check As You Type** enables live misspelling hints.
- **Show Line Numbers** changes the navigation and status-bar experience.
- **Start With No Document Open** makes Quill open into an empty workspace instead of a starter document.

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
- **Match Bracket**
- **Next Structure**
- **Previous Structure**
- **Next Region**
- **Previous Region**

Bookmark and search navigation:

- **Set Bookmark...**
- **Go To Bookmark...**
- **Find Next**
- **Find Previous**
- **Find All Matches**

If your work involves transcripts, legal text, long Markdown notes, HTML source, or extracted PDFs, spend time here. This is the menu that turns Quill from a text box into a navigable workspace.

### Format

The **Format** menu handles presentation and markup-aware editing.

Case operations:

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

Inline and structural formatting:

- Bold
- Italic
- Insert Heading levels 1 through 6
- Increase or decrease heading level
- Style headings (font, size, alignment) for the current level or all levels
- Open Heading Organizer (`Ctrl+Alt+Shift+H`) for heading-level edits, section reorder, and heading validation
- Insert bullet, numbered, and task lists
- Insert code block
- Insert footnote
- Insert table
- Insert HTML tag
- Insert Markdown tag
- Word prediction (`Ctrl+Space`)
- Insert snippet (`Ctrl+Alt+Space`)
- Manage snippets (`Ctrl+Alt+Shift+Space`)

Quill treats Markdown and HTML as working surfaces, not special-purpose export formats. This menu is where that philosophy becomes practical.

### Word prediction and snippets

Quill 0.1.2 separates live prediction from snippet insertion so the hotkeys feel more like a modern editor:

1. Press `Ctrl+Space` to open **Word Prediction**.
2. Type to surface matching document words, HTML tags, and Markdown tags.
3. Use arrow keys to choose a result and press Enter to insert it.

For setup and maintenance:

- Press `Ctrl+Alt+Space` for **Insert Snippet**.
- Press `Ctrl+Alt+Shift+Space` for **Manage Snippets** (create, edit, delete, import, export, and starter packs).
- Open **Preferences -> Install Starter Snippet Packs** to install sample libraries for daily writing, developer flow, and support/accessibility notes.
- In **General Preferences**, toggle **Word prediction and tag IntelliSense** or **Expand snippet triggers while typing** as needed.

Snippets still support placeholders such as `${input:name}`, `${choice:a|b}`, `${date}`, `${time}`, and `${cursor}`.

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
- **Writing Assistant...**
- **Rewrite Selection**
- **Summarize Selection**
- **Continue Writing**
- **Fix Grammar**
- **Run Python...**
- **Browser Preview...** (`Ctrl+Shift+V`)

Browser Preview opens the current document in your chosen browser, defaulting to the system browser. It refreshes as you type so Markdown and HTML changes stay visible without leaving Quill.

The Writing Assistant shell ranks Quill commands from your prompt, offers preset prompts for rewrite/summarize/continue/grammar flows, and Run Python executes a sandboxed transform against the current document text and selection.

Use **AI -> AI Connection...** or **Preferences -> AI Connection** to set provider, host, model, and optional key.

AI connection flow:

1. Choose provider (`Ollama (local)`, `Ollama Cloud (API key)`, or `Custom HTTP`).
2. Confirm host URL and model.
3. Enter key only when your endpoint requires authentication.
4. Use **Verify Connection** to test endpoint and credentials.
5. Use **List Models** to fetch available models and select one.
6. Save settings. Quill auto-runs verification and updates the AI status line in the AI menu.

Quill stores optional keys with Windows DPAPI and announces the verification result in plain language for immediate screen-reader feedback.

These help you stay inside the editor instead of breaking flow for small writing chores.

#### Read aloud and integrations

- **Read Aloud** submenu for start or pause, stop, and voice selection
- **Dictation** submenu for Windows dictation, plus an opt-in **Hey QUILL Commands** toggle that lets dictation phrases trigger Quill commands instead of inserting text.
- **Integrations** submenu with **OCR Image...** and shell integration commands.

Read Aloud is particularly useful for proofreading by ear. OCR Image handles image-to-text work with an explicit consent and progress flow.
Dictation uses Windows' own speech input. When Hey QUILL Commands is enabled, Quill stays silent and only listens while dictation is active, then runs the matching action after the wake phrase.

#### Document intake and extraction review

- **Document Intake Report...**
- **Review Extraction Quality...**
- **Report Bad Extraction...**

These commands matter when Quill is acting as a trusted reader for imported formats rather than a plain writer. They help answer questions like:

- How good was the extraction?
- Did the source likely contain structure that did not survive?
- Is this document safe to quote from directly?
- Do I need to escalate this source for manual cleanup?

Release-safety note for current beta validation:

- Word files (`.doc`, `.docx`) open into the normal plain-text editing surface.
- CSV/TSV files open into the normal plain-text editing surface.
- Structured Word and CSV grid surfaces remain in the codebase behind an internal verification gate.

#### GLOW

- **GLOW Audit Current Document**
- **GLOW Audit Selection**
- **GLOW Fix Current Document**
- **GLOW Fix Selection**

GLOW inside Quill is a guided layout and output workflow for deterministic text review. Today it focuses on plain text, Markdown, and HTML. It looks for issues such as:

- missing spaces after Markdown heading markers
- heading-level jumps
- generic link text
- missing HTML language metadata
- missing HTML image alt attributes
- tables without HTML header cells
- dense paragraphs and plain-language friction

The key design choice is how GLOW feels inside Quill. Audit results open as readable Quill tabs. Fixing the current document opens a named preview tab and immediately starts a compare session against the original. Selection fixes apply in place to the current selection, paragraph, or line. That keeps GLOW close to the writing experience instead of making it feel like a detached compliance tool.

#### Authoring and automation

- **Regex Helper...**
- **Pandoc Conversion Wizard...**
- **External Tools and Format Support...**
- **GLOW** submenu
- **Macros** submenu
- **Convert** submenu with sort, reverse, deduplicate, trim trailing whitespace, normalize whitespace, and convert indentation commands

These are especially valuable in large cleanup jobs and repetitive editing workflows.

The new external-tools surface deserves a special note. Quill does not treat optional tools as hidden technical chores. **External Tools and Format Support...** explains what each supported helper unlocks, whether Quill can already see it, and what the best first touch point is. If Pandoc is installed or bundled, **Pandoc Conversion Wizard...** can turn supported source files into Markdown, HTML, or plain text tabs that open directly in Quill. That makes Quill feel less like a dead-end editor and more like a calm bridge into real-world document cleanup and GLOW-oriented handoff work.

#### Compare documents

- **Compare with File...**
- **Compare Open Documents**
- **Compare Next Difference**
- **Compare Previous Difference**
- **Difference List**
- **Compare Options**
- **Compare Summary**
- **Copy Current Difference**
- **Copy All Differences**

Quill's compare model is practical and local. It supports file-to-file review, multi-document review, summary generation, and synchronized movement through differences.

#### Accessibility

- **Accessibility Audit...**
- **Keyboard Trap Snapshot...**
- **Validate Contrast...**
- **Link Inventory...**

These tools help review the editor experience itself, the current document's link surface, and low-vision presentation issues.

#### Support and customization

- **Show Notifications**
- **Report a Bug...**
- **Save Diagnostics...**
- **Check for Updates...**
- **Profiles and Features...**
- **Status Bar Settings...**
- **Keymap Editor...**
- **Export Keymap...**
- **Import Keymap...**
- **Reset Keymap**

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
- **Check for Updates...** verifies the signed update manifest, opens the installer download page, and can close Quill so setup can run immediately.
- **About Quill** shows version and publisher details.

If you only remember one thing about Help, remember this: it is a working surface, not a dead-end menu. The welcome guide teaches the basics, the keyboard reference reflects your live bindings, the user guide gives the full map, diagnostics package the current state, and the bug-report action turns that state into a support-ready starting point.

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

### Copy With Source

`Ctrl+Shift+C` copies the current selection, then appends a source reference that captures document context. If nothing is selected, Quill uses the current line. This is excellent for notes, review workflows, and evidence gathering.

### Extend Selection Mode and marks

`F8` toggles Extend Selection Mode. This lets you grow selections more deliberately. The mark ring adds an editor-like memory of important places in a document. Set a mark, move, then return or exchange point and mark when you need to re-anchor yourself.

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

Read Aloud uses local voices when available. You can start, pause, stop, and choose a voice. It is useful for proofreading by ear, reviewing extracted text, and staying oriented in dense material.

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

Some of these live in the View menu for quick toggling. Others live in **Profiles and Features...**, **Status Bar Settings...**, **Keymap Editor...**, and the related customization commands under **Tools**.

## Trust, Recovery, Sessions, and Safety

Quill is serious about recovery and user control.

### Sessions

Sessions in Quill are best understood as **workspace snapshots**. A session captures your currently open documents and active tab, then lets you reopen that exact working set later.

If you are familiar with VS Code workspaces, think of Quill sessions as a simpler, document-focused version of that idea:

- save your current workspace state
- reopen it from Recent Workspace Snapshots
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

RTF documents can use Quill's rich-text-capable editing surface when formatting fidelity matters. Commands such as bold, italic, and underline are exposed contextually in this mode while preserving Quill's keyboard-first, screen-reader-first behavior.

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

## Help, Learning, and Daily Confidence

Quill includes several layers of help because confidence does not come from memorizing everything.

- **Open Welcome Guide** when you want a lighter orientation.
- **Open User Guide** when you want the full map.
- **Open Keyboard Reference** when you want exact current bindings.
- **What Can I Do Here?** when you need immediate, contextual guidance.
- **Why Don't I See a Feature?** when a command seems to have disappeared.

That last command matters more than it first appears. It turns feature visibility from a mystery into an explanation.

## Beta Feedback and Bug Reporting

Quill is ready for serious beta use, and Quill 0.1.2 Beta now ships a real in-app support starting point.

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

Until that exists, use the current Help-menu path as the practical bridge. The important improvement in Quill 0.1.2 Beta is that Quill now helps users gather diagnostics locally, review what is being shared, and start a structured support report without forcing them to begin outside the tool.

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
