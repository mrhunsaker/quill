# Converting QUILL features into bundled Quillins — a flexibility proof

Status: **Proposed roadmap (2.0-scale, demonstration- and maintainability-driven)**
· Companion to `docs/scripting.md` (esp. §6 security, §16 modularization) and
`docs/quillin-migration-plan.md` · Sample artifact:
[`examples/quillins/markdown-helpers/`](../examples/quillins/markdown-helpers/)

> **This is the bolder sibling of `docs/quillin-migration-plan.md`.** That plan
> moves built-in features onto the contribution *grammar* but keeps them
> **trusted and in-process** (the rich `Host` facade). This roadmap takes the
> step that actually *proves the platform*: re-express a curated set of real
> QUILL features as **genuine Quillins** — `register(api)`, out-of-process,
> capability-gated — ship them **bundled and enabled**, and **delete their
> implementation from core**. If QUILL can host its own features through the same
> narrow door it offers strangers, the extension platform is real, not a brochure.

## 1. What this proves, and why it is worth doing

The Quillins framework is fully built and tested (`quill/core/quillins/*`), but
in QUILL 1.0 it runs **zero** real extensions: third-party execution is locked
off (SEC-8) and every shipping feature lives in core/UI Python. The framework is
therefore proven only by its own unit/integration tests and one worked example
([`examples/quillins/markdown-helpers/`](../examples/quillins/markdown-helpers/)).

Converting real features into Quillins delivers three things a test suite cannot:

1. **A flexibility proof.** Exercising the contribution grammar, capability
   catalogue, consent gate, out-of-process isolation, and packaging against
   *features users already rely on* shows the platform can carry production
   weight — the strongest possible signal to third-party authors.
2. **A smaller core.** Each converted feature's algorithm, tests, menu wiring,
   and handler leave `quill/core`/`quill/ui`. The god object
   (`quill/ui/main_frame.py`) shrinks and `quill/core` keeps only what other core
   code still needs.
3. **A living dogfood.** Bundled Quillins are run on every launch, so the
   framework's hot paths stay exercised and honest rather than dormant behind a
   locked flag.

This is a **demonstration + maintainability** effort. It adds no user-facing
capability (the features already exist), so it is sequenced **after** 1.0
user-facing work and proceeds opportunistically — every step leaves the suite
green and the accessibility contract intact, or it does not land.

## 2. Three trust tiers (read this before proposing any conversion)

The migration plan established two tiers; this roadmap needs a third. Keeping
them straight is the whole game.

```
  Tier A — CORE GUARDRAILS            Tier B — FIRST-PARTY MODULES        Tier C — BUNDLED QUILLINS
  editor surface, announcement        register(host): trusted,            register(api): trusted-AUTHOR but
  engine, lifecycle, registry         in-process, rich Host facade        run through the SAME sandboxed,
  (never pluginized — §2 of           (quillin-migration-plan.md)         out-of-process, capability-gated
  migration plan)                                                         path as third-party Quillins
       │                                     │                                     │
       └─────────── one contribution grammar / one registry / one keymap ─────────┘
```

- **Tier A — core guardrails.** Unchanged from `quillin-migration-plan.md` §2:
  the `wx.TextCtrl` editor surface, the NVDA/JAWS/Narrator announcement engine,
  app lifecycle/frame construction, and the contribution registry/keymap itself.
  These are never converted.
- **Tier B — first-party in-process modules.** The subject of
  `quillin-migration-plan.md`. Trusted code, no sandbox, rich facade, sub-ms
  latency. The right home for anything latency-sensitive or wx-bound that is
  still command-shaped.
