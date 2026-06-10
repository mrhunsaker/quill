from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quill.core.plain_language import lint_plain_language

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GlowFinding:
    rule_id: str
    severity: str
    message: str
    suggestion: str
    line: int | None = None
    column: int | None = None
    fixable: bool = False


@dataclass(frozen=True, slots=True)
class GlowFix:
    description: str


@dataclass(frozen=True, slots=True)
class GlowFixResult:
    text: str
    fixes: tuple[GlowFix, ...]


_GENERIC_LINK_TEXT = {
    "click here",
    "here",
    "read more",
    "more",
    "link",
    "this",
}


def audit_text(text: str, markup: str) -> list[GlowFinding]:
    if markup == "markdown":
        findings = _audit_markdown(text)
    elif markup == "html":
        findings = _audit_html(text)
    else:
        findings = _audit_plain(text)
    findings.extend(_audit_common(text))
    findings.sort(key=lambda item: (item.line or 0, item.column or 0, item.rule_id))
    return findings


def build_audit_report(document_name: str, text: str, markup: str, scope_label: str) -> str:
    findings = audit_text(text, markup)
    fixable = sum(1 for item in findings if item.fixable)
    lines = [
        f"GLOW audit for {document_name}",
        "",
        f"Scope: {scope_label}",
        f"Format: {markup}",
        f"Findings: {len(findings)}",
        f"Automatically fixable: {fixable}",
    ]
    if not findings:
        lines.extend([
            "",
            "No deterministic GLOW findings detected in this scope.",
            "The document is ready for deeper human review and export checks.",
        ])
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "Findings:"])
    for index, finding in enumerate(findings, start=1):
        location = ""
        if finding.line is not None:
            location = f" (line {finding.line}"
            if finding.column is not None:
                location += f", column {finding.column}"
            location += ")"
        fixable_suffix = " [auto-fix]" if finding.fixable else ""
        lines.append(
            f"{index}. [{finding.severity.upper()}] {finding.rule_id}{location}{fixable_suffix}"
        )
        lines.append(f"   {finding.message}")
        lines.append(f"   Suggestion: {finding.suggestion}")
    return "\n".join(lines).rstrip() + "\n"


def fix_text(text: str, markup: str) -> GlowFixResult:
    updated = text
    fixes: list[GlowFix] = []
    updated, trimmed = _trim_trailing_whitespace(updated)
    if trimmed:
        fixes.append(GlowFix("Trimmed trailing whitespace"))
    if markup == "markdown":
        updated, markdown_fixes = _fix_markdown(updated)
        fixes.extend(markdown_fixes)
    elif markup == "html":
        updated, html_fixes = _fix_html(updated)
        fixes.extend(html_fixes)
    return GlowFixResult(text=updated, fixes=tuple(fixes))


def build_fix_report(
    document_name: str,
    result: GlowFixResult,
    markup: str,
    scope_label: str,
) -> str:
    lines = [
        f"GLOW fixes for {document_name}",
        "",
        f"Scope: {scope_label}",
        f"Format: {markup}",
        f"Applied fixes: {len(result.fixes)}",
    ]
    if not result.fixes:
        lines.extend(["", "No deterministic GLOW fixes were available for this scope."])
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "Applied fixes:"])
    for index, fix in enumerate(result.fixes, start=1):
        lines.append(f"{index}. {fix.description}")
    return "\n".join(lines).rstrip() + "\n"


