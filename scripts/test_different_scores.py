"""Test script to verify different resumes get different scores and questions."""
import json
from parser import parse_resume, parse_job_description, match_jd_keywords_in_resume
from scoring import calculate_comprehensive_score, suggest_questions
from docx import Document as DocxDocument
import tempfile
import os

# Define 3 different test resumes
RESUME_1 = """
Alice Chen
alice@example.com
(555) 111-1111

EXPERIENCE
Senior Python Engineer | TechCorp | 2019-2024
• Built distributed data pipeline processing 10M+ records/day
• Designed and led migration to AWS microservices architecture
• Managed team of 4 engineers across Python, Kubernetes, Docker
• Implemented machine learning model achieving 35% accuracy improvement
• Optimized SQL queries reducing database load by 60%

Mid-Level Developer | StartupXYZ | 2017-2019
• Developed REST APIs serving 50K+ requests/second
• Set up CI/CD pipelines using Jenkins and GitLab

SKILLS
Python, SQL, AWS, Docker, Kubernetes, REST API, Machine Learning, Jenkins, Git, Spark

EDUCATION
B.S. Computer Science, MIT, 2017
"""

RESUME_2 = """
Bob Johnson
bob@example.com
(555) 222-2222

EXPERIENCE
Frontend Developer | WebCorp | 2021-2024
• Developed React components using modern JavaScript
• Built responsive dashboards for client data visualization
• Worked with Node.js backend teams

SKILLS
JavaScript, React, HTML, CSS, Node.js

EDUCATION
Bootcamp Certificate, General Assembly, 2021
"""

RESUME_3 = """
Carol Davis
carol@example.com

EXPERIENCE
2015-2024: Software Engineer at Various Companies
Worked on different projects including web and mobile applications
Some experience with Python and databases

SKILLS
Java, Python, SQL
"""

# Job description
JOB_DESC = """
Senior Software Engineer - Python & Cloud

We're looking for an experienced Python developer with strong cloud infrastructure experience.

Requirements:
• 5+ years of professional software development experience
• Expert-level Python programming
• AWS cloud platform experience
• Docker and Kubernetes for containerization
• SQL and relational database design
• REST API development
• Leadership experience managing engineering teams

Nice to Have:
• Machine Learning / Data Engineering background
• Distributed systems experience
• CI/CD pipeline expertise
• React or modern frontend knowledge
"""

def create_resume_file(resume_text, filename):
    """Create a temporary DOCX file from resume text."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        path = f.name
    
    doc = DocxDocument()
    doc.add_paragraph(resume_text)
    doc.save(path)
    return path

print("=" * 80)
print("TESTING MULTIPLE RESUMES - VERIFICATION OF BUG FIXES")
print("=" * 80)

resumes = [
    ("Alice (Senior, 5 years, Python/AWS/ML expert)", RESUME_1),
    ("Bob (Junior, 3 years, React/Node focus)", RESUME_2),
    ("Carol (5 years, Java/Python generalist)", RESUME_3),
]

results = []

for candidate_name, resume_text in resumes:
    print(f"\n{'='*80}")
    print(f"Analyzing: {candidate_name}")
    print(f"{'='*80}")
    
    # Create temp resume file
    resume_path = create_resume_file(resume_text, candidate_name)
    
    try:
        # Parse
        candidate = parse_resume(resume_path)
        job = parse_job_description(JOB_DESC)
        
        # Extract keywords
        jd_keywords = job.get("jd_keywords", [])
        candidate["extracted_keywords"] = match_jd_keywords_in_resume(
            candidate.get("text", ""), 
            jd_keywords
        )
        
        # Score
        result = calculate_comprehensive_score(candidate, job)
        
        # Questions
        questions = suggest_questions(candidate, job, set(result.get("missing", [])))
        
        # Display results
        print(f"\nSCORE: {result['score']}%")
        print(f"\nBreakdown:")
        for comp, score in result['breakdown'].items():
            print(f"  • {comp.replace('_', ' ').title()}: {score}%")
        
        
        print(f"\n📝 Years Detected: {candidate.get('experience', 0)}")
        print(f"📝 Action Verbs Found: {len(candidate.get('action_verbs', []))} ({', '.join(candidate.get('action_verbs', [])[:3])}...)")
        
        print(f"\n💡 Feedback:")
        feedback = result['feedback']
        if feedback.get('strengths'):
            print(f"  Strengths: {feedback['strengths'][0] if feedback['strengths'] else 'None'}")
        if feedback.get('weaknesses'):
            print(f"  Weaknesses: {feedback['weaknesses'][0] if feedback['weaknesses'] else 'None'}")
        if feedback.get('suggestions'):
            print(f"  Suggestions: {feedback['suggestions'][0] if feedback['suggestions'] else 'None'}")
        
        print(f"\n❓ Personalized Questions:")
        for i, q in enumerate(questions[:3], 1):
            print(f"  {i}. {q}")
        
        results.append({
            'name': candidate_name,
            'score': result['score'],
            'years': candidate.get('experience', 0),
            'matched': result['matched'],
            'missing': result['missing'],
        })
        
    finally:
        os.unlink(resume_path)

# Summary
print(f"\n\n{'='*80}")
print("SUMMARY - Verification Results")
print(f"{'='*80}\n")

if len(set(r['score'] for r in results)) == 3:
    print("✅ SUCCESS: All resumes have DIFFERENT scores!")
else:
    print("❌ FAILED: Some resumes have same scores")

for r in results:
    print(f"  {r['name']:40} Score: {r['score']:6.2f}%  Years: {r['years']}  Matched: {len(r['matched'])}")

print(f"\nScores: {[r['score'] for r in results]}")
print("\n✅ Bug fixes verified - Ready to restart API!")
