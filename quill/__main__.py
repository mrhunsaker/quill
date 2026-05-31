from __future__ import annotations

import os
import sys
import time
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path

from quill import __version__
from quill.core.features import reset_feature_profile_store
from quill.core.paths import app_data_dir, ensure_app_directories
from quill.core.storage_mode import load_storage_mode, portable_root_dir, save_storage_mode
from quill.stability.diagnostics import dump_all_thread_stacks, setup_fault_handler
from quill.stability.logging_config import configure_logging


@dataclass(frozen=True, slots=True)
class LaunchRequest:
    path: Path
    line: int | None = None
    column: int | None = None


def main() -> int:
    parsed = _parse_cli_arguments(sys.argv[1:])
    if parsed.version:
        print(__version__)
        return 0

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

        if parsed.dump_stacks:
            dump_file = dump_all_thread_stacks("manual CLI request")
            print(dump_file)
            return 0

        launch_requests, safe_mode, reset_profile, diagnostics_mode, force_new_window, wait = (
            _launch_configuration(parsed)
        )
        if reset_profile:
            reset_feature_profile_store()
        if not force_new_window and not try_claim_primary_instance():
            for request in launch_requests:
                enqueue_open_request(request.path, line=request.line, column=request.column)
            enqueue_open_request(None)
            if wait:
                _wait_for_primary_instance_shutdown()
            return 0
        try:
            run_app(launch_requests, safe_mode=safe_mode, diagnostics_mode=diagnostics_mode)
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


def _parse_cli_arguments(arguments: list[str]) -> Namespace:
    parser = ArgumentParser(
        prog="quill",
        description="Quill: screen-reader-first writing and document environment.",
    )
    parser.add_argument("paths", nargs="*", help="Optional files to open on startup.")
    parser.add_argument("--version", action="store_true", help="Show QUILL version and exit.")
    parser.add_argument("--safe-mode", action="store_true", help="Start QUILL in safe mode.")
    parser.add_argument(
        "--reset-profile",
        action="store_true",
        help="Reset the feature profile store before launch.",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Start with diagnostics tracing enabled.",
    )
    parser.add_argument(
        "--dump-stacks",
        action="store_true",
        help="Write a thread-stack dump and exit.",
    )
    parser.add_argument(
        "--new-window",
        action="store_true",
        help="Force a new QUILL process instead of reusing an existing instance.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="When forwarding to an existing instance, wait for it to close.",
    )
    parser.add_argument(
        "--line",
        type=int,
        default=None,
        help="1-based line number for the first opened file.",
    )
    parser.add_argument(
        "--column",
        type=int,
        default=None,
        help="1-based column number for the first opened file.",
    )
    return parser.parse_args(arguments)


def _launch_configuration(
    parsed: Namespace,
) -> tuple[list[LaunchRequest], bool, bool, bool, bool, bool]:
    requests: list[LaunchRequest] = []
    for index, raw_path in enumerate(parsed.paths):
        if not str(raw_path).strip():
            continue
        candidate = Path(str(raw_path)).expanduser()
        if not candidate.exists():
            continue
        request = LaunchRequest(
            path=candidate.resolve(),
            line=parsed.line if index == 0 else None,
            column=parsed.column if index == 0 else None,
        )
        requests.append(request)

    safe_mode = bool(parsed.safe_mode)
    if os.environ.get("QUILL_SAFE_MODE") == "1":
        safe_mode = True
    return (
        requests,
        safe_mode,
        bool(parsed.reset_profile),
        bool(parsed.diagnostics),
        bool(parsed.new_window),
        bool(parsed.wait),
    )


def _wait_for_primary_instance_shutdown(timeout_seconds: int = 3600) -> None:
    from quill.core.ipc import release_primary_instance, try_claim_primary_instance

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if try_claim_primary_instance():
            release_primary_instance()
            return
        time.sleep(0.25)


if __name__ == "__main__":
    raise SystemExit(main())
