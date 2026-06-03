from __future__ import annotations


def duplicate_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    lines.insert(index + 1, lines[index])
    updated = "\n".join(lines)
    return updated, _line_start(updated, index + 1)


def delete_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if len(lines) == 1:
        return "", 0
    del lines[index]
    if index >= len(lines):
        index = len(lines) - 1
    updated = "\n".join(lines)
    return updated, _line_start(updated, index)


def move_line_up(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index == 0:
        return text, cursor
    lines[index - 1], lines[index] = lines[index], lines[index - 1]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index - 1)


def move_line_down(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index >= len(lines) - 1:
        return text, cursor
    lines[index], lines[index + 1] = lines[index + 1], lines[index]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index + 1)


def join_with_next_line(text: str, cursor: int) -> tuple[str, int]:
    lines = _lines(text)
    index = _line_index(text, cursor)
    if index >= len(lines) - 1:
        return text, cursor
    lines[index] = f"{lines[index].rstrip()} {lines[index + 1].lstrip()}".rstrip()
    del lines[index + 1]
    updated = "\n".join(lines)
    return updated, _line_start(updated, index)


def number_lines(text: str, start: int = 1, separator: str = ". ") -> str:
    """Prefix each non-blank line with a consecutive number (EDS-4).

    Numbering starts at ``start`` and increments only for non-blank lines; blank
    lines are passed through unchanged.
    """
    number = start
    out: list[str] = []
    for line in text.split("\n"):
        if line.strip() == "":
            out.append(line)
        else:
            out.append(f"{number}{separator}{line}")
            number += 1
    return "\n".join(out)


def delete_to_line_start(text: str, cursor: int) -> tuple[str, int]:
    """Delete from the cursor back to the start of the line (EDS-9)."""
    start = text.rfind("\n", 0, cursor) + 1
    return text[:start] + text[cursor:], start


def delete_to_line_end(text: str, cursor: int) -> tuple[str, int]:
    """Delete from the cursor to the end of the line, keeping the newline (EDS-9)."""
    newline = text.find("\n", cursor)
    end = len(text) if newline == -1 else newline
    return text[:cursor] + text[end:], cursor


def delete_to_document_start(text: str, cursor: int) -> tuple[str, int]:
    """Delete from the cursor to the top of the document (EDS-9)."""
    return text[cursor:], 0


def delete_to_document_end(text: str, cursor: int) -> tuple[str, int]:
    """Delete from the cursor to the bottom of the document (EDS-9)."""
    return text[:cursor], cursor


def delete_paragraph(text: str, cursor: int) -> tuple[str, int]:
    """Delete the current paragraph and any blank lines after it (EDS-10)."""
    lines = _lines(text)
    index = _line_index(text, cursor)
    if lines[index].strip() == "":
        start = end = index
    else:
        start = index
        while start > 0 and lines[start - 1].strip() != "":
            start -= 1
        end = index
        while end < len(lines) - 1 and lines[end + 1].strip() != "":
            end += 1
    while end < len(lines) - 1 and lines[end + 1].strip() == "":
        end += 1
    del lines[start : end + 1]
    if not lines:
        lines = [""]
    new_index = min(start, len(lines) - 1)
    updated = "\n".join(lines)
    return updated, _line_start(updated, new_index)


def first_non_blank_position(text: str, cursor: int) -> int:
    """Return the offset of the first non-whitespace character on the line (EDS-16)."""
    line_start = text.rfind("\n", 0, cursor) + 1
    newline = text.find("\n", cursor)
    line_end = len(text) if newline == -1 else newline
    line = text[line_start:line_end]
    leading = len(line) - len(line.lstrip())
    if leading == len(line):
        return line_end
    return line_start + leading


def last_non_blank_position(text: str, cursor: int) -> int:
    """Return the offset just past the last non-whitespace character (EDS-16)."""
    line_start = text.rfind("\n", 0, cursor) + 1
    newline = text.find("\n", cursor)
    line_end = len(text) if newline == -1 else newline
    line = text[line_start:line_end]
    return line_start + len(line.rstrip())


def _lines(text: str) -> list[str]:
    if text == "":
        return [""]
    return text.split("\n")


def _line_index(text: str, cursor: int) -> int:
    if cursor <= 0:
        return 0
    return text[:cursor].count("\n")


def _line_start(text: str, index: int) -> int:
    if index <= 0:
        return 0
    position = 0
    current = 0
    while current < index and position < len(text):
        if text[position] == "\n":
            current += 1
        position += 1
    return position
