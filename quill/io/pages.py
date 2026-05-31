from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from quill.core.document import Document
from quill.io.markitdown_bridge import convert_with_markitdown


def read_pages_document(path: Path) -> Document:
    """Import an Apple Pages document and extract text with heading structure.

    Uses Route A (pure Python IWA parsing) when available, falls back to Route B
    (LibreOffice + MarkItDown) for higher fidelity. If neither is available,
    returns a graceful error message.
    """
    try:
        # Try Route A: Pure Python IWA parsing (requires keynote-parser)
        return _read_pages_via_iwa(path)
    except (ImportError, Exception):
        pass  # Fall through to Route B

    try:
        # Route B: LibreOffice headless + MarkItDown
        return _read_pages_via_libreoffice(path)
    except (ImportError, subprocess.CalledProcessError, Exception):
        pass  # Fall through to error message

    # No engines available
    return Document(
        text=(
            f"(Pages import not available for {path.name}.)\n\n"
            "To import Pages documents, either:\n"
            "1. Install keynote-parser: pip install keynote-parser\n"
            "2. Or install LibreOffice and MarkItDown: pip install markitdown[all]\n"
        ),
        path=path,
        modified=False,
        encoding="utf-8",
        line_ending="\n",
        source_metadata={
            "source_kind": "pages",
            "engine": "unavailable",
            "quality_score": 0,
        },
    )


def _read_pages_via_iwa(path: Path) -> Document:
    """Route A: Parse .pages as IWA (requires keynote-parser + pyiwa)."""
    try:
        from keynote_parser.parser import load_presentation  # type: ignore[import-untyped]
    except ImportError as e:
        raise ImportError("keynote-parser not available") from e

    # Load via keynote-parser (also handles Pages via IWA)
    doc_obj: Any = load_presentation(str(path))

    # Extract text and structure from IWA
    text_parts: list[str] = []

    # keynote-parser returns slides/pages; iterate and extract text with heading levels
    if hasattr(doc_obj, "pages") or hasattr(doc_obj, "slides"):
        pages_or_slides: list[Any] = getattr(doc_obj, "pages", None) or getattr(
            doc_obj, "slides", []
        )
        for page_or_slide in pages_or_slides:
            # Extract title (usually h1 equivalent)
            if hasattr(page_or_slide, "title") and page_or_slide.title:
                text_parts.append(f"# {page_or_slide.title}\n")

            # Extract body/notes (h2+)
            if hasattr(page_or_slide, "notes") and page_or_slide.notes:
                text_parts.append(page_or_slide.notes)
            elif hasattr(page_or_slide, "text") and page_or_slide.text:
                text_parts.append(page_or_slide.text)

            text_parts.append("\n")
    else:
        # Fallback: try direct text extraction
        text_content = str(doc_obj)
        text_parts.append(text_content)

    text = "".join(text_parts).strip()
    if not text:
        raise ValueError("No text extracted from Pages via IWA")

    return Document(
        text=text + "\n",
        path=path,
        modified=False,
        encoding="utf-8",
        line_ending="\n",
        source_metadata={
            "source_kind": "pages",
            "engine": "keynote-parser (IWA)",
            "quality_score": 75,
        },
    )


def _read_pages_via_libreoffice(path: Path) -> Document:
    """Route B: Convert .pages to DOCX/HTML via LibreOffice, then MarkItDown.

    Requires LibreOffice (soffice) and markitdown Python package.
    """
    # Use a temp directory for the converted file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Try DOCX first (MarkItDown handles it well)
        docx_path = tmpdir_path / "converted.docx"

        try:
            # Call LibreOffice headless to convert .pages to DOCX
            subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    str(tmpdir_path),
                    str(path),
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except FileNotFoundError as e:
            raise ImportError("LibreOffice (soffice) not found in PATH") from e
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"LibreOffice conversion failed: {stderr}") from e

        # Check if conversion succeeded
        if not docx_path.exists():
            raise RuntimeError("LibreOffice did not produce a DOCX file")
        # Convert DOCX to Markdown via MarkItDown
        text = convert_with_markitdown(docx_path)

        return Document(
            text=text.strip() + "\n",
            path=path,
            modified=False,
            encoding="utf-8",
            line_ending="\n",
            source_metadata={
                "source_kind": "pages",
                "engine": "libreoffice + markitdown",
                "quality_score": 85,
            },
        )


def outline_pages_document(document: Document) -> list[tuple[int, str]]:
    """Extract heading outline from a Pages-imported document.

    Returns list of (level, heading_text) tuples.
    Expects document to be Markdown with # headings.
    """
    import re

    headings: list[tuple[int, str]] = []
    for line in document.text.split("\n"):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((level, heading_text))

    return headings
