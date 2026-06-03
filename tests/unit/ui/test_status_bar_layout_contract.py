from __future__ import annotations

from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
    encoding="utf-8"
)


def test_status_bar_layout_dialog_parents_controls_to_dialog() -> None:
    # Regression: the Status Bar Layout dialog could not be dismissed. Controls
    # were parented to an inner wx.Panel while dialog.CreateButtonSizer()'s
    # OK/Cancel buttons (children of the dialog) were added to the panel's
    # sizer. That parent/sizer mismatch mislaid the buttons, and because
    # SetEscapeId(wx.ID_CANCEL) needs a realized Cancel button, neither the
    # buttons nor Escape could exit the dialog. The fix parents every control
    # directly to the dialog in a single sizer (the working #119 pattern).
    start = SOURCE.index("def open_status_bar_settings")
    end = SOURCE.index("def open_share_export_dialog")
    body = SOURCE[start:end]

    assert 'wx.Dialog(self.frame, title="Status Bar Layout"' in body
    # No inner panel: controls share the dialog's sizer tree.
    assert "wx.Panel(dialog)" not in body
    assert "panel.SetSizer(root)" not in body
    assert "SetSizerAndFit(outer)" not in body
    # Controls and buttons are all children of the dialog.
    assert "wx.CheckListBox(\n            dialog," in body
    assert 'wx.Button(dialog, label="Move Up")' in body
    assert "buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)" in body
    assert "dialog.SetSizer(root)" in body
    # Explicit default action and Escape mapping for predictable dismissal.
    assert "ok_button.SetDefault()" in body
    assert "apply_modal_ids(dialog, affirmative_id=wx.ID_OK, escape_id=wx.ID_CANCEL)" in body
