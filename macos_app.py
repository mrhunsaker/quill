"""Entry point for the macOS .app bundle (used by setup_macos.py / py2app)."""
from quill.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
