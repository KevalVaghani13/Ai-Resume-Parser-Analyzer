from scoring import calculate_comprehensive_score, suggest_questions
from parser import parse_resume, parse_job_description, match_jd_keywords_in_resume


def main():
    candidate = {
        "skills": ["python", "sql", "docker"],
        "experience": 3,
        "text": "Built data pipeline using Python and SQL. Optimized queries by 40%. Led team of 3. AWS Docker PostgreSQL. Machine learning models deployed.",
        "name": "Test Candidate",
        "email": "test@example.com",
        "action_verbs": ["built", "optimized", "led", "deployed"],
        "metrics_data": {"metrics_count": 1, "has_impact": True},
        "experience_bullets": ["Built data pipeline using Python and SQL", "Optimized queries reducing latency by 40%", "Led data team through AWS migration"],
        "education": ["B.S. Computer Science"],
        "formatting_score": 85,
        "extracted_keywords": [],
    }
    
    job = parse_job_description("Need Python SQL AWS Docker with 2 years experience")
    
    # Extract keywords
    candidate["extracted_keywords"] = match_jd_keywords_in_resume(candidate.get("text", ""), job.get("jd_keywords", []))
    
    result = calculate_comprehensive_score(candidate, job)
    questions = suggest_questions(candidate, job, set(result.get("missing", [])))

    print("\n=== COMPREHENSIVE SCORING RESULTS ===")
    print(f"Final Score: {result.get('score')}%")
    print(f"\nScore Breakdown:")
    for component, score in result.get("breakdown", {}).items():
        print(f"  - {component}: {score}%")
    print(f"\nMatched Skills: {result.get('matched')}")
    print(f"Missing Skills: {result.get('missing')}")
    print(f"\nFeedback:")
    feedback = result.get("feedback", {})
    if feedback.get("strengths"):
        print(f"  Strengths: {'; '.join(feedback['strengths'])}")
    if feedback.get("weaknesses"):
        print(f"  Weaknesses: {'; '.join(feedback['weaknesses'])}")
    if feedback.get("suggestions"):
        print(f"  Suggestions: {'; '.join(feedback['suggestions'][:2])}")
    print(f"\nInterview Questions (Personalized):")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")


if __name__ == "__main__":
    main()
