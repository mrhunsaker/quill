from __future__ import annotations

import hashlib
import hmac
import json
import ssl
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

DEFAULT_UPDATE_MANIFEST_URL = (
    "https://community-access.github.io/quill/updates/.quill-update-feed-v1.json"
)
# GitHub Releases: stable releases reach everyone; anything marked "prerelease"
# reaches beta users only (see fetch_latest_release / the Get beta updates setting).
GITHUB_RELEASES_API = "https://api.github.com/repos/Community-Access/quill/releases"
_SIGNATURE_SALT = "quill-manifest-signature-v1"


def _ssl_context() -> ssl.SSLContext:
    """An SSL context with a real CA bundle.

    Python on macOS ships without trusted roots wired into urllib, which causes
    'CERTIFICATE_VERIFY_FAILED'. Prefer certifi's bundle; fall back to the
    system default so this never hard-fails at import.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        return ssl.create_default_context()


@dataclass(frozen=True, slots=True)
class UpdateManifest:
    version: str
    download_url: str
    published_at: str
    notes: str
    signature: str


def fetch_update_manifest(
    url: str = DEFAULT_UPDATE_MANIFEST_URL,
    timeout: int = 10,
) -> UpdateManifest:
    with urlopen(url, timeout=timeout, context=_ssl_context()) as response:
        payload = response.read().decode("utf-8", errors="strict")
    return parse_update_manifest(payload)


@dataclass(frozen=True, slots=True)
class GitHubRelease:
    version: str
    download_url: str
    published_at: str
    notes: str
    prerelease: bool


def fetch_latest_release(
    include_prereleases: bool = False,
    api_url: str = GITHUB_RELEASES_API,
    timeout: int = 10,
) -> GitHubRelease | None:
    """Return the newest GitHub release the user is eligible for.

    Stable channel (default): newest non-prerelease, non-draft release.
    Beta channel (include_prereleases=True): newest release including prereleases.
    Returns None when no eligible release exists.
    """
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Quill-Updater",
        },
    )
    with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        payload = response.read().decode("utf-8", errors="strict")
    releases = json.loads(payload)
    if not isinstance(releases, list):
        raise ValueError("GitHub releases payload must be a JSON array")

    candidates = [r for r in releases if isinstance(r, dict) and not r.get("draft")]
    if not include_prereleases:
        candidates = [r for r in candidates if not r.get("prerelease")]
    if not candidates:
        return None
    # The API returns releases newest-first; pick the newest by version to be safe.
    best = max(candidates, key=lambda r: _version_tuple(str(r.get("tag_name") or "")))
    return _release_from_json(best)


def _release_from_json(data: dict) -> GitHubRelease:
    assets = data.get("assets") or []
    # Prefer a real downloadable asset; fall back to the release page.
    download_url = ""
    for asset in assets:
        if isinstance(asset, dict) and asset.get("browser_download_url"):
            download_url = str(asset["browser_download_url"])
            break
    if not download_url:
        download_url = str(data.get("html_url") or "")
    return GitHubRelease(
        version=str(data.get("tag_name") or data.get("name") or "").strip(),
        download_url=download_url,
        published_at=str(data.get("published_at") or "").strip(),
        notes=str(data.get("body") or "").strip(),
        prerelease=bool(data.get("prerelease")),
    )


def fetch_releases(api_url: str = GITHUB_RELEASES_API, timeout: int = 10) -> list[GitHubRelease]:
    """All non-draft GitHub releases (newest-first as GitHub returns them)."""
    request = Request(
        api_url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Quill-Updater"},
    )
    with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        payload = response.read().decode("utf-8", errors="strict")
    raw = json.loads(payload)
    if not isinstance(raw, list):
        raise ValueError("GitHub releases payload must be a JSON array")
    return [_release_from_json(r) for r in raw if isinstance(r, dict) and not r.get("draft")]


def select_latest(
    releases: list[GitHubRelease], include_prereleases: bool = False
) -> GitHubRelease | None:
    candidates = [r for r in releases if include_prereleases or not r.prerelease]
    if not candidates:
        return None
    return max(candidates, key=lambda r: _version_tuple(r.version))


def find_release(releases: list[GitHubRelease], version: str) -> GitHubRelease | None:
    """The release whose tag matches ``version`` (so we can tell if the running
    build is itself a prerelease)."""
    target = _version_tuple(version)
    for release in releases:
        if _version_tuple(release.version) == target:
            return release
    return None


def parse_update_manifest(payload: str) -> UpdateManifest:
    raw = json.loads(payload)
    if not isinstance(raw, dict):
        raise ValueError("Manifest payload must be a JSON object")
    manifest = UpdateManifest(
        version=str(raw.get("version", "")).strip(),
        download_url=str(raw.get("download_url", "")).strip(),
        published_at=str(raw.get("published_at", "")).strip(),
        notes=str(raw.get("notes", "")).strip(),
        signature=str(raw.get("signature", "")).strip(),
    )
    if not manifest.version or not manifest.download_url or not manifest.signature:
        raise ValueError("Manifest is missing required fields")
    if not verify_manifest_signature(manifest):
        raise ValueError("Manifest signature verification failed")
    return manifest


def verify_manifest_signature(manifest: UpdateManifest) -> bool:
    canonical = json.dumps(
        {
            "download_url": manifest.download_url,
            "notes": manifest.notes,
            "published_at": manifest.published_at,
            "version": manifest.version,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = hashlib.sha256(f"{canonical}|{_SIGNATURE_SALT}".encode()).hexdigest()
    return hmac.compare_digest(manifest.signature, expected)


def is_newer_version(current: str, available: str) -> bool:
    return _version_tuple(available) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("v")
    parts = cleaned.split(".")
    integers: list[int] = []
    for index in range(3):
        if index < len(parts):
            token = "".join(char for char in parts[index] if char.isdigit())
            integers.append(int(token or "0"))
        else:
            integers.append(0)
    return integers[0], integers[1], integers[2]


def download_release_asset(url: str, destination, timeout: int = 60) -> None:
    """Download an update asset to ``destination`` (verified TLS)."""
    request = Request(url, headers={"User-Agent": "Quill-Updater"})
    with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        data = response.read()
    with open(destination, "wb") as handle:
        handle.write(data)


__all__ = [
    "DEFAULT_UPDATE_MANIFEST_URL",
    "GITHUB_RELEASES_API",
    "GitHubRelease",
    "UpdateManifest",
    "URLError",
    "download_release_asset",
    "fetch_latest_release",
    "fetch_releases",
    "find_release",
    "select_latest",
    "fetch_update_manifest",
    "is_newer_version",
    "parse_update_manifest",
    "verify_manifest_signature",
]
