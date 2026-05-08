"""
Comprehensive resume scoring engine with 8 scoring components.
"""
import re
from parser import match_jd_keywords_in_resume
from matcher import semantic_similarity

# Synonym mappings for skills
SKILL_SYNONYMS = {
    "javascript": ["js", "node", "nodejs"],
    "python": ["py"],
    "machine learning": ["ml", "deep learning", "ai", "artificial intelligence"],
    "aws": ["amazon web services", "amazon"],
    "sql": ["postgres", "mysql", "sql server", "database"],
    "react": ["reactjs"],
    "docker": ["containerization", "containers"],
    "kubernetes": ["k8s", "k8"],
    "rest api": ["restful", "rest"],
    "git": ["github", "gitlab", "version control"],
}


def parse_experience_duration(duration_str):
    """
    Parse experience duration string and return years as a float.
    Handles formats like: "4 weeks", "2 years", "2+ years", "June 2024 - July 2025",
    and year-only ranges like "2020 - 2024".
    Returns 0 if no experience or cannot parse.
    """
    if not duration_str or not isinstance(duration_str, str):
        return 0.0
    
    duration_lower = duration_str.lower().strip()
    
    # Check for years patterns: "X years", "X+ years"
    years_match = re.search(r'(\d+)\+?\s*years?', duration_lower)
    if years_match:
        return float(years_match.group(1))
    
    # Check for months: "X months" or "X-month"
    months_match = re.search(r'(\d+)\s*(?:months?|-month)', duration_lower)
    if months_match:
        return float(months_match.group(1)) / 12.0
    
    # Check for weeks: "X weeks" or "X-week"
    weeks_match = re.search(r'(\d+)\s*(?:weeks?|-week)', duration_lower)
    if weeks_match:
        return float(weeks_match.group(1)) / 52.0
    
    months_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    # Check for date range: "Month Year - Month Year" (e.g., "June 2024 - July 2025")
    date_pattern = r'([a-z]+)\s+(\d{4})\s*[-\u2013]\s*([a-z]+)\s+(\d{4}|present|current|now)'
    date_match = re.search(date_pattern, duration_lower)
    if date_match:
        start_month_str, start_year, end_month_str, end_year = date_match.groups()

        try:
            start_month = months_map.get(start_month_str[:3], 1)
            start_year_int = int(start_year)

            if end_year.lower() in ['present', 'current', 'now']:
                import datetime
                now = datetime.datetime.now()
                end_month = now.month
                end_year_int = now.year
            else:
                end_month = months_map.get(end_month_str[:3], 1)
                end_year_int = int(end_year)

            total_months = (end_year_int * 12 + end_month) - (start_year_int * 12 + start_month)
            return max(0.0, total_months / 12.0)
        except:
            return 0.0

    # Check for year-only ranges: "2020 - 2024" or "2020 - Present"
    year_range_match = re.search(r'((?:19|20)\d{2})\s*[-\u2013]\s*((?:19|20)\d{2}|present|current|now)', duration_lower)
    if year_range_match:
        start_year, end_year = year_range_match.groups()
        try:
            start_year_int = int(start_year)
            if end_year in ['present', 'current', 'now']:
                import datetime
                end_year_int = datetime.datetime.now().year
            else:
                end_year_int = int(end_year)
            return max(0.0, float(end_year_int - start_year_int))
        except:
            return 0.0
    
    return 0.0


def normalize_skill(skill):
    """Convert skill to canonical form for matching."""
    skill_lower = skill.lower().strip()
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if skill_lower == canonical.lower():
            return canonical
        for syn in synonyms:
            if skill_lower == syn.lower():
                return canonical
    return skill_lower


def keyword_match_score(candidate, job):
    """
    Component 1: Multi-layer keyword matching (exact + synonym + semantic).
    Returns score 0-100.
    """
    job_skills = set(job.get("required_skills", []))
    candidate_skills = set(candidate.get("skills", []))
    
    if not job_skills:
        return 100.0, [], []
    
    # Layer 1: Exact match
    exact_matched = candidate_skills.intersection(job_skills)
    
    # Layer 2: Synonym match
    synonym_matched = set()
    for job_skill in job_skills:
        canonical_job = normalize_skill(job_skill)
        for cand_skill in candidate_skills:
            canonical_cand = normalize_skill(cand_skill)
            if canonical_job == canonical_cand and job_skill not in exact_matched:
                synonym_matched.add(job_skill)
    
    # Layer 3: JD keyword coverage found in resume text
    jd_keywords = job.get("jd_keywords", [])
    semantic_matched = set(candidate.get("extracted_keywords", []))

    # Use capped keyword denominator so long JDs do not crush score quality.
    effective_keyword_pool = max(8, len(job_skills) * 2)
    keyword_pool = min(len(jd_keywords), effective_keyword_pool)

    skill_coverage = (len(exact_matched) + len(synonym_matched)) / len(job_skills) if job_skills else 0.0
    keyword_coverage = len(semantic_matched) / keyword_pool if keyword_pool else 0.0

    # Skill precision has higher impact than generic keyword frequency.
    score = (0.75 * skill_coverage + 0.25 * min(1.0, keyword_coverage)) * 100
    
    missing = job_skills - exact_matched - synonym_matched
    
    return min(100.0, score), list(exact_matched) + list(synonym_matched), list(missing)


