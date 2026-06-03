"""Banned-pattern gate (GATE-4).

Fails the build on a small set of high-value patterns that have previously
caused real bugs in Quill:

1. Bare ``wx.`` usage in ``quill/ui/main_frame.py``. The module never imports
   ``wx`` at module scope; every method that needs wx must bind it locally with
   ``wx = self._wx``. A bare ``wx.X`` where ``wx`` is not bound in the current or
   any enclosing function scope is a ``NameError`` waiting to happen (this is
   exactly the BUG-2 class).

2. Unhardened XML parsing: a direct ``ET.fromstring`` / ``etree.fromstring`` /
   ``ElementTree.fromstring`` call anywhere except ``quill/core/safe_xml.py``.
   All untrusted XML must go through ``quill.core.safe_xml.fromstring`` so
   entity-expansion attacks stay disabled (the SEC-10 class).

3. Configuration guard: ruff's undefined-name (F) and redefinition (F811)
   rules must stay enabled in ``pyproject.toml`` so undefined names and
   duplicate imports (the BUG-1 / BUG-4 classes) keep failing lint.

4. Dialog-contract guard (A11Y-4). Every ``wx.Dialog`` in ``quill/ui`` must
   follow the construction contract that the find-in-files trap (#84) and the
   status-bar / misspelling layout bugs all shared:

   * A button sizer is never added with ``wx.ALIGN_RIGHT`` (the banned
     alignment that pushed OK/Cancel off-screen and broke focus order); the
     approved pattern adds it with ``wx.EXPAND``. ``wx.ALIGN_RIGHT`` is banned
     outright in ``quill/ui`` source.
   * A module that constructs a raw ``wx.Dialog(...)`` (anything other than the
     auto-destroying ``with wx.Dialog(...)`` form) must also ``Destroy()`` it,
     so no modal dialog leaks (the crash-recovery leak class).

   This makes the bug class un-regressable and steers new dialogs to the
   approved helpers (``quill/ui/dialog_contract.py``, the stock
   ``wx.MessageDialog`` / ``SingleChoiceDialog`` / ``TextEntryDialog``, or the
   web ``show_web_form``).

Run directly (``python -m quill.tools.check_banned_patterns``) or via pytest
(``tests/unit/tools/test_check_banned_patterns.py``). Exit code is non-zero when
any violation is found.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MAIN_FRAME = _REPO_ROOT / "quill" / "ui" / "main_frame.py"
_SAFE_XML = _REPO_ROOT / "quill" / "core" / "safe_xml.py"
_PACKAGE_ROOT = _REPO_ROOT / "quill"
_UI_ROOT = _REPO_ROOT / "quill" / "ui"

# Names that, when called as ``<name>.fromstring(...)``, indicate a raw stdlib
# ElementTree parse instead of the hardened wrapper.
_RAW_XML_MODULE_NAMES = frozenset({"ET", "etree", "ElementTree"})


class Violation:
    __slots__ = ("path", "line", "message")

    def __init__(self, path: Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        rel = self.path.relative_to(_REPO_ROOT)
        return f"{rel}:{self.line}: {self.message}"


class _BareWxVisitor(ast.NodeVisitor):
    """Flag ``wx.<attr>`` where ``wx`` is not bound in any enclosing scope."""

    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []
        # Each stack frame is the set of names bound in that function scope.
        self._scopes: list[set[str]] = [set()]

    def _bound(self, name: str) -> bool:
        return any(name in scope for scope in self._scopes)

    def _collect_bindings(self, node: ast.AST, scope: set[str]) -> None:
        """Record names assigned, imported, or declared in this function body.

        Walks the function body but does NOT descend into nested function or
        class definitions (those get their own scope), so a name bound only in a
        sibling nested function does not leak here.
        """
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                scope.add(child.name)
                continue
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    self._add_target(target, scope)
            elif isinstance(child, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                self._add_target(child.target, scope)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    scope.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(child, (ast.For, ast.AsyncFor)):
                self._add_target(child.target, scope)
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                for item in child.items:
                    if item.optional_vars is not None:
                        self._add_target(item.optional_vars, scope)
            elif isinstance(child, (ast.Global, ast.Nonlocal)):
                scope.update(child.names)
            self._collect_bindings(child, scope)

    def _add_target(self, target: ast.AST, scope: set[str]) -> None:
        if isinstance(target, ast.Name):
            scope.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._add_target(element, scope)

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        scope: set[str] = set()
        args = node.args
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
            scope.add(arg.arg)
        if args.vararg:
            scope.add(args.vararg.arg)
        if args.kwarg:
            scope.add(args.kwarg.arg)
        self._collect_bindings(node, scope)
        self._scopes.append(scope)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_function(node)
        for child in node.body:
            self.visit(child)
        self._scopes.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_function(node)
        for child in node.body:
            self.visit(child)
        self._scopes.pop()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        value = node.value
        if isinstance(value, ast.Name) and value.id == "wx" and not self._bound("wx"):
            self.violations.append((
                node.lineno,
                "bare 'wx.' usage; bind 'wx = self._wx' in this scope first",
            ))
        self.generic_visit(node)


def _check_bare_wx(path: Path) -> list[Violation]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _BareWxVisitor()
    visitor.visit(tree)
    return [Violation(path, line, message) for line, message in visitor.violations]


def _check_raw_xml(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        if path == _SAFE_XML:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "fromstring"
                and isinstance(node.value, ast.Name)
                and node.value.id in _RAW_XML_MODULE_NAMES
            ):
                violations.append(
                    Violation(
                        path,
                        node.lineno,
                        f"raw '{node.value.id}.fromstring'; use quill.core.safe_xml.fromstring",
                    )
                )
    return violations


def _is_wx_dialog_call(node: ast.AST) -> bool:
    """True for a ``wx.Dialog(...)`` construction (base dialog only)."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Dialog"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "wx"
    )


