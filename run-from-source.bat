@echo off
setlocal EnableExtensions

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