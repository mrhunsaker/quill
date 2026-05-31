from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _run_step(title: str, command: list[str], *, cwd: Path) -> None:
    print(f"\n==> {title}")
    print(" ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _build_docs(repo_root: Path) -> None:
    pandoc_path = shutil.which("pandoc")
    if pandoc_path is None:
        raise RuntimeError(
            "Pandoc is required for release readiness. "
            "Install with: winget install --id JohnMacFarlane.Pandoc -e"
        )
    docs_dir = repo_root / "docs"
    for source in sorted(docs_dir.glob("*.md")):
        html_out = source.with_suffix(".html")
        epub_out = source.with_suffix(".epub")
        _run_step(
            f"Building {html_out.name}",
            [pandoc_path, str(source), "-f", "gfm", "-t", "html5", "-s", "-o", str(html_out)],
            cwd=repo_root,
        )
        _run_step(
            f"Building {epub_out.name}",
            [pandoc_path, str(source), "-f", "gfm", "-t", "epub3", "-o", str(epub_out)],
            cwd=repo_root,
        )


def _require_tool(tool_name: str, *, install_hint: str) -> None:
    if shutil.which(tool_name) is None:
        raise RuntimeError(
            f"{tool_name} is required for release readiness. Install with: {install_hint}"
        )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    _require_tool("pip-audit", install_hint="python -m pip install pip-audit")

    _run_step("Running lint", ["ruff", "check", "."], cwd=repo_root)
    _run_step("Running dependency audit", ["pip-audit", "--strict"], cwd=repo_root)
    _run_step("Running tests", ["pytest", "-q"], cwd=repo_root)
    _build_docs(repo_root)
    _run_step(
        "Checking docs artifact parity",
        [sys.executable, "scripts/check_docs_artifacts.py"],
        cwd=repo_root,
    )
    _run_step(
        "Verifying release corpus",
        [sys.executable, "scripts/verify_release_corpus.py"],
        cwd=repo_root,
    )
    print("\nRelease readiness checks completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
