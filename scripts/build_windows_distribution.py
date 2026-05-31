"""Build a Windows distribution of Quill.

Outputs under ``windows-distribution/``:

* ``portable/`` — the runnable bundle (launcher, manifest, README, the
  Quill package source, and optionally an embedded Python runtime with
  all required wheels pre-installed).
* ``installer/quill.iss`` — an Inno Setup script that turns the portable
  bundle into a polished Windows installer (per-user by default, Start
  Menu shortcut, optional Desktop shortcut, optional Open-With entries,
  proper Add/Remove Programs metadata).

The ``--bundle-python`` flag downloads the official Windows embeddable
Python distribution and pre-installs ``wxPython`` and ``pyttsx3`` into
it, so end users do **not** need to install Python or pip themselves.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import textwrap
import tomllib
import urllib.request
import zipfile
from pathlib import Path

from quill.core.storage import write_json_atomic

# Pinned Windows embeddable Python. Bumping these values is the only
# thing needed to ship on a new Python point release.
EMBEDDED_PYTHON_VERSION = "3.12.6"
EMBEDDED_PYTHON_URL = (
    f"https://www.python.org/ftp/python/{EMBEDDED_PYTHON_VERSION}/"
    f"python-{EMBEDDED_PYTHON_VERSION}-embed-amd64.zip"
)
# SHA-256 of the official embeddable zip. If python.org rotates the file
# the build will fail loudly rather than ship an unverified runtime.
EMBEDDED_PYTHON_SHA256 = "a86a2e28870967745d255cc597d1e4d19ae79e65e927cdc324baa0256202231c"

DECTALK_RELEASE_ZIP_URL = (
    "https://github.com/dectalk/dectalk/releases/download/2023-10-30/vs2022.zip"
)

DEFAULT_BUNDLED_DEPENDENCY_GROUPS = ("ui", "spellcheck")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate portable and Inno Setup packaging artefacts for Windows.",
    )
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--output-dir", type=Path, default=Path("windows-distribution"))
    parser.add_argument(
        "--bundle-python",
        action="store_true",
        help=(
            "Download an embedded Python runtime and install wxPython/pyttsx3 "
            "into the portable bundle so end users do not need Python."
        ),
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("."),
        help="Repository root that contains the quill/ package source to ship.",
    )
    parser.add_argument(
        "--pandoc-dir",
        type=Path,
        default=None,
        help="Optional local Pandoc directory to bundle under portable\\tools\\pandoc.",
    )
    parser.add_argument(
        "--tesseract-dir",
        type=Path,
        default=None,
        help="Optional local Tesseract directory to bundle under portable\\tools\\tesseract.",
    )
    parser.add_argument(
        "--dectalk-dir",
        type=Path,
        default=None,
        help="Optional local DECtalk runtime directory to bundle under portable\\tools\\speech\\dectalk.",
    )
    parser.add_argument(
        "--kokoro-dir",
        type=Path,
        default=None,
        help="Optional local Kokoro voices/models directory to bundle under portable\\tools\\speech\\kokoro.",
    )
    parser.add_argument(
        "--piper-dir",
        type=Path,
        default=None,
        help="Optional local Piper voices/models directory to bundle under portable\\tools\\speech\\piper.",
    )
    parser.add_argument(
        "--rhvoice-dir",
        type=Path,
        default=None,
        help="Optional local RHVoice voices/models directory to bundle under portable\\tools\\speech\\rhvoice.",
    )
    parser.add_argument(
        "--melotts-dir",
        type=Path,
        default=None,
        help="Optional local MeloTTS voices/models directory to bundle under portable\\tools\\speech\\melotts.",
    )
    parser.add_argument(
        "--chatterbox-dir",
        type=Path,
        default=None,
        help="Optional local Chatterbox voices/models directory to bundle under portable\\tools\\speech\\chatterbox.",
    )
    parser.add_argument(
        "--openvoice-dir",
        type=Path,
        default=None,
        help="Optional local OpenVoice voices/models directory to bundle under portable\\tools\\speech\\openvoice.",
    )
    parser.add_argument(
        "--bundle-dectalk-release",
        action="store_true",
        help="Download the official dectalk/dectalk vs2022 release and bundle it under portable\\tools\\speech\\dectalk.",
    )
    parser.add_argument(
        "--compile-installer",
        action="store_true",
        help="Compile the generated Inno Setup script into an installer executable.",
    )
    parser.add_argument(
        "--iscc-path",
        type=Path,
        default=None,
        help="Optional explicit path to ISCC.exe for installer compilation.",
    )
    args = parser.parse_args()

    bundle = build_windows_distribution(
        args.pyproject,
        args.output_dir,
        bundle_python=args.bundle_python,
        source_root=args.source_root,
        bundle_dectalk_release=args.bundle_dectalk_release,
        bundled_tool_dirs={
            tool_id: path
            for tool_id, path in {
                "pandoc": args.pandoc_dir,
                "tesseract": args.tesseract_dir,
                "speech/dectalk": args.dectalk_dir,
                "speech/kokoro": args.kokoro_dir,
                "speech/piper": args.piper_dir,
                "speech/rhvoice": args.rhvoice_dir,
                "speech/melotts": args.melotts_dir,
                "speech/chatterbox": args.chatterbox_dir,
                "speech/openvoice": args.openvoice_dir,
            }.items()
            if path is not None
        },
        compile_installer=args.compile_installer,
        iscc_path=args.iscc_path,
    )
    print(f"Wrote portable bundle to {bundle['portable_dir']}")
    print(f"Wrote installer template to {bundle['installer_script']}")
    if bundle.get("python_runtime"):
        print(f"Bundled embedded Python to {bundle['python_runtime']}")
    if bundle.get("installer_exe"):
        print(f"Built installer executable at {bundle['installer_exe']}")
    return 0


def build_windows_distribution(
    pyproject: Path,
    output_dir: Path,
    bundle_python: bool = False,
    source_root: Path | None = None,
    bundled_tool_dirs: dict[str, Path] | None = None,
    bundle_dectalk_release: bool = False,
    compile_installer: bool = False,
    iscc_path: Path | None = None,
) -> dict[str, str]:
    version = _project_version(pyproject)
    resolved_source_root = source_root or Path(".")
    portable_dir = output_dir / "portable"
    installer_dir = output_dir / "installer"
    reference_installer_dir = pyproject.parent / "installer"
    portable_dir.mkdir(parents=True, exist_ok=True)
    installer_dir.mkdir(parents=True, exist_ok=True)
    reference_installer_dir.mkdir(parents=True, exist_ok=True)

    launcher = portable_dir / "run-quill.cmd"
    launcher.write_text(_render_launcher_script(), encoding="utf-8")

    staged_docs = _stage_distribution_docs(portable_dir, resolved_source_root)
    effective_bundled_tools = dict(bundled_tool_dirs or {})
    if bundle_dectalk_release and "speech/dectalk" not in effective_bundled_tools:
        downloaded_dectalk_dir = _download_and_stage_dectalk_release(portable_dir)
        effective_bundled_tools["speech/dectalk"] = downloaded_dectalk_dir
    bundled_tools = _stage_bundled_tools(portable_dir, effective_bundled_tools)

    readme = portable_dir / "README.txt"
    readme.write_text(
        _render_readme(
            version,
            bundle_python,
            bundled_tools=bundled_tools,
            staged_docs=staged_docs,
        ),
        encoding="utf-8",
    )

    manifest_path = portable_dir / "manifest.json"
    manifest = {
        "project": "quill",
        "version": version,
        "publisher": "Blind Information Technology Solutions (BITS) and Community Access",
        "portableLauncher": str(launcher),
        "installerScript": str(installer_dir / "quill.iss"),
        "bundledPython": bool(bundle_python),
        "embeddedPythonVersion": EMBEDDED_PYTHON_VERSION if bundle_python else None,
        "bundledTools": bundled_tools,
        "docs": [str(path.relative_to(portable_dir)) for path in staged_docs],
        "speechAssets": _speech_asset_manifest(portable_dir, bundled_tools),
    }
    write_json_atomic(manifest_path, manifest)

    installer_script = installer_dir / "quill.iss"
    reference_installer_script = reference_installer_dir / "quill.iss"
    installer_script_text = build_inno_setup_script(version=version)
    installer_script.write_text(installer_script_text, encoding="utf-8")
    reference_installer_script.write_text(installer_script_text, encoding="utf-8")

    python_runtime_dir: Path | None = None
    if bundle_python:
        python_runtime_dir = bundle_embedded_python(
            portable_dir / "python",
            source_root=resolved_source_root,
            pyproject=pyproject,
        )

    result = {
        "portable_dir": str(portable_dir),
        "installer_script": str(installer_script),
        "reference_installer_script": str(reference_installer_script),
    }
    if python_runtime_dir is not None:
        result["python_runtime"] = str(python_runtime_dir)
    if compile_installer:
        installer_exe = compile_inno_setup_installer(
            installer_script,
            version=version,
            iscc_path=iscc_path,
        )
        result["installer_exe"] = str(installer_exe)
    return result


def _render_launcher_script() -> str:
    """Return the contents of ``run-quill.cmd``.

    The launcher prefers a Python interpreter shipped alongside it
    (``python\\pythonw.exe`` for normal windowed launch and
    ``python\\python.exe`` with ``--console``) so the
    typical end user never has to install Python. If no bundled
    interpreter is present we fall back to one on ``PATH`` and, failing
    that, print a clear screen-reader-friendly error.
    """

    return (
        "@echo off\r\n"
        "setlocal\r\n"
        "set QUILL_PORTABLE=1\r\n"
        "set QUILL_APP_ROOT=%~dp0\r\n"
        "set QUILL_PORTABLE_ROOT=%~dp0data\r\n"
        "set QUILL_CONSOLE_MODE=0\r\n"
        'if /I "%~1"=="--console" (\r\n'
        "    set QUILL_CONSOLE_MODE=1\r\n"
        "    shift\r\n"
        ")\r\n"
        'if /I "%~1"=="--no-console" (\r\n'
        "    set QUILL_CONSOLE_MODE=0\r\n"
        "    shift\r\n"
        ")\r\n"
        ":: Prefer the bundled embedded Python that ships with the installer.\r\n"
        'set "QUILL_BUNDLED_PYTHON=%~dp0python\\python.exe"\r\n'
        'set "QUILL_BUNDLED_PYTHONW=%~dp0python\\pythonw.exe"\r\n'
        'if "%QUILL_CONSOLE_MODE%"=="0" (\r\n'
        '    if exist "%QUILL_BUNDLED_PYTHONW%" (\r\n'
        '        start "" "%QUILL_BUNDLED_PYTHONW%" -m quill %*\r\n'
        "        exit /b 0\r\n"
        "    )\r\n"
        "    where pythonw >nul 2>nul\r\n"
        "    if errorlevel 1 goto :run_console\r\n"
        '    start "" pythonw -m quill %*\r\n'
        "    exit /b 0\r\n"
        ")\r\n"
        ":run_console\r\n"
        'if exist "%QUILL_BUNDLED_PYTHON%" (\r\n'
        '    "%QUILL_BUNDLED_PYTHON%" -m quill %*\r\n'
        "    goto :after_run\r\n"
        ")\r\n"
        ":: Fallback: a system-wide Python on PATH (developer / dev-build mode).\r\n"
        "where python >nul 2>nul\r\n"
        "if errorlevel 1 (\r\n"
        "    echo.\r\n"
        "    echo Quill could not find its bundled Python runtime, and no Python\r\n"
        "    echo interpreter is available on PATH.\r\n"
        "    echo.\r\n"
        "    echo If you installed Quill from the official installer, please\r\n"
        "    echo reinstall: this build is missing the bundled runtime.\r\n"
        "    echo.\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n"
        "python -m quill %*\r\n"
        ":after_run\r\n"
        "if errorlevel 1 (\r\n"
        "    echo.\r\n"
        "    echo Quill exited with an error. See the messages above.\r\n"
        "    pause\r\n"
        ")\r\n"
    )


def _render_readme(
    version: str,
    bundle_python: bool,
    *,
    bundled_tools: list[str],
    staged_docs: list[Path],
) -> str:
    if bundle_python:
        runtime_paragraph = (
            "This bundle ships a private Python runtime in the python\\ folder,\n"
            "so you do NOT need to install Python, pip, wxPython, or anything\n"
            "else. Just run run-quill.cmd and start writing."
        )
    else:
        runtime_paragraph = (
            "This bundle does not include a Python runtime. To run it,\n"
            "install Python 3.12+ from https://www.python.org/downloads/windows/\n"
            "and run:  pip install wxPython pyttsx3\n"
            "Then double-click run-quill.cmd."
        )

    docs_paragraph = ""
    if staged_docs:
        docs_paragraph = (
            "\nIncluded guides:\n"
            "- docs\\userguide.md - the full guided user manual\n"
            "Internal engineering docs are published on the Quill GitHub Pages site\n"
            "instead of being bundled in the installer.\n"
        )
    bundled_tools_paragraph = ""
    if bundled_tools:
        bundled_tools_paragraph = (
            "\nBundled external tools:\n"
            + "\n".join(f"- {tool_id}" for tool_id in bundled_tools)
            + (
                "\nQuill can also detect additional tools installed system-wide "
                "and guide users through what they unlock.\n"
            )
        )

    return (
        textwrap.dedent(
            f"""
            Quill Portable {version}
            Publisher: Blind Information Technology Solutions (BITS) and Community Access

            {runtime_paragraph}

            Quill is a screen-reader-first writing, reading, review, and document-intelligence
            environment for Windows. It is designed to stay calm on the keyboard while still
            giving power users deep navigation, structured editing, comparison, GLOW review,
            diagnostics, and optional external-tool workflows.

            Optional tool onboarding is built into Quill itself. If Pandoc, Tesseract OCR,
            or other supported tools are installed or bundled, Quill explains what they unlock
            and offers guided touch points such as the Pandoc Conversion Wizard.

            {bundled_tools_paragraph}{docs_paragraph}

            On first run, Quill asks whether to store its data in your
            Windows AppData folder (default) or alongside this bundle
            (portable mode). Choose portable if you are running Quill from
            a USB stick or a managed work laptop where AppData is volatile.

            To rebuild the installer from this portable bundle, open
            installer\\quill.iss in Inno Setup 6.
            """
        ).strip()
        + "\r\n"
    )


def build_inno_setup_script(version: str) -> str:
    """Return a production-quality Inno Setup script for the portable bundle.

    The script is assembled line-by-line to avoid the f-string + triple-
    quote pitfalls of templating Inno (which uses ``""`` as its own
    quote-escape) inside a Python triple-quoted string.
    """

    lines: list[str] = [
        "; Generated by scripts/build_windows_distribution.py",
        "; Edit build_inno_setup_script(), not this file, to change packaging.",
        "",
        '#define AppName "Quill"',
        f'#define AppVersion "{version}"',
        '#define AppPublisher "Blind Information Technology Solutions (BITS) and Community Access"',
        '#define AppURL "https://github.com/Community-Access/quill"',
        '#define AppExeName "run-quill.cmd"',
        "",
        "[Setup]",
        "AppId={{6E0A1C52-4A90-4C6E-A8A1-3C2A16E2B7F2}",
        "AppName={#AppName}",
        "AppVersion={#AppVersion}",
        "AppPublisher={#AppPublisher}",
        "AppPublisherURL={#AppURL}",
        "AppSupportURL={#AppURL}",
        "AppUpdatesURL={#AppURL}",
        "VersionInfoVersion={#AppVersion}",
        "VersionInfoCompany={#AppPublisher}",
        "VersionInfoDescription={#AppName} accessible writing environment",
        "DefaultDirName={autopf}\\{#AppName}",
        "DefaultGroupName={#AppName}",
        "DisableDirPage=no",
        "DisableProgramGroupPage=auto",
        "AllowNoIcons=yes",
        "PrivilegesRequired=lowest",
        "PrivilegesRequiredOverridesAllowed=dialog",
        f"OutputBaseFilename=Quill-Setup-{version}",
        "Compression=lzma2/ultra",
        "SolidCompression=yes",
        "WizardStyle=modern",
        "; Accessibility: do not auto-close the wizard, so screen-reader users",
        "; have time to hear the final status message.",
        "CloseApplications=force",
        "RestartApplications=no",
        "UninstallDisplayName={#AppName} {#AppVersion}",
        "UninstallDisplayIcon={app}\\{#AppExeName}",
        "LicenseFile=..\\..\\LICENSE",
        "InfoAfterFile=..\\portable\\README.txt",
        "SetupLogging=yes",
        "",
        "[Languages]",
        'Name: "english"; MessagesFile: "compiler:Default.isl"',
        "",
        "[Tasks]",
        'Name: "desktopicon"; Description: "Create a &Desktop shortcut";'
        ' GroupDescription: "Additional shortcuts:"; Flags: unchecked',
        'Name: "fileassoc"; Description: "Register Quill in the Open With menu'
        ' for common text formats (.txt, .md, .rst, .log, .csv, .json)";'
        ' GroupDescription: "File associations:"; Flags: unchecked',
        "",
        "[Components]",
        'Name: "aiassistant"; Description: "Install the Writing Assistant setup guide and AI connection shortcut";'
        " Types: full compact custom; Flags: checkablealone",
        'Name: "pandoc"; Description: "Install bundled Pandoc for document conversion";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechdectalk"; Description: "Install bundled DECtalk runtime";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechdectalk\\voices"; Description: "DECtalk voice selection";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechdectalk\\voices\\all_voices"; Description: "All DECtalk voices";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechdectalk\\voices\\paul"; Description: "Paul voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\harry"; Description: "Harry voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\dennis"; Description: "Dennis voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\frank"; Description: "Frank voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\betty"; Description: "Betty voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\ursula"; Description: "Ursula voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\rita"; Description: "Rita voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\wendy"; Description: "Wendy voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechdectalk\\voices\\kit"; Description: "Kit voice"; Types: full custom; Flags: checkablealone',
        'Name: "speechkokoro"; Description: "Install bundled Kokoro voices/models";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechpiper"; Description: "Install bundled Piper voices/models";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechrhvoice"; Description: "Install bundled RHVoice voices/models";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechmelotts"; Description: "Install bundled MeloTTS voices/models";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechchatterbox"; Description: "Install bundled Chatterbox voices/models";'
        " Types: full custom; Flags: checkablealone",
        'Name: "speechopenvoice"; Description: "Install bundled OpenVoice voices/models";'
        " Types: full custom; Flags: checkablealone",
        "",
        "[Files]",
        'Source: "..\\portable\\*"; DestDir: "{app}";'
        " Flags: ignoreversion recursesubdirs createallsubdirs;"
        ' Excludes: "docs\\announcement-beta.md,docs\\QUILL-PRD.md,tools\\pandoc\\*,tools\\speech\\dectalk\\*,tools\\speech\\kokoro\\*,tools\\speech\\piper\\*,tools\\speech\\rhvoice\\*,tools\\speech\\melotts\\*,tools\\speech\\chatterbox\\*,tools\\speech\\openvoice\\*"',
        'Source: "..\\portable\\tools\\pandoc\\*"; DestDir: "{app}\\tools\\pandoc";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: pandoc",
        'Source: "..\\portable\\tools\\speech\\dectalk\\*"; DestDir: "{app}\\tools\\speech\\dectalk";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        ' Excludes: "voices\\*"; Components: speechdectalk',
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\all_voices",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\paul\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\paul";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\paul; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\harry\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\harry";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\harry; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\dennis\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\dennis";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\dennis; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\frank\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\frank";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\frank; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\betty\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\betty";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\betty; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\ursula\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\ursula";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\ursula; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\rita\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\rita";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\rita; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\wendy\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\wendy";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\wendy; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\dectalk\\voices\\kit\\*"; DestDir: "{app}\\tools\\speech\\dectalk\\voices\\kit";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: speechdectalk\\voices\\kit; Check: not WizardIsComponentSelected('speechdectalk\\voices\\all_voices')",
        'Source: "..\\portable\\tools\\speech\\kokoro\\*"; DestDir: "{app}\\tools\\speech\\kokoro";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechkokoro",
        'Source: "..\\portable\\tools\\speech\\piper\\*"; DestDir: "{app}\\tools\\speech\\piper";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechpiper",
        'Source: "..\\portable\\tools\\speech\\rhvoice\\*"; DestDir: "{app}\\tools\\speech\\rhvoice";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechrhvoice",
        'Source: "..\\portable\\tools\\speech\\melotts\\*"; DestDir: "{app}\\tools\\speech\\melotts";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechmelotts",
        'Source: "..\\portable\\tools\\speech\\chatterbox\\*"; DestDir: "{app}\\tools\\speech\\chatterbox";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechchatterbox",
        'Source: "..\\portable\\tools\\speech\\openvoice\\*"; DestDir: "{app}\\tools\\speech\\openvoice";'
        " Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist;"
        " Components: speechopenvoice",
        "",
        "[Icons]",
        'Name: "{group}\\{#AppName}"; Filename: "{app}\\python\\pythonw.exe"; Parameters: "-m quill"; WorkingDir: "{app}"; Check: FileExists(ExpandConstant(\'{app}\\python\\pythonw.exe\'))',
        'Name: "{group}\\{#AppName}"; Filename: "{app}\\{#AppExeName}"; WorkingDir: "{app}"; Check: not FileExists(ExpandConstant(\'{app}\\python\\pythonw.exe\'))',
        'Name: "{group}\\{#AppName} README"; Filename: "{app}\\README.txt"',
        ('Name: "{group}\\{#AppName} User Guide"; Filename: "{app}\\docs\\userguide.md"'),
        (
            'Name: "{group}\\Writing Assistant Setup"; '
            'Filename: "{app}\\docs\\userguide.md"; Components: aiassistant'
        ),
        'Name: "{group}\\Uninstall {#AppName}"; Filename: "{uninstallexe}"',
        'Name: "{autodesktop}\\{#AppName}"; Filename: "{app}\\python\\pythonw.exe"; Parameters: "-m quill";'
        " WorkingDir: \"{app}\"; Tasks: desktopicon; Check: FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))",
        'Name: "{autodesktop}\\{#AppName}"; Filename: "{app}\\{#AppExeName}";'
        " WorkingDir: \"{app}\"; Tasks: desktopicon; Check: not FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))",
        "",
        "[Registry]",
        "; Register Quill in the OpenWithList for common text formats. We",
        "; never overwrite the user's chosen default app for any extension.",
        # Inno uses "" as an escaped quote inside a string; we feed it via
        # Python str.format-style concatenation to keep the file readable.
        (
            "Root: HKCU;"
            ' Subkey: "Software\\Classes\\Applications\\{#AppExeName}\\shell\\open\\command";'
            ' ValueType: string; ValueName: "";'
            ' ValueData: """{app}\\{#AppExeName}"" ""%1""";'
            " Flags: uninsdeletekey; Tasks: fileassoc"
        ),
    ]
    for extension in (".txt", ".md", ".rst", ".log", ".csv", ".json"):
        lines.append(
            f'Root: HKCU; Subkey: "Software\\Classes\\{extension}\\OpenWithList\\{{#AppExeName}}";'
            " Flags: uninsdeletekey; Tasks: fileassoc"
        )
    lines += [
        "",
        "[Run]",
        'Filename: "{app}\\README.txt"; Description: "View the Quill README";'
        " Flags: postinstall shellexec skipifsilent unchecked",
        'Filename: "{app}\\docs\\userguide.md";'
        ' Description: "View the Writing Assistant setup guide";'
        " Flags: postinstall shellexec skipifsilent unchecked; Components: aiassistant",
        'Filename: "{app}\\python\\pythonw.exe"; Parameters: "-m quill"; Description: "Launch {#AppName}";'
        " Flags: postinstall nowait skipifsilent unchecked; Check: FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))",
        'Filename: "{app}\\{#AppExeName}"; Description: "Launch {#AppName}";'
        " Flags: postinstall nowait skipifsilent unchecked; Check: not FileExists(ExpandConstant('{app}\\python\\pythonw.exe'))",
        "",
        "[UninstallDelete]",
        "; Always remove install-dir build junk. Whether to also remove the",
        "; user's data in %APPDATA%\\Quill is decided by an explicit prompt in",
        "; [Code] below -- we never silently keep or wipe it.",
        'Type: filesandordirs; Name: "{app}\\__pycache__"',
        'Type: filesandordirs; Name: "{app}\\python\\__pycache__"',
        "",
        "[Code]",
        "// Ask, on uninstall, whether to also remove personal data instead of",
        "// assuming. 'Yes' wipes %APPDATA%\\Quill (settings, dictionaries,",
        "// autosaves, backups, onboarding/first-run flags, and the IPC lock) so a",
        "// later reinstall is a clean first run. 'No' keeps everything for a",
        "// future reinstall. MsgBox is a native dialog, so it is screen-reader",
        "// accessible.",
        "procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);",
        "var",
        "  DataDir: String;",
        "begin",
        "  if CurUninstallStep = usUninstall then",
        "  begin",
        "    DataDir := ExpandConstant('{userappdata}\\Quill');",
        "    if DirExists(DataDir) then",
        "    begin",
        "      if MsgBox('Also remove your Quill data?' + #13#10 + #13#10 +",
        "                'This deletes your settings, dictionaries, autosaves, backups,'"
        " + #13#10 +",
        "                'and onboarding state in:' + #13#10 + DataDir + #13#10 + #13#10 +",
        "                'Choose No to keep your documents and settings for a future' + #13#10 +",
        "                'reinstall. Choose Yes to remove everything.',",
        "                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then",
        "      begin",
        "        DelTree(DataDir, True, True, True);",
        "      end;",
        "    end;",
        "  end;",
        "end;",
    ]
    return "\n".join(lines) + "\n"


