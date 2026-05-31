from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

_ZERO_SHA = "0000000000000000000000000000000000000000"


def _normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def _git_changed_paths(*, base_ref: str | None, head_ref: str | None) -> set[str]:
    if base_ref and head_ref:
        if base_ref == _ZERO_SHA:
            return set()
        command = ["git", "diff", "--name-only", base_ref, head_ref, "--"]
    else:
        command = ["git", "diff", "--name-only", "HEAD", "--"]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = {_normalize_path(line) for line in result.stdout.splitlines() if line.strip()}
    return paths


def _validate_docs_artifacts(changed_paths: set[str]) -> list[str]:
    errors: list[str] = []
    for source in sorted(changed_paths):
        source_path = Path(source)
        if source_path.parent.as_posix() != "docs" or source_path.suffix.lower() != ".md":
            continue
        if not source_path.exists():
            # Source markdown was removed or moved; matching artifact files are
            # expected to be removed as well, not regenerated.
            continue
        expected = {
            source_path.with_suffix(".html").as_posix(),
            source_path.with_suffix(".epub").as_posix(),
        }
        missing = sorted(path for path in expected if path not in changed_paths)
        if missing:
            missing_text = ", ".join(missing)
            errors.append(f"{source} changed without regenerated artifacts: {missing_text}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail if docs/*.md changed without matching HTML/EPUB updates."
    )
    parser.add_argument("--base-ref", help="Base git ref for diff comparison.")
    parser.add_argument("--head-ref", help="Head git ref for diff comparison.")
    args = parser.parse_args()

    if bool(args.base_ref) != bool(args.head_ref):
        parser.error("--base-ref and --head-ref must be provided together")

    changed_paths = _git_changed_paths(base_ref=args.base_ref, head_ref=args.head_ref)
    if not changed_paths:
        print("Docs artifact check skipped: no changed files detected.")
        return 0

    errors = _validate_docs_artifacts(changed_paths)
    if errors:
        print("Docs artifact check failed:")
        for line in errors:
            print(f"- {line}")
        return 1

    print("Docs artifact check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
