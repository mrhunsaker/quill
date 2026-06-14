"""Page implementations for the QUILL setup wizard.

Each page is a ``wx.Panel`` subclass. ``SetupWizardDialog`` hosts all pages
inside a single ``wx.Dialog``, showing one at a time with Back/Next/Finish
navigation.

Pages (in order):
  0 - Welcome
  1 - Keyboard and Sound
  2 - Feature Profile
  3 - Remote Access
  4 - AI Assistance
  5 - Reading and Accessibility
  6 - Writing Tools
  7 - Watch Folder
  8 - Startup Behaviour
  9 - Summary

Feature toggles are held in ``_pending_overrides: dict[str, str]`` inside
the dialog and applied to the ``FeatureManager`` only when the user clicks
Finish, keeping the wizard transactional.
"""

from __future__ import annotations

import logging

import wx

from quill.core.features import (
    FEATURE_STATE_OFF,
    FEATURE_STATE_ON,
    PROFILE_DEFINITIONS,
    FeatureManager,
)
from quill.core.settings import Settings
from quill.ui.dialog_contract import apply_modal_ids

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual pages
# ---------------------------------------------------------------------------


class _WizardPage(wx.Panel):
    """Base for all wizard page panels."""

    def __init__(self, parent: wx.Window, name: str) -> None:
        super().__init__(parent)
        self.SetName(name)

    # The page panel is a layout container, not a control: keep it out of the
    # Tab order so keyboard users never land on an empty "panel" between the
    # real controls. wxWidgets consults these on every traversal step.
    def AcceptsFocus(self) -> bool:  # noqa: N802 - wx override
        return False

    def AcceptsFocusFromKeyboard(self) -> bool:  # noqa: N802 - wx override
        return False


