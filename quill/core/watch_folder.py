from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_POLL_SECONDS = 5
_MIN_POLL_SECONDS = 2
_MAX_POLL_SECONDS = 300
_MIN_FILE_AGE_SECONDS = 2.0
_WATCHED_SUFFIXES = (
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".xhtml",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".csv",
    ".tsv",
    ".ipynb",
    ".sqlite",
    ".db",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".epub",
    ".pages",
    ".pdf",
    ".odt",
    ".rtf",
)


@dataclass(frozen=True, slots=True)
class WatchFolderConfig:
    enabled: bool = False
    folder_path: str = ""
    include_subfolders: bool = False
    process_existing: bool = False
    auto_start: bool = False
    poll_interval_seconds: int = _DEFAULT_POLL_SECONDS

    def normalized(self) -> WatchFolderConfig:
        interval = int(self.poll_interval_seconds)
        if interval < _MIN_POLL_SECONDS:
            interval = _MIN_POLL_SECONDS
        if interval > _MAX_POLL_SECONDS:
            interval = _MAX_POLL_SECONDS
        return WatchFolderConfig(
            enabled=bool(self.enabled),
            folder_path=str(self.folder_path).strip(),
            include_subfolders=bool(self.include_subfolders),
            process_existing=bool(self.process_existing),
            auto_start=bool(self.auto_start),
            poll_interval_seconds=interval,
        )

    @property
    def suffixes(self) -> tuple[str, ...]:
        return _WATCHED_SUFFIXES


@dataclass(frozen=True, slots=True)
class WatchFolderResult:
    source_path: Path


class WatchFolderService:
    def __init__(
        self,
        *,
        on_result: Callable[[WatchFolderResult], None],
        on_error: Callable[[Path, str], None] | None = None,
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
        self._on_result = on_result
        self._on_error = on_error
        self._on_state_change = on_state_change
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._seen_files: set[str] = set()
        self._running = False
        self._config: WatchFolderConfig | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def config(self) -> WatchFolderConfig | None:
        return self._config

    def start(self, config: WatchFolderConfig) -> bool:
        normalized = config.normalized()
        if self._running:
            return False
        if not normalized.enabled:
            return False
        watch_path = Path(normalized.folder_path).expanduser()
        if not watch_path.is_dir():
            raise ValueError(f"Watch folder does not exist: {watch_path}")

        self._stop_event.clear()
        with self._lock:
            self._seen_files.clear()
        self._config = normalized
        if not normalized.process_existing:
            self._prescan(watch_path, normalized)
        self._running = True

        self._thread = threading.Thread(
            target=self._poll_loop, name="quill-watch-folder", daemon=True
        )
        self._thread.start()
        self._notify_state(True)
        return True

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=5.0)
        self._notify_state(False)

    def restart(self, config: WatchFolderConfig) -> bool:
        self.stop()
        return self.start(config)

    def _notify_state(self, running: bool) -> None:
        if self._on_state_change is None:
            return
        self._on_state_change(running)

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            config = self._config
            if config is None:
                return
            watch_path = Path(config.folder_path).expanduser()
            try:
                self._scan_once(watch_path, config)
            except Exception as error:  # surface via callback
                logger.exception("Watch folder scan failed")
                if self._on_error is not None:
                    self._on_error(watch_path, str(error))
            self._stop_event.wait(float(config.poll_interval_seconds))

    def _prescan(self, folder: Path, config: WatchFolderConfig) -> None:
        with self._lock:
            for path in self._iter_supported_files(folder, config):
                self._seen_files.add(str(path.resolve()))

    def _scan_once(self, folder: Path, config: WatchFolderConfig) -> None:
        now = time.time()
        for path in self._iter_supported_files(folder, config):
            try:
                canonical = str(path.resolve())
            except OSError:
                canonical = str(path)
            with self._lock:
                if canonical in self._seen_files:
                    continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_size <= 0:
                continue
            if (now - stat.st_mtime) < _MIN_FILE_AGE_SECONDS:
                continue
            with self._lock:
                self._seen_files.add(canonical)
            self._process_supported_file(path)

    def _process_supported_file(self, path: Path) -> None:
        try:
            result = WatchFolderResult(source_path=path)
        except Exception as error:  # surfaced via callback
            logger.exception("Watch folder processing failed for %s", path)
            if self._on_error is not None:
                self._on_error(path, str(error))
            return
        self._on_result(result)

    def _iter_supported_files(self, folder: Path, config: WatchFolderConfig) -> Iterable[Path]:
        if not folder.is_dir():
            return ()
        suffixes = {suffix.lower() for suffix in config.suffixes}
        glob_pattern = "**/*" if config.include_subfolders else "*"
        candidates: list[Path] = []
        for candidate in folder.glob(glob_pattern):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() not in suffixes:
                continue
            candidates.append(candidate)
        candidates.sort(key=lambda path: path.name.lower())
        return candidates
