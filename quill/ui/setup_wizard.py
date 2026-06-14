"""QUILL first-run setup wizard.

Shown automatically the first time QUILL launches
(``settings.setup_wizard_completed == False``).  Re-runnable from
Help > Personalise QUILL.

The wizard walks the user through ten pages and writes the result into
``Settings`` and ``FeatureManager`` before closing.  No feature is toggled
mid-wizard; all changes are applied atomically when the user clicks Finish.

Usage::

    from quill.ui.setup_wizard import run_setup_wizard
    changed = run_setup_wizard(parent, settings, feature_manager)
    if changed:
        # reload menu, announce profile change, etc.
        ...
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import wx

from quill.core.features import FeatureManager
from quill.core.settings import Settings

_log = logging.getLogger(__name__)

_WIZARD_TITLE = "Personalise QUILL"
_PAGE_COUNT = 9


def run_setup_wizard(
    parent: wx.Window,
    settings: Settings,
    feature_manager: FeatureManager,
    *,
    show_modal_fn: Callable[[Any, str], int] | None = None,
) -> bool:
    """Open the setup wizard as a modal dialog.

    Returns ``True`` if the user completed or skipped to the end (Finish),
    ``False`` if they cancelled.  The caller is responsible for saving
    ``settings`` and ``feature_manager`` after a ``True`` return.

    Pass ``show_modal_fn`` (typically ``MainFrame._show_modal_dialog``) so the
    dialog gets screen-reader enter/exit announcements and region tracking.
    """
    from quill.ui.setup_wizard_pages import SetupWizardDialog

    dlg = SetupWizardDialog(parent, settings, feature_manager)
    try:
        if show_modal_fn is not None:
            result = show_modal_fn(dlg, "Setup Wizard")
        else:
            result = dlg.ShowModal()
        completed = result == wx.ID_OK
        if completed:
            settings.setup_wizard_completed = True
        return completed
    finally:
        dlg.Destroy()
