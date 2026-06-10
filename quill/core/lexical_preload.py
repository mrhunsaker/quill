"""Background warm-up for the spell-check and thesaurus caches.

The first spell check or thesaurus lookup otherwise pays a one-time file-load
cost on the calling thread (PERF-1/PERF-2). Warming both in a daemon thread at
startup keeps that first interaction snappy without blocking launch. This module
is UI-framework-agnostic: it only spawns a worker thread and calls the existing
idempotent, thread-safe ``preload`` helpers.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


def _worker() -> None:
    try:
        from quill.core import spellcheck, thesaurus

        spellcheck.preload()
        thesaurus.preload()
    except Exception as error:  # noqa: BLE001
        # A preload failure must never affect the running app; the lazy
        # loaders remain the source of truth on first use.
        logger.debug("Lexical preload failed (non-fatal): %s", error)


def start_lexical_preload() -> threading.Thread:
    """Warm the lexical caches off the calling thread.

    Returns the started daemon thread so callers (and tests) can join it.
    """

    thread = threading.Thread(target=_worker, name="quill-lexical-preload", daemon=True)
    thread.start()
    return thread
