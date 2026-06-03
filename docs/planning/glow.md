# Tier 3 plan: the GLOW accessibility suite

This document is the full, reviewable plan for Tier 3 of QUILL: making QUILL
accessibility-native by adopting GLOW as its shared accessibility engine. It is
written so you can review the intent and the cross-repo coordination while the
work is in progress. It expands on section 19 and section 21 of `ROADMAP.md` and
the GLOW-1 through GLOW-7 and WATCH-8 backlog rows, and it is the source of truth
for what changes land in each of the three repositories.

This is a planning document. Nothing here is built yet. Items are tracked in
`ROADMAP.md` under the GLOW IDs.

## 1. The goal in one sentence

A user opens any real document in QUILL, runs a full accessibility audit in
place, hears the findings as a navigable spoken list, applies reviewable fixes,
and publishes clean accessible output, all by keyboard and voice, using exactly
the same rules that the GLOW desktop and web apps use.

## 2. The three repositories and their roles

Tier 3 spans up to three separate repositories. Each is committed on its own, and
the shared API between them is kept stable so they can move independently.

| Repo | Path | Role in the suite |
| --- | --- | --- |
| QUILL | this repo | The presentation layer. In-editor reports, the editor shell, onboarding, keyboard and screen-reader surfaces. Consumes the shared core. |
| quill-glow-core | `s:\code\quill-glow-core` | The shared contract. A stable host-facing API that both QUILL and the GLOW apps call. Package `quill_glow_core`, public API in `src/quill_glow_core/services.py`. |
| glow | `s:\code\glow` | The rule engine. The canonical accessibility engine (`acb_large_print_core`) plus the GLOW desktop and web apps. |

Important: `s:\code\glow-7.0.0` is a stale snapshot. It is ignored entirely. Do
not read it and do not modify it.

The boundary is deliberately clean: shared rules and fixers live in
`quill-glow-core`, and three thin presentation layers sit on top (QUILL in-editor,
GLOW desktop, GLOW web). QUILL never absorbs GLOW's web app, its branding-profile
deployment machinery, or its template-generation server flows.

## 3. The shared contract (quill-glow-core)

The shared library already exposes a stable host-facing API. QUILL calls into it
rather than reimplementing rules:

- `configure_default_services`: set up the engine and its fallbacks.
- `audit_by_extension`: audit a document, dispatched by file type.
- `fix_by_extension`: apply fixes, dispatched by file type.
- `convert_to_markdown`: the conversion entry point.
- `get_component_versions`: report which engine and rule version is active.
- `from_glow_backend`: bridge that wires the shared core to the canonical
  engine `acb_large_print_core`.

The dispatch core has two backends behind it:

- The GLOW backend, present when the optional dependency is installed, gives
  QUILL the full ACB Large Print, APH, WCAG 2.2 AA, and Microsoft Accessibility
  Checker rule sets across Word, Excel, PowerPoint, PDF, EPUB, HTML, and
  Markdown.
- A safe no-op fallback (`NoOpCoreServices`), used when the backend is absent,
  keeps QUILL fully functional with its existing text-level behavior and no
  crash.

## 4. The current QUILL surface that Tier 3 replaces

QUILL already contains `quill/core/glow.py`, a text-level GLOW audit and fix
surface: generic link-text detection, plain-language lint, and audit and fix
reports for the selection or document, wired to commands such as
`tools.glow_fix_document` and `tools.glow_fix_selection`. Tier 3 keeps these
friendly in-editor reports as the presentation layer and routes the actual rule
checking and fixing through the shared core instead of the bespoke checks.

## 5. The ordered plan

### Step 0 (prerequisite, part of GLOW-1): get the glow repo green

Before QUILL depends on `quill-glow-core`, the `glow` repo must build green.

- The consumed desktop core (`acb_large_print` / `acb_large_print_core`, the
  target of `from_glow_backend`) is already green at 308 tests.
- The failing part is the Flask web suite (`acb_large_print_web`): the `/guide/`
  content string, branding injection, and form-POST tests.
- Reconcile the version sweep (VERSION 8.0.0 against README against TODO.md).
- Commit the fix in the `glow` repo so the whole engine is green, so QUILL
  builds on a stable engine rather than inheriting breakage.

### Step 1 (GLOW-1): adopt quill-glow-core as the shared engine

- Add a new optional extra to QUILL: `glow = ["quill-glow-core[glow]"]`.
- QUILL audits and fixes via `quill-glow-core`, using the GLOW backend when
  present and the `NoOpCoreServices` fallback when absent.
- `quill/core/glow.py` becomes a thin presentation shim plus a
  `_glow_finding_to_quill` adapter. The adapter maps GLOW severities
  (critical and high) to QUILL's `error` level and carries `score`, `grade`,
  and ACB `metadata` through to the report.
- In-editor reports are unchanged for users.
- Tests cover both the backend path and the fallback path.

Status (QUILL side, done): the optional `glow` extra is declared, and
`quill/core/glow.py` gained a file-based seam — `audit_file`/`fix_file`,
`get_glow_services`, `glow_backend_available`, and the `_glow_finding_to_quill`
adapter (critical/high -> `error`, medium-band -> `warning`, low -> `info`;
`score`/`grade` carried on `GlowFileAuditResult`, ACB `metadata` and location
folded into the suggestion). The existing in-editor text reports
(`audit_text`/`fix_text`/`build_audit_report`) are untouched, and
`tests/unit/core/test_glow_backend.py` exercises both the backend and the
fallback paths. `quill_glow_core` is registered in the mypy ignore-missing list
so the scoped strict gate stays green. Remaining for GLOW-1: complete and verify
Step 0 in the `glow` repo (green Flask web suite + version reconciliation).

