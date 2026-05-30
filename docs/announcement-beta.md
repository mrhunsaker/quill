# Announcing Quill Beta

## A screen-reader-first writing environment for Windows

Quill Beta is here.

This release is Quill 0.1.1 Beta from Blind Information Technology Solutions (BITS) and Community Access.

Quill is a writing, reading, review, and document-intelligence environment for Windows built around a simple idea: powerful tools should feel calm, predictable, and welcoming from the keyboard. The editor is local-first, screen-reader-first, and designed to make serious text work feel steady instead of fragile.

The name is intentional. Quill reflects both writing craft and a love of magical storytelling (yes, Harry Potter), but grounded in dependable engineering. This work is built by us, for us, and for the wider world.

Quill is not only a place to type notes. It is a place to open and write plain text, Markdown, HTML, and RTF; inspect structure; compare revisions; navigate EPUB content; review extraction quality; run accessibility checks; work with spelling and thesaurus tools; use golden keyboard packs; and move through real documents with confidence.

It is also a place to grow. Quill now includes guided onboarding for optional external tools, so users can see exactly what helpers such as Pandoc, Tesseract OCR, LibreOffice, and Ghostscript would unlock before they install anything. When Pandoc is present, Quill can open a native conversion wizard and turn supported source files into Markdown, HTML, or plain text surfaces ready for reading, editing, or GLOW-oriented downstream workflows.

This beta also includes a menu discoverability pass. The Tools menu is grouped into plain-language submenus (Writing and Language, Read Aloud, Integrations, Document Intake, Authoring and Automation, Compare Documents, Accessibility, Support, and Customize), and mark-ring wording now reads as Recent Marks (Ring) to lower jargon. The interactive status bar is also fuller: focused cells now expose direct context actions (Activate, Hide this item, Status bar settings), and status bar settings now include Restore Defaults.

## What makes Quill special

Quill Beta already includes a broad set of everyday and specialist features:

- a keyboard-first editor shell with command palette, tabs, rich navigation, and an interactive status bar
- plain text, Markdown, HTML, and RTF workflows that stay readable and structured
- spell check, thesaurus, word count, link insertion, and source-aware copy
- heading, list, table, code block, and markup insertion tools
- compare workflows for file-to-file and document-to-document review
- EPUB navigation, OCR image intake, and extraction-quality review
- feature profiles that keep the interface calm without taking power away
- golden keyboard packs inspired by Windows Notepad, Notepad++, VS Code, Microsoft Word, and Quill-native workflows
- the first native GLOW workflows for deterministic audit and fix work inside the editor itself
- external tool onboarding with wizard-like guidance for Pandoc and other optional format helpers
- accessibility-focused support such as region cycling, keyboard-trap inspection, contrast validation, and discoverable help surfaces
- backups, autosave, recovery, persistent undo, trusted locations, notifications, diagnostics export, and signed update checks

## The new GLOW experience inside Quill

One of the most exciting additions in this beta is the first native GLOW workflow inside Quill.

GLOW stands for guided layout and output workflow. In Quill Beta, GLOW makes accessibility-aware review feel like part of writing rather than a separate compliance chore. You can audit the current document, audit the current selection, fix the current document into a preview tab, compare original and fixed output, or apply deterministic fixes directly to the current selection.

This first slice focuses on plain text, Markdown, and HTML. It already helps with heading spacing, heading-level jumps, generic link text, missing HTML language metadata, missing image alt attributes, dense paragraphs, and plain-language friction.

Quill also now has the start of a broader format-bridge story. With Pandoc available, users can bring in supported text-centric source formats through a guided wizard instead of a command line, then continue the work inside Quill with structure-aware editing, compare, spell, and GLOW flows. That matters because accessible document work often begins in an awkward format and only becomes productive after it is translated into a surface that is stable, readable, and reviewable.

That same spirit applies to the learning surface. Quill now has a cleaner documentation ladder: the welcome guide for a first orientation, the keyboard reference for exact current bindings, the full user guide for day-to-day depth, this beta announcement for the big-picture feature story, and the PRD for the broader 1.0 direction. The goal is not to bury users in docs. The goal is to make sure there is always one clear next document when a user asks, "What do I do now?"

## Why this beta matters

Quill is being built for people who need an editor that feels trustworthy.

That includes:

- screen-reader users who want a native Windows experience
- writers and editors who work heavily in plain text, Markdown, or HTML
- accessibility-minded teams reviewing structure and readability
- people opening difficult or imperfect source documents and trying to decide whether the extracted text is good enough to trust
- people who need one Windows editor that can stay simple for daily writing while expanding into optional conversion and ingestion workflows when needed
- users who want a serious editor that still teaches them what it can do

This beta is not just a preview. It is the moment when Quill starts learning from real work.

## This is a beta

Quill Beta is already useful, but it is still a beta.

That means:

- bugs may be found
- some features are deeper than others
- some workflows are still maturing toward the full 1.0 vision
- parts of the support and feedback experience still need polishing before the broadest public rollout

If something feels rough, that feedback is valuable. If something delights you, that is valuable too. Both help shape what Quill becomes next.

## Feedback and bug reports

We want the beta feedback path to be inclusive and low-friction.

Inside Quill 0.1.1 Beta, the primary feedback path starts in the Help menu.

If you want to report a problem, Quill now guides you through it like this:

1. Open **Help -> Report a Bug...**.
2. Review the in-app support summary that Quill prepares for you.
3. Choose whether to include diagnostics, and whether to include plain file paths.
4. If diagnostics are included, save the diagnostics zip somewhere easy to find, such as your Desktop or Downloads folder.
5. Choose **Open Support Form** to open the Community Access support page.
6. Describe what happened in plain language and attach the diagnostics zip if it helps.

That is the intended unified user route. It keeps the work inside Quill for as long as possible, explains what is being shared, and gives the user a clearer handoff into the Community Access support process.

There is still room to improve this over time, especially around future no-login upload flows, but the important point for Quill 0.1.1 Beta is that users should start in **Help**, not by hunting for a GitHub page.

## Thank you for trying Quill

Trying a beta takes generosity. You are trusting unfinished software with real work, real attention, and real patience.

Thank you for that.

We also want to give specific, sincere thanks to contributors and beta testers who helped shape this release:

- Techopolis
- Taylor Arndt
- Michael Doise
- Kayla Bentas
- Shane Popplestone
- Becky Knobb

If Quill helps you write more confidently, review more carefully, or simply feel more at home in a Windows editor, then the beta is already doing something important. And if you help point out what still needs work, you are helping build the version that will be even stronger.

Quill Beta is ready to be explored. Open a file, press `Ctrl+Shift+P`, and start.
