"""Sandboxed worker process that runs a Layer 2 Quillin.

This module is the untrusted side of the out-of-process bridge. It is launched as
``python -m quill.core.quillins.host_worker <extension_dir>`` by
:class:`quill.core.quillins.host.ExtensionHost`, loads the extension's ``main``
module, runs its top-level ``register(api)``, and dispatches handler invocations.

The extension never imports ``wx`` and never touches the editor directly. Every
editor/ui/fs/net effect is a request sent back to the host, which enforces
capabilities and consent before doing anything. The :class:`QuillExtensionApi`
below is the narrow, versioned surface the extension sees; it simply marshals
each call into an ``api_call`` message and blocks for the host's reply.

The worker speaks the protocol on stdin/stdout only; everything it prints to
those streams must be a framed protocol message, so it must never ``print`` for
debugging — it uses :meth:`QuillExtensionApi.log` instead.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import IO, Any

from quill.core.quillins import protocol
from quill.core.quillins.model import (
    API_VERSION,
    CapabilityError,
    ConsentDeniedError,
    QuillinError,
)

HandlerFn = Callable[["QuillExtensionApi"], None]


@dataclass(frozen=True, slots=True)
class CursorAddress:
    """Where the caret is, as seen by an extension handler."""

    line: int
    column: int
    percent: int


def _raise_api_error(error_kind: str, message: str) -> None:
    if error_kind == "CapabilityError":
        raise CapabilityError(message)
    if error_kind == "ConsentDeniedError":
        raise ConsentDeniedError(message)
    raise QuillinError(message)


class QuillExtensionApi:
    """The versioned façade passed to an extension's ``register(api)``.

    The same object is handed to each ``handler(ctx)`` as ``ctx``, so a handler
    has the identical read/write/announce surface. Methods raise
    :class:`CapabilityError` (or :class:`ConsentDeniedError`) when the host
    refuses the underlying request.
    """

    version = API_VERSION

    def __init__(self, worker: _Worker) -> None:
        self._worker = worker
        self._handlers: dict[str, HandlerFn] = {}

    # -- registration ---------------------------------------------------------
    def register_command(self, handler_name: str, handler: HandlerFn) -> None:
        """Bind a ``run.handler`` name to a callable ``handler(ctx)``."""

        self._handlers[handler_name] = handler

    # -- editor.read ----------------------------------------------------------
    def get_text(self) -> str:
        return str(self._worker.call("get_text", []))

    def get_selection(self) -> str:
        return str(self._worker.call("get_selection", []))

    def get_cursor(self) -> CursorAddress:
        value = self._worker.call("get_cursor", [])
        data = value if isinstance(value, dict) else {}
        return CursorAddress(
            line=int(data.get("line", 1)),
            column=int(data.get("column", 1)),
            percent=int(data.get("percent", 0)),
        )

    # -- editor.write ---------------------------------------------------------
    def insert_text(self, text: str) -> None:
        self._worker.call("insert_text", [text])

    def replace_selection(self, text: str) -> None:
        self._worker.call("replace_selection", [text])

    # -- ui -------------------------------------------------------------------
    def announce(self, message: str) -> None:
        self._worker.call("announce", [message])

    # -- fs (consent-gated) ---------------------------------------------------
    def read_file(self, path: str) -> str:
        return str(self._worker.call("read_file", [path]))

    def write_file(self, path: str, text: str) -> None:
        self._worker.call("write_file", [path, text])

    # -- net (consent-gated) --------------------------------------------------
    def fetch(self, url: str, *, method: str = "GET", body: str | None = None) -> dict[str, Any]:
        value = self._worker.call("fetch", [url, method, body])
        return value if isinstance(value, dict) else {}

    # -- clipboard ------------------------------------------------------------
    def get_clipboard(self) -> str:
        return str(self._worker.call("get_clipboard", []))

    def set_clipboard(self, text: str) -> None:
        self._worker.call("set_clipboard", [text])

    # -- diagnostics ----------------------------------------------------------
    def log(self, message: str) -> None:
        """Emit a diagnostic line to the host (never document content)."""

        self._worker.send(protocol.log(message))


class _Worker:
    """Owns the stdio streams and the request/response message loop."""

    def __init__(self, directory: Path, reader: IO[str], writer: IO[str]) -> None:
        self._directory = directory
        self._reader = reader
        self._writer = writer
        self._call_id = 0
        self._api = QuillExtensionApi(self)

    def run(self) -> int:
        self.send(protocol.hello(API_VERSION))
        while True:
            line = self._reader.readline()
            if not line:
                return 0
            try:
                message = protocol.decode_message(line)
            except ValueError:
                continue
            kind = message.get("type")
            if kind == protocol.MSG_SHUTDOWN:
                return 0
            if kind == protocol.MSG_LOAD:
                self._handle_load(message)
            elif kind == protocol.MSG_INVOKE:
                self._handle_invoke(message)

    def _handle_load(self, message: dict[str, Any]) -> None:
        main = str(message.get("main", ""))
        call_id = int(message.get("id", 0))
        try:
            module = self._import_main(main)
            register = getattr(module, "register", None)
            if not callable(register):
                raise QuillinError("extension module defines no register(api) function")
            register(self._api)
        except Exception as error:  # report any load fault as a terminal result
            self.send(protocol.result_error(call_id, _error_kind(error), str(error)))
            return
        self.send(protocol.registered(list(self._api._handlers)))

    def _handle_invoke(self, message: dict[str, Any]) -> None:
        call_id = int(message.get("id", 0))
        handler_name = str(message.get("command", ""))
        handler = self._api._handlers.get(handler_name)
        if handler is None:
            self.send(protocol.result_error(call_id, "QuillinError", f"no handler: {handler_name}"))
            return
        try:
            handler(self._api)
        except Exception as error:
            self.send(protocol.result_error(call_id, _error_kind(error), str(error)))
            return
        self.send(protocol.result_ok(call_id))

    def _import_main(self, main: str) -> ModuleType:
        main_path = (self._directory / main).resolve()
        if self._directory.resolve() not in main_path.parents:
            raise QuillinError("main module escapes the extension directory")
        spec = importlib.util.spec_from_file_location("quillin_extension_main", main_path)
        if spec is None or spec.loader is None:
            raise QuillinError(f"cannot import extension main: {main}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def call(self, method: str, args: list[Any]) -> Any:
        """Send an api_call to the host and block for its result."""

        self._call_id += 1
        self.send(protocol.api_call(self._call_id, method, args))
        reply = self._read()
        if reply.get("type") != protocol.MSG_API_RESULT:
            raise QuillinError(f"expected api_result, got {reply.get('type')!r}")
        if not reply.get("ok", False):
            _raise_api_error(
                str(reply.get("error_kind", "QuillinError")),
                str(reply.get("message", "api call failed")),
            )
        return reply.get("value")

    def send(self, message: dict[str, Any]) -> None:
        self._writer.write(protocol.encode_message(message))
        self._writer.flush()

    def _read(self) -> dict[str, Any]:
        line = self._reader.readline()
        if not line:
            raise QuillinError("host closed the connection")
        return protocol.decode_message(line)


def _error_kind(error: Exception) -> str:
    if isinstance(error, QuillinError):
        return type(error).__name__
    return "QuillinError"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.stderr.write("usage: host_worker <extension_dir>\n")
        return 2
    directory = Path(args[0])
    worker = _Worker(directory, sys.stdin, sys.stdout)
    return worker.run()


if __name__ == "__main__":
    raise SystemExit(main())
