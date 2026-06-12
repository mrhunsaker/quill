"""Download bootstrapper binaries for the autoupdate vendor package.

Fetches ``bootstrap.exe``, ``bootstrap-lin.sh``, and ``bootstrap-mac.sh``
from the AccessibleApps/app_updater repository on GitHub and writes SHA-256
checksums to ``checksums.sha256``.

Usage::

    python scripts/fetch_bootstrappers.py
    python scripts/fetch_bootstrappers.py --force
    python scripts/fetch_bootstrappers.py --verify-only
"""

from __future__ import annotations

import argparse
import hashlib
import urllib.request  # noqa: S310
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/accessibleapps/app_updater/HEAD/autoupdate/bootstrappers/"
)

BOOTSTRAPPERS = [
    "bootstrap.exe",
    "bootstrap-lin.sh",
    "bootstrap-mac.sh",
]

_DEFAULT_DIR = Path("quill/_vendor/autoupdate/bootstrappers")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_checksums(checksum_path: Path) -> dict[str, str]:
    """Return {filename: hex_digest} from the recorded checksum file."""
    if not checksum_path.exists():
        return {}
    result: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            digest, filename = parts
            result[filename.lstrip("*")] = digest
    return result


def _save_checksums(checksum_path: Path, checksums: dict[str, str]) -> None:
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{digest}  {name}\n" for name, digest in sorted(checksums.items())]
    checksum_path.write_text("".join(lines), encoding="utf-8")


def _download(filename: str, dest: Path) -> str:
    url = BASE_URL + filename
    print(f"  Downloading {filename} from {url} ...")
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        data = resp.read()
    dest.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch bootstrapper binaries for the autoupdate vendor package."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download all files even if the recorded checksum matches.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Check hashes without downloading; exit non-zero if any file is missing or changed.",
    )
    parser.add_argument(
        "--bootstrapper-dir",
        type=Path,
        default=_DEFAULT_DIR,
        help="Directory that holds the bootstrapper binaries.",
    )
    args = parser.parse_args()

    bootstrapper_dir: Path = args.bootstrapper_dir
    checksum_path = bootstrapper_dir / "checksums.sha256"

    recorded = _load_checksums(checksum_path)
    failures: list[str] = []
    updated: dict[str, str] = dict(recorded)

    for filename in BOOTSTRAPPERS:
        dest = bootstrapper_dir / filename
        recorded_digest = recorded.get(filename, "")

        actual_digest = _sha256(dest) if dest.exists() else ""

        if args.verify_only:
            if not dest.exists():
                print(f"  MISSING  {filename}")
                failures.append(filename)
            elif actual_digest != recorded_digest:
                print(
                    f"  MISMATCH {filename}"
                    f"  (expected {recorded_digest[:12]}, got {actual_digest[:12]})"
                )
                failures.append(filename)
            else:
                print(f"  OK       {filename}  {actual_digest[:12]}...")
            continue

        if (
            dest.exists()
            and not args.force
            and actual_digest == recorded_digest
            and recorded_digest
        ):
            print(f"  SKIP     {filename}  (hash matches, use --force to re-download)")
            continue

        bootstrapper_dir.mkdir(parents=True, exist_ok=True)
        digest = _download(filename, dest)
        updated[filename] = digest
        print(f"  OK       {filename}  {digest[:12]}...")

    if not args.verify_only:
        _save_checksums(checksum_path, updated)
        print(f"Checksums written to {checksum_path}")

    if failures:
        print(f"FAILED: {len(failures)} file(s) failed verification: {', '.join(failures)}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
