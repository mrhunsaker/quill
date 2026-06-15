"""Detect and install the optional QUILL Braille Pack (#243 / BR-020).

The pack bundles liblouis plus the English UEB tables and powers the Translation
submenu (BR-022). It is entirely optional: when absent, the Translation submenu
is hidden so users never see disabled items. Detection is non-invasive (PATH,
bundled binding, or a python module) and never imports liblouis in-process.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

# Names that, if present, indicate a usable liblouis install shipped with the
# pack: the CLI tools on PATH, or the python binding importable.
_PACK_EXECUTABLES = ("lou_translate", "louis")
_PACK_MODULES = ("louis", "lou_translate")


def is_braille_pack_installed() -> bool:
    """Return True when a liblouis-backed braille pack is available."""
    import os

    # Fastest check: look for lou_translate.exe in the vendor location set
    # by the installer (QUILL_APP_ROOT is set by run-quill.cmd).
    app_root_env = os.environ.get("QUILL_APP_ROOT")
    if app_root_env:
        pack_exe = Path(app_root_env) / "vendor" / "braille-pack" / "lou_translate.exe"
        if pack_exe.exists():
            return True

    if any(shutil.which(name) for name in _PACK_EXECUTABLES):
        return True
    if any(name in sys.modules for name in _PACK_MODULES):
        return True
    for module in _PACK_MODULES:
        try:
            if importlib.util.find_spec(module) is not None:
                return True
        except (ImportError, ValueError):
            continue
    return False


def braille_pack_version() -> str | None:
    """Return the installed pack version string, or None when not installed."""
    if not is_braille_pack_installed():
        return None
    try:
        import louis  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - any import failure means "version unknown"
        return "unknown"
    version = getattr(louis, "version", None)
    if callable(version):
        try:
            return str(version())
        except Exception:  # noqa: BLE001
            return "unknown"
    return str(getattr(louis, "__version__", "") or "unknown")


def get_brf_profiles() -> list[dict]:
    """Return the list of BRF profiles from the installed pack's brf_profiles.json.

    Searches the vendor braille pack directory for brf_profiles.json. Returns
    an empty list when the pack is not installed or the file cannot be read.

    Search order:
    1. ``{QUILL_APP_ROOT}/vendor/braille-pack/`` — set by run-quill.cmd in the
       installer build; covers both portable and installed modes.
    2. ``<repo-root>/liblouis/vendor/braille/pack/`` — dev source tree.
    3. ``<repo-root>/vendor/braille-pack/`` — portable staging path.
    """
    import os

    candidates: list[Path] = []

    app_root_env = os.environ.get("QUILL_APP_ROOT")
    if app_root_env:
        candidates.append(Path(app_root_env) / "vendor" / "braille-pack" / "brf_profiles.json")

    repo_root = Path(__file__).resolve().parents[2]
    candidates += [
        repo_root / "liblouis" / "vendor" / "braille" / "pack" / "brf_profiles.json",
        repo_root / "vendor" / "braille-pack" / "brf_profiles.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return list(data.get("profiles", []))
            except Exception:  # noqa: BLE001
                continue
    return []


def install_braille_pack(progress_cb: Callable[[str], None] | None = None) -> bool:
    """Phase 5 stub: no auto-download, no silent network calls.

    Points the user at the docs and returns False (nothing installed). A real
    installer in a later PR MUST register its download site in the network-egress
    audit (``_REVIEWED_EGRESS``) before adding any network call.
    """
    message = "Download the QUILL Braille Pack from docs/braille.md (Phase 5, optional)."
    if progress_cb is not None:
        progress_cb(message)
    return False
