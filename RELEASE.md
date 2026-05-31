# QUILL Release Process

This document defines the release flow for QUILL.

## Release goals

1. Ship predictable, accessibility-safe releases.
2. Keep changelogs accurate and contributor-visible.
3. Ensure every release has validated docs and artifacts.

## Release cadence

- Normal releases are cut from `main`.
- Hotfixes may use short-lived `release/x.y.z` branches when needed.

## Required release checks

Before tagging a release:

1. `ruff check .`
2. `pytest -q`
3. `python scripts/check_docs_artifacts.py`
4. Windows packaging workflow readiness (`.github/workflows/windows-release.yml`)

## Changelog and notes

- Release notes are prepared through Release Drafter.
- Labels are used to group changes by feature area and impact.
- Include accessibility, reliability, and security changes explicitly.

## Branch and merge policy

- `main` is branch-protected with required checks and pull-request reviews.
- **Admin bypass remains enabled** to allow emergency direct commits/pushes when required.
- Emergency pushes must be followed by:
  1. post-merge explanation in commit/PR notes,
  2. follow-up tests and remediation if needed.

## Versioning

- Follow semantic versioning intent for user-visible behavior:
  - Patch: bug fixes and low-risk changes
  - Minor: additive features and workflow improvements
  - Major: breaking changes or large platform shifts

## Release checklist

1. Confirm branch is green and up to date.
2. Review drafted release notes for correctness and tone.
3. Confirm docs artifacts are updated (`.md`, `.html`, `.epub` parity).
4. Tag release and publish notes.
5. Verify distribution artifacts and checksums.
6. Announce release with key highlights and known limitations.
