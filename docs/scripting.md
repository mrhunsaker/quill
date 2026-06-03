# QUILL Scripting & Extensions — Design Plan (for review)

Status: **Draft for review** · Target: **QUILL 2.0** · Branch: `edsharp`

This document proposes how QUILL should let power users extend the application
with custom behaviour that hooks into the **menu system**, **hotkeys**, and
**right-click / context menus**. It is a design plan only — no runtime code in
this document is wired into the shipping app yet.

## 0. Provenance and inspiration

This capability is QUILL's answer to the scripting/add-in model pioneered by
**EdSharp 4.0** by **Jamal Mazrui** (2007–2017), a respected accessible,
screen-reader-first Windows editor that exposed almost its entire object model
to add-in code.

- Jamal Mazrui on GitHub: <https://github.com/jamalmazrui>
- EdSharp source: <https://github.com/jamalmazrui/EdSharp> and
  <https://github.com/EmpowermentZone/EdSharp>

EdSharp used **JScript.NET** as its scripting language because its host
application was written in C#/.NET, so the scripting language matched the
platform object model and the .NET Framework Class Library. The faithful
translation of that design for QUILL is to expose **QUILL's own object model**,
which is **Python** — see the language decision below.

## 1. Goals and non-goals

### Goals
- Let power users add **menu items**, **context-menu entries**, and **hotkeys**
  that run custom actions, without rebuilding QUILL.
- Keep the **writing path plain-text-first** and the **screen-reader-first**
  guarantees intact: extensions must never degrade NVDA/JAWS/Narrator parity.
- Make extensions **safe by default**: no ambient filesystem, network, or
  subprocess access unless explicitly declared and user-granted, consistent with
  QUILL's existing consent gates, DPAPI secret handling, and "no silent network
  calls" rule.
- Make extensions **authorable by blind power users** — the EdSharp audience —
  with plain-text manifests, readable Python, and accessible install/enable UX.
- Preserve the architecture boundary: `quill/core` and `quill/io` stay
  UI-framework-agnostic; only `quill/ui` and `quill/platform/windows` touch `wx`.

### Non-goals (explicitly out of scope for the first iteration)
- A live rich-text/RTF editing surface (a standing QUILL design exclusion).
- Arbitrary native code plugins or replacing core UI widgets.
- A general-purpose marketplace / auto-update of third-party extensions (later).
- JavaScript as the *primary* extension language (see §3; a QuickJS **snippet
  expression evaluator** is noted as optional future work only).

## 2. Language decision (resolved)

**Two-layer model, with Python as the scripting language, not JavaScript.**

Rationale: QUILL's platform object model is Python, so scripting it in Python is
the lowest-friction, most powerful, most debuggable, and most maintainable
option — and it is the faithful analogue of EdSharp scripting its C# host with
JScript.NET. Choosing JavaScript as the primary language would mean maintaining
a second runtime and a permanent Python⇄JS marshalling layer purely to script an
application that is already Python. JavaScript's only strong advantages
(familiarity, EdSharp-parity optics) do not outweigh that cost.

A comparison of the options considered (Python, embedded JavaScript via
QuickJS/V8, Lua via `lupa`, WASM via Extism, declarative-only) is retained in
Appendix A.

## 3. Architecture: two layers

### Layer 1 — Declarative manifest (safe, covers the common ~70%)
A static, schema-validated manifest (JSON, validated like every other QUILL
store under `quill/core/schemas/`) that **maps** menu items, context-menu
entries, and hotkeys onto:
- existing built-in QUILL command IDs (the same IDs used in
  `quill/core/keymap.py`), and/or
- text **snippets / templates** (no executable code).

This layer is **non-Turing-complete and fully sandboxable** — it can do nothing
except invoke commands QUILL already trusts and insert literal text. Most real
"add a menu item / bind a key / add a right-click action" requests are satisfied
here with effectively zero risk.

### Layer 2 — Python extension API (real logic, isolated)
For genuine custom logic, an extension ships a Python entry point that QUILL runs
**out-of-process** (mirroring the existing OCR worker-process precedent in the
concurrency model) behind a **capability-gated RPC bridge**. The extension never
imports `wx` and never touches the editor widget directly; it talks to a narrow,
versioned API object and all UI effects are marshalled back onto the UI thread
via `wx.CallAfter`.

