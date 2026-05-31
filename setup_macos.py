"""py2app build configuration for the macOS Quill app.

Usage:
    pip install -e ".[ui,macos]"
    python setup_macos.py py2app
    ./scripts/build_macos.sh          # sign + notarize + DMG

Produces dist/Quill.app.
"""
from setuptools import setup

from quill.platform.macos.shell_integration import (
    APP_DISPLAY_NAME,
    BUNDLE_IDENTIFIER,
    document_types_plist,
)

APP = ["macos_app.py"]

OPTIONS = {
    "argv_emulation": False,
    "packages": ["quill"],
    "includes": ["wx"],
    "plist": {
        "CFBundleName": APP_DISPLAY_NAME,
        "CFBundleDisplayName": APP_DISPLAY_NAME,
        "CFBundleIdentifier": BUNDLE_IDENTIFIER,
        "CFBundleShortVersionString": "0.1.1",
        "CFBundleVersion": "0.1.1",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "CFBundleDocumentTypes": document_types_plist(),
        "NSMicrophoneUsageDescription": "Quill uses the microphone for dictation.",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
