@echo off
rem Paths are resolved relative to this script (%~dp0 = <repo>\tools\), so the
rem repo can live anywhere and be renamed/moved without editing this file.
rem Uses the backend venv's own Python: a bare `py`/`python` on a fresh Windows
rem machine resolves to the Microsoft Store stub, which is not a real interpreter.
cd /d "%~dp0..\html-prototype"
"%~dp0..\src\backend\.venv\Scripts\python.exe" -m http.server 8088
