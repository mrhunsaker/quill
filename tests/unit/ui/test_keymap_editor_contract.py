from __future__ import annotations

from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
    encoding="utf-8"
)


def test_keymap_editor_uses_persistent_dialog_with_inline_bindings() -> None:
    # Issue #117 part 1 + 2: the editor is a persistent dialog whose list shows
    # each command's current binding inline (or "Unassigned"), and a single edit
    # returns to the list rather than dismissing the dialog.
    start = SOURCE.index("def open_keymap_editor")
    end = SOURCE.index("def _apply_keymap_binding")
    body = SOURCE[start:end]

    assert 'wx.Dialog(self.frame, title="Keymap Editor"' in body
    assert "wx.ListBox(dialog" in body
    assert "or 'Unassigned'" in body
    assert "self._binding_for(command_id)" in body
    assert "def edit_selected" in body
    assert "self._apply_keymap_binding(command_id, new_binding)" in body
    assert "refresh_list(keep=selected)" in body
    # Double-click and an explicit Edit button both trigger editing.
    assert "EVT_LISTBOX_DCLICK, edit_selected" in body
    assert 'wx.Button(dialog, label="&Edit Keybinding...")' in body
    # Issue #119: controls are parented to the dialog (not an inner panel) so the
    # OK button shares the dialog's sizer tree and can dismiss the dialog.
    assert "wx.Panel(dialog)" not in body
    assert "dialog.SetSizer(root)" in body


def test_apply_keymap_binding_validates_and_persists() -> None:
    start = SOURCE.index("def _apply_keymap_binding")
    end = SOURCE.index("def ", start + 1)
    body = SOURCE[start:end]

    assert "if not new_binding:" in body
    assert "self._parse_keybinding(new_binding) is None" in body
    assert "find_keymap_conflict(self.keymap, command_id, new_binding)" in body
    assert "self.keymap[command_id] = new_binding" in body
    assert "save_keymap(self.keymap)" in body


def test_keyboard_reference_opens_html_in_browser() -> None:
    # Issue #117 part 3: the Help -> Open Keyboard Reference command renders the
    # shared accessible HTML table and opens it in the browser.
    start = SOURCE.index("def open_keyboard_reference")
    end = SOURCE.index("def open_user_guide")
    body = SOURCE[start:end]

    assert "build_keyboard_shortcut_html(self.commands.list(), self.features)" in body
    assert "keyboard-shortcuts" in body
    assert "os.replace(temp_path, target_path)" in body
    assert "webbrowser.open(target_path.as_uri())" in body
