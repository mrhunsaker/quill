# QUILL 0.6.0 release notes

This release sets a new watermark for what an accessible writing environment can do. Typed triggers that feel like magic. Extensions with real settings you can search and configure by keyboard. Braille editing and professional translation built for people who actually need it. Compare mode. Code-aware navigation. A sound layer you shape yourself. And underneath it all, an extension architecture that lets a small, well-declared Quillin feel like a first-class feature of the application.

Everything is built screen-reader-first. Every new view is a real, navigable control. Every new action is announced, undoable, and keyboard-complete. No surprises, no visual-only flourishes, no mouse required.

If you are upgrading from 0.5.0, the "Things that work a little differently now" section near the end lists the few places where a habit or a menu location changed.

## New: Insert Automation — type a trigger, get magic

This is the one that changes how you work day to day.

Insert Automation is a unified system for typed shortcuts, templates, log files, and text generation. It brings together four related ideas — abbreviations, smart triggers, document directives, and append anchors — into one coherent, keyboard-first platform. Everything is announced, undoable, and discoverable. Nothing scans your file silently or runs without an exact match.

**Typed abbreviations.** Type a short word and press a delimiter (space, comma, period, and more) and QUILL replaces it with the full text. The **Smart Insert** Quillin ships five right out of the box:

- **qbug** — a complete bug report template: Title, Build, Screen reader, Windows version, Steps to reproduce, Expected result, Actual result, Notes. Type it, press space, and the whole form lands at your cursor.
- **qmeet** — a meeting notes template with today's date already filled in. Attendees, Purpose, Notes, Action Items.
- **qlog** — today's date and time, for a quick timestamped entry.
- **qtodo** — a short to-do checklist, three blank items ready to fill.
- **qbrf** — a multi-page BRF test document, generated on the spot, ready to feed to the braille translator.

Your own abbreviations always win if there is a conflict. Quillin-provided ones are listed in the Insert Automation Reference and can be disabled individually.

**Smart text triggers.** Type a command alone on a line and press Enter and QUILL replaces the whole line with the result. These begin with `=` so they can never collide with an ordinary sentence:

```
=bug()            → bug report template
=meeting()        → meeting notes template
=journal()        → journal entry with today's date
=todo(5)          → five-item to-do checklist
=logentry()       → timestamp at the cursor, formatted your way
=rand(3,4)        → three paragraphs of four readable sentences each
=brftest()        → a complete, predictable BRF test document
```

The parser is strict: it only activates when the trigger is alone on the line, only accepts the allowed number and type of arguments, and rejects anything it does not recognize outright — so typing `=bug()` in the middle of a sentence is always safe. If you ask for a very large insertion, QUILL asks for confirmation before writing anything.

**`.LOG` file compatibility.** Open a file whose first line is `.LOG` and QUILL does what Notepad does: it finds the right spot and inserts a fresh timestamp. If you place a `QUILL-LOG-APPEND-HERE` anchor near the bottom of the file, the timestamp lands just before the anchor and the anchor stays in place for next time. If the file is read-only, QUILL tells you so rather than failing silently.

The timestamp format is configurable — Long date and time, Short, ISO 8601, Date only, Time only, or a custom `strftime` pattern — through **Preferences → Smart Insert → Log Mode**.

**Append anchors.** Any file can have a `QUILL-APPEND-HERE` marker near the bottom. Once present, generated content is inserted before it — not shoved at the absolute end, not after footer notes or metadata. A stable anchor means generated content always lands exactly where you want it, every time.

**Every action is safe.** Abbreviations trigger only after an exact match and a delimiter. Smart triggers inspect only the current line and only activate on Enter. No file is scanned in full on open. Quillin-provided triggers run only when the Quillin is enabled. Every result is announced, every insertion is one undo step, and nothing modifies a read-only file.

## New: The Quillin Extension Platform

QUILL 0.6.0 ships a comprehensive upgrade to the Quillin extension framework. What started as a way to contribute commands and snippets is now a full extension platform: Quillins can subscribe to events, own their settings, display live data in the status bar, declare dependencies, restrict network access, and initialize themselves cleanly when the user enables them or QUILL shuts down.

The upgrade covers every layer of the system — the manifest, the validator, the JSON schema, the API surface, and the developer tooling — all built screen-reader-first and enforced at install time so authors cannot accidentally ship a misbehaving extension.

