# QUILL Menu Bar — Definitive Consolidation Plan

> **Status:** Implemented — Phases 1–4 shipped (top level reduced 12 → 10;
> AI/BITS demoted; Find/Replace folded into Edit; Tools flattened and EdSharp
> recirculated/renamed to Power Tools). Phase 5 (menus-as-data) remains future
> work. See §5 for the per-phase ledger.
> **Scope:** The top-level menu bar and its nesting in `quill/ui/main_frame_menu.py`.
> **Goal:** Cut top-level menu sprawl, cap nesting depth, and bring the shipped
> menu bar back into conformance with **PRD §5.1a "The magical menu bar"** —
> without hiding a single command.
>
> This is the menu companion to `dialogs.md`. `dialogs.md` governs dialog
> surfaces; this file governs the menu bar shape. Both are screen-reader-first
> contracts.

---

## 0. TL;DR

The shipped bar has **12 top-level menus**; the PRD specifies **10** and does
**not** list a top-level **AI** or **BITS Whisperer** menu. The implementation
drifted from its own spec, the order is non-standard, and `Tools` has grown into
a 3-level-deep dumping ground. The fix is **reconcile to the PRD, then tighten**:

- **Reduce** top-level menus from **12 → 10** (default), in a conventional order.
- **Demote** `AI` and `BITS Whisperer` out of the top level (PRD does not grant
  them top-level status); fold them into `Tools` (with an opt-in promotion path
  for `AI` when the AI profile is active).
- **Cap nesting at 2 levels** in the writing path; flatten the three 3-level
  `Tools` chains.
- **De-duplicate** `Search` against `Edit` (Find/Replace are already the
  `edit.find` / `edit.replace` commands).
- **Relocate settings-like toggles** out of `View` into Settings (precedent:
  Tools toggles already moved to the registry-driven Settings).
- Do all of this **on top of the existing `quill.core.menu_customization` model
  and post-build transform** — no new machinery for Phases 1–4.
- **Never hide a command.** Every command stays reachable via menu **and** the
  command palette **and** the Keymap Editor (PRD §5.1a: "No menu item is
  hidden").

---

## 1. The problem, grounded in the code

### 1.1 Twelve top-level menus (bar order)

Source: `menu_bar.Append(...)` calls in `quill/ui/main_frame_menu.py`.

| # | Menu | `Append` line | Direct items | Submenus |
|---|------|---------------|--------------|----------|
| 1 | **File** | 73 | 13 | Open Recent, Workspace Snapshots |
| 2 | **Edit** | 208 | 10 | Selection (→ Recent Marks Ring) |
| 3 | **Insert** | 210 | 8 | Heading, List |
| 4 | **View** | 342 | 15 | Dirty Title Style |
| 5 | **Search** | 343 | 7 | — |
| 6 | **AI** (`A&I`) | 1039 | 18 | Speech |
| 7 | **BITS Whisperer** *(conditional)* | 1143 | 2 | Dictation/Watch, Speech Models, Providers, Rollout |
| 8 | **Navigate** | 1293 | 18 | — |
| 9 | **Format** | 1294 | 11 | Change Case |
| 10 | **Tools** | 1295 | 1 | 12+ submenus (see §1.3) |
| 11 | **Window** | 1374 | 3 | — |
| 12 | **Help** | 1375 | 13 | Feature Profiles |

Conventional Windows desktop editors expose **~6–8** top-level menus
(File / Edit / View / Insert / Format / Tools / Window / Help). Twelve is a lot
of stops for a screen-reader user arrowing across the bar, and the ordering is
non-standard.

### 1.2 Divergence from PRD §5.1a (the spec we already wrote)

PRD §5.1a lists the intended top-level set as: **File, Edit, Search, View,
Navigate, Format, Insert, Tools, Window, Help** — **10 menus, with no top-level
AI and no top-level BITS Whisperer.** The shipped bar diverges:

- **Added** `AI` and `BITS Whisperer` as top-level menus (not in the spec).
- **Re-ordered** unconventionally: `Insert` appears before `View`; `Format`
  appears *after* `Navigate` (lines 1293–1295 append Navigate, Format, Tools
  late, after AI).
- **Grew** `Tools` beyond the PRD's clean 10-submenu taxonomy (EdSharp Tools,
  Quillins, Sticky Notes, Read Aloud → Announcement Backend added).

The plan's north star: **make the implementation match the PRD again, then go a
step further on ordering and depth.**

### 1.3 `Tools` is a 3-level-deep hub

