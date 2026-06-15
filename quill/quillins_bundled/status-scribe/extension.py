"""Status Scribe — live document statistics in the status bar.

Pushes a word/character/sentence count into a status bar cell after every save
and on tab activation.  Demonstrates:
- ``status_bar`` contribution (get_count_cell handler)
- ``api.log()`` developer logging routed to the Developer Console
- ``quillin.enabled`` / ``quillin.disabled`` lifecycle events
- ``settings.changed`` event for live preference hot-reload
"""

from __future__ import annotations

_api = None
_last_count: int = 0


def setup(api) -> None:
    global _api
    _api = api
    api.log("Status Scribe: setup() called")


# ---------------------------------------------------------------------------
# Status bar cell handler
# ---------------------------------------------------------------------------


def get_count_cell() -> str:
    """Return the current cell text.  Called by the host to refresh the cell."""
    assert _api is not None
    mode = _api.get_setting("count_mode", "words")
    show_label = _api.get_setting("show_label", True)
    prefix = {"words": "Words", "chars": "Chars", "sentences": "Sents"}.get(mode, "Words")
    if show_label:
        return f"{prefix}: {_last_count}"
    return str(_last_count)


# ---------------------------------------------------------------------------
# Document event handlers
# ---------------------------------------------------------------------------


def on_after_save(api, event: dict) -> None:
    global _last_count
    _refresh_count(api)
    if api.get_setting("announce_on_save", False):
        priority = api.get_setting("announce_priority", "quiet")
        api.announce(get_count_cell(), priority=priority)


def on_activated(api, event: dict) -> None:
    _refresh_count(api)


def on_enabled(api, event: dict) -> None:
    api.log("Status Scribe enabled — status bar cell is live.")


def on_disabled(api, event: dict) -> None:
    global _last_count
    _last_count = 0
    api.log("Status Scribe disabled — cell cleared.")


def on_settings_changed(api, event: dict) -> None:
    key: str = event.get("key", "")
    value = event.get("value")
    api.log(f"Status Scribe setting changed: {key} = {value!r}")
    _refresh_count(api)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _refresh_count(api) -> None:
    global _last_count
    try:
        text: str = api.get_text()
    except Exception:
        return
    mode = api.get_setting("count_mode", "words")
    if mode == "chars":
        _last_count = len(text)
    elif mode == "sentences":
        import re

        _last_count = len(re.split(r"[.!?]+", text.strip())) if text.strip() else 0
    else:
        _last_count = len(text.split())
    api.log(f"Status Scribe: count refreshed to {_last_count} ({mode})")
