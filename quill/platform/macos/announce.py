"""Post spoken announcements to VoiceOver on macOS.

Uses NSAccessibility's announcement notification via pyobjc when available.
If pyobjc isn't installed, falls back to a no-op so imports never fail. Intended
to back the app's announce handler on macOS (see issue #29 / #42).
"""
from __future__ import annotations


def announce(message: str) -> bool:
    """Speak ``message`` through VoiceOver. Returns True if dispatched."""
    if not message:
        return False
    try:
        import AppKit  # type: ignore[import-not-found]
        import Foundation  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        app = AppKit.NSApplication.sharedApplication()
        window = app.keyWindow() or app.mainWindow()
        element = window if window is not None else app
        user_info = {
            AppKit.NSAccessibilityAnnouncementKey: Foundation.NSString.stringWithString_(message),
            AppKit.NSAccessibilityPriorityKey: AppKit.NSAccessibilityPriorityHigh,
        }
        AppKit.NSAccessibilityPostNotificationWithUserInfo(
            element,
            AppKit.NSAccessibilityAnnouncementRequestedNotification,
            user_info,
        )
        return True
    except Exception:
        return False
