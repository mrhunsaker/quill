#!/usr/bin/env bash
# Run Quill from source on macOS / Linux. Mirror of run-from-source.bat.
#
# Picks the first Python interpreter that has wxPython installed, in order:
#   $QUILL_PYTHON -> active venv -> active conda -> ./.venv -> ./venv -> PATH,
# then runs `python -m quill` from the repo root (so the in-tree `quill`
# package is importable). Pass `--print-python` to just print the interpreter.
#
# First time, create a dev environment:
#   python3 -m venv .venv && .venv/bin/pip install -e ".[dev,ui]"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXE=""

has_wx() { [ -x "$1" ] && "$1" -c "import wx" >/dev/null 2>&1; }
try() { [ -z "$PYTHON_EXE" ] && has_wx "$1" && PYTHON_EXE="$1"; return 0; }

[ -n "${QUILL_PYTHON:-}" ] && try "$QUILL_PYTHON"
[ -n "${VIRTUAL_ENV:-}" ] && try "$VIRTUAL_ENV/bin/python"
[ -n "${CONDA_PREFIX:-}" ] && try "$CONDA_PREFIX/bin/python"
try "$ROOT/.venv/bin/python"
try "$ROOT/venv/bin/python"
[ -z "$PYTHON_EXE" ] && try "$(command -v python3 2>/dev/null || true)"
[ -z "$PYTHON_EXE" ] && try "$(command -v python 2>/dev/null || true)"

if [ -z "$PYTHON_EXE" ]; then
  echo "No Python interpreter with wxPython was found." >&2
  echo >&2
  echo "Create or activate a development environment first, for example:" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/pip install -e \".[dev,ui]\"" >&2
  exit 1
fi

if [ "${1:-}" = "--print-python" ]; then
  echo "$PYTHON_EXE"
  exit 0
fi

# --- Auto-install dependencies when requirements.txt changes ---
# Reinstall only when requirements.txt changed (e.g. after a git pull).
# Skip with QUILL_NO_AUTO_DEPS=1.
REQ="$ROOT/requirements.txt"
STAMP="$ROOT/.quill-reqs.sha256"
if [ -z "${QUILL_NO_AUTO_DEPS:-}" ] && [ -f "$REQ" ]; then
  if command -v shasum >/dev/null 2>&1; then
    NEW_HASH="$(shasum -a 256 "$REQ" | awk '{print $1}')"
  else
    NEW_HASH="$(sha256sum "$REQ" | awk '{print $1}')"
  fi
  OLD_HASH="$(cat "$STAMP" 2>/dev/null || true)"
  if [ -n "$NEW_HASH" ] && [ "$NEW_HASH" != "$OLD_HASH" ]; then
    echo "Requirements changed — installing dependencies..."
    if "$PYTHON_EXE" -m pip install -r "$REQ"; then
      printf '%s\n' "$NEW_HASH" > "$STAMP"
    else
      echo "Dependency install failed; launching with the existing environment." >&2
    fi
  fi
fi

cd "$ROOT"
exec "$PYTHON_EXE" -m quill "$@"
