from __future__ import annotations

from pathlib import Path

from quill.core.file_search import (
    render_replace_preview,
    render_replace_report,
    render_search_report,
    replace_files,
    search_files,
)
from quill.core.search import SearchOptions


def test_search_files_finds_matches_by_pattern(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.txt").write_text("alpha\nbeta alpha\n", encoding="utf-8")
    (root / "b.md").write_text("gamma\n", encoding="utf-8")

    report = search_files(root, "*.txt", "alpha", SearchOptions())

    assert report.scanned_files == 1
    assert report.total_matches == 2
    assert len(report.entries) == 1
    assert report.entries[0].path.name == "a.txt"
    assert "Line 2" in render_search_report(report, "context")


def test_replace_files_updates_content(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    path = root / "a.txt"
    path.write_text("alpha beta alpha\n", encoding="utf-8")

    report = replace_files(root, "*.txt", "alpha", "omega", SearchOptions())

    assert report.total_replacements == 2
    assert path.read_text(encoding="utf-8") == "omega beta omega\n"
    assert "omega" in render_replace_report(report)


def test_replace_preview_includes_changed_files(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.txt").write_text("alpha\n", encoding="utf-8")

    search_report = search_files(root, "*.txt", "alpha", SearchOptions())
    preview = render_replace_preview(search_report, "omega")

    assert "Replace Across Files Preview" in preview
    assert "a.txt" in preview
