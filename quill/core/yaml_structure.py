from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Literal

from quill.core.outline import OutlineEntry

YamlNodeKind = Literal["mapping", "sequence"]


@dataclass(slots=True)
class YamlNode:
    kind: YamlNodeKind
    label: str
    value: str
    line_no: int
    indent: int
    start_offset: int
    end_line: int
    children: list[YamlNode] = field(default_factory=list)


def extract_yaml_nodes(text: str) -> list[YamlNode]:
    roots: list[YamlNode] = []
    stack: list[YamlNode] = []
    offset = 0
    for line_no, raw_line in enumerate(text.splitlines(keepends=True)):
        line = raw_line.rstrip("\r\n")
        stripped = line.lstrip(" \t")
        if not stripped or stripped.startswith("#") or stripped in {"---", "..."}:
            offset += len(raw_line)
            continue
        content = _strip_yaml_comment(stripped).rstrip()
        if not content:
            offset += len(raw_line)
            continue
        indent = len(line) - len(stripped)
        parsed = _parse_yaml_node(content, line_no=line_no, indent=indent, start_offset=offset)
        offset += len(raw_line)
        if parsed is None:
            continue
        while stack and stack[-1].indent >= parsed.indent:
            stack.pop()
        if stack:
            stack[-1].children.append(parsed)
        else:
            roots.append(parsed)
        stack.append(parsed)
    _finalize_end_lines(roots)
    return roots


def extract_yaml_outline_entries(text: str) -> list[OutlineEntry]:
    entries: list[OutlineEntry] = []
    for node in extract_yaml_nodes(text):
        _collect_outline_entries(node, entries)
    return entries


def rename_yaml_node(text: str, line_no: int, new_label: str) -> str:
    node = _find_node(extract_yaml_nodes(text), line_no)
    if node is None:
        raise ValueError("YAML node was not found")
    label = _format_yaml_label(new_label)
    lines = text.splitlines(keepends=True)
    line, ending = _split_line_ending(lines[line_no])
    prefix = line[: node.indent]
    stripped = line[node.indent :]
    if node.kind == "mapping":
        key, value = _split_yaml_mapping(stripped)
        if key is None:
            raise ValueError("Selected YAML line is not a mapping")
        replacement = f"{label}:"
        if value:
            replacement = f"{replacement} {value}"
        lines[line_no] = f"{prefix}{replacement}{ending}"
        return "".join(lines)
    body = stripped[1:].lstrip()
    if not body:
        lines[line_no] = f"{prefix}- {label}{ending}" if label else f"{prefix}-{ending}"
        return "".join(lines)
    key, value = _split_yaml_mapping(body)
    if key is None:
        replacement = label
    else:
        replacement = f"{label}:"
        if value:
            replacement = f"{replacement} {value}"
    lines[line_no] = f"{prefix}- {replacement}{ending}" if replacement else f"{prefix}-{ending}"
    return "".join(lines)


def add_yaml_child(text: str, line_no: int, kind: YamlNodeKind, label: str) -> str:
    node = _find_node(extract_yaml_nodes(text), line_no)
    if node is None:
        raise ValueError("YAML node was not found")
    if not _node_accepts_children(node):
        raise ValueError("Selected YAML node does not accept children")
    return _insert_yaml_entry(text, node.end_line + 1, node.indent + 2, kind, label)


def add_yaml_sibling(text: str, line_no: int, kind: YamlNodeKind, label: str) -> str:
    node = _find_node(extract_yaml_nodes(text), line_no)
    if node is None:
        raise ValueError("YAML node was not found")
    return _insert_yaml_entry(text, node.end_line + 1, node.indent, kind, label)


def delete_yaml_node(text: str, line_no: int) -> str:
    node = _find_node(extract_yaml_nodes(text), line_no)
    if node is None:
        raise ValueError("YAML node was not found")
    lines = text.splitlines(keepends=True)
    del lines[node.line_no : node.end_line + 1]
    return "".join(lines)