- **Tier C — bundled Quillins (NEW, this roadmap).** Real Quillins authored by
  the QUILL project, shipped *inside* the install tree, and enabled by a
  **separate trusted mechanism** — they are **not** discovered from
  `%APPDATA%\Quill\extensions\` and are therefore **unaffected by the SEC-8
  third-party lock**. They run through the identical out-of-process, capability,
  and consent machinery as third-party code, which is exactly why they are a
  valid proof of it.

> **Non-negotiable boundary (restated from `scripting.md` §16.1).** Tier B exists
> precisely so trusted per-keystroke built-ins are *not* forced across an RPC
> bridge. Tier C is for features where the out-of-process round-trip is
> acceptable (on-demand, not per-keystroke) **and** the whole point is to demo the
> extension path. Converting a hot-path feature to Tier C to "be pure" would wreck
> latency for zero gain — that belongs in Tier B.

## 3. The enabling work the platform needs first (honest prerequisites)

Tier C does not exist yet. Wave 0 builds it. None of this weakens SEC-8.

| Prerequisite | What it is | Where it touches |
| --- | --- | --- |
| **Bundled-extensions root** | A read-only `extensions/` directory staged *inside* the install tree, discovered separately from the per-user `%APPDATA%` root. | New branch in `quill/core/quillins/loader.py` (`bundled_extensions_root()` alongside `extensions_root()`), path-contained like today. |
| **Trusted-enable path** | Bundled Quillins ship **enabled** without the `core.third_party_plugins` flag (which stays `locked_off`). A distinct, on-by-default `core.bundled_quillins` gate, or an explicit bundled-manifest allowlist. | `quill/core/quillins/loader.py` discovery gate; `quill/core/features.py` feature definition. |
| **Worker imports its own modules** | A bundled Quillin may ship pure-Python helpers next to `extension.py` and import them. | Already supported — `host_worker.py` loads `main` and sibling files within the path-contained extension dir. Confirm + test. |
| **Capability pre-grant for trusted authors** | Bundled Quillins still *declare* capabilities and still hit the **consent gate** for `fs.*`/`net` (the proof must be real); non-consent-gated caps (`editor.*`, `ui.*`, `clipboard.*`) may be pre-granted so a shipped feature does not nag on first use. | `loader.grant_capabilities` seeded for bundled ids; consent path unchanged. |
| **Packaging** | The installer stages the bundled `extensions/` tree and registers it as a component. | `scripts/build_windows_distribution.py`, `installer/quill.iss`. |
| **Latency budget** | Measure cold-load + warm-invoke round-trip for an on-demand command; set a published budget (e.g. warm invoke < 50 ms) below which Tier C is acceptable. | New perf test under `tests/perf`. |

**Wave 0 exit criterion:** the existing `examples/quillins/markdown-helpers`
sample, promoted to a bundled Quillin, ships enabled in a build, appears in
**Tools ▸ Quillins Manager**, and runs end-to-end — with the third-party flag
still `locked_off`.

## 4. Candidate selection — what can become a Quillin

A feature is a Tier C candidate iff **all** hold:

- **Command-shaped:** stable id, title, handler, optional menu/hotkey/context.
- **Capability-expressible:** its effect is reachable through the catalogue
  (`editor.read/write`, `ui.announce/command`, `clipboard.read/write`, and —
  consent-gated — `fs.read/write`, `net`). If it needs anything outside that
  catalogue, it cannot be a Quillin by construction.
- **No `wx`, no platform API, no tight editor/selection-state coupling.** Pure
  logic over text/clipboard/files.
- **Latency-tolerant:** invoked on demand, never on every keystroke.
- **Deterministic & characterization-testable** before the move.

### Candidate catalogue (grounded in today's code)

| Feature(s) | Current home | Verdict | Target |
| --- | --- | --- | --- |
| Line transforms: number lines, hard-wrap | `quill/ui/features/line_transforms.py` (already Tier B) | ✅ Strong — pure text, already extracted | Tier C "Text Tools" |
| `set_lines_first_not_second`, `set_lines_common` | `quill/ui/main_frame_edsharp.py` | ✅ Strong — pure set algebra over two buffers | Tier C "Text Tools" |
| `count_regex_matches`, `extract_regex_matches` | `quill/ui/main_frame_edsharp.py` | ✅ Good — pure regex over text (uses `regex`, a runtime dep the worker can ship) | Tier C "Text Tools" |
| HTML-clipboard → Markdown paste | `quill/core/html_to_markdown.py` + `paste_html_as_markdown` | ✅ Good — pure transform + `clipboard.read`; helper vendored into the Quillin | Tier C "Markdown Tools" |
| Insert date/time, calculate-and-insert-date | `insert_date_time`, `calculate_and_insert_date` | ✅ Good — Layer 1 snippet (`${date}`/`${time}`) or a small handler, no caps / `editor.write` | Tier C "Insert Tools" |
| Front-matter / boilerplate snippets | sample Quillin | ✅ Already a Layer 1 Quillin (the worked example) | Tier C (ship it) |
| Read-only guard, `speak_*`, key describer, indent announce | `quill/ui/main_frame_edsharp.py` | ❌ No — announcement-engine / wx / live-event coupled (Tier A/B) | Stay core |
| `run_current_file`, `run_target_at_cursor`, file rename/delete | `quill/ui/main_frame_edsharp.py` | ❌ No — process execution / shell / filesystem beyond the consent model's intent | Stay core |
| Dictation, OCR, AI assistant, watch folders, sticky-notes UI, spell-check | various `quill/ui`, `quill/platform` | ❌ No — wx UI, platform bindings, background services, or models | Stay core |

The pattern is clear: **the EdSharp-parity text transforms are the ideal proving
ground** — many are already pure functions or one mixin method away from it, and
several already passed through Tier B (`line_transforms.py`), so the path from
inline → Tier B → Tier C is a graded, low-risk ramp.

## 5. The conversion procedure (per feature, strangler-fig)

Mirrors `quillin-migration-plan.md` §5/§8 but the target is the **Quillin path**,
and the algorithm **moves out of core** rather than staying behind a facade.

1. **Pin behavior first.** Add/extend a characterization test asserting the
   feature's current observable behavior (handler output for representative
   input, announcement text, menu/hotkey placement). For an already-extracted
   helper, the existing core test is the baseline.
2. **Author the bundled Quillin.** Create
   `quill/quillins_bundled/<name>/` (or the chosen install-tree home) with a
   `manifest.json` (`quill.extension/1`, `ext.*` ids, declared capabilities) and
   `extension.py`. **Vendor the pure algorithm into the Quillin** — move the
   wx-free helper (e.g. the relevant function from `quill/core/html_to_markdown.py`)
   into a sibling module the Quillin imports, and move its unit tests alongside.
   "Thin core, fat Quillin": core keeps a function only if other *core* code still
   calls it.
3. **Register it as bundled.** Add the Quillin to the bundled-manifest allowlist
   so it ships enabled (Wave 0 machinery).
4. **Delete the old wiring.** Remove the mixin handler body, the inline command
   registration, and the menu/hotkey wiring from core/UI in the *same* PR — no
   dead duplicate.
5. **Re-pin through the Quillin.** Convert the characterization test to load the
   bundled Quillin through `ExtensionHost`, invoke the command, and assert the
   **identical** output/announcement. (This is exactly the shape of
   `tests/unit/core/test_quillins_example.py` + the live host smoke test.)
6. **Verify the bar.** `ruff format`/`check`; strict `mypy` on any touched
   `quill/core`; dialog/inventory/egress gates green; public-surface fixture
   regenerated if a `MainFrame` method disappeared.

Rollback at any step is a single-directory + single-PR revert.

## 6. Wave-by-wave sequencing

| Wave | Scope | Exit criterion |
| --- | --- | --- |
| **0 — Platform** | Build Tier C: bundled-extensions root, trusted-enable gate, packaging, latency budget (§3). | The promoted `markdown-helpers` Quillin ships **enabled**, shows in the Manager, runs end-to-end; third-party flag still `locked_off`; perf budget published and met. |
| **1 — Text Tools** | Convert 3–5 pure text transforms (`set_lines_*`, number/wrap lines, trim/case/sort if present) into ONE bundled "Text Tools" Quillin; delete their core helpers. | Each command loads + invokes through the host with byte-identical output; core LOC for those features removed; suite green. |
| **2 — Insert Tools** | Convert date/time + snippet/boilerplate inserters into a bundled "Insert Tools" Quillin (mostly Layer 1, zero capabilities). | Snippets expand identically; no consent prompts (no gated caps); menu homes match `menus.md`. |
| **3 — Gated proof** | Convert one **consent-gated** feature (e.g. an online lookup over `net`, or a file-backed action over `fs.*`) to a bundled Quillin. | The real shipped Quillin triggers the **consent gate** before its first network/file action and degrades gracefully on denial — proving the gated path in production. |
| **4 — Markdown Tools** | Convert HTML→Markdown paste, vendoring `html_to_markdown` into the Quillin; retire the core helper if no other core caller remains. | `clipboard.read` capability exercised; conversion fidelity tests move alongside the Quillin. |
| **N — Re-evaluate** | Measure core LOC removed and Manager dogfood coverage; decide the stop point. | A documented tally of features now served by bundled Quillins, with the guardrail set (§2) explicitly *not* converted. |

Each wave is multiple small PRs. Stop converting the moment a feature would have
to cross a guardrail (§2) or a latency budget (§3) — that feature belongs in Tier
A/B, and saying so is part of the honest result.

## 7. Done criteria & honest limits

**Done looks like:** a Tier C mechanism shipping a handful of QUILL's own
text/insert/markdown features as **bundled, enabled, sandboxed Quillins**; their
algorithms and tests living *in the Quillins*, not in `quill/core`/`quill/ui`; the
**Tools ▸ Quillins Manager** listing real, running, project-authored Quillins on a
default build; and a published latency budget the out-of-process path meets.

**Honest limits — what this roadmap deliberately does NOT claim:**

- **Not everything becomes a Quillin.** The editor surface, announcement engine,
  lifecycle, dictation/OCR/AI/watch/spell-check, and every wx/platform-bound or
  per-keystroke feature stay in Tier A/B *by design* (§2, §4). A platform proven
  by converting *suitable* features is the goal; converting *all* features is an
  anti-goal that would regress accessibility and latency.
- **SEC-8 is untouched.** Third-party discovery/execution remains `locked_off`.
  Tier C is trusted-author, install-tree, separately gated code — the proof works
  precisely *because* it reuses the sandbox without unlocking strangers.
- **No new user-facing capability.** Justification is flexibility-demonstration
  and maintainability; sequence after 1.0 user-facing work; every wave stays
  green and accessible or it does not land.
- **Latency is a real constraint, not a footnote.** If Wave 0's measurement shows
  the out-of-process round-trip is too slow for a candidate's expected use, that
  candidate stays Tier B. The budget decides, not the aspiration.
