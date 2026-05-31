# Building Quill for macOS

The macOS build reuses the cross-platform wxPython core plus the
`quill/platform/macos/` adapters. See issue #42 for the full plan.

## Prerequisites
- macOS 12+ (Apple Silicon or Intel), Python 3.11+
- `pip install -e ".[ui,macos]"` (wxPython, pyttsx3, pyobjc, py2app)
- For distribution: an Apple **Developer ID Application** certificate and a
  `notarytool` keychain profile (`xcrun notarytool store-credentials`).

## Build
```bash
python setup_macos.py py2app          # -> dist/Quill.app
```

## Sign, notarize, package
```bash
export IDENTITY="Developer ID Application: Your Name (TEAMID)"
export NOTARY_PROFILE="quill-notary"
./scripts/build_macos.sh              # -> dist/Quill.dmg (signed, notarized, stapled)
```

## Platform adapters (macOS)
- Screen reader detect: `quill/platform/macos/sr_detect.py` (VoiceOver)
- Increase Contrast: `quill/platform/macos/high_contrast.py`
- Secrets: `quill/platform/macos/keychain.py` (Keychain, replaces DPAPI)
- Announcements: `quill/platform/macos/announce.py` (VoiceOver via NSAccessibility; needs pyobjc)
- File types: `quill/platform/macos/shell_integration.py` (CFBundleDocumentTypes)
- OS dispatch: `quill/platform/dispatch.py`

## Remaining integration (tracked in #42)
- Route the app's announce handler to `macos.announce.announce` on macOS (ties to #29).
- Migrate secret/high-contrast/screen-reader call sites to `quill.platform.dispatch`.
- Verify the app launches under VoiceOver; keyboard-only QA.