def compile_inno_setup_installer(
    installer_script: Path,
    *,
    version: str,
    iscc_path: Path | None = None,
) -> Path:
    compiler = iscc_path or find_inno_setup_compiler()
    if compiler is None:
        raise RuntimeError(
            "Inno Setup compiler not found. Install Inno Setup 6 or pass --iscc-path."
        )
    subprocess.run([str(compiler), str(installer_script)], check=True)
    expected_name = f"Quill-Setup-{version}.exe"
    for installer_exe in (
        installer_script.parent / expected_name,
        installer_script.parent / "Output" / expected_name,
    ):
        if installer_exe.exists():
            return installer_exe
    raise RuntimeError(
        "Expected installer executable at "
        f"{installer_script.parent / expected_name} or "
        f"{installer_script.parent / 'Output' / expected_name}"
    )


def find_inno_setup_compiler() -> Path | None:
    for candidate_name in ("ISCC.exe", "iscc"):
        discovered = shutil.which(candidate_name)
        if discovered:
            return Path(discovered)
    for candidate in (
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ):
        if candidate.exists():
            return candidate
    return None


def bundle_embedded_python(
    target_dir: Path,
    source_root: Path,
    pyproject: Path,
    download_url: str = EMBEDDED_PYTHON_URL,
    expected_sha256: str | None = EMBEDDED_PYTHON_SHA256,
) -> Path:
    """Download the official Windows embeddable Python and prepare it for use.

    The embeddable distribution is a small (~10 MB) zip that does NOT
    include pip and disables ``sys.path`` discovery of site-packages by
    default. To ship Quill as a single self-contained bundle we:

    1. Download and SHA-256 verify the official zip from python.org.
    2. Extract it to ``target_dir``.
    3. Patch the ``python<ver>._pth`` file so ``site`` is enabled
       (otherwise ``pip``-installed wheels are invisible).
    4. Bootstrap pip via the official ``get-pip.py``.
    5. ``pip install`` the runtime dependencies (wxPython, pyttsx3).
    6. Drop the Quill package source into the runtime so
       ``python -m quill`` resolves without a wheel build step.

    Returns the path to the prepared runtime directory.
    """

    target_dir = target_dir.resolve()
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    archive = target_dir.parent / f"python-{EMBEDDED_PYTHON_VERSION}-embed-amd64.zip"
    print(f"Downloading {download_url}...")
    _download_with_verification(download_url, archive, expected_sha256)

    print(f"Extracting embedded Python to {target_dir}...")
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target_dir)

    # Enable site-packages discovery in the embedded distribution.
    pth_files = list(target_dir.glob("python*._pth"))
    if not pth_files:
        raise RuntimeError("Embedded Python zip did not contain a ._pth file")
    pth = pth_files[0]
    pth_text = pth.read_text(encoding="utf-8")
    if "#import site" in pth_text:
        pth_text = pth_text.replace("#import site", "import site")
        pth.write_text(pth_text, encoding="utf-8")

    python_exe = target_dir / "python.exe"
    if not python_exe.exists():
        raise RuntimeError(f"Embedded Python missing python.exe at {python_exe}")

    print("Bootstrapping pip into the embedded runtime...")
    get_pip = target_dir / "get-pip.py"
    _download_with_verification(
        "https://bootstrap.pypa.io/get-pip.py",
        get_pip,
        expected_sha256=None,
    )
    subprocess.run([str(python_exe), str(get_pip), "--no-warn-script-location"], check=True)
    get_pip.unlink(missing_ok=True)

    runtime_dependencies = bundled_runtime_dependencies(pyproject)
    print(f"Installing runtime dependencies ({', '.join(runtime_dependencies)})...")
    subprocess.run(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--no-compile",
            *runtime_dependencies,
        ],
        check=True,
    )

    # Copy the Quill package source into site-packages so `python -m quill`
    # works without requiring a separate wheel build.
    site_packages = target_dir / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    quill_source = source_root / "quill"
    if not quill_source.is_dir():
        raise RuntimeError(f"Could not find quill/ package source under {source_root.resolve()}.")
    print(f"Copying Quill package source from {quill_source} into runtime...")
    shutil.copytree(quill_source, site_packages / "quill", dirs_exist_ok=True)

    archive.unlink(missing_ok=True)
    return target_dir


