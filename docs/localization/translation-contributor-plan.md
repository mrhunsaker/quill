# QUILL Translation Contributor Plan

**QUILL** follows a community-first localization model inspired by NVDA's gettext workflow.

This document is the working plan for contributors who want to help translate QUILL and help maintain translation quality across releases.

## Goals

1. Keep translation contribution easy for first-time contributors.
2. Keep translation quality high enough for daily screen-reader use.
3. Keep release timing predictable with clear string-freeze expectations.
4. Keep translator effort visible and credited in the product and docs.

## Translation model (POT/PO/MO)

QUILL uses GNU gettext catalogs:

- `locale/quill.pot` as the extracted template
- `locale/<lang>/LC_MESSAGES/quill.po` as editable translator source
- `locale/<lang>/LC_MESSAGES/quill.mo` as compiled runtime catalog

Developers write user-facing strings in source code. The extraction step updates `quill.pot`. Translators edit `quill.po`. Build/release compiles `.po` to `.mo`.

## Community contribution workflow

### Phase 1 (current): GitHub pull requests

1. Fork the repository.
2. Create or update `locale/<lang>/LC_MESSAGES/quill.po`.
3. Validate placeholders and syntax locally.
4. Open a pull request with a short summary of updated sections.

This phase is intentionally lightweight so contributors can join immediately.

### Phase 2 (planned): Translation portal

When volume grows, QUILL will add Weblate or Crowdin while keeping gettext catalogs as the source format. The goal is easier review, glossary enforcement, and translator-team coordination without changing runtime architecture.

## Required translator conventions

1. Preserve placeholders exactly (for example `{filename}`, `{count}`).
2. Respect translator comments prefixed with `Translators:`.
3. Translate UI and accessibility announcements, not user-authored document content.
4. Use context-aware strings where supplied (`pgettext`/`npgettext` contexts).

## Release cycle expectations

1. **Development window**: source strings may change.
2. **Beta translation push**: translators update active languages.
3. **String freeze** (before release): only critical wording fixes allowed.
4. **Release candidate checks**: catalog validation, compile checks, pseudo-locale smoke pass.
5. **Credits refresh**: contributor names and language coverage updated.

## Quality gates for maintainers

Maintainers should block release if translation checks fail:

1. POT extraction succeeds and is committed when strings changed.
2. PO syntax validates.
3. MO compilation succeeds.
4. Named placeholders match source strings.
5. Required release languages are not left in fuzzy-only or broken state.

## What gets translated vs not translated

Translate:

- Menus, dialogs, labels, settings, status text
- Accessible names/descriptions and spoken announcements
- Built-in snippet pack names, descriptions, prompts, and categories

Do not auto-translate:

- User-created document text
- User-created snippets
- User-specific content and imports

## Community recognition

QUILL treats translators as product contributors, not post-release afterthoughts.

- Release notes should include localization updates.
- The About and documentation surfaces should credit translation contributors.
- Community review is encouraged for terminology, consistency, and accessibility clarity.

## Related documentation

- [Announcement: Quill 0.1.2 Beta](../announcement-beta.md)
- [Quill User Guide](../userguide.md)
- [QUILL Product Requirements Document](../QUILL-PRD.md)
