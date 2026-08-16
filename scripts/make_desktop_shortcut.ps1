# Creates a "Harness Quote" shortcut on your Desktop, wired to this
# project's venv, so you can launch the app without a terminal.
#
# Usage (from the project root, in PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts\make_desktop_shortcut.ps1

$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonwExe = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "No venv found at $ProjectDir\.venv — run the setup steps in README.md first."
    exit 1
}

# pythonw.exe runs without popping up a console window; falls back to
# python.exe (console-visible) if pythonw.exe isn't present for some reason.
$Target = if (Test-Path $PythonwExe) { $PythonwExe } else { $PythonExe }

$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Harness Quote.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.Arguments = "main.py"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.IconLocation = $PythonExe
$Shortcut.Description = "Harness Quote"
$Shortcut.Save()

Write-Host "Created `"$ShortcutPath`" - double-click it to launch the app."
