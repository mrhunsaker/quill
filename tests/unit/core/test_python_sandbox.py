from __future__ import annotations

from quill.core.python_sandbox import run_python_sandbox


def test_python_sandbox_runs_simple_transform() -> None:
    result = run_python_sandbox(
        "result = selection_text.upper()",
        selection_text="hello",
        timeout_seconds=5.0,
    )

    assert result.succeeded is True
    assert result.result == "HELLO"


def test_python_sandbox_blocks_disallowed_imports() -> None:
    result = run_python_sandbox("import os\nresult = 'x'")

    assert result.succeeded is False
    assert "not allowed" in result.error.lower()


def test_python_sandbox_times_out_runaway_code() -> None:
    result = run_python_sandbox("while True:\n    pass", timeout_seconds=0.2)

    assert result.timed_out is True
