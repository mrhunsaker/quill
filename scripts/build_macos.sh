#!/usr/bin/env bash
# Build, sign, notarize, and package the macOS Quill app.
# Prereqs: pip install -e ".[ui,macos]"; an Apple "Developer ID Application"
# certificate; a notarytool keychain profile (xcrun notarytool store-credentials).
set -euo pipefail

echo "==> Building .app with py2app"
python setup_macos.py py2app

APP="dist/Quill.app"
DMG="dist/Quill.dmg"

if [[ -n "${IDENTITY:-}" ]]; then
  echo "==> Codesigning (hardened runtime)"
  codesign --deep --force --options runtime --timestamp --sign "$IDENTITY" "$APP"
else
  echo "!! IDENTITY not set — skipping codesign (set IDENTITY='Developer ID Application: ...')"
fi

echo "==> Creating DMG"
hdiutil create -volname Quill -srcfolder "$APP" -ov -format UDZO "$DMG"

if [[ -n "${NOTARY_PROFILE:-}" ]]; then
  echo "==> Notarizing"
  xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
  echo "==> Stapling"
  xcrun stapler staple "$DMG"
else
  echo "!! NOTARY_PROFILE not set — skipping notarization"
fi

echo "==> Done: $DMG"
