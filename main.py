from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from parser import parse_resume, parse_job_description, match_jd_keywords_in_resume
from scoring import calculate_comprehensive_score, suggest_questions
from database import save_analysis_row, get_recent_matches, clear_history
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/analyze/")
async def analyze_resume(
    file: UploadFile = File(...),
    job_title: str = Form("Untitled Job"),
    job_description: str = Form(...)
):
    upload_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(upload_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    candidate = parse_resume(upload_path)
    job = parse_job_description(job_description)
    
    # Extract JD keywords into candidate for scoring
    jd_keywords = job.get("jd_keywords", [])
    candidate["extracted_keywords"] = match_jd_keywords_in_resume(candidate.get("text", ""), jd_keywords)

    # Comprehensive scoring
    result = calculate_comprehensive_score(candidate, job)
    
    # Generate personalized questions
    questions = suggest_questions(candidate, job, set(result.get("missing", [])))
    questions_to_save = [q['question'] if isinstance(q, dict) and 'question' in q else q for q in questions]
    persistence_error = None
    try:
        save_analysis_row(
            candidate.get("name") or file.filename,
            candidate.get("email"),
            candidate.get("mobile"),
            candidate.get("location"),
            candidate.get("skills", []),
            candidate.get("education", []),
            job_title,
            job.get("text", ""),
            job.get("required_skills", []),
            result.get("matched", []),
            result.get("missing", []),
            questions_to_save,
            result.get("score", 0.0),
        )
    except Exception as e:
        persistence_error = str(e)

    return {
        "filename": file.filename,
        "candidate_name": candidate.get("name") or file.filename,
        "email": candidate.get("email"),
        "mobile": candidate.get("mobile"),
        "location": candidate.get("location"),
        "match_percentage": result.get("score"),
        "match_score": result.get("score"),
        "score_breakdown": result.get("breakdown"),
        "matched_skills": result.get("matched"),
        "missing_skills": result.get("missing"),
        "feedback": result.get("feedback"),
        "suggested_questions": questions,
        "persistence_error": persistence_error,
    }


@app.post("/analyze-batch/")
async def analyze_batch(
    files: list[UploadFile] = File(...),
    job_title: str = Form("Untitled Job"),
    job_description: str = Form(...)
):
    job = parse_job_description(job_description)
    jd_keywords = job.get("jd_keywords", [])

    results = []
    for file in files:
        upload_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(upload_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        candidate = parse_resume(upload_path)
        
        # Extract JD keywords into candidate for scoring
        candidate["extracted_keywords"] = match_jd_keywords_in_resume(candidate.get("text", ""), jd_keywords)
        
        # Comprehensive scoring
        result = calculate_comprehensive_score(candidate, job)
        
        # Generate personalized questions
        questions = suggest_questions(candidate, job, set(result.get("missing", [])))
        questions_to_save = [q['question'] if isinstance(q, dict) and 'question' in q else q for q in questions]

        persistence_error = None
        try:
            save_analysis_row(
                candidate.get("name") or file.filename,
                candidate.get("email"),
                candidate.get("mobile"),
                candidate.get("location"),
                candidate.get("skills", []),
                candidate.get("education", []),
                job_title,
                job.get("text", ""),
                job.get("required_skills", []),
                result.get("matched", []),
                result.get("missing", []),
                questions_to_save,
                result.get("score", 0.0),
            )
        except Exception as e:
            persistence_error = str(e)

        results.append(
            {
                "filename": file.filename,
                "candidate_name": candidate.get("name") or file.filename,
                "score": result.get("score"),
                "score_breakdown": result.get("breakdown"),
                "matched_skills": result.get("matched"),
                "missing_skills": result.get("missing"),
                "feedback": result.get("feedback"),
                "suggested_questions": questions,
                "persistence_error": persistence_error,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "total_candidates": len(results),
        "results": results,
    }


@app.get("/matches/")
async def list_matches(limit: int = 50):
    return {"items": get_recent_matches(limit=limit)}


@app.post("/matches/clear")
async def clear_matches_history():
    return clear_history()