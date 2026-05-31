from __future__ import annotations

from quill.core.sticky_notes import (
    StickyNote,
    delete_sticky_note,
    load_sticky_notes,
    save_sticky_note,
)

class StickyNoteEditorDialog:
    def __init__(self, parent: object, note: StickyNote | None = None) -> None:
        import wx

        self._wx = wx
        self._note = note
        self.dialog = wx.Dialog(
            parent,
            title="New Sticky Note" if note is None else "Edit Sticky Note",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((720, 540))

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label="Type your note. Press Escape to save. The first line becomes the title.",
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )
        self.body = wx.TextCtrl(
            self.dialog,
            value=note.body if note is not None else "",
            style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB,
        )
        root.Add(self.body, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        buttons = self.dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            ok_button = buttons.FindWindowById(wx.ID_OK)
            if ok_button is not None:
                ok_button.SetLabel("Save")
            root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.dialog.SetSizer(root)
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        self.body.SetFocus()

    def show_modal_and_get_body(self) -> str | None:
        self.dialog.CentreOnParent()
        try:
            result = self.dialog.ShowModal()
            if result != self._wx.ID_OK:
                return None
            return self.body.GetValue()
        finally:
            self.dialog.Destroy()

    def _on_char_hook(self, event: object) -> None:
        if event.GetKeyCode() == self._wx.WXK_ESCAPE:
            self.dialog.EndModal(self._wx.ID_OK)
            return
        event.Skip()


class StickyNotesVaultDialog:
    def __init__(self, parent: object) -> None:
        import wx

        self._wx = wx
        self.dialog = wx.Dialog(
            parent,
            title="Quill Notes Vault",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((900, 620))
        self._notes: list[StickyNote] = []

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label="Manage global sticky notes. Delete removes the selected note. Ctrl+C copies it.",
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )
        self.list = wx.ListCtrl(
            self.dialog,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
        )
        self.list.AppendColumn("Title", width=260)
        self.list.AppendColumn("Updated", width=180)
        self.list.AppendColumn("Preview", width=420)
        root.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.preview = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 140),
        )
        root.Add(self.preview, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.new_button = wx.Button(self.dialog, label="New")
        self.edit_button = wx.Button(self.dialog, label="Edit")
        self.copy_button = wx.Button(self.dialog, label="Copy")
        self.delete_button = wx.Button(self.dialog, label="Delete")
        self.close_button = wx.Button(self.dialog, id=wx.ID_OK, label="Close")
        for control in (
            self.new_button,
            self.edit_button,
            self.copy_button,
            self.delete_button,
            self.close_button,
        ):
            buttons.Add(control, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer(1)
        root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.dialog.SetSizer(root)

        self.new_button.Bind(wx.EVT_BUTTON, lambda _e: self._create_note())
        self.edit_button.Bind(wx.EVT_BUTTON, lambda _e: self._edit_selected())
        self.copy_button.Bind(wx.EVT_BUTTON, lambda _e: self._copy_selected())
        self.delete_button.Bind(wx.EVT_BUTTON, lambda _e: self._delete_selected())
        self.close_button.Bind(wx.EVT_BUTTON, lambda _e: self.dialog.EndModal(wx.ID_OK))
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection_changed)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda _e: self._edit_selected())
        self.list.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        self._refresh()

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _refresh(self, select_note_id: str | None = None) -> None:
        wx = self._wx
        self._notes = load_sticky_notes()
        self.list.DeleteAllItems()
        selected_index = 0
        for index, note in enumerate(self._notes):
            item = self.list.InsertItem(index, note.title)
            self.list.SetItem(item, 1, note.updated_at.replace("T", " ")[:19])
            preview = note.body.splitlines()[1] if len(note.body.splitlines()) > 1 else note.body
            self.list.SetItem(item, 2, preview[:120])
            if select_note_id is not None and note.id == select_note_id:
                selected_index = index
        if self._notes:
            self.list.SetItemState(
                selected_index,
                wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
            )
            self.list.EnsureVisible(selected_index)
        self._update_preview()

    def _selected_note(self) -> StickyNote | None:
        index = self.list.GetFirstSelected()
        if index == -1 or index >= len(self._notes):
            return None
        return self._notes[index]

    def _update_preview(self) -> None:
        note = self._selected_note()
        if note is None:
            self.preview.SetValue("No sticky note selected.")
            return
        self.preview.SetValue(
            f"Title: {note.title}\nCreated: {note.created_at}\nUpdated: {note.updated_at}\n\n{note.body}"
        )

    def _on_selection_changed(self, _event: object) -> None:
        self._update_preview()

    def _on_char_hook(self, event: object) -> None:
        key_code = event.GetKeyCode()
        if key_code == self._wx.WXK_DELETE:
            self._delete_selected()
            return
        if key_code in (self._wx.WXK_RETURN, self._wx.WXK_NUMPAD_ENTER):
            self._edit_selected()
            return
        if key_code == ord("C") and event.ControlDown():
            self._copy_selected()
            return
        if key_code == self._wx.WXK_F10 and event.ShiftDown():
            self._show_context_menu()
            return
        if key_code == getattr(self._wx, "WXK_MENU", -1):
            self._show_context_menu()
            return
        if key_code == self._wx.WXK_ESCAPE:
            self.dialog.EndModal(self._wx.ID_OK)
            return
        event.Skip()

    def _on_context_menu(self, event: object) -> None:
        self._show_context_menu()

    def _show_context_menu(self) -> None:
        menu = self._wx.Menu()
        new_id = self._wx.NewIdRef()
        edit_id = self._wx.NewIdRef()
        copy_id = self._wx.NewIdRef()
        delete_id = self._wx.NewIdRef()
        menu.Append(new_id, "New Sticky Note")
        menu.Append(edit_id, "Edit Sticky Note")
        menu.Append(copy_id, "Copy Sticky Note")
        menu.Append(delete_id, "Delete Sticky Note")
        menu.Bind(self._wx.EVT_MENU, lambda _e: self._create_note(), id=new_id)
        menu.Bind(self._wx.EVT_MENU, lambda _e: self._edit_selected(), id=edit_id)
        menu.Bind(self._wx.EVT_MENU, lambda _e: self._copy_selected(), id=copy_id)
        menu.Bind(self._wx.EVT_MENU, lambda _e: self._delete_selected(), id=delete_id)
        self.list.PopupMenu(menu)
        menu.Destroy()

    def _create_note(self) -> None:
        editor = StickyNoteEditorDialog(self.dialog)
        body = editor.show_modal_and_get_body()
        if body is None:
            return
        note = save_sticky_note(body)
        self._refresh(select_note_id=note.id)

    def _edit_selected(self) -> None:
        note = self._selected_note()
        if note is None:
            return
        editor = StickyNoteEditorDialog(self.dialog, note=note)
        body = editor.show_modal_and_get_body()
        if body is None:
            return
        updated = save_sticky_note(body, note_id=note.id)
        self._refresh(select_note_id=updated.id)

    def _copy_selected(self) -> None:
        note = self._selected_note()
        if note is None:
            return
        clipboard = self._wx.TheClipboard
        if not clipboard.Open():
            return
        try:
            clipboard.SetData(self._wx.TextDataObject(note.body))
        finally:
            clipboard.Close()

    def _delete_selected(self) -> None:
        note = self._selected_note()
        if note is None:
            return
        if (
            self._wx.MessageBox(
                f"Delete sticky note \"{note.title}\"?",
                "Delete Sticky Note",
                self._wx.ICON_WARNING | self._wx.YES_NO | self._wx.NO_DEFAULT,
                self.dialog,
            )
            != self._wx.YES
        ):
            return
        if delete_sticky_note(note.id):
            self._refresh()
