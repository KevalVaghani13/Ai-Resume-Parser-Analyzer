import math
import json
from functools import lru_cache
from parser import match_jd_keywords_in_resume

MODEL = None
MODEL_NAME = 'all-MiniLM-L6-v2'

def _load_model():
    global MODEL
    try:
        from sentence_transformers import SentenceTransformer, util
        MODEL = SentenceTransformer(MODEL_NAME)
        return True
    except Exception:
        MODEL = None
        return False


@lru_cache(maxsize=1024)
def _encode_text_cached(text):
    global MODEL
    if MODEL is None:
        ok = _load_model()
        if not ok:
            return None
    return MODEL.encode(text, convert_to_tensor=True, normalize_embeddings=True)


def semantic_similarity(a_text, b_text):
    """Return cosine similarity between two texts using sentence-transformers if available.
    Falls back to 0.0 if model not available."""
    global MODEL
    try:
        from sentence_transformers import util
        emb1 = _encode_text_cached(a_text)
        emb2 = _encode_text_cached(b_text)
        if emb1 is None or emb2 is None:
            return 0.0
        sim = util.cos_sim(emb1, emb2).item()
        return (sim + 1) / 2
    except Exception:
        return 0.0


def calculate_match(candidate, job):
    candidate_skills = set(candidate.get("skills", []))
    job_skills = set(job.get("required_skills", []))
    jd_keywords = job.get("jd_keywords", [])
    
    # Match candidate text against JD keywords (full PDF scan)
    matched_keywords = match_jd_keywords_in_resume(candidate.get("text", ""), jd_keywords)
    candidate["extracted_keywords"] = matched_keywords  # store for later use in questions

    if not job_skills and not jd_keywords:
        return {
            "score": 0.0,
            "matched": [],
            "missing": [],
            "skill_score": 0.0,
            "semantic_score": 0.0,
            "experience_score": 0.0,
            "keyword_score": 0.0
        }

    matched = candidate_skills.intersection(job_skills)
    missing = job_skills - candidate_skills

    # Skill score: how many required skills candidate has
    skill_score = len(matched) / len(job_skills) if job_skills else 0.0

    # Keyword score: how many JD keywords appear in resume text
    keyword_score = len(matched_keywords) / len(jd_keywords) if jd_keywords else 0.0

    # Experience score
    cand_years = candidate.get("experience", 0)
    min_years = job.get("min_experience", 0)
    experience_score = 1.0
    if min_years > 0:
        experience_score = min(1.0, cand_years / float(min_years))

    # Semantic similarity
    sem_score = 0.0
    try:
        sem_score = semantic_similarity(job.get("text", ""), candidate.get("text", ""))
    except Exception:
        sem_score = 0.0

    # Weighted final score: skills + keywords + experience + semantic
    final = 0.45 * skill_score + 0.25 * keyword_score + 0.15 * sem_score + 0.15 * experience_score

    return {
        "score": round(final * 100, 2),
        "matched": list(matched),
        "missing": list(missing),
        "skill_score": round(skill_score, 3),
        "keyword_score": round(keyword_score, 3),
        "semantic_score": round(sem_score, 3),
        "experience_score": round(experience_score, 3)
    }


def suggest_questions(candidate, job, missing_skills):
    """Generate personalized interview questions based on candidate profile and job requirements."""
    questions = []
    
    # Extract candidate info
    cand_years = candidate.get("experience", 0)
    matched_keywords = candidate.get("extracted_keywords", [])
    candidate_text = candidate.get("text", "").lower()
    
    # Question 1: Ask about missing core skills
    for skill in list(missing_skills)[:3]:
        questions.append(f"You don't have explicit {skill} experience. Walk us through how you'd approach learning {skill} for this role.")
    
    # Question 2: Dig deeper into matched skills (ask for specific examples)
    matched_skills = candidate.get("skills", [])
    for skill in list(matched_skills)[:2]:
        questions.append(f"Can you describe a specific project where you used {skill} and what impact it had?")
    
    # Question 3: Experience level-based questions
    job_min_years = job.get("min_experience", 0)
    if cand_years < job_min_years:
        gap = job_min_years - cand_years
        questions.append(f"The role typically requires {job_min_years}+ years. You have {cand_years} years. How have you made up for this in your other experiences?")
    elif cand_years >= job_min_years + 3:
        questions.append(f"With {cand_years} years of experience, what attracted you to this specific role?")
    
    # Question 4: Semantically related questions based on keywords found in resume
    if matched_keywords:
        # Pick a keyword that was in resume and ask about it
        kw = matched_keywords[0] if matched_keywords else ""
        if kw and kw not in missing_skills:
            questions.append(f"Your resume mentions {kw}. Tell us more about how you've applied it and your level of expertise.")
    
    # Question 5: Culture/soft skills
    if "leadership" in candidate_text or "led" in candidate_text or "managed" in candidate_text:
        questions.append("Tell us about a time you led or mentored others. What did you learn?")
    else:
        questions.append("Describe a time you had to collaborate cross-functionally to solve a problem.")
    
    # Question 6: Motivation
    questions.append("What interests you about this specific role and company?")
    
    return questions[:6]  # Return top 6 personalized questions