def _audit_common(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    for issue in lint_plain_language(text):
        findings.append(
            GlowFinding(
                rule_id="GLOW-PLAIN-LANGUAGE",
                severity="info",
                message=f'Consider replacing "{issue.phrase}" with plainer language.',
                suggestion=f'Use "{issue.suggestion}" instead.',
                line=issue.line,
                column=issue.column,
            )
        )
    for line_number, paragraph in enumerate(text.split("\n\n"), start=1):
        compact = paragraph.strip()
        if not compact:
            continue
        if len(compact) > 600:
            findings.append(
                GlowFinding(
                    rule_id="GLOW-DENSE-PARAGRAPH",
                    severity="warning",
                    message="This paragraph is long and may be difficult to review or read aloud.",
                    suggestion="Split the paragraph into shorter units or add headings.",
                    line=line_number,
                    column=1,
                )
            )
    return findings


def _audit_plain(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    if "\t" in text:
        line, column = _line_column_for_offset(text, text.index("\t"))
        findings.append(
            GlowFinding(
                rule_id="GLOW-TAB-INDENT",
                severity="warning",
                message="Tab characters can create inconsistent reading and export behavior.",
                suggestion="Replace tabs with spaces before sharing or exporting.",
                line=line,
                column=column,
            )
        )
    return findings


def _audit_markdown(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    previous_heading_level = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        heading_match = re.match(r"^(#{1,6})([^\s#].*)$", line)
        if heading_match:
            findings.append(
                GlowFinding(
                    rule_id="GLOW-MD-HEADING-SPACING",
                    severity="warning",
                    message="Markdown headings should include a space after the # markers.",
                    suggestion="Insert a space between the heading markers and the heading text.",
                    line=line_number,
                    column=len(heading_match.group(1)) + 1,
                    fixable=True,
                )
            )
        spaced_heading = re.match(r"^(#{1,6})\s+", line)
        if spaced_heading:
            level = len(spaced_heading.group(1))
            if previous_heading_level and level > previous_heading_level + 1:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-HEADING-JUMP",
                        severity="warning",
                        message="Heading levels jump by more than one level.",
                        suggestion="Use intermediate heading levels for a smoother outline.",
                        line=line_number,
                        column=1,
                    )
                )
            previous_heading_level = level
        for match in re.finditer(r"!?\[([^\]]*)\]\(([^)]+)\)", line):
            label = match.group(1).strip().lower()
            if line[match.start()] == "!" and not label:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-IMAGE-ALT",
                        severity="error",
                        message="Markdown image is missing alternative text.",
                        suggestion="Add concise alt text inside the image brackets.",
                        line=line_number,
                        column=match.start() + 1,
                    )
                )
            if line[match.start()] != "!" and label in _GENERIC_LINK_TEXT:
                findings.append(
                    GlowFinding(
                        rule_id="GLOW-MD-LINK-TEXT",
                        severity="warning",
                        message="Markdown link text is too generic.",
                        suggestion="Use link text that describes the destination or purpose.",
                        line=line_number,
                        column=match.start() + 1,
                    )
                )
    return findings


def _audit_html(text: str) -> list[GlowFinding]:
    findings: list[GlowFinding] = []
    html_tag = re.search(r"<html\b([^>]*)>", text, re.IGNORECASE)
    if html_tag is not None and re.search(r"\blang\s*=", html_tag.group(1), re.IGNORECASE) is None:
        line, column = _line_column_for_offset(text, html_tag.start())
        findings.append(
            GlowFinding(
                rule_id="GLOW-HTML-LANG",
                severity="error",
                message="The html element is missing a language attribute.",
                suggestion='Add lang="en" (or the correct language code) to the html element.',
                line=line,
                column=column,
                fixable=True,
            )
        )
    heading_matches = list(re.finditer(r"<h([1-6])\b", text, re.IGNORECASE))
    previous_level = 0
    for match in heading_matches:
        level = int(match.group(1))
        if previous_level and level > previous_level + 1:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-HEADING-JUMP",
                    severity="warning",
                    message="HTML heading levels jump by more than one level.",
                    suggestion="Use intermediate heading levels for a predictable outline.",
                    line=line,
                    column=column,
                )
            )
        previous_level = level
    for match in re.finditer(r"<img\b([^>]*)>", text, re.IGNORECASE):
        attributes = match.group(1)
        if re.search(r"\balt\s*=", attributes, re.IGNORECASE) is None:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-IMG-ALT",
                    severity="error",
                    message="Image element is missing an alt attribute.",
                    suggestion='Add alt text or alt="" for decorative images.',
                    line=line,
                    column=column,
                    fixable=True,
                )
            )
    for match in re.finditer(r"<a\b[^>]*>(.*?)</a>", text, re.IGNORECASE | re.DOTALL):
        link_text = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
        if link_text in _GENERIC_LINK_TEXT:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-LINK-TEXT",
                    severity="warning",
                    message="Link text is too generic.",
                    suggestion="Use text that describes the destination or action.",
                    line=line,
                    column=column,
                )
            )
    for match in re.finditer(r"<table\b.*?</table>", text, re.IGNORECASE | re.DOTALL):
        if re.search(r"<th\b", match.group(0), re.IGNORECASE) is None:
            line, column = _line_column_for_offset(text, match.start())
            findings.append(
                GlowFinding(
                    rule_id="GLOW-HTML-TABLE-HEADERS",
                    severity="warning",
                    message="Table does not contain header cells.",
                    suggestion="Add th elements for header rows or columns before export.",
                    line=line,
                    column=column,
                )
            )
    return findings