def bundled_runtime_dependencies(pyproject: Path) -> list[str]:
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project", {})
    if not isinstance(project, dict):
        return ["wxPython>=4.2.2", "pyttsx3>=2.99"]
    dependencies: list[str] = []
    raw_dependencies = project.get("dependencies", [])
    if isinstance(raw_dependencies, list):
        dependencies.extend(item for item in raw_dependencies if isinstance(item, str))
    optional = project.get("optional-dependencies", {})
    if isinstance(optional, dict):
        for group in DEFAULT_BUNDLED_DEPENDENCY_GROUPS:
            values = optional.get(group, [])
            if isinstance(values, list):
                dependencies.extend(item for item in values if isinstance(item, str))
    unique: list[str] = []
    for dependency in dependencies:
        if dependency not in unique:
            unique.append(dependency)
    return unique or ["wxPython>=4.2.2", "pyttsx3>=2.99"]


def _stage_distribution_docs(portable_dir: Path, source_root: Path) -> list[Path]:
    docs_dir = portable_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for relative in (Path("docs") / "userguide.md",):
        source = source_root / relative
        if not source.exists():
            continue
        target = docs_dir / source.name
        shutil.copy2(source, target)
        staged.append(target)
    return staged


def _stage_bundled_tools(portable_dir: Path, bundled_tool_dirs: dict[str, Path]) -> list[str]:
    if not bundled_tool_dirs:
        return []
    tools_root = portable_dir / "tools"
    tools_root.mkdir(parents=True, exist_ok=True)
    bundled: list[str] = []
    for tool_id, source in bundled_tool_dirs.items():
        if not source.exists():
            raise RuntimeError(f"Bundled tool path does not exist: {source}")
        target = tools_root / tool_id
        shutil.copytree(source, target, dirs_exist_ok=True)
        bundled.append(tool_id)
    return sorted(bundled)


