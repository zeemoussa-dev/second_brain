@echo off
rem Stop, start or restart this checkout's backend: tools\backend.cmd status|stop|start|restart
rem See backend.ps1 for why a plain "kill uvicorn" is not enough (BUG-068, BUG-070).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend.ps1" %*
exit /b %errorlevel%