def formatting_score(candidate):
    """
    Component 2: Formatting quality score 0-100.
    """
    return candidate.get("formatting_score", 50)


def experience_relevance_score(candidate, job):
    """
    Component 3: Experience relevance based on role match and semantic similarity.
    Returns score 0-100.
    """
    cand_years = parse_experience_duration(candidate.get("experience", ""))
    min_years = job.get("min_experience", 0)
    
    # Years requirement match
    if min_years == 0:
        years_score = 100.0
    else:
        years_score = min(100.0, (cand_years / float(min_years)) * 100)
    
    # Semantic similarity of experience bullets to job description
    job_text = job.get("text", "")
    experience_bullets = candidate.get("experience_bullets", [])
    
    if experience_bullets and job_text:
        # Fast lexical precheck avoids expensive embedding calls for irrelevant bullets.
        job_tokens = set(re.findall(r"\b[a-z]{3,}\b", job_text.lower()))
        similarities = []
        for bullet in experience_bullets[:2]:
            bullet_tokens = set(re.findall(r"\b[a-z]{3,}\b", bullet.lower()))
            overlap = len(job_tokens.intersection(bullet_tokens))
            if overlap < 2:
                sim = 0.25
            else:
                sim = semantic_similarity(bullet, job_text)
            similarities.append(sim * 100)  # convert to 0-100
        
        relevance_score = sum(similarities) / len(similarities) if similarities else 0.0
    else:
        relevance_score = 50.0
    
    # Combine: 60% years, 40% relevance
    final = 0.6 * years_score + 0.4 * relevance_score
    return min(100.0, final)


def skills_context_score(candidate, job):
    """
    Component 4: Score based on skills appearing in context (experience bullets).
    Returns score 0-100.
    """
    job_skills = set(job.get("required_skills", []))
    candidate_skills = set(candidate.get("skills", []))
    matched_skills = job_skills.intersection(candidate_skills)
    
    if not matched_skills:
        return 0.0
        
    experience_bullets_text = " ".join(candidate.get("experience_bullets", [])).lower()
    
    matched_in_context = 0
    for skill in matched_skills:
        if skill.lower() in experience_bullets_text:
            matched_in_context += 1
    
    # Score: percentage of RELEVANT skills mentioned in bullets
    context_score = (matched_in_context / len(matched_skills)) * 100
    
    return min(100.0, context_score)


def bonus_signals_score(candidate):
    """
    Component 5: Bonus points for impact signals (metrics, action verbs, education).
    Returns score 0-100. Additive bonus.
    """
    bonus = 0.0
    
    # Action verbs (up to +20 points)
    action_verbs_count = len(candidate.get("action_verbs", []))
    action_bonus = min(20.0, action_verbs_count * 2)
    bonus += action_bonus
    
    # Metrics and impact (up to +20 points)
    metrics_data = candidate.get("metrics_data", {})
    metrics_count = metrics_data.get("metrics_count", 0)
    has_impact = metrics_data.get("has_impact", False)
    impact_bonus = min(20.0, metrics_count * 3 + (10 if has_impact else 0))
    bonus += impact_bonus
    
    # Education (up to +15 points)
    education = candidate.get("education", [])
    if education:
        # +5 for having education, +10 for advanced degree indicators
        education_bonus = 5.0
        for edu in education:
            edu_l = edu.lower()
            if re.search(r'\b(master|phd|m\.s\.|m\.a\.|m\.tech)\b', edu_l):
                education_bonus += 10.0
                break
        bonus += min(15.0, education_bonus)
    
    # Cap bonus at 100 for this component
    return min(100.0, bonus)


def calculate_comprehensive_score(candidate, job):
    """
    Calculate final score using all 8 components with weighted formula.
    
    Weights:
    - 0.30 Keyword matching (most important)
    - 0.25 Experience relevance
    - 0.20 Skills context
    - 0.15 Bonus signals
    - 0.10 Formatting
    
    Returns:
        dict with full scoring breakdown and feedback
    """
    # Calculate individual scores
    keyword_score, matched, missing = keyword_match_score(candidate, job)
    formatting = formatting_score(candidate)
    experience_rel = experience_relevance_score(candidate, job)
    skills_context = skills_context_score(candidate, job)
    bonus = bonus_signals_score(candidate)
    
    # Weighted final score
    final_score = (
        0.30 * keyword_score +
        0.25 * experience_rel +
        0.20 * skills_context +
        0.15 * bonus +
        0.10 * formatting
    )
    
    # Generate feedback
    feedback = generate_feedback(candidate, job, missing, keyword_score, skills_context)
    
    return {
        "score": round(final_score, 2),
        "breakdown": {
            "keyword_score": round(keyword_score, 2),
            "experience_relevance": round(experience_rel, 2),
            "skills_context": round(skills_context, 2),
            "bonus_signals": round(bonus, 2),
            "formatting": round(formatting, 2),
        },
        "matched": matched,
        "missing": missing,
        "feedback": feedback,
    }


