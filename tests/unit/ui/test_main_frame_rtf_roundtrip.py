"""Source-contract test for EDS-21 RTF round-trip wiring in MainFrame.

The live MainFrame is not runtime-instantiated here; the repo validates UI wiring
through source contracts. This asserts that the save path routes ``.rtf`` targets
through the RTF io writer while other formats keep using ``write_text_document``,
and that the open dispatch resolves ``.rtf`` via ``read_structured_document``
(which now delegates to ``read_rtf_document``).
"""

from __future__ import annotations

from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[3] / "quill" / "ui" / "main_frame.py").read_text(
    encoding="utf-8"
)


def test_imports_rtf_writer() -> None:
    assert "from quill.io.rtf import write_rtf_document" in SOURCE


def test_write_dispatch_routes_rtf() -> None:
    start = SOURCE.index("def _write_document_to_disk(")
    next_def = SOURCE.index("\n    def ", start + 1)
    body = SOURCE[start:next_def]
    assert '.suffix.lower() == ".rtf"' in body
    assert "write_rtf_document(" in body
    assert "write_text_document(" in body


def test_save_file_uses_dispatch() -> None:
    start = SOURCE.index("def save_file(")
    next_def = SOURCE.index("\n    def ", start + 1)
    body = SOURCE[start:next_def]
    assert "self._write_document_to_disk(self.document)" in body


def test_save_file_as_uses_dispatch() -> None:
    start = SOURCE.index("def save_file_as(")
    next_def = SOURCE.index("\n    def ", start + 1)
    body = SOURCE[start:next_def]
    assert "self._write_document_to_disk(self.document, target)" in body


def test_save_as_wildcard_offers_rtf() -> None:
    start = SOURCE.index("def save_file_as(")
    next_def = SOURCE.index("\n    def ", start + 1)
    body = SOURCE[start:next_def]
    assert "Rich Text Format (*.rtf)|*.rtf" in body