```
+------------------+        capability-gated RPC         +-----------------------+
|  QUILL UI thread | <--------------------------------> | Extension host worker |
|  (wx, main_frame)|   (stdio/pipe, JSON messages)      |  (sandboxed Python)   |
+------------------+                                     +-----------------------+
        |  registers menu/hotkey/context hooks                   |
        |  marshals results via wx.CallAfter                     | user extension code
        v                                                        v
   core command dispatch                                  QuillExtensionApi (v1)
```

## 4. Manifest schema (Layer 1 sketch)

Stored per-extension under `%APPDATA%\Quill\extensions\<id>\manifest.json`,
schema-validated, atomic-written, with `.bak`/recovery like other stores.

```jsonc
{
  "schema": "quill.extension/1",
  "id": "com.example.wraptools",
  "name": "Wrap Tools",
  "version": "1.0.0",
  "author": "Jane Power-User",
  "license": "MIT",
  "capabilities": ["editor.read", "editor.write"],   // requested permissions
  "contributes": {
    "commands": [
      { "id": "ext.wraptools.fence", "title": "Wrap In Code Fence",
        "run": { "snippet": "```\n${selection}\n```" } }
    ],
    "menus": [
      { "parent": "Format", "command": "ext.wraptools.fence" }
    ],
    "context_menu": [
      { "when": "editor.hasSelection", "command": "ext.wraptools.fence" }
    ],
    "hotkeys": [
      { "command": "ext.wraptools.fence", "binding": "Ctrl+Shift+Grave, F" }
    ]
  },
  "main": "extension.py"   // optional; presence triggers Layer 2 host
}
```

Notes:
- `hotkeys[].binding` reuses QUILL's existing binding grammar, including the
  **QUILL Key** chord prefix (`Ctrl+Shift+Grave, …`). Conflicts are detected with
  the existing `find_keymap_conflict` logic and reported to the user; extension
  bindings never silently override user/default bindings.
- `menus[].parent` / `context_menu[]` register through the existing menu and
  context-menu construction paths in `quill/ui`, honouring the project rule to
  **defer menu mutations until menus are closed**.
- A `command.run.snippet` with no `main` is pure Layer 1 (no code execution).

## 5. The Python extension API (Layer 2 sketch)

A single, versioned, capability-checked facade — no direct widget access:

```python
class QuillExtensionApi:        # v1, passed to the extension's register()
    # editor.read
    def get_text(self) -> str: ...
    def get_selection(self) -> str: ...
    def get_cursor(self) -> CursorAddress: ...     # line, column, percent
    # editor.write   (all routed through core commands + undo history)
    def replace_selection(self, text: str) -> None: ...
    def insert_text(self, text: str) -> None: ...
    # ui (always marshalled to the UI thread)
    def announce(self, message: str) -> None: ...  # screen-reader announcement
    def register_command(self, command_id: str, title: str, handler) -> None: ...
    # fs / net only if capability granted + user-consented at install/run
    def read_file(self, path: str) -> str: ...     # requires "fs.read"
    def fetch(self, url: str) -> Response: ...      # requires "net" + consent gate
```

Design rules:
- Every method maps to an existing core operation so extension edits flow through
  **command + history** (undoable) and through the **announcement engine** for
  consistent NVDA/JAWS/Narrator output.
- All editor mutations go through `quill/core`; the extension process holds **no**
  `wx` reference and **no** direct buffer handle.
- The API is **versioned** (`v1`); breaking changes ship a new version while old
  extensions keep working against the old facade.

## 6. Security & consent model

- **Default deny.** No capability ⇒ no filesystem, no network, no subprocess.
  Pure-snippet extensions need no capabilities at all.
- **Declared + granted.** Capabilities are listed in the manifest and **shown to
  the user at install/enable time**; network/file capabilities additionally pass
  through QUILL's existing per-action **consent gate** with visible progress and
  outcome (no silent network calls).