def _fix_markdown(text: str) -> tuple[str, list[GlowFix]]:
    fixes: list[GlowFix] = []
    updated = re.sub(r"(?m)^(#{1,6})([^\s#])", r"\1 \2", text)
    if updated != text:
        fixes.append(GlowFix("Inserted missing spaces after Markdown heading markers"))
    return updated, fixes


def _fix_html(text: str) -> tuple[str, list[GlowFix]]:
    fixes: list[GlowFix] = []
    updated = text
    updated = re.sub(
        r"<html\b(?![^>]*\blang\s*=)([^>]*)>",
        r'<html lang="en"\1>',
        updated,
        count=1,
        flags=re.IGNORECASE,
    )
    if updated != text:
        fixes.append(GlowFix('Added lang="en" to the html element'))
        text = updated

    def add_alt(match: re.Match[str]) -> str:
        attributes = match.group(1).rstrip()
        space = " " if attributes else ""
        return f'<img{space}{attributes} alt="">'

    updated = re.sub(
        r"<img\b((?:(?!\balt\s*=)[^>])*)>",
        add_alt,
        updated,
        flags=re.IGNORECASE,
    )
    if updated != text:
        fixes.append(GlowFix("Added empty alt attributes to img elements missing alt text"))
    return updated, fixes


def _trim_trailing_whitespace(text: str) -> tuple[str, bool]:
    updated = re.sub(r"[ \t]+(?=\r?$)", "", text, flags=re.MULTILINE)
    return updated, updated != text


def _line_column_for_offset(text: str, offset: int) -> tuple[int, int]:
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    line_start = prefix.rfind("\n")
    if line_start < 0:
        return line, offset + 1
    return line, offset - line_start


# ---------------------------------------------------------------------------
# GLOW shared-core engine seam (GLOW-1).
#
# When the optional `quill-glow-core` backend is installed (the `glow` extra),
# QUILL audits and fixes structured documents through that shared engine. When
# it is absent, the seam degrades to a safe, QUILL-native result so `core`
# never hard-fails and keeps no hard dependency on the optional package. The
# in-editor text audit above (`audit_text`/`fix_text`) is unchanged.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GlowFileAuditResult:
    """Adapted result of a shared-core structured-document audit."""

    path: str
    score: int
    grade: str
    findings: tuple[GlowFinding, ...]
    backend: str


@dataclass(frozen=True, slots=True)
class GlowFileFixResult:
    """Adapted result of a shared-core structured-document fix."""

    output_path: str
    total_fixes: int
    audit: GlowFileAuditResult
    warnings: tuple[str, ...]
    backend: str


# Maps shared-core severities onto QUILL's three presentation levels. Per
# GLOW-1, critical/high collapse to "error"; medium-band severities become
# "warning"; the remainder are informational.
_SEVERITY_MAP = {
    "critical": "error",
    "high": "error",
    "error": "error",
    "medium": "warning",
    "moderate": "warning",
    "warning": "warning",
    "warn": "warning",
    "low": "info",
    "minor": "info",
    "info": "info",
    "informational": "info",
}


def _map_severity(severity: str) -> str:
    return _SEVERITY_MAP.get(severity.strip().lower(), "warning")


def _parse_location(location: str) -> tuple[int | None, int | None]:
    """Best-effort line/column extraction from a shared-core location string.

    Accepts trailing ``:line:column`` or ``:line`` suffixes (as emitted for
    text-like sources) and a bare ``line N`` form. Returns ``(None, None)`` for
    opaque locations such as a file path or a structural address.
    """
    text = location.strip()
    if not text:
        return None, None
    tail = re.search(r":(\d+)(?::(\d+))?$", text)
    if tail is not None:
        line = int(tail.group(1))
        column = int(tail.group(2)) if tail.group(2) is not None else None
        return line, column
    worded = re.search(r"\bline\s+(\d+)(?:\D+(\d+))?", text, re.IGNORECASE)
    if worded is not None:
        line = int(worded.group(1))
        column = int(worded.group(2)) if worded.group(2) is not None else None
        return line, column
    return None, None


