@echo off
rem Paths are resolved relative to this script (%~dp0 = <repo>\tools\), so the
rem repo can live anywhere and be renamed/moved without editing this file.
cd /d "%~dp0..\src\backend"
if not exist "%~dp0..\src\backend\.venv\Scripts\uvicorn.exe" (
    echo [Second Brain] Backend venv is missing.
    echo Create it with:
    echo   uv venv --python 3.11 .venv
    echo   uv pip install --python .venv\Scripts\python.exe -r requirements.txt
    echo See Deployment.md section 3.
    pause
    exit /b 1
)
"%~dp0..\src\backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8001
