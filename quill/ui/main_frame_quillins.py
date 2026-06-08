"""Quillins surfaces for :class:`MainFrame`: command, menu, runtime, Manager.

This mixin wires the Quillins framework (``quill.core.quillins``) into the
accessible UI:

* registers the ``tools.quillins_manager`` command (palette + Keymap Editor; no
  default binding, opened via the Tools menu);
* builds the **Quillins Manager** dialog — a hardened ``wx.Dialog`` of stock
  controls that lists installed Quillins, shows manifest/capability detail, and
  offers Enable/Disable, Reload, and Remove;
* when the SEC-8 ``core.third_party_plugins`` flag is enabled, loads enabled
  manifests, registers their ``ext.*`` commands, and runs them — snippet
  commands inline, handler commands through the out-of-process host with a
  capability + consent gate.

SEC-8 (non-negotiable for 1.0): the flag is ``locked_off``, so a shipping build
discovers nothing and runs nothing third-party. The Manager still opens and is
fully operable; it simply reports that third-party Quillins are disabled. The
live runtime paths below are reachable only when the flag is forced on (tests).

``core``/``io`` stay wx-free; this UI module owns all ``wx`` use, marshalling
editor effects on the UI thread per the host services contract.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any

from quill.core.quillins import (
    ExtensionManifest,
    SnippetContext,
    build_registry,
    expand_snippet,
)
from quill.core.quillins.host import ExtensionHost
from quill.core.quillins.loader import (
    discover_extensions,
    load_enabled_manifests,
    remove_extension,
    set_enabled,
)
from quill.core.quillins.registry import ContributionRegistry
from quill.plugins import THIRD_PARTY_PLUGINS_FEATURE

_QUILLINS_MANAGER_COMMAND = "tools.quillins_manager"


class _EditorHostServices:
    """Adapt :class:`MainFrame`'s editor to the host ``HostServices`` protocol.

    Editor writes go through the same ``wx.TextCtrl`` the user edits, so they
    participate in normal undo. Filesystem/network/clipboard methods are only
    ever reached after the host's capability + consent gate has approved them.
    """

    def __init__(self, frame: Any) -> None:
        self._frame = frame

    def get_text(self) -> str:
        return str(self._frame.editor.GetValue())

    def get_selection(self) -> str:
        return str(self._frame.editor.GetStringSelection())

    def get_cursor(self) -> dict[str, int]:
        editor = self._frame.editor
        position = int(editor.GetInsertionPoint())
        text = str(editor.GetValue())
        line = text.count("\n", 0, position) + 1
        column = position - (text.rfind("\n", 0, position) + 1) + 1
        percent = int((position / len(text)) * 100) if text else 0
        return {"line": line, "column": column, "percent": percent}

    def insert_text(self, text: str) -> None:
        self._frame.editor.WriteText(text)

    def replace_selection(self, text: str) -> None:
        editor = self._frame.editor
        start, end = editor.GetSelection()
        if start == end:
            editor.WriteText(text)
        else:
            editor.Replace(start, end, text)

    def announce(self, message: str) -> None:
        self._frame._announce(message)

    def read_file(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_file(self, path: str, text: str) -> None:
        Path(path).write_text(text, encoding="utf-8")

    def fetch(self, url: str, method: str, body: str | None) -> dict[str, Any]:
        data = body.encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            payload = response.read().decode("utf-8", errors="replace")
            return {"status": int(getattr(response, "status", 200)), "body": payload}

    def get_clipboard(self) -> str:
        return str(self._frame._read_clipboard_text())

    def set_clipboard(self, text: str) -> None:
        self._frame._write_clipboard_text(text)


class QuillinsMenuMixin:
    """Command, menu, runtime, and Manager wiring for Quillins."""

    # -- menu ----------------------------------------------------------------
    def _build_quillins_menu(self) -> object:
        """Build the Tools > Quillins submenu and bind every item.

        The Manager item is always present. When the SEC-8 flag is enabled, every
        contributed ``ext.*`` command is also listed here so it is reachable by
        keyboard even before per-menu placement; labels show any user binding via
        ``_menu_label``.
        """

        wx = self._wx
        menu = wx.Menu()

        manager_id = wx.NewIdRef()
        menu.Append(
            manager_id,
            self._menu_label("&Manage Quillins...", _QUILLINS_MANAGER_COMMAND),
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_quillins_manager(), id=manager_id)

        registry = self._quillin_registry
        if registry is not None and registry.commands:
            menu.AppendSeparator()
            for command_id, resolved in sorted(registry.commands.items()):
                item_id = wx.NewIdRef()
                menu.Append(item_id, self._menu_label(resolved.command.title, command_id))
                self.frame.Bind(
                    wx.EVT_MENU,
                    lambda _e, cid=command_id: self.run_quillin_command(cid),
                    id=item_id,
                )
        return menu

    # -- command + runtime registration --------------------------------------
    def _register_quillins_commands(self) -> None:
        self.commands.register(
            _QUILLINS_MANAGER_COMMAND,
            "Manage Quillins",
            self.open_quillins_manager,
            self._binding_for(_QUILLINS_MANAGER_COMMAND),
        )
        self._quillin_index: dict[str, tuple[ExtensionManifest, Path]] = {}
        self._quillin_registry: ContributionRegistry | None = None
        self._register_quillin_contributions()

    def _quillins_enabled(self) -> bool:
        is_enabled = getattr(self.features, "is_enabled", None)
        if not callable(is_enabled):
            return False
        return bool(is_enabled(THIRD_PARTY_PLUGINS_FEATURE))

    def _register_quillin_contributions(self) -> None:
        """Load enabled Quillins and register their commands (SEC-8 gated)."""

        self._quillin_index = {}
        self._quillin_registry = None
        if not self._quillins_enabled():
            return

        installed = {item.id: item for item in discover_extensions(self.features)}
        manifests = load_enabled_manifests(self.features)
        registry = build_registry(manifests, host_keymap=self.keymap)
        self._quillin_registry = registry

        for manifest in manifests:
            entry = installed.get(manifest.id)
            if entry is not None:
                for command in manifest.contributes.commands:
                    self._quillin_index[command.id] = (manifest, entry.directory)

        for command_id, resolved in registry.commands.items():
            binding = next(
                (h.binding for h in registry.hotkeys if h.command_id == command_id), None
            )
            try:
                self.commands.register(
                    command_id,
                    resolved.command.title,
                    lambda cid=command_id: self.run_quillin_command(cid),
                    binding,
                )
            except ValueError:
                # A duplicate id (already registered) must never crash startup.
                continue

    # -- execution -----------------------------------------------------------
    def run_quillin_command(self, command_id: str) -> None:
        """Run a contributed command: snippet inline, handler out-of-process."""

        if not self._quillins_enabled():
            self._announce("Third-party Quillins are disabled in this build.")
            return
        entry = self._quillin_index.get(command_id)
        if entry is None:
            self._announce("Quillin command is unavailable.")
            return
        manifest, directory = entry
        command = next((c for c in manifest.contributes.commands if c.id == command_id), None)
        if command is None:
            return
        if command.is_snippet and command.snippet is not None:
            self._run_quillin_snippet(command.snippet)
            return
        self._run_quillin_handler(manifest, directory, command_id)

    def _run_quillin_snippet(self, body: str) -> None:
        editor = self._frame_editor()
        context = SnippetContext(
            selection=str(editor.GetStringSelection()),
            clipboard=str(self._read_clipboard_text()),
            filename=self._current_filename(),
        )
        expansion = expand_snippet(body, context)
        start, end = editor.GetSelection()
        if start == end:
            editor.WriteText(expansion.text)
        else:
            editor.Replace(start, end, expansion.text)
        self._announce("Quillin snippet inserted.")

    def _run_quillin_handler(
        self, manifest: ExtensionManifest, directory: Path, command_id: str
    ) -> None:
        services = _EditorHostServices(self)
        host = ExtensionHost(manifest, directory, services, consent=self._quillin_consent)
        try:
            host.start()
            host.load()
            host.invoke(command_id, {})
        except Exception as error:  # surface, never crash the editor
            self._announce(f"Quillin error: {error}")
        finally:
            host.close()

    def _quillin_consent(self, capability: str, detail: str) -> bool:
        wx = self._wx
        message = (
            f"A Quillin is requesting the '{capability}' capability for:\n\n{detail}\n\n"
            "Allow this action?"
        )
        dialog = wx.MessageDialog(
            self.frame,
            message,
            "Quillin Permission Request",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        try:
            return bool(dialog.ShowModal() == wx.ID_YES)
        finally:
            dialog.Destroy()

    # -- Quillins Manager dialog (hardened custom) ---------------------------
    def open_quillins_manager(self) -> None:
        wx = self._wx
        launcher = self.frame.FindFocus() if hasattr(self.frame, "FindFocus") else None

        installed = discover_extensions(self.features)
        dialog = wx.Dialog(
            self.frame,
            title="Quillins Manager",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(dialog)
        outer = wx.BoxSizer(wx.VERTICAL)
        body = wx.BoxSizer(wx.VERTICAL)

        if self._quillins_enabled():
            intro_text = (
                "Installed Quillins. Choose one to read its details, then Enable, "
                "Disable, Reload, or Remove it."
            )
        else:
            intro_text = (
                "Third-party Quillins are disabled in this build. Installed Quillins "
                "are listed for review but cannot run until enabled."
            )
        body.Add(wx.StaticText(panel, label=intro_text), 0, wx.ALL | wx.EXPAND, 8)

        labels = [self._quillin_list_label(item) for item in installed] or [
            "(no Quillins installed)"
        ]
        chooser = wx.ListBox(panel, choices=labels)
        chooser.SetName("Installed Quillins")
        if installed:
            chooser.SetSelection(0)
        body.Add(chooser, 1, wx.ALL | wx.EXPAND, 8)

        body.Add(wx.StaticText(panel, label="&Details"), 0, wx.LEFT | wx.RIGHT, 8)
        details = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        details.SetName("Quillin details")
        body.Add(details, 1, wx.ALL | wx.EXPAND, 8)

        enable_button = wx.Button(panel, label="&Enable")
        disable_button = wx.Button(panel, label="&Disable")
        reload_button = wx.Button(panel, label="&Reload")
        remove_button = wx.Button(panel, label="Re&move...")
        close_button = wx.Button(panel, id=wx.ID_OK, label="&Close")

        actions = wx.BoxSizer(wx.HORIZONTAL)
        for button in (enable_button, disable_button, reload_button, remove_button):
            actions.Add(button, 0, wx.RIGHT, 6)
        body.Add(actions, 0, wx.ALL, 8)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(close_button)
        button_sizer.Realize()
        body.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 8)

        panel.SetSizer(body)
        outer.Add(panel, 1, wx.EXPAND)
        dialog.SetSizerAndFit(outer)
        dialog.SetSize((640, 560))
        if hasattr(dialog, "CentreOnParent"):
            dialog.CentreOnParent()

        def selected_extension() -> object | None:
            index = chooser.GetSelection()
            if not installed or index < 0 or index >= len(installed):
                return None
            return installed[index]

        def refresh_details() -> None:
            item = selected_extension()
            details.SetValue(self._quillin_detail_text(item))
            has_item = item is not None
            enable_button.Enable(has_item and self._quillins_enabled())
            disable_button.Enable(has_item and self._quillins_enabled())
            reload_button.Enable(has_item)
            remove_button.Enable(has_item)

        def on_select(_event: object) -> None:
            refresh_details()

        def on_enable(_event: object) -> None:
            item = selected_extension()
            if item is None:
                return
            set_enabled(item.id, True)
            self._register_quillin_contributions()
            self._announce(f"Enabled {item.id}.")
            refresh_details()

        def on_disable(_event: object) -> None:
            item = selected_extension()
            if item is None:
                return
            set_enabled(item.id, False)
            self._register_quillin_contributions()
            self._announce(f"Disabled {item.id}.")
            refresh_details()

        def on_reload(_event: object) -> None:
            self._register_quillin_contributions()
            self._announce("Reloaded Quillins from disk.")

        def on_remove(_event: object) -> None:
            item = selected_extension()
            if item is None:
                return
            confirm = wx.MessageDialog(
                dialog,
                f"Remove the Quillin '{item.id}'? This deletes it from disk.",
                "Remove Quillin",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            )
            try:
                approved = confirm.ShowModal() == wx.ID_YES
            finally:
                confirm.Destroy()
            if approved:
                remove_extension(item.id)
                self._register_quillin_contributions()
                self._announce(f"Removed {item.id}.")

        chooser.Bind(wx.EVT_LISTBOX, on_select)
        enable_button.Bind(wx.EVT_BUTTON, on_enable)
        disable_button.Bind(wx.EVT_BUTTON, on_disable)
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        remove_button.Bind(wx.EVT_BUTTON, on_remove)

        close_button.SetDefault()
        from quill.ui.dialog_contract import apply_modal_ids

        apply_modal_ids(dialog, affirmative_id=wx.ID_OK, escape_id=wx.ID_CANCEL)
        refresh_details()

        call_after = getattr(wx, "CallAfter", None)
        if callable(call_after):
            call_after(chooser.SetFocus)
        else:
            chooser.SetFocus()

        try:
            self._show_modal_dialog(dialog, "Quillins Manager")
        finally:
            dialog.Destroy()
            if launcher is not None and hasattr(launcher, "SetFocus"):
                launcher.SetFocus()

    # -- helpers -------------------------------------------------------------
    def _frame_editor(self) -> Any:
        return self.editor

    def _current_filename(self) -> str:
        document = getattr(self, "document", None)
        path = getattr(document, "path", None)
        if path is None:
            return ""
        return Path(str(path)).name

    def _quillin_list_label(self, item: Any) -> str:
        name = item.manifest.name if item.manifest is not None else item.id
        if item.errors:
            state = "invalid"
        elif item.enabled:
            state = "enabled"
        else:
            state = "disabled"
        return f"{name} ({state})"

    def _quillin_detail_text(self, item: Any) -> str:
        if item is None:
            return "No Quillin selected."
        lines = [f"Id: {item.id}", f"Folder: {item.directory}"]
        if item.manifest is not None:
            manifest = item.manifest
            lines.append(f"Name: {manifest.name}")
            lines.append(f"Version: {manifest.version}")
            if manifest.author:
                lines.append(f"Author: {manifest.author}")
            if manifest.description:
                lines.append(f"Description: {manifest.description}")
            caps = ", ".join(manifest.capabilities) if manifest.capabilities else "(none)"
            lines.append(f"Capabilities: {caps}")
            lines.append(f"Type: {'Python handler' if manifest.is_layer_two else 'snippet only'}")
            command_ids = ", ".join(c.id for c in manifest.contributes.commands) or "(none)"
            lines.append(f"Commands: {command_ids}")
        lines.append(f"Enabled: {'yes' if item.enabled else 'no'}")
        if item.errors:
            lines.append("")
            lines.append("Problems:")
            lines.extend(f"  - {error}" for error in item.errors)
        return "\n".join(lines)

    def _read_clipboard_text(self) -> str:
        wx = self._wx
        text = ""
        clipboard = getattr(wx, "TheClipboard", None)
        if clipboard is None or not clipboard.Open():
            return text
        try:
            data = wx.TextDataObject()
            if clipboard.GetData(data):
                text = str(data.GetText())
        finally:
            clipboard.Close()
        return text

    def _write_clipboard_text(self, text: str) -> None:
        wx = self._wx
        clipboard = getattr(wx, "TheClipboard", None)
        if clipboard is None or not clipboard.Open():
            return
        try:
            clipboard.SetData(wx.TextDataObject(text))
        finally:
            clipboard.Close()