`Tools` has one direct item and a forest of submenus:
Sticky Notes · Writing and Language · Read Aloud (→ Announcement Backend) ·
Integrations (→ Shell Integration) · Document Intake · Authoring & Automation
(→ GLOW, Macros, Convert) · Compare Documents · Accessibility · Support ·
Customize · EdSharp Tools · Quillins.

Three chains reach **three levels deep**, which is the worst case for
screen-reader navigation (more key presses, easy to lose place):

- `Tools → Read Aloud → Announcement Backend`
- `Tools → Integrations → Shell Integration`
- `Tools → Authoring & Automation → {GLOW, Macros, Convert}`
- `Tools → EdSharp Tools → {Insert, Lines, …}` (six sub-submenus; §3.7)

### 1.4 Oversized menus for linear review

Screen-reader users review a menu **linearly**, top to bottom. Menus that are
too long are hard to scan:

- `AI` — 18 items
- `Navigate` — 18 items
- `View` — 15 items
- `File` / `Help` — 13 items each

### 1.5 Redundancy and miscategorization

- **`Search` duplicates `Edit`.** `Search`'s Find/Replace entries invoke the
  `edit.find` and `edit.replace` commands (see lines 213–217). Find/Replace
  conventionally live in **Edit**; `Search` then only adds *Search/Replace in
  Files*.
- **`View` mixes Settings toggles with view actions.** `View` carries
  persistent-undo, spell-check-as-you-type, word-prediction, dark-mode, tray-mode
  toggles — these are preferences, not view actions. There is already a
  precedent for moving such toggles into the registry-driven Settings dialog
  (Tools menu toggles were migrated there).

---

## 2. Design principles (screen-reader-first)

1. **Predictability beats completeness at the top level.** NVDA / JAWS /
   Narrator users navigate by platform muscle memory. Match the Windows
   convention and order so the bar is *learnable*, not *exhaustive*.
2. **The palette is the exhaustive surface; the menu is the learnable surface.**
   Every menu item is already a palette command (PRD §5.1a). Discovery and power
   use happen in `Ctrl+Shift+P`; the menu bar optimizes for first-contact
   learnability.
3. **Shallow wins.** Cap nesting at **2 levels** in the writing path. Each extra
   level multiplies key presses and the chance of losing place.
4. **Never hide a command.** PRD §5.1a forbids hidden items. Consolidation
   **relocates**, it does not remove. Every command keeps a menu home **and**
   palette **and** keymap reachability. Disabled items stay visible with a
   tooltip.
5. **Unique mnemonics per menu.** Regrouping must preserve a unique accelerator
   letter for every item within its new parent menu.
6. **Defer menu mutations until the menu closes.** (Existing rule — avoid focus
   churn / native menu instability under rapid arrow navigation.)
7. **Feature-gating, not deletion.** Menus tied to optional features
   (AI, BITS Whisperer, GLOW) appear only when their feature profile is active,
   keeping a minimal profile's bar small.

---

## 3. Target menu bar

### 3.1 Default top-level set (10, conventional order)

```
File   Edit   View   Insert   Format   Navigate   Search   Tools   Window   Help
```

- **Down from 12 → 10** at the default profile (AI and BITS Whisperer demoted;
  see §3.2). This matches the PRD's intended count: `Window` is kept as its own
  top-level entry and `Search` is retained (reduced to in-files scope per §3.3)
  rather than folded into `Edit`.
- Order follows Windows convention: editing menus first (File/Edit), then
  viewing/structuring (View/Insert/Format/Navigate/Search), then
  Tools/Window/Help.
- `Format` moves up next to `Insert` (no longer appended late after `Navigate`).
- `Insert` moves after `View` (no longer before it).

### 3.2 Where AI and BITS Whisperer go

Per the PRD neither is a top-level menu. Recommended default:

- **AI → `Tools → AI Assistant` submenu.** Its 18 items regroup into a tidy
  submenu (e.g. *Ask / Rewrite / Summarize / Speech ▸ / Providers & Models / …*).
  **Opt-in promotion:** when the AI feature profile is active, the user may
  promote `AI` back to top-level via **Edit → Customize Menus** (the existing
  `MenuCustomization` reorder/show machinery already supports this). This
  respects AI as a flagship while keeping the default bar lean.
- **BITS Whisperer → `Tools` submenu**, consistently with the other optional
  tool families. It is already conditional; nesting it under `Tools` removes a
  top-level entry for users who do have it enabled.

> **Open decision (see §8):** if the product wants AI to remain top-level by
> default as a flagship, the plan still reduces to **10** (File, Edit, View,
> Insert, Format, Navigate, Search, AI, Tools, Help — folding Window into View;
> see §3.4). The recommended path is AI-under-Tools-by-default.