### Settings and preferences

Quillins can now contribute their own settings pages. A Quillin declares its preferences as structured data in the manifest — control type, label, description, default value, validation rules — and QUILL renders everything using accessible, keyboard-navigable stock controls. The Quillin never touches wxPython directly. QUILL handles layout, tab order, focus, keyboard navigation, search, reset, and accessibility entirely.

A Quillin with several settings groups declares **tabs** inside its preferences page. Each tab is arrow-key navigable and clearly announced. The Smart Insert Quillin ships with five tabs: General, Log Mode, Smart Triggers, Abbreviations, and BRF Testing. BRF Tools shows what a specialized page looks like — four tabs covering Translation defaults, Page Handling, Status Bar display, and Advanced diagnostics.

Settings are stored per Quillin, survive restarts, and migrate when a Quillin updates its manifest. They appear in Preferences search alongside QUILL's own settings, identified by Quillin, page, and tab.

New for 0.6.0: individual settings may carry **`search_keywords`** — extra synonyms and technical terms that surface the setting when users search for a concept they know by a different name. For example, a "Date format" setting might carry keywords `timestamp, iso, strftime` so it appears for all three search queries.

### Document and lifecycle events

Quillins can subscribe to document lifecycle events and run code automatically when important moments happen — no user action required.

**Fourteen events. The full lifecycle covered.**

| Event | When it fires |
| --- | --- |
| `document.opened` | A file was opened from disk |
| `document.activated` | The user switched to this document tab |
| `document.before_save` | Right before saving — time to validate or transform |
| `document.after_save` | After a successful save — safe to log, sync, or confirm |
| `document.before_close` | Before a tab closes — safe to warn |
| `document.after_close` | After a tab closes — safe to clean up |
| `document.created` | A new blank document was created |
| `document.loaded_from_session` | A document was restored from a crash or session file |
| `smart_trigger.entered` | Any smart trigger was activated |
| `abbreviation.expanded` | Any abbreviation was expanded |
| `quillin.enabled` | This Quillin was enabled or QUILL started with it active |
| `quillin.disabled` | This Quillin was disabled in Quillin Manager |
| `quill.shutdown` | QUILL is about to exit |
| `settings.changed` | A setting owned by this Quillin was changed by the user |

The high-frequency events — text changed, cursor moved, key pressed — are deliberately not available. They would let a Quillin observe keystrokes, which is both a performance problem and a privacy problem.

**Lifecycle events** let Quillins manage their own existence. `quillin.enabled` is ideal for initialization — announcing activation, building caches, or registering anything that needs the API live. `quillin.disabled` lets a Quillin clean up gracefully. `quill.shutdown` lets a Quillin flush state before the process exits. `settings.changed` fires immediately when the user saves a preference change so Quillins can hot-reload their internal config without restarting.

