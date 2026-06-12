"""Tests for quill.devtools.python_console."""

from __future__ import annotations

from quill.core.script_results import ScriptError, ScriptSuccess
from quill.devtools.python_console import PythonConsole


def make_console(extra: dict | None = None) -> PythonConsole:
    ns: dict = {}
    if extra:
        ns.update(extra)
    return PythonConsole(ns)


def test_simple_expression_returns_success():
    con = make_console()
    result = con.execute("1 + 1")
    assert isinstance(result, ScriptSuccess)


def test_print_output_captured():
    con = make_console()
    result = con.execute("print('hello world')")
    assert isinstance(result, ScriptSuccess)
    assert "hello world" in result.output


def test_variable_persists_across_calls():
    con = make_console()
    con.execute("x = 42")
    result = con.execute("print(x)")
    assert isinstance(result, ScriptSuccess)
    assert "42" in result.output


def test_syntax_error_returns_script_error():
    con = make_console()
    result = con.execute("def foo(:")
    assert isinstance(result, ScriptError)
    assert "syntax" in result.message.lower() or "Syntax" in result.message


def test_runtime_exception_returns_script_error():
    con = make_console()
    result = con.execute("raise ValueError('test error')")
    assert isinstance(result, ScriptError)
    assert "test error" in result.message or "test error" in result.detail


def test_sys_exit_blocked():
    con = make_console()
    result = con.execute("import sys; sys.exit(0)")
    assert isinstance(result, ScriptError)
    assert "not allowed" in result.message.lower() or "exit" in result.message.lower()


def test_reset_namespace_clears_variables():
    con = make_console()
    con.execute("my_secret = 99")
    con.reset_namespace({"q": "mock"})
    result = con.execute("print(my_secret)")
    assert isinstance(result, ScriptError)


def test_initial_namespace_available():
    con = make_console(extra={"answer": 42})
    result = con.execute("print(answer)")
    assert isinstance(result, ScriptSuccess)
    assert "42" in result.output


def test_update_namespace_merges():
    con = make_console()
    con.update_namespace({"greeting": "hi"})
    result = con.execute("print(greeting)")
    assert isinstance(result, ScriptSuccess)
    assert "hi" in result.output
