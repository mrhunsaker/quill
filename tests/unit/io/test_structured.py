import sqlite3
import zipfile
from pathlib import Path

from quill.core.document import Document
from quill.io.pdf import PdfExtractionResult
from quill.io.structured import read_structured_document


def test_read_structured_json_formats_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.json"
    target.write_text('{"b":2,"a":1}', encoding="utf-8")
    document = read_structured_document(target)
    assert document.path == target
    assert document.text == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_read_structured_toml_validates_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.toml"
    target.write_text('name = "quill"\n', encoding="utf-8")
    document = read_structured_document(target)
    assert document.text == 'name = "quill"\n'


def test_read_structured_xml_formats_document(tmp_path: Path) -> None:
    target = tmp_path / "sample.xml"
    target.write_text("<root><a>1</a></root>", encoding="utf-8")
    document = read_structured_document(target)
    assert "<root>" in document.text
    assert "  <a>1</a>" in document.text


def test_read_structured_csv_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "sample.csv"
    target.write_text("a,b\n1,2\n", encoding="utf-8")
    document = read_structured_document(target)
    assert document.text == "a,b\n1,2\n"


def test_read_structured_notebook_renders_cells(tmp_path: Path) -> None:
    target = tmp_path / "sample.ipynb"
    notebook = (
        '{"cells":['
        '{"cell_type":"markdown","source":["# Title\\n"]},'
        '{"cell_type":"code","source":"print(1)"}'
        "]} "
    ).strip()
    target.write_text(
        notebook,
        encoding="utf-8",
    )
    document = read_structured_document(target)
    assert "## Cell 1 (markdown)" in document.text
    assert "## Cell 2 (code)" in document.text


def test_read_structured_sqlite_renders_table_summary(tmp_path: Path) -> None:
    target = tmp_path / "sample.sqlite"
    with sqlite3.connect(target) as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
        cursor.execute("INSERT INTO notes (body) VALUES ('hello')")
        connection.commit()
    document = read_structured_document(target)
    assert "# SQLite Database: sample.sqlite" in document.text
    assert "- notes: 1 row(s)" in document.text


def test_read_structured_docx_extracts_text(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.docx"
    target.write_bytes(b"PK\x03\x04")
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: "# DOCX Extract\n\nHello\nWorld\n",
    )
    document = read_structured_document(target)
    assert "# DOCX Extract" in document.text
    assert "Hello" in document.text
    assert "World" in document.text


def test_read_structured_doc_extracts_text(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.doc"
    target.write_bytes(b"\xd0\xcf\x11\xe0")
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: "# Word Extract\n\nLegacy Word text\n",
    )

    document = read_structured_document(target)

    assert document.source_metadata["source_kind"] == "doc"
    assert document.source_metadata["engine"] == "markitdown"
    assert "Legacy Word text" in document.text


def test_read_structured_epub_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.epub"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("OEBPS/chapter1.xhtml", "<html><body><p>Hello EPUB</p></body></html>")
    document = read_structured_document(target)
    assert "# EPUB:" in document.text
    assert "Hello EPUB" in document.text


def test_read_structured_odt_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.odt"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("content.xml", "<office><text:p>Hello ODT</text:p></office>")
    document = read_structured_document(target)
    assert "# ODT Extract" in document.text
    assert "Hello ODT" in document.text


def test_read_structured_rtf_extracts_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.rtf"
    target.write_text(r"{\rtf1\ansi Hello RTF}", encoding="latin-1")
    document = read_structured_document(target)
    assert "# RTF Extract" in document.text
    assert "Hello RTF" in document.text


def test_read_structured_pdf_attaches_metadata(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.pdf"
    target.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(
        "quill.io.structured.extract_pdf_text",
        lambda _path: PdfExtractionResult(
            text="Extracted PDF text\n",
            quality_score=81,
            engine="pdfplumber",
            page_count=2,
            extracted_pages=2,
            page_scores=[81, 79],
        ),
    )
    document = read_structured_document(target)
    assert document.source_metadata["source_kind"] == "pdf"
    assert document.source_metadata["quality_score"] == 81
    assert document.source_metadata["page_count"] == 2


def test_read_structured_xlsx_uses_markitdown_when_available(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.xlsx"
    target.write_bytes(b"PK\x03\x04")
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: "# Sheet: Budget\n\n| Item | Amount |\n| --- | --- |\n| Snacks | 12 |\n",
    )

    document = read_structured_document(target)

    assert document.source_metadata["source_kind"] == "xlsx"
    assert document.source_metadata["engine"] == "markitdown"
    assert "| Item | Amount |" in document.text


def test_read_structured_pdf_prefers_markitdown_when_quality_is_low(
    monkeypatch, tmp_path: Path
) -> None:
    target = tmp_path / "sample.pdf"
    target.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(
        "quill.io.structured.extract_pdf_text",
        lambda _path: PdfExtractionResult(
            text="",
            quality_score=12,
            engine="pdfplumber",
            page_count=2,
            extracted_pages=0,
            page_scores=[12, 8],
        ),
    )
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: "# PDF Extract\n\nReadable PDF text\n",
    )

    document = read_structured_document(target)

    assert document.source_metadata["engine"] == "pdfplumber + markitdown"
    assert document.source_metadata["markitdown_used"] is True
    assert "Readable PDF text" in document.text


def test_read_structured_pptx_extracts_headings_lists_tables_and_notes(
    monkeypatch, tmp_path: Path
) -> None:
    target = tmp_path / "sample.pptx"
    target.write_bytes(b"PK\x03\x04")
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: (
            "# Slide Title\n\n- Top item\n  - Nested item\n\n"
            "| H1 | H2 |\n| --- | --- |\n| A | B |\n\n"
            "## Notes\n\nSpeaker note line\n"
        ),
    )

    document = read_structured_document(target)

    assert "# Slide Title" in document.text
    assert "- Top item" in document.text
    assert "  - Nested item" in document.text
    assert "| H1 | H2 |" in document.text
    assert "## Notes" in document.text
    assert "Speaker note line" in document.text


def test_read_structured_ppt_extracts_text(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "sample.ppt"
    target.write_bytes(b"\xd0\xcf\x11\xe0")
    monkeypatch.setattr(
        "quill.io.structured.convert_with_markitdown",
        lambda _path: "# Slide Title\n\nSpeaker note line\n",
    )

    document = read_structured_document(target)

    assert document.source_metadata["source_kind"] == "ppt"
    assert document.source_metadata["engine"] == "markitdown"
    assert "Speaker note line" in document.text


def test_read_structured_pages_gracefully_handles_missing_deps(tmp_path: Path, monkeypatch) -> None:
    """Test that Pages import shows a helpful message when dependencies are missing."""
    target = tmp_path / "sample.pages"
    # Create a minimal ZIP file (Pages files are ZIPs)
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("Index/Document.iwa", b"fake iwa data")

    # Mock both Pages readers to fail (simulating missing deps)
    from unittest.mock import Mock
    from quill.io import pages

    monkeypatch.setattr(
        pages, "_read_pages_via_iwa", Mock(side_effect=ImportError("keynote-parser not available"))
    )
    monkeypatch.setattr(
        pages,
        "_read_pages_via_libreoffice",
        Mock(side_effect=ImportError("markitdown not available")),
    )

    document = read_structured_document(target)

    assert "Pages import not available" in document.text
    assert "pip install keynote-parser" in document.text
    assert "pip install markitdown" in document.text
    assert document.source_metadata["source_kind"] == "pages"
    assert document.source_metadata["quality_score"] == 0
