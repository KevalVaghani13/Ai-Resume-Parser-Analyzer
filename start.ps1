# Resume Screening AI - Start Script
Write-Host "Starting Resume Screening AI..." -ForegroundColor Green
Write-Host ""
Write-Host "Testing fixes with multiple resumes..." -ForegroundColor Cyan

# Run test
& '.\.venv\Scripts\python.exe' scripts\test_different_scores.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Starting API server on http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Start API
& '.\.venv\Scripts\python.exe' -m uvicorn main:app --host 127.0.0.1 --port 8000
