@echo off
rem Paths are resolved relative to this script (%~dp0 = <repo>\tools\), so the
rem repo can live anywhere and be renamed/moved without editing this file.
cd /d "%~dp0..\src\frontend"
if not exist "%~dp0node\npm.cmd" (
    echo [Second Brain] Portable Node is missing at tools\node.
    echo See Deployment.md section 3 for how to populate it.
    pause
    exit /b 1
)
set "PATH=%~dp0node;%PATH%"
"%~dp0node\npm.cmd" run dev
