@echo off
cd /d "C:\myWorx\Projects\Second Brain\src\demo-backend"
"C:\myWorx\Projects\Second Brain\src\demo-backend\.venv\Scripts\uvicorn.exe" main:app --reload --port 8090
