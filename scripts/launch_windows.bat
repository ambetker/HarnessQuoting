@echo off
REM Launches the Harness Quoting app on Windows. Can be run directly, or
REM double-clicked via the Desktop shortcut created by
REM make_desktop_shortcut.ps1.

set "PROJECT_DIR=%~dp0.."
set "LOG_FILE=%PROJECT_DIR%\app_launch.log"

if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo No venv found at %PROJECT_DIR%\.venv — run the setup steps in README.md first.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
"%PROJECT_DIR%\.venv\Scripts\python.exe" main.py > "%LOG_FILE%" 2>&1
