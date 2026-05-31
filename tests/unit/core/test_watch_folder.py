from __future__ import annotations

import os
import time
from pathlib import Path

from quill.core.watch_folder import WatchFolderConfig, WatchFolderResult, WatchFolderService


def test_watch_folder_config_normalizes_values() -> None:
    config = WatchFolderConfig(
        enabled=True,
        folder_path=" C:\\incoming ",
        poll_interval_seconds=1,
    ).normalized()

    assert config.poll_interval_seconds == 2
    assert config.folder_path == "C:\\incoming"


def test_watch_folder_scan_processes_supported_file_once(tmp_path: Path) -> None:
    text_file = tmp_path / "notes.md"
    text_file.write_text("# Notes", encoding="utf-8")
    stale_mtime = time.time() - 10
    os.utime(text_file, (stale_mtime, stale_mtime))
    (tmp_path / "clip.wav").write_bytes(b"audio")

    results: list[WatchFolderResult] = []
    errors: list[tuple[Path, str]] = []
    service = WatchFolderService(on_result=results.append, on_error=errors.append)
    config = WatchFolderConfig(
        enabled=True, folder_path=str(tmp_path), process_existing=True
    ).normalized()

    service._scan_once(tmp_path, config)
    service._scan_once(tmp_path, config)

    assert len(results) == 1
    assert results[0].source_path == text_file
    assert errors == []


def test_watch_folder_prescan_skips_existing_files(tmp_path: Path) -> None:
    existing_file = tmp_path / "existing.md"
    existing_file.write_text("existing", encoding="utf-8")

    seen_results: list[WatchFolderResult] = []
    service = WatchFolderService(on_result=seen_results.append)
    config = WatchFolderConfig(
        enabled=True, folder_path=str(tmp_path), process_existing=False
    ).normalized()

    service._prescan(tmp_path, config)
    service._scan_once(tmp_path, config)

    assert seen_results == []
