from __future__ import annotations

from pathlib import Path


def convert_with_markitdown(path: Path) -> str:
    try:
        from markitdown import MarkItDown  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("markitdown not available") from exc

    converter = MarkItDown(enable_plugins=False)
    result = converter.convert(str(path))
    text = result.text_content or ""
    if not text.strip():
        raise ValueError(f"MarkItDown produced empty output for {path.name}")
    return text.rstrip() + "\n"
