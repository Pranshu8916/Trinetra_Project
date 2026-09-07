@echo off
title Trinetra Backend - SIH
cd /d "%~dp0"
color 0A
echo =====================================================================
echo           TRINETRA AI BACKEND (SIH PROJECT WITH FACENET)
echo =====================================================================
echo.
echo [*] Starting FastAPI Backend on http://0.0.0.0:8000 ...
echo [*] MongoDB: mongodb://localhost:27017
echo.
"%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