### 3.3 `Search` (option)

- **Recommended:** keep `Search` top-level (PRD lists it) but **move Find /
  Replace / Find Next / Find Previous / Find All Matches into `Edit`** (their
  conventional home), leaving `Search` as a focused **"in files"** menu:
  *Search in Files…*, *Replace Across Files…*. This de-duplicates and gives
  `Search` a clear, distinct identity.
- **Alternative (8 top-level):** fold `Search` entirely into `Edit` (Find group)
  and `Tools` (in-files group), dropping `Search` as a top-level menu.

### 3.4 `Window` (option)

`Window` has only 3 items. Optionally fold them into `View` (a "Window" group),
dropping another top-level entry. Kept separate in the §3.1 default for Windows
convention familiarity; folding it yields an **8-menu** bar.

### 3.5 `Tools`, flattened to ≤2 levels

Regroup `Tools` to the PRD §5.1a taxonomy and flatten the three 3-level chains:

- `Read Aloud`: keep the read-aloud actions; **move "Announcement Backend"
  picker into Settings** (it is a preference, not an action).
- `Integrations`: promote `Shell Integration` items to direct entries under
  `Integrations` (no third level).
- `Authoring and Automation`: split the 3-level group into **two 2-level
  submenus** — `Authoring` (GLOW, Convert) and `Automation` (Macros) — or
  promote GLOW/Macros/Convert to direct entries under a single
  `Authoring & Automation` submenu. Either way, **no third level**.
- `EdSharp Tools` is **renamed and recirculated** — see §3.7.
- `Quillins`, `Sticky Notes` remain `Tools` submenus (consistent with their
  current home).

### 3.7 `EdSharp Tools` — rename and recirculate (the centerpiece)

`Tools → EdSharp Tools` (built in `quill/ui/main_frame_edsharp_menu.py`,
attached at `main_frame_menu.py:1291`) is the clearest example of menu sprawl
done wrong:

- **The name leaks a foreign brand.** "EdSharp" is the name of *another* editor;
  it means nothing to a QUILL user and fails the discoverability test — a
  screen-reader user hears "EdSharp Tools submenu" and learns nothing about what
  is inside.
- **It is a 33-command monolith nested two levels deep**, with its own six
  sub-submenus (Insert, Lines, Compare Blocks, Find with Regex, Go, Speak) —
  reaching **three levels** (`Tools → EdSharp Tools → Insert → …`). That is the
  exact 3-level anti-pattern §1.3 calls out.
- **Most of its commands already have a natural home** elsewhere on the bar.

The fix is two moves: **recirculate** the commands that belong in conventional
menus, and **rename** the cohesive remainder.

#### 3.7.1 Recirculation map

Each EdSharp command keeps its `eds.*` id, palette entry, and Keymap-Editor
binding (nothing is lost); only its **menu home** changes.

| EdSharp group | Commands | New menu home |
|---------------|----------|---------------|
| Insert | special character, date/time, calculated date, file content | **Insert** menu |
| Line transforms | number lines, hard-wrap lines | **Format → Transform Lines** (consolidated — see §3.7.2) |
| Line deletion | delete to line start/end, to document top/bottom, delete paragraph | **Edit** menu |
| New from clipboard | new document from clipboard | **File** menu (next to New) |
| Paste variant | paste HTML as Markdown | **Edit** menu (paste group) |
| Regex find | count matches, extract matches | **Search** menu |
| Block set-ops | lines in first block only, lines common to both | **Search** menu (filter/extract by block membership) |
| Movement | go to percent, first non-blank, last non-blank | **Navigate** menu |
| Speak / status | cursor address, document status, selection length | **Tools → Accessibility** (screen-reader status queries) |
| File ops | run current file, open target at cursor, rename/delete current file | **File** menu |

Placement rationale for the four non-obvious moves:

- **Line transforms → `Format → Transform Lines`, not a standalone Format
  entry.** See §3.7.2 — this unifies them with the existing Convert group.
- **Block set-ops → `Search`, not Compare Documents.** "Lines in first block
  only / common to both" are *line filtering by block membership*, not document
  diffing; they sit naturally beside the regex find/extract commands, making
  `Search` the single "find / filter / extract lines" hub.
- **Speak/status → `Tools → Accessibility`, not Read Aloud.** These announce
  *cursor/selection/document status* to the screen reader; they are status
  queries, not text-to-speech of content.
- **Clipboard pair is split.** New-document-from-clipboard *creates a document*
  (File, next to New); paste-HTML-as-Markdown is a *paste variant* (Edit).

