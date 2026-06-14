from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from quill.core.document import Document

# Braille text family (#226 / BR-004). Saving any of these must round-trip
# byte-for-byte (#235 / BR-012): no line-ending normalization, no trailing
# space trimming, form feeds and encoding preserved.
BRF_SUFFIXES: frozenset[str] = frozenset({".brf", ".brl", ".pef", ".ueb"})

# Soft save-warning hook (#235 / BR-012). The UI registers a callback so a BRF
# saved with non-NABCC characters surfaces a single, non-blocking announcement;
# tests register a collector. None means warnings are silently dropped.
_save_warning_hook: Callable[[str], None] | None = None


def set_save_warning_hook(hook: Callable[[str], None] | None) -> None:
    """Register (or clear) the soft save-warning sink. Returns nothing."""
    global _save_warning_hook
    _save_warning_hook = hook


def _emit_save_warning(message: str) -> None:
    hook = _save_warning_hook
    if hook is None:
        return
    try:
        hook(message)
    except Exception:  # noqa: BLE001 - a warning sink must never break a save
        pass


def read_text_document(path: Path, encoding: str = "utf-8") -> Document:
    text = path.read_text(encoding=encoding)
    line_ending = "\r\n" if "\r\n" in text else "\n"
    return Document(
        text=text,
        path=path,
        modified=False,
        encoding=encoding,
        line_ending=line_ending,
        source_metadata={"source_kind": "text", "engine": "plain text", "quality_score": 100},
    )


def write_text_document(document: Document, path: Path | None = None) -> Path:
    target_path = path or document.path
    if target_path is None:
        raise ValueError("A path is required to save this document.")

    if target_path.suffix.lower() in BRF_SUFFIXES:
        return _write_brf_document(document, target_path)

    text = _normalize_line_endings(document.text, document.line_ending)
    with target_path.open("w", encoding=document.encoding, newline="") as file_handle:
        file_handle.write(text)
    document.mark_saved(target_path)
    return target_path


def _write_brf_document(document: Document, target_path: Path) -> Path:
    """Save a braille text file byte-for-byte (#235 / BR-012).

    No line-ending normalization, no trailing-space trimming, form feeds and
    the original text preserved exactly. ``newline=""`` stops Python from
    translating ``\\n``. A soft, non-blocking warning is emitted (via the
    save-warning hook) when the text contains non-NABCC characters; those
    characters are still written unchanged, falling back to UTF-8 so the save
    never crashes on a braille-unicode codepoint.
    """
    from quill.core.brf_ascii import find_non_brf_ascii_offsets

    text = document.text
    offsets = find_non_brf_ascii_offsets(text)
    encoding = document.encoding or "utf-8"
    if offsets:
        encoding = "utf-8"
        count = len(offsets)
        plural = "s" if count != 1 else ""
        _emit_save_warning(
            f"{target_path.name} was saved with {count} non-braille-ASCII "
            f"character{plural} preserved as-is."
        )
    with target_path.open("w", encoding=encoding, newline="") as file_handle:
        file_handle.write(text)
    document.mark_saved(target_path)
    return target_path


def _normalize_line_endings(text: str, line_ending: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if line_ending == "\n":
        return normalized
    return normalized.replace("\n", line_ending)
