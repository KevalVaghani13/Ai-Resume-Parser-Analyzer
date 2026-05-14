<#
Windows setup script for Resume Screening AI
Usage (PowerShell):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .\setup.ps1
#>

$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment .venv..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "Installing Python packages into .venv..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Attempting to download spaCy model (if spaCy installed)..." -ForegroundColor Cyan
try {
    .\.venv\Scripts\python.exe -m spacy download en_core_web_sm
} catch {
    Write-Host "spaCy model download skipped or failed (not required for light deploy)." -ForegroundColor Yellow
}

Write-Host "Setup complete. Activate the virtualenv with: .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "To run the app: .\\.venv\\Scripts\\python.exe -m uvicorn main:app --reload" -ForegroundColor Green

Write-Host "If you need OCR support, install Tesseract separately (winget or chocolatey recommended)." -ForegroundColor Yellow
Write-Host "Example (winget): winget install --id UB-Mannheim.Tesseract -e" -ForegroundColor Yellow