#### 3.7.2 Consolidation finding: one home for line/text transforms

EdSharp's line transforms (number lines, hard-wrap) overlap the **Convert**
group already shipped under `Tools → Authoring & Automation → Convert` (sort
ascending/descending, reverse, remove duplicates, trim trailing whitespace,
normalize whitespace, convert indentation to spaces/tabs). Two homes for the
same concept is exactly the miscategorization §1.5 warns about.

**Decision:** create a single **`Format → Transform Lines`** submenu and move
**both** sets into it — the EdSharp line transforms *and* the entire Convert
group. This removes a 3-level chain (`Tools → Authoring & Automation → Convert`),
empties most of `Authoring & Automation` toward just GLOW + Macros, and gives
users one obvious place for every line/text transform. It is a strict win for
discoverability and depth.

#### 3.7.3 The renamed remainder

What stays together is the cohesive set of **editor-behavior power toggles** with
no conventional home: read-only guard, clipboard collector, collect clipboard
now, key describer, indentation announcements, infer indentation. These are the
genuine "EdSharp-signature" behaviors and deserve one discoverable submenu.

- **Recommended name (clarity-first): `Power Tools`** — conventional, instantly
  discoverable ("a submenu of advanced utilities"), and brand-neutral.
- **Flagship alternative (on-brand, more magical): `Scribe's Toolkit`** —
  characterful and consistent with QUILL's "Literate" pillar, while "Toolkit"
  still signals *utilities inside*. (Avoid purely evocative names like
  "Scriptorium": for a screen-reader-first bar, the name must announce its
  function, not just its vibe.)

Final pick is an §8 open question; the implementation lands `Power Tools` and the
product owner may rename via **Edit → Customize Menus** (the `MenuCustomization`
rename lever already supports this with zero code).

#### 3.7.4 Why this is the model for the whole bar

EdSharp is the proof of the §2 principles in miniature: **relocate, never
remove**; **shallow wins** (kills a 3-level chain); **brand-neutral,
function-announcing names**; and **palette/keymap parity preserved**. It rides
the existing command table in `_edsharp_command_table()` (the single source of
truth for ids/labels/handlers), so the recirculation is pure menu wiring — the
commands, handlers, and tests for behavior are untouched. This is the template
every later consolidation follows.

Target `Tools` submenu set (matches PRD §5.1a + the shipped extras):
Writing and Language · Read Aloud · Dictation and Watch Folder Automation
(BITS Whisperer) · Integrations · Document Intake · Authoring and Automation ·
Compare Documents · Accessibility · Support · Customize · Power Tools
(renamed from EdSharp Tools — §3.7) · Quillins · AI Assistant · Sticky Notes.

### 3.6 `View`, de-cluttered

Move preference toggles (persistent undo, spell-check-as-you-type,
word-prediction, dark mode, tray mode, title-path mode, dirty-title style) into
the registry-driven **Settings** dialog, leaving `View` with genuine view
actions (previews, soft wrap, tab control, side-by-side, menu-bar visibility).
This shortens `View` from 15 items and gives toggles one consistent home — the
exact pattern already used for the former Tools toggles.

---

## 4. Enabling mechanism (the magical part)

The bar is currently built imperatively in one large method in
`main_frame_menu.py`. Two reshaping levers already exist:

1. **`quill.core.menu_customization.MenuCustomization`** — a wx-free model that
   can **reorder, show/hide, and rename** top-level menus and items, applied via
   a **post-build transform pass** that bails out untouched if the live bar
   looks unexpected (PRD §13 checklist item). Phases 1–2 (reorder, demote) ride
   this lever by changing the **default** key order/visibility — no new code.
2. **The contribution grammar** introduced for **Quillins** (`menus` /
   `commands` contributions; see `docs/scripting.md` and
   `docs/quillin-migration-plan.md`). Phase 5 extracts the first-party menu into
   a **declarative manifest** consumed by the same merge/registry the Quillins
   host uses, so first-party items and Quillin contributions share one model and
   one set of tests. This is the long-term "menus as data" endgame and the
   natural first beachhead for the Quillin migration playbook.

---

## 5. Phased migration

Phases 1–4 are **shipped on `main`** (commits `954e0b8`, `c525a4e`, `73567be`,
`8f83cfa`). Each phase was independently shippable, behind characterization
tests, and kept `tests/unit/ui/test_main_frame_menu_contract.py` and `dialogs.md`
green. Phase 5 remains future work.

