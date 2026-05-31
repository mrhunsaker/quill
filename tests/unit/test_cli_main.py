from __future__ import annotations

from pathlib import Path

import pytest

from quill import __main__ as entry
from quill import __version__


def test_parse_cli_arguments_sets_known_flags() -> None:
    parsed = entry._parse_cli_arguments([
        "--safe-mode",
        "--reset-profile",
        "--diagnostics",
        "--new-window",
        "--wait",
        "--line",
        "12",
        "--column",
        "4",
        "demo.txt",
    ])

    assert parsed.safe_mode is True
    assert parsed.reset_profile is True
    assert parsed.diagnostics is True
    assert parsed.new_window is True
    assert parsed.wait is True
    assert parsed.line == 12
    assert parsed.column == 4
    assert parsed.paths == ["demo.txt"]


def test_parse_cli_arguments_help_exits_cleanly() -> None:
    with pytest.raises(SystemExit) as info:
        entry._parse_cli_arguments(["--help"])
    assert info.value.code == 0


def test_launch_configuration_applies_line_and_column_to_first_file(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")

    parsed = entry._parse_cli_arguments([
        str(first),
        str(second),
        "--line",
        "20",
        "--column",
        "6",
    ])
    requests, safe_mode, reset_profile, diagnostics_mode, force_new_window, wait = (
        entry._launch_configuration(parsed)
    )

    assert safe_mode is False
    assert reset_profile is False
    assert diagnostics_mode is False
    assert force_new_window is False
    assert wait is False
    assert len(requests) == 2
    assert requests[0].path == first.resolve()
    assert requests[0].line == 20
    assert requests[0].column == 6
    assert requests[1].path == second.resolve()
    assert requests[1].line is None
    assert requests[1].column is None


def test_main_version_prints_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(entry.sys, "argv", ["quill", "--version"])

    result = entry.main()

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == __version__
