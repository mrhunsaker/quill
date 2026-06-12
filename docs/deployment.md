# QUILL Deployment Guide

Covers distribution, update packaging, pack distribution, and release best practices.

## Table of Contents

- [Release types](#release-types)
- [Building a Windows release](#building-a-windows-release)
- [Update mechanism overview](#update-mechanism-overview)
- [Update feed format](#update-feed-format)
- [Building an update archive](#building-an-update-archive)
- [Bootstrapper binaries](#bootstrapper-binaries)
- [Update ZIP scripts](#update-zip-scripts)
- [Hosting the feed](#hosting-the-feed)
- [Publishing a release](#publishing-a-release)
- [Pack distribution](#pack-distribution)
- [Version numbering](#version-numbering)
- [Testing updates locally](#testing-updates-locally)
- [Rollback](#rollback)
- [Best practices](#best-practices)

---

## Release types

| Type | Description | Tag pattern |
|------|-------------|-------------|
| Beta | Pre-release for wider testing | `v0.5.0-beta.1` |
| Stable | Production release | `v1.0.0` |
| Hotfix | Critical-only patch | `v1.0.1` |

All three go through the same `windows-release` workflow. Mark betas as
`prerelease: true` in the GitHub release (already the default in the
workflow).

---

## Building a Windows release

The build workflow (`windows-release.yml`) runs on `push` to a `v*` tag.
To trigger it manually:

```powershell
git tag v0.5.0-beta.1
git push origin v0.5.0-beta.1
```

The workflow produces three artifacts:

- `quill-installer` — Inno Setup `.exe` installer
- `quill-portable` — standalone folder, no installer required
- `quill-release-artifacts` — checksums, SBOM, update feed stub

To build locally (requires Inno Setup 6 and Python 3.12):

```powershell
pip install -e .[ui,spellcheck,dev]
python scripts/build_windows_distribution.py `
    --bundle-python `
    --compile-installer `
    --iscc-path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" `
    --output-dir windows-distribution
```

---

## Update mechanism overview

QUILL uses the AccessibleApps `autoupdate` library (vendored at
`quill/_vendor/autoupdate/`) for incremental over-the-air updates.

The flow:

1. `QuillUpdateManager.check_for_updates()` is called (on startup or from
   Help > Check for Updates).
2. The manager fetches the update feed JSON from a hosted endpoint.
3. If the feed version is newer than the running version, the user is
   prompted via `_on_update_available`.
4. If accepted, the update ZIP is downloaded with progress announcements.
5. The ZIP is extracted to a temp directory.
6. The platform bootstrapper (`bootstrap.exe` on Windows) is moved out of
   the extracted tree and executed.
7. The bootstrapper waits for QUILL to exit, then copies the new files over
   the installation and restarts the app.

The manager announces all state changes through the screen-reader bridge
(`prism_bridge.announce`) so users with NVDA/JAWS/Narrator hear every step
without watching the UI.

---

## Update feed format

The feed is a single JSON file served over HTTPS. Example:

```json
{
  "current_version": "0.5.0",
  "description": "Accessibility improvements and bug fixes. See the release notes for details.",
  "published_at": "2026-06-12T14:00:00Z",
  "downloads": {
    "Windows": "https://releases.example.com/quill-0.5.0-windows.zip",
    "Darwin":  "https://releases.example.com/quill-0.5.0-macos.zip",
    "Linux":   "https://releases.example.com/quill-0.5.0-linux.zip"
  }
}
```

Field notes:

- `current_version` — the version string clients compare against their
  running version. See [version numbering](#version-numbering) for the
  comparison rules.
- `description` — shown to the user in the update prompt. Keep it one or
  two sentences; longer notes belong in the release notes URL.
- `downloads` — key is the `platform.system()` return value (`Windows`,
  `Darwin`, `Linux`). A client whose platform is not present skips the
  update silently.

Generate the feed with the bundled script:

```powershell
python scripts/generate_app_updater_feed.py `
    --version "0.5.0" `
    --windows-url "https://github.com/Community-Access/quill/releases/download/v0.5.0/quill-0.5.0-windows.zip" `
    --macos-url   "https://github.com/Community-Access/quill/releases/download/v0.5.0/quill-0.5.0-macos.zip" `
    --linux-url   "https://github.com/Community-Access/quill/releases/download/v0.5.0/quill-0.5.0-linux.zip" `
    --description "Accessibility improvements and bug fixes." `
    --output docs/site/updates/.quill-app-updater-v1.json
```

Commit and push; the GitHub Pages workflow publishes it automatically.

---

## Building an update archive

The update ZIP must contain:

```
quill/                   all application Python files
quill-data/              data files (words_alpha, thesaurus, schemas, quillins)
bootstrap.exe            Windows bootstrapper (see below)
```

The bootstrapper **must be at the root of the ZIP** (not in a subdirectory)
so `move_bootstrap` can find it. The rest of the layout must match the
structure that `bootstrap.exe` expects when copying files over the existing
installation.

Use `scripts/build_update_zip.py` to produce the update ZIP automatically.
It handles delta computation, bootstrapper placement, and `UPDATE_MANIFEST.json`
generation. See [Update ZIP scripts](#update-zip-scripts) for full usage.

> The bootstrapper binaries are not checked into this repo because they are
> native executables maintained upstream. Run `scripts/fetch_bootstrappers.py`
> to download them, or see
> `quill/_vendor/autoupdate/bootstrappers/README.txt` for manual instructions.

---

## Bootstrapper binaries

The bootstrapper (`bootstrap.exe` on Windows, `bootstrap-mac.sh` on macOS,
`bootstrap-lin.sh` on Linux) is built and maintained by the AccessibleApps
project:

    https://github.com/accessibleapps/app_updater

To obtain the binaries for a release build, use the bundled fetch script:

```powershell
python scripts/fetch_bootstrappers.py
```

This downloads all three bootstrappers from the upstream repo, verifies
their SHA-256 hashes, and records checksums in
`quill/_vendor/autoupdate/bootstrappers/checksums.sha256`. Re-running is
idempotent — files with matching checksums are skipped.

The binaries are not required for development or running tests. They are
only needed when building a distributable package that supports in-place
updates.

Add the `bootstrappers/` directory to the Windows installer via the Inno
Setup script generated by `build_windows_distribution.py`. The script
already includes a `[Files]` directive for the bootstrapper; verify it
points to the correct path before compiling.

---

## Update ZIP scripts

Three scripts in `scripts/` automate the update ZIP pipeline. All three are
stdlib-only and require no extra dependencies beyond what `pip install -e .`
already installs.

### `scripts/fetch_bootstrappers.py`

Downloads `bootstrap.exe`, `bootstrap-lin.sh`, and `bootstrap-mac.sh` from
the AccessibleApps upstream repo and writes a `checksums.sha256` file for
verification. Binaries land in `quill/_vendor/autoupdate/bootstrappers/` and
are excluded from git.

```powershell
# Download (idempotent — skips files whose SHA-256 matches the recorded checksum)
python scripts/fetch_bootstrappers.py

# Force re-download regardless of checksum
python scripts/fetch_bootstrappers.py --force

# Verify existing files without downloading
python scripts/fetch_bootstrappers.py --verify-only
```

The CI `build` job runs this automatically before compiling the installer.

### `scripts/generate_file_manifest.py`

Walks `quill/` and records the SHA-256 hash, size, and install path of every
distributable file. Output is `docs/site/updates/manifests/manifest-{version}.json`.
The manifest feeds `build_update_zip.py` to compute deltas.

```powershell
# Generate manifest for the current source tree
python scripts/generate_file_manifest.py --version 0.5.0

# Generate and compare against a previous release
python scripts/generate_file_manifest.py --version 0.5.0 --compare-to 0.4.9
```

Excluded from the manifest: `quill/tools/`, `__pycache__/`, `*.pyc`, `*.pyo`.
The `--compare-to` flag prints changed, added, and deleted file counts and a
net size delta — useful for sanity-checking before cutting a release.

### `scripts/build_update_zip.py`

Produces the update ZIP consumed by the autoupdate bootstrapper. By default
it runs in delta mode: only files whose SHA-256 changed since the previous
manifest are included, keeping update ZIPs lean.

```powershell
# Delta update (auto-detects base version from available manifests)
python scripts/build_update_zip.py --version 0.5.0

# Force full update
python scripts/build_update_zip.py --version 0.5.0 --mode full

# Specify base version explicitly
python scripts/build_update_zip.py --version 0.5.0 --mode delta --base-version 0.4.9

# Target a non-Windows platform
python scripts/build_update_zip.py --version 0.5.0 --platform macos
```

The ZIP always contains:

- `bootstrap.exe` (or platform equivalent) at the root
- `UPDATE_MANIFEST.json` at the root — lists which files were changed, added,
  or deleted
- Changed/added files under `python/Lib/site-packages/` (the portable
  distribution layout)

If no previous manifest exists, the script falls back to full mode
automatically.

### Running the full pipeline

```powershell
# 1. Fetch bootstrappers (once per release machine)
python scripts/fetch_bootstrappers.py

# 2. Generate the manifest for this version
python scripts/generate_file_manifest.py --version 0.5.0

# 3. Build the delta update ZIP
python scripts/build_update_zip.py --version 0.5.0

# Output: release-artifacts/quill-0.5.0-update-windows.zip
```

The CI `build` job runs all three steps automatically on each `v*` tag push.

---

## Hosting the feed

### GitHub Pages (default)

The update feed lives at:

    docs/site/updates/.quill-app-updater-v1.json

The `github-pages` workflow publishes the entire `docs/site/` tree on every
push to `main`. The feed URL used by `QuillUpdateManager` should be:

    https://community-access.github.io/quill/updates/.quill-app-updater-v1.json

Update `UPDATE_FEED_ENDPOINT` in `quill/core/settings_specs.py` (or
wherever the URL is configured) before the first beta that ships the update
check.

### Keeping the feed up to date

Workflow: after every release, regenerate the feed, commit it, and push.
The Pages deployment runs automatically:

```powershell
python scripts/generate_app_updater_feed.py --version "0.5.1" ...
git add docs/site/updates/.quill-app-updater-v1.json
git commit -m "chore: update feed to 0.5.1"
git push
```

Do not update the feed until all platform ZIPs are uploaded and their URLs
are stable. Clients check the feed on startup; a partial update (feed
updated before ZIPs are live) will offer a broken download to users.

---

## Publishing a release

1. Bump the version in `pyproject.toml` and commit.
2. Tag the commit: `git tag v0.5.0 && git push origin v0.5.0`
3. The `windows-release` workflow runs automatically:
   - runs tests (with `--ignore` for the two known-hanging tests)
   - builds the installer and portable ZIP
   - uploads artifacts
   - creates a GitHub release draft
4. Download the portable ZIP artifact, add the bootstrapper at the root,
   re-upload as the final update ZIP to the GitHub release.
5. Generate the update feed pointing at the final ZIP URLs.
6. Commit and push the feed; Pages deploys within minutes.
7. Announce the release (release notes, mailing list, etc.).

---

## Pack distribution

Packs (Quillins) are distributed as `.zip` archives containing a
`manifest.json` validated against `quill/core/schemas/extension.json`.

### Creating a pack

```powershell
# Directory structure:
my-pack/
  manifest.json
  README.md
  LICENSE
  <script-or-data files>

# Validate before distributing:
python -m quill.tools.quillin_lint my-pack --strict

# Package:
Compress-Archive -Path my-pack -DestinationPath my-pack-1.0.zip
```

### Distributing a pack

Packs can be distributed through any channel — GitHub Releases, a personal
website, email. Users install them via Tools > Quillin Manager > Install
from File.

For packs that should ship bundled with QUILL, place them in
`quill/quillins_bundled/` and submit a pull request. Bundled Quillins are
linted in CI with `--strict` and require a `README.md`, a `LICENSE`, and a
`manifest.json` with a `justification` for each capability requested.

### Pack versioning

Pack versions are free-form strings in `manifest.json`. There is no
automatic update mechanism for packs; users re-install a newer `.zip` to
upgrade.

---

## Version numbering

QUILL uses semantic versioning (`MAJOR.MINOR.PATCH`). The vendored autoupdate
library (`quill/_vendor/autoupdate/autoupdate.py`) compares versions with a
tuple-based integer comparison:

```python
tuple(int(x) for x in str(v).split("."))
```

This correctly orders `1.9` before `1.10`. The upstream library used a plain
string comparison (`"1.9" > "1.10"` evaluates True — wrong). The fix is
in `_version_tuple()` in the vendored copy; the upstream issue should be
tracked at https://github.com/accessibleapps/app_updater if a PR is
contributed.

---

## Testing updates locally

To test the full update pipeline without publishing a real release:

1. Start a local HTTP server:

   ```powershell
   python -m http.server 8765 --directory /path/to/test-assets
   ```

2. Create a test feed at `/path/to/test-assets/feed.json`:

   ```json
   {
     "current_version": "99.0.0",
     "description": "Local test update",
     "downloads": { "Windows": "http://localhost:8765/test-update.zip" }
   }
   ```

3. Create `test-update.zip` containing the app files and `bootstrap.exe`.

4. Override the feed URL in a dev settings file (do not commit):

   ```python
   # quill/core/settings.py — temporary, revert before committing
   update_feed_endpoint = "http://localhost:8765/feed.json"
   ```

5. Run QUILL and trigger Help > Check for Updates.

The screen reader should announce "Quill 99.0.0 is available", then
progress during download, then "Update ready. Quill will restart...".

For CI-safe automated tests, see `tests/unit/ui/test_update_manager.py`.
All HTTP is mocked; the bootstrapper execution step is always stubbed.

---

## Rollback

To roll back to a previous version after a bad release:

1. Update the feed to point at the previous version's ZIP:

   ```powershell
   python scripts/generate_app_updater_feed.py `
       --version "0.4.9" `
       --windows-url "https://.../quill-0.4.9-windows.zip" ...
   ```

2. Commit and push. Clients on 0.5.0 will be offered the 0.4.9 update on
   their next startup check.

   Note: `"0.4.9" > "0.5.0"` is false under string comparison, so the
   rollback feed will **not** be offered automatically. You must either:

   - Republish as a higher version number (e.g., `0.5.1-hotfix`) containing
     the older code, or
   - Ask users to reinstall manually.

   This is a known limitation of string-comparison versioning. Plan hotfix
   releases as forward increments.

---

## Best practices

**Do not update the feed before the ZIPs are live.** Users who start QUILL
in the window between feed publication and ZIP upload will get a failed
download.

**Keep description text short.** The description is read aloud by the
screen reader when the update dialog opens. Two sentences maximum; link to
the full release notes instead of embedding them.

**Sign the ZIPs.** The autoupdate library downloads and extracts ZIPs
without verifying a signature. For the beta, this is acceptable. Before
1.0, add SHA-256 checksums to the feed and verify them in
`QuillUpdateManager` before calling `extract_update`.

**Test the bootstrapper on a clean machine before each major release.**
The bootstrapper is a native binary that replaces files on disk. Run it
manually on a clean install once per release cycle to confirm the file-copy
logic matches the new distribution layout.

**Announce update availability through the screen reader, not a modal.**
The current `_on_update_available` implementation returns `True` without
showing a dialog. Before 1.0, replace this with a non-modal notification
bar (or a simple Yes/No dialog that is immediately reachable with Tab).
Never block QUILL startup on an update prompt.

**Staged rollout.** For major versions, serve the new feed to a fraction of
users first. This is not natively supported by autoupdate; implement it by
hosting multiple feed URLs (e.g., `/updates/beta.json` and
`/updates/stable.json`) and shipping beta builds that point at the beta
feed.
