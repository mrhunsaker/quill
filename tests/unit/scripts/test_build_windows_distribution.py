from __future__ import annotations

import json
import re
from pathlib import Path

from quill.core.shell_verbs import default_shell_verbs
from scripts.build_windows_distribution import (
    build_inno_setup_script,
    build_shell_verb_registry_lines,
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
    assert manifest["speechAssets"]["espeak"]["downloadable"] is True
    assert manifest["speechAssets"]["kokoro"]["downloadable"] is True
    assert manifest["speechAssets"]["piper"]["downloadable"] is True
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
    # The amd64 embedded-Python bundle must install 64-bit only, target
    # Windows 10+, and refresh Explorer associations for the assoc tasks.
    assert "ArchitecturesAllowed=x64compatible" in script
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in script
    assert "MinVersion=10.0" in script
    assert "ChangesAssociations=yes" in script
    # The dead "aiassistant" component (no [Files] payload) was removed; the
    # Writing Assistant ships with the core bundle, not as a toggle.
    assert "aiassistant" not in script
    assert (
        'Name: "pandoc"; Description: "Install bundled Pandoc for document conversion";' in script
    )
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
    assert 'Name: "speechespeak"; Description: "Install bundled eSpeak-NG runtime";' in script
    assert 'Name: "speechkokoro"; Description: "Install bundled Kokoro voices/models";' in script
    assert 'Name: "speechpiper"; Description: "Install bundled Piper voices/models";' in script
    assert (
        'Name: "speechopenvoice"; Description: "Install bundled OpenVoice voices/models";' in script
    )
    assert (
        'Excludes: "docs\\QUILL-PRD.md,tools\\pandoc\\*,tools\\speech\\dectalk\\*,tools\\speech\\espeak-ng\\*,tools\\speech\\kokoro\\*,tools\\speech\\piper\\*,tools\\speech\\openvoice\\*,tools\\nodejs\\*,vendor\\braille-pack\\*"'
        in script
    )
    assert 'Source: "..\\portable\\tools\\pandoc\\*"; DestDir: "{app}\\tools\\pandoc";' in script
    assert "Components: pandoc" in script
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\*"; DestDir: "{app}\\tools\\speech\\dectalk";'
        in script
    )
    assert 'Excludes: "voices\\*"; Components: speechdectalk' in script
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices";'
        in script
    )
    assert "Components: speechdectalk\\voices\\all_voices" in script
    assert "Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')" in script
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\paul\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\paul";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\harry\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\harry";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\dennis\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\dennis";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\frank\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\frank";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\betty\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\betty";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\ursula\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\ursula";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\rita\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\rita";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\wendy\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\wendy";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\kit\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\kit";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\espeak-ng\\*"; DestDir: "{app}\\tools\\speech\\espeak-ng";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\kokoro\\*"; DestDir: "{app}\\tools\\speech\\kokoro";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\piper\\*"; DestDir: "{app}\\tools\\speech\\piper";'
        in script
    )
    assert (
        'Source: "..\\portable\\tools\\speech\\openvoice\\*"; DestDir: "{app}\\tools\\speech\\openvoice";'
        in script
    )
    assert "Components: speechdectalk" in script
    assert "Components: speechespeak" in script
    assert "Components: speechkokoro" in script
    assert "Components: speechpiper" in script
    assert "Components: speechopenvoice" in script
    assert "User Guide" in script
    assert "userguide.html" in script
    assert "python\\pythonw.exe" in script
    assert 'Parameters: "-m quill"' in script
    assert "Check: FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))" in script
    assert "Check: not FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))" in script
    assert "Beta Announcement" not in script
    assert "Product Requirements" not in script
    # File-association registry entries use HKCU only (never overwrite defaults).
    assert "HKCU" in script
    assert "HKLM" not in script
    # The script parses as plain ASCII text (catches stray bad characters).
    script.encode("ascii")


def test_shell_verb_registry_lines_cover_every_verb_and_extension() -> None:
    # SHELL-3: the installer's right-click verbs are generated straight from
    # the single core registry, so the menu can never drift from the CLI.
    lines = build_shell_verb_registry_lines()
    text = "\n".join(lines)
    for verb in default_shell_verbs():
        key = f"shell\\Quill.{verb.verb_id}"
        # Each verb appears with its label and its --action launch command.
        assert f'ValueData: "{verb.label}"' in text
        assert f"--action {verb.action} " in text
        for extension in verb.extensions:
            base = f"Software\\Classes\\SystemFileAssociations\\{extension}\\{key}"
            assert f'Subkey: "{base}"' in text
            assert f'Subkey: "{base}\\command"' in text


def test_shell_verb_registry_lines_are_optin_and_uninstall_clean() -> None:
    # Every verb key is gated behind the opt-in shellverbs task and tagged
    # uninsdeletekey so a full uninstall removes the context-menu entries.
    lines = build_shell_verb_registry_lines()
    assert lines, "expected at least one generated verb registry line"
    assert all("Tasks: shellverbs" in line for line in lines)
    # The verb root keys (not the MUIVerb/command values) carry uninsdeletekey.
    root_key_lines = [line for line in lines if 'ValueName: ""' in line and "\\command" not in line]
    assert root_key_lines
    assert all("Flags: uninsdeletekey" in line for line in root_key_lines)


def test_shell_verb_command_launches_run_quill_cmd_with_action() -> None:
    # The launch command routes through run-quill.cmd (AppExeName), which
    # forwards %* to `python -m quill`, passing the file as %1.
    lines = build_shell_verb_registry_lines()
    command_lines = [line for line in lines if "\\command" in line]
    assert command_lines
    for line in command_lines:
        assert 'ValueData: """{app}\\{#AppExeName}"" --action ' in line
        assert '""%1"""' in line


def test_inno_setup_script_includes_shell_verb_task_and_registry() -> None:
    # SHELL-3 is wired end-to-end into the generated installer script.
    script = build_inno_setup_script("9.9.9")
    assert 'Name: "shellverbs"; Description: "Add ""Send to Quill"" actions' in script
    assert 'Send to Quill" file right-click verbs (SHELL-3)' in script
    # Spot-check one concrete verb/extension pair made it into the [Registry].
    assert 'Subkey: "Software\\Classes\\SystemFileAssociations\\.png\\shell\\Quill.ocr"' in script
    assert "--action ocr " in script


def test_committed_installer_iss_is_in_sync_with_generator() -> None:
    # #114 / SHELL-1: installer/quill.iss carries a "Generated by ...; Edit
    # build_inno_setup_script()" header, so the committed file must be the exact
    # output of the generator for its declared version. This guard fails if the
    # generator changes (e.g. a new shell verb or extension) without the
    # committed installer being regenerated, preventing a silent drift between
    # the shipped Explorer context menu and the single core verb registry.
    repo_root = Path(__file__).resolve().parents[3]
    committed = (repo_root / "installer" / "quill.iss").read_text(encoding="utf-8")

    version_match = re.search(r'#define AppVersion "([^"]+)"', committed)
    assert version_match, "committed installer is missing an AppVersion define"
    version = version_match.group(1)

    generated = build_inno_setup_script(version)
    assert committed.strip() == generated.strip(), (
        "installer/quill.iss is out of sync with build_inno_setup_script(); "
        "regenerate it (the file is generated, not hand-edited)."
    )


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