def _download_and_stage_dectalk_release(portable_dir: Path) -> Path:
    speech_root = portable_dir / "_speech-download" / "dectalk"
    speech_root.mkdir(parents=True, exist_ok=True)
    archive = speech_root / "vs2022.zip"
    print(f"Downloading DECtalk release from {DECTALK_RELEASE_ZIP_URL}...")
    _download_with_verification(DECTALK_RELEASE_ZIP_URL, archive, expected_sha256=None)

    extract_root = speech_root / "extracted"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extract_root)

    # Prefer AMD64 runtime payload; keep the entire folder to preserve voices/dictionaries.
    amd64 = extract_root / "AMD64"
    if amd64.exists():
        return amd64
    return extract_root


def _speech_asset_manifest(
    portable_dir: Path, bundled_tools: list[str]
) -> dict[str, dict[str, object]]:
    speech_root = portable_dir / "tools" / "speech"
    manifest: dict[str, dict[str, object]] = {}
    for engine in (
        "dectalk",
        "kokoro",
        "piper",
        "rhvoice",
        "melotts",
        "chatterbox",
        "openvoice",
    ):
        engine_dir = speech_root / engine
        manifest[engine] = {
            "bundled": f"speech/{engine}" in bundled_tools,
            "path": str(engine_dir) if engine_dir.exists() else "",
            "exists": engine_dir.exists(),
            "downloadable": True,
        }
    return manifest


def _download_with_verification(
    url: str,
    target: Path,
    expected_sha256: str | None,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - URL is pinned
        data = response.read()
    if expected_sha256:
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha256:
            raise RuntimeError(
                f"SHA-256 mismatch for {url}\n  expected: {expected_sha256}\n  got:      {digest}"
            )
    target.write_bytes(data)


def _project_version(pyproject: Path) -> str:
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project", {})
    if isinstance(project, dict):
        version = project.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    return "unknown"


if __name__ == "__main__":
    sys.exit(main())
