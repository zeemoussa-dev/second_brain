@echo off
setlocal
set "ROOT=%~dp0"

if not exist "%ROOT%src\backend\.env" (
    echo [Second Brain] src\backend\.env is missing.
    echo Copy src\backend\.env.example to src\backend\.env and fill in the
    echo required values before starting - see Documentation\DeploymentGuide.md.
    pause
    exit /b 1
)

echo [Second Brain] Starting backend and frontend, each in its own window...

start "Second Brain - Backend"  cmd /k "%ROOT%tools\run-backend.cmd"
start "Second Brain - Frontend" cmd /k "%ROOT%tools\run-frontend.cmd"

echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:5173
echo.
echo Each server keeps running in its own window after you close this one.