**Event filtering.** Each subscription can declare `conditions` so it only fires for certain file types, path patterns, or content signatures. A template inserter can limit itself to files under `\journal\`. A `.LOG` handler can require `*.log` files. These filters are pure data, with no code to debug.

**The capability gate.** A Quillin must declare `document.events` in its capabilities to subscribe to any event. Missing the capability or the `main` module fails validation at install time, not at runtime.

### Status bar contributions

Quillins can add live cells to the QUILL status bar. Each cell has a handler the host calls on demand — after a save, on tab switch, or on a timer — and whatever the handler returns becomes the cell text.

To add a cell, declare `ui.status` in capabilities, provide a `main` module, and describe the cell:

```json
"status_bar": [
  {
    "id": "wordcount",
    "label": "Words: --",
    "handler": "get_word_count",
    "tooltip": "Current document word count",
    "width": 12
  }
]
```

The cell has a `tooltip` that is read to screen-reader users when the cell receives focus — so the status bar is fully navigable and informative without being a visual-only feature.

### Categories

Quillins may declare one or more category labels — `writing`, `accessibility`, `braille`, `productivity`, `developer`, `formatting`, `navigation`, `ai`, `integration`, `education`, `utilities` — for filtering in the Quillins Manager. A single manifest line is enough:

```json
"categories": ["writing", "productivity"]
```

### Quillin dependencies

A Quillin can declare that it requires another Quillin to be installed and enabled:

```json
"requires": [{ "id": "com.quill.journalstamp", "min_version": "1.0.0" }]
```

QUILL verifies the dependency at load time. If it is missing or too old, the declaring Quillin fails to load with a clear message.

### Network host allowlist

Quillins with the `net` capability may restrict which servers they connect to:

```json
"net_allowed_hosts": ["api.openweathermap.org", "*.example.com"]
```

When the list is non-empty, QUILL blocks connections to any host not on the list, even after the user has granted blanket `net` consent. Wildcards (`*.example.com`) are supported.

### Command descriptions and search

Commands may carry a `description` field that appears in the keyboard reference and command palette — a one-line summary of what the command does, distinct from the menu title:

```json
"description": "Inserts a bug report skeleton with title, steps, expected, and actual fields."
```

### Developer logging (`api.log`)

Quillins with the `ui.log` capability may call `api.log(message)` to write structured log lines to the QUILL Developer Console. The console is opened from **Tools → Developer Console** (available in dev builds; toggle with `QUILL_DEV_BUILD=1`). `api.log()` is a no-op in production with the console closed, so it adds zero overhead to normal usage and never writes to files or speaks to the screen reader.

### Announcement priority

`api.announce()` now accepts a `priority` keyword argument:

```python
api.announce("Saved.", priority="quiet")      # queued
api.announce("File not writable.", priority="urgent")  # interrupts
```

Valid values: `quiet`, `normal`, `urgent`. The host maps these to the screen reader's urgency channel. Use `quiet` for informational messages; use `urgent` only for errors that need immediate attention.

### Scaffold tool

A new command-line tool generates a ready-to-edit Quillin directory:

```
python -m quill.tools.quillin_new com.example.myquillin "My Quillin"
```

Options include `--layer1` (snippet-only, no Python), `--categories`, `--doc-events` (sample lifecycle handlers), and `--status-bar` (sample status cell). The tool writes `manifest.json`, `extension.py`, `README.md`, and `LICENSE`, then tells you the next three steps. Run `quillin_lint` on the output to verify before publishing.

### User control — what you can control and how

One of the design principles of the Quillin framework is that users stay in control at every level. Here is how that works in practice in 0.6.0.

**Enable or disable any Quillin.** Open **Tools → Quillins Manager**. Select a Quillin and press **Enable** or **Disable**. The change takes effect immediately — no restart required. Disabling a Quillin stops all its commands, event handlers, and status bar cells from running. Its preferences data is preserved so it picks up where it left off if you re-enable it.

**Per-action consent for sensitive capabilities.** Four capabilities require a dialog confirmation every time a Quillin tries to use them:

| Capability | What it does |
| --- | --- |
| `fs.read` | Read a file from disk |
| `fs.write` | Write a file to disk |
| `net` | Make a network request |
| `settings.core.write` | Change a QUILL-wide setting |

When a Quillin tries to use one of these, QUILL pauses and shows a dialog: "A Quillin is requesting the 'fs.read' capability for: read_file(path). Allow this action?" You choose yes or no. Choosing no raises a `ConsentDeniedError` that the Quillin handles gracefully. This dialog fires for every individual action — not once at install time — so a Quillin that reads files can never read one you have not explicitly approved.

The remaining capabilities — editor access, UI announcements, clipboard, storage, settings.own.*, document events, status bar, developer log — are granted once at install time (or pre-granted for bundled Quillins) and do not prompt again.

**Per-event toggle in the Quillin Manager.** Each document event subscription in the manifest carries an `enabled_by_default` field. When `false`, the subscription starts inactive. Users can change this at any time: open the Quillin Manager, select the Quillin, and click **Configure Events...** to see every event subscription with a checkbox. Turning an event off stops the handler from firing; turning it back on resumes it. The per-event state is persisted in `state.json` alongside enable/disable and capability grants.

**Capability declarations are enforced, not advisory.** At runtime, if a Quillin calls an API it did not declare in its `capabilities` list, the call is blocked with a `CapabilityError` and the Quillin is notified rather than QUILL crashing. Declarations are validated at install time by `quillin_lint` and re-validated at load time by the manifest parser.

**Third-party Quillins are locked off.** The SEC-8 gate (`core.third_party_plugins`) is `locked_off` for QUILL 1.0. A shipping build never discovers, loads, or executes third-party Quillin code. The Quillin Manager opens and is fully navigable — it simply reports that third-party Quillins are disabled. This will lift when the third-party publishing and review process is ready.

**`min_quill_version` is enforced at load time.** When a Quillin declares `"min_quill_version": "0.6.0"` and the running QUILL is older, the Quillin is rejected during discovery and listed in the Manager with an explanatory error. Users see "requires QUILL 0.6.0 (running 0.5.x)" rather than a silent failure or a crash.

**`requires` is enforced at load time.** If a Quillin declares a dependency (`requires`) on another Quillin that is not installed, or is installed at a version too old to satisfy `min_version`, the dependent Quillin is blocked from loading. The Manager shows the specific dependency error so users know what to install. Circular dependencies are caught during validation.

**`net_allowed_hosts` is enforced at every fetch call.** When a Quillin declares `"net_allowed_hosts": ["api.example.com"]` and then tries to fetch from a host not on that list, the call is blocked before reaching the network — even if the user has granted the `net` capability. Wildcard patterns (`*.example.com`) allow any subdomain but not the bare domain. An empty `net_allowed_hosts` with the `net` capability keeps the current behavior: any host is reachable with user consent.

### Five bundled Quillins — comprehensive sample coverage

QUILL 0.6.0 ships five bundled Quillins that collectively demonstrate every contribution type and framework feature. Each one is a working, useful extension first and a reference implementation second.

- **Smart Insert** (`com.quill.smartinsert`) — typed abbreviations and smart triggers for bug reports, meeting notes, log entries, to-do lists, and BRF test documents. Five tabs of configurable preferences. Now carries `categories: [writing, productivity, formatting]` and command `description` fields on every command.

- **BRF Tools** (`com.quill.brftools`) — preferences for braille translation, page handling, and status bar display. Now carries `categories: [braille, accessibility]`.

- **Journal Stamp** (`com.quill.journalstamp`) — subscribes to `document.created` (inserts a date header), `document.after_save` (announces word count and daily goal progress), `document.loaded_from_session` (announces which document was restored), `quillin.enabled` (logs activation), and `settings.changed` (hot-reloads preferences). Settings include `search_keywords` on the date format and daily goal controls. Categories: `writing, productivity`.

- **Document Guardian** (`com.quill.docguardian`) — subscribes to `document.before_close` (warns on unfinished docs), `document.before_save` (stamps an `Updated:` line), `document.after_save` (confirms with file size), `quillin.enabled` (announces and logs activation), `quillin.disabled` (announces deactivation), and `quill.shutdown` (cleans up). Categories: `writing, productivity`.

- **Status Scribe** (`com.quill.statusscribe`) — a live word/character/sentence count in the status bar, updated after every save and on tab switch. Demonstrates `status_bar` contribution, `ui.log` developer logging, `quillin.enabled`/`quillin.disabled`/`settings.changed` lifecycle events, and announcement priority. Categories: `writing, productivity, accessibility`.

## New: Braille Mode

QUILL can now opens and edit formatted braille text files. The point is to let a braille proofreader move through a transcription the way it is actually laid out, in braille pages and cells, with speech that tells you exactly where you are.

**Opening a braille file.** Open any braille file the way you open anything else. QUILL reads it as braille text, and the file is scanned for any character that is not braille ASCII. Nothing is transformed on the way in, what you see is the file's bytes.

**Saving is byte-for-byte.** When you save a braille file, QUILL preserves it exactly: no trailing-space trimming, no line-ending normalization, and form feeds (the hard page breaks) are kept. If the text contains characters outside the braille-ASCII range, QUILL still saves them as-is and gives you a single, non-blocking spoken warning so nothing is silently changed. This means a round-trip — open, save — gives you back an identical file.

**The braille status cell.** While a braille file is active, the status bar carries a braille cell that updates as you move: it reads like `BRF Pg 12/87 | Ln 14/25 | Cell 31/40 | Print 7`. That is the braille page, the line within the page, the cell within the line, and the print page. Print-page detection arrives in a later phase; until then the print segment reads `Print ?`.

**The Braille menu.** Braille commands live under **Tools > Braille**. Bindings are intentionally left unset so nothing collides with your screen reader or existing editor keys; you can assign your own in the keyboard customizer, or run them from the Command Palette.

- **Status** — Read Braille Status (respects your status verbosity), Read Detailed Braille Status, Read Current Line and Cell, Read Current Braille Page, Read Current Print Page, and Read Progress Summary (how far through the document you are).
- **Navigation** — Go to Braille Page… (type a page number), Next Braille Page, and Previous Braille Page. Stepping past the first or last page tells you there is no more.
- **Page Tools** — Insert Braille Page Break (a form feed) and Remove Braille Page Break at the cursor, plus Recalculate Page Map (rebuild the page map after edits) and a placeholder for Normalize Line Endings.

Every status and navigation command is safe to run on a non-braille document — it simply tells you "This is not a braille document" rather than doing anything.

**Translation (Universal QUILL Braille Pack).** Forward and back translation between print text and braille require the optional **QUILL Braille Pack**, which can be selected during installation. The pack uses a three-layer architecture: a full technical catalog of every available liblouis table, a set of user-facing profiles that map friendly names to the correct tables, and the translation runtime itself.

When the pack is installed, the **Translation** submenu is organized into three sections:

- **UEB (Unified English Braille)** — Contracted (Grade 2), Uncontracted (Grade 1), Translate Selection to UEB, and Back-Translate UEB.
- **Standard American English (Legacy)** — Contracted (Grade 2) and Uncontracted (Grade 1) using the traditional North American English tables.
- **More Languages** — populated automatically from the pack's profile catalog: German, French, Spanish, Russian, Korean, and dozens more. Languages with both contracted and uncontracted variants appear as their own sub-group.

When the pack is absent, the Translation submenu is hidden entirely — you never see disabled items. Forward translation opens the BRF result in a new document and tells you how many braille pages it produced. Back-translation always opens its result as a clearly labeled **draft** because no automatic back-translation is authoritative. Translation runs entirely out of process, so a liblouis failure can never take QUILL down. The Translation submenu is also hidden in Safe Mode.

## New: sound notifications you can shape

QUILL can now play short, non-speech audio cues — earcons — at meaningful moments: a file saved, a search found, a comparison opened. The point is to let your screen reader stay focused on the text while a quick sound carries the "something happened" signal.

- **What it is.** Sounds come from a *sound pack*: a folder (or a single `.qsp` file) of audio clips with a small manifest that says which event plays which sound. QUILL ships a pack called **Ink**, and you can drop in your own.
- **QUILL key confirmation tone.** When you press the QUILL key (`Ctrl+Shift+Grave`) to arm the prefix, QUILL now plays a short two-tone ping (`quill_key_pressed`) — distinct from every other earcon — so you get instant audio confirmation that the prefix is live, without waiting for speech. This earcon is included in all bundled sound packs and can be toggled individually in **Tools → Reading & Dictation → Sound Events...**.
- **You are in control.** Open **Tools → Reading & Dictation → Sound Events...** to switch individual events on or off. They are grouped — Earcons, Compare, and Indentation tones — so you can keep the cues you like and silence the rest. **Toggle Sound Notifications** turns everything on or off at once and plays a short "on" or "off" cue so you know where you landed.
- **Why it matters.** For a screen-reader user, a well-chosen sound is faster than a spoken phrase and never talks over your reader. Because it is all opt-in and per-event, it adds information without adding noise.

### Indentation tones for code

When you turn on indentation tones (pick a musical scale under the **Indentation tones** setting, or leave it Off), QUILL plays a pitch that rises as your caret moves deeper into indented code and falls as you come back out. Blank lines stay silent and hold the last level, so cursoring through gaps does not chirp. It is a quiet, ambient way to feel the shape of code without counting spaces.

## New: compare mode you can navigate by ear

Comparing two files is now a first-class, keyboard-driven experience. Open a comparison and move through it with **F8** (next difference), **Shift+F8** (previous), **Ctrl+F8** (re-announce the current one), and **Alt+F8** (hear just the words that changed on a line). The differences are presented as a real list you can review one at a time with your screen reader.

If you use a sound pack, compare mode also gives you distinct cues for opening and closing a comparison, stepping between differences, and bumping against the first or last one — so you can keep your attention on the text and let sound tell you where you are.

**Why it matters.** Reviewing edits used to mean a lot of careful re-reading. Now you can step difference-to-difference at the speed you read, with both speech and optional sound confirming each move.

## New: code-aware editing

Open a source file and QUILL loads a *language profile* from the file extension — Python, JavaScript and TypeScript, Kotlin, Shell, Markdown, JSON, TOML, and SQL are recognized, with a sensible plain-text fallback.

- **Move by token.** **Next Token** and **Previous Token** (in the Navigate menu) jump the caret to the next identifier, keyword, operator, or literal, which is far more predictable than word movement when you are reading code by ear.
- **Set the language yourself.** **Navigate → Set Document Language** overrides the automatic choice — handy for an unsaved buffer, an unusual extension, or a snippet pasted into a plain file.

Paired with indentation tones, code-aware editing lets structure come through as pitch while you move through the meaning token by token.

## New: text encoding tools

If you have ever fought a file that was UTF-8 when the next tool wanted plain ASCII, these three commands under **Format → HTML & Encoding** are for you.

- **Show Non-ASCII Characters** opens a read-only report of every character beyond plain ASCII — with its line and column, codepoint, name, and whether it converts cleanly to Latin-1 and Windows-1252 (MS-ANSI). Reviewing that list with your screen reader replaces the old trick of running a file through `iconv` with a sentinel string and hunting for what failed.
- **Jump to Source Line** — while the report is open, move your cursor to any character entry row and invoke this command (**Format → HTML & Encoding → Jump to Source Line**) to switch to the source document and land on the reported line. Assign it a key in the Keymap Editor for faster character-by-character review.
- **Jump Back to Non-ASCII Report** — returns focus to the report tab so you can continue stepping through the list without reaching for the mouse.
- **Convert Non-ASCII to HTML Entities** rewrites every accented letter or symbol as an HTML entity (`&eacute;`, or `&#233;` when there is no name), while leaving ordinary text and existing markup alone. This is the reliable way to feed text to a tool — Pandoc is the classic example — that refuses anything with high characters in it.
- **Re-encode As...** saves a copy in the encoding you choose (UTF-8, UTF-8 with a byte-order mark, Latin-1, Windows-1252, or ASCII). Anything that does not fit a narrow target is written as a numeric HTML entity instead of a silent question mark, so nothing is quietly lost.