- **Isolation.** Layer 2 runs out-of-process; a crash or hang in an extension
  cannot take down the editor or corrupt the buffer (the UI side owns the buffer).
- **No secrets to extensions.** Extensions never receive DPAPI-protected secrets
  or document content over the wire unless a capability + consent explicitly
  authorise it; **no document content is ever logged**.
- **Signing/trust (later).** A future iteration may add signature/trust prompts
  and a per-extension audit log.

## 7. Accessibility of the authoring experience

- Manifests are plain JSON and extensions are plain `.py` — both fully readable in
  QUILL itself, the EdSharp authoring philosophy.
- The **Extensions Manager** dialog uses stock controls
  (`wx.ListBox` / `wx.TextCtrl` read-only review panes, explicit default buttons,
  consistent Escape/Close handling, focus returned to the editor on close) per
  the project's dialog/accessibility rules, and is registered in `dialogs.md`.
- Errors from extension code surface as **announced**, reviewable text (a
  read-only multiline control), never as transient-only message boxes.

## 8. Packaging

- Bundled with the existing Windows distribution builder / Inno Setup component
  model. Layer 1 + Layer 2 (Python host) need **no new native runtime** because
  the interpreter already ships with QUILL.
- The optional QuickJS snippet evaluator (Appendix B) would be the *only* item
  that adds a native dependency, which is why it is deferred and optional.

## 9. Optional future: JavaScript snippet evaluator (QuickJS)

Strictly optional, post-foundation, for literal EdSharp `.js`-snippet parity:
embed **QuickJS** (tiny, no ambient I/O by default) as an **expression/snippet
evaluator** only — e.g. a "Evaluate Expression" command and `.js` snippet tokens,
matching EdSharp's `Control+Equals` / `Alt+V`. It would **not** be the extension
API. Capabilities would be granted explicitly, identical to the Python layer.

## 10. Phasing / milestones

1. **M1 — Manifest + loader (Layer 1):** schema, validation, load/enable/disable,
   command/menu/context/hotkey registration, conflict detection, Extensions
   Manager dialog. No code execution. Highest value, lowest risk.
2. **M2 — Python host (Layer 2):** out-of-process worker, RPC bridge,
   `QuillExtensionApi v1` with `editor.read`/`editor.write`/`announce`/
   `register_command`, undo/announcement integration.
3. **M3 — Capabilities + consent:** `fs.read`/`fs.write`/`net`, install-time
   disclosure, per-action consent gate, audit log.
4. **M4 (optional) — QuickJS snippet evaluator** for EdSharp `.js` parity.

## 11. Testing strategy

- `quill/core` + `quill/io` (manifest model, schema validation, capability
  checks, conflict detection): real unit tests, wx-free, strict mypy.
- UI registration (menu/context/hotkey wiring): source-contract tests plus the
  A11Y-4 dialog-contract guard for the Extensions Manager dialog.
- Host/RPC bridge: integration tests with a fake extension exercising
  read/write/announce and a capability-denied path.
- Security: explicit tests that an undeclared capability is rejected and that no
  document content crosses the bridge without consent.

## 12. Open questions for review

1. Distribution: local folder install only for 2.0, or a curated gallery later?
2. Do we want per-extension **profiles** (tie enablement to QUILL feature
   profiles) in the first cut, or global enable/disable only?
3. Hotkey precedence when an extension binding conflicts with a user rebinding —
   reject (proposed) vs. prompt-to-override?
4. Should Layer 1 snippets support the existing snippet token system, unifying
   "snippets" and "extension snippets" into one engine?
5. Minimum capability set for M2 — is `editor.read` + `editor.write` + `announce`
   enough to be useful, deferring `fs`/`net` to M3?

---

## 13. Manifest JSON Schema (normative)