def generate_feedback(candidate, job, missing_skills, keyword_score, skills_context):
    """
    Generate actionable feedback for hiring team and candidate.
    """
    feedback = {
        "strengths": [],
        "weaknesses": [],
        "suggestions": [],
    }
    
    # Strengths
    action_verbs = candidate.get("action_verbs", [])
    if len(action_verbs) >= 5:
        feedback["strengths"].append(f"Strong action-oriented language: uses {len(action_verbs)} action verbs")
    
    metrics_data = candidate.get("metrics_data", {})
    if metrics_data.get("has_impact"):
        feedback["strengths"].append("Demonstrates quantifiable impact with metrics")
    
    if skills_context >= 70:
        feedback["strengths"].append("Skills mentioned in context of actual experience")
    
    # Weaknesses
    if keyword_score < 50:
        feedback["weaknesses"].append(f"Low keyword match score ({keyword_score:.1f}%)")
    
    if missing_skills:
        feedback["weaknesses"].append(f"Missing core skills: {', '.join(list(missing_skills)[:3])}")
    
    if skills_context < 40:
        feedback["weaknesses"].append("Skills listed but not demonstrated in experience bullets")
    
    if candidate.get("experience", 0) == 0:
        feedback["weaknesses"].append("Years of experience not detected in resume")
    
    education = candidate.get("education", [])
    if not education:
        feedback["weaknesses"].append("No education section found")
    
    # Suggestions
    if missing_skills:
        feedback["suggestions"].append(f"Consider adding experience or certifications in: {', '.join(list(missing_skills)[:2])}")
    
    if keyword_score < 60:
        feedback["suggestions"].append("Add job description keywords naturally in experience bullets")
    
    if len(action_verbs) < 3:
        feedback["suggestions"].append("Use more action verbs (Built, Designed, Optimized, Scaled, etc.)")
    
    if not metrics_data.get("has_impact"):
        feedback["suggestions"].append("Quantify achievements with metrics (%, time saved, revenue impact, etc.)")
    
    return feedback


def suggest_questions(candidate, job, missing_skills):
    """Generate professional role-specific interview questions with tiered difficulty."""
    questions = []

    cand_years = parse_experience_duration(candidate.get("experience", ""))
    job_min_years = job.get("min_experience", 0)
    candidate_skills = candidate.get("skills", [])
    job_skills = job.get("required_skills", [])
    matched_skills = list(set(candidate_skills) & set(job_skills))
    missing = list(missing_skills)
    focus_skill = matched_skills[0] if matched_skills else (job_skills[0] if job_skills else "this role")

    def q(level, subject, text):
        return {"level": level, "subject": subject, "question": text}

    # Easy: fundamentals and communication.
    if missing:
        questions.append(q("easy", missing[0], f"How would you build working proficiency in {missing[0]} within your first 60 days on this role?"))
    else:
        questions.append(q("easy", focus_skill, f"Explain the core concepts of {focus_skill} to a non-technical stakeholder and when you would use it."))

    questions.append(q("easy", "collaboration", "Describe a project where you partnered with product or business teams. How did you keep communication clear?"))

    # Moderate: delivery, trade-offs, execution quality.
    questions.append(q("moderate", focus_skill, f"Walk through a production project where you used {focus_skill}. What trade-offs did you make and why?"))

    metrics_data = candidate.get("metrics_data", {})
    if metrics_data.get("has_impact"):
        questions.append(q("moderate", "impact", "Share a feature you delivered with measurable outcomes. How did you define and track success metrics?"))
    else:
        questions.append(q("moderate", "impact", "When formal metrics are unavailable, how do you evaluate technical success and business value after release?"))

    # Difficult: system thinking, leadership, and risk management.
    questions.append(q("difficult", focus_skill, f"Design a scalable solution using {focus_skill} for high-throughput workloads. Which failure modes would you anticipate first?"))

    if cand_years >= job_min_years and job_min_years > 0:
        questions.append(q("difficult", "leadership", "Tell us about a critical technical decision you drove under ambiguity. How did you align stakeholders and mitigate delivery risk?"))
    else:
        questions.append(q("difficult", "growth", f"This role targets {job_min_years}+ years and you currently show {cand_years}. What is your plan to close that gap while maintaining delivery quality?"))

    return questions[:6]
