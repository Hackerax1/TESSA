@echo off
echo Launching Proxmox NLI Setup Wizard...

REM Check if Python is available in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found in PATH. Checking known locations...
    
    REM Try common Python installation locations
    set PYTHON_FOUND=0
    for %%p in (
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
        "%PROGRAMFILES%\Python310\python.exe"
        "%PROGRAMFILES%\Python39\python.exe"
        "%PROGRAMFILES%\Python38\python.exe"
        "%PROGRAMFILES(X86)%\Python310\python.exe"
        "%PROGRAMFILES(X86)%\Python39\python.exe"
        "%PROGRAMFILES(X86)%\Python38\python.exe"
    ) do (
        if exist %%p (
            echo Found Python at %%p
            set PYTHON_PATH=%%p
            set PYTHON_FOUND=1
            goto :found_python
        )
    )
    
    :found_python
    if %PYTHON_FOUND% equ 0 (
        echo.
        echo Python 3.8 or higher is required but was not found on your system.
        echo Please install Python from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        echo Press any key to open the Python download page...
        pause >nul
        start "" https://www.python.org/downloads/
        goto :end
    )
) else (
    set PYTHON_PATH=python
)

REM Run the installer script
echo Starting installer...
"%PYTHON_PATH%" installer.py

:end
if %errorlevel% neq 0 (
    echo.
    echo Setup wizard encountered an error.
    echo.
    pause
)