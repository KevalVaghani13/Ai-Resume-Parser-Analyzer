import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
import base64

from dotenv import load_dotenv

load_dotenv()

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception as exc:
    raise RuntimeError("Missing Google Sheets dependencies. Install 'gspread' and 'google-auth'.") from exc

DEFAULT_SERVICE_ACCOUNT_FILE = "service_account.json"
WORKSHEET_TITLE = "analysis"
WORKSHEET_HEADERS = [
    "id",
    "candidate_name",
    "email",
    "mobile",
    "location",
    "skills",
    "education",
    "job_title",
    "job_description",
    "required_skills",
    "matched_skills",
    "missing_skills",
    "suggested_questions",
    "match_score",
    "created_at",
]


def _sheet_settings():
    service_account_file = (
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or DEFAULT_SERVICE_ACCOUNT_FILE
    )
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    return service_account_file, sheet_id


def _service_account_credentials():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        return Credentials.from_service_account_info(json.loads(service_account_json), scopes=scopes)

    service_account_json_base64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    if service_account_json_base64:
        decoded_json = base64.b64decode(service_account_json_base64).decode("utf-8")
        return Credentials.from_service_account_info(json.loads(decoded_json), scopes=scopes)

    service_account_file, _ = _sheet_settings()
    if not os.path.exists(service_account_file):
        raise RuntimeError(f"Service account file not found: {service_account_file}")

    return Credentials.from_service_account_file(service_account_file, scopes=scopes)


def _ensure_client():
    _, sheet_id = _sheet_settings()
    if not sheet_id:
        raise RuntimeError("Environment variable GOOGLE_SHEET_ID is required.")

    creds = _service_account_credentials()
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def _sheet_available() -> bool:
    _, sheet_id = _sheet_settings()
    has_json_credentials = bool(
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    )
    service_account_file, _ = _sheet_settings()
    return bool(sheet_id and (has_json_credentials or os.path.exists(service_account_file)))


def _get_or_create_ws(sheet):
    try:
        ws = sheet.worksheet(WORKSHEET_TITLE)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=WORKSHEET_TITLE, rows=1000, cols=len(WORKSHEET_HEADERS) + 5)
        ws.append_row(WORKSHEET_HEADERS)
        return ws

    header = ws.row_values(1)
    if header != WORKSHEET_HEADERS:
        ws.clear()
        ws.append_row(WORKSHEET_HEADERS)
    return ws


def _next_id(ws) -> int:
    values = ws.col_values(1)
    if len(values) <= 1:
        return 1
    try:
        return int(values[-1]) + 1
    except Exception:
        return len(values)


def _json_text(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _parse_json_list(value: Any) -> List[Any]:
    """Safely parse a JSON list from sheet text; return [] on invalid input."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _parse_questions(value: Any) -> List[str]:
    """Support both historical JSON-array format and new newline-separated text."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value).strip()
    if not text:
        return []

    # Backward compatibility for older rows that stored JSON arrays.
    if text.startswith("["):
        parsed = _parse_json_list(text)
        return [str(v).strip() for v in parsed if str(v).strip()]

    # Current format: one question per line.
    return [line.strip() for line in text.splitlines() if line.strip()]


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def _to_years_months(experience: Any) -> tuple[int, int]:
    years = _to_int(experience)
    return years, years * 12


def save_analysis_row(
    candidate_name: str,
    email: str,
    mobile: str,
    location: str,
    skills: List[str],
    education: List[str],
    job_title: str,
    job_description: str,
    required_skills: List[str],
    matched_skills: List[str],
    missing_skills: List[str],
    suggested_questions: List[Any],
    match_score: Any,
):
    sheet = _ensure_client()
    ws = _get_or_create_ws(sheet)
    row_id = _next_id(ws)
    created_at = datetime.now(timezone.utc).isoformat()
    questions_formatted = "\n".join(suggested_questions or [])
    
    ws.append_row(
        [
            row_id,
            candidate_name or "",
            email or "",
            mobile or "",
            location or "",
            ", ".join(skills or []),
            "; ".join(education or []),
            job_title or "",
            job_description or "",
            ", ".join(required_skills or []),
            _json_text(matched_skills),
            _json_text(missing_skills),
            questions_formatted,
            float(match_score or 0.0),
            created_at,
        ]
    )
    return row_id


def get_recent_matches(limit: int = 50):
    if not _sheet_available():
        return []

    sheet = _ensure_client()
    ws = _get_or_create_ws(sheet)
    rows = ws.get_all_records()
    rows_sorted = sorted(rows, key=lambda row: _to_int(row.get("id", 0)), reverse=True)[:limit]

    result = []
    for row in rows_sorted:
        result.append(
            {
                "match_id": row.get("id"),
                "candidate_name": row.get("candidate_name"),
                "email": row.get("email"),
                "mobile": row.get("mobile"),
                "location": row.get("location"),
                "skills": [item.strip() for item in (row.get("skills") or "").split(",") if item.strip()],
                "experience_duration": row.get("experience_duration"),
                "education": [item.strip() for item in (row.get("education") or "").split(";") if item.strip()],
                "job_title": row.get("job_title"),
                "job_description": row.get("job_description"),
                "required_skills": [item.strip() for item in (row.get("required_skills") or "").split(",") if item.strip()],
                "matched_skills": _parse_json_list(row.get("matched_skills")),
                "missing_skills": _parse_json_list(row.get("missing_skills")),
                "suggested_questions": _parse_questions(row.get("suggested_questions")),
                "score": row.get("match_score"),
                "feedback": _parse_json_list(row.get("feedback")),
                "created_at": row.get("created_at"),
            }
        )
    return result


def clear_history():
    if not _sheet_available():
        return {"cleared": False, "message": "Google Sheets persistence is not configured."}

    sheet = _ensure_client()
    try:
        ws = sheet.worksheet(WORKSHEET_TITLE)
        ws.clear()
        ws.append_row(WORKSHEET_HEADERS)
    except gspread.exceptions.WorksheetNotFound:
        _get_or_create_ws(sheet)
    return {"cleared": True}