from __future__ import annotations

import json
from pathlib import Path

from scripts.build_windows_distribution import (
    build_inno_setup_script,
    build_windows_distribution,
    bundled_runtime_dependencies,
    compile_inno_setup_installer,
    find_inno_setup_compiler,
)


def test_build_windows_distribution_writes_portable_and_installer_files(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "2.4.6"
""".strip(),
        encoding="utf-8",
    )

    bundle = build_windows_distribution(pyproject, tmp_path / "dist")

    portable_dir = tmp_path / "dist" / "portable"
    installer_script = tmp_path / "dist" / "installer" / "quill.iss"
    assert portable_dir.exists()
    launcher = (portable_dir / "run-quill.cmd").read_text(encoding="utf-8")
    assert launcher.startswith("@echo off")
    assert "set QUILL_PORTABLE=1" in launcher
    assert "set QUILL_APP_ROOT=%~dp0" in launcher
    assert "set QUILL_PORTABLE_ROOT=%~dp0data" in launcher
    # Launcher defaults to pythonw and supports --console for diagnostics.
    assert "QUILL_BUNDLED_PYTHON" in launcher
    assert "QUILL_BUNDLED_PYTHONW" in launcher
    assert "python\\python.exe" in launcher
    assert "python\\pythonw.exe" in launcher
    assert '"--console"' in launcher

    readme_text = (portable_dir / "README.txt").read_text(encoding="utf-8")
    assert "Quill Portable 2.4.6" in readme_text
    assert "Blind Information Technology Solutions (BITS) and Community Access" in readme_text
    assert "first run" in readme_text.lower()
    assert "Pandoc Conversion Wizard" in readme_text

    assert (portable_dir / "docs" / "userguide.md").exists()
    assert not (portable_dir / "docs" / "announcement-beta.md").exists()
    assert not (portable_dir / "docs" / "QUILL-PRD.md").exists()

    manifest_path = portable_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert (
        manifest["publisher"]
        == "Blind Information Technology Solutions (BITS) and Community Access"
    )
    assert manifest["version"] == "2.4.6"
    assert manifest["bundledPython"] is False
    assert manifest["bundledTools"] == []
    assert manifest["docs"] == [r"docs\userguide.md"]

    assert installer_script.exists()
    assert bundle["installer_script"] == str(installer_script)
    assert (tmp_path / "installer" / "quill.iss").exists()
    assert bundle["reference_installer_script"] == str(tmp_path / "installer" / "quill.iss")


def test_build_inno_setup_script_mentions_portable_bundle() -> None:
    script = build_inno_setup_script("9.9.9")

    assert '#define AppVersion "9.9.9"' in script
    assert 'Source: "..\\portable\\*"' in script
    # Publisher and accessibility-friendly installer flags are present.
    assert "Blind Information Technology Solutions (BITS) and Community Access" in script
    assert "PrivilegesRequired=lowest" in script
    assert "WizardStyle=modern" in script
    assert "DisableDirPage=no" in script
    assert "InfoAfterFile=..\\portable\\README.txt" in script
    assert "aiassistant" in script
    assert "Writing Assistant Setup" in script
    assert "User Guide" in script
    assert "Beta Announcement" not in script
    assert "Product Requirements" not in script
    assert 'Excludes: "docs\\announcement-beta.md,docs\\QUILL-PRD.md"' in script
    # File-association registry entries use HKCU only (never overwrite defaults).
    assert "HKCU" in script
    assert "HKLM" not in script
    # The script parses as plain ASCII text (catches stray bad characters).
    script.encode("ascii")


def test_build_windows_distribution_can_bundle_external_tools(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "3.0.0"
""".strip(),
        encoding="utf-8",
    )
    fake_pandoc_dir = tmp_path / "pandoc"
    fake_pandoc_dir.mkdir()
    (fake_pandoc_dir / "pandoc.exe").write_text("binary", encoding="utf-8")

    bundle = build_windows_distribution(
        pyproject,
        tmp_path / "dist",
        bundled_tool_dirs={"pandoc": fake_pandoc_dir},
    )

    manifest = json.loads(
        (tmp_path / "dist" / "portable" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["bundledTools"] == ["pandoc"]
    assert (tmp_path / "dist" / "portable" / "tools" / "pandoc" / "pandoc.exe").exists()
    assert bundle["portable_dir"] == str(tmp_path / "dist" / "portable")


def test_find_inno_setup_compiler_checks_common_locations(monkeypatch, tmp_path: Path) -> None:
    compiler = tmp_path / "ISCC.exe"
    compiler.write_text("binary", encoding="utf-8")
    monkeypatch.setattr("scripts.build_windows_distribution.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "scripts.build_windows_distribution.Path.exists",
        lambda self: self == compiler,
    )
    monkeypatch.setattr(
        "scripts.build_windows_distribution.Path",
        lambda value: compiler if "Inno Setup" in str(value) else Path(value),
    )

    discovered = find_inno_setup_compiler()

    assert discovered == compiler


def test_compile_inno_setup_installer_runs_compiler(monkeypatch, tmp_path: Path) -> None:
    installer_script = tmp_path / "quill.iss"
    installer_script.write_text("script", encoding="utf-8")
    compiler = tmp_path / "ISCC.exe"
    compiler.write_text("binary", encoding="utf-8")
    installer_exe = tmp_path / "Quill-Setup-0.1.exe"

    def fake_run(command: list[str], check: bool) -> None:
        assert check is True
        assert command == [str(compiler), str(installer_script)]
        installer_exe.write_text("exe", encoding="utf-8")

    monkeypatch.setattr("scripts.build_windows_distribution.subprocess.run", fake_run)

    built = compile_inno_setup_installer(
        installer_script,
        version="0.1",
        iscc_path=compiler,
    )

    assert built == installer_exe


def test_compile_inno_setup_installer_accepts_inno_output_folder(
    monkeypatch,
    tmp_path: Path,
) -> None:
    installer_script = tmp_path / "quill.iss"
    installer_script.write_text("script", encoding="utf-8")
    compiler = tmp_path / "ISCC.exe"
    compiler.write_text("binary", encoding="utf-8")
    output_dir = tmp_path / "Output"
    output_dir.mkdir()
    installer_exe = output_dir / "Quill-Setup-0.1.exe"

    def fake_run(command: list[str], check: bool) -> None:
        assert check is True
        assert command == [str(compiler), str(installer_script)]
        installer_exe.write_text("exe", encoding="utf-8")

    monkeypatch.setattr("scripts.build_windows_distribution.subprocess.run", fake_run)

    built = compile_inno_setup_installer(
        installer_script,
        version="0.1",
        iscc_path=compiler,
    )

    assert built == installer_exe


def test_bundled_runtime_dependencies_uses_runtime_groups(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "quill"
version = "0.1"
dependencies = ["alpha>=1.0"]

[project.optional-dependencies]
ui = ["wxPython>=4.2.2", "pyttsx3>=2.99"]
spellcheck = ["pyenchant>=3.2"]
dev = ["pytest>=8.2"]
""".strip(),
        encoding="utf-8",
    )

    dependencies = bundled_runtime_dependencies(pyproject)

    assert dependencies == ["alpha>=1.0", "wxPython>=4.2.2", "pyttsx3>=2.99", "pyenchant>=3.2"]