class _WelcomePage(_WizardPage):
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Welcome")
        sizer = wx.BoxSizer(wx.VERTICAL)
        heading = wx.StaticText(
            self,
            label="Welcome to QUILL",
            name="wizard.welcome_heading",
        )
        heading.SetFont(heading.GetFont().Scaled(1.4).Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        body = wx.StaticText(
            self,
            label=(
                "This short wizard helps you personalise QUILL for the way "
                "you work. It takes about two minutes. You can skip ahead at "
                "any time and re-run it later from Help > Personalise QUILL."
            ),
            name="wizard.welcome_body",
        )
        body.Wrap(440)
        sizer.Add(body, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self.SetSizer(sizer)

    def collect(self, _settings: Settings, _overrides: dict) -> None:
        pass


class _KeyboardSoundPage(_WizardPage):
    # (value, label) for the indentation-tone scale. "" turns tones off.
    _INDENT_TONE_CHOICES: tuple[tuple[str, str], ...] = (
        ("", "Off"),
        ("pentatonic", "Pentatonic (no dissonance)"),
        ("whole_tone", "Whole tone (even steps)"),
        ("diatonic", "Diatonic C major (familiar)"),
        ("chromatic", "Chromatic (one semitone per level)"),
    )

    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Keyboard and Sound")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Keyboard and Sound", name="wizard.kb_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "Choose a keyboard layout and how QUILL uses sound: earcons, a "
                "sound pack, and optional indentation tones for code. Sound is "
                "always optional and never replaces speech."
            ),
            name="wizard.kb_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1, 1)

        pack_label = wx.StaticText(self, label="Keyboard pack:", name="wizard.kb_pack_label")
        self._pack = wx.Choice(self, name="wizard.kb_pack_choice")
        self._pack.Append("QUILL Default")
        self._pack.Append("JAWS Compatible")
        self._pack.Append("NVDA Compatible")
        self._pack.Append("Narrator Compatible")
        current = settings.keyboard_pack
        idx = self._pack.FindString(current)
        self._pack.SetSelection(idx if idx != wx.NOT_FOUND else 0)
        grid.Add(pack_label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._pack, flag=wx.EXPAND)

        # Master sound toggle (earcons). The label lives on the checkbox itself
        # so screen readers announce it (#208); an empty cell keeps the grid
        # aligned.
        self._sound_enabled = wx.CheckBox(
            self, label="Play sound notifications (earcons)", name="wizard.sound_enabled_check"
        )
        self._sound_enabled.SetValue(bool(getattr(settings, "sound_enabled", True)))
        grid.Add(wx.StaticText(self, label=""), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._sound_enabled)

        # Sound pack: a read-only display plus a Browse button (empty path means
        # the bundled Ink pack).
        self._sound_pack_path = str(getattr(settings, "sound_pack_path", "") or "")
        pack_row_label = wx.StaticText(self, label="Sound pack:", name="wizard.sound_pack_label")
        pack_row = wx.BoxSizer(wx.HORIZONTAL)
        self._sound_pack_display = wx.StaticText(
            self, label=self._sound_pack_name(), name="wizard.sound_pack_display"
        )
        choose_pack = wx.Button(self, label="Choose...", name="wizard.sound_pack_choose")
        choose_pack.Bind(wx.EVT_BUTTON, self._on_choose_sound_pack)
        pack_row.Add(self._sound_pack_display, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        pack_row.Add(choose_pack, 0)
        grid.Add(pack_row_label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(pack_row, flag=wx.EXPAND)

        # Indentation tones for code (off by default).
        indent_label = wx.StaticText(
            self, label="Indentation tones:", name="wizard.indent_tone_label"
        )
        self._indent = wx.Choice(
            self,
            name="wizard.indent_tone_choice",
            choices=[label for _value, label in self._INDENT_TONE_CHOICES],
        )
        current_scale = str(getattr(settings, "indent_tone_scale", "") or "")
        indent_idx = next(
            (
                i
                for i, (value, _l) in enumerate(self._INDENT_TONE_CHOICES)
                if value == current_scale
            ),
            0,
        )
        self._indent.SetSelection(indent_idx)
        grid.Add(indent_label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._indent, flag=wx.EXPAND)

        sizer.Add(grid, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)
        self.SetSizer(sizer)

    def _sound_pack_name(self) -> str:
        if not self._sound_pack_path:
            return "Bundled Ink pack (default)"
        from pathlib import Path

        return Path(self._sound_pack_path).name or self._sound_pack_path

    def _on_choose_sound_pack(self, _event: object) -> None:
        with wx.FileDialog(
            self,
            "Choose a sound pack (.qsp)",
            wildcard="Sound packs (*.qsp)|*.qsp|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._sound_pack_path = dlg.GetPath()
        self._sound_pack_display.SetLabel(self._sound_pack_name())
        self.Layout()

    def collect(self, settings: Settings, _overrides: dict) -> None:
        settings.keyboard_pack = self._pack.GetStringSelection() or "QUILL Default"
        settings.sound_enabled = self._sound_enabled.GetValue()
        settings.sound_pack_path = self._sound_pack_path
        selection = self._indent.GetSelection()
        if 0 <= selection < len(self._INDENT_TONE_CHOICES):
            settings.indent_tone_scale = self._INDENT_TONE_CHOICES[selection][0]


class _ProfilePage(_WizardPage):
    def __init__(self, parent: wx.Window, feature_manager: FeatureManager) -> None:
        super().__init__(parent, "Feature Profile")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Feature Profile", name="wizard.profile_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "Profiles control which features are visible. Choose the one "
                "that best describes how you use QUILL. You can change it "
                "at any time from Help > Personalise QUILL."
            ),
            name="wizard.profile_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        # A single RadioBox (not a row of individual RadioButtons): arrow keys
        # navigate within the group and wrap top-to-bottom, instead of escaping
        # into the Back/Next/Cancel buttons at the ends (#209). Screen readers
        # also announce it as one labelled radio group.
        self._profiles: list[str] = list(PROFILE_DEFINITIONS.keys())
        choices = [
            f"{profile.name}  -  {profile.description}" for profile in PROFILE_DEFINITIONS.values()
        ]
        self._radio = wx.RadioBox(
            self,
            label="Choose a profile",
            choices=choices,
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            name="wizard.profile_choices",
        )
        try:
            active_index = self._profiles.index(feature_manager.active_profile_id)
        except ValueError:
            active_index = 0
        self._radio.SetSelection(active_index)
        sizer.Add(self._radio, flag=wx.ALL, border=12)

        self.SetSizer(sizer)

    def collect(self, _settings: Settings, overrides: dict) -> None:
        index = self._radio.GetSelection()
        if 0 <= index < len(self._profiles):
            overrides["_profile"] = self._profiles[index]


class _RemoteAccessPage(_WizardPage):
    def __init__(self, parent: wx.Window, feature_manager: FeatureManager) -> None:
        super().__init__(parent, "Remote Access")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Remote Access", name="wizard.remote_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "Remote Access lets you open and save files on FTP, SFTP, "
                "WebDAV, and S3 servers directly from QUILL. If you do not "
                "use remote servers, turn this off to keep the File menu simple."
            ),
            name="wizard.remote_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._enable = wx.CheckBox(
            self,
            label="Enable Remote Access",
            name="wizard.remote_enable",
        )
        self._enable.SetValue(feature_manager.is_enabled("core.remote"))
        sizer.Add(self._enable, flag=wx.LEFT | wx.BOTTOM, border=12)
        self.SetSizer(sizer)

    def collect(self, _settings: Settings, overrides: dict) -> None:
        state = FEATURE_STATE_ON if self._enable.GetValue() else FEATURE_STATE_OFF
        overrides["core.remote"] = state


class _AIPage(_WizardPage):
    def __init__(self, parent: wx.Window, feature_manager: FeatureManager) -> None:
        super().__init__(parent, "AI Assistance")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="AI Assistance", name="wizard.ai_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "QUILL can connect to AI services to help you rewrite, "
                "summarise, and continue your writing. An API key is "
                "required. If you do not want AI features, turn this off "
                "to hide them from all menus and the command palette."
            ),
            name="wizard.ai_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._enable = wx.CheckBox(
            self,
            label="Enable AI Assistance",
            name="wizard.ai_enable",
        )
        self._enable.SetValue(feature_manager.is_enabled("future.ai"))
        self._enable.Bind(wx.EVT_CHECKBOX, self._on_toggle)
        sizer.Add(self._enable, flag=wx.LEFT | wx.BOTTOM, border=12)

        self._note = wx.StaticText(
            self,
            label=("Note: you can add your API key later in Help > Personalise QUILL > AI."),
            name="wizard.ai_note",
        )
        self._note.Wrap(440)
        self._note.Show(self._enable.GetValue())
        sizer.Add(self._note, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self.SetSizer(sizer)

    def _on_toggle(self, _: wx.CommandEvent) -> None:
        self._note.Show(self._enable.GetValue())
        self.Layout()

    def collect(self, _settings: Settings, overrides: dict) -> None:
        state = FEATURE_STATE_ON if self._enable.GetValue() else FEATURE_STATE_OFF
        overrides["future.ai"] = state


class _ReadingAccessibilityPage(_WizardPage):
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Reading and Accessibility")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(
            self, label="Reading and Accessibility", name="wizard.reading_heading"
        )
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "QUILL is screen-reader-first and auto-detects your reader. "
                "These options control the built-in Read Aloud voice and "
                "spoken announcement verbosity."
            ),
            name="wizard.reading_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1, 1)

        verb_label = wx.StaticText(
            self, label="Announcement verbosity:", name="wizard.reading_verb_label"
        )
        self._verbosity = wx.Choice(self, name="wizard.reading_verbosity")
        for value, label in [("minimal", "Minimal"), ("normal", "Normal"), ("verbose", "Verbose")]:
            self._verbosity.Append(label, value)
        cur = settings.announcement_verbosity
        idx = next(
            (
                i
                for i in range(self._verbosity.GetCount())
                if self._verbosity.GetClientData(i) == cur
            ),
            1,
        )
        self._verbosity.SetSelection(idx)
        grid.Add(verb_label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._verbosity, flag=wx.EXPAND)

        sizer.Add(grid, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)
        self.SetSizer(sizer)

    def collect(self, settings: Settings, _overrides: dict) -> None:
        idx = self._verbosity.GetSelection()
        if idx != wx.NOT_FOUND:
            data = self._verbosity.GetClientData(idx)
            if data:
                settings.announcement_verbosity = data


