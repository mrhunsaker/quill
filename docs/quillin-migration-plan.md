# Migrating QUILL's first-party code onto the Quillins contribution grammar

Status: **Plan / playbook** · Companion to `docs/scripting.md` (esp. §16) · Scope:
**internal refactor, 2.0-scale, maintainability-driven**

> Read `docs/scripting.md` §16 for the *why* (one vocabulary, two tiers). This
> document is the *how*: a concrete, low-risk, reversible procedure for moving
> built-in features out of the `quill/ui/main_frame.py` god object and onto the
> same **contribution grammar** (commands, menus, hotkeys, context-menu entries)
> that Quillins already use — turning `quill/core` into a genuine framework.

## 1. The one insight this plan rests on

The Quillins framework already defines, validates, and wires a contribution
vocabulary: a **command** (`id`, `title`, a handler), its placement in **menus**
and the **context menu**, and its **hotkey** binding, all merged with conflict
detection (`quill/core/quillins/registry.py`). QUILL's built-ins are wired with
*the same concepts*, but by hand, inline, inside one 20k-line class.

So the migration is not "rewrite features". It is: **express each existing
feature as a self-registering module that contributes commands through one host
facade**, and delete the corresponding hand-wiring from `main_frame.py`.

```
            ┌─────────────── one contribution grammar ───────────────┐
            │                                                         │
  first-party feature module                          third-party Quillin
  register(host)  ── rich, in-process host ──►   register(api) ── narrow, gated API
  (trusted, no sandbox)                           (untrusted, out-of-process, §6)
            │                                                         │
            └────────► same commands / menus / hotkeys / palette ◄────┘
```

The crucial rule (restated from §16.1, non-negotiable): **first-party modules run
in-process against a rich host facade. They are NEVER routed through the
sandboxed, capability-gated, out-of-process Quillin path.** That path exists for
*untrusted* code; forcing trusted per-keystroke built-ins across an RPC bridge
would wreck latency and capability for zero security gain.

## 2. Guardrails — what must NOT be migrated

These are load-bearing for QUILL's identity. Decomposing them is how
accessibility regresses (see §16.3):

- **The editor surface.** The plain-text `wx.TextCtrl` writing path stays a
  first-class, hand-owned widget. It is not a plugin and gets no `register(host)`.
- **The accessibility / announcement engine.** NVDA/JAWS/Narrator parity is the
  framework's central guarantee. It is *called by* migrated modules; it is not
  itself pluginized.
- **App lifecycle & frame construction.** Startup ordering, tab management, the
  single-instance guard, crash recovery, and the menu *bar* skeleton remain core.
- **Anything with deep shared-mutable-state coupling** that cannot be covered by
  a characterization test first (see §5). If you can't pin its behavior, you
  can't safely move it yet.

When in doubt: a feature is a migration candidate iff it is **command-shaped** —
it has a stable id, a title, a handler, and (optionally) a menu/hotkey/context
placement — and its handler can reach everything it needs through the host
facade (§4).

## 3. Target shape of a migrated module

A first-party feature module is a small, self-contained file exposing one
top-level `register(host)` that contributes its commands. It mirrors the Quillin
`register(api)` shape so the mental model is identical, but `host` is the **rich
trusted facade**, not the narrow capability-gated `QuillExtensionApi`.

```python
# quill/ui/features/line_ops.py  (illustrative target)
"""Line operations, migrated off main_frame.py onto the contribution grammar."""

from quill.core.contributions import Host  # the first-party host facade (§4)


def register(host: Host) -> None:
    host.add_command(
        id="lines.number",
        title="Number Lines",
        handler=_number_lines,
        menu=("Format",),          # optional placement
        context=("editor.hasText",),
        # no default hotkey: user binds via the Keymap Editor
    )


def _number_lines(ctx: Host) -> None:
    text = ctx.get_text()
    numbered = "\n".join(f"{i + 1}\t{line}" for i, line in enumerate(text.splitlines()))
    with ctx.undo_group("Number Lines"):
        ctx.set_text(numbered)
    ctx.announce("Numbered lines")
```