def _glow_finding_to_quill(finding: Any) -> GlowFinding:
    """Adapt a shared-core ``Finding`` (duck-typed) into a QUILL ``GlowFinding``.

    Reads attributes defensively so the adapter tolerates the absence of the
    optional package and minor shape drift. ACB metadata and the source
    location are folded into the suggestion text because ``GlowFinding`` is a
    flat presentation record; the structural score/grade ride on the enclosing
    :class:`GlowFileAuditResult`.
    """
    rule_id = str(getattr(finding, "rule_id", "") or "GLOW-UNKNOWN")
    severity = _map_severity(str(getattr(finding, "severity", "") or "warning"))
    message = str(getattr(finding, "message", "") or "")
    description = str(getattr(finding, "description", "") or "")
    location = str(getattr(finding, "location", "") or "")
    fixable = bool(getattr(finding, "auto_fixable", False))
    line, column = _parse_location(location)

    suggestion_parts: list[str] = []
    if description:
        suggestion_parts.append(description)
    metadata = getattr(finding, "metadata", None)
    if isinstance(metadata, dict) and metadata:
        rendered = ", ".join(f"{key}: {value}" for key, value in sorted(metadata.items()))
        suggestion_parts.append(f"Details: {rendered}.")
    if not suggestion_parts:
        suggestion_parts.append("Review this finding and apply an accessible correction.")
    suggestion = " ".join(suggestion_parts)

    return GlowFinding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        suggestion=suggestion,
        line=line,
        column=column,
        fixable=fixable,
    )


def _load_glow_core() -> Any:
    """Return the imported ``quill_glow_core`` module, or ``None`` when absent."""
    try:
        import quill_glow_core
    except ImportError:
        return None
    except Exception as error:  # noqa: BLE001
        logger.warning("quill_glow_core import failed unexpectedly: %s", error)
        return None
    return quill_glow_core


def glow_backend_available() -> bool:
    """True when the optional GLOW shared-core engine can be imported."""
    return _load_glow_core() is not None


def _backend_name(core: Any) -> str:
    """Report the active shared-core backend ("glow", "safe-mode", ...)."""
    try:
        telemetry = core.get_startup_telemetry()
    except Exception as error:  # noqa: BLE001
        logger.warning("GLOW get_startup_telemetry failed: %s", error)
        telemetry = None
    if telemetry is None:
        try:
            core.configure_default_services()
            telemetry = core.get_startup_telemetry()
        except Exception as error:  # noqa: BLE001
            logger.warning("GLOW configure_default_services/telemetry failed: %s", error)
            telemetry = None
    if telemetry is not None:
        return str(getattr(telemetry, "backend", "") or "unknown")
    return "unknown"


def get_glow_services() -> Any:
    """Return the configured shared-core services, or ``None`` when absent.

    Delegates to ``quill_glow_core.get_services()``, which auto-selects the
    real GLOW backend when installed and the safe ``NoOpCoreServices`` fallback
    otherwise. Returns ``None`` only when the package itself is not installed.
    """
    core = _load_glow_core()
    if core is None:
        return None
    try:
        return core.get_services()
    except Exception as error:  # noqa: BLE001
        logger.warning("GLOW get_services failed: %s", error)
        return None


@dataclass(frozen=True, slots=True)
class GlowEngineVersions:
    """The active GLOW engine and rule versions, with a safe fallback.

    ``backend`` is ``"unavailable"`` when the optional package is not installed;
    the version strings are empty in that case so callers can render a stable
    "not installed" message without special-casing missing attributes.
    """

    backend: str
    release_version: str
    core_version: str
    components: tuple[tuple[str, str], ...]


