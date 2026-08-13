@echo off
cd /d "C:\myWorx\Projects\Second Brain\src\backend"
"C:\myWorx\Projects\Second Brain\src\backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8001
