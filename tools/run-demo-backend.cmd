@echo off
rem Paths are resolved relative to this script (%~dp0 = <repo>\tools\), so the
rem repo can live anywhere and be renamed/moved without editing this file.
cd /d "%~dp0..\src\demo-backend"
"%~dp0..\src\demo-backend\.venv\Scripts\uvicorn.exe" main:app --reload --port 8090
