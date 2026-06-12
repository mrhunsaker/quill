"""Structural guards for the repository tree (ORG-1).

These tests encode the "best-in-class repository tree" invariant: a new
contributor should be able to navigate the layout at a glance. Source lives
under ``quill/``, build tooling under ``scripts/``, internal helpers under
``tools/``, and tests under ``tests/`` — never as loose modules in the
repository root. The guards fail loudly if a stray module reappears at the root
so the cleanup cannot silently regress.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

# The only Markdown files sanctioned to live at the repository root: conventional
# community/governance/legal files plus the two master regression/usability plans
# that copilot-instructions pins to the root — dialogs.md (the manual
# dialog-regression checklist) and menus.md (the definitive menu-reorganization
# plan). Every other Markdown document — design notes, research, planning
# (including ROADMAP.md), and engineering — lives under docs/ so the root stays
# scannable at a glance.
_SANCTIONED_ROOT_MARKDOWN = frozenset({
    "CHANGELOG.md",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "PRIVACY.md",
    "README.md",
    "RELEASE.md",
    "RESPONSIBLE_AI_USE.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
    "dialogs.md",
    "issues.md",
    "menus.md",
    "x2.md",
})


def test_repository_root_has_no_loose_python_modules() -> None:
    stray = sorted(path.name for path in _REPO_ROOT.glob("*.py"))
    assert stray == [], (
        "The repository root must stay free of loose Python modules: importable "
        "source belongs under quill/, build tooling under scripts/, and tests "
        f"under tests/. Found stray root modules: {stray}"
    )


def test_repository_root_markdown_is_limited_to_sanctioned_files() -> None:
    present = {path.name for path in _REPO_ROOT.glob("*.md")}
    stray = sorted(present - _SANCTIONED_ROOT_MARKDOWN)
    assert stray == [], (
        "Only conventional root Markdown files are allowed at the repository "
        "root; design, research, and planning notes belong under docs/ (for "
        f"example docs/planning/). Found unsanctioned root Markdown: {stray}"
    )


def test_relocated_planning_docs_live_under_docs() -> None:
    planning = _REPO_ROOT / "docs" / "planning"
    for stem in ("aa", "glow", "pi", "ROADMAP"):
        assert (planning / f"{stem}.md").is_file(), f"missing docs/planning/{stem}.md"
        # Each planning doc keeps the docs/ HTML + EPUB artifact triple in step.
        assert (planning / f"{stem}.html").is_file(), f"missing docs/planning/{stem}.html"
        assert (planning / f"{stem}.epub").is_file(), f"missing docs/planning/{stem}.epub"


def test_macos_build_files_live_in_sanctioned_homes() -> None:
    # The py2app entry point is genuine platform source and lives in the macOS
    # platform package; the py2app build configuration is build tooling and
    # lives in scripts/ alongside build_macos.sh (deliberately outside the
    # bundled `quill` package so it is never packed into the .app).
    assert (_REPO_ROOT / "quill" / "platform" / "macos" / "macos_app.py").is_file()
    assert (_REPO_ROOT / "scripts" / "setup_macos.py").is_file()
