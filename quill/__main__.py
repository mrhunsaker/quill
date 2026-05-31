from __future__ import annotations

import os
import sys
from pathlib import Path

from quill.core.features import reset_feature_profile_store
from quill.core.paths import app_data_dir, ensure_app_directories
from quill.core.storage_mode import load_storage_mode, portable_root_dir, save_storage_mode
from quill.stability.diagnostics import dump_all_thread_stacks, setup_fault_handler
from quill.stability.logging_config import configure_logging


def main() -> int:
    ensure_app_directories()
    log_listener = configure_logging(app_data_dir() / "logs")
    setup_fault_handler()
    try:
        _bootstrap_storage_mode()

        try:
            from quill.ui.main_frame import run_app
        except ModuleNotFoundError as exc:
            if exc.name == "wx":
                print("wxPython is required to run the UI. Install with: pip install -e .[ui]")
                return 1
            raise

        from quill.core.ipc import (
            enqueue_open_request,
            release_primary_instance,
            try_claim_primary_instance,
        )

        dump_stacks = "--dump-stacks" in sys.argv[1:]
        diagnostics_mode = "--diagnostics" in sys.argv[1:]
        if dump_stacks:
            dump_file = dump_all_thread_stacks("manual CLI request")
            print(dump_file)
            return 0

        launch_paths, safe_mode, reset_profile = _launch_arguments(sys.argv[1:])
        if reset_profile:
            reset_feature_profile_store()
        if not try_claim_primary_instance():
            for path in launch_paths:
                enqueue_open_request(path)
            enqueue_open_request(None)
            return 0
        try:
            run_app(launch_paths, safe_mode=safe_mode, diagnostics_mode=diagnostics_mode)
        finally:
            release_primary_instance()
    finally:
        log_listener.stop()
    return 0


def _bootstrap_storage_mode() -> None:
    if os.environ.get("QUILL_PORTABLE") != "1":
        return
    if os.environ.get("QUILL_DATA_DIR"):
        return
    root = portable_root_dir()
    if root is None:
        return
    mode = load_storage_mode()
    if mode == "portable":
        os.environ["QUILL_DATA_DIR"] = str(root)
        return
    if mode == "appdata":
        return

    try:
        import wx
    except ModuleNotFoundError:
        return

    app = wx.App(False)
    try:
        with wx.SingleChoiceDialog(
            None,
            "Where should Quill store its settings and other local data?",
            "Quill Storage Location",
            choices=[
                "AppData (recommended)",
                "Portable folder next to Quill",
            ],
        ) as dialog:
            selection = dialog.ShowModal()
            if selection != wx.ID_OK:
                choice = "appdata"
            elif dialog.GetSelection() == 1:
                choice = "portable"
            else:
                choice = "appdata"
    finally:
        app.Destroy()

    save_storage_mode(choice)
    if choice == "portable":
        root.mkdir(parents=True, exist_ok=True)
        os.environ["QUILL_DATA_DIR"] = str(root)


def _launch_arguments(arguments: list[str]) -> tuple[list[Path], bool, bool]:
    paths: list[Path] = []
    safe_mode = False
    reset_profile = False
    for value in arguments:
        if value == "--safe-mode":
            safe_mode = True
            continue
        if value == "--reset-profile":
            reset_profile = True
            continue
        if value.startswith("--"):
            continue
        if not value.strip():
            continue
        candidate = Path(value).expanduser()
        if candidate.exists():
            paths.append(candidate.resolve())
    if os.environ.get("QUILL_SAFE_MODE") == "1":
        safe_mode = True
    return paths, safe_mode, reset_profile


if __name__ == "__main__":
    raise SystemExit(main())
