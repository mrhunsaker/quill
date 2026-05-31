@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "PYTHON_EXE="

if defined QUILL_PYTHON call :UsePythonIfHasWx "%QUILL_PYTHON%"
if not defined PYTHON_EXE if defined VIRTUAL_ENV call :UsePythonIfHasWx "%VIRTUAL_ENV%\Scripts\python.exe"
if not defined PYTHON_EXE if defined CONDA_PREFIX call :UsePythonIfHasWx "%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE call :UsePythonIfHasWx "%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON_EXE call :UsePythonIfHasWx "%ROOT%venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE call :UsePythonIfHasWx "%%I"
    )
)

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where py.exe 2^>nul') do (
        if not defined PYTHON_EXE call :UsePythonIfHasWx "%%I"
    )
)

if not defined PYTHON_EXE (
    echo No Python interpreter was found.
    echo.
    echo Create or activate a development environment first, for example:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -e ".[dev,ui]"
    exit /b 1
)

if /i "%~1"=="--print-python" (
    echo %PYTHON_EXE%
    exit /b 0
)

REM --- Auto-install dependencies when requirements.txt changes ---
REM Hash requirements.txt and compare to the last installed hash; reinstall
REM only when it changed (e.g. after a git pull). Skip with QUILL_NO_AUTO_DEPS=1.
if not defined QUILL_NO_AUTO_DEPS if exist "%ROOT%requirements.txt" (
    set "REQ_HASH="
    for /f "skip=1 delims=" %%H in ('certutil -hashfile "%ROOT%requirements.txt" SHA256 2^>nul') do if not defined REQ_HASH set "REQ_HASH=%%H"
    set "OLD_HASH="
    if exist "%ROOT%.quill-reqs.sha256" set /p OLD_HASH=<"%ROOT%.quill-reqs.sha256"
    if not "!REQ_HASH!"=="!OLD_HASH!" (
        echo Requirements changed -- installing dependencies...
        "%PYTHON_EXE%" -m pip install -r "%ROOT%requirements.txt"
        if not errorlevel 1 (
            >"%ROOT%.quill-reqs.sha256" echo !REQ_HASH!
        ) else (
            echo Dependency install failed; launching with the existing environment.
        )
    )
)

pushd "%ROOT%"
"%PYTHON_EXE%" -m quill %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%

:UsePythonIfHasWx
set "CANDIDATE=%~1"
if not exist "%CANDIDATE%" exit /b 0
"%CANDIDATE%" -c "import wx" >nul 2>nul
if errorlevel 1 exit /b 0
set "PYTHON_EXE=%CANDIDATE%"
exit /b 0