### Step 2 (GLOW-2, with IO-1): audit and fix by structure, not just text

- Today QUILL audits plain text, Markdown, and HTML.
- Extend it through the shared core to audit and, where supported, fix the
  structured formats QUILL already reads: DOCX, PPTX, XLSX, PDF, and EPUB.
- A user can open a real document and run a full accessibility audit in place.

### Step 3 (GLOW-3, with AGENT-1 and AI-7): the in-editor report that reads beautifully

- Present GLOW findings as a navigable, screen-reader-pageable list grouped by
  severity.
- Each finding has a one-key jump to its location, a plain-language
  explanation, and, where fixable, a reviewable apply-and-undo.
- This is the same surface the Accessibility agent (AGENT-1) drives later.

### Step 4 (GLOW-4, with SET-1): standards profiles as a setting

- Surface GLOW's profiles (ACB 2025 Baseline, APH Submission, Combined Strict)
  as a QUILL setting.
- The active profile is shown in every report for traceable evidence.

### Step 5 (GLOW-5, realizing FEAT-17): one-key accessible publish

- Reuse GLOW's conversion chain (MarkItDown plus Pandoc, with
  LibreOffice-assisted pre-conversion and PyMuPDF table preservation).
- QUILL exports clean, accessible Word, HTML, EPUB, and PDF with announced
  results.

### Step 6 (GLOW-6): show the active engine and rule version

- Use `get_component_versions` and the startup telemetry so QUILL can display
  which accessibility engine and rule version is active.
- Surface it in `diagnostics.py` and the About dialog, keeping the honesty
  principle.

Status: Done. `quill/core/glow.py` adds `GlowEngineVersions`,
`glow_engine_versions()` (reads the backend name and `get_component_versions`,
sorts components, never raises), and `glow_engine_version_summary()`. The
diagnostics environment info carries a `glow_engine` key through a
try/except-wrapped `_safe_glow_engine_summary()`, and the About dialog shows the
same summary. Verified against the live backend (release 8.0.0); the fallback
yields "GLOW engine: not installed" when the backend is absent. Covered by
`tests/unit/core/test_glow_backend.py`.

### Step 7 (GLOW-7): consent gate for optional AI and network features

- GLOW's optional networked features (AI alt-text generation, Presidio PII
  redaction, WCAG language processing) are off by default.
- When a user enables one, it is gated by an explicit per-action consent prompt
  with visible progress and outcome, honoring QUILL's no-silent-network rule and
  the GATE-9 egress audit.
- A test asserts the defaults are off and that no GLOW path performs a silent
  outbound call.

Status: In progress. The core contract and consent UI are done — the
`GlowNetworkConsent` model (all three features off by default), consent-gated
`audit_file`/`fix_file`, the Settings flags (`glow_enabled` on by default plus
the three consent flags off), the "GLOW Accessibility" Preferences entry, and
the Startup Wizard GLOW step (both sanctioned `web` surfaces). Remaining: the
per-action consent prompt at audit time, which lands with the in-editor report
(GLOW-3).

## 6. How Tier 3 connects to the rest of QUILL

- Watch Profiles (Tier 2): once GLOW lands, WATCH-8 registers an "audit and fix
  accessibility" watch action through the WATCH-2 registry, so a watched folder
  of documents is audited and fixed automatically against a chosen standards
  profile, reversibly, with findings surfaced in the queue outcome. Until GLOW
  is present, the action advertises itself as unavailable with an announced
  reason.
- Feature flags: the GLOW capability gets a feature id (`core.glow`) and honors
  `FeatureManager`. When the feature is off, its commands, the watch action, and
  its menu entries disappear in lockstep, and no GLOW path runs.
- The Accessibility agent (Tier 2 flagship, AGENT-1): drives the same GLOW-3
  report surface to make documents accessible step by step, reversibly, by
  keyboard and voice.

## 7. What stays out of QUILL

QUILL consumes the shared core. It does not absorb:

- GLOW's web application.
- GLOW's branding-profile deployment machinery.
- GLOW's template-generation server flows.

The GLOW desktop and web apps remain the heavyweight authoring and batch
surfaces. QUILL is the in-editor accessibility home.

## 8. Acceptance and definition of done

Tier 3 is done when:

- The `glow` repo is green and committed (Step 0).
- QUILL audits and fixes through `quill-glow-core` with both backend and
  fallback paths tested (GLOW-1).
- Structured formats audit in place (GLOW-2).
- The report is a navigable, spoken, reviewable surface (GLOW-3).
- Standards profiles are selectable and shown in every report (GLOW-4).
- One-key accessible publish works with announced results (GLOW-5).
- The active engine and rule version are visible (GLOW-6).
- Optional networked features are off by default and consent-gated, with a test
  proving no silent egress (GLOW-7).
- Every change is committed in its own repo and the shared API stays stable.

## 9. Risks and how the plan handles them

- Cross-repo breakage: the shared API is kept stable and each repo is committed
  independently, so a change in the rule engine does not silently break QUILL.
- Missing backend: the `NoOpCoreServices` fallback keeps QUILL fully functional
  when the GLOW backend is not installed.
- Silent network calls: GLOW-7 plus the GATE-9 egress audit make any outbound
  call explicit, consented, and tested.
- Inheriting a red engine: Step 0 requires the `glow` repo to be green before
  QUILL depends on it.

## Maintenance note

Keep this document in step with the GLOW backlog rows in `ROADMAP.md`. When a
GLOW item changes scope or status, update both this file and `ROADMAP.md` in the
same change.
