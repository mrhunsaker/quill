# QUILL Menu Bar — Definitive Consolidation Plan

> **Status:** Plan / not yet executed.
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

- **Reduce** top-level menus from **12 → 9** (default), in a conventional order.
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

### 3.1 Default top-level set (9, conventional order)

```
File   Edit   View   Insert   Format   Navigate   Search   Tools   Window   Help
```

- **Down from 12 → 9** at the default profile (AI and BITS Whisperer demoted;
  see §3.2). This is the PRD's 10 minus a top-level `Search` split-out folded
  back toward `Edit` per §3.3 — see the option there.
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
- `EdSharp Tools`, `Quillins`, `Sticky Notes` remain `Tools` submenus
  (consistent with their current home).

Target `Tools` submenu set (matches PRD §5.1a + the shipped extras):
Writing and Language · Read Aloud · Dictation and Watch Folder Automation
(BITS Whisperer) · Integrations · Document Intake · Authoring and Automation ·
Compare Documents · Accessibility · Support · Customize · EdSharp Tools ·
Quillins · AI Assistant · Sticky Notes.

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

Each phase is independently shippable, behind characterization tests, and must
keep `tests/unit/ui/test_main_frame_menu_contract.py` and `dialogs.md` green.

| Phase | Change | Risk | Lever |
|-------|--------|------|-------|
| **1. Reorder** | Top-level order → §3.1 convention; `Format` up by `Insert`; `Insert` after `View`. Pure ordering. | Low | default order list |
| **2. Demote** | `AI` and `BITS Whisperer` → `Tools` submenus; AI promotable via Customize Menus when AI profile active. | Med | menu_customization + build |
| **3. De-dup / relocate** | Move Find/Replace into `Edit`; reduce `Search` to in-files; move `View` preference toggles → Settings. | Med | build + settings registry |
| **4. Flatten Tools** | Collapse the three 3-level chains to ≤2; regroup to PRD taxonomy; move Announcement Backend picker → Settings. | Med | build |
| **5. Menus-as-data** | Extract first-party menu into a declarative manifest consumed by the Quillins contribution registry. | High | contribution grammar |

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

AFTER  (9, conventional order; AI/BITS nested under Tools):
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

---

## 9. Files this plan touches

- `quill/ui/main_frame_menu.py` — menu construction (all phases).
- `quill/core/menu_customization.py` — default order/visibility (Phases 1–2).
- `quill/core/settings_registry.py` + Settings dialog — relocated toggles
  (Phases 3–4).
- `tests/unit/ui/test_main_frame_menu_contract.py` — re-baselined contract.
- `dialogs.md` — updated menu paths for any moved dialog.
- `docs/QUILL-PRD.md` (+ `.html` / `.epub`) — §5.1a reconciliation.
- (Phase 5) the Quillins contribution registry + `docs/quillin-migration-plan.md`
  — first-party menu manifest.