This is the authoritative, machine-validatable contract for `quill.extension/1`
manifests. It is the schema that will live under `quill/core/schemas/` and be
enforced by the loader. AI or human authors can validate a generated manifest
against this before submission.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://quill.app/schemas/extension/1.json",
  "title": "QUILL Extension Manifest",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema", "id", "name", "version"],
  "properties": {
    "schema": { "const": "quill.extension/1" },
    "id": {
      "type": "string",
      "description": "Reverse-DNS unique id, e.g. com.example.wraptools.",
      "pattern": "^[a-z0-9]+([._-][a-z0-9]+)*$",
      "minLength": 3,
      "maxLength": 128
    },
    "name": { "type": "string", "minLength": 1, "maxLength": 80 },
    "version": {
      "type": "string",
      "description": "Semantic version MAJOR.MINOR.PATCH.",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "author": { "type": "string", "maxLength": 120 },
    "description": { "type": "string", "maxLength": 400 },
    "license": { "type": "string", "maxLength": 64 },
    "min_quill_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Lowest QUILL version this extension supports."
    },
    "capabilities": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "enum": [
          "editor.read",
          "editor.write",
          "ui.announce",
          "ui.command",
          "fs.read",
          "fs.write",
          "net",
          "clipboard.read",
          "clipboard.write"
        ]
      }
    },
    "main": {
      "type": "string",
      "description": "Relative path to the Python entry module (Layer 2). Omit for snippet-only (Layer 1) extensions.",
      "pattern": "^[A-Za-z0-9_./-]+\\.py$"
    },
    "contributes": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "commands": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["id", "title"],
            "properties": {
              "id": {
                "type": "string",
                "pattern": "^ext\\.[a-z0-9]+([._-][a-z0-9]+)*$",
                "description": "Must be namespaced under ext. to avoid colliding with built-in command ids."
              },
              "title": { "type": "string", "minLength": 1, "maxLength": 80 },
              "run": {
                "type": "object",
                "description": "How the command executes. Exactly one of snippet or handler.",
                "oneOf": [
                  {
                    "additionalProperties": false,
                    "required": ["snippet"],
                    "properties": {
                      "snippet": {
                        "type": "string",
                        "description": "Literal text inserted/replacing selection. Supports ${selection}, ${clipboard}, ${date}, ${time}, ${filename} placeholders. No code execution."
                      }
                    }
                  },
                  {
                    "additionalProperties": false,
                    "required": ["handler"],
                    "properties": {
                      "handler": {
                        "type": "string",
                        "description": "Name of a function registered by the Python entry module via api.register_command. Requires main + ui.command capability."
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "menus": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["parent", "command"],
            "properties": {
              "parent": {
                "type": "string",
                "description": "Top-level menu title to attach under, e.g. File, Edit, Format, Tools, Help.",
                "enum": ["File", "Edit", "Format", "Tools", "Navigate", "View", "Help"]
              },
              "command": { "type": "string", "description": "A command id contributed above or a built-in command id." }
            }
          }
        },
        "context_menu": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["command"],
            "properties": {
              "command": { "type": "string" },
              "when": {
                "type": "string",
                "description": "Optional visibility guard.",
                "enum": ["always", "editor.hasSelection", "editor.hasText", "editor.empty"]
              }
            }
          }
        },
        "hotkeys": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["command", "binding"],
            "properties": {
              "command": { "type": "string" },
              "binding": {
                "type": "string",
                "description": "QUILL binding grammar. Supports the QUILL Key chord prefix, e.g. 'Ctrl+Shift+Grave, F'. Conflicts are rejected, never silently overridden."
              }
            }
          }
        }
      }
    }
  },
  "allOf": [
    {
      "$comment": "A handler-based command requires a Python entry module.",
      "if": {
        "properties": {
          "contributes": {
            "properties": {
              "commands": {
                "contains": { "properties": { "run": { "required": ["handler"] } } }
              }
            }
          }
        }
      },
      "then": { "required": ["main"] }
    }
  ]
}
```

## 14. Extension authoring reference (humans and AI)

This section is the complete, self-contained reference an author needs. It is
written so an LLM can produce a valid, working extension from this document
alone, with no access to QUILL source.

### 14.1 Capability catalogue

| Capability | Grants | Consent | Notes |
| --- | --- | --- | --- |
| `editor.read` | Read buffer text, selection, cursor address | Install-time disclosure | Required by `get_text`, `get_selection`, `get_cursor` |
| `editor.write` | Insert text, replace selection (undoable) | Install-time disclosure | All writes flow through core command + history |
| `ui.announce` | Send screen-reader announcements | Install-time disclosure | Required by `announce` |
| `ui.command` | Register `handler` commands invoked from menus/hotkeys | Install-time disclosure | Required when `run.handler` is used |
| `fs.read` / `fs.write` | Read/write files by path | Per-action consent gate | Paths validated; no access outside granted scope |
| `net` | Outbound HTTP(S) | Per-action consent gate, visible progress | No silent network calls — ever |
| `clipboard.read` / `clipboard.write` | Read/write the system clipboard | Install-time disclosure | |

A pure snippet-only extension declares **no** capabilities.

### 14.2 Contribution reference

- **commands** — declare an `ext.*`-namespaced id + human title; `run` is either a
  `snippet` (Layer 1, no code) or a `handler` (Layer 2, requires `main` +
  `ui.command`).
- **menus** — attach a command under a fixed top-level menu (`parent`). Menu
  mutation is deferred until menus close (project rule).
- **context_menu** — attach a command to the editor right-click menu, optionally
  guarded by a `when` predicate.
- **hotkeys** — bind a command using QUILL's binding grammar, including the QUILL
  Key chord prefix `Ctrl+Shift+Grave, <key>`. Conflicts are detected with the
  same logic as user keymaps and **rejected with an announced message**.

### 14.3 Snippet placeholder reference (Layer 1)

| Placeholder | Expands to |
| --- | --- |
| `${selection}` | Current selection (empty string if none) |
| `${clipboard}` | Current clipboard text (requires `clipboard.read`) |
| `${date}` | Current date in the user's configured format |
| `${time}` | Current time in the user's configured format |
| `${filename}` | Current document file name (empty if unsaved) |
| `${cursor}` | Final cursor position marker after insertion |

### 14.4 Python API reference (Layer 2, `QuillExtensionApi` v1)

Every extension's entry module defines a top-level `register(api)` function.
QUILL calls it once when the extension loads. All methods are synchronous from
the extension's perspective; UI effects are marshalled onto the UI thread by the
host. Methods raise `CapabilityError` if the required capability was not granted.

| Method | Capability | Returns | Description |
| --- | --- | --- | --- |
| `api.register_command(command_id, handler)` | `ui.command` | `None` | Bind a `handler` name (referenced by `run.handler`) to a callable `handler(ctx)` |
| `api.get_text()` | `editor.read` | `str` | Full document text |
| `api.get_selection()` | `editor.read` | `str` | Selected text (`""` if none) |
| `api.get_cursor()` | `editor.read` | `CursorAddress` | `.line` (1-based), `.column` (1-based), `.percent` (0–100) |
| `api.insert_text(text)` | `editor.write` | `None` | Insert at cursor (undoable) |
| `api.replace_selection(text)` | `editor.write` | `None` | Replace selection, or insert if none (undoable) |
| `api.announce(message)` | `ui.announce` | `None` | Screen-reader announcement via the announcement engine |
| `api.read_file(path)` | `fs.read` | `str` | Read a text file (consent-gated) |
| `api.write_file(path, text)` | `fs.write` | `None` | Write a text file (consent-gated) |
| `api.fetch(url, *, method="GET", body=None)` | `net` | `Response` | HTTP(S) request (consent-gated, visible progress) |
| `api.get_clipboard()` | `clipboard.read` | `str` | Clipboard text |
| `api.set_clipboard(text)` | `clipboard.write` | `None` | Set clipboard text |

`handler(ctx)` receives a `ctx` exposing the same read/write/announce surface
scoped to the invocation, so a handler typically reads, computes, and writes back.

Error types an author may see: `CapabilityError`, `ConsentDeniedError`,
`ConflictError` (hotkey/menu), `ApiVersionError`.

### 14.5 Worked example A — snippet-only (no capabilities, no code)

`manifest.json`:

```json
{
  "schema": "quill.extension/1",
  "id": "com.example.fence",
  "name": "Code Fence",
  "version": "1.0.0",
  "contributes": {
    "commands": [
      { "id": "ext.fence.wrap", "title": "Wrap In Code Fence",
        "run": { "snippet": "```\n${selection}\n```\n${cursor}" } }
    ],
    "context_menu": [ { "when": "editor.hasSelection", "command": "ext.fence.wrap" } ],
    "hotkeys": [ { "command": "ext.fence.wrap", "binding": "Ctrl+Shift+Grave, F" } ]
  }
}
```

### 14.6 Worked example B — Python handler

`manifest.json`:

```json
{
  "schema": "quill.extension/1",
  "id": "com.example.titlecase",
  "name": "Title Case",
  "version": "1.0.0",
  "capabilities": ["editor.read", "editor.write", "ui.announce", "ui.command"],
  "main": "extension.py",
  "contributes": {
    "commands": [
      { "id": "ext.titlecase.run", "title": "Title Case Selection",
        "run": { "handler": "title_case" } }
    ],
    "menus": [ { "parent": "Format", "command": "ext.titlecase.run" } ],
    "hotkeys": [ { "command": "ext.titlecase.run", "binding": "Ctrl+Shift+Grave, T" } ]
  }
}
```

`extension.py`:

```python
def register(api):
    def title_case(ctx):
        text = ctx.get_selection()
        if not text:
            ctx.announce("Title Case: no selection")
            return
        ctx.replace_selection(text.title())
        ctx.announce("Title Case applied")
    api.register_command("title_case", title_case)
