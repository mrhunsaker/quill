from __future__ import annotations

import concurrent.futures
import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from quill.stability.wx_dispatch import call_ui_safely

logger = logging.getLogger(__name__)


class CancelledError(Exception):
    pass


@dataclass(slots=True)
class CancellationToken:
    event: threading.Event = field(default_factory=threading.Event)

    def cancel(self) -> None:
        self.event.set()

    def is_cancelled(self) -> bool:
        return self.event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled():
            raise CancelledError("Operation cancelled")


@dataclass(slots=True)
class QuillTask:
    operation_id: str
    name: str
    future: concurrent.futures.Future[Any]
    cancellation_token: CancellationToken
    started_at: float
    timeout_seconds: float | None
    safe_to_cancel: bool = True
    safe_to_kill: bool = False


class TaskManager:
    def __init__(self, max_workers: int = 4) -> None:
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="quill-worker",
        )
        self._tasks: dict[str, QuillTask] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        name: str,
        func: Callable[..., Any],
        *,
        timeout_seconds: float | None = None,
        on_success: Callable[[str, Any], None] | None = None,
        on_failure: Callable[[str, BaseException], None] | None = None,
        on_progress: Callable[[str, Any], None] | None = None,
        safe_to_cancel: bool = True,
        safe_to_kill: bool = False,
        **kwargs: Any,
    ) -> QuillTask:
        operation_id = str(uuid.uuid4())
        token = CancellationToken()

        def report_progress(payload: Any) -> None:
            if on_progress is None:
                return
            call_ui_safely(on_progress, operation_id, payload)

        def wrapped() -> Any:
            started = time.monotonic()
            logger.info("Task started operation_id=%s name=%s", operation_id, name)
            try:
                result = func(
                    cancellation_token=token,
                    operation_id=operation_id,
                    progress_callback=report_progress,
                    **kwargs,
                )
                duration_ms = (time.monotonic() - started) * 1000
                logger.info(
                    "Task finished operation_id=%s name=%s duration_ms=%.1f",
                    operation_id,
                    name,
                    duration_ms,
                )
                if on_success is not None:
                    call_ui_safely(on_success, operation_id, result)
                return result
            except BaseException as exc:
                duration_ms = (time.monotonic() - started) * 1000
                if isinstance(exc, CancelledError):
                    logger.info(
                        "Task cancelled operation_id=%s name=%s duration_ms=%.1f",
                        operation_id,
                        name,
                        duration_ms,
                    )
                else:
                    logger.exception(
                        "Task failed operation_id=%s name=%s duration_ms=%.1f",
                        operation_id,
                        name,
                        duration_ms,
                    )
                if on_failure is not None:
                    call_ui_safely(on_failure, operation_id, exc)
                raise

        future = self._executor.submit(wrapped)
        task = QuillTask(
            operation_id=operation_id,
            name=name,
            future=future,
            cancellation_token=token,
            started_at=time.monotonic(),
            timeout_seconds=timeout_seconds,
            safe_to_cancel=safe_to_cancel,
            safe_to_kill=safe_to_kill,
        )
        with self._lock:
            self._tasks[operation_id] = task
        future.add_done_callback(lambda _future: self._remove_task(operation_id))
        return task

    def cancel(self, operation_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(operation_id)
        if task is None:
            return False
        task.cancellation_token.cancel()
        return task.future.cancel()

    def snapshot(self) -> list[QuillTask]:
        with self._lock:
            return list(self._tasks.values())

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=not wait)

    def _remove_task(self, operation_id: str) -> None:
        with self._lock:
            self._tasks.pop(operation_id, None)
