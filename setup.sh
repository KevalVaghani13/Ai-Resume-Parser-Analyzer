#!/usr/bin/env bash
# Unix setup script for Resume Screening AI
# Usage:
#   bash setup.sh

set -euo pipefail

echo "Creating virtual environment .venv..."
python3 -m venv .venv

echo "Activating virtualenv and upgrading pip..."
source .venv/bin/activate
python -m pip install --upgrade pip

echo "Installing Python packages from requirements.txt..."
python -m pip install -r requirements.txt

echo "Attempting to download spaCy model (if spaCy installed)..."
if python -c "import importlib; importlib.util.find_spec('spacy')" >/dev/null 2>&1; then
  python -m spacy download en_core_web_sm || true
else
  echo "spaCy not installed; skipping model download."
fi

echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Run server: python -m uvicorn main:app --reload"

echo "If you need OCR support, install Tesseract (e.g., on Debian/Ubuntu: sudo apt install tesseract-ocr)."