def _check_dialog_contract(paths: Iterable[Path]) -> list[Violation]:
    """Enforce the A11Y-4 dialog construction contract in ``quill/ui``.

    * ``wx.ALIGN_RIGHT`` is banned outright (button sizers use ``wx.EXPAND``).
    * A module that builds a raw ``wx.Dialog(...)`` (not the auto-destroying
      ``with wx.Dialog(...)`` form) must also ``Destroy()`` a dialog somewhere
      in the module, so modal dialogs never leak.
    """
    violations: list[Violation] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        # Collect the wx.Dialog calls that are the context expression of a
        # ``with`` statement; those auto-destroy and are exempt from the
        # explicit-Destroy requirement.
        managed_dialog_calls: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if _is_wx_dialog_call(item.context_expr):
                        managed_dialog_calls.add(id(item.context_expr))

        has_raw_dialog = False
        has_destroy = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "ALIGN_RIGHT"
                and isinstance(node.value, ast.Name)
                and node.value.id == "wx"
            ):
                violations.append(
                    Violation(
                        path,
                        node.lineno,
                        "wx.ALIGN_RIGHT is banned in quill/ui; add button "
                        "sizers with wx.EXPAND (A11Y-4 dialog contract)",
                    )
                )
            if _is_wx_dialog_call(node) and id(node) not in managed_dialog_calls:
                has_raw_dialog = True
            if isinstance(node, ast.Attribute) and node.attr == "Destroy":
                has_destroy = True

        if has_raw_dialog and not has_destroy:
            violations.append(
                Violation(
                    path,
                    0,
                    "constructs a raw wx.Dialog but never calls .Destroy(); "
                    "Destroy the dialog or use 'with wx.Dialog(...)' "
                    "(A11Y-4 dialog contract)",
                )
            )
    return violations


def _check_ruff_config() -> list[Violation]:
    pyproject = _REPO_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    select = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("select", [])
    if "F" not in select:
        return [
            Violation(
                pyproject,
                0,
                "ruff lint.select must include 'F' (undefined names F821, "
                "redefinition F811) so banned name patterns keep failing lint",
            )
        ]
    return []


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    violations.extend(_check_bare_wx(_MAIN_FRAME))
    violations.extend(_check_raw_xml(sorted(_PACKAGE_ROOT.rglob("*.py"))))
    violations.extend(_check_dialog_contract(sorted(_UI_ROOT.rglob("*.py"))))
    violations.extend(_check_ruff_config())
    return violations


def main() -> int:
    violations = find_violations()
    if not violations:
        print("Banned-pattern gate: no violations.")
        return 0
    print("Banned-pattern gate found violations:")
    for violation in violations:
        print(f"  {violation}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
