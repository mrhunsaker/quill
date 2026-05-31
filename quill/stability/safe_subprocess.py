from __future__ import annotations

import logging
import subprocess
from collections.abc import Sequence

logger = logging.getLogger(__name__)


def run_subprocess_safely(
    args: Sequence[str],
    *,
    timeout_seconds: float = 30.0,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    logger.info("Running subprocess args=%r timeout=%s cwd=%r", list(args), timeout_seconds, cwd)
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        logger.info("Subprocess finished returncode=%s args=%r", result.returncode, list(args))
        return result
    except subprocess.TimeoutExpired:
        logger.exception("Subprocess timed out args=%r timeout=%s", list(args), timeout_seconds)
        raise
