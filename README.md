# Resume Screening AI (Free Stack)

This project screens resumes against a job description and returns:
- match percentage
- matched and missing skills
- suggested interview questions
- persisted history in Google Sheets

## Tech
- FastAPI
- pdfplumber + python-docx
- gspread + Google service account for persistence
- Optional local extras: spaCy, sentence-transformers, OCR libraries

The optional extras are only needed if you want local OCR or semantic scoring. Install `requirements.txt` on your machine to get the full feature set.

## API Endpoints
- `POST /analyze/` : Analyze one resume
- `POST /analyze-batch/` : Analyze multiple resumes (10-12 supported)
- `GET /matches/` : Get recent history

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

For server or local deployment, install dependencies with `pip install -r requirements.txt`.

**One-step setup (recommended for new users)**

Windows (PowerShell):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\setup.ps1
```

Linux / macOS:
```bash
bash setup.sh
```

These scripts will create a `.venv` virtual environment, install all Python packages from `requirements.txt`, and attempt to download the spaCy model if spaCy is installed.

If you need to extract text from image-based PDFs, also install the Tesseract OCR engine on Windows and keep the `tesseract` binary on your PATH. The app will fall back to OCR automatically when a PDF page has little or no selectable text.

Windows install (recommended):

- Using winget (Windows 10/11):

```powershell
winget install --id UB-Mannheim.Tesseract -e
```

- Using Chocolatey:

```powershell
choco install tesseract -y
```

After installing, ensure the `tesseract` executable is available from PowerShell or CMD (restart shell if needed):

```powershell
tesseract --version
```

If the command prints a version, OCR is available and the app will automatically use it when needed.

## Google Sheets Setup
This app stores analysis results in Google Sheets. To keep credentials private, do not upload your `.env` file or `service_account.json` to GitHub. They are already listed in `.gitignore`.

### Easy setup for non-coders
1. Open the project folder.
2. Copy `.env.example` to `.env`.
3. Fill in your Google Sheet ID.
4. Download your Google service account JSON key from Google Cloud and save it as `service_account.json` in the project root.
5. Share your Google Sheet with the service account email from that JSON file.

If you prefer, you can also keep the JSON out of the project folder and use environment variables instead.

Create a `.env` file in the project root with:
```env
GOOGLE_SHEET_ID=1mDk__V-GDYUH2RG-Ulee7QEZQTXoaQf5PtcwG7RKMJc
GOOGLE_SERVICE_ACCOUNT_FILE=C:\Users\ADMIN\Desktop\resume builder\service_account.json
```

Then share the Google Sheet with the service account email from that JSON file.

For serverless deployments, you can also set the service account as an environment variable instead of a file:

```env
GOOGLE_SERVICE_ACCOUNT_JSON={...raw JSON...}
# or
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=...
```

The app writes all analysis data into one worksheet named `analysis` with one row per resume/job analysis.

## Deploying Frontend to Netlify and Backend to a Python Host

Netlify is a great place to host the static dashboard; it doesn't natively run Python backends. A common pattern is:

- Host the static site on Netlify (publish directory: `static`).
- Host the FastAPI backend on a Python-friendly host (Render, Railway, Fly, or a VM).
- Configure Netlify redirects or proxy so frontend API calls (e.g. `/analyze/`) are forwarded to the backend.

Quick steps:

1. Pick a backend host (Render recommended for quick deploy):
  - Create an account and connect your GitHub repo.
  - Create a new Web Service using the `main` branch.
  - Set the start command to: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
  - Add environment variables: `GOOGLE_SHEET_ID` and either `GOOGLE_SERVICE_ACCOUNT_FILE` (upload) or `GOOGLE_SERVICE_ACCOUNT_JSON` (raw JSON).
  - Deploy. Note the published domain (e.g. `https://my-backend.onrender.com`).

2. Configure the frontend on Netlify:
  - Create a new site and connect the same GitHub repo (or drag the `static/` folder to Netlify deploy UI).
  - Set `Publish directory` to `static` and no build command (unless you add a build step).
  - Add a file `static/_redirects` with rules to proxy API paths to your backend (a template is included in the repo). Replace `<YOUR_BACKEND_DOMAIN>` with your backend URL.

3. CORS: Ensure the backend allows requests from the Netlify site. This repo now enables permissive CORS in `main.py`. For production, restrict `allow_origins` to your Netlify domain.

4. Secrets: Never commit `.env` or `service_account.json`. Use your host's environment variable settings to supply secrets.

That setup keeps the static UI fast on Netlify while the Python API runs on a proper Python host.

### What gets committed to GitHub
- Application code, UI files, and docs are committed normally.
- `.env` stays local and is never uploaded.
- `service_account.json` stays local and is never uploaded.

## Example: Single Resume
```bash
curl -X POST "http://127.0.0.1:8000/analyze/" ^
  -F "file=@C:/path/to/resume.pdf" ^
  -F "job_title=Data Engineer" ^
  -F "job_description=Need Python SQL AWS Docker with 3 years experience"
```

## Example: Batch (10-12 resumes)
```bash
curl -X POST "http://127.0.0.1:8000/analyze-batch/" ^
  -F "files=@C:/path/r1.pdf" ^
  -F "files=@C:/path/r2.pdf" ^
  -F "files=@C:/path/r3.docx" ^
  -F "job_title=Data Engineer" ^
  -F "job_description=Need Python SQL AWS Docker with 3 years experience"
```
