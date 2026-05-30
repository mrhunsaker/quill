"""AI Model settings — choose which on-device model Quill uses.

Defaults to "Recommended" (picked from the machine's RAM). The chosen model is
downloaded automatically (no manual file handling). Accessible; download runs
off the UI thread.
"""
from __future__ import annotations

import threading

from quill.core.ai.model_manager import (
    MODELS,
    ensure_model,
    is_downloaded,
    load_model_choice,
    recommended_id,
    resolve_spec,
    save_model_choice,
    total_ram_gb,
)


class AIModelDialog:
    def __init__(self, parent: object, announce=None) -> None:
        import wx

        self._wx = wx
        self._announce = announce or (lambda _m: None)

        self.dialog = wx.Dialog(parent, title="AI Model", style=wx.DEFAULT_DIALOG_STYLE)
        self.dialog.SetSize((540, 380))
        root = wx.BoxSizer(wx.VERTICAL)

        rec = recommended_id()
        root.Add(
            wx.StaticText(
                self.dialog,
                label=f"This computer has about {total_ram_gb():.0f} GB of RAM.\n"
                f"Recommended model: {MODELS[rec].name}.",
            ),
            0, wx.ALL, 12,
        )

        root.Add(wx.StaticText(self.dialog, label="Model"), 0, wx.LEFT | wx.RIGHT, 12)
        self._ids = ["auto", *MODELS.keys()]
        labels = [f"Recommended ({MODELS[rec].name})"]
        for model_id, spec in MODELS.items():
            tags = []
            if model_id == rec:
                tags.append("recommended")
            if is_downloaded(spec):
                tags.append("downloaded")
            suffix = f" — {', '.join(tags)}" if tags else ""
            labels.append(f"{spec.name} (~{spec.approx_gb:g} GB){suffix}")
        self.choice = wx.Choice(self.dialog, choices=labels)
        self.choice.SetName("AI model")
        current = load_model_choice()
        self.choice.SetSelection(self._ids.index(current) if current in self._ids else 0)
        root.Add(self.choice, 0, wx.EXPAND | wx.ALL, 12)

        self.status = wx.StaticText(self.dialog, label="")
        root.Add(self.status, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.download_button = wx.Button(self.dialog, label="Download Now")
        buttons.Add(self.download_button, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer()
        buttons.Add(wx.Button(self.dialog, wx.ID_OK, label="Save"), 0, wx.RIGHT, 8)
        buttons.Add(wx.Button(self.dialog, wx.ID_CANCEL, label="Cancel"), 0)
        root.Add(buttons, 0, wx.EXPAND | wx.ALL, 12)
        self.dialog.SetSizer(root)

        self.choice.Bind(wx.EVT_CHOICE, lambda _e: self._refresh_status())
        self.download_button.Bind(wx.EVT_BUTTON, self._on_download)
        self._refresh_status()

    def _selected_id(self) -> str:
        return self._ids[self.choice.GetSelection()]

    def _refresh_status(self) -> None:
        spec = resolve_spec(self._selected_id())
        state = "already downloaded" if is_downloaded(spec) else "downloads automatically on first use"
        self.status.SetLabel(f"{spec.note}\n{spec.name} (~{spec.approx_gb:g} GB) — {state}.")

    def _on_download(self, _event: object) -> None:
        save_model_choice(self._selected_id())
        self.download_button.Enable(False)
        self.status.SetLabel("Downloading… this can take a while.")
        self._announce("Downloading model")

        def worker() -> None:
            try:
                path = ensure_model()
                message = f"Downloaded. Using: {path}"
            except Exception as exc:  # noqa: BLE001
                message = f"Download failed: {exc}"
            self._wx.CallAfter(self._after_download, message)

        threading.Thread(target=worker, daemon=True).start()

    def _after_download(self, message: str) -> None:
        self.download_button.Enable(True)
        self.status.SetLabel(message)
        self._announce("Download finished")

    def show(self) -> None:
        wx = self._wx
        self.dialog.CentreOnParent()
        try:
            if self.dialog.ShowModal() == wx.ID_OK:
                save_model_choice(self._selected_id())
                self._announce("Saved AI model choice")
        finally:
            self.dialog.Destroy()
