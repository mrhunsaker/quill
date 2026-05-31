from __future__ import annotations

import logging
import os
import tracemalloc
from pathlib import Path

logger = logging.getLogger(__name__)


def start_memory_tracing(n_frames: int = 25) -> None:
    if not tracemalloc.is_tracing():
        tracemalloc.start(n_frames)
        logger.info("tracemalloc started n_frames=%d", n_frames)


def write_memory_snapshot(path: Path, limit: int = 50) -> None:
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("QUILL memory snapshot\n\n")
        for index, stat in enumerate(top_stats[:limit], start=1):
            handle.write(f"{index}. {stat}\n")


def should_trace_memory() -> bool:
    return os.environ.get("QUILL_TRACEMALLOC") == "1"
