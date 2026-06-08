# Markdown Helpers — a sample Quillin

A small, self-contained **proof-of-concept Quillin** that demonstrates both
authoring layers of the QUILL extension framework documented in
[`docs/scripting.md`](../../../docs/scripting.md):

| Command | Layer | What it does | Capabilities |
| --- | --- | --- | --- |
| **Insert Markdown Front Matter** (`ext.mdh.frontmatter`) | 1 — snippet, no code | Inserts a YAML front-matter block, expanding `${filename}`, `${date}`, and placing the caret at `${cursor}` | none |
| **Wrap Selection in Bold** (`ext.mdh.bold`) | 2 — Python handler | Wraps the current selection in Markdown `**bold**` markers and announces the result | `editor.read`, `editor.write`, `ui.announce`, `ui.command` |

Both commands are surfaced on the **Format** menu; the bold command is also
offered on the editor right-click menu (only when there is a selection) and on
the **Ctrl+Shift+B** hotkey.

## Files

- `manifest.json` — the `quill.extension/1` manifest (the normative contract; see
  `docs/scripting.md` §13–§15).
- `extension.py` — the Layer 2 entry module. QUILL calls `register(api)` once
  inside the sandboxed worker; the handler runs only on explicit invocation.

## Trying it

> [!IMPORTANT]
> Third-party Quillins are **locked off** in QUILL 1.0 (the `core.third_party_plugins`
> feature flag is `locked_off`, SEC-8). A default 1.0 build will **not** discover,
> load, or run this sample. It ships as a reference for authors and as the
> framework's proof-of-concept. When third-party loading is enabled in a later
> build, copy this directory to:
>
> ```text
> %APPDATA%\Quill\extensions\com.quill.examples.markdown-helpers\
> ```
>
> then enable it from **Tools → Quillins Manager**.

## Verifying it

The sample is exercised by
[`tests/unit/core/test_quillins_example.py`](../../../tests/unit/core/test_quillins_example.py),
which validates the manifest, builds a conflict-free contribution registry from
it, expands the Layer 1 snippet, and drives the Layer 2 handler through a fake
host context — proving the framework loads and runs a real Quillin end to end.