The module imports **no `wx`** directly for its *logic*; UI effects go through the
host facade, exactly as the EdSharp handlers already centralize their edits. (A
module may still live under `quill/ui/` and use `wx` for genuinely bespoke UI, but
that UI must pass A11Y-4 review — it is first-party, not a sandboxed extension.)

## 4. The first-party host facade

This is the single piece of *new* core surface the migration introduces:
`quill/core/contributions.py` (wx-free protocol) with a `quill/ui` implementation
that adapts `MainFrame`. It is the trusted superset of `QuillExtensionApi`:

| Group | Methods (illustrative) | Notes |
| --- | --- | --- |
| Registration | `add_command`, `add_menu`, `add_context`, `add_hotkey` | Same grammar as `Contributions`; conflicts routed through `build_registry` |
| Editor read | `get_text`, `get_selection`, `get_cursor`, `get_lines` | |
| Editor write | `set_text`, `insert_text`, `replace_selection`, `undo_group(label)` | All writes go through core command + history (undoable) |
| Announce | `announce`, `set_status` | The one announcement engine; never bypassed |
| Services | `settings`, `document`, `dialogs.show_web_form`, `workers`, `platform` | Rich, synchronous, in-process — the trusted breadth |

Two design rules keep this honest:

1. **The registration quartet is shared with Quillins.** `add_command` /
   `add_menu` / `add_hotkey` feed the *same* `ContributionRegistry`
   (`quill/core/quillins/registry.py`) so first-party and third-party
   contributions collide-detect against each other and the host keymap uniformly.
   First-party ids are *not* forced under `ext.` — they keep their existing
   namespaces (`lines.*`, `eds.*`, …); only third-party ids carry `ext.`.
2. **The breadth gap is the only difference between tiers.** `host` exposes
   settings/workers/platform/dialogs; `api` does not. That asymmetry *is* the
   trust boundary — there is no second registration mechanism, no second menu
   builder, no second keymap.

## 5. Strategy: strangler-fig, behind characterization tests

Never a big-bang "everything is a plugin" rewrite (§16.3). Each feature is moved
in a self-contained, individually revertible step:

1. **Pin behavior first.** Write/extend a characterization test that asserts the
   feature's *current* observable behavior (command id registered, menu present,
   handler output for representative input, announcement text). The existing
   `test_eds_command_wiring.py` is the template: it reads source text and asserts
   the wiring contract without constructing the full frame.
2. **Introduce the facade seam.** Land `quill/core/contributions.py` + its
   `MainFrame` adapter with **zero behavior change** — `main_frame.py` keeps
   working; the facade just wraps what it already does.
3. **Move one feature.** Extract its handler(s) into a `register(host)` module;
   replace the inline registration/menu/hotkey wiring in `main_frame.py` with a
   single `register(module, host)` call.
4. **Delete the old wiring.** The inline command registration, menu append, and
   handler body leave `main_frame.py`. The line count drops; the test stays green.
5. **Repeat.** One feature (or one cohesive mixin) per PR.

Rollback at any step is a single-file revert because each module is independent.

## 6. Pilot selection

Pick first movers that are **already command-shaped and already extracted into a
mixin**, so the migration is mechanical and the risk is near zero. The codebase
hands us an ideal pilot:

- **Pilot 1 — EdSharp Tools (`eds.*`).** `quill/ui/main_frame_edsharp_menu.py`
  already centralizes the commands as a `(id, label, handler)` table
  (`_edsharp_command_table`) and the handlers already live on one mixin
  (`EdSharpActionsMixin`). That table *is* a contribution list in all but name —
  converting it to `host.add_command(...)` calls is a near-syntactic transform,
  and `test_eds_command_wiring.py` already pins the contract.
- **Pilot 2 — line operations & "speak …" commands.** Self-contained, pure-ish
  text transforms with clear announcements and no dialog dependencies.
- **Pilot 3 — formatting commands** that contribute under the `Format` menu.

Defer: anything touching tab lifecycle, the watch service, AI/assistant flows, or
shared mutable selection state until the facade has proven itself on Pilots 1–3.