**Why it matters.** This turns a fiddly, error-prone command-line ritual into five clear, screen-reader-friendly menu commands — and the jump navigation means you can inspect every flagged character in place, then come back to decide what to do with it.

## New: hand it over in Word (or RTF)

Sooner or later somebody asks for "the Word version." Now you can just give it to them. **File -> Save As...**, pick **Word Document (*.docx)** (or Rich Text) from the type list, and QUILL converts your document on the way out the door — no copy-paste-into-Word dance, no reformatting marathon.

And because we hand the conversion to Pandoc with real Word styles, your headings come out as actual Word headings, not "bold text that looks like a heading." That means the file is navigable by the next person's screen reader too — accessibility doesn't stop at the export button.

A word to the wise: Word keeps whatever structure your source had. Save a richly formatted Markdown or HTML document and it arrives dressed for the occasion; save a plain-text file and you get a tidy but unadorned document, because there was no structure to carry. QUILL will tell you so rather than quietly flattening your work.

## New: citations without the tears

Setting up MLA or Chicago citations has a special talent for going wrong at 2 a.m. the night before a paper is due — a comma in the wrong place, an italic that should not be there, a hanging indent that refuses to hang. QUILL now does the fussy part for you.

**Insert -> Insert Citation...** opens a plain, labelled form: pick your source type (book, journal article, or website), pick your style (MLA 9, Chicago 17, or APA 7), type in what you know — author, title, year, the usual suspects — and choose whether you want the in-text citation, the full bibliography entry, or both. QUILL formats it correctly and drops it in at your cursor.