def _collect_outline_entries(node: YamlNode, entries: list[OutlineEntry]) -> None:
    entries.append(
        OutlineEntry(
            level=node.indent,
            title=node.label or "(item)",
            position=node.start_offset,
        )
    )
    for child in node.children:
        _collect_outline_entries(child, entries)


def _parse_yaml_node(
    content: str,
    *,
    line_no: int,
    indent: int,
    start_offset: int,
) -> YamlNode | None:
    if content.startswith("-"):
        body = content[1:]
        if body and not body[0].isspace():
            return None
        item = body.lstrip()
        label, value = _parse_yaml_label_and_value(item)
        return YamlNode(
            kind="sequence",
            label=label,
            value=value,
            line_no=line_no,
            indent=indent,
            start_offset=start_offset,
            end_line=line_no,
        )
    key, value = _split_yaml_mapping(content)
    if key is None:
        return None
    return YamlNode(
        kind="mapping",
        label=_unquote_yaml_text(key),
        value=value,
        line_no=line_no,
        indent=indent,
        start_offset=start_offset,
        end_line=line_no,
    )


def _strip_yaml_comment(text: str) -> str:
    result: list[str] = []
    quote: str | None = None
    escaped = False
    for char in text:
        if quote == '"':
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = None
            continue
        if quote == "'":
            result.append(char)
            if char == "'":
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
            result.append(char)
            continue
        if char == "#":
            break
        result.append(char)
    return "".join(result)


def _parse_yaml_label_and_value(text: str) -> tuple[str, str]:
    key, value = _split_yaml_mapping(text)
    if key is None:
        return _unquote_yaml_text(text), ""
    return _unquote_yaml_text(key), value


def _split_yaml_mapping(text: str) -> tuple[str | None, str]:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = None
            continue
        if quote == "'":
            if char == "'":
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
            continue
        if char != ":":
            continue
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if next_char and next_char not in " \t#":
            continue
        key = text[:index].strip()
        if not key:
            return None, ""
        value = text[index + 1 :].lstrip()
        return key, value
    if text.strip():
        return None, ""
    return None, ""


def _format_yaml_label(text: str) -> str:
    value = " ".join(text.strip().split())
    if not value:
        return ""
    if re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        return value
    return json.dumps(value)


def _unquote_yaml_text(text: str) -> str:
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _node_accepts_children(node: YamlNode) -> bool:
    return not node.value.strip()


def _insert_yaml_entry(
    text: str,
    insert_line_no: int,
    indent: int,
    kind: YamlNodeKind,
    label: str,
) -> str:
    lines = text.splitlines(keepends=True)
    ending = _preferred_line_ending(lines)
    formatted = _render_yaml_entry(indent, kind, label)
    if insert_line_no >= len(lines):
        if lines and lines[-1].endswith(("\n", "\r")):
            lines.append(formatted + ending)
        elif lines:
            lines[-1] = lines[-1] + ending + formatted + ending
        else:
            lines.append(formatted + ending)
        return "".join(lines)
    lines.insert(insert_line_no, formatted + ending)
    return "".join(lines)


def _render_yaml_entry(indent: int, kind: YamlNodeKind, label: str) -> str:
    text = _format_yaml_label(label)
    prefix = " " * indent
    if kind == "mapping":
        return f"{prefix}{text}:" if text else f"{prefix}:"
    return f"{prefix}- {text}" if text else f"{prefix}-"


def _preferred_line_ending(lines: list[str]) -> str:
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
    return "\n"


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


def _finalize_end_lines(nodes: list[YamlNode]) -> None:
    for node in nodes:
        _finalize_node(node)


def _finalize_node(node: YamlNode) -> int:
    end_line = node.line_no
    for child in node.children:
        end_line = max(end_line, _finalize_node(child))
    node.end_line = end_line
    return end_line


def _find_node(nodes: list[YamlNode], line_no: int) -> YamlNode | None:
    for node in nodes:
        if node.line_no == line_no:
            return node
        child = _find_node(node.children, line_no)
        if child is not None:
            return child
    return None
