"""Debug script to see what's happening with parsing and scoring."""
import json
from parser import parse_resume, parse_job_description, match_jd_keywords_in_resume
from scoring import calculate_comprehensive_score, suggest_questions

# Sample test data
sample_resume_text = """
John Smith
john@example.com
(555) 123-4567

EXPERIENCE
Senior Software Engineer | TechCorp | 2020-2024
• Built a Python data pipeline that reduced processing time by 40%
• Designed AWS infrastructure serving 1M+ users
• Led team of 5 engineers on Docker containerization project
• Implemented REST APIs handling 10K requests/sec
• Optimized SQL queries improving performance by 3x

Mid-Level Developer | StartupXYZ | 2018-2020
• Developed React frontend for internal tools
• Set up CI/CD using Jenkins and Git
• Managed Kubernetes clusters with Docker containers

SKILLS
Python, SQL, AWS, Docker, Kubernetes, React, Node.js, REST API, Jenkins, Git, Machine Learning

EDUCATION
B.S. in Computer Science, University of Tech, 2018
"""

sample_jd = """
Senior Software Engineer - Python & Cloud

We're looking for an experienced Python developer with strong cloud experience.

Requirements:
• 5+ years of experience with Python
• AWS or cloud platform experience required
• SQL and database design knowledge
• Docker and Kubernetes expertise
• REST API development experience
• Leadership experience managing teams

Nice to have:
• Machine Learning background
• React or modern frontend framework
• CI/CD pipeline experience
• Distributed systems knowledge
"""

# Create fake file to parse
import tempfile
import os

# Test parsing
print("=" * 60)
print("TESTING PARSER")
print("=" * 60)

# Create temp resume file as DOCX
from docx import Document as DocxDocument

with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
    resume_path = f.name

doc = DocxDocument()
doc.add_paragraph(sample_resume_text)
doc.save(resume_path)

try:
    candidate = parse_resume(resume_path)
    print("\nCandidate parsed:")
    print(f"  Name: {candidate.get('name')}")
    print(f"  Email: {candidate.get('email')}")
    print(f"  Skills found: {candidate.get('skills')}")
    print(f"  Years of experience: {candidate.get('experience')}")
    print(f"  Action verbs: {candidate.get('action_verbs')}")
    print(f"  Metrics data: {candidate.get('metrics_data')}")
    print(f"  Experience bullets: {candidate.get('experience_bullets')[:2]}")
    print(f"  Formatting score: {candidate.get('formatting_score')}")
    
    job = parse_job_description(sample_jd)
    print("\n\nJob description parsed:")
    print(f"  Required skills: {job.get('required_skills')}")
    print(f"  JD keywords extracted: {job.get('jd_keywords')[:10]}")  # First 10
    print(f"  Min experience: {job.get('min_experience')}")
    
    # Now test matching
    print("\n\n" + "=" * 60)
    print("TESTING KEYWORD MATCHING")
    print("=" * 60)
    
    jd_keywords = job.get("jd_keywords", [])
    extracted = match_jd_keywords_in_resume(candidate.get("text", ""), jd_keywords)
    print(f"\nJD keywords: {jd_keywords[:15]}")
    print(f"Matched in resume: {extracted[:15]}")
    
    candidate["extracted_keywords"] = extracted
    
    # Now score
    print("\n\n" + "=" * 60)
    print("TESTING SCORING")
    print("=" * 60)
    
    result = calculate_comprehensive_score(candidate, job)
    print("\nScoring result:")
    print(json.dumps(result, indent=2))
    
    # Test questions
    print("\n\n" + "=" * 60)
    print("TESTING QUESTION GENERATION")
    print("=" * 60)
    
    questions = suggest_questions(candidate, job, set(result.get("missing", [])))
    print("\nGenerated questions:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

finally:
    os.unlink(resume_path)