class _WritingToolsPage(_WizardPage):
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Writing Tools")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Writing Tools", name="wizard.writing_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label="Choose which writing helpers are active as you type.",
            name="wizard.writing_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._spellcheck = wx.CheckBox(
            self,
            label="Spell check as you type",
            name="wizard.writing_spellcheck",
        )
        self._spellcheck.SetValue(settings.spellcheck_as_you_type)
        sizer.Add(self._spellcheck, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._intellisense = wx.CheckBox(
            self,
            label="Word prediction and tag IntelliSense",
            name="wizard.writing_intellisense",
        )
        self._intellisense.SetValue(settings.intellisense_as_you_type)
        sizer.Add(self._intellisense, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._smart_quotes = wx.CheckBox(
            self,
            label="Autoformat straight quotes to curly",
            name="wizard.writing_smart_quotes",
        )
        self._smart_quotes.SetValue(settings.autoformat_smart_quotes)
        sizer.Add(self._smart_quotes, flag=wx.LEFT | wx.BOTTOM, border=8)

        self.SetSizer(sizer)

    def collect(self, settings: Settings, _overrides: dict) -> None:
        settings.spellcheck_as_you_type = self._spellcheck.GetValue()
        settings.intellisense_as_you_type = self._intellisense.GetValue()
        settings.autoformat_smart_quotes = self._smart_quotes.GetValue()


class _StartupBehaviourPage(_WizardPage):
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Startup Behaviour")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Startup Behaviour", name="wizard.startup_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label="Control what QUILL does when it first opens.",
            name="wizard.startup_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._no_doc = wx.CheckBox(
            self,
            label="Start with no document open",
            name="wizard.startup_no_doc",
        )
        self._no_doc.SetValue(settings.start_with_no_document_open)
        sizer.Add(self._no_doc, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._updates = wx.CheckBox(
            self,
            label="Check for updates on startup",
            name="wizard.startup_updates",
        )
        self._updates.SetValue(settings.auto_check_updates)
        sizer.Add(self._updates, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._tray = wx.CheckBox(
            self,
            label="Enable system tray icon",
            name="wizard.startup_tray",
        )
        self._tray.SetValue(settings.tray_enabled)
        sizer.Add(self._tray, flag=wx.LEFT | wx.BOTTOM, border=8)

        self.SetSizer(sizer)

    def collect(self, settings: Settings, _overrides: dict) -> None:
        settings.start_with_no_document_open = self._no_doc.GetValue()
        settings.auto_check_updates = self._updates.GetValue()
        settings.tray_enabled = self._tray.GetValue()


class _WatchFolderPage(_WizardPage):
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        super().__init__(parent, "Watch Folder")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="Watch Folder", name="wizard.watch_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        desc = wx.StaticText(
            self,
            label=(
                "QUILL can watch a folder and process files that arrive there. "
                "This is optional; leave it off if you are not sure."
            ),
            name="wizard.watch_desc",
        )
        desc.Wrap(440)
        sizer.Add(desc, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._enable = wx.CheckBox(self, label="Enable watch folder", name="wizard.watch_enable")
        self._enable.SetValue(bool(getattr(settings, "watch_folder_enabled", False)))
        sizer.Add(self._enable, flag=wx.LEFT | wx.BOTTOM, border=12)

        folder_label = wx.StaticText(
            self, label="Folder to watch:", name="wizard.watch_folder_label"
        )
        sizer.Add(folder_label, flag=wx.LEFT, border=12)
        folder_row = wx.BoxSizer(wx.HORIZONTAL)
        self._folder_path = str(getattr(settings, "watch_folder_path", "") or "")
        self._folder_display = wx.StaticText(
            self, label=self._folder_name(), name="wizard.watch_folder_display"
        )
        choose = wx.Button(self, label="Choose Folder...", name="wizard.watch_folder_choose")
        choose.Bind(wx.EVT_BUTTON, self._on_choose_folder)
        folder_row.Add(self._folder_display, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        folder_row.Add(choose, 0)
        sizer.Add(folder_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._subfolders = wx.CheckBox(
            self, label="Include subfolders", name="wizard.watch_subfolders"
        )
        self._subfolders.SetValue(bool(getattr(settings, "watch_folder_include_subfolders", False)))
        sizer.Add(self._subfolders, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._process_existing = wx.CheckBox(
            self,
            label="Process files already in the folder when watching starts",
            name="wizard.watch_process_existing",
        )
        self._process_existing.SetValue(
            bool(getattr(settings, "watch_folder_process_existing", False))
        )
        sizer.Add(self._process_existing, flag=wx.LEFT | wx.BOTTOM, border=8)

        self._auto_start = wx.CheckBox(
            self, label="Start watching automatically on launch", name="wizard.watch_auto_start"
        )
        self._auto_start.SetValue(bool(getattr(settings, "watch_folder_auto_start", False)))
        sizer.Add(self._auto_start, flag=wx.LEFT | wx.BOTTOM, border=12)

        self.SetSizer(sizer)

    def _folder_name(self) -> str:
        return self._folder_path or "(no folder chosen)"

    def _on_choose_folder(self, _event: object) -> None:
        with wx.DirDialog(
            self,
            "Choose a folder to watch",
            defaultPath=self._folder_path or "",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self._folder_path = dlg.GetPath()
        self._folder_display.SetLabel(self._folder_name())
        self.Layout()

    def collect(self, settings: Settings, _overrides: dict) -> None:
        settings.watch_folder_path = self._folder_path
        # Only enable if a folder is actually set, so the feature never turns on
        # pointing at nothing.
        settings.watch_folder_enabled = self._enable.GetValue() and bool(self._folder_path)
        settings.watch_folder_include_subfolders = self._subfolders.GetValue()
        settings.watch_folder_process_existing = self._process_existing.GetValue()
        settings.watch_folder_auto_start = self._auto_start.GetValue()


class _SummaryPage(_WizardPage):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent, "Summary")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(self, label="You are all set!", name="wizard.summary_heading")
        heading.SetFont(heading.GetFont().Bold())
        sizer.Add(heading, flag=wx.ALL, border=12)

        self._summary = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.BORDER_NONE,
            name="wizard.summary_text",
        )
        self._summary.SetMinSize((-1, 160))
        sizer.Add(self._summary, proportion=1, flag=wx.EXPAND | wx.ALL, border=12)

        note = wx.StaticText(
            self,
            label=(
                "Click Finish to apply these settings. You can change "
                "anything later from Help > Personalise QUILL."
            ),
            name="wizard.summary_note",
        )
        note.Wrap(440)
        sizer.Add(note, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self.SetSizer(sizer)

    def update_summary(
        self,
        settings: Settings,
        overrides: dict,
        feature_manager: FeatureManager,
    ) -> None:
        lines: list[str] = []
        profile_id = overrides.get("_profile")
        if profile_id and profile_id in PROFILE_DEFINITIONS:
            lines.append(f"Profile: {PROFILE_DEFINITIONS[profile_id].name}")
        lines.append(f"Keyboard pack: {settings.keyboard_pack}")
        remote_state = overrides.get("core.remote")
        if remote_state is not None:
            lines.append(f"Remote Access: {'on' if remote_state == FEATURE_STATE_ON else 'off'}")
        ai_state = overrides.get("future.ai")
        if ai_state is not None:
            lines.append(f"AI Assistance: {'on' if ai_state == FEATURE_STATE_ON else 'off'}")
        lines.append(f"Verbosity: {settings.announcement_verbosity}")
        self._summary.SetValue("\n".join(lines))

    def collect(self, _settings: Settings, _overrides: dict) -> None:
        pass


# ---------------------------------------------------------------------------
# Host dialog
# ---------------------------------------------------------------------------


class SetupWizardDialog(wx.Dialog):
    """Multi-page wizard dialog that personalises QUILL.

    Accepts user choices on each page and applies them atomically when the
    user clicks Finish.  The caller is responsible for persisting ``Settings``
    and ``FeatureManager`` after the dialog closes with ``wx.ID_OK``.
    """

    def __init__(
        self,
        parent: wx.Window,
        settings: Settings,
        feature_manager: FeatureManager,
    ) -> None:
        super().__init__(
            parent,
            title="Personalise QUILL",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            name="setup_wizard",
        )
        self._settings = settings
        self._feature_manager = feature_manager
        self._pending_overrides: dict[str, str] = {}
        self._current_page = 0

        self._pages = self._build_pages()
        self._build_ui()
        self._show_page(0)
        self.SetMinSize((500, 420))
        self.Fit()
        self.CentreOnParent()
        apply_modal_ids(self, affirmative_id=wx.ID_OK, cancel_id=wx.ID_CANCEL)
        # SetFocus() during __init__ doesn't survive the Windows dialog-show
        # sequence.  EVT_INIT_DIALOG (WM_INITDIALOG) fires just before the
        # window is shown, but Windows runs its own post-INITDIALOG focus reset
        # afterward — overwriting our SetFocus call with the Cancel button.
        # wx.CallAfter defers _focus_nav_button to the next event-loop tick,
        # which runs AFTER Windows finishes its own initialisation, so our
        # choice wins.  The Navigate() binding previously on _WizardPage panels
        # was also removed: Navigate() without a focusable child calls wxBell().
        self.Bind(wx.EVT_INIT_DIALOG, lambda _e: wx.CallAfter(self._focus_nav_button))

    def _build_pages(self) -> list[wx.Panel]:
        return [
            _WelcomePage(self, self._settings),
            _KeyboardSoundPage(self, self._settings),
            _ProfilePage(self, self._feature_manager),
            _RemoteAccessPage(self, self._feature_manager),
            _AIPage(self, self._feature_manager),
            _ReadingAccessibilityPage(self, self._settings),
            _WritingToolsPage(self, self._settings),
            _WatchFolderPage(self, self._settings),
            _StartupBehaviourPage(self, self._settings),
            _SummaryPage(self),
        ]

    def _build_ui(self) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)

        self._page_container = wx.BoxSizer(wx.VERTICAL)
        for page in self._pages:
            self._page_container.Add(page, proportion=1, flag=wx.EXPAND)
            page.Hide()

        outer.Add(self._page_container, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)
        outer.Add(wx.StaticLine(self), flag=wx.EXPAND)

        nav = wx.BoxSizer(wx.HORIZONTAL)
        self._progress = wx.StaticText(self, name="wizard.progress_label")
        nav.Add(self._progress, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
        nav.AddStretchSpacer()

        self._back_btn = wx.Button(self, label="< Back", name="wizard.back")
        self._next_btn = wx.Button(self, label="Next >", name="wizard.next")
        self._finish_btn = wx.Button(self, wx.ID_OK, label="Finish", name="wizard.finish")
        self._cancel_btn = wx.Button(self, wx.ID_CANCEL, label="Cancel", name="wizard.cancel")

        nav.Add(self._back_btn, flag=wx.LEFT, border=4)
        nav.Add(self._next_btn, flag=wx.LEFT, border=4)
        nav.Add(self._finish_btn, flag=wx.LEFT, border=4)
        nav.Add(self._cancel_btn, flag=wx.LEFT | wx.RIGHT, border=8)

        outer.Add(nav, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=8)

        self._back_btn.Bind(wx.EVT_BUTTON, self._on_back)
        self._next_btn.Bind(wx.EVT_BUTTON, self._on_next)
        self._finish_btn.Bind(wx.EVT_BUTTON, self._on_finish)

        self.SetSizer(outer)

    def _show_page(self, index: int) -> None:
        if 0 <= self._current_page < len(self._pages):
            self._pages[self._current_page].Hide()

        self._current_page = index
        page = self._pages[index]
        page.Show()
        self.Layout()

        total = len(self._pages)
        self._progress.SetLabel(f"Step {index + 1} of {total}")
        self._back_btn.Enable(index > 0)
        self._next_btn.Show(index < total - 1)
        self._finish_btn.Show(index == total - 1)

        if index == total - 1:
            summary_page = self._pages[-1]
            if isinstance(summary_page, _SummaryPage):
                summary_page.update_summary(
                    self._settings, self._pending_overrides, self._feature_manager
                )
        self._focus_nav_button()

    def _focus_nav_button(self) -> None:
        # SetDefaultItem makes Enter trigger the active nav button regardless
        # of which page control currently holds focus — without it, Windows
        # picks Cancel as the default (because Next/Finish have no standard ID).
        total = len(self._pages)
        if self._current_page == total - 1:
            self.SetDefaultItem(self._finish_btn)
            self._finish_btn.SetFocus()
        else:
            self.SetDefaultItem(self._next_btn)
            self._next_btn.SetFocus()

    def _collect_current(self) -> None:
        page = self._pages[self._current_page]
        page.collect(self._settings, self._pending_overrides)

    def _on_back(self, _: wx.CommandEvent) -> None:
        self._collect_current()
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    def _on_next(self, _: wx.CommandEvent) -> None:
        self._collect_current()
        if self._current_page < len(self._pages) - 1:
            self._show_page(self._current_page + 1)

    def _on_finish(self, _: wx.CommandEvent) -> None:
        self._collect_current()
        self._apply_pending()
        self.EndModal(wx.ID_OK)

    def _apply_pending(self) -> None:
        profile_id = self._pending_overrides.pop("_profile", None)
        if profile_id and profile_id in PROFILE_DEFINITIONS:
            self._feature_manager.switch_profile(profile_id)

        for feature_id, state in self._pending_overrides.items():
            enabled = state == FEATURE_STATE_ON
            self._feature_manager.set_feature_enabled(feature_id, enabled)
