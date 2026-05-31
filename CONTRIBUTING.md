# Contributing to QUILL

Thank you for helping improve QUILL.

QUILL is a screen-reader-first Windows writing environment. Contributions should
preserve that core direction: practical keyboard workflows, stable editing,
accessible defaults, and clear user control.

## Before you start

1. Read the architecture and product expectations in:
   - `docs/QUILL-PRD.md`
   - `docs/engineering/README.md`
2. Review project conduct rules in `CODE_OF_CONDUCT.md`.
3. Check existing issues and pull requests before starting overlapping work.
4. Review project decision process in `GOVERNANCE.md`.

## Development setup

1. Install Python 3.12.
2. Install dependencies:
   - `pip install -e ".[ui,dev]"`
3. Run QUILL locally:
   - `python -m quill`

## Making changes

1. Create a feature branch from `main`.
2. Keep changes focused and small enough to review.
3. Follow the current module boundaries:
   - `quill/core`: no `wx` imports
   - `quill/ui`: UI behavior and dialogs
   - `quill/io`: format readers/writers
   - `quill/platform/windows`: Windows-specific integration
4. Prefer existing helpers and patterns over introducing parallel paths.
5. Keep user-facing text clear and accessibility-friendly.

## Quality checks

Run these before opening a pull request:

- Lint: `ruff check .`
- Tests: `pytest -q`
- Docs artifact parity (if docs changed): `python scripts/check_docs_artifacts.py`

If your change updates `docs/*.md`, regenerate matching artifacts:

- `pandoc docs\\<name>.md -f gfm -t html5 -s -o docs\\<name>.html`
- `pandoc docs\\<name>.md -f gfm -t epub3 -o docs\\<name>.epub`

## Pull request expectations

A strong PR includes:

1. A clear summary of what changed and why.
2. Notes on accessibility impact, if any.
3. Notes on risk or migration impact, if any.
4. Evidence of the checks you ran.

Please avoid mixing unrelated refactors with feature or bug-fix work.

## Reporting bugs and proposing features

- For product/support issues, users can use in-app `Help -> Report a Bug`.
- For repository work, open a GitHub issue with:
  - expected behavior
  - actual behavior
  - reproduction steps
  - environment details
- Use the most specific issue template available (accessibility, AI, intake,
  snippets, dictation, performance, or general bug/feature).
- Use GitHub Discussions for Q&A and early design exploration.

## Security issues

Do not open public issues for vulnerabilities. Follow `SECURITY.md` for private
reporting.

Before opening a PR, quickly sanity-check security posture:

1. No secrets or credentials in code, tests, fixtures, or docs.
2. No user document content added to logs/diagnostics paths.
3. New network calls are explicit and user-controlled.
4. New file/command paths are validated and not shell-interpolated.

## Translation contributions

Localization contributors should follow:

- `docs/localization/translation-contributor-plan.md`

## License

By contributing, you agree that your contributions are licensed under the
repository's MIT license.