def glow_engine_versions() -> GlowEngineVersions:
    """Report the active GLOW engine and rule version (GLOW-6).

    Reads ``get_component_versions`` plus the startup telemetry backend name.
    Never raises: a missing package or a backend error degrades to an
    ``unavailable``/empty manifest so diagnostics and the About dialog can show
    an honest fallback.
    """
    core = _load_glow_core()
    if core is None:
        return GlowEngineVersions(
            backend="unavailable",
            release_version="",
            core_version="",
            components=(),
        )
    backend = _backend_name(core)
    try:
        manifest = core.get_component_versions()
    except Exception as error:  # noqa: BLE001
        logger.warning("GLOW get_component_versions failed: %s", error)
        manifest = None
    if manifest is None:
        return GlowEngineVersions(
            backend=backend,
            release_version="",
            core_version="",
            components=(),
        )
    raw_components = getattr(manifest, "components", {}) or {}
    try:
        components = tuple((str(key), str(value)) for key, value in sorted(raw_components.items()))
    except Exception as error:  # noqa: BLE001
        logger.warning("GLOW component version parsing failed: %s", error)
        components = ()
    return GlowEngineVersions(
        backend=backend,
        release_version=str(getattr(manifest, "release_version", "") or ""),
        core_version=str(getattr(manifest, "core_version", "") or ""),
        components=components,
    )


def glow_engine_version_summary() -> str:
    """A one-line, human-readable summary of the active GLOW engine (GLOW-6)."""
    versions = glow_engine_versions()
    if versions.backend == "unavailable":
        return "GLOW engine: not installed"
    release = versions.release_version or "unknown"
    core_version = versions.core_version or "unknown"
    return f"GLOW engine: {versions.backend} (release {release}, rules {core_version})"


def _unavailable_audit(path: str) -> GlowFileAuditResult:
    return GlowFileAuditResult(
        path=path,
        score=0,
        grade="F",
        findings=(
            GlowFinding(
                rule_id="GLOW-CORE-UNAVAILABLE",
                severity="warning",
                message="The GLOW accessibility engine is not installed.",
                suggestion=(
                    "Install QUILL's optional 'glow' extra to audit and fix "
                    "structured documents (DOCX, PPTX, XLSX, PDF, EPUB)."
                ),
                fixable=False,
            ),
        ),
        backend="unavailable",
    )


# ---------------------------------------------------------------------------
# GLOW optional networked features (GLOW-7).
#
# The shared core ships optional features that can reach the network — AI
# alt-text generation, Presidio PII redaction, and WCAG language processing.
# QUILL's no-silent-network rule (GATE-9) requires these to be OFF by default
# and turned on only with explicit per-action consent. The seam below makes
# that guarantee structural: a default `audit_file`/`fix_file` call forwards no
# feature-enabling option, so the backend runs its on-device deterministic
# rules only. A networked feature is reached solely when a caller passes a
# `GlowNetworkConsent` that explicitly enables it.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GlowNetworkFeature:
    """A GLOW optional feature that may perform an outbound network call."""

    feature_id: str
    label: str
    description: str


GLOW_NETWORK_FEATURES: tuple[GlowNetworkFeature, ...] = (
    GlowNetworkFeature(
        feature_id="ai_alt_text",
        label="AI alt-text generation",
        description="Generate image alt text with a cloud AI model.",
    ),
    GlowNetworkFeature(
        feature_id="pii_redaction",
        label="PII redaction",
        description="Detect and redact personal data with Presidio.",
    ),
    GlowNetworkFeature(
        feature_id="language_processing",
        label="WCAG language processing",
        description="Analyze readability and language with a networked service.",
    ),
)


@dataclass(frozen=True, slots=True)
class GlowNetworkConsent:
    """Per-feature consent for GLOW's optional networked features.

    Every feature defaults to ``False`` (off). A networked feature is only
    reachable when the caller constructs this with the matching flag set to
    ``True`` after obtaining explicit, per-action user consent.
    """

    ai_alt_text: bool = False
    pii_redaction: bool = False
    language_processing: bool = False

    def enabled_feature_ids(self) -> frozenset[str]:
        enabled = {
            feature.feature_id
            for feature in GLOW_NETWORK_FEATURES
            if getattr(self, feature.feature_id, False)
        }
        return frozenset(enabled)

    def is_any_enabled(self) -> bool:
        return bool(self.enabled_feature_ids())

    def to_backend_kwargs(self) -> dict[str, bool]:
        """Backend kwargs for the consented features, or ``{}`` when none.

        The default (no feature enabled) returns an empty mapping, so the GLOW
        seam forwards nothing network-enabling on the default path.
        """
        return {feature_id: True for feature_id in sorted(self.enabled_feature_ids())}


