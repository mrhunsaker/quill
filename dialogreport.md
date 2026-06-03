# QUILL Dialog Estate Report (DLG-3)

_Last updated: 2026-06-04_

This report is the human-readable companion to the machine-enforced dialog
governance described in **PRD §9.13 (Dialog estate governance)** and tracked in
`golden.md` as DLG-3.0 through DLG-3.8. It records where the dialog-unification
work stands after the triage and Phase 3 hardening pass.

## Headline

- **154** dialog surfaces inventoried across `quill/**/*.py`.
- Classification: **100 native**, **49 hardened_custom**, **5 web**.
- Triage of all 49 `hardened_custom` surfaces: **0 convert / 48 harden / 1 keep-web**.
- **All 49** `hardened_custom` dialogs now wire the shared `dialog_contract`
  (`apply_modal_ids` + an accessible show path), enforced by a new AST guard.

## How the estate is governed

| Mechanism | File | Role |
| --- | --- | --- |
| Source-generated inventory | `quill/tools/dialog_inventory.py` | AST-scans every `wx.Dialog(...)`, stock wx dialog, and `show_web_form(...)`; assigns a stable key `<module>::<enclosing_qualname>::<kind>` and a sanctioned classification. |
| Committed snapshot | `tests/unit/ui/fixtures/dialog_inventory.json` | The source of truth; CI fails if the live scan disagrees. |
| Inventory gate | `tests/unit/ui/test_dialog_inventory.py` | Fails on any new, moved, removed, or reclassified surface. |
| Banned-pattern gate | `quill/tools/check_banned_patterns.py` | Cross-checks every surface against the snapshot; fails on unregistered/misclassified dialogs (Security CI). |
| Shared contract helpers | `quill/ui/dialog_contract.py` | `apply_modal_ids(...)` (affirmative/escape IDs) and `show_modal_dialog(...)` (region + announcement hooks). |
| **Hardening guard (new)** | `tests/unit/ui/test_dialog_hardening_contract.py` | AST-asserts every `hardened_custom` surface wires `apply_modal_ids` + an accessible show/`ShowModal`/`Show` path. Blocks future drift at author time. |

## Triage outcome

A live audit on the Windows wx 4.2.5 (Phoenix, wxWidgets 3.2.9) runtime, plus a
source scan for custom-drawn paint code
(`EVT_PAINT` / `wx.lib.agw` / `OnPaint` / `wx.PaintDC` / owner-draw / `wx.html2`),
returned **zero** custom-drawn dialogs. Every `hardened_custom` surface is already
a stock-widget `wx.Dialog` container (ListBox, TextCtrl, SearchCtrl, TreeCtrl,
multi-action button rows). "Convert to native" is therefore, in the literal wx
sense, already true — the genuine work is **contract hardening**, not rewrites.

| Bucket | Count | Meaning |
| --- | --- | --- |
| Convert (flatten to a stock one-shot) | **0** | No dialog is a lossless single confirm/choice/text entry; flattening any would drop live search, lists, previews, or multi-action rows. |
| Harden (enhanced-native onto one contract) | **48** | Genuinely multi-control native dialogs that converge on one focus/default/lifecycle grammar via `dialog_contract`. |
| Keep web | **1** | `AskQuillChatDialog` (rich streaming chat surface) stays on the sanctioned web surface. |

## Phase status

| Phase | Item | Status | Notes |
| --- | --- | --- | --- |
| 0 | Source-generated registry + gates | **Done** | Inventory engine + snapshot + two gates shipped. |
| 1 | Strengthened A11Y-4 dialog-contract guard | **Done** | `_check_dialog_registry` + Dialog Excellence Mandates. |
| T | Triage all 49 `hardened_custom` dialogs | **Done** | 0 convert / 48 harden / 1 keep-web. |
| 2 | Native conversion wave (flatten to one-shot) | **Done (no applicable work)** | Triage found zero lossless conversion candidates; honest no-op. |
| 3 | Enhanced-native contract standardization | **Done** | All 49 wire the shared contract; new AST guard prevents drift. |
| 4 | Web-surface standardization | **Todo** | Confirm the 5 web surfaces have native-fallback parity and no raw HTML in onboarding tabs. |
| 5 | Startup/onboarding hardening | **Todo** | Deterministic focus across chained startup modals; consent preserved. |
| 6 | Assistant/AI dialog consolidation (folds DLG-2) | **Todo** | `assistant_tools.py`/`ai_model_panel.py`/`style_panel.py`/`assistant_panel.py` async/"busy" semantics. |
| 7 | CQ-16 characterization around dialog-launch paths | **Todo** | Return-value/side-effect regression tests before any CQ-1 split. |
| 8 | Manual NVDA/JAWS/Narrator SR pass | **Todo** | Requires a live Windows screen-reader runtime; cannot be machine-verified. |

## Phase 3 — what changed

A machine-derived AST audit of every `hardened_custom` scope found **5** surfaces
that did not fully wire the shared contract. Four were brought onto it; the fifth
was already correct.

| Dialog | Module | Action |
| --- | --- | --- |
| `_present_quill_key_help` | `quill/ui/main_frame.py` | Added `apply_modal_ids(ID_OK, ID_OK)`; routed direct `ShowModal()` through `_show_modal_dialog` (adds region/announce hooks). |
| `_offer_crash_recovery` | `quill/ui/main_frame.py` | Added `apply_modal_ids(ID_YES, ID_NO)` alongside existing `SetDefaultItem`/`SetEscapeId`. |
| `_present_quick_nav` | `quill/ui/main_frame.py` | Added `apply_modal_ids(ID_OK, ID_CANCEL)`; routed direct `ShowModal()` through `_show_modal_dialog`. |
| `_choose_searchable_option` | `quill/ui/main_frame.py` | Added `apply_modal_ids(ID_OK, ID_CANCEL)` + deterministic `search.SetFocus()`. |
| `show_watch_folder_status` | `quill/ui/main_frame.py` | No change — correctly-hardened **modeless** monitor (`Show()` + `EVT_CLOSE` → `Destroy`); the contract audit's "missing show" was a false positive for modeless windows. |

No dialog was flattened; live search, lists, and preview panes are preserved.

## Tests and validation

- `tests/unit/ui/test_dialog_hardening_contract.py` — new durable guard (2 tests).
- `tests/unit/ui/test_dialog_contract.py`, `test_dialog_inventory.py` — green.
- `tests/unit/ui/test_main_frame_navigation.py`, `test_main_frame_quill_key.py`,
  `test_main_frame_share_dialogs.py` — 113 passed (exercise the edited methods).
- `ruff format` + `ruff check` — clean.
- Banned-pattern gate — no violations.
- Dialog inventory — unchanged at 154 surfaces (100/49/5); no reclassification.

## Honest remaining work

- **Phases 4–7** are real engineering still to do (web parity, startup focus
  chains, assistant/AI async semantics, CQ-16 characterization).
- **Phase 8** is a manual NVDA/JAWS/Narrator pass that **cannot** be
  machine-verified; it needs a human tester on a live Windows screen-reader
  runtime, with each `dialogs.md` row carrying pass/fail evidence.
