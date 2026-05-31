"""Report whether macOS "Increase contrast" is enabled.

Counterpart to ``quill.platform.windows.high_contrast.is_high_contrast_enabled``.
Reads the Universal Access preference; returns False if it can't be read.
"""
from __future__ import annotations

import subprocess


def is_high_contrast_enabled() -> bool:
    try:
        completed = subprocess.run(
            ["defaults", "read", "com.apple.universalaccess", "increaseContrast"],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
    except OSError:
        return False
    if completed.returncode != 0:
        return False
    return completed.stdout.strip() in {"1", "true", "YES"}
