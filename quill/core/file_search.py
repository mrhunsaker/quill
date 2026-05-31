from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from quill.core.search import SearchOptions, find_matches, replace_all


@dataclass(frozen=True, slots=True)
class FileSearchLineMatch:
    line_number: int
    text: str
    match_count: int


@dataclass(frozen=True, slots=True)
class FileSearchEntry:
    path: Path
    match_count: int
    lines: tuple[FileSearchLineMatch, ...]


@dataclass(frozen=True, slots=True)
class FileSearchReport:
    root: Path
    pattern: str
    query: str
    options: SearchOptions
    entries: tuple[FileSearchEntry, ...]
    scanned_files: int
    total_matches: int


@dataclass(frozen=True, slots=True)
class FileReplaceEntry:
    path: Path
    match_count: int
    replacement_count: int


@dataclass(frozen=True, slots=True)
class FileReplaceReport:
    root: Path
    pattern: str
    query: str
    replacement: str
    options: SearchOptions
    entries: tuple[FileReplaceEntry, ...]
    scanned_files: int
    total_matches: int
    total_replacements: int


def search_files(
    root: Path,
    pattern: str,
    query: str,
    options: SearchOptions | None = None,
    *,
    encoding: str = "utf-8",
    progress: Callable[[str, int, int], None] | None = None,
) -> FileSearchReport:
    options = options or SearchOptions()
    entries: list[FileSearchEntry] = []
    total_matches = 0
    files = _iter_matching_files(root, pattern)
    scanned_files = len(files)
    for index, path in enumerate(files, start=1):
        if progress is not None:
            progress(str(path), index, scanned_files)
        text, _line_ending = _read_text(path, encoding)
        matches = find_matches(text, query, options)
        if not matches:
            continue
        line_matches = _group_matches_by_line(text, matches)
        entries.append(
            FileSearchEntry(
                path=path,
                match_count=len(matches),
                lines=line_matches,
            )
        )
        total_matches += len(matches)
    return FileSearchReport(
        root=root,
        pattern=pattern,
        query=query,
        options=options,
        entries=tuple(entries),
        scanned_files=scanned_files,
        total_matches=total_matches,
    )


def replace_files(
    root: Path,
    pattern: str,
    query: str,
    replacement: str,
    options: SearchOptions | None = None,
    *,
    encoding: str = "utf-8",
    progress: Callable[[str, int, int], None] | None = None,
) -> FileReplaceReport:
    options = options or SearchOptions()
    entries: list[FileReplaceEntry] = []
    total_matches = 0
    total_replacements = 0
    files = _iter_matching_files(root, pattern)
    scanned_files = len(files)
    for index, path in enumerate(files, start=1):
        if progress is not None:
            progress(str(path), index, scanned_files)
        text, line_ending = _read_text(path, encoding)
        matches = find_matches(text, query, options)
        if not matches:
            continue
        updated_text, replacement_count = replace_all(text, query, replacement, options)
        _write_text(path, updated_text, encoding, line_ending)
        entries.append(
            FileReplaceEntry(
                path=path,
                match_count=len(matches),
                replacement_count=replacement_count,
            )
        )
        total_matches += len(matches)
        total_replacements += replacement_count
    return FileReplaceReport(
        root=root,
        pattern=pattern,
        query=query,
        replacement=replacement,
        options=options,
        entries=tuple(entries),
        scanned_files=scanned_files,
        total_matches=total_matches,
        total_replacements=total_replacements,
    )


def render_search_report(report: FileSearchReport, mode: str) -> str:
    header = [
        "Search in Files",
        f"Root: {report.root}",
        f"Pattern: {report.pattern}",
        f"Query: {report.query}",
        f"Scanned files: {report.scanned_files}",
        f"Total matches: {report.total_matches}",
        "",
    ]
    body: list[str] = []
    if not report.entries:
        body.append("No matches found.")
        return "\n".join(header + body)

    for entry in report.entries:
        if mode == "filenames":
            body.append(str(entry.path))
            continue
        if mode == "counts":
            body.append(f"{entry.path}: {entry.match_count}")
            continue
        if mode == "filenames_lines_counts":
            body.append(f"{entry.path}: {entry.match_count}")
            for line in entry.lines:
                body.append(
                    f"  Line {line.line_number} ({line.match_count} match(es)): {line.text}"
                )
            body.append("")
            continue
        body.append(f"{entry.path}: {entry.match_count}")
        for line in entry.lines:
            body.append(f"  Line {line.line_number} ({line.match_count} match(es)): {line.text}")
        body.append("")
    return "\n".join(header + body).rstrip()