```

## 15. AI authoring guide — deterministic generation contract

This section gives an AI agent an unambiguous procedure to generate a valid
extension. Following it should yield a manifest that passes §13 and an entry
module that loads under §14.4.

**Generation checklist (must all hold):**
1. `schema` is exactly `"quill.extension/1"`.
2. `id` is reverse-DNS, lowercase, matches the §13 pattern, and is globally unique.
3. `version` is `MAJOR.MINOR.PATCH`.
4. Every contributed command `id` starts with `ext.` and is unique within the file.
5. Every `menus[].command`, `context_menu[].command`, and `hotkeys[].command`
   references either a contributed command id or a documented built-in id.
6. If **any** command uses `run.handler`, then `main` is present **and**
   `capabilities` includes `ui.command`.
7. `capabilities` is the minimal set: include a capability **iff** an API method
   or placeholder in the extension requires it (see §14.1, §14.3, §14.4).
8. Hotkey `binding` uses the QUILL grammar; prefer the QUILL Key prefix
   (`Ctrl+Shift+Grave, <letter>`) to avoid clashing with built-ins.
9. The Python entry module defines exactly one top-level `register(api)` and
   registers every `handler` name referenced by the manifest.
10. No `wx` import, no direct filesystem/network/subprocess/clipboard access
    except through the granted `api` methods.

**Minimal-capability decision table:**

| If the extension… | Declare |
| --- | --- |
| only inserts literal/snippet text | *(none)* |
| reads buffer/selection/cursor | `editor.read` |
| inserts or replaces text | `editor.write` |
| speaks to the screen reader | `ui.announce` |
| has any `run.handler` command | `ui.command` + `main` |
| reads/writes files | `fs.read` / `fs.write` |
| makes network requests | `net` |
| touches the clipboard | `clipboard.read` / `clipboard.write` |

**Machine-readable contract summary (for prompt embedding):**

```
ENTRYPOINT: register(api) -> None              # exactly one, top-level
HANDLER:    handler(ctx) -> None               # ctx mirrors api read/write/announce
WRITES:     undoable, via core commands only
THREADING:  api is sync; UI effects marshalled by host (never call wx)
DENY:       no capability => no fs/net/subprocess/clipboard
NAMESPACE:  command ids must start with "ext."
CONFLICTS:  hotkey/menu conflicts are rejected + announced, never overridden
VERSION:    target QuillExtensionApi v1
```

---

## 16. Internal modularization — core as a framework

A deliberate, longer-horizon consequence of this design: the **contribution
grammar** defined here (commands, menus, hotkeys, context-menu entries) is the
same vocabulary QUILL already uses *internally* to wire up its built-in
features. That makes it a natural blueprint for decomposing the
`quill/ui/main_frame.py` "god object" into self-registering **first-party
feature modules**, leaving `quill/core` as a genuine framework.

### 16.1 Two tiers, one vocabulary

There are **two tiers of extension**, sharing one contribution grammar but
differing in **trust level and API breadth** — not in how they appear to users.

| | First-party feature modules | Third-party extensions |
| --- | --- | --- |
| Trust | Trusted, shipped, reviewed | Untrusted |
| Process | In-process | Out-of-process (Appendix B) |
| API breadth | Rich, synchronous host API (editor, dialogs, settings, undo, workers, platform, announcements) | Narrow, capability-gated `QuillExtensionApi` (§5) |
| Sandbox | None needed (trusted code) | Mandatory (§6) |
| Registration | Same contribution grammar (§4) | Same contribution grammar (§4) |

The crucial rule: **first-party features must NOT be routed through the
sandboxed, out-of-process, capability-gated path.** Built-ins need rich,
synchronous, in-process access; forcing them across the RPC bridge would be a
severe downgrade in capability, latency (per-keystroke operations!), and
complexity for zero security benefit, since the code is already trusted.

### 16.2 What this enables

- An internal `register(host)` module interface, where `host` exposes the rich
  trusted API. Related commands (line-ops, EDS parity, search, formatting…) are
  extracted from `main_frame.py` into self-registering modules.
- `quill/core` keeps only the framework: document model, command registry,
  keymap, event bus, feature gating, and the announcement engine.
- The contribution grammar (this document) becomes the single registration
  mechanism for both tiers.

### 16.3 Honest limits (do not over-rotate)

- **Do not pluginize the editor surface or the accessibility / announcement
  engine.** The plain-text `wx.TextCtrl` writing path and NVDA/JAWS/Narrator
  parity are the framework's central guarantee, not a plugin. Delegating them is
  how accessibility regresses.
- `main_frame.py` is deeply entangled (shared mutable state, wx id maps, ordering
  dependencies). Decompose **incrementally and opportunistically, behind
  characterization tests** — never a big-bang "everything is a plugin" rewrite.
- Feature profiles already deliver much of the user-facing modularity benefit, so
  the refactor's justification is **maintainability**, not new capability.
- This is a **2.0-scale effort**, sequenced after user-facing wins.

## 17. Seamless use, transparent governance

Extensions should be **indistinguishable from built-in features at the point of
use**, while remaining **fully auditable and controllable** in management.

### 17.1 Seamless at the point of use

A user should never be able to tell, while writing, whether a command came from
core, a bundled module, or a third-party extension. All of them:

- appear in the same menus, command palette, and context menus;
- bind through the same keymap (and surface in the key-describer / learning
  mode);
- announce outcomes through the same announcement engine with NVDA/JAWS/Narrator
  parity;
- respect the same feature-gating and Settings UI.

That uniformity is exactly *why* both tiers share one contribution grammar
(§16.1). No second-class citizens; no "bolted-on" feel.

### 17.2 Transparent where it matters (non-negotiable)

Seamlessness hides the *seam*, never the *capabilities*. Consistent with QUILL's
"no silent network calls", per-action consent, and DPAPI rules:

- An **Extensions manager** lists every installed extension, its publisher, and
  its granted capabilities, so the user can audit, disable, or revoke.
- **Capability prompts** (§6) surface the first time an untrusted extension wants
  something sensitive (network, filesystem beyond the document, clipboard, running
  executables). Trusted first-party modules do not prompt; third-party ones do.
- **Provenance is visible on demand** (e.g. in command-palette details or a
  "Where did this come from?" affordance), even though it is invisible by default.

Principle: **users should not have to *think* about whether something is an
extension during normal use, but must always be *able to find out* and *control
it* when trust or accessibility is at stake.** Hiding the seam is a UX win;
hiding capabilities or network access would violate QUILL's privacy-first
contract.

## 18. Declarative dialogs & accessibility enforcement

Extensions may contribute **dialogs**, but they **describe** dialogs
declaratively — they never instantiate a `wx` widget. QUILL renders them. This
makes inaccessible or unsafe UI **structurally impossible** rather than merely
discouraged.

### 18.1 The mechanism

QUILL already has the right primitive: `show_web_form` (`quill/ui/web_form.py`)
builds a dialog from a **field spec** using vetted stock controls
(`wx.TextCtrl`, `wx.ListBox`, `wx.Dialog`) with consistent focus, a default
button, and Escape/Close handling. (The EDS `DLG-1` migrations already use it.)

An extension contributes a dialog description:

```json
{
  "dialog": "calculate_date",
  "title": "Calculate Date",
  "fields": [
    { "id": "anchor", "label": "Start date", "type": "text" },
    { "id": "offset", "label": "Days to add", "type": "number" },
    { "id": "unit",   "label": "Unit", "type": "choice",
      "choices": ["days", "weeks", "months"] }
  ]
}
```

…and receives back a plain dict (`{anchor, offset, unit}`). It never creates a
control, sets a sizer, or manages focus.

### 18.2 Why this enforces accessibility without risk

- **Accessibility is structural, not requested.** Every dialog comes from QUILL's
  one renderer, so it inherits stock-control usage, focus return to editor,
  label/announcement parity, and the **A11Y-4 dialog-contract guard**
  automatically. An extension *cannot* produce an inaccessible dialog because it
  cannot produce a dialog at all — only a description of one.
- **No untrusted code in the UI thread.** Third-party logic stays out-of-process
  (Appendix B); only data crosses the boundary. A buggy or malicious extension
  cannot freeze the UI, draw a custom-painted control, or break screen-reader
  focus.
- **`dialogs.md` stays truthful.** Because the renderer is central, contributed
  dialogs are enumerable and can be registered into the manual regression map the
  same way native dialogs are.

### 18.3 Constrained vocabulary is the safety property

- The field-type catalogue is intentionally **finite**: text, multiline
  read-only, number, choice, checkbox, file-pick-with-consent, list. Allowing
  "arbitrary layout" or "custom control" would forfeit the guarantee — so it is
  not allowed. That finiteness *is* the safety property.
- Genuinely novel custom UI is **out of scope** for extensions; it must be a
  first-party module reviewed against A11Y-4 (§16.1), not a sandboxed extension.
- Anything sensitive a dialog *triggers* (network, file write, run executable)
  still passes through capability prompts (§6). An accessible dialog never
  bypasses consent.

---

## Appendix A — Language options considered

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **Python (embedded, app's own language)** | No new runtime; whole object model already Python; best debugging/docs/stdlib; faithful analogue of EdSharp scripting its C# host; easiest to maintain | In-process sandboxing is weak — must run out-of-process for real isolation | **Chosen (Layer 2)** |
| **JavaScript (QuickJS / V8 via `py_mini_racer`)** | Familiar to most; strong sandbox (isolates / no ambient I/O); EdSharp/JScript.NET optics; QuickJS tiny | Permanent Python⇄JS marshalling; cross-boundary stack traces; native build/packaging dependency; async/wx impedance | Optional future snippet evaluator only |
| **Lua (`lupa`/LuaJIT)** | Classic embeddable scripting; tiny; easy to sandbox | Small user base among QUILL power users; another language to learn; weak text-tooling stdlib | Rejected |
| **WASM (Extism / Wasmtime)** | Strongest sandbox; language-agnostic | Heavy; complex host bindings; hard to author/debug; overkill | Rejected for 2.0 |
| **Declarative-only (manifest)** | Safest; covers ~70% of requests; trivially accessible to author | Not Turing-complete; power users hit a ceiling | **Chosen (Layer 1), paired with Python** |

## Appendix B — Why out-of-process

QUILL's concurrency model already runs OCR in a separate worker process and
marshals UI updates through `wx.CallAfter`. Reusing that pattern for the
extension host gives real fault isolation (a runaway extension can't corrupt the
buffer or freeze the editor) and is the only way to meaningfully sandbox Python.
The UI side remains the sole owner of the editor buffer; the extension side only
ever sends intents over the RPC bridge.
