"""Unit tests for scripts/generate_file_manifest.py."""

from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.generate_file_manifest import (
    compare_manifests,
    scan_files,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_quill_tree(base: Path, files: dict[str, bytes]) -> None:
    """Write a synthetic quill/ directory tree under *base*."""
    for rel, content in files.items():
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)


def _make_old_manifest(files: dict[str, str]) -> dict[str, object]:
    """Build a minimal manifest dict from {path: sha256}."""
    return {
        "version": "0.4.0",
        "files": [
            {"path": p, "install_path": f"python/Lib/site-packages/{p}", "sha256": h, "size": 10}
            for p, h in files.items()
        ],
    }


# ---------------------------------------------------------------------------
# scan_files
# ---------------------------------------------------------------------------


def test_manifest_includes_all_quill_files(tmp_path: Path) -> None:
    _write_quill_tree(
        tmp_path,
        {
            "quill/__init__.py": b"",
            "quill/core/settings.py": b"x = 1",
        },
    )
    entries = scan_files(tmp_path, "python/Lib/site-packages")
    paths = {e["path"] for e in entries}
    assert "quill/__init__.py" in paths
    assert "quill/core/settings.py" in paths


def test_manifest_excludes_tools_and_pycache(tmp_path: Path) -> None:
    _write_quill_tree(
        tmp_path,
        {
            "quill/__init__.py": b"",
            "quill/tools/check_banned.py": b"# ci gate",
            "quill/core/__pycache__/settings.cpython-312.pyc": b"\x00",
            "quill/core/settings.pyc": b"\x00",
            "quill/core/settings.pyo": b"\x00",
        },
    )
    entries = scan_files(tmp_path, "python/Lib/site-packages")
    paths = {e["path"] for e in entries}
    assert "quill/__init__.py" in paths
    assert "quill/tools/check_banned.py" not in paths
    assert not any("__pycache__" in p for p in paths)
    assert not any(p.endswith(".pyc") for p in paths)
    assert not any(p.endswith(".pyo") for p in paths)


def test_manifest_sha256_correct(tmp_path: Path) -> None:
    content = b"hello world"
    _write_quill_tree(tmp_path, {"quill/__init__.py": content})
    entries = scan_files(tmp_path, "python/Lib/site-packages")
    entry = next(e for e in entries if e["path"] == "quill/__init__.py")
    expected = hashlib.sha256(content).hexdigest()
    assert entry["sha256"] == expected


def test_manifest_install_path_uses_prefix(tmp_path: Path) -> None:
    _write_quill_tree(tmp_path, {"quill/__init__.py": b""})
    entries = scan_files(tmp_path, "python/Lib/site-packages")
    entry = next(e for e in entries if e["path"] == "quill/__init__.py")
    assert entry["install_path"] == "python/Lib/site-packages/quill/__init__.py"


# ---------------------------------------------------------------------------
# compare_manifests
# ---------------------------------------------------------------------------


def test_compare_detects_changed_files(tmp_path: Path) -> None:
    old = _make_old_manifest({"quill/__init__.py": "aaaa", "quill/core/settings.py": "bbbb"})
    new_entries = [
        {
            "path": "quill/__init__.py",
            "install_path": "python/Lib/site-packages/quill/__init__.py",
            "sha256": "cccc",  # changed
            "size": 10,
        },
        {
            "path": "quill/core/settings.py",
            "install_path": "python/Lib/site-packages/quill/core/settings.py",
            "sha256": "bbbb",  # unchanged
            "size": 10,
        },
    ]
    diff = compare_manifests(old, new_entries)
    assert "quill/__init__.py" in diff["changed"]
    assert "quill/core/settings.py" not in diff["changed"]


def test_compare_detects_added_files(tmp_path: Path) -> None:
    old = _make_old_manifest({"quill/__init__.py": "aaaa"})
    new_entries = [
        {
            "path": "quill/__init__.py",
            "install_path": "python/Lib/site-packages/quill/__init__.py",
            "sha256": "aaaa",
            "size": 10,
        },
        {
            "path": "quill/new_module.py",
            "install_path": "python/Lib/site-packages/quill/new_module.py",
            "sha256": "dddd",
            "size": 20,
        },
    ]
    diff = compare_manifests(old, new_entries)
    assert "quill/new_module.py" in diff["added"]
    assert "quill/__init__.py" not in diff["added"]


def test_compare_detects_deleted_files(tmp_path: Path) -> None:
    old = _make_old_manifest({"quill/__init__.py": "aaaa", "quill/old_module.py": "bbbb"})
    new_entries = [
        {
            "path": "quill/__init__.py",
            "install_path": "python/Lib/site-packages/quill/__init__.py",
            "sha256": "aaaa",
            "size": 10,
        },
    ]
    diff = compare_manifests(old, new_entries)
    assert "quill/old_module.py" in diff["deleted"]
    assert "quill/__init__.py" not in diff["deleted"]
