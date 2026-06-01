# GOLDEN: The QUILL Path to Magical, Accessible Greatness

Status: Draft 1, authored 2026-06-01. Owner: product and engineering. Current product version: 0.1.5 Beta (target: 1.0 GA).

This is the master plan to take QUILL from an already strong, screen-reader-first editor to something genuinely delightful, dependable, and shocking in the best way. It combs the whole product: every layer, every feature, the QUILL key, navigation, selection, documentation, podcasts and tutorials, plus a full code-quality, security, and performance review.

Non-negotiable principle: everything ships accessible. No feature is "done" until it is fully operable and pleasant with NVDA, JAWS, Narrator, and VoiceOver, by keyboard alone, in high contrast, and at large font sizes.

## How to read this document

- Sections 1 to 13 are the reasoned plan, grouped by theme.
- Section 14 is the prioritized, trackable backlog. Each item has an ID, priority, size, and acceptance criteria. Treat that table as the single source of truth for execution.
- Priorities: P0 (must fix or land for 1.0), P1 (high value, near-term), P2 (valuable, post-1.0), P3 (exploratory or stretch).
- Sizes: S (under a day), M (a few days), L (about a week), XL (multi-week).

## Table of contents

1. Vision and the "magical and accessible" bar
2. Product-wide delight themes
3. The QUILL key as a flagship feature
4. Navigation deep dive (Quick Nav)
5. Selection deep dive
6. Menus and information architecture
7. Keymaps and profiles
8. Feature-by-feature enhancement pass
9. Missing features and new magic
10. Code quality review
11. Security review
12. Performance review
13. Documentation, podcasts, and tutorials
14. Prioritized backlog (tracker)
15. Suggested release sequencing

---

## 1. Vision and the "magical and accessible" bar

QUILL already does something most editors never attempt: it treats blind and low-vision writers as the primary audience, not an afterthought. The opportunity now is to make the product feel alive and considerate at every touch point.

What "magical" means here, concretely:

- Every action confirms its outcome in plain language, with consistent phrasing across screen readers.
- The product anticipates intent. It meets people where they are: a new user gets gentle scaffolding, a power user gets speed and silence.
- Nothing is a dead end. Every error explains the next step. Every surface has a way back to the editor.
- Discoverability without clutter. The right command is reachable in two or three keystrokes, and the system teaches itself as you use it.
- Trust is felt. Local-first, explicit consent, visible progress, honest extraction quality.

What "accessible, no questions asked" means here, concretely:

- Stock controls in the writing path, no custom-drawn editor surfaces.
- Focus is always predictable and recoverable. Modal close returns focus to the editor.
- Announcements never fight the screen reader. On macOS we route through VoiceOver and never self-voice.
- Contrast and keyboard-trap checks run in continuous integration, not just on demand.

---

## 2. Product-wide delight themes

These themes cut across many features and inform the backlog.

1. Outcome announcements with a shared grammar. Define a small announcement style guide (verb, object, scope, count) and apply it everywhere. Example: "Rewrote paragraph, 42 words." See backlog A11Y-1.
2. A consistent "scope" concept. Many actions operate on selection, paragraph, or document. Make that fallback model uniform and always announced. See NAV-3, SEL-2.
3. Progressive disclosure. First-run users see scaffolding and tips; power users can silence it. Tie this to feature profiles. See UX-2.
4. Earcons (optional, off by default). Subtle, distinct sounds for mode-enter, action-done, not-found. Already partially present for the QUILL key; generalize tastefully and make it opt-in. See QK-6.
5. Recoverability everywhere. Undo, backups, crash recovery, and "return to editor" are universal guarantees. Audit every dialog for an escape and a default. See A11Y-4.
6. Honesty about AI and extraction. Always show provider, model, scope, and confidence. Never a silent network call. Already strong; keep it as a hard rule. See AI-5.

---

## 3. The QUILL key as a flagship feature

Today the QUILL key is implemented as a prefix chord, `Ctrl+Shift+Grave`, followed by a second key, with a 1.5 second timeout window. It drives document actions (headings, snippets, preview, read aloud, dictation, sticky notes) and a separate Quick Nav browse mode that uses single-letter keys (H for heading, A for link, L for list, I for list item, T for table, Q for block quote, B for bookmark, P for paragraph, S for sentence, and so on).

This is good bones. The problem: the QUILL key is powerful but under-told and slightly inconsistent. It deserves to be the signature interaction that people talk about.

### 3.1 Make the QUILL key a named, prominent identity

