from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quill.io.markitdown_bridge import convert_with_markitdown


@dataclass(slots=True)
class PdfExtractionResult:
    text: str
    quality_score: int
    engine: str
    page_count: int
    extracted_pages: int
    page_scores: list[int]


def extract_pdf_text(path: Path) -> PdfExtractionResult:
    for extractor in (_extract_with_pdfplumber, _extract_with_pypdf):
        try:
            result = extractor(path)
        except ModuleNotFoundError:
            continue
        if result.text.strip():
            return result
    return PdfExtractionResult(
        text=f"(No PDF text extractor was available for {path.name}.)\n",
        quality_score=0,
        engine="unavailable",
        page_count=0,
        extracted_pages=0,
        page_scores=[],
    )


def format_pdf_document(path: Path | PdfExtractionResult) -> str:
    result = path if isinstance(path, PdfExtractionResult) else extract_pdf_text(path)
    header = [
        "# PDF Extract",
        "",
        f"Engine: {result.engine}",
        f"Quality score: {result.quality_score}/100",
    ]
    if result.quality_score < 50:
        header.append("Low-confidence extraction. MarkItDown or OCR may improve the result.")
    header.append("")
    body = result.text.rstrip() + "\n"
    if isinstance(path, Path) and result.quality_score < 50:
        try:
            markitdown_text = convert_with_markitdown(path)
        except (ImportError, ValueError, RuntimeError):
            return "\n".join(header) + body
        if len(markitdown_text.strip()) > len(result.text.strip()):
            return (
                "\n".join(
                    [
                        "# PDF Extract",
                        "",
                        "Engine: markitdown",
                        "Quality score: 85/100",
                        "",
                    ]
                )
                + markitdown_text.rstrip()
                + "\n"
            )
    return "\n".join(header) + body


def _extract_with_pdfplumber(path: Path) -> PdfExtractionResult:
    import pdfplumber

    page_texts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        pages = list(pdf.pages)
        for page in pages:
            text = page.extract_text() or ""
            page_texts.append(text.strip())
    text = "\n\n".join(page_texts).strip()
    score = _score_pdf_text(text, len(pages), sum(1 for page_text in page_texts if page_text))
    return PdfExtractionResult(
        text=text + "\n" if text else "",
        quality_score=score,
        engine="pdfplumber",
        page_count=len(pages),
        extracted_pages=sum(1 for page_text in page_texts if page_text),
        page_scores=[_score_pdf_text(page_text, 1, 1) for page_text in page_texts],
    )


def _extract_with_pypdf(path: Path) -> PdfExtractionResult:
    from pypdf import PdfReader  # type: ignore[import-not-found]

    reader = PdfReader(str(path))
    page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(page_texts).strip()
    score = _score_pdf_text(
        text, len(reader.pages), sum(1 for page_text in page_texts if page_text)
    )
    return PdfExtractionResult(
        text=text + "\n" if text else "",
        quality_score=score,
        engine="pypdf",
        page_count=len(reader.pages),
        extracted_pages=sum(1 for page_text in page_texts if page_text),
        page_scores=[_score_pdf_text(page_text, 1, 1) for page_text in page_texts],
    )


def _score_pdf_text(text: str, page_count: int, extracted_pages: int) -> int:
    normalized = " ".join(text.split())
    if not normalized:
        return 0
    words = len(normalized.split())
    char_score = min(40, len(normalized) // 80)
    word_score = min(30, words // 4)
    page_score = min(30, extracted_pages * 10 if page_count else 0)
    return min(100, char_score + word_score + page_score)
