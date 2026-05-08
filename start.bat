@echo off
cd /d "%~dp0"
echo Starting Resume Screening AI...
echo.
echo Testing fixes with multiple resumes...
call .venv\Scripts\python.exe scripts\test_different_scores.py
echo.
echo.
echo ============================================================
echo Starting API server on http://127.0.0.1:8000
echo ============================================================
call .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
