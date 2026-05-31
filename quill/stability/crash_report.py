from __future__ import annotations

import json
import platform
import sys
import time
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from quill import __version__
from quill.core.paths import app_data_dir, ensure_app_directories


def build_diagnostic_bundle(
    *,
    logs_path: Path | None = None,
    fault_dump_path: Path | None = None,
    thread_dump_path: Path | None = None,
    memory_snapshot_path: Path | None = None,
    task_snapshot: Sequence[object] | None = None,
    feature_flags: Mapping[str, bool] | None = None,
    enabled_plugins: Sequence[str] | None = None,
    safe_mode: bool = False,
    recent_commands: Sequence[str] | None = None,
    wx_version: str | None = None,
    output_path: Path | None = None,
) -> Path:
    ensure_app_directories()
    output_dir = app_data_dir() / "diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_path or output_dir / f"quill-diagnostic-bundle-{time.time_ns()}.zip"

    payload: dict[str, Any] = {
        "quill_version": __version__,
        "python_version": sys.version.splitlines()[0],
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "safe_mode": safe_mode,
        "wx_version": wx_version,
        "feature_flags": dict(feature_flags or {}),
        "enabled_plugins": list(enabled_plugins or []),
        "recent_commands": list(recent_commands or []),
    }
    if task_snapshot is not None:
        payload["active_tasks"] = [_snapshot_task(task) for task in task_snapshot]

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metadata.json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        _maybe_write_file(archive, "quill.log", logs_path)
        _maybe_write_file(archive, "faulthandler.log", fault_dump_path)
        _maybe_write_file(archive, "thread-dump.log", thread_dump_path)
        _maybe_write_file(archive, "memory-snapshot.txt", memory_snapshot_path)
    return bundle_path


def _maybe_write_file(archive: zipfile.ZipFile, name: str, path: Path | None) -> None:
    if path is None or not path.exists():
        return
    archive.write(path, arcname=name)


def _snapshot_task(task: object) -> dict[str, Any]:
    if is_dataclass(task):
        data = asdict(task)
    elif hasattr(task, "__dict__"):
        data = dict(task.__dict__)
    else:
        data = {"repr": repr(task)}
    data.pop("future", None)
    return data
