# Resume Screening AI (Free Stack)

This project screens resumes against a job description and returns:
- match percentage
- matched and missing skills
- suggested interview questions
- persisted history in Google Sheets

## Tech
- FastAPI
- pdfplumber + python-docx
- spaCy
- sentence-transformers (optional semantic score)
- gspread + Google service account for persistence

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
Create a `.env` file in the project root with:
```env
GOOGLE_SHEET_ID=1mDk__V-GDYUH2RG-Ulee7QEZQTXoaQf5PtcwG7RKMJc
GOOGLE_SERVICE_ACCOUNT_FILE=C:\Users\ADMIN\Desktop\resume builder\service_account.json
```

Then share the Google Sheet with the service account email from that JSON file.

The app writes all analysis data into one worksheet named `analysis` with one row per resume/job analysis.

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