def render_replace_preview(report: FileSearchReport, replacement: str) -> str:
    lines = [
        "Replace Across Files Preview",
        f"Root: {report.root}",
        f"Pattern: {report.pattern}",
        f"Query: {report.query}",
        f"Replacement: {replacement}",
        f"Files with matches: {len(report.entries)}",
        f"Total matches: {report.total_matches}",
        "",
    ]
    if not report.entries:
        lines.append("No matches found.")
        return "\n".join(lines)
    for entry in report.entries:
        lines.append(f"{entry.path}: {entry.match_count}")
        for line in entry.lines[:10]:
            lines.append(f"  Line {line.line_number}: {line.text}")
        if len(entry.lines) > 10:
            lines.append(f"  ...and {len(entry.lines) - 10} more line(s)")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_replace_report(report: FileReplaceReport) -> str:
    lines = [
        "Replace Across Files",
        f"Root: {report.root}",
        f"Pattern: {report.pattern}",
        f"Query: {report.query}",
        f"Replacement: {report.replacement}",
        f"Scanned files: {report.scanned_files}",
        f"Files changed: {len(report.entries)}",
        f"Total matches: {report.total_matches}",
        f"Total replacements: {report.total_replacements}",
        "",
    ]
    if not report.entries:
        lines.append("No files were changed.")
        return "\n".join(lines)
    for entry in report.entries:
        lines.append(f"{entry.path}: {entry.replacement_count} replacement(s)")
    return "\n".join(lines).rstrip()


def _iter_matching_files(root: Path, pattern: str) -> list[Path]:
    root = root.expanduser()
    wildcard = pattern.strip() or "*"
    if root.is_file():
        return [root]
    if not root.exists():
        raise FileNotFoundError(f"Starting folder not found: {root}")
    return [path for path in root.rglob(wildcard) if path.is_file()]


def _read_text(path: Path, encoding: str) -> tuple[str, str]:
    with path.open("r", encoding=encoding, newline="") as file_handle:
        text = file_handle.read()
    return text, _detect_line_ending(text)


def _write_text(path: Path, text: str, encoding: str, line_ending: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if line_ending == "\r\n":
        normalized = normalized.replace("\n", "\r\n")
    elif line_ending == "\r":
        normalized = normalized.replace("\n", "\r")
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding=encoding, newline="") as file_handle:
        file_handle.write(normalized)
    temp_path.replace(path)


def _group_matches_by_line(
    text: str, matches: list[tuple[int, int]]
) -> tuple[FileSearchLineMatch, ...]:
    spans = _line_spans(text)
    grouped: dict[int, list[tuple[int, int]]] = {}
    for start, end in matches:
        line_number = _line_number_for_position(spans, start)
        grouped.setdefault(line_number, []).append((start, end))
    line_matches: list[FileSearchLineMatch] = []
    for line_number in sorted(grouped):
        start, end, line_text = spans[line_number - 1]
        line_matches.append(
            FileSearchLineMatch(
                line_number=line_number,
                text=line_text.rstrip("\r\n"),
                match_count=len(grouped[line_number]),
            )
        )
    return tuple(line_matches)


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    start = 0
    for line in text.splitlines(keepends=True):
        end = start + len(line)
        spans.append((start, end, line))
        start = end
    if not spans:
        spans.append((0, 0, ""))
    return spans


def _line_number_for_position(spans: list[tuple[int, int, str]], position: int) -> int:
    for index, (start, end, _line) in enumerate(spans, start=1):
        if start <= position < end:
            return index
    return len(spans)


def _detect_line_ending(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"