- Give it a canonical name in all docs and UI: "the QUILL key." Establish that `Ctrl+Shift+Grave` is the QUILL key, and that it is also remappable for keyboards where Grave is awkward (for example to `Caps Lock` via an opt-in, or to a single dedicated key). See QK-1.
- Add a discoverable, always-available "QUILL key menu" overlay. When you press the QUILL key and pause, a non-modal, screen-reader-friendly list appears announcing the available follow-on keys grouped by purpose (Navigate, Insert, Format, Read, Dictate). This is a guided cheat sheet that does not block typing. See QK-2.
- QUILL key plus question mark shows the full, live QUILL key cheat sheet on demand: every follow-on key and what it does, grouped by purpose, in an accessible, screen-reader-pageable list that reflects the active keymap and profile (so it always matches the user's real bindings). This is the instant "what can I press" answer and the fastest path to discovery. See QK-9.
- Context-sensitive help is built into every mode: pressing question mark after entering a QUILL sub-mode shows only that mode's keys. For example, QUILL key plus N (Quick Nav) followed by question mark lists every navigation key (H heading, A link, L list, T table, and the rest) with live counts and current bindings; the same pattern applies to Insert, Format, Read, and Dictate sub-modes. Help is always one question mark away, wherever the user is. See QK-9, NAV-1.
- Status bar indicator. When QUILL key mode is pending or active, the status bar announces and shows a subtle state so users always know the mode is live. See QK-3.

### 3.2 Make the timeout forgiving and configurable

- The 1.5 second window is invisible and can feel like a trap. Make the timeout configurable (including "no timeout until Escape") and announce entry and expiry. See QK-4.
- Allow a sticky mode: press the QUILL key twice to "lock" browse mode until Escape, for extended navigation sessions. See QK-5.

### 3.3 Resolve the binding collisions and inconsistencies

- Today `Ctrl+Shift+Grave, N` is Sticky Note capture, while Quick Nav uses bare letters once in browse mode. Two different mental models share one prefix. Document the two modes clearly and consider unifying: a single QUILL key that opens a navigable, type-ahead "QUILL panel" with tabs for Navigate, Insert, Format, Read. See QK-2, QK-7.
- Audit all QUILL key chords for conflicts and ensure `find_keymap_conflict` is wired into the keymap editor and import flow with a spoken warning. See KEY-3.

### 3.4 Extend the QUILL key with new magic (opt-in, discoverable)

- QUILL key plus G: "Go to anything" universal jump (headings, bookmarks, links, open documents, recent files) with type-ahead. See NAV-4.
- QUILL key plus K: command palette scoped to the cursor context ("what can I do here").
- QUILL key plus number 0: jump to top, repeated for cycling key landmarks.
- QUILL key plus period: repeat last QUILL action. See QK-8.

Acceptance for the QUILL key program: a new user can discover every QUILL action without reading a manual, a power user can operate silently and fast, and the feature is documented as the headline interaction in the user guide and the marketing announcement.

---

## 4. Navigation deep dive (Quick Nav)

Quick Nav already supports 13 element types with an asynchronous prewarm cache (debounced at 250 milliseconds, large-document threshold at 20,000 characters). This is strong. Here is how to make it magical.

### 4.1 A unified Quick Nav panel

Add an opt-in "Quick Nav panel" (QUILL key plus N) that lists every navigable element type with live counts ("Headings: 12, Links: 8, Tables: 2"). Arrow into a type, then arrow through instances with a one-line context preview, and Enter to jump. This complements, not replaces, the fast single-letter browse. See NAV-1.

### 4.2 Directional and wrapping controls

- Make next or previous direction explicit and consistent for every element type (Shift reverses direction). Announce wrap events ("wrapped to top"). See NAV-2.
- Honor a configurable "wrap navigation" setting that already exists for find. Reuse it for Quick Nav.

### 4.3 Richer element awareness

- Headings: announce level and number ("Heading 2, 3 of 7"). See NAV-5.
- Links: announce link text and destination, and whether it is an image link with or without alt text (cross-reference the Link Inventory). See NAV-6.
- Tables: enter a lightweight table review mode that announces row and column position while reading cells. See NAV-7.
- Misspellings and search matches as first-class Quick Nav types. See NAV-8.

### 4.4 Semantic landmarks and "jump to anything"

- Build a single index of landmarks (headings, links, tables, code blocks, bookmarks, marks, comments or footnotes) and expose a type-ahead jumper (QUILL key plus G). See NAV-4.
- Cache invalidation correctness: ensure the prewarm cache invalidates on edits within the changed region only, and verify there is no race in cache rebuild. See NAV-9, PERF-5.

---

## 5. Selection deep dive

Selection today includes line, paragraph, block, to-end and to-start of line and document, an Emacs-style mark ring (set, jump, swap, list), and an F8 extend-selection mode.

### 5.1 Bind and announce the structural selections

- Select Line, Select Paragraph, Select Block are present but unbound by default. Provide sensible default bindings and announce the resulting scope and word count. See SEL-1.

### 5.2 Expand and shrink selection by structure

- Add "expand selection" and "shrink selection" that grow or shrink by semantic unit: word, sentence, paragraph, block, document. This is one of the most loved features in modern editors and is highly accessible because each step announces its new scope. See SEL-2.

### 5.3 Selection actions surface

- After any selection, offer a quick "do something with this" affordance (QUILL key while a selection is active) that lists scope-aware actions: rewrite, summarize, fix grammar, read aloud, copy with source, convert case, count words. See SEL-3.

### 5.4 Multi-mark and rectangular review

- Allow naming marks and reviewing a marked range non-destructively. Consider a read-only "review buffer" that shows the marked region in a stock multiline control for screen-reader paging. See SEL-4.

### 5.5 Extend mode polish

- Make extend-selection mode announce on enter and exit, show state in the status bar, and confirm the committed scope when broken. See SEL-5.

---

## 6. Menus and information architecture

The menu bar is exhaustive but the Tools menu has grown very large (roughly 800 lines of construction), and preferences are scattered across View, Tools > Customize, and Tools > Read Aloud > Backend.

### 6.1 Introduce a coherent Settings home

- Create a single Preferences surface (or a clearly grouped Settings menu) that gathers the scattered toggles. Keep deep links from context, but provide one front door. See MENU-1.

### 6.2 Split the Tools menu

- Promote Accessibility and Support to clearer positions. Consider a dedicated Accessibility top-level menu given the product's mission. See MENU-2.

### 6.3 Reduce redundancy and clarify

- Insert Link appears in both Edit and Insert. Keep one primary and make the other a clearly secondary discoverability alias, or remove duplication. See MENU-3.
- Ensure every menu item shows its current keybinding (already common) and that labels match the announcement grammar. See MENU-4.

### 6.4 Context-sensitive help that actually helps

- "What Can I Do Here?" should list commands relevant to the cursor context (inside a list, a table, a code block, a link) with their keybindings, and read well top to bottom. See HELP-1.
- The same instant help is reachable as QUILL key plus question mark anywhere, and as question mark inside any QUILL sub-mode, so users never have to leave the keyboard to learn what is possible. See QK-9.

### 6.5 Deep, tunable settings for every feature

The product should let users tune QUILL like crazy. Every feature that has timing, verbosity, behavior, or appearance should expose those knobs in a discoverable, accessible Settings surface, with sensible defaults, plain-language descriptions, per-setting reset, and search. Power users can shape QUILL precisely to their hands and ears; new users never have to touch any of it.

- Every feature gets a settings group. Each major area (QUILL key, Quick Nav, selection, Read Aloud and speech, spell check, thesaurus, find and replace, snippets, macros, document intake, watch folder, sticky notes, status bar, AI, autosave and recovery, accessibility and announcements) has its own clearly labeled group with all of its tunable options in one place. See SET-1.
- Tune timing and pacing. QUILL key timeout (including no-timeout-until-Escape), Quick Nav debounce and large-document threshold, autosave interval, announcement throttle, Read Aloud rate and pitch and per-sentence pause, and dictation pause sensitivity are all user-adjustable with live preview where possible. See SET-2, QK-4.
- Tune verbosity and announcements. A global verbosity level plus per-event overrides (for example, announce wrap events, announce counts, announce mode entry and expiry, read with spelling, punctuation level) so users decide exactly how chatty QUILL is. See SET-3, FEAT-13.
- Tune behavior. Wrap navigation on or off, sticky browse mode, confirmation prompts on or off per destructive action, default export preset, default new-document format, smart quotes and autoformat toggles, and Quick Nav element types to include or skip. See SET-4.
- Robust settings model. Group the 45-plus flat fields into nested, versioned dataclasses with schema migration, validation on load, and a corrupt-file recovery path that never loses other settings. This is the engineering backbone that makes deep tunability safe. See CQ-4, SET-5.
- Discover, search, reset, and share. The Settings surface is fully keyboard and screen-reader navigable, every setting has a plain-language description and a per-setting reset, settings are searchable by name, and the whole configuration can be exported and imported (and reset to defaults) so users can back up or share a finely tuned setup. See SET-6, SET-7.
- Pre-configuration for organizations. Document a settings schema reference so administrators can pre-tune QUILL for a lab or classroom before first run. See SET-7, DOC-7.

---

## 7. Keymaps and profiles

The keymap system has defaults, a Word pack, import and export, reset, and conflict detection. Vim and Emacs packs are referenced but not implemented.

- Ship at least two more complete keyboard packs: Vim-style and Emacs-style, plus a VS Code-style pack for developers. Each must be fully accessible and documented. See KEY-1.
- Wire conflict detection into the editor and import flow with spoken warnings and a resolution prompt. See KEY-3.
- Add a "print or export keyboard reference" that produces an accessible HTML and EPUB cheat sheet filtered by the active profile. See KEY-2, DOC-6.
- Validate keybinding syntax on save and explain errors in plain language. See KEY-4.

---

## 8. Feature-by-feature enhancement pass

This section proposes targeted delight for existing features. Each maps to a backlog ID.

- Read Aloud: add sentence highlighting sync where the screen reader allows, a "read from cursor" and "read selection" distinction, and a "read with spelling" mode for proofreading. Cache synthesized audio to avoid regenerating identical sentences. See FEAT-1, PERF-3.
- Spell check: pre-load the wordlist in a background thread at startup so the first check is instant; add "add to document dictionary" and "ignore for session" with clear announcements. See FEAT-2, PERF-1.
- Thesaurus: background pre-load, and inline synonym replacement that announces the substitution. See FEAT-3, PERF-2.
- Find and Replace: add "replace and find next" muscle memory, regex named-group preview, and a saved-recipe quick picker. See FEAT-4.
- Snippets: add tab-stops navigation with announced placeholders and a snippet picker with live preview. See FEAT-5.
- Compare documents: add a spoken summary ("12 changes: 5 additions, 4 deletions, 3 edits") and synchronized navigation announcements. See FEAT-6.
- Macros: add named macros with descriptions, a safe replay that announces each step, and export or import. See FEAT-7.
- Document Intake: make the intake report a calm, skimmable summary with confidence and a one-key path to cleanup recipes. See FEAT-8.
- Watch Folder: announce new arrivals with a non-interrupting notification and a one-key "open it." See FEAT-9.- Sticky Notes: make the vault searchable and screen-reader pageable, with quick capture confirmation. See FEAT-10.
- Status bar: ensure every cell has a crisp spoken label and a context menu, and that layout changes persist and announce. See FEAT-11.

---

## 9. Missing features and new magic

Ideas that would expand the product, in priority order within the backlog.

- Universal "Go to anything" jumper (headings, files, bookmarks, symbols). See NAV-4.
- Session restore polish: name and reopen named workspaces, announce what was restored. See FEAT-12.
- Distraction-free or focus mode tuned for screen readers (silences non-essential chatter, keeps essential confirmations). See FEAT-13.
- Reading ruler and line-focus for low-vision users (high-contrast, large, configurable). See FEAT-14.
- Inline definitions and word lookup (dictionary plus thesaurus) on a single key. See FEAT-15.
- Document health dashboard: one pane combining accessibility audit, contrast, link or alt-text inventory, and plain-language lint. See FEAT-16.
- Export presets: one-key "export to clean HTML or Word or PDF" with announced results, building on Pandoc. See FEAT-17.
- Autosave and recovery transparency: a visible, spoken "last saved" and "recovered from" state. See FEAT-18.
- External file-change watch and safe reload: detect when the open document is changed (or deleted) by another program, reload in place without moving the cursor when the buffer is clean, and offer a clear, spoken reload-or-keep-mine choice on conflict; fully configurable and quiet by default. See FEAT-19.

---

## 10. Code quality review

Overall the codebase is well-structured: clean dataclass document model, a tidy command registry, an elegant three-tier spell-check, a well-designed sandbox, and a solid stability layer (task manager, wx dispatch, safe subprocess, safe regex). No TODO or FIXME debt markers were found in core, which is excellent hygiene. The findings below are about hardening and scaling, not rescue.

### 10.1 Module size and cohesion

- `quill/ui/main_frame.py` is 18,748 lines with 200-plus methods (verified 2026-06-01). This is the single biggest maintainability risk. Extract cohesive mixins or controller modules: menu construction, QUILL key and Quick Nav, selection and marks, file and session lifecycle, status bar, AI actions. Keep behavior identical and covered by tests. See CQ-1. A verified decomposition map into 22 subsystems with line ranges is in Part II, section 16.6.
- `quill/core/read_aloud.py` (roughly 1,130 lines) should become a package with one module per TTS engine behind a common base. See CQ-2.
- `quill/io/structured.py` (roughly 450 lines, 20-plus format branches) should use a dispatch table or per-format reader modules. See CQ-3.
- `quill/core/settings.py` (45-plus fields, a very large `from_dict`) should group related settings into nested dataclasses with versioned schema migration. See CQ-4.

### 10.2 Typing and contracts

- `storage.read_json` and `write_json_atomic` use `Any`. Introduce typed helpers or `TypedDict` and generics where practical so deserialization is type-safe. See CQ-5.
- Apple Foundation Models backend uses `Any` for the SDK handle. Type it behind a Protocol so the core stays strict. See CQ-6.
- Keep strict mypy on `quill/core` and `quill/io` green in continuous integration on every pull request, scoped to those paths to avoid the whole-tree slowdown that previously froze a machine. See CQ-7, PERF-8.

### 10.3 Error handling discipline

- There are several broad `except Exception` blocks marked with noqa (in `assistant_ai.py`, `spellcheck.py`, `ai/assistant.py`, `diagnostics.py`, `updates.py`, `read_aloud.py`). Each is defensible as graceful degradation, but each should log at debug or warning with context so real bugs are not invisible. Define a small "degrade and log" helper and use it consistently. See CQ-8.
- IO reader fallback chains currently return human-readable strings instead of raising. Keep the friendly surface, but log the underlying cause so diagnostics capture it. See CQ-9.

### 10.4 Documentation in code

- Add module docstrings to `io/structured.py`, `search.py`, and other public modules that lack them, and method docstrings to the public surface of `Document`, `CommandRegistry`, and the IO readers and writers. See CQ-10.

### 10.5 Tests to add

- Spell-check tier fallback (enchant to wordlist to stub) and the background pre-load path. See CQ-11.
- Undo and redo behavior and persistence edge cases. See CQ-12.
- IO format coverage beyond text: at least Markdown, HTML, JSON, CSV, DOCX (via the bridge), and PDF quality scoring with small fixtures. See CQ-13.
- Path-safety tests that confirm writes cannot escape the app data directory. See CQ-14, SEC-2.
- Thread-safety test for the thesaurus cache and any other lazily loaded global. See CQ-15.
- A characterization test harness around `main_frame` before the extraction in CQ-1, so refactors are provably behavior-preserving. See CQ-16.

### 10.6 Concurrency

- Note: a verified audit (Part II) confirms the thesaurus, spell-check, and watch-folder caches already use locks, so there is no race there. The remaining concurrency work is documenting the invariants and the storage atomic-write behavior on Windows. See CQ-15, CQ-17, CQ-18.
- Document thread-safety invariants for all module-level caches in a short engineering note. See CQ-17.

---

## 11. Security review

Threat model note: most user data files live under the per-user app data directory, which is trusted in the single-user desktop model. The findings below harden against tampered config, untrusted document inputs, and supply-chain risk.

### 11.1 Subprocess and executable path validation (highest priority)

- TTS and speech engines, and external tools, can be configured with executable paths read from settings. If the settings file is tampered with, an arbitrary executable could be launched. Validate configured executable paths at load time: confirm existence, and prefer an allowlist of known tool names resolved via `shutil.which` or the bundled path. See SEC-1.
- OCR passes a language code to Tesseract via a command flag. Whitelist language codes to prevent flag or argument injection. See SEC-3.
- Continue routing all subprocess calls through `stability/safe_subprocess.py`, and document a `cwd` safety requirement so callers cannot point it outside expected directories. See SEC-4.

### 11.2 Path traversal hardening

- Add a single helper that asserts a resolved path stays within an expected base directory, and use it in `storage.write_json_atomic` and other persistence call sites. Add tests. See SEC-2, CQ-14.

### 11.3 Network and downloads

- Verify TLS certificates explicitly on all outbound requests (AI endpoints, update checks, DECtalk or model downloads). See SEC-5.
- Verify a checksum or signature for any downloaded binary or model before use (DECtalk runtime, GGUF models). See SEC-6.

### 11.4 Secrets

- Current key storage (Windows Credential Manager first, DPAPI-encrypted file fallback; macOS Keychain) is sound. Document the shared-account limitation and add a "forget key" command that clears both stores and announces success. See SEC-7.

### 11.5 Plugins

- The plugin system is a v1.0 skeleton with no sandbox, signing, or capability model. Do not enable third-party plugin loading in a shipping build until a capability model, signature verification, and a trust prompt exist. Gate it behind a clearly experimental, off-by-default flag. See SEC-8.

### 11.6 Python sandbox

- The user Python transform runs in an isolated subprocess with an import allowlist and blocked builtins. Add a wall-clock and memory limit to prevent denial of service from infinite loops, and announce when a transform is terminated for exceeding limits. See SEC-9.

---

## 12. Performance review

The product is responsive for typical workloads. These changes remove first-use stalls and keep the UI thread free.

- Pre-load the 370,000-word spell-check list on a background thread at startup so the first spell check does not stall. See PERF-1.
- Pre-load the thesaurus index in the background; first lookup currently pays the full load cost. See PERF-2.
- Cache synthesized TTS audio so identical sentences are not re-rendered, and avoid round-tripping every sentence through temp files where possible. See PERF-3.
- Replace OCR busy-wait polling with a proper wait or `communicate` to remove the 100 millisecond granularity and reduce churn. See PERF-4.
- Confirm the Quick Nav prewarm cache invalidates only the changed region and never blocks typing; add a perf test for large documents. See PERF-5, NAV-9.
- Move non-critical persistence (settings, palette usage, recent files) off the UI thread or batch writes to avoid synchronous disk stalls. See PERF-6.
- Cache markup-kind inference and heading or block scans per document revision instead of re-scanning on each navigation. See PERF-7.
- Keep the strict type check fast and scoped in continuous integration, and document the safe local command (`mypy quill\core quill\io`) so contributors never run an unscoped, machine-freezing scan. See PERF-8, CQ-7.
- Add a small performance budget suite (startup time, first spell check, first thesaurus lookup, Quick Nav prewarm on a large file) to catch regressions. See PERF-9.

---

## 13. Documentation, podcasts, and tutorials

Documentation greatness is a first-class theme of this plan, equal in weight to the product and engineering work. QUILL's mission demands documentation that is itself a model of accessibility, clarity, and completeness: every feature explained, every keystroke listed, every artifact available in Markdown, HTML, and EPUB, and the whole docs folder organized so that a reader (or a contributor, or a screen-reader user) can always find the right page fast. The bar is not "adequate docs"; it is documentation people point to as exemplary.

Documentation is already strong: a 3,900-plus line PRD, a comprehensive user guide, engineering docs, an accessibility conformance report and VPAT, a localization plan, and multi-format output (Markdown, HTML, EPUB) enforced by a docs-artifact gate. The gaps are learning content, a few reference pieces, and consolidation of the docs folder itself.

### 13.1 Documentation completeness

- Add a dedicated QUILL key primer to the user guide and a standalone quick-reference, positioned as the signature feature. See DOC-1.
- Add a navigation and selection guide that teaches Quick Nav and structural selection with worked examples. See DOC-2.
- Add a developer quickstart for contributors (environment, run from source, test, lint, type-check, build). See DOC-3.
- Generate an API or module reference from docstrings (for example with a lightweight static generator) and publish it in the multi-format pipeline. See DOC-4.
- Keep the docs-artifact gate green: every changed Markdown file regenerates its HTML and EPUB. This is already enforced; document it for contributors. See DOC-5.
- Produce an accessible, profile-filtered keyboard reference in HTML and EPUB. See DOC-6, KEY-2.

### 13.2 Podcast transcripts (launch-ready)

Create a short podcast series with full, accessible transcripts ready for distribution at launch. Transcripts are the primary artifact; audio is optional and secondary. Each transcript must be clean, well-structured Markdown with headings and speaker labels, and follow the plain-language lint already in the repo. Proposed episodes:

1. "Meet QUILL: a text editor that puts blind and low-vision writers first." See POD-1.
2. "The QUILL key: one key to navigate, format, and read." See POD-2.
3. "Reading and reviewing with confidence: Read Aloud, intake quality, and trust." See POD-3.
4. "Writing with on-device AI you control." See POD-4.
5. "Make any document accessible: GLOW, audits, and cleanup." See POD-5.

Each episode delivers a Markdown transcript plus an optional short script for narration. Reuse the existing plain-language lint and docs-artifact pipeline so transcripts ship as HTML and EPUB too.

### 13.3 Tutorials

Create task-focused tutorials, text-first and screen-reader-validated, with optional audio walkthrough transcripts:

1. First session: open, edit, save, and recover. See TUT-1.
2. Navigate any document with the QUILL key and Quick Nav. See TUT-2.
3. Select and transform text by structure. See TUT-3.
4. Find and replace, including regex, safely. See TUT-4.
5. Set up and use AI assistance privately. See TUT-5.
6. Convert and clean up messy documents with Pandoc and cleanup recipes. See TUT-6.
7. Customize keymaps and profiles to fit your hands. See TUT-7.

Each tutorial includes numbered steps, the exact keystrokes, and the expected spoken confirmation, so a screen-reader user can follow along and verify success at each step.

### 13.4 Review and consolidate the docs folder

Treat the `docs/` folder as a product surface that deserves the same care as the code. Review it end to end, consolidate overlap, fix accessibility, and raise every page to a consistent high-quality bar. This is the work that makes documentation greatness real rather than aspirational.

- Full docs audit and inventory. Catalog every file under [docs/](docs/) (PRD, user guide, engineering docs, accessibility ACR and VPAT, localization, announcements, and the generated HTML and EPUB), note status (current, stub, stale, duplicate), and record the result so nothing is missed. See DOC-14.
- Consolidate and structure. Establish a clear top-level docs index (a single entry page that links to user docs, learning content, reference, and engineering docs), merge overlapping or stub pages, remove or clearly mark stale content, and ensure a predictable folder structure so readers and contributors always know where a topic lives. See DOC-15.
- Raise quality to a consistent bar. Give every page a clear purpose statement, consistent heading structure, working internal links, and a last-reviewed date. Expand the skeletal engineering docs (architecture, module contracts, data layout, runtime model, diagnostics runbook, quality gates) beyond stubs. See DOC-12, DOC-16.
- Documentation accessibility pass. Apply the project's own markdown accessibility rules across all docs source: replace emoji with text labels, remove em-dashes, ensure accessible tables and meaningful link text, and add alt text or text alternatives for any diagrams. Regenerate artifacts and keep the docs-artifact gate green. See DOC-11.
- Make consolidation durable. Add a docs style guide and a contributor checklist (purpose, structure, accessibility, regenerate artifacts) so the folder stays consolidated and high quality over time. See DOC-17.

---

## 14. Prioritized backlog (tracker)

This table is the execution source of truth. Update Status as work progresses. Status values: Todo, In progress, Blocked, Done.

### P0: must land for 1.0

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| SEC-1 | Validate configured executable paths at load | Security | M | Done | Tampered settings cannot launch arbitrary executables; unknown tool paths are rejected and announced; tests cover the reject path. |
| SEC-2 | Path-escape guard for persistence writes | Security | S | Todo | A shared helper blocks writes outside the app data base; used in storage writers; tests prove traversal is blocked. |
| SEC-3 | Whitelist OCR language codes | Security | S | Todo | Only known language codes reach Tesseract; invalid codes are rejected with a clear message; test included. |
| SEC-5 | Explicit TLS verification on all network calls | Security | S | Todo | AI, update, and download requests verify certificates; a test or audit confirms no unverified context is used. |
| SEC-6 | Verify checksums for downloaded binaries and models | Security | M | Todo | DECtalk runtime and GGUF downloads are checksum-verified before use; failure aborts with a clear message. |
| SEC-8 | Gate plugin loading behind off-by-default experimental flag | Security | S | Todo | No third-party plugin loads in a default build; flag is documented as experimental. |
| SEC-9 | Resource limits for the Python sandbox | Security | M | Todo | A wall-clock and memory limit terminate runaway transforms; termination is announced; test included. |
| CQ-7 | Scoped strict mypy in CI on every pull request | Code quality | S | Todo | CI runs mypy on quill/core and quill/io; failures block merge; local command documented. |
| PERF-8 | Document and enforce scoped type-check command | Performance | S | Todo | Contributor docs specify the scoped command; no unscoped whole-tree scan is recommended anywhere. |
| A11Y-1 | Announcement style guide and audit | Accessibility | M | Todo | A written grammar exists; top 50 announcements conform; a test verifies key phrases. |
| A11Y-4 | Dialog escape and default audit | Accessibility | M | Todo | Every dialog has an Escape path and an explicit default; focus returns to the editor on close; tests or a contract check cover representative dialogs. |
| QK-1 | Name and remappable QUILL key | QUILL key | S | Todo | Docs and UI call it the QUILL key; it is remappable; default remains Ctrl+Shift+Grave. |
| QK-3 | QUILL key mode status indicator | QUILL key | S | Todo | Pending and active states announce and show in the status bar. |
| QK-4 | Configurable, announced QUILL key timeout | QUILL key | S | Todo | Timeout is configurable including no-timeout; entry and expiry announce. |
| KEY-3 | Wire keymap conflict detection into UI and import | Keymaps | M | Todo | Conflicts are detected on bind and import, announced, and resolvable. |
| DOC-1 | QUILL key primer and quick reference | Docs | M | Todo | User guide section plus standalone reference; ships as HTML and EPUB via the gate. |
| DOC-5 | Document the docs-artifact gate for contributors | Docs | S | Todo | Contributor docs explain regenerating HTML and EPUB; gate stays green. |

### P1: high value, near-term

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| CQ-1 | Decompose main_frame into cohesive modules | Code quality | XL | Todo | main_frame is split into controllers or mixins with no behavior change; characterization tests pass before and after. |
| CQ-16 | Characterization tests around main_frame | Code quality | L | Todo | Behavior is pinned by tests prior to CQ-1; coverage includes menus, QUILL key, selection, file lifecycle. |
| CQ-8 | Degrade-and-log helper for broad excepts | Code quality | S | Todo | A shared helper logs context; broad excepts in core use it; no silent failures remain in the listed files. |
| CQ-11 | Spell-check fallback and preload tests | Code quality | S | Todo | Tier fallback and background preload are covered by tests. |
| CQ-13 | IO format coverage tests | Code quality | M | Todo | Markdown, HTML, JSON, CSV, DOCX bridge, and PDF scoring have fixture-based tests. |
| CQ-15 | Document cache locking and add concurrency tests | Code quality | S | Todo | Thesaurus/spell-check/watch-folder locks are confirmed present; add a concurrency test that exercises them and a short note of the invariants. |
| PERF-1 | Background preload of spell-check wordlist | Performance | S | Todo | First spell check does not stall; preload runs off the UI thread; perf test added. |
| PERF-2 | Background preload of thesaurus | Performance | S | Todo | First lookup does not stall; perf test added. |
| PERF-3 | Cache synthesized TTS audio | Performance | M | Todo | Identical sentences are not re-rendered; measurable latency reduction; test or benchmark added. |
| PERF-9 | Performance budget suite | Performance | M | Todo | Startup, first spell check, first thesaurus, and Quick Nav prewarm have budgets enforced in CI. |
| NAV-1 | Unified Quick Nav panel | Navigation | L | Todo | Panel lists element types with counts and previews; fully keyboard and screen-reader operable. |
| NAV-2 | Consistent directional and wrapping Quick Nav | Navigation | M | Todo | Every element type supports next and previous with announced wrap. |
| NAV-4 | Go to anything jumper | Navigation | L | Todo | One index of landmarks with type-ahead jump; bound to the QUILL key plus G. |
| NAV-5 | Heading level and position announcements | Navigation | S | Todo | Heading navigation announces level and ordinal. |
| SEL-1 | Bind and announce structural selections | Selection | S | Todo | Select line, paragraph, block have defaults and announce scope and word count. |
| SEL-2 | Expand and shrink selection by structure | Selection | M | Todo | Selection grows and shrinks by semantic unit with announced scope at each step. |
| SEL-3 | Scope-aware selection actions surface | Selection | M | Todo | With a selection active, the QUILL key offers scope-aware actions. |
| QK-2 | QUILL key guided panel or overlay | QUILL key | L | Todo | A non-modal, screen-reader-friendly guide lists follow-on keys grouped by purpose. |
| QK-9 | QUILL key plus question mark cheat sheet and per-mode help | QUILL key | M | Todo | QUILL key plus question mark shows the full, live cheat sheet of every follow-on key grouped by purpose, reflecting the active keymap and profile; pressing question mark inside any sub-mode (for example QUILL key plus N then question mark) lists only that mode's keys with current bindings and live counts; the surface is fully keyboard and screen-reader navigable; a test verifies the keys shown match the active bindings. |
| QK-5 | Sticky QUILL browse mode | QUILL key | S | Todo | Double-press locks browse mode until Escape; state announces. |
| KEY-1 | Vim, Emacs, and VS Code keyboard packs | Keymaps | L | Todo | Three complete, documented, accessible packs are selectable. |
| MENU-1 | Unified Preferences home | Menus | M | Todo | Scattered toggles are gathered into one front door; deep links preserved. |
| SET-1 | Per-feature settings groups | Settings | M | Todo | Every major feature has a clearly labeled settings group containing all of its tunable options; groups are keyboard and screen-reader navigable. |
| SET-2 | Tunable timing and pacing | Settings | M | Todo | QUILL key timeout, Quick Nav debounce and threshold, autosave interval, announcement throttle, Read Aloud rate, pitch, and pause, and dictation sensitivity are user-adjustable with live preview where possible. |
| SET-3 | Tunable verbosity and announcements | Settings | M | Todo | A global verbosity level plus per-event overrides (wrap, counts, mode entry and expiry, spelling, punctuation level) let users decide exactly how chatty QUILL is. |
| SET-4 | Tunable behavior toggles | Settings | M | Todo | Wrap navigation, sticky browse, per-action confirmations, default export preset and new-document format, autoformat toggles, and Quick Nav element inclusion are all configurable. |
| SET-5 | Robust settings model with migration | Settings | L | Todo | Flat fields are grouped into nested, versioned dataclasses with validation on load and corrupt-file recovery that preserves other settings; round-trip and migration tests pass. (Pairs with CQ-4.) |
| SET-6 | Searchable settings with per-setting reset and descriptions | Settings | M | Todo | Settings are searchable by name; each has a plain-language description and a per-setting reset; the surface is fully accessible. |
| SET-7 | Export, import, and pre-configure settings | Settings | S | Todo | The full configuration can be exported, imported, and reset to defaults; a documented schema lets administrators pre-tune before first run. (Pairs with DOC-7.) |
| MENU-2 | Split the Tools menu and elevate Accessibility | Menus | M | Todo | Tools is smaller; Accessibility is easy to find; labels match announcement grammar. |
| HELP-1 | Context-aware What Can I Do Here | Help | M | Todo | The help lists commands relevant to the cursor context with keybindings, readable top to bottom. |
| FEAT-2 | Spell-check usability polish | Features | S | Todo | Add to document dictionary and ignore for session, with announcements. |
| FEAT-19 | External file-change watch and safe reload | Features | M | Todo | QUILL watches the open document for external modification (and deletion). When the file changes on disk and the buffer is unmodified, it reloads in place without moving the cursor or scroll position and announces "Reloaded from disk." When the buffer has unsaved edits (a conflict), it never overwrites silently: it announces the change and offers reload, keep-mine, or compare, with a clear spoken prompt. Behavior is configurable (auto-reload-when-clean on or off, prompt-on-conflict, watch on or off, debounce interval) in a Settings group, defaults are safe and quiet, and the watcher runs off the UI thread reusing the existing watch-folder and stability patterns. Cursor, selection, and scroll are preserved across reload; tests cover clean reload, conflict prompt, deletion, and cursor preservation. |
| FEAT-16 | Document health dashboard | Features | L | Todo | One pane combines audit, contrast, link or alt-text inventory, and plain-language lint. |
| AI-5 | Reaffirm no-silent-network and scope honesty in code and tests | AI | S | Todo | A test asserts no network call without consent; provider, model, and scope are always shown. |
| DOC-2 | Navigation and selection guide | Docs | M | Todo | Worked examples for Quick Nav and structural selection ship in all formats. |
| DOC-14 | Full docs folder audit and inventory | Docs | S | Todo | Every file under docs is cataloged with status (current, stub, stale, duplicate); the inventory is recorded so nothing is missed. |
| DOC-15 | Consolidate and structure the docs folder | Docs | M | Todo | A single top-level docs index links user docs, learning content, reference, and engineering docs; overlapping and stub pages are merged; stale content is removed or marked; folder structure is predictable. |
| DOC-16 | Raise every docs page to a consistent quality bar | Docs | M | Todo | Each page has a purpose statement, consistent headings, working internal links, and a last-reviewed date; skeletal engineering docs are expanded. |
| DOC-17 | Docs style guide and contributor checklist | Docs | S | Todo | A style guide and a checklist (purpose, structure, accessibility, regenerate artifacts) keep the docs folder consolidated and high quality over time. |
| DOC-6 | Profile-filtered keyboard reference | Docs | M | Todo | Accessible HTML and EPUB cheat sheet filtered by active profile. |
| POD-1 | Podcast transcript: Meet QUILL | Docs | S | Todo | Clean Markdown transcript passes plain-language lint and ships as HTML and EPUB. |
| POD-2 | Podcast transcript: The QUILL key | Docs | S | Todo | As above, focused on the QUILL key. |
| TUT-1 | Tutorial: first session | Docs | S | Todo | Numbered steps with keystrokes and expected spoken confirmations. |
| TUT-2 | Tutorial: navigate with the QUILL key | Docs | S | Todo | As above, navigation focused. |

### P2: valuable, post-1.0

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| CQ-2 | Read Aloud engine package split | Code quality | L | Todo | One module per engine behind a base; behavior unchanged; tests pass. |
| CQ-3 | IO structured dispatch table | Code quality | M | Todo | Format routing uses a table or per-format modules; complexity reduced; tests pass. |
| CQ-4 | Settings nested schema and migration | Code quality | L | Todo | Settings grouped into nested dataclasses with versioned migration; round-trip tests pass. |
| CQ-5 | Typed storage helpers | Code quality | M | Todo | read_json and write helpers are typed; core stays strict. |
| CQ-6 | Type the Foundation Models SDK handle | Code quality | S | Todo | A Protocol replaces Any; mypy strict passes. |
| CQ-9 | Log underlying causes in IO fallbacks | Code quality | S | Todo | Friendly messages remain; root causes are logged for diagnostics. |
| CQ-10 | Add missing module and method docstrings | Code quality | M | Todo | Listed public modules and methods are documented. |
| CQ-12 | Undo and redo tests | Code quality | S | Todo | Edge cases and persistence are covered. |
| CQ-14 | Path-safety tests | Code quality | S | Todo | Writes cannot escape app data; tests included. (Pairs with SEC-2.) |
| CQ-17 | Thread-safety invariants note | Code quality | S | Todo | A short engineering note documents cache locking rules. |
| PERF-4 | Replace OCR busy-wait | Performance | S | Todo | OCR uses a proper wait; no fixed-interval polling. |
| PERF-5 | Quick Nav cache invalidation correctness | Performance | M | Todo | Only changed regions invalidate; large-document perf test passes. |
| PERF-6 | Off-thread or batched persistence | Performance | M | Todo | Settings, palette, and recent writes do not stall the UI thread. |
| PERF-7 | Cache markup and structure scans per revision | Performance | M | Todo | Navigation reuses cached scans; measurable improvement on large files. |
| NAV-3 | Uniform scope fallback model | Navigation | S | Todo | Selection, paragraph, document fallback is consistent and announced across actions. |
| NAV-6 | Link navigation announces text, destination, alt state | Navigation | S | Todo | Link browse announces details and alt-text presence. |
| NAV-7 | Table review mode | Navigation | M | Todo | Cell reading announces row and column position. |
| NAV-8 | Misspellings and matches as Quick Nav types | Navigation | S | Todo | Both are navigable element types with announcements. |
| NAV-9 | Quick Nav prewarm race audit | Navigation | S | Todo | No race in cache rebuild; covered by a test. (Pairs with PERF-5.) |
| SEL-4 | Named marks and review buffer | Selection | M | Todo | Marks can be named; a read-only review buffer pages a marked range. |
| SEL-5 | Extend mode polish | Selection | S | Todo | Enter and exit announce; status shows state; committed scope confirms. |
| QK-6 | Optional generalized earcons | QUILL key | S | Todo | Distinct, opt-in sounds for mode enter, action done, not found. |
| QK-7 | Unify QUILL key mental models | QUILL key | M | Todo | The two modes are clearly documented or unified into one panel; no ambiguity. |
| QK-8 | Repeat last QUILL action | QUILL key | S | Todo | A key repeats the last QUILL action with announcement. |
| KEY-2 | Exportable keyboard reference | Keymaps | S | Todo | Reference exports as accessible HTML and EPUB. (Pairs with DOC-6.) |
| KEY-4 | Validate keybinding syntax on save | Keymaps | S | Todo | Invalid bindings are rejected with a plain-language explanation. |
| MENU-3 | Resolve menu redundancy | Menus | S | Todo | Insert Link duplication is rationalized. |
| MENU-4 | Labels match announcement grammar | Menus | S | Todo | Menu labels and announcements are consistent. |
| FEAT-1 | Read Aloud read-from-cursor, read-selection, spell mode | Features | M | Todo | Three modes work and announce; audio caching applies. (Pairs with PERF-3.) |
| FEAT-3 | Thesaurus inline replacement | Features | S | Todo | Synonym replacement announces the substitution. |
| FEAT-4 | Find and Replace ergonomics | Features | S | Todo | Replace-and-find-next, named-group preview, recipe quick picker. |
| FEAT-5 | Snippet tab-stops and picker | Features | M | Todo | Tab-stops announce placeholders; picker previews. |
| FEAT-6 | Compare spoken summary | Features | S | Todo | A spoken change summary and synchronized navigation announcements. |
| FEAT-7 | Named macros with safe replay | Features | M | Todo | Named, described macros replay with per-step announcements; export and import. |
| FEAT-8 | Calm Document Intake summary | Features | S | Todo | Skimmable intake with one-key path to cleanup. |
| FEAT-9 | Watch Folder arrival announcements | Features | S | Todo | Non-interrupting notification with one-key open. |
| FEAT-10 | Searchable Sticky Notes vault | Features | M | Todo | Vault is searchable and pageable; capture confirms. |
| FEAT-11 | Status bar label and persistence polish | Features | S | Todo | Every cell announces; layout persists and announces. |
| SEC-4 | Document cwd safety for safe_subprocess | Security | S | Todo | Callers cannot point cwd outside expected directories; documented and tested. |
| SEC-7 | Forget key command and shared-account note | Security | S | Todo | A command clears both secret stores and announces; limitation documented. |
| AI-1 | Streaming response UI | AI | M | Todo | Replies stream incrementally with accessible, announced updates. |
| POD-3 | Podcast transcript: Reading and reviewing | Docs | S | Todo | Transcript passes lint; ships in all formats. |
| POD-4 | Podcast transcript: On-device AI | Docs | S | Todo | As above. |
| POD-5 | Podcast transcript: Make documents accessible | Docs | S | Todo | As above. |
| TUT-3 | Tutorial: select and transform by structure | Docs | S | Todo | Numbered steps with keystrokes and confirmations. |
| TUT-4 | Tutorial: find and replace safely | Docs | S | Todo | As above. |
| TUT-5 | Tutorial: private AI setup | Docs | S | Todo | As above. |
| TUT-6 | Tutorial: convert and clean up documents | Docs | S | Todo | As above. |
| TUT-7 | Tutorial: customize keymaps and profiles | Docs | S | Todo | As above. |
| DOC-3 | Developer quickstart | Docs | S | Todo | Environment, run, test, lint, type-check, build steps documented. |
| DOC-4 | Generated API or module reference | Docs | M | Todo | Reference generated from docstrings and published in all formats. |

### P3: exploratory or stretch

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| QK-6b | Earcon sound design pass | QUILL key | M | Todo | A small, tasteful sound set is designed and user-tested with screen-reader users. |
| FEAT-12 | Named workspace restore polish | Features | M | Todo | Named workspaces reopen and announce what was restored. |
| FEAT-13 | Screen-reader-tuned focus mode | Features | M | Todo | Non-essential chatter is silenced; essential confirmations remain. |
| FEAT-14 | Reading ruler and line focus | Features | M | Todo | Configurable, high-contrast, large line focus for low vision. |
| FEAT-15 | One-key inline definition and lookup | Features | S | Todo | Dictionary and thesaurus lookup on a single key with announcement. |
| FEAT-17 | One-key export presets | Features | M | Todo | Clean HTML, Word, and PDF export with announced results. |
| FEAT-18 | Save and recovery transparency | Features | S | Todo | Visible and spoken last-saved and recovered-from state. |
| NAV-10 | Symbol navigation for source files | Navigation | M | Todo | Functions, classes, and headings index for code; type-ahead jump. |
| AI-2 | Multi-modal image understanding | AI | L | Todo | Optional, opt-in image analysis with consent and announced results. |
| LINUX-1 | Linux platform layer exploration | Platform | XL | Todo | A spike assesses an accessible Linux path; decision recorded. |
| LINUX-2 | Accessible Linux platform layer to product quality | Platform | XL | Todo | Following the LINUX-1 spike, a platform layer (screen-reader bridge, secret store, shell integration) ships at the same accessibility and stability bar as Windows and macOS, gated on the same checks. |
| ECO-1 | Plugin capability, signing, and marketplace model | Ecosystem | XL | Todo | A documented capability and signing model lets vetted third-party plugins load safely off the experimental flag (builds on SEC-8), with a review process; no unsigned plugin runs by default. |
| L10N-1 | Full localization of UI and documentation | Localization | XL | Todo | The UI and the core documentation set are fully translated and accessibility-reviewed for the committed launch languages, with a process to keep translations current. |
| COLLAB-1 | Asynchronous review and sharing (scoped) | Features | L | Todo | A local-first, accessible async review and comment exchange (export, annotate, merge) is delivered; real-time multi-user editing remains explicitly out of scope with the reason recorded. |

---

## 15. Suggested release sequencing

1. Harden and gate (P0 security, accessibility, and continuous integration items). These protect users and unblock everything else. This is the 1.0 quality bar.
2. Land the QUILL key flagship (QK-1 through QK-5, NAV-1, NAV-4, SEL-1 through SEL-3) plus the primer and first tutorials. This is the story that makes QUILL memorable.
3. Decompose main_frame safely (CQ-16 then CQ-1) to make all future work faster and lower risk.
4. Performance polish (PERF-1 through PERF-3 and PERF-9) so first use feels instant.
5. Documentation and launch content (remaining podcasts and tutorials, keyboard reference, developer quickstart) so launch lands with a complete learning surface.
6. Post-1.0 delight and expansion (P2 and P3) guided by beta feedback.

Definition of greatness for this plan: when a first-time blind writer can open QUILL, discover the QUILL key, navigate a messy document by structure, fix it, read it back, and save it, all by keyboard, with every step confirmed clearly, and a returning power user can do the same in silence at speed, then QUILL is golden.

---

## Part II: Verified line-by-line audit (2026-06-01)

This part records a structured, tool-assisted audit that read across the entire source tree (148 Python files, 37,559 lines), all documentation, the test suite (118 test files), and the build and release scripts. Findings below are concrete and carry file-and-line citations so they can be acted on directly. Each new actionable item is added to the backlog in section 16.10 with a stable ID, and the P0 correctness bugs are also called out at the top because several are latent crashes.

Tooling run for this audit:

- ruff on the `quill` package: 113 findings (83 line-too-long, 10 undefined-name, 7 unsorted-imports, 5 unused-import, 3 quoted-annotation, 2 zip-without-strict, 2 unused-variable, 1 redefinition). On `tests` and `scripts`: 36 findings.
- mypy scoped to `quill/core` and `quill/io` (the strict zone): 44 errors across 14 files. Important correction to earlier notes: the strict zone is not currently clean; only the two AI files touched in a previous session were verified green. The scoped command remains `mypy quill\core quill\io` to avoid the whole-tree scan that previously exhausted memory.

### 16.1 Confirmed correctness bugs (latent crashes), highest priority

These are real defects found by reading the code, several confirmed by ruff undefined-name analysis. They should be fixed before 1.0.

1. Corrupted method `_show_bw_onboarding` in [quill/ui/main_frame.py](quill/ui/main_frame.py#L19426) (lines 19426 to 19470). The method body contains copy-pasted "Insert Link" dialog code and references undefined names `selected_text` (line 19442), `dialog` (line 19463), and `profiles` (line 19470), plus assigns `display_text` and `url` that are never used. If this onboarding path is reached it raises `NameError`. The intended behavior is to confirm the BITS Whisperer rollout and then present a profile choice. This is a P0 crash. See BUG-1.
2. Four bare `wx.` calls that should be `self._wx.` in [quill/ui/main_frame.py](quill/ui/main_frame.py#L16983) at lines 16983, 17015, 17022, and 17042 (`wx.GetSingleChoice` and `wx.GetTextFromUser` in the heading-style prompts). Module-level `wx` is not imported; it is only stored as `self._wx` (assigned around line 683). These four call sites raise `NameError` at runtime when the heading-style flow executes. This is a P0 crash on a real user path. See BUG-2.
3. Undefined type annotation `VoiceOption` in [quill/ui/main_frame.py](quill/ui/main_frame.py#L12503) at lines 12503 and 12532. The symbol is imported as `ReadAloudVoiceOption` (around line 240) but the annotations use the bare name. With `from __future__ import annotations` this does not crash at call time, but it breaks `typing.get_type_hints` and static analysis. Fix by using the imported alias. See BUG-3.
4. Redefinition of `URLError` in [quill/ui/main_frame.py](quill/ui/main_frame.py#L339): imported first from `urllib.error` (line 15) and again from `quill.core.updates` (line 339). The second import shadows the first. Pick one source. See BUG-4.
5. Unchecked llama.cpp response shape in [quill/core/ai/llama_cpp_backend.py](quill/core/ai/llama_cpp_backend.py#L113) (lines 113 to 117): `out["choices"][0]["message"]["content"]` will raise `KeyError` or `IndexError` on a malformed or version-mismatched response. Add validation and a friendly error. See BUG-5.
6. XML element handling bug in [quill/io/structured.py](quill/io/structured.py#L614) (lines 614 and 615): a `list[str]` is assigned where an `Element` is expected and then passed to `str.join`, which mypy flags as an assignment and arg-type error. This is a real type-level defect in the DOCX path. See BUG-6.
7. Potential infinite loop in [quill/core/ai/assistant.py](quill/core/ai/assistant.py#L196) chunk splitting if `max_chars <= 0` is ever passed; add a guard. See BUG-7.

### 16.2 Security findings (verified)

Highest priority first. Most user files live under the trusted per-user app data directory, so the focus is tampered configuration, untrusted document inputs, and supply chain.

1. XML entity expansion (billion laughs) in document parsing. [quill/io/structured.py](quill/io/structured.py#L416) uses `ET.fromstring` for XML (line 416), DOCX `word/document.xml` (around line 408), and PPTX slide XML; [quill/io/pages.py](quill/io/pages.py#L107) parses PPTX XML similarly. None disable entity expansion, so a crafted file can cause memory and CPU exhaustion. Fix by switching to `defusedxml` or a hardened parser for all untrusted XML. P0 hardening. See SEC-10.
2. Decompression bombs in ZIP-based formats (DOCX, XLSX, ODT, PPTX) in [quill/io/structured.py](quill/io/structured.py#L604) (around lines 604, 683, 717). The archives are read without checking total uncompressed size. Add a cumulative size limit before reading entries. See SEC-11.
3. Subprocess executable paths sourced from settings. [quill/core/external_tools.py](quill/core/external_tools.py#L132) (around line 132) expands and runs configured executable paths (for example the DECtalk executable and other engines) without validating they live in a trusted location. If `settings.json` is tampered, this is arbitrary code execution. Validate against an allowlist or bundled or `shutil.which`-resolved path. This pairs with the earlier SEC-1. See SEC-1.
4. PATH hijacking via tool discovery in [quill/core/external_tools.py](quill/core/external_tools.py#L102) (around lines 102 to 115): `shutil.which` trusts the process PATH. Document the risk and prefer bundled tool paths where available. See SEC-12.
5. Update download without binary checksum or signature verification in [quill/core/updates.py](quill/core/updates.py#L249) (around line 249). The manifest signature is verified, but the downloaded asset itself is not checksum-verified before use. Verify a hash from the signed manifest against the downloaded bytes. This pairs with SEC-6. See SEC-6.
6. Incomplete secret redaction in diagnostics. [quill/core/diagnostics.py](quill/core/diagnostics.py#L20) (around lines 20 to 29) redacts `Authorization: Bearer` style tokens but misses patterns like `token:`, `password:`, and `NAME_KEY=` environment assignments. Broaden the redaction patterns so diagnostic bundles never leak partial secrets. See SEC-13.
7. Python sandbox environment and resource limits. [quill/core/python_sandbox.py](quill/core/python_sandbox.py#L143) inherits `PATH` into the subprocess (around line 143) and passes the user code as a base64 environment variable (around line 145), which can appear in a process list on shared systems; there is also no wall-clock or memory cap beyond the timeout. Add memory and CPU limits and avoid leaking the payload via the environment where possible. This refines SEC-9. See SEC-9, SEC-14.
8. `run_subprocess_safely` does not validate `cwd` or the executable in [quill/stability/safe_subprocess.py](quill/stability/safe_subprocess.py#L11) (around lines 11 to 26), and only catches `TimeoutExpired`, not `OSError` or `FileNotFoundError`. Add validation and wrap the missing exception. This refines SEC-4. See SEC-4, SEC-15.
9. Credential and Keychain input validation. [quill/platform/windows/credential_manager.py](quill/platform/windows/credential_manager.py#L73) does not validate `target_name` (around lines 73 to 99), and [quill/platform/macos/keychain.py](quill/platform/macos/keychain.py#L30) does not check the `security` subprocess return code in `set_secret` (around lines 30 to 50). Validate names against a safe pattern and check return codes. See SEC-16.
10. Shell integration registry command in [quill/platform/windows/shell_integration.py](quill/platform/windows/shell_integration.py#L35) is safe today because it derives from `launcher_command()`, but it is not escaped; document that it must never accept user input, or escape it if that changes. See SEC-17.

### 16.3 Correctness and robustness (non-crashing) findings

1. Windows atomic write is not guaranteed. [quill/core/storage.py](quill/core/storage.py#L16) uses temp file plus `replace` (around line 16). On Windows this can be a two-step operation under contention. Confirm `os.replace` semantics and, where needed, add retry-on-`PermissionError` so a concurrent reader cannot cause data loss. See CQ-19.
2. Version comparison ignores pre-release suffixes in [quill/core/updates.py](quill/core/updates.py#L136) (around line 136): `1.2.0-rc1` parses as `1.2.0`, so a release candidate sorts equal to the stable. Decide and document the intended ordering. See CQ-20.
3. Snippet placeholder regex does not handle nested braces in [quill/core/snippets.py](quill/core/snippets.py#L90) (around lines 90 to 120). Document the limitation or support nesting. See FEAT-5.
4. TOML parse has no guard in [quill/core/compliance.py](quill/core/compliance.py#L142) (around lines 142 to 160): a corrupted `pyproject.toml` aborts the dependency audit. Wrap and report. See CQ-21.
5. Credential empty-blob path in [quill/platform/windows/credential_manager.py](quill/platform/windows/credential_manager.py#L68) returns an empty secret indistinguishable from absent; log and document. See CQ-22.

### 16.4 Typing gaps in the strict zone (the 44 mypy errors)

The strict zone (`quill/core` and `quill/io`) currently reports 44 errors in 14 files. Representative clusters, all to be driven to zero and then kept green in continuous integration (see CQ-7):

- [quill/core/ipc.py](quill/core/ipc.py#L75): six errors from a `handle: object` annotation that is then used as a file object, plus `fcntl` attributes that are POSIX-only. The cross-platform branch on `os.name` is logically sound; annotate the handle as `IO[bytes]` or `Any` and guard the `fcntl` import for type-checkers. See TYPE-1.
- [quill/core/bw_speech.py](quill/core/bw_speech.py#L169): an `Any` returned where `float` is declared (line 169), missing parameter annotations (lines 223, 255), and the optional `faster_whisper` import. See TYPE-2.
- [quill/core/read_aloud.py](quill/core/read_aloud.py#L298): the `kokoro.KPipeline` attribute is not visible to mypy (line 298); fix the ignore code. See TYPE-3.
- [quill/core/dictation.py](quill/core/dictation.py#L10): `None` assigned to a `Callable`-typed name (line 10), and `recognize_whisper` and `recognize_vosk` on an untyped recognizer (lines 71, 78). See TYPE-4.
- [quill/io/pages.py](quill/io/pages.py#L73): missing return and parameter annotations (lines 73, 78, 91), untyped third-party `keynote_parser`, and an `Any` returned as `str` (line 238). See TYPE-5.
- [quill/io/structured.py](quill/io/structured.py#L173): untyped `openpyxl` import (line 173), a missing annotation (line 249), and the Element bug from 16.1 item 6 (lines 614, 615). See TYPE-6, BUG-6.
- [quill/core/ai/llama_cpp_backend.py](quill/core/ai/llama_cpp_backend.py#L65): missing annotations (lines 65, 71), a `None`-typed attribute later assigned a `Llama` (line 82), and an `Any` returned as `str` (line 118). See TYPE-7.
- [quill/core/ai/assistant.py](quill/core/ai/assistant.py#L130): missing annotations (lines 130, 200). See TYPE-8.

Where third-party stubs are missing (`openpyxl`, `faster_whisper`, `keynote_parser`, `kokoro`, `llama_cpp`), either install the available stub packages (for example `types-openpyxl`) or add precise per-import ignores with the correct error codes, and add Protocols for the SDK handles so the strict zone stays honest.

### 16.5 Performance findings (verified)

1. Spell-check wordlist loads synchronously (about 370,000 words) in [quill/core/spellcheck.py](quill/core/spellcheck.py#L100) (around lines 100 to 115), under the backend lock, stalling the first check. Background preload at startup. Pairs with PERF-1. See PERF-1.
2. Thesaurus index loads synchronously (a large data file) in [quill/core/thesaurus.py](quill/core/thesaurus.py#L52) (around lines 52 to 60) on first lookup. Background preload. Pairs with PERF-2. See PERF-2.
3. Read Aloud accumulates uncompressed audio arrays in memory in [quill/core/read_aloud.py](quill/core/read_aloud.py#L295) (around lines 295 to 325); stream to file for long documents, and cache identical sentences. Pairs with PERF-3. See PERF-3, PERF-10.
4. Spreadsheet reading loads entire worksheets into memory in [quill/io/structured.py](quill/io/structured.py#L193) (around lines 193 to 199); cap rows or stream. See PERF-11.
5. DOCX and PPTX load whole XML payloads and build full in-memory documents in [quill/io/structured.py](quill/io/structured.py#L604) (around lines 604 and 637); consider streaming and run these off the UI thread. See PERF-12.
6. PDF extraction materializes all pages in [quill/io/pdf.py](quill/io/pdf.py#L58) (around line 58); page-stream for very large PDFs. See PERF-13.
7. File search scans whole documents with no chunking in [quill/core/file_search.py](quill/core/file_search.py#L48) (around lines 48 to 70); stream large corpora. See PERF-14.

Concurrency note (correction): the spell-check wordlist cache, the enchant dictionary, the thesaurus index, and the watch-folder seen-set all already use `threading.Lock`. There is no missing lock there. The remaining work is documenting these invariants (CQ-17) and the Windows atomic-write behavior (CQ-19).

### 16.6 main_frame.py decomposition map (verified seams)

The 18,748-line [quill/ui/main_frame.py](quill/ui/main_frame.py) divides cleanly into roughly 22 subsystems. This map is the basis for CQ-1 (extract behind characterization tests, CQ-16):

- Initialization and setup: lines 678 to 860.
- Command registry and keybinding: lines 971 to 4975.
- Menu building and identifier management: lines 2358 to 4640 (the single largest block).
- Event binding and frame lifecycle: lines 4927 to 6663.
- QUILL key mode: lines 5162 to 5287.
- Browse and navigation (Quick Nav, ARIA regions): lines 5358 to 5817.
- Tab and document management: lines 5016 to 5120 and 5781 to 5860.
- Text editor operations: lines 5849 to 6201.
- Context menus: lines 6206 to 6650.
- Status bar: lines 7252 to 7675.
- Dialogs and modal presentation: lines 7675 to 7702.
- File input/output and sessions: lines 7067 to 7141 and 8075 to 8824.
- Speech and Read Aloud: lines 12400 to 13460.
- Update checking: lines 14963 to 15100.
- Find and replace: lines 15655 to 16000.
- Link insertion: lines 16080 to 16210.
- Heading styles: lines 16950 to 17060 (contains BUG-2).
- List manager: lines 17259 to 17700.
- Intellisense and autocomplete: lines 18079 to 18240.
- Onboarding and first run: lines 14369 to 19700 (contains BUG-1).

### 16.7 IO contract and coverage findings

- Readers that follow `read(path) -> Document` and raise on error are compliant (text and structured confirmed). Several formats are read-only by design (PDF, Pages) and lack `write`; only Pages implements `outline`. If the product promises `outline` for structured formats, add it for DOCX, PPTX, and XLSX. See IO-1.
- Format test coverage is thin: only text, PDF, OCR, pandoc, and structured have any tests, and pandoc and structured are minimal. There are no fixtures exercising real conversions. The "100-plus formats" claim rests almost entirely on pandoc and is essentially untested end to end. See CQ-13 and the test plan in 16.9.

### 16.8 Documentation findings (verified)

- Missing entirely: API or module reference, developer quickstart, plugin developer guide, a static (offline) keyboard reference, a configuration schema reference, a troubleshooting guide, and any podcast transcripts or tutorial or video scripts. See DOC-1 through DOC-6, DOC-7, DOC-8, and the POD and TUT items.
- The accessibility conformance report at [docs/accessibility/acr-vpat.md](docs/accessibility/acr-vpat.md) is a template with placeholder evidence. It must be either filled in with a real 0.1.5 assessment or clearly labeled as not yet assessed. See DOC-9.
- The PRD at [docs/QUILL-PRD.md](docs/QUILL-PRD.md) mixes 1.0 specification with 0.1.5 reality; its header should state plainly that it specifies 1.0 and that 0.1.5 implements the subset marked in the roadmap mapping. See DOC-10.
- Documentation accessibility: the PRD uses emoji (check marks, warning and cross symbols, and others) and em-dashes throughout. Per the project's own markdown accessibility rules, replace emoji with text labels such as the words pass, warning, and error, and replace em-dashes. This applies to the source markdown so the generated HTML and EPUB inherit the fix. See DOC-11.
- The engineering docs (architecture, module-contracts, data-layout, runtime-model, diagnostics-runbook, quality-gates) are useful but skeletal (most under 50 lines). Expand them alongside the API reference. See DOC-12.
- User guide gaps: concrete AI setup examples (for example connecting to a local Ollama endpoint and an error matrix for 401 versus 403 versus 500), spell-check dictionary workflow, watch-folder walkthrough, and a troubleshooting section (Quick Nav key conflicts, garbled PDF extraction, autosave disk pressure). See DOC-13.

### 16.9 Test strategy findings (verified)

- Inventory: 118 test files. Core has the most coverage; the UI monolith, the IO format matrix, integration, performance, and accessibility content depth are the weak spots.
- The 18,748-line UI has only a handful of behavior tests. Before decomposition (CQ-1), add a characterization suite (CQ-16) covering tab lifecycle, undo and redo isolation, autosave and recovery, session restore, Quick Nav, find and replace, spell-check as you type, sticky notes, and macros.
- Add policy and attack-surface tests for the Python sandbox (allowed versus blocked modules, escape attempts, resource limits), spell-check tier fallback, Read Aloud backend fallback, and IO format smoke tests with real fixtures. See CQ-11, CQ-13, CQ-23, CQ-24.
- Performance tests are smoke-level only; add the budget suite (PERF-9).
- Scripts: the release orchestrator [scripts/release_readiness.py](scripts/release_readiness.py) runs ruff, pip-audit strict, pytest, docs build, and corpus verification, but there is no dependency lockfile and no timeouts on long commands; the Windows build pins an embeddable Python by a hardcoded hash that requires a code change to rotate. See CQ-25, CQ-26.

### 16.10 New backlog items from the verified audit

These extend the section 14 tracker. Priorities follow the same scheme. The confirmed latent crashes are P0.

#### P0 correctness bugs (new)

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| BUG-1 | Repair corrupted `_show_bw_onboarding` | UI correctness | S | Done | Method no longer references undefined names; the BITS Whisperer onboarding presents the intended profile choice; a test exercises the path so it cannot regress. |
| BUG-2 | Fix four bare `wx.` calls in heading-style prompts | UI correctness | S | Done | Lines 16983, 17015, 17022, 17042 use `self._wx`; a test invokes the heading-style flow without `NameError`. |
| BUG-3 | Fix undefined `VoiceOption` annotations | UI correctness | S | Done | Lines 12503 and 12532 use the imported alias; ruff reports no F821 for these. |
| BUG-4 | Resolve `URLError` redefinition | UI correctness | S | Done | A single import source for `URLError`; ruff F811 cleared. |
| BUG-5 | Validate llama.cpp response shape | AI correctness | S | Done | Malformed responses produce a friendly error, not `KeyError` or `IndexError`; test included. |
| BUG-6 | Fix DOCX Element handling in structured reader | IO correctness | S | Done | Lines 614 and 615 type-check and behave correctly on a fixture DOCX; mypy clean for that path. |
| BUG-7 | Guard chunk splitting against non-positive size | AI correctness | S | Done | `max_chars <= 0` cannot cause an infinite loop; test included. |

#### P0 and P1 security (new and refined)

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| SEC-10 | Harden all untrusted XML parsing | Security | M | Done | DOCX, XLSX, ODT, PPTX, and generic XML use a parser with entity expansion disabled; a billion-laughs fixture is rejected quickly; test included. |
| SEC-11 | Decompression-bomb limits for ZIP formats | Security | S | Done | A cumulative uncompressed-size cap aborts oversized archives with a clear message; test included. |
| SEC-12 | Document and reduce PATH-hijack exposure for tool discovery | Security | S | Todo | Bundled tool paths are preferred; the residual risk is documented. |
| SEC-13 | Broaden diagnostics secret redaction | Security | S | Done | Redaction covers token, password, and NAME_KEY assignment patterns; test asserts no secret leaks. |
| SEC-14 | Python sandbox memory and CPU limits | Security | M | Todo | Runaway transforms are terminated by memory and wall-clock limits; payload is not exposed via the environment where avoidable; test included. (Extends SEC-9.) |
| SEC-15 | safe_subprocess validates cwd and wraps OSError | Security | S | Todo | `cwd` and executable are validated; `OSError` and `FileNotFoundError` are caught and surfaced clearly; test included. (Extends SEC-4.) |
| SEC-16 | Validate credential and keychain inputs | Security | S | Todo | `target_name`, account, and service match a safe pattern; macOS `set_secret` checks the return code; tests included. |
| SEC-17 | Document or escape shell-integration command | Security | S | Todo | The registry command path is documented as internal-only or escaped if user input is ever accepted. |

#### P1 and P2 quality, typing, performance, IO, docs, tests (new)

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| CQ-18 | Resolve ruff debt across quill, tests, scripts | Code quality | S | Todo | The 113 plus 36 ruff findings are fixed or explicitly justified; ruff is clean in continuous integration. |
| CQ-19 | Verify and harden atomic write on Windows | Code quality | S | Todo | Writes use `os.replace` with retry on transient `PermissionError`; a test simulates contention. |
| CQ-20 | Define version pre-release ordering | Code quality | S | Todo | Release-candidate ordering is intentional and documented; test covers it. |
| CQ-21 | Guard TOML parsing in compliance | Code quality | S | Todo | A corrupted `pyproject.toml` produces a clear error, not a silent abort. |
| CQ-22 | Document credential empty-blob behavior | Code quality | S | Todo | Empty-secret versus absent-credential is logged and documented. |
| CQ-23 | Python sandbox policy and attack-surface tests | Code quality | M | Todo | Tests cover allowed versus blocked modules, escape attempts, and resource limits. |
| CQ-24 | Read Aloud backend fallback tests | Code quality | M | Todo | Each backend and the fallback order is tested with stubs. |
| CQ-25 | Add dependency lockfile and CI timeouts | Build | M | Todo | Dependencies are pinned for release runs; long commands have timeouts. |
| CQ-26 | Make the embeddable Python hash configurable | Build | S | Todo | The Windows build reads the expected hash from config, not a code constant. |
| TYPE-1 | Type `ipc.py` handle and guard fcntl | Typing | S | Todo | mypy clean for `ipc.py` in the strict zone. |
| TYPE-2 | Annotate `bw_speech.py` | Typing | S | Todo | mypy clean for `bw_speech.py`. |
| TYPE-3 | Fix `read_aloud.py` kokoro ignore | Typing | S | Todo | mypy clean for the kokoro import. |
| TYPE-4 | Annotate `dictation.py` recognizer | Typing | S | Todo | mypy clean for `dictation.py`. |
| TYPE-5 | Annotate `io/pages.py` | Typing | S | Todo | mypy clean for `pages.py`. |
| TYPE-6 | Annotate `io/structured.py` and add openpyxl stubs | Typing | S | Todo | mypy clean for `structured.py` (with BUG-6). |
| TYPE-7 | Type the llama.cpp backend handle | Typing | S | Todo | mypy clean for `llama_cpp_backend.py`. |
| TYPE-8 | Annotate `ai/assistant.py` | Typing | S | Todo | mypy clean for `ai/assistant.py`. |
| PERF-10 | Stream and cache Read Aloud audio | Performance | M | Todo | Long-document synthesis does not spike memory; identical sentences are cached. |
| PERF-11 | Cap or stream spreadsheet reads | Performance | S | Todo | Large sheets do not exhaust memory; a row cap or streaming applies. |
| PERF-12 | Stream DOCX and PPTX off the UI thread | Performance | M | Todo | Large office files do not block the UI thread. |
| PERF-13 | Page-stream large PDFs | Performance | S | Todo | Very large PDFs extract without materializing all pages at once. |
| PERF-14 | Chunk file search over large corpora | Performance | S | Todo | Search streams large inputs without quadratic blowups. |
| IO-1 | Add outline support for structured formats | IO | M | Todo | DOCX, PPTX, and XLSX provide an outline, or the contract is amended and documented. |
| DOC-7 | Configuration schema reference | Docs | M | Todo | Settings, keymap, and data schemas are documented for pre-configuration. |
| DOC-8 | Troubleshooting guide | Docs | S | Todo | Common issues (key conflicts, PDF extraction, AI connection, autosave) are documented with fixes. |
| DOC-9 | Replace or label the ACR template | Docs | M | Todo | The conformance report reflects a real 0.1.5 assessment or is clearly marked not yet assessed. |
| DOC-10 | Clarify 1.0 versus 0.1.5 in the PRD header | Docs | S | Todo | The PRD states its 1.0 scope and the 0.1.5 implemented subset. |
| DOC-11 | Make the PRD and docs accessible | Docs | M | Todo | Emoji are replaced with text labels and em-dashes removed across docs source; artifacts regenerated and the docs gate passes. |
| DOC-12 | Expand engineering docs | Docs | M | Todo | Architecture, contracts, data layout, runtime model, diagnostics, and quality gates are filled out beyond stubs. |
| DOC-13 | Fill user-guide gaps | Docs | M | Todo | AI setup examples, spell-check dictionary workflow, watch-folder walkthrough, and troubleshooting are added. |

### 16.11 Summary of verified counts

- Confirmed latent-crash bugs: 7 (BUG-1 through BUG-7), of which two (BUG-1, BUG-2) are on real user paths in the UI.
- Security findings: 10 verified items spanning untrusted-input parsing, supply chain, secret handling, and subprocess and credential validation.
- Strict-zone typing errors: 44 across 14 files (TYPE-1 through TYPE-8 cover the clusters).
- Lint findings: 113 in the package and 36 in tests and scripts (CQ-18).
- Performance hotspots: 7 verified (PERF-1, PERF-2, PERF-3, PERF-10 through PERF-14).
- Documentation gaps: 7 missing artifacts plus accessibility and version-clarity fixes (DOC-1 through DOC-13).
- Test gaps: the UI monolith, the IO format matrix, sandbox policy, and a performance budget are the highest-value additions.

Revised sequencing note: the new P0 correctness bugs (BUG-1 and BUG-2 especially) and the untrusted-input hardening (SEC-10, SEC-11) should be folded into step 1 of the section 15 sequencing, because they are small, concrete, and protect users immediately.

---

## Part III: Quality gates and the AI and agent program

This part does two bold things. First, it defines a ladder of automated quality gates so that every change (whether written by a person or by an AI coding assistant such as Copilot) is held to a high, consistent, machine-checked bar before it can merge. Second, it reimagines QUILL's own AI and agent features so they become a signature strength: local-first, fully accessible, consented, reversible, and genuinely useful to a blind or low-vision writer.

The two are connected. Strong gates are what let a team move fast with AI assistance without drifting in quality. They turn "the AI wrote it" from a risk into an advantage, because nothing reaches users that has not passed the same objective checks.

### 17. Quality gates for an AI-assisted workflow

The repository already has the raw materials: ruff, mypy, pytest, a docs-artifact gate, pip-audit in the release script, accessibility and performance test folders, and a release readiness orchestrator. The work is to assemble these into an explicit, enforced gate ladder, close the holes the audit found, and make the gates fast enough to run on every change.

#### 17.1 The gate ladder

Three tiers, each stricter than the last:

- Pre-commit (local, seconds). Format and lint the changed files, run quick syntax and undefined-name checks, and block commits that fail. This catches the class of bug the audit found (bare `wx.` calls, undefined names, unsorted imports) before they ever leave a developer's machine. See GATE-1.
- Pull request (continuous integration, minutes). The full objective bar that must be green to merge: lint, scoped strict typing, the test suite with a coverage floor, the accessibility checks, the docs-artifact gate, and the security scans. See GATE-2 through GATE-9.
- Release (pre-tag, thorough). The existing release readiness orchestrator, hardened: pinned dependencies, command timeouts, corpus verification, performance budgets, and provenance and software bill of materials generation. See GATE-10, CQ-25, CQ-26.

#### 17.2 The specific gates to enforce

- Lint gate. Ruff must be clean (or explicitly justified) on the package, tests, and scripts. Closes the 113 plus 36 findings and keeps them closed. See GATE-2, CQ-18.
- Typing gate. Strict mypy on `quill/core` and `quill/io`, always scoped to those paths (never the whole tree, which previously froze a machine), must report zero errors. Drives the 44 strict-zone errors to zero and holds the line. See GATE-3, CQ-7.
- Banned-pattern gate. A small, fast check that fails the build on known footguns: a bare `wx.` reference in `main_frame` (must be `self._wx`), undefined names, duplicate imports, `print` left in library code, `ET.fromstring` on untrusted XML (must use the hardened parser), and `except Exception` without a logged cause. This is the gate that would have caught BUG-1, BUG-2, BUG-4, and SEC-10 automatically. See GATE-4.
- Test and coverage gate. The full pytest suite (unit, integration, accessibility, performance smoke) must pass, with a coverage floor that ratchets upward over time and a hard floor for `quill/core` and `quill/io`. New code may not lower coverage. See GATE-5, CQ-13.
- Characterization gate for the UI monolith. Before and during the `main_frame` decomposition, a characterization suite must pass so refactors are provably behavior-preserving. See GATE-6, CQ-16, CQ-1.
- Accessibility gate. Keyboard-trap and contrast checks, plus the announcement-grammar and focus-order assertions, run on every pull request, not on demand. No UI change merges if it regresses screen-reader operability. See GATE-7, A11Y items.
- Security gate. pip-audit (strict) for dependency vulnerabilities, a static security scan (for example bandit or semgrep) for subprocess, XML, and path-traversal patterns, a check that all untrusted XML uses the hardened parser, and a "no plaintext secret" scan of diagnostics output. See GATE-8, SEC-10 through SEC-17.
- No-silent-network gate. An automated test asserts that no AI or network code path makes an outbound call without explicit consent, and that provider, model, and scope are always surfaced. This makes the product's core trust promise machine-enforced, not just a convention. See GATE-9, AI-5.
- Docs-artifact and accessibility gate. Every changed Markdown file regenerates its HTML and EPUB, and the docs accessibility rules (no emoji, no em-dashes, accessible tables, meaningful links) are linted. See GATE-2 (docs job), DOC-11, DOC-5.
- Performance budget gate. Startup time, first spell-check, first thesaurus lookup, large-document Quick Nav, and Read Aloud start must stay within published budgets; a regression fails the build. See GATE-10, PERF-9.
- Module-size budget gate. A soft, ratcheting budget on the largest files (starting with `main_frame`) that prevents new growth and rewards extraction, so the monolith shrinks monotonically. See GATE-11, CQ-1.

#### 17.3 Make AI coding assistants productive and safe in this repo

The goal is that an AI assistant (Copilot or an agent) can contribute high-quality, accessible, secure code with minimal back-and-forth, because the repository tells it exactly how, and the gates catch anything that slips.

- Strengthen the repository guidance. Expand the existing `.github/copilot-instructions.md` and add an `AGENTS.md` so any assistant has a crisp, current description of the architecture, the strict-typing zone, the scoped mypy command, the accessibility non-negotiables, the no-silent-network rule, the PowerShell and commit conventions, and the definition of done. See GATE-12.
- Ship a machine-readable definition of done. A short checklist (accessible, typed in the strict zone, tested, lint-clean, no silent network, docs regenerated) that both humans and agents follow, mirrored by the gates so the checklist is actually enforced. See GATE-13.
- Encode the footguns the audit found. Document the bare `wx.` versus `self._wx` rule, the hardened-XML rule, the scoped-mypy rule, and the path-safety helper directly in the guidance, with examples, so assistants do not reintroduce them. See GATE-12.
- Add CODEOWNERS and required reviews for the highest-risk areas (security, the sandbox, the AI provider boundary, the platform secret stores) so sensitive changes always get human eyes even when AI-authored. See GATE-14.
- Provide test-first scaffolding. Templates and fixtures (IO sample files, an accessibility test harness, a sandbox policy harness) so an assistant can write the test alongside the change and the coverage gate is easy to satisfy. See GATE-5, CQ-23, CQ-13.
- Keep the guidance honest over time. A periodic check that the instructions match reality (version, commands, structure), so assistants are never working from stale facts. See GATE-12.

### 18. Make QUILL's own AI and agents amazing

QUILL already has a thoughtful AI layer: a provider and model boundary, an enable toggle with an honest status badge, an Assistant Hub, Ask QUILL chat, model and connection management, a Writing Assistant, a Prompt Studio, an Agent Center scaffold, selection actions, style training, and a Speech submenu, all gated behind explicit consent with no silent network calls. The bold move is to turn this solid foundation into the most accessible AI writing experience anywhere: local-first, fully spoken, always reversible, and genuinely agentic for the tasks that matter most to this audience.

Guiding principles for all AI and agent work, non-negotiable:

- Local-first and private by default. On-device models (llama.cpp and Apple Foundation Models) are first-class; any cloud use is explicit, per-action, and clearly labeled. See AI-5.
- Consent, visibility, and reversibility. Every AI action shows provider, model, and scope, streams visible progress, and produces a result the user can review and undo. No AI edit is ever silent or irreversible. See AI-5, AI-7.
- Accessible to the core. Every AI surface is fully keyboard and screen-reader operable, with results that read well top to bottom and diffs that can be reviewed line by line by ear. See A11Y items.

#### 18.1 Make the assistant feel magical

- Streaming, announced responses. Replies stream incrementally with accessible, throttled announcements so the user hears progress without being flooded. See AI-1.
- Preview-and-apply diffs that are reviewable by ear. Any AI edit is presented as a structured, navigable diff (added, removed, changed), readable line by line with the screen reader, with apply, apply-partially, and reject, and a single undo. This is the feature that makes AI editing trustworthy for a blind writer. See AI-7.
- Context-aware actions. The actions offered adapt to the cursor or selection context (inside a list, a table, a heading, a code block) and to the document type, so the right help is always one key away, including from the QUILL key. See AI-8, HELP-1.
- A real prompt library. Save, name, organize, and share prompts and recipes, with a quick picker and live preview, building on Prompt Studio. See AI-9.
- Style that is truly yours. Strengthen style training so the assistant can match a user's voice, explain why it made a change, and stay consistent across a document. See AI-10.

#### 18.2 A genuine, accessible agent program

Move the Agent Center from scaffold to a small set of reliable, consented, reversible agents that each complete a real multi-step task and narrate every step. An agent never acts without consent, announces each step as it works, and produces a reviewable, undoable result.

- The Accessibility agent (the headline). Tell QUILL "make this document accessible" and it runs a consented, announced, reversible plan: audit structure, fix heading levels, add or improve alt text (with the user confirming each suggestion), tighten link text, apply plain-language improvements, then re-run the audit and report what changed. Every step is a reviewable diff and a single undo. This is the agent that embodies the product's mission. See AGENT-1.
- The Cleanup agent. Turn a messy imported document (bad OCR, broken structure, inconsistent formatting) into clean, well-structured text through a sequence of cleanup recipes, each announced and reversible. See AGENT-2, FEAT-8.
- The Review agent. Produce a spoken, skimmable review of a document (structure, readability, accessibility, consistency) with one-key jumps to each issue, building on the document health dashboard. See AGENT-3, FEAT-16.
- A safe, local agent loop. The agent runtime plans, takes one consented step at a time, can call only a small allowlist of in-app tools (navigate, edit-with-diff, run a sandboxed transform, run an audit), never the network without explicit consent, with a hard step cap and a guard against loops, and full step-by-step announcement. This reuses the existing sandbox and stability layers. See AGENT-4, SEC-9.
- Grounded answers over the user's own content. Optional, local retrieval over open documents and the sticky-notes vault so "ask QUILL" can answer from what the user is actually working on, always citing where an answer came from, never sending content anywhere without consent. See AI-11.

#### 18.3 Trust, safety, and evaluation for AI

- Machine-enforced no-silent-network, as a gate, not just a convention. See GATE-9, AI-5.
- An evaluation harness for AI quality. A small, repeatable set of tasks (accessibility fixes, cleanup, summarization) with expected-quality checks, so AI and agent changes can be measured and regressions caught before release. See AI-12.
- Redaction and offline integrity. Diagnostics never capture document content or secrets (SEC-13), and every AI feature degrades gracefully and announces clearly when a model is unavailable or a key is missing. See CQ-8, AI-6.

#### 18.4 Review of the cloud and local providers (OpenAI, OpenRouter, Gemini, Azure, Ollama, Claude)

A focused review of the provider boundary in `quill/core/assistant_ai.py`, the backends in `quill/core/ai/`, and how the UI wires them found one structural defect and several smaller correctness and enhancement gaps. The provider configuration surface is genuinely strong; the gap is that it is not yet connected to generation.

- The headline defect: configured providers never generate. `assistant_ai.py` fully implements provider selection, secure key storage (Credential Manager with a DPAPI fallback), HTTPS-only policy for cloud endpoints, model discovery, and connection verification for all six providers. But the `Assistant` is always constructed with no backend (`Assistant()` in `main_frame.py`), so generation always runs through `make_default_backend()`, which is Apple Foundation Models on macOS or local llama.cpp elsewhere. Selecting OpenAI, OpenRouter, Gemini, Azure OpenAI, Ollama, or Claude lets a user save a key, list models, and pass verification, yet every actual rewrite, summarize, chat, or agent step still runs on the local model. This is the single most important fix in the AI area: wire a provider-aware chat backend so the selected provider is the one that responds. See AI-13.
- Provider-specific correctness, needed once chat is wired:
  - OpenAI, OpenRouter, custom: standard `POST /v1/chat/completions`; OpenRouter benefits from optional `HTTP-Referer` and `X-Title` attribution headers.
  - Claude: messages API at `POST /v1/messages` with `x-api-key`, `anthropic-version`, and a required `max_tokens`; the model-listing headers are already correct.
  - Gemini: `POST /v1beta/models/{model}:generateContent` with `x-goog-api-key`; the request and response shape differ from the OpenAI schema and need their own adapter.
  - Azure OpenAI: chat targets a deployment, not a model name, at `/openai/deployments/{deployment}/chat/completions?api-version=...`; the connection UI should make the deployment-versus-model distinction explicit. See AI-15.
  - Ollama (local): generation should use `POST /api/chat`; model listing already uses `/api/tags` correctly.
- Streaming. No provider streams today; responses are blocking. Streaming with throttled, accessible announcements (AI-1) should be implemented once per provider in the shared backend so progress is heard, not awaited in silence. See AI-14.
- Tests and trust. There are no contract tests that exercise each provider's request and response shape. Add recorded or mocked per-provider contract tests (no live network in CI) so a provider change cannot silently break generation, and extend the existing, well-designed error taxonomy (auth, forbidden, rate-limited, warming-up, timeout) from the listing path to the chat path so users get the same cause-specific, screen-reader-friendly messages. See AI-16, AI-17.
- What is already good and should be preserved: the HTTPS-only policy with a careful local-loopback and private-network exception (a sound anti-SSRF posture), the Credential Manager plus DPAPI key handling with an honest "could not unlock on this device" status, the retry-with-backoff on transient categories, and the duplicate-tolerant model-name extraction across `models`, `data`, and `items` payload shapes.

#### 18.5 On the GitHub Copilot SDK: a measured recommendation

The user is right to be cautious. The recommendation is to not ship or integrate the GitHub Copilot SDK as a flagship or default path for 1.0, and instead to treat it as an optional, clearly labeled provider behind the same AIBackend boundary, considered after 1.0. The reasoning:

- It would add real value: strong models, and for developer-leaning users a familiar, already-paid-for entitlement. That value is genuine and worth capturing eventually.
- But it conflicts with QUILL's core promises if made central. Copilot requires a paid subscription and an interactive GitHub OAuth device-flow sign-in, which is friction at odds with the local-first, bring-your-own-key, no-silent-network design and with the screen-reader-first simplicity of the connection flow. Its terms and telemetry posture are also a poorer fit for a privacy-first writing tool than a user's own API key.
- The pragmatic path: because the provider boundary is OpenAI-compatible, most of Copilot's value is already reachable through the existing custom OpenAI-compatible provider and through OpenAI, Claude, Gemini, and OpenRouter directly. So the marginal benefit of a dedicated Copilot integration is modest, while the cost (a bespoke auth flow, subscription gating, accessibility review of the sign-in, and ongoing terms compliance) is real. Add it later, gated and optional, only if beta users ask for it, and never as a default. See AI-18.

#### 18.6 New backlog items for gates and AI

These extend the section 14 tracker.

##### Quality gates (mostly P0 and P1)

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| GATE-1 | Pre-commit hooks for format, lint, and quick checks | Gates | S | Todo | Commits that fail format, lint, or undefined-name checks on changed files are blocked locally; documented for contributors. |
| GATE-2 | Pull-request CI pipeline | Gates | M | Todo | A required pipeline runs lint, scoped typing, tests, accessibility, docs-artifact, and security jobs; merge is blocked unless green. |
| GATE-3 | Strict typing gate (scoped) | Gates | S | Todo | mypy on `quill/core` and `quill/io` reports zero errors and is required for merge; the whole-tree scan is never used. |
| GATE-4 | Banned-pattern gate | Gates | S | Todo | The build fails on bare `wx.` in main_frame, undefined names, duplicate imports, unhardened `ET.fromstring`, and `except Exception` without a logged cause; tests cover the checker. |
| GATE-5 | Test and coverage floor | Gates | M | Todo | The full suite must pass; coverage has a hard floor for core and io and may not decrease on a change; floor ratchets upward. |
| GATE-6 | Characterization gate for main_frame | Gates | M | Todo | A characterization suite is required green before and during decomposition so refactors are behavior-preserving. |
| GATE-7 | Accessibility gate on every PR | Gates | M | Todo | Keyboard-trap, contrast, focus-order, and announcement-grammar checks run on every pull request and block regressions. |
| GATE-8 | Security scan gate | Gates | M | Todo | pip-audit strict, a static security scan, a hardened-XML check, and a no-plaintext-secret diagnostics check are required for merge. |
| GATE-9 | No-silent-network gate | Gates | S | Todo | An automated test asserts no outbound call without consent and that provider, model, and scope are always shown; required for merge. |
| GATE-10 | Performance budget gate | Gates | M | Todo | Startup, first spell-check, first thesaurus lookup, large-document Quick Nav, and Read Aloud start stay within published budgets; regressions fail the build. |
| GATE-11 | Module-size budget gate | Gates | S | Todo | A ratcheting size budget prevents new growth in the largest files and decreases as extraction proceeds. |
| GATE-12 | Strengthen AI assistant repository guidance | Gates | S | Todo | copilot-instructions and a new AGENTS.md describe architecture, strict zone, scoped mypy, accessibility, no-silent-network, the audit footguns, and the definition of done; a check keeps them current. |
| GATE-13 | Machine-checked definition of done | Gates | S | Todo | A short done checklist (accessible, typed, tested, lint-clean, no silent network, docs regenerated) is documented and mirrored by the gates. |
| GATE-14 | CODEOWNERS and required review for high-risk areas | Gates | S | Todo | Security, sandbox, AI boundary, and secret-store changes require a human review even when AI-authored. |

##### AI and agent features

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| AI-6 | Graceful AI degradation and clear status | AI | S | Todo | Every AI feature announces clearly when a model is unavailable or a key is missing, and never blocks the editor. |
| AI-7 | Preview-and-apply AI diffs reviewable by ear | AI | L | Todo | AI edits present a navigable added/removed/changed diff, readable line by line, with apply, partial apply, reject, and a single undo. |
| AI-8 | Context-aware AI actions | AI | M | Todo | Offered actions adapt to cursor or selection context and document type and are reachable from the QUILL key. |
| AI-9 | Prompt library and recipes | AI | M | Todo | Prompts and recipes can be saved, named, organized, shared, and picked with live preview. |
| AI-10 | Style training and explainable edits | AI | M | Todo | The assistant can match a user's voice and explain why it made each change, consistently across a document. |
| AI-11 | Local grounded answers over user content | AI | L | Todo | Optional local retrieval over open documents and the sticky-notes vault answers questions with citations and no network without consent. |
| AI-12 | AI evaluation harness | AI | M | Todo | A repeatable task set with quality checks measures AI and agent output and catches regressions before release. |
| AGENT-1 | Accessibility agent (make this document accessible) | AI | L | Todo | A consented, announced, reversible plan audits and fixes structure, alt text, link text, and plain language, then re-audits and reports; every step is a reviewable diff and a single undo. |
| AGENT-2 | Cleanup agent | AI | M | Todo | A messy import is cleaned through announced, reversible recipes ending in well-structured text. |
| AGENT-3 | Review agent | AI | M | Todo | A spoken, skimmable review reports structure, readability, accessibility, and consistency with one-key jumps to issues. |
| AGENT-4 | Safe local agent runtime | AI | L | Todo | The agent plans and takes one consented step at a time, calls only an in-app tool allowlist, never the network without consent, has a hard step cap and loop guard, and announces every step; reuses the sandbox and stability layers. |

##### AI provider review (from section 18.4 and 18.5)

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| AI-13 | Wire configured providers to a real chat backend | AI | L | Todo | A provider-aware AIBackend routes generation to the selected provider (OpenAI/OpenRouter/custom and Azure via chat-completions, Claude via messages, Gemini via generateContent, local Ollama via /api/chat); selecting a cloud or Ollama provider actually changes who responds, verified by tests. This is the top AI fix. |
| AI-14 | Streaming responses across providers | AI | M | Todo | Each wired provider streams tokens with throttled, accessible announcements (ties to AI-1); a non-streaming fallback degrades cleanly. |
| AI-15 | Provider-specific correctness | AI | M | Todo | Azure targets a deployment (UI distinguishes deployment from model); Claude sends required max_tokens; Gemini uses its own request/response adapter; OpenRouter can send attribution headers; Ollama chat uses /api/chat. |
| AI-16 | Per-provider contract tests | AI | M | Todo | Recorded or mocked request/response tests cover each provider with no live network in CI; a provider schema change fails the build instead of silently breaking generation. |
| AI-17 | Extend the error taxonomy to the chat path | AI | S | Todo | The existing auth/forbidden/rate-limited/warming-up/timeout categories produce the same cause-specific, screen-reader-friendly messages for generation as they do for model listing. |
| AI-18 | GitHub Copilot SDK as an optional post-1.0 provider | AI | M | Todo | If pursued, Copilot is an optional, clearly labeled provider behind the AIBackend boundary with an accessible OAuth device-flow sign-in, gated and never default; documented rationale (section 18.5) is honored. Not required for 1.0. |

---

## Part IV: The combined accessibility suite (GLOW and BITS Whisperer)

QUILL does not exist alone. It sits beside two sibling products built for the same audience, and there is a rare opportunity to fuse them into a single, coherent, best-in-class accessibility suite rather than three overlapping apps. This part defines how to bring GLOW (document accessibility audit and fix) and BITS Whisperer (audio transcription) into QUILL as first-class, deeply integrated capabilities, what to keep, what to drop, and what shared foundation makes it durable.

The strategic case: all three products share a mission (do excellent work for blind and low-vision people), a stack (Python and wxPython, accessibility-first, local-first), and an audience. Three separate apps mean three menus to learn, three update mechanisms, three places for a document to live, and triplicated engineering. One suite, with QUILL as the writing and editing home, GLOW as its accessibility engine, and BITS Whisperer as its transcription engine, is simpler for users and far more powerful: write, transcribe, audit, fix, and publish in one place, by keyboard and voice, with one set of conventions.

### 19. GLOW integration: make QUILL accessibility-native

QUILL already contains `quill/core/glow.py`, a text-level GLOW audit and fix surface (generic link text, plain-language lint, audit and fix reports for the selection or document) wired to commands such as `tools.glow_fix_document` and `tools.glow_fix_selection`. Separately, GLOW is a full document-accessibility platform (a VS Code agent toolkit, a desktop app, and a web app) enforcing ACB Large Print, APH, WCAG 2.2 AA, and Microsoft Accessibility Checker rules across Word, Excel, PowerPoint, PDF, EPUB, HTML, and Markdown, with audit, auto-fix, template generation, and conversion. The shared library `quill-glow-core` already exposes a stable host-facing API (`audit_by_extension`, `fix_by_extension`, `convert_to_markdown`, `get_component_versions`) with a dispatch core, a safe no-op fallback, and a GLOW backend adapter.

The plan: adopt `quill-glow-core` as the single shared engine so QUILL's in-editor GLOW and the GLOW desktop and web apps audit and fix by exactly the same rules, with one place to improve them.

- Depend on the shared core. Replace QUILL's bespoke text-level checks with calls into `quill-glow-core` (`configure_default_services` then `audit_by_extension` and `fix_by_extension`), keeping QUILL's friendly in-editor reports as the presentation layer. When the GLOW backend is present, QUILL gets the full ACB, APH, WCAG, and MSAC rule sets; when it is absent, the safe no-op fallback keeps QUILL fully functional. See GLOW-1.
- Audit and fix by structure, not just text. Today QUILL audits plain text, Markdown, and HTML. Extend it through the shared core to audit and fix the structured formats QUILL already reads (DOCX, PPTX, XLSX, PDF, EPUB) so a user can open a real document and run a full accessibility audit in place. See GLOW-2, IO-1.
- An in-editor accessibility report that reads beautifully. Present GLOW findings as a navigable, screen-reader-pageable list grouped by severity, each with a one-key jump to the location, a plain-language explanation, and (where fixable) a reviewable apply-and-undo. This is the same surface the Accessibility agent (AGENT-1) drives. See GLOW-3, AGENT-1, AI-7.
- Standards profiles in QUILL. Surface GLOW's profiles (ACB 2025 Baseline, APH Submission, Combined Strict) as a setting so a user can choose the rigor that fits their work, with the active profile shown in every report for traceable evidence. See GLOW-4, SET-1.
- One-key publish to accessible output. Reuse GLOW's conversion chain (MarkItDown plus Pandoc, with LibreOffice-assisted pre-conversion and PyMuPDF table preservation) so QUILL can export clean, accessible Word, HTML, EPUB, and PDF with announced results. This realizes FEAT-17 on a proven engine. See GLOW-5, FEAT-17.
- Shared versioning and telemetry. Use `get_component_versions` and the startup telemetry so QUILL can show which accessibility engine and rule version is active, keeping the honesty principle. See GLOW-6.

What to keep lightweight in QUILL: QUILL should not absorb GLOW's web app, its branding-profile deployment machinery, or its template-generation server flows. QUILL consumes the shared core; the GLOW desktop and web apps remain the heavyweight authoring and batch surfaces. The boundary is clean: shared rules and fixers in `quill-glow-core`, three thin presentation layers on top.

### 20. BITS Whisperer integration: transcription becomes a QUILL superpower

QUILL already contains `quill/core/bw_speech.py`, a speech-model manager that mirrors a subset of BITS Whisperer (faster-whisper model specs, hardware eligibility, a model manager, provider status), exposed through a "BITS Whisperer" menu group (Speech Model Manager, Provider Center, Use Recommended, and so on). BITS Whisperer itself is a mature, accessibility-first transcription app: 18 providers (cloud and on-device), 14 Whisper models, AI translation and summarization, live microphone transcription, speaker diarization, a watch folder, scheduled transcription, do-not-disturb, a plugin system, seven export formats, and a setup wizard, all WCAG-adapted with a menu-first, screen-reader-first design.

The opportunity is large: a writer who can transcribe an interview or a lecture and immediately edit, audit, and publish it, all in one accessible app, has something no mainstream editor offers. The plan is to bring BITS Whisperer's transcription engine into QUILL as a first-class "Transcribe" capability, reusing BW's provider and model layer rather than reimplementing it.

What to bring into QUILL (high value):

- Transcribe to a document. Add a Transcribe command that takes an audio or video file (or a folder) and produces a QUILL document with the transcript, ready to edit, audit with GLOW, and publish. Reuse BW's provider abstraction and faster-whisper model manager (the `bw_speech.py` foundation already present). See BW-1.
- Local-first providers by default. Surface BW's on-device providers (local Whisper via faster-whisper, Vosk, Parakeet, Windows Speech, Azure Embedded) as the default, with cloud providers strictly opt-in and consented, matching QUILL's no-silent-network rule. See BW-2, AI-5.
- Live dictation into the editor. Bring BW's live microphone transcription in as an accessible "dictate into the document" mode with clear start, stop, and status announcements, complementing QUILL's existing dictation. See BW-3.
- Speaker labels and clean structure. Use BW's diarization to produce well-structured, speaker-labeled transcripts that QUILL can then clean with the Cleanup agent. See BW-4, AGENT-2.
- AI translation and summarization on the transcript, through QUILL's own consented AI layer rather than a parallel one. See BW-5, AI-8.
- Watch folder and batch. Offer BW's watch-folder and batch transcription as an optional power feature, announced non-intrusively, reusing QUILL's existing watch-folder pattern. See BW-6, FEAT-9.
- A unified Provider and Model Center. Consolidate BW's provider and model management with QUILL's AI model and connection management into one accessible Settings home, so a user manages all engines (writing AI, transcription providers, speech models) in one place. See BW-7, MENU-1, SET-1.

What to drop or de-scope from the standalone BITS Whisperer plan once integrated:

- Retire the duplicate application shell. The separate BW main window, tray icon, setup wizard, and updater are not needed inside QUILL; QUILL provides the shell, onboarding, and update path. Keep BW as a library, not a second app. See BW-8.
- Drop duplicated subsystems. BW's own settings store, watch folder, plugin manager, registration and licensing, beta service, and Copilot chat panel should defer to QUILL's equivalents rather than ship twice. Consolidate to one of each. See BW-8.
- Reconsider breadth of cloud providers. Eighteen providers is a maintenance load; in the suite, lead with the strong on-device set plus a small, well-supported cloud selection, and treat the long tail as optional plugins rather than core. See BW-9.
- Unify export. QUILL plus GLOW already cover accessible export (Word, HTML, EPUB, PDF, Markdown); transcript-specific formats (SRT, VTT) become QUILL export presets rather than a separate BW exporter. See BW-10, FEAT-17.

The combined-suite outcome: one accessible app where a blind or low-vision user can transcribe spoken audio, write and edit the result, audit and fix it to ACB, APH, and WCAG standards, and publish accessible output, entirely by keyboard and voice, with local-first privacy and one consistent set of conventions. That is a genuinely category-defining product, and it reuses two existing, proven engines instead of building from scratch.

### 21. Shared foundation for the suite

- One shared accessibility core. `quill-glow-core` is the single source of audit and fix rules for QUILL, GLOW desktop, and GLOW web. See GLOW-1.
- One transcription engine. BITS Whisperer's provider and model layer becomes a library consumed by QUILL (and still usable standalone if desired). See BW-1, BW-8.
- One set of conventions and gates. The quality-gate ladder (Part III) and the accessibility non-negotiables apply across the suite, so all three surfaces meet the same bar. See GATE-2.
- One identity for the user. Shared secret storage, shared update path, and a single Settings home reduce cognitive load and duplicated engineering. See SET-1, BW-7.

#### 21.1 New backlog items for the combined suite

These extend the section 14 tracker.

| ID | Item | Area | Size | Status | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| GLOW-1 | Adopt quill-glow-core as the shared engine | Suite | M | Todo | QUILL audits and fixes via `quill-glow-core` with the GLOW backend when present and the safe no-op fallback when absent; in-editor reports unchanged for users; tests cover both paths. |
| GLOW-2 | Audit and fix structured formats in-editor | Suite | L | Todo | DOCX, PPTX, XLSX, PDF, and EPUB can be audited (and fixed where supported) in place through the shared core. |
| GLOW-3 | Navigable in-editor accessibility report | Suite | M | Todo | Findings are a screen-reader-pageable list grouped by severity with one-key jump, plain-language explanation, and reviewable apply-and-undo. |
| GLOW-4 | Standards profiles setting | Suite | S | Todo | ACB Baseline, APH Submission, and Combined Strict are selectable; the active profile shows in every report. |
| GLOW-5 | Accessible publish via the GLOW conversion chain | Suite | M | Todo | One-key export to accessible Word, HTML, EPUB, and PDF using the shared conversion chain, with announced results. |
| GLOW-6 | Show active accessibility engine and rule version | Suite | S | Todo | QUILL displays the GLOW engine and rule version via `get_component_versions` and startup telemetry. |
| BW-1 | Transcribe audio or video to a QUILL document | Suite | L | Todo | A Transcribe command produces an editable transcript document, reusing BW's provider and faster-whisper model layer; on-device by default. |
| BW-2 | Local-first transcription providers with consented cloud | Suite | M | Todo | On-device providers are default; cloud providers are opt-in and consented; no silent network calls. |
| BW-3 | Live dictation into the editor | Suite | M | Todo | Live microphone transcription writes into the document with clear start, stop, and status announcements. |
| BW-4 | Speaker-labeled, structured transcripts | Suite | M | Todo | Diarization produces speaker-labeled structure that the Cleanup agent can refine. |
| BW-5 | Translate and summarize transcripts via QUILL AI | Suite | M | Todo | Translation and summarization run through QUILL's consented AI layer, not a parallel one. |
| BW-6 | Watch-folder and batch transcription | Suite | M | Todo | Optional batch and watch-folder transcription reuses QUILL's watch-folder pattern with non-intrusive announcements. |
| BW-7 | Unified Provider and Model Center | Suite | M | Todo | Writing AI, transcription providers, and speech models are managed in one accessible Settings home. |
| BW-8 | Consume BITS Whisperer as a library, retire the duplicate shell | Suite | L | Todo | QUILL provides the shell, onboarding, settings, watch folder, plugins, and updates; BW ships as a consumed library, not a second app. |
| BW-9 | Right-size the cloud provider set | Suite | S | Todo | The suite leads with on-device providers plus a small supported cloud set; the long tail becomes optional plugins. |
| BW-10 | Unify transcript export into QUILL presets | Suite | S | Todo | SRT and VTT become QUILL export presets; there is one export path for the suite. |

---

## Part V: Impact ranking and build order

The user's directive is to develop with an impact-first mindset, and to be wise about whether and when to do hardening, security, and refactoring. This part ranks the entire plan, including QUILL's own features, from most impactful to least, and explains the reasoning so the order is clear and defensible. We are building for greatness and high quality, so impact here means lasting value to the user and to the product's standing, not just visible novelty.

### 22. How impact is judged

Two ideas, kept distinct on purpose:

- User impact: how much an item improves the real experience of a blind or low-vision writer (and the power user). A delightful, discoverable QUILL key is high user impact; an internal refactor is not.
- Leverage: how much an item unlocks or de-risks everything else. The quality-gate ladder and the main_frame characterization tests are low direct user impact but very high leverage, because they make all later work faster, safer, and higher quality.

Great products optimize for both. The wise sequence does the small, high-leverage protections first (so nothing later regresses users), then the high user-impact flagship work, then the larger structural and breadth investments, then the long tail. Specifically, on the user's question: yes, hardening and security and refactoring are worth doing, but not all at once and not all first. The cheap, user-protecting parts of hardening (the latent-crash bug fixes and the untrusted-input security) are top-tier because they are small and prevent real harm. The large refactor (decomposing the UI monolith) is high leverage but should come after the flagship value lands and only behind characterization tests, so it never becomes risk for its own sake.

### 23. The ranked tiers

Each tier lists what belongs in it and why, with the value it brings and the high-value outcome it produces. Items are referenced by their backlog IDs. The order follows the build directive: QUILL's own features and the cheap hardening come first, then GLOW, then BITS Whisperer last, with structural health and documentation sequenced around them.

#### Tier 1: Protect users and unlock the team (do first)

These are small, cheap, and either prevent real harm or unlock everything after them. Highest impact-to-effort ratio in the whole plan.

- Fix the latent-crash bugs: BUG-1, BUG-2 (real user paths), then BUG-3 through BUG-7. Value: the product cannot crash on a path a user can reach. Outcome: basic trust and a clean baseline.
- Harden untrusted input and the worst security gaps: SEC-10 and SEC-11 (XML and zip bombs), SEC-1 (executable-path validation), SEC-13 (secret redaction). Value: a malicious or malformed file cannot harm the user. Outcome: a defensible 1.0 safety bar.
- Stand up the gate ladder: GATE-1 through GATE-9, especially GATE-4 (banned patterns), GATE-9 (no-silent-network), and GATE-3 (scoped typing). Value: quality becomes objective and AI-assisted work accelerates safely. Outcome: nothing regresses users again, and Copilot and agents become a force multiplier instead of a risk.
- The accessibility gate on every change: GATE-7. Value: the mission becomes machine-enforced. Outcome: no UI change can quietly break a screen reader.

Why first: these are inexpensive, they protect users immediately, and they make every later step cheaper and safer. Skipping them would mean building flagship features on sand.

#### Tier 2: The flagship experience users will talk about (do next)

The highest user-impact features: the reasons a blind writer would choose and recommend QUILL.

- The QUILL key as a discoverable, tunable, consistent flagship: QK-1 through QK-5, QK-9 (question-mark cheat sheet and per-mode help). Value: the signature interaction becomes learnable in seconds and fast forever. Outcome: a memorable identity no competitor has.
- Navigation and selection by structure: NAV-1, NAV-4 (go-to-anything), NAV-5, SEL-1 through SEL-3. Value: moving and selecting by meaning, not by guesswork. Outcome: real documents become navigable by ear at speed.
- The Accessibility agent and trustworthy AI editing: AGENT-1, AI-7 (diffs reviewable by ear), AI-1 (streaming), AI-6 (graceful degradation). Value: "make this document accessible," done step by step, reversibly, by keyboard and voice. Outcome: a category-defining capability that embodies the mission.
- Make the configured AI providers actually work: AI-13 (the headline fix), AI-15 (provider correctness), AI-17 (chat-path error messages), then AI-14 (streaming) and AI-16 (contract tests). Value: when a user selects OpenAI, OpenRouter, Gemini, Azure, Ollama, or Claude, that provider is the one that responds, instead of silently falling back to the local model. Outcome: the provider boundary becomes trustworthy and the QUILL AI surface is honest end to end. This is both a QUILL feature and AI hardening, so it sits here with the flagship.
- Deep, tunable settings: SET-1 through SET-7. Value: users shape QUILL precisely to their hands and ears. Outcome: the product meets people exactly where they are.
- Trustworthy external-change handling: FEAT-19. Value: a file edited by another program is never silently lost or silently overwritten; clean files reload in place without losing the cursor, and conflicts get a clear spoken choice. Outcome: QUILL feels safe and alive when documents change underneath it, which matters most to a screen-reader user who cannot see a flicker.

Why second: this is where user love is won. It comes right after the protections so the flagship is built on a safe, gated base.

#### Tier 3: GLOW, the accessibility engine inside QUILL (second strategic priority)

Per the build directive, GLOW comes before transcription: it deepens QUILL's core mission of accessible documents and reuses a proven engine.

- GLOW as the in-app accessibility engine: GLOW-1 through GLOW-5. Value: audit and fix real documents to ACB, APH, and WCAG standards in place, through the shared `quill-glow-core` API rather than the thin local bridge. Outcome: writing and document accessibility become one app.
- GLOW interaction quality: surface findings as reviewable-by-ear diffs and one-key jumps, reuse the consented, reversible flow from the Accessibility agent (AGENT-1), and keep the standards profiles (ACB 2025 Baseline, APH Submission, Combined Strict) explicit and announced. Value: the audit-and-fix loop is fully accessible. Outcome: GLOW feels native to QUILL, not bolted on.
- Code-quality and integration fixes for the boundary: replace the thin `quill/core/glow.py` bridge with calls into `quill-glow-core`, add contract tests for the shared API, and keep version and component reporting honest. Value: a clean, tested seam. Outcome: GLOW improvements flow into QUILL without surprises.

Why third: high strategic value that extends the core mission, depends on the gated base (Tier 1), and is most compelling once the flagship experience (Tier 2) already feels great. Most cost is integration, not invention.

#### Tier 4: Structural health and performance that keep greatness durable (high leverage)

Not flashy, but what lets the product stay excellent as it grows.

- Decompose the UI monolith behind characterization tests: CQ-16 then CQ-1, with GATE-6 and GATE-11. Value: every future change gets faster and safer. Outcome: the 18,748-line risk becomes maintainable. Sequencing note: do this after Tier 2 ships, never as a prerequisite to it, and always behind passing characterization tests.
- Drive the strict-typing zone and lint to clean: TYPE-1 through TYPE-8, CQ-18. Value: a class of bugs disappears at author time. Outcome: a codebase that resists regression.
- Remove first-use stalls and enforce budgets: PERF-1 through PERF-3, PERF-9 through PERF-14, GATE-10. Value: the app feels instant. Outcome: performance that does not slip back.
- The remaining security hardening: SEC-6, SEC-7, SEC-14 through SEC-17, SEC-8 (plugins stay gated). Value: defense in depth. Outcome: a product that is safe by construction.

Why fourth: high leverage but mostly invisible to users, so it follows the work that wins user love, while the cheap protective parts of it already happened in Tier 1.

#### Tier 5: Documentation greatness and the learning surface (completes the product)

A great product is not done until people can learn it.

- Consolidate and elevate the docs folder: DOC-14 through DOC-17, DOC-11 (accessibility), DOC-12 (engineering docs). Value: documentation that is itself a model of accessibility and clarity. Outcome: nobody is left behind.
- The learning surface: DOC-1 through DOC-8, the podcasts (POD-1 through POD-5), and the tutorials (TUT-1 through TUT-7). Value: a complete path from first launch to mastery. Outcome: a launch that lands with a full learning experience.
- Test breadth: CQ-11 through CQ-16, CQ-23, CQ-24, the IO matrix, and the sandbox policy suite. Value: confidence that everything documented actually works. Outcome: durable quality.

Why fifth: essential for greatness, but it should describe a product that is already built, safe, and delightful, so it follows the feature and structural work it documents.

#### Tier 6: BITS Whisperer and expansion (last, after 1.0, guided by feedback)

Per the build directive, transcription comes last. It is valuable and unique, but it is the furthest from QUILL's writing-and-accessibility core, so it follows the flagship, GLOW, structure, and docs.

- BITS Whisperer as the transcription engine: BW-1 through BW-4, BW-7. Value: transcribe audio, then edit, audit, and publish without leaving QUILL. Outcome: a write-transcribe-audit-publish loop no mainstream editor has.
- Right-size and unify the suite: BW-8 (drop BITS Whisperer's duplicate shell, tray, setup wizard, updater, settings, watch folder, plugins, and registration in favor of QUILL's), BW-9 (right-size the 18 providers to a sensible default set), BW-10 (one shared export path). Value: less to learn, less to maintain. Outcome: a coherent suite rather than overlapping apps.
- One shared foundation: shared core, one transcription library, one Settings home, one update path (Part IV, section 21). Value: coherence across the suite. Outcome: the suite feels like one product.
- Breadth and exploration: NAV-10 (symbol navigation), AI-11 (local grounded answers), AI-12 (evaluation harness), AI-18 (optional GitHub Copilot SDK provider, only if beta users ask), FEAT-12 through FEAT-18, BW-5, BW-6, and LINUX-1. Value: new reach and polish. Outcome: a growing product shaped by real user feedback.
- Close every dimension to highest quality: LINUX-2 (accessible Linux to product bar), ECO-1 (plugin capability, signing, and marketplace model), L10N-1 (full UI and docs localization), and COLLAB-1 (accessible asynchronous review and sharing). Value: nothing of substance is left below best-in-class. Outcome: the only remaining limits are deliberate scope choices, not shortfalls.

Why last: valuable but not required for a great, trustworthy 1.0; the transcription suite and the stretch items are best chosen with beta evidence in hand, and the build directive explicitly places transcription after QUILL, hardening, and GLOW.

### 24. The development mindset in one paragraph

Lead with cheap protections and gates, because they make everything after them safe and fast. Then spend the bulk of the energy on the flagship QUILL experience, including making the configured AI providers actually respond (AI-13), because that is where greatness is felt and where the product must be honest. Bring GLOW in next, since it extends QUILL's accessibility mission and reuses a proven engine, and only then add BITS Whisperer transcription, which is the most distant from the writing core. Treat the big refactor and performance and security depth as high-leverage investments that follow, not precede, the user-facing wins, and always do the refactor behind characterization tests. On the GitHub Copilot SDK: keep it optional and post-1.0, behind the same provider boundary, never a default, because its subscription and sign-in friction conflict with the local-first, bring-your-own-key promise even though the underlying models add value. Finish by making the documentation and learning surface as excellent as the product. Do not do hardening or refactoring for their own sake or all at once; do the parts that protect users early, and the parts that only reshape code later, once their value is clear and their risk is contained.

---

## Part VI: State of the union

If every item in this plan were completed (Parts I through V: the delight program, the verified bug and security and typing and performance fixes, the documentation greatness work, the quality-gate ladder, the AI and agent program, the combined GLOW and BITS Whisperer suite, and the impact-ordered build sequence), here is the scale and standing the product would reach.

### What QUILL would be

QUILL would be a mature, 1.0-grade, screen-reader-first writing application: not a promising beta, but a dependable daily tool that a blind or low-vision writer could trust for real work, and that a sighted power user would also find fast and pleasant. The signature QUILL key would be a genuinely memorable interaction (discoverable with one question mark, tunable, consistent, and documented as the headline feature), and the accessibility agent would be a category-defining capability: tell the app to make a document accessible, and watch it do so, step by step, reversibly, entirely by keyboard and voice. The AI surface would also be honest end to end: when a user picks OpenAI, OpenRouter, Gemini, Azure, Ollama, or Claude, that provider is the one that responds, instead of the configuration being accepted while generation silently falls back to the local model (AI-13). GLOW would be folded in as the in-app accessibility engine, and transcription would arrive last as a unifying capability, in that deliberate order.

### Scale on the dimensions that matter

The following self-assessment uses a simple five-level scale: Level 1 prototype, Level 2 beta, Level 3 product, Level 4 polished product, Level 5 best-in-class or category-defining. Today's honest baseline is included for contrast.

| Dimension | Today (0.1.5 beta) | After this plan | Notes |
| --- | --- | --- | --- |
| Accessibility | Level 4: strong, screen-reader-first | Level 5: category-defining | Accessibility is gated on every change; the accessibility agent has no real peer. |
| Core writing and navigation | Level 3 to 4 | Level 5 | QUILL key, Quick Nav, and structural selection become a cohesive, discoverable, tunable system. |
| AI and agents | Level 2: strong config, but providers do not yet generate | Level 4 to 5 | Today the provider boundary, key storage, and model discovery are excellent, but a configured cloud or Ollama provider silently falls back to the local model (AI-13); after this plan, local-first, consented, reversible, fully accessible AI editing and a real accessibility agent, with the selected provider actually responding. |
| Code quality and architecture | Level 3: well-structured but a monolith | Level 5 | The UI monolith is fully decomposed behind characterization tests; strict typing and lint are clean and enforced everywhere, not only in the core zone. |
| Security and privacy | Level 3 | Level 5 | Untrusted-input hardening, supply-chain checks, machine-enforced no-silent-network, and a documented plugin capability and signing model (ECO-1). |
| Performance | Level 3 | Level 5 | First-use stalls removed; budgets enforced by a gate; large-document and Read Aloud paths tuned to best-in-class responsiveness. |
| Documentation | Level 3 to 4 | Level 5 | Consolidated, accessible, complete, with primers, references, podcasts, tutorials, and full localization (L10N-1). |
| Combined suite (GLOW and transcription) | Level 2: separate apps, partial bridges | Level 5 | Write, transcribe, audit, fix, and publish in one accessible app on shared engines. |
| Engineering process and gates | Level 2: tools exist, not enforced | Level 5 | A full gate ladder makes quality objective and lets AI assistance accelerate safely. |
| Test coverage | Level 2 to 3 | Level 5 | UI characterization, IO matrix, sandbox policy, per-provider contract tests, and a performance budget close every major gap, with a ratcheting coverage floor. |
| Platform breadth | Level 3: Windows and macOS | Level 5 | Windows and macOS are excellent and Linux reaches the same accessibility and stability bar (LINUX-2). |

### Overall standing

- Today: a strong, accessibility-leading 0.1.5 beta with an excellent foundation, a few latent bugs, a large UI monolith, an AI provider surface whose configuration outruns its wiring (cloud and Ollama selections do not yet drive generation), and quality tools that are present but not yet enforced. Roughly Level 3 overall, already Level 4 on accessibility.
- After this plan: a confident, releasable product at Level 5 across every dimension that matters, and clearly category-defining on accessibility and on accessible AI-assisted editing. It would be, credibly, the most accessible writing application available, with an agent capability that no mainstream editor offers, backed by an engineering process strong enough to keep it that way. Because the plan now commits to closing every dimension to highest quality (the former frontiers below are committed work, not deferred hopes), nothing of substance is left at less than best-in-class once it is complete.

### Closing every remaining gap to highest quality

The earlier draft of this plan listed frontiers that would remain even after full implementation. To meet the directive that nothing be left below highest quality, those frontiers are now committed plan items rather than acknowledged shortfalls:

- Platform breadth. Beyond the Linux spike (LINUX-1), the plan now commits to an accessible Linux platform layer at the same bar as Windows and macOS (LINUX-2).
- Collaboration. Real-time multi-user editing stays deliberately out of scope (with the reason recorded), but the plan commits to local-first, accessible asynchronous review and sharing so collaboration is not a blank (COLLAB-1).
- Ecosystem. The plan commits to a documented plugin capability and signing model and a review process, so a safe third-party ecosystem can grow off the experimental flag (ECO-1, building on SEC-8).
- Localization depth. The plan commits to full UI and core-documentation localization for the launch languages, with a process to keep translations current (L10N-1).

These are large (XL) investments and are sequenced into Tier 6 after the 1.0 wins, but they are now part of the committed plan, so the honest answer to "what would still fall short?" is: nothing of substance. The only remaining limits are deliberate scope choices (no real-time co-editing) and the permanent reality that a living product keeps improving with user feedback.
