import requests
import json

# Test with second image-based PDF
file_path = 'uploads/RESUME_VIDHI.pdf'
with open(file_path, 'rb') as f:
    files = {
        'file': f,
    }
    data = {
        'job_title': 'Full Stack Developer',
        'job_description': 'Need React Node.js MongoDB Flutter experience with 2+ years development'
    }
    response = requests.post('http://127.0.0.1:8000/analyze/', files=files, data=data)

result = response.json()
print("API Response for RESUME_VIDHI.pdf:")
print(json.dumps({
    'candidate_name': result.get('candidate_name'),
    'email': result.get('email'),
    'mobile': result.get('mobile'),
    'location': result.get('location'),
    'match_percentage': result.get('match_percentage'),
    'skills_matched': result.get('matched_skills', [])[:5]
}, indent=2))