| Phase | Change | Risk | Lever | Status |
|-------|--------|------|-------|--------|
| **1. Reorder** | Top-level order → §3.1 convention; `Format` up by `Insert`; `Insert` after `View`. Pure ordering. | Low | default order list | ✅ Shipped (`954e0b8`) |
| **2. Demote** | `AI` and `BITS Whisperer` → `Tools` submenus; AI promotable via Customize Menus when AI profile active. | Med | menu_customization + build | ✅ Shipped (`c525a4e`) |
| **3. De-dup / relocate** | Move Find/Replace into `Edit`; reduce `Search` to in-files; move `View` preference toggles → Settings. | Med | build + settings registry | ✅ Shipped (`73567be`) |
| **4. Flatten Tools** | Collapse the three 3-level chains to ≤2; regroup to PRD taxonomy; move Announcement Backend picker → Settings; **recirculate + rename EdSharp Tools (§3.7)**. | Med | build | ✅ Shipped (`8f83cfa`) |
| **5. Menus-as-data** | Extract first-party menu into a declarative manifest consumed by the Quillins contribution registry. | High | contribution grammar | ⏳ Future |

**Sequencing note:** Phases 1–4 deliver the entire user-visible improvement on
the existing machinery. Phase 5 is an internal refactor that unlocks the Quillin
migration and is optional for the usability win.

---

## 6. Guardrails / Done criteria

- **No command lost.** Add a test asserting the set of `command_id`s reachable
  from the menu bar is unchanged across each phase (commands relocate, never
  disappear). Cross-check menu ↔ palette ↔ keymap parity.
- **`test_main_frame_menu_contract.py` updated, not weakened.** The contract is
  re-baselined to the new structure with the same strictness.
- **Dialog reachability intact.** Every dialog in `dialogs.md` still opens from
  its documented menu path; update `dialogs.md` rows whose menu path changed.
- **Mnemonics unique** within every (re)grouped menu.
- **Nesting ≤ 2 levels** in the writing path (verify no 3-level chains remain).
- **Feature-gating respected.** Minimal profile shows the small bar; optional
  menus appear only with their profile.
- **Accessibility pass.** Manual NVDA / JAWS / Narrator sweep of the new bar:
  arrow across all top-levels, into every submenu, confirm announcements and
  that no menu mutates while open.
- **PRD reconciled.** Update PRD §5.1a to the final shipped structure and
  regenerate `docs/QUILL-PRD.html` / `.epub` (pandoc) if the structure changes
  the spec text.

---

## 7. Before / after (at a glance)

```
BEFORE (12, non-standard order):
  File Edit Insert View Search AI [BITS] Navigate Format Tools Window Help

AFTER  (10, conventional order; AI/BITS nested under Tools):
  File Edit View Insert Format Navigate Search Tools Window Help
        ^Find/Replace        ^in-files only   ^AI Assistant, BITS,
                                               EdSharp, Quillins, … (≤2 deep)
```

---

## 8. Open questions for the product owner

1. **AI placement.** Default to `Tools → AI Assistant` (recommended, matches
   PRD), or keep `AI` top-level as a flagship by default? Either way the bar
   shrinks; this only changes whether the default count is 9 or 10.
2. **`Search` fate.** Keep as an "in files" top-level menu (recommended), or
   fold entirely into `Edit` + `Tools` for an 8-menu bar?
3. **`Window` fate.** Keep separate for Windows familiarity (default), or fold
   its 3 items into `View` for one fewer top-level?
4. **Feature-profile gating.** Should optional menus be hidden entirely under a
   minimal profile, or shown-but-disabled with an explanatory tooltip (PRD's
   "disabled items remain visible" stance)?
5. **`Power Tools` name.** Ship `Power Tools` (clarity-first, recommended) or the
   on-brand `Scribe's Toolkit` for the renamed EdSharp remainder (§3.7.3)?

---

## 9. Files this plan touches

- `quill/ui/main_frame_menu.py` — menu construction (all phases).
- `quill/ui/main_frame_edsharp_menu.py` — EdSharp recirculation + rename (§3.7).
- `quill/core/menu_customization.py` — default order/visibility (Phases 1–2).
- `quill/core/settings_registry.py` + Settings dialog — relocated toggles
  (Phases 3–4).
- `tests/unit/ui/test_main_frame_menu_contract.py` — re-baselined contract.
- `dialogs.md` — updated menu paths for any moved dialog.
- `docs/QUILL-PRD.md` (+ `.html` / `.epub`) — §5.1a reconciliation.
- (Phase 5) the Quillins contribution registry + `docs/quillin-migration-plan.md`
  — first-party menu manifest.
