"""macOS platform adapters.

Counterparts to ``quill.platform.windows.*`` for running Quill natively on
macOS. Modules here intentionally avoid hard third-party dependencies and use
stable system tools (``security``, ``defaults``, ``ps``) so they import safely
even when those tools are absent (each function degrades gracefully).
"""
