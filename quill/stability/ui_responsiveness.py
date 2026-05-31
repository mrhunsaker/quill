from __future__ import annotations

import functools
import logging
import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

_wx_main_thread_id: int | None = None


def mark_wx_main_thread() -> None:
    global _wx_main_thread_id
    _wx_main_thread_id = threading.get_ident()


def is_wx_main_thread() -> bool:
    return threading.get_ident() == _wx_main_thread_id


@contextmanager
def timed_operation(
    name: str, warn_after_ms: float = 100.0, **context: Any
) -> Generator[None, None, None]:
    started = time.monotonic()
    try:
        yield
    finally:
        duration_ms = (time.monotonic() - started) * 1000
        if duration_ms >= warn_after_ms:
            logger.warning(
                "Slow operation name=%s duration_ms=%.1f on_wx_thread=%s context=%r",
                name,
                duration_ms,
                is_wx_main_thread(),
                context,
            )


def wx_event_handler(
    name: str, warn_after_ms: float = 100.0
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with timed_operation(name, warn_after_ms=warn_after_ms):
                return func(*args, **kwargs)

        return wrapper

    return decorator
