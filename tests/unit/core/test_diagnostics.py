from __future__ import annotations

import json
import zipfile
from pathlib import Path

from quill.core.diagnostics import (
    build_bug_report_payload,
    build_diagnostics_review_text,
    build_support_issue_url,
    load_diagnostic_events,
    record_diagnostic_event,
    write_diagnostics_bundle,
)
from quill.core.document import Document
from quill.core.notifications import Notification
from quill.core.settings import Settings


def test_record_diagnostic_event_round_trips(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))

    record_diagnostic_event("command", "tools.pandoc_wizard")
    events = load_diagnostic_events()

    assert events[-1].kind == "command"
    assert events[-1].name == "tools.pandoc_wizard"


def test_write_diagnostics_bundle_writes_expected_members(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path / "data"))
    target = tmp_path / "quill-diagnostics.zip"
    document = Document(text="hello", path=Path("C:/Docs/sample.md"), modified=False)

    write_diagnostics_bundle(
        target,
        settings=Settings(),
        keymap={"file.open": "Ctrl+O"},
        notifications=[
            Notification(
                timestamp="2026-05-29T00:00:00+00:00",
                category="info",
                message="Ready",
            )
        ],
        current_document=document,
        include_file_paths=False,
        extra_environment={"screen_reader": "NVDA"},
    )

    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
        assert "metadata.json" in names
        assert "recent-actions.json" in names
        assert "settings-redacted.json" in names
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["screen_reader"] == "NVDA"
        assert metadata["current_document"]["path_hash"]


def test_build_bug_report_payload_mentions_diagnostics() -> None:
    payload = build_bug_report_payload(current_document=Document(text="x"))

    assert "Bug report:" in payload["summary"]
    assert "Save Diagnostics" in payload["body"]


def test_build_bug_report_payload_supports_user_entered_sections() -> None:
    payload = build_bug_report_payload(
        current_document=Document(text="x", path=Path("C:/Docs/sample.md")),
        summary_override="Bug report: Spell check speaks too fast",
        happened="Pressed Speak Word and could not follow the letters.",
        expected="Letters should be spoken slowly and clearly.",
        steps="1. Open spell check\n2. Select misspelling\n3. Press Speak Word",
        diagnostics_note="Attach diagnostics bundle: C:\\Temp\\quill-diagnostics.zip",
    )

    assert payload["summary"] == "Bug report: Spell check speaks too fast"
    assert "Pressed Speak Word" in payload["body"]
    assert "Expected behavior:" in payload["body"]
    assert "Steps to reproduce:" in payload["body"]
    assert "Attach diagnostics bundle" in payload["body"]


def test_build_diagnostics_review_text_mentions_hashing() -> None:
    review = build_diagnostics_review_text(
        settings=Settings(),
        keymap={"file.open": "Ctrl+O"},
        notifications=[],
        current_document=Document(text="x", path=Path("C:/Docs/a.md")),
        include_file_paths=False,
    )

    assert "Diagnostics Review" in review
    assert "File path will be hashed" in review


def test_build_support_issue_url_targets_support_hub() -> None:
    url = build_support_issue_url(
        {"summary": "Bug report: sample", "body": "Body"},
        source_app="Quill",
        version="1.0.0",
        platform_label="Windows 11",
    )

    assert url.startswith("https://github.com/Community-Access/support/issues/new?")
    assert "source-app=Quill" in url


def test_diagnostics_bundle_redacts_log_secrets(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "latest.log").write_text(
        "Authorization: Bearer super-secret-token\napi_key=abc123\nvalue=sk-test-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("QUILL_DATA_DIR", str(data_dir))

    target = tmp_path / "quill-diagnostics.zip"
    write_diagnostics_bundle(
        target,
        settings=Settings(),
        keymap={},
        notifications=[],
        current_document=None,
        include_file_paths=False,
    )

    with zipfile.ZipFile(target) as archive:
        payload = archive.read("logs/latest.log").decode("utf-8")
        assert "super-secret-token" not in payload
        assert "abc123" not in payload
        assert "sk-test-secret" not in payload
        assert "[REDACTED]" in payload