## 7. Wave-by-wave sequencing

| Wave | Scope | Exit criterion |
| --- | --- | --- |
| 0 | Land `quill/core/contributions.py` + `MainFrame` adapter; no features moved | Facade unit-tested; `main_frame.py` unchanged in behavior; public-surface fixture stable |
| 1 | Pilot 1 (EdSharp `eds.*`) | EdSharp table replaced by `register(host)`; `test_eds_command_wiring.py` green; `main_frame.py` net-smaller |
| 2 | Line-ops + speak/status commands | Each command a module; characterization tests green |
| 3 | Format-menu commands | `Format` contributions all flow through the registry |
| 4 | Navigate/View read-only commands | … |
| 5 | Tools utilities that already use `show_web_form` | Dialogs stay A11Y-4-registered; `dialogs.md` rows unchanged |
| N | Re-evaluate; stop when `main_frame.py` is a thin shell of lifecycle + surface | `quill/core` is the framework; remaining `main_frame.py` is guardrail code (§2) |

Each wave is multiple small PRs, not one large one.

## 8. Per-feature migration checklist

For every feature moved:

- [ ] Characterization test pins current id(s), menu/hotkey placement, handler
      output, and announcement text **before** any move.
- [ ] New module exposes exactly one top-level `register(host)`.
- [ ] Logic reaches the editor/settings/announcer **only** through the host
      facade; no new direct `MainFrame` attribute reach-ins.
- [ ] All writes use `host.undo_group(...)` so behavior stays undoable and
      announced identically.
- [ ] Inline registration/menu/hotkey/handler code is **removed** from
      `main_frame.py` in the same PR (no dead duplicate).
- [ ] Command ids and bindings still collide-detect via the shared registry
      (no silently-overridden hotkey — §4 rule 1).
- [ ] If the feature owns a dialog: `dialog_inventory.json` regenerated, the
      A11Y-4 gate green, `dialogs.md` row unchanged (the dialog didn't move for
      the user, only in code).
- [ ] `ruff format`/`check` clean; strict `mypy` green on the new wx-free core
      facade and any `quill/core` touched; targeted `pytest` green.
- [ ] If a public `MainFrame` method disappeared, regenerate the public-surface
      fixture and review the diff.

## 9. Worked example — migrating `eds.number_lines`

**Before** (conceptually, in `main_frame_edsharp_menu.py` + `EdSharpActionsMixin`):

```python
# table row
("eds.number_lines", "EdSharp: Number Lines", self.number_lines)
# registration loop calls self.commands.register(id, label, handler, binding)
# and the menu builder appends + binds the same id
```

**After** (`quill/ui/features/eds_line_ops.py`):

```python
def register(host):
    host.add_command(
        id="eds.number_lines",
        title="EdSharp: Number Lines",
        handler=_number_lines,
        menu=("Tools", "EdSharp Tools", "Lines"),
    )

def _number_lines(ctx):
    if ctx.is_read_only():
        ctx.set_status("Document is read-only")
        return
    ...                       # same body as today's EdSharpActionsMixin.number_lines
    ctx.announce("Numbered lines")
```

and in `main_frame.py`, the EdSharp block collapses to:

```python
from quill.ui.features import eds_line_ops
eds_line_ops.register(self._contribution_host)
```

The user sees **no change**: same palette entry, same menu path, same
key-bindability, same announcement. The maintainer sees one fewer responsibility
in the god object and a module they can read in isolation.

## 10. Done criteria & honest limits

**Done looks like:** `quill/core` carries the document model, command registry,
keymap, event bus, feature gating, the announcement engine, **and** the shared
contribution registry + host-facade protocol; the majority of command-shaped
features live in self-registering modules; `main_frame.py` is a thin shell of
lifecycle, the editor surface, and guardrail code (§2).

**This refactor does not add user-facing capability.** Its justification is
maintainability and testability (§16.3). Feature profiles already deliver most of
the user-visible modularity, so this is sequenced **after** user-facing wins and
proceeds **opportunistically** — every wave must leave the suite green and the
accessibility contract intact, or it does not land.
