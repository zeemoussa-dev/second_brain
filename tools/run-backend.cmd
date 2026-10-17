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
rem A backend already on 8001 -- often an orphaned --reload worker serving old code --
rem would make this one fail to bind while /health kept answering (BUG-068). Name it
rem and stop, rather than start a second one. No pause: a hidden launch would hang on it.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend.ps1" preflight
if errorlevel 1 exit /b 1
rem --timeout-graceful-shutdown: uvicorn's default is to wait FOREVER for open
rem connections and background tasks, and this app serves SSE streams
rem (text/event-stream, in agents_router and cockpit_router) that a page holds
rem open for as long as it is open. On 2026-10-18 a --reload after a plugin
rem install sat at "Waiting for connections to close" for over five minutes with
rem no worker serving anything: every route timed out, for every plugin, until
rem someone found and killed the stuck child. Ten seconds drains a normal
rem reload; past that the connections are dropped, which is always better than
rem the whole app staying down.
"%~dp0..\src\backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8001 --timeout-graceful-shutdown 10
