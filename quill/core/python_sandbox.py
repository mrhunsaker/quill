from __future__ import annotations

import ast
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from typing import Any


ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "fractions",
        "functools",
        "heapq",
        "itertools",
        "json",
        "math",
        "operator",
        "re",
        "statistics",
        "string",
        "textwrap",
        "typing",
    }
)

_SANDBOX_BOOTSTRAP = textwrap.dedent(
    """
    from __future__ import annotations

    import base64
    import builtins
    import contextlib
    import io
    import json
    import os
    import sys
    import traceback

    payload = json.loads(base64.b64decode(os.environ["QUILL_SANDBOX_PAYLOAD"]).decode("utf-8"))
    code = base64.b64decode(payload["code_b64"]).decode("utf-8")
    document_text = payload.get("document_text", "")
    selection_text = payload.get("selection_text", "")
    input_text = payload.get("input_text", "")
    outline = payload.get("outline")

    allowed_modules = set(payload.get("allowed_imports", ()))
    original_import = builtins.__import__

    def _blocked(name: str, *_args, **_kwargs):
        raise PermissionError(f"{name} is not available in the sandbox")

    def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        root_name = name.split(".", 1)[0]
        if root_name not in allowed_modules:
            raise ImportError(f"Import of {root_name} is not allowed in the sandbox")
        return original_import(name, globals, locals, fromlist, level)

    safe_builtins = {
        "abs": builtins.abs,
        "all": builtins.all,
        "any": builtins.any,
        "bool": builtins.bool,
        "dict": builtins.dict,
        "enumerate": builtins.enumerate,
        "filter": builtins.filter,
        "float": builtins.float,
        "format": builtins.format,
        "frozenset": builtins.frozenset,
        "getattr": builtins.getattr,
        "hasattr": builtins.hasattr,
        "hash": builtins.hash,
        "int": builtins.int,
        "isinstance": builtins.isinstance,
        "issubclass": builtins.issubclass,
        "iter": builtins.iter,
        "len": builtins.len,
        "list": builtins.list,
        "map": builtins.map,
        "max": builtins.max,
        "min": builtins.min,
        "next": builtins.next,
        "object": builtins.object,
        "pow": builtins.pow,
        "print": builtins.print,
        "range": builtins.range,
        "repr": builtins.repr,
        "reversed": builtins.reversed,
        "round": builtins.round,
        "set": builtins.set,
        "slice": builtins.slice,
        "sorted": builtins.sorted,
        "str": builtins.str,
        "sum": builtins.sum,
        "tuple": builtins.tuple,
        "zip": builtins.zip,
        "__import__": _guarded_import,
        "open": _blocked,
        "input": _blocked,
        "eval": _blocked,
        "exec": _blocked,
        "compile": _blocked,
        "help": _blocked,
        "breakpoint": _blocked,
        "exit": _blocked,
        "quit": _blocked,
    }

    globals_ns = {
        "__builtins__": safe_builtins,
        "document_text": document_text,
        "selection_text": selection_text,
        "outline": outline,
        "result": None,
        "set_result": lambda value: globals_ns.__setitem__("result", value),
    }
    sys.stdin = io.StringIO(input_text)
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(sys.stdout), contextlib.redirect_stderr(sys.stderr):
            exec(compile(code, "<quill-sandbox>", "exec"), globals_ns, globals_ns)
    except BaseException:
        payload = {
            "stdout": sys.stdout.getvalue(),
            "stderr": sys.stderr.getvalue(),
            "result": globals_ns.get("result"),
            "error": traceback.format_exc(),
        }
    else:
        payload = {
            "stdout": sys.stdout.getvalue(),
            "stderr": sys.stderr.getvalue(),
            "result": globals_ns.get("result"),
            "error": "",
        }
    if payload["result"] is not None and not isinstance(payload["result"], str):
        payload["result"] = str(payload["result"])
    sys.__stdout__.write(json.dumps(payload))
    """
).strip()


@dataclass(frozen=True, slots=True)
class PythonSandboxResult:
    stdout: str
    stderr: str
    result: str
    error: str
    timed_out: bool
    returncode: int
    elapsed_seconds: float

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.returncode == 0 and not self.error


def run_python_sandbox(
    code: str,
    *,
    document_text: str = "",
    selection_text: str = "",
    input_text: str = "",
    outline: list[dict[str, Any]] | None = None,
    timeout_seconds: float = 5.0,
) -> PythonSandboxResult:
    try:
        _validate_code_policy(code)
    except (SyntaxError, ValueError) as error:
        return PythonSandboxResult("", "", "", str(error), False, 1, 0.0)
    payload = {
        "code_b64": base64.b64encode(code.encode("utf-8")).decode("ascii"),
        "document_text": document_text,
        "selection_text": selection_text,
        "input_text": input_text,
        "outline": outline,
        "allowed_imports": sorted(ALLOWED_IMPORTS),
    }
    env = {key: value for key, value in os.environ.items() if key in {"SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "PATHEXT"}}
    env.update({
        "QUILL_SANDBOX_PAYLOAD": base64.b64encode(
            json.dumps(payload).encode("utf-8")
        ).decode("ascii"),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    start = time.perf_counter()
    completed: subprocess.CompletedProcess[str] | None = None
    timed_out = False
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", _SANDBOX_BOOTSTRAP],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
            cwd=tempfile.gettempdir(),
        )
    except subprocess.TimeoutExpired:
        timed_out = True
    except OSError as error:
        elapsed = time.perf_counter() - start
        return PythonSandboxResult("", "", "", str(error), False, 1, elapsed)
    elapsed = time.perf_counter() - start
    if timed_out:
        return PythonSandboxResult("", "", "", "Execution timed out", True, 124, elapsed)
    assert completed is not None
    if not completed.stdout:
        return PythonSandboxResult("", completed.stderr, "", "No result returned", False, completed.returncode, elapsed)
    try:
        payload_data = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return PythonSandboxResult(
            completed.stdout,
            completed.stderr,
            "",
            f"Could not parse sandbox output: {error}",
            False,
            completed.returncode,
            elapsed,
        )
    return PythonSandboxResult(
        stdout=str(payload_data.get("stdout", "")),
        stderr=str(payload_data.get("stderr", "")),
        result=str(payload_data.get("result", "")),
        error=str(payload_data.get("error", "")),
        timed_out=False,
        returncode=completed.returncode,
        elapsed_seconds=elapsed,
    )


def _validate_code_policy(code: str) -> None:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                if root_name not in ALLOWED_IMPORTS:
                    raise ValueError(f"Import of {root_name} is not allowed in the sandbox")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root_name = node.module.split(".", 1)[0]
            if root_name not in ALLOWED_IMPORTS:
                raise ValueError(f"Import of {root_name} is not allowed in the sandbox")
