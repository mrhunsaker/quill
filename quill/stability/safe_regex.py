from __future__ import annotations

import logging
import time

import regex

logger = logging.getLogger(__name__)


class RegexTimeoutError(Exception):
    pass


def safe_finditer(
    pattern: str,
    text: str,
    *,
    timeout_seconds: float = 1.0,
    flags: int = 0,
) -> list[regex.Match[str]]:
    started = time.monotonic()
    try:
        compiled = regex.compile(pattern, flags)
        matches = list(compiled.finditer(text, timeout=timeout_seconds))
        duration_ms = (time.monotonic() - started) * 1000
        logger.info(
            "Regex search completed pattern_length=%d text_length=%d matches=%d duration_ms=%.1f",
            len(pattern),
            len(text),
            len(matches),
            duration_ms,
        )
        return matches
    except TimeoutError as exc:
        duration_ms = (time.monotonic() - started) * 1000
        logger.warning(
            "Regex search timed out pattern_length=%d text_length=%d timeout=%s duration_ms=%.1f",
            len(pattern),
            len(text),
            timeout_seconds,
            duration_ms,
        )
        raise RegexTimeoutError(
            "This regular expression search took too long and was stopped."
        ) from exc


def safe_subn(
    pattern: str,
    replacement: str,
    text: str,
    *,
    timeout_seconds: float = 1.0,
    flags: int = 0,
) -> tuple[str, int]:
    started = time.monotonic()
    try:
        compiled = regex.compile(pattern, flags)
        updated, count = compiled.subn(replacement, text, timeout=timeout_seconds)
        duration_ms = (time.monotonic() - started) * 1000
        logger.info(
            (
                "Regex replace completed pattern_length=%d text_length=%d "
                "replacements=%d duration_ms=%.1f"
            ),
            len(pattern),
            len(text),
            count,
            duration_ms,
        )
        return updated, count
    except TimeoutError as exc:
        duration_ms = (time.monotonic() - started) * 1000
        logger.warning(
            "Regex replace timed out pattern_length=%d text_length=%d timeout=%s duration_ms=%.1f",
            len(pattern),
            len(text),
            timeout_seconds,
            duration_ms,
        )
        raise RegexTimeoutError(
            "This regular expression search took too long and was stopped."
        ) from exc
