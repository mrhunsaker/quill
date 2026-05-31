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
    assert manifest["speechAssets"]["dectalk"]["downloadable"] is True
    assert manifest["speechAssets"]["kokoro"]["downloadable"] is True
    assert manifest["speechAssets"]["piper"]["downloadable"] is True
    assert manifest["speechAssets"]["vibevoice"]["downloadable"] is True
    assert manifest["speechAssets"]["rhvoice"]["downloadable"] is True
    assert manifest["speechAssets"]["melotts"]["downloadable"] is True
    assert manifest["speechAssets"]["chatterbox"]["downloadable"] is True
    assert manifest["speechAssets"]["openvoice"]["downloadable"] is True

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
    assert 'Name: "pandoc"; Description: "Install bundled Pandoc for document conversion";' in script
    assert 'Name: "speechdectalk"; Description: "Install bundled DECtalk runtime";' in script
    assert 'Name: "speechdectalk\\voices"; Description: "DECtalk voice selection";' in script
    assert 'Name: "speechdectalk\\voices\\all_voices"; Description: "All DECtalk voices";' in script
    assert 'Name: "speechdectalk\\voices\\paul"; Description: "Paul voice";' in script
    assert 'Name: "speechdectalk\\voices\\harry"; Description: "Harry voice";' in script
    assert 'Name: "speechdectalk\\voices\\dennis"; Description: "Dennis voice";' in script
    assert 'Name: "speechdectalk\\voices\\frank"; Description: "Frank voice";' in script
    assert 'Name: "speechdectalk\\voices\\betty"; Description: "Betty voice";' in script
    assert 'Name: "speechdectalk\\voices\\ursula"; Description: "Ursula voice";' in script
    assert 'Name: "speechdectalk\\voices\\rita"; Description: "Rita voice";' in script
    assert 'Name: "speechdectalk\\voices\\wendy"; Description: "Wendy voice";' in script
    assert 'Name: "speechdectalk\\voices\\kit"; Description: "Kit voice";' in script
    assert 'Name: "speechkokoro"; Description: "Install bundled Kokoro voices/models";' in script
    assert 'Name: "speechpiper"; Description: "Install bundled Piper voices/models";' in script
    assert 'Name: "speechvibevoice"; Description: "Install bundled VibeVoice voices/models";' in script
    assert 'Name: "speechrhvoice"; Description: "Install bundled RHVoice voices/models";' in script
    assert 'Name: "speechmelotts"; Description: "Install bundled MeloTTS voices/models";' in script
    assert 'Name: "speechchatterbox"; Description: "Install bundled Chatterbox voices/models";' in script
    assert 'Name: "speechopenvoice"; Description: "Install bundled OpenVoice voices/models";' in script
    assert (
        'Excludes: "docs\\announcement-beta.md,docs\\QUILL-PRD.md,tools\\pandoc\\*,tools\\speech\\dectalk\\*,tools\\speech\\kokoro\\*,tools\\speech\\piper\\*,tools\\speech\\vibevoice\\*,tools\\speech\\rhvoice\\*,tools\\speech\\melotts\\*,tools\\speech\\chatterbox\\*,tools\\speech\\openvoice\\*"'
        in script
    )
    assert 'Source: "..\\portable\\tools\\pandoc\\*"; DestDir: "{app}\\tools\\pandoc";' in script
    assert 'Components: pandoc' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\*"; DestDir: "{app}\\tools\\speech\\dectalk";' in script
    assert 'Excludes: "voices\\*"; Components: speechdectalk' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices";' in script
    assert 'Components: speechdectalk\\voices\\all_voices' in script
    assert "Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')" in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\paul\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\paul";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\harry\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\harry";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\dennis\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\dennis";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\frank\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\frank";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\betty\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\betty";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\ursula\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\ursula";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\rita\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\rita";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\wendy\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\wendy";' in script
    assert 'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\kit\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\kit";' in script
    assert 'Source: "..\\portable\\tools\\speech\\kokoro\\*"; DestDir: "{app}\\tools\\speech\\kokoro";' in script
    assert 'Source: "..\\portable\\tools\\speech\\piper\\*"; DestDir: "{app}\\tools\\speech\\piper";' in script
    assert 'Source: "..\\portable\\tools\\speech\\vibevoice\\*"; DestDir: "{app}\\tools\\speech\\vibevoice";' in script
    assert 'Source: "..\\portable\\tools\\speech\\rhvoice\\*"; DestDir: "{app}\\tools\\speech\\rhvoice";' in script
    assert 'Source: "..\\portable\\tools\\speech\\melotts\\*"; DestDir: "{app}\\tools\\speech\\melotts";' in script
    assert 'Source: "..\\portable\\tools\\speech\\chatterbox\\*"; DestDir: "{app}\\tools\\speech\\chatterbox";' in script
    assert 'Source: "..\\portable\\tools\\speech\\openvoice\\*"; DestDir: "{app}\\tools\\speech\\openvoice";' in script
    assert 'Components: speechdectalk' in script
    assert 'Components: speechkokoro' in script
    assert 'Components: speechpiper' in script
    assert 'Components: speechvibevoice' in script
    assert 'Components: speechrhvoice' in script
    assert 'Components: speechmelotts' in script
    assert 'Components: speechchatterbox' in script
    assert 'Components: speechopenvoice' in script
    assert "Writing Assistant Setup" in script
    assert "User Guide" in script
    assert "python\\pythonw.exe" in script
    assert "Parameters: \"-m quill\"" in script
    assert "Check: FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))" in script
    assert "Check: not FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))" in script
    assert "Beta Announcement" not in script
    assert "Product Requirements" not in script
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
    assert manifest["speechAssets"]["dectalk"]["bundled"] is False
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
