# Ask Quill Chat (on-device AI) setup

The **Ask Quill Chat** assistant (Tools ▸ AI ▸ *Ask Quill Chat…*) is a
message-style chat that can answer, write/insert text, rewrite a selection, and
run Quill commands — with **approval required before anything changes the
document**. It runs **on-device** (no cloud) via a pluggable backend:

- **Windows / Linux:** `llama.cpp` (CPU, GGUF) — `llama-cpp-python`.
- **macOS (Apple Silicon, macOS 26+):** Apple Foundation Models (no install).

The backend is chosen automatically per platform; on Windows it's llama.cpp.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

This installs the UI deps plus **`llama-cpp-python`** (the on-device backend).
On Windows, `llama-cpp-python` ships prebuilt CPU wheels for most setups; if a
build is triggered, install **CMake** and the **Visual C++ Build Tools** first.

## 2. Download a model (GGUF)

Pick a quantized `.gguf` model and put it where Quill looks for it:

- **Recommended:** **Phi-4-mini** (Q4_K_M) — strong writing, ~2.3 GB, MIT.
- **Low-end machines:** **Llama 3.2 1B** (Q4) — ~0.7 GB.

Place the file in either location:

- `%APPDATA%\Quill\models\` on Windows (`~/.quill/models/` on Linux), **or**
- anywhere, and set the environment variable `QUILL_LLAMA_MODEL` to its full path.

Quill uses `QUILL_LLAMA_MODEL` if set, otherwise the first `*.gguf` in the
models folder.

## 3. Use it

1. Open **Tools ▸ AI ▸ Ask Quill Chat…**
2. Type a request (or pick a suggestion) and press **Send**. Examples:
   - "Summarize this document"
   - "Write an introduction about …"
   - "Fix the grammar in my selection"
   - "Save the document"
3. When Quill proposes a change (insert / replace / run a command), an
   **Approve / Discard** bar appears — nothing touches your document until you
   **Approve**.
4. **Copy Last Response** copies the latest reply.

## Notes

- If the model or `llama-cpp-python` is missing, the chat reports it clearly and
  does nothing destructive (no crash).
- Large documents/selections are handled by trimming context / chunking, so it
  won't error on the model's context-window limit.
- This is separate from the Ollama-based **Writing Assistant** (see
  `assistant-setup.md`); both can coexist.