You provide the facts; QUILL handles the punctuation gymnastics. The goal here is simple and, frankly, a little bit personal for an accessibility-first editor: a screen-reader user should never be at a disadvantage just because citation formatting is finicky visual busywork. Now you are on the same footing as everyone else in the seminar — and you got there without fighting a single hanging indent.

## New: Vision Prompt Library — contributed by Kelly Ford

QUILL 0.6.0 ships a Vision Prompt Library for the **Describe Image with AI** feature, contributed by [Kelly Ford](https://github.com/kellylford). Kelly independently built and evaluated 12 prompt styles drawn from his [Image Description Toolkit](https://github.com/kellylford/Image-Description-Toolkit) — a set of experimental tools for accessible image interaction that every accessibility developer and practitioner should know about.

Instead of a single hardcoded prompt, you now choose from twelve IDT-evaluated styles, each targeting a specific use case: a concise identification, a detailed scene description, an alt-text optimized for web publishing, a screen-reader-first narrative, a document-context interpretation, and more. Styles are evaluated and curated, not randomly generated.

- **Zero disruption by default.** If you never change a setting, Describe Image behaves exactly as before — the default IDT style is applied silently with no extra clicks.
- **One click to try a different style.** After a description arrives, a **Try a different prompt...** button appears in the review dialog. One click re-runs the description with the next style in the list. No re-uploading, no dialog re-opening, no extra navigation.
- **Opt-in pre-describe picker.** If you want to choose a style *before* describing an image, enable the style picker in **Settings → AI**. Once on, you see a focused, keyboard-navigable list of the twelve styles before every description.
- **Manage Image Prompts dialog.** Open **AI Hub → Image Prompt Styles...** to see all built-in styles with a read-only preview pane, toggle styles on or off, set the default, and add custom prompts of your own. Built-in styles are immutable; custom prompts are additive.
- **Settings sync immediately.** A bug where AI Hub changes to the vision settings (picker toggle, default style) had no effect until restart is fixed. Changes now apply the moment you save.

Kelly's Image Description Toolkit is an independent project worth bookmarking: [https://github.com/kellylford/Image-Description-Toolkit](https://github.com/kellylford/Image-Description-Toolkit). He also maintains several other screen-reader-friendly applications — [QuickMail](https://github.com/kellylford/QuickMail) (an accessible IMAP email client), [RSSQuick](https://github.com/kellylford/rssquick) (an accessible WPF RSS reader), and [ChatViewer](https://github.com/kellylford/ChatViewer) (a GitHub Copilot Chat viewer). His work consistently puts the screen-reader user first. Thank you, Kelly.

## New: Dynamic Keyboard Reference

The keyboard reference is no longer a static document. It is now generated live from the active command registry and your current feature profile.

- **Reflects your actual setup.** If you rebind a key or switch to a different keyboard pack, the exported HTML reference updates instantly to show exactly what is bound.
- **Layer-aware.** The reference now explicitly documents the layered nature of the QUILL key, including the prefix chords and the dedicated browse mode (Quick Nav) shortcuts.
- **Accessible export.** The output is a clean, semantic HTML page designed for high-performance screen-reader review.


## Smaller additions worth knowing

- **Speak where you are.** From the QUILL key, press **F** to speak the window title, **P** to speak the full file path, or **Q** to speak a short status summary — without leaving the editor.
- **Switch documents with Ctrl+Tab** (and Ctrl+Shift+Tab to go back), the shortcut your fingers already expect.
- **Files open where you work.** Open and Save As now start in your Documents folder, and you can set your own default startup folder in Preferences — no more landing in the install directory.
- **Launch straight to the spot.** `--goto FILE:LINE:COL` opens a file at a position in one argument (great when a linter or search result hands you a `file:line:column` string), and `--diff LEFT RIGHT` opens two files straight into compare mode.
- **A friendlier bug report.** **Help → Report a Bug...** now opens focused on the Summary field, remembers your name and email so you only type them once, and asks which screen reader you use (pre-selected from what QUILL detects) so the team can reproduce reader-specific issues.
- **Feature search finds more.** Searching the feature list now returns copy tray, macros, and abbreviations.
- **More file types in Open**, including common developer extensions (Kotlin, TypeScript, Go, Rust, and more), and **HEIC/HEIF images** are now supported for AI image description.
- **The About screen** now credits every GitHub contributor, including new project owner Kelly Ford and design contributor Ken Perry.

## Fixes that change the day-to-day

This release also clears out a batch of accessibility and startup problems that got in the way day to day.

- **Report a Bug actually accepts typing now.** Under NVDA, the bug-report fields were refusing keyboard input. The dialog has been rebuilt so every field is editable, and it moved to the Help menu where you would expect it. It also no longer freezes the app while it contacts the server — that work happens in the background with a timeout. The impact: reporting a problem is no longer itself a problem.
- **JAWS stops saying "splitter window" and "panel."** Those stray announcements on menu close and when the app took focus are gone, because the invisible layout container is no longer exposed to your screen reader. Quieter focus changes mean less to wade through.
- **Describe Image works again.** A small internal error was silently stopping the "Describe Image with AI" feature from running. It now completes as intended — an accessibility feature blind users rely on is dependable again.
- **Faster, quieter startup.** Screen-reader detection now runs in the background instead of stalling the first window, a crash in the preview warm-up is fixed, and the title bar no longer flashes "untitled Quill unavailable" before the app is ready. The preview pane also no longer hangs for minutes with no way to close it.
- **A reliable first run.** The first window now comes to the foreground so the trust and privacy dialog is reachable, and you can re-open the personalization wizard later if you skipped it. The wizard's startup beep and its Cancel-button focus are fixed too.
- **A tidier Personalize Quill wizard.** Two snags in the setup wizard are gone: the "Play sounds for mode changes" checkbox on step 2 now reads with its label instead of as an unlabeled control, and the profile choices on step 3 now wrap when you arrow past the last one instead of dumping you onto the Back and Next buttons.
- **The user guide opens the right way.** It now opens as a read-only page in your browser instead of as an editable Markdown document you could accidentally change — and a stray edit can no longer throw a `0x8007139f` browser error. A glossary of QUILL terms was added to the guide as well.
- **Upgrading from 0.5.0 gets a Braille Pack prompt.** The QUILL Braille Pack (braille translation, BRF/BRL export, liblouis integration) ships as an optional installer component that many 0.5.0 users will miss during the upgrade wizard. On the first launch of 0.6.0, QUILL now detects if the pack is absent and offers to run the installer again so you can add it — without re-downloading, using the copy already in your updates folder. Choose "Not Now" and the prompt goes away permanently; you can always add it later by re-running the installer and checking the Braille Pack component.
- **Skipped-update notifications work correctly again.** If you had skipped a version using "Skip this update," the notification center was silently reporting "no newer version" instead of reminding you that a skipped update was still waiting. Fixed.
- **macOS keeps your API keys.** Saving an Ask Quill API key on macOS used to crash; keys and tokens are now stored in the login Keychain, so you set them up once and on-device or cloud AI just works.
- **macOS builds install cleanly.** The notarized macOS build now signs its bundled image libraries and uses hardened-runtime entitlements, so the app installs without security warnings.

## Things that work a little differently now

- **Braille commands moved to Tools.** The top-level **Braille** menu is gone. All braille commands — status, navigation, page tools, and translation — now live under **Tools > Braille**. Everything is still there; it just has a new home alongside the other authoring tools.
- **Translation menu is now dynamic.** The flat list of UEB items has been replaced by a structured menu: a **UEB** section, a **Standard American English (Legacy)** section, and a **More Languages** submenu built from the installed pack's profiles. If you had a habit of reaching for a specific item by position, check the new structure the first time you open it.
- **No "Install Braille Pack" in the menu.** That item is gone from the Braille menu. The pack is now a selectable component during the QUILL installer — check the box there if you want it. Once installed, the Translation submenu appears automatically.
- **Report a Bug is now just above Check for Updates.** It moved from its earlier position in the Help menu to sit immediately before **Check for Updates**, which is where most people look for support-related items.
- **Two entity commands, two jobs.** The older **Encode HTML Entities** still escapes only the five markup characters (`<`, `>`, `&`, `"`, `'`). The new **Convert Non-ASCII to HTML Entities** is the one that handles accents and symbols. If you used to reach for the old command expecting it to fix accented text for Pandoc, reach for the new one instead.
- **Insert > Date and Time is a submenu now.** The flat **Date and Time** and **Calculated Date...** items have been replaced by a single **Date and Time** submenu that ships three items: **Insert Date**, **Insert Time**, and **Insert Date and Time**. The bundled `com.quill.bundled.insert-tools` Quillin owns the submenu — this is the canonical home for date/time snippets and is the model we use for migrating other built-in conveniences into Quillins.
- **Sound is opt-in.** Most earcons are off until you choose a sound pack and enable events, so nothing about your current setup gets noisier on upgrade. Turn sound on from **Preferences → Sound** and **Tools → Reading & Dictation → Sound Events...**.
- **Indentation tones default to Off.** They only play once you pick a scale, so code files stay silent unless you ask for the tones.
