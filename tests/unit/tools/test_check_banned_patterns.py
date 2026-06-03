from __future__ import annotations

import ast
from pathlib import Path

from quill.tools.check_banned_patterns import (
    _BareWxVisitor,
    _check_dialog_contract,
    _check_raw_xml,
    find_violations,
)


def _bare_wx_violations(source: str) -> list[tuple[int, str]]:
    visitor = _BareWxVisitor()
    visitor.visit(ast.parse(source))
    return visitor.violations


def test_clean_tree_has_no_violations() -> None:
    assert find_violations() == []


def test_bare_wx_without_local_binding_is_flagged() -> None:
    # The BUG-2 class: wx is never imported at module scope, so this is a
    # NameError at runtime.
    source = "class Frame:\n    def do(self):\n        return wx.GetTextFromUser('x')\n"
    violations = _bare_wx_violations(source)
    assert len(violations) == 1
    assert "bare 'wx.'" in violations[0][1]


def test_wx_bound_to_self_attr_is_allowed() -> None:
    source = (
        "class Frame:\n"
        "    def do(self):\n"
        "        wx = self._wx\n"
        "        return wx.GetTextFromUser('x')\n"
    )
    assert _bare_wx_violations(source) == []


def test_wx_from_enclosing_scope_in_nested_function_is_allowed() -> None:
    source = (
        "class Frame:\n"
        "    def do(self):\n"
        "        wx = self._wx\n"
        "        def cb():\n"
        "            return wx.CallAfter(lambda: None)\n"
        "        return cb\n"
    )
    assert _bare_wx_violations(source) == []


def test_wx_as_parameter_is_allowed() -> None:
    source = "def helper(wx):\n    return wx.ID_OK\n"
    assert _bare_wx_violations(source) == []


def test_raw_et_fromstring_outside_safe_xml_is_flagged(tmp_path: Path) -> None:
    module = tmp_path / "reader.py"
    module.write_text(
        "import xml.etree.ElementTree as ET\n\n\n"
        "def parse(text):\n    return ET.fromstring(text)\n",
        encoding="utf-8",
    )
    violations = _check_raw_xml([module])
    assert len(violations) == 1
    assert "safe_xml" in violations[0].message


def test_safe_xml_fromstring_call_is_not_flagged(tmp_path: Path) -> None:
    module = tmp_path / "reader.py"
    module.write_text(
        "from quill.core.safe_xml import fromstring\n\n\n"
        "def parse(text):\n    return fromstring(text)\n",
        encoding="utf-8",
    )
    assert _check_raw_xml([module]) == []


def test_dialog_align_right_is_flagged(tmp_path: Path) -> None:
    # The A11Y-4 bug class: button sizers added with wx.ALIGN_RIGHT pushed
    # OK/Cancel off-screen and broke focus order.
    module = tmp_path / "panel.py"
    module.write_text(
        "def build(self):\n"
        "    dialog = wx.Dialog(self)\n"
        "    root.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 8)\n"
        "    dialog.Destroy()\n",
        encoding="utf-8",
    )
    violations = _check_dialog_contract([module])
    assert any("ALIGN_RIGHT" in v.message for v in violations)


def test_dialog_expand_button_sizer_is_allowed(tmp_path: Path) -> None:
    module = tmp_path / "panel.py"
    module.write_text(
        "def build(self):\n"
        "    dialog = wx.Dialog(self)\n"
        "    buttons.AddStretchSpacer(1)\n"
        "    root.Add(buttons, 0, wx.ALL | wx.EXPAND, 8)\n"
        "    dialog.Destroy()\n",
        encoding="utf-8",
    )
    assert _check_dialog_contract([module]) == []


def test_raw_dialog_without_destroy_is_flagged(tmp_path: Path) -> None:
    # The crash-recovery leak class: a modal dialog built but never destroyed.
    module = tmp_path / "panel.py"
    module.write_text(
        "def build(self):\n    dialog = wx.Dialog(self)\n    dialog.ShowModal()\n",
        encoding="utf-8",
    )
    violations = _check_dialog_contract([module])
    assert any("Destroy" in v.message for v in violations)


def test_with_dialog_form_is_exempt_from_destroy(tmp_path: Path) -> None:
    # The auto-destroying context-manager form needs no explicit Destroy().
    module = tmp_path / "panel.py"
    module.write_text(
        "def build(self):\n    with wx.Dialog(self) as dialog:\n        dialog.ShowModal()\n",
        encoding="utf-8",
    )
    assert _check_dialog_contract([module]) == []
