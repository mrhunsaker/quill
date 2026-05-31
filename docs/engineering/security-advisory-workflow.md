# Security Advisory Workflow

This runbook defines how QUILL handles private vulnerability coordination.

## Intake

1. Receive report through `SECURITY.md` private channel.
2. Acknowledge receipt and open a private advisory in GitHub Security Advisories.
3. Classify severity and affected versions.

## Triage

1. Reproduce issue in a controlled environment.
2. Assess exploitability, user impact, and affected surfaces.
3. Record mitigation options and patch strategy.

## Patch and validation

1. Implement fix on a private branch when needed.
2. Validate with standard checks:
   - `ruff check .`
   - `pytest -q`
3. Add regression tests where appropriate.

## Disclosure

1. Coordinate disclosure date with reporter when possible.
2. Publish patched release and advisory details.
3. Include clear upgrade/mitigation guidance for users.

## Post-incident actions

1. Add follow-up hardening tasks.
2. Update security checks/process docs if gaps were found.