def glow_network_features_all_off() -> GlowNetworkConsent:
    """The default consent state: every optional networked feature off."""
    return GlowNetworkConsent()


def audit_file(
    path: str | Path,
    *,
    consent: GlowNetworkConsent | None = None,
    **kwargs: Any,
) -> GlowFileAuditResult:
    """Audit a structured document through the shared GLOW core.

    Falls back to a safe, QUILL-native "engine unavailable" result when the
    optional package is absent, so callers never have to special-case the
    missing backend. Optional networked features stay off unless ``consent``
    explicitly enables them (GLOW-7).
    """
    target = str(path)
    services = get_glow_services()
    if services is None:
        return _unavailable_audit(target)
    network_kwargs = consent.to_backend_kwargs() if consent is not None else {}
    result = services.audit_by_extension(path, **network_kwargs, **kwargs)
    findings = tuple(_glow_finding_to_quill(item) for item in result.findings)
    return GlowFileAuditResult(
        path=str(getattr(result, "file_path", target)),
        score=int(getattr(result, "score", 0)),
        grade=str(getattr(result, "grade", "") or "F"),
        findings=findings,
        backend=_backend_name(_load_glow_core()),
    )


def fix_file(
    path: str | Path,
    output_path: str | Path | None = None,
    *,
    consent: GlowNetworkConsent | None = None,
    **kwargs: Any,
) -> GlowFileFixResult:
    """Fix a structured document through the shared GLOW core.

    Returns a safe, no-op result when the optional package is absent. Optional
    networked features stay off unless ``consent`` explicitly enables them
    (GLOW-7).
    """
    target = str(path)
    services = get_glow_services()
    if services is None:
        audit = _unavailable_audit(target)
        return GlowFileFixResult(
            output_path=str(output_path) if output_path is not None else target,
            total_fixes=0,
            audit=audit,
            warnings=("The GLOW accessibility engine is not installed; no changes were made.",),
            backend="unavailable",
        )
    network_kwargs = consent.to_backend_kwargs() if consent is not None else {}
    result = services.fix_by_extension(path, output_path, **network_kwargs, **kwargs)
    audit_result = getattr(result, "audit_result", None)
    if audit_result is not None:
        findings = tuple(_glow_finding_to_quill(item) for item in audit_result.findings)
        audit = GlowFileAuditResult(
            path=str(getattr(audit_result, "file_path", target)),
            score=int(getattr(audit_result, "score", 0)),
            grade=str(getattr(audit_result, "grade", "") or "F"),
            findings=findings,
            backend=_backend_name(_load_glow_core()),
        )
    else:
        audit = _unavailable_audit(target)
    return GlowFileFixResult(
        output_path=str(getattr(result, "output_path", target)),
        total_fixes=int(getattr(result, "total_fixes", 0)),
        audit=audit,
        warnings=tuple(str(item) for item in getattr(result, "warnings", ())),
        backend=_backend_name(_load_glow_core()),
    )


def build_file_audit_report(result: GlowFileAuditResult) -> str:
    """Render an adapted structured-document audit as plain text."""
    fixable = sum(1 for item in result.findings if item.fixable)
    lines = [
        f"GLOW structured audit for {result.path}",
        "",
        f"Engine: {result.backend}",
        f"Score: {result.score} (grade {result.grade})",
        f"Findings: {len(result.findings)}",
        f"Automatically fixable: {fixable}",
    ]
    if not result.findings:
        lines.extend(["", "No GLOW findings detected for this document."])
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "Findings:"])
    for index, finding in enumerate(result.findings, start=1):
        location = ""
        if finding.line is not None:
            location = f" (line {finding.line}"
            if finding.column is not None:
                location += f", column {finding.column}"
            location += ")"
        fixable_suffix = " [auto-fix]" if finding.fixable else ""
        lines.append(
            f"{index}. [{finding.severity.upper()}] {finding.rule_id}{location}{fixable_suffix}"
        )
        lines.append(f"   {finding.message}")
        lines.append(f"   Suggestion: {finding.suggestion}")
    return "\n".join(lines).rstrip() + "\n"
