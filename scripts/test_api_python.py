import requests
import json

# Test with image-based PDF
file_path = 'uploads/Priyanshi Vaghani.pdf'
with open(file_path, 'rb') as f:
    files = {
        'file': f,
    }
    data = {
        'job_title': 'UI/UX Designer',
        'job_description': 'Need UI/UX design experience with Figma and React'
    }
    response = requests.post('http://127.0.0.1:8000/analyze/', files=files, data=data)

result = response.json()
print("API Response:")
print(json.dumps({
    'candidate_name': result.get('candidate_name'),
    'email': result.get('email'),
    'mobile': result.get('mobile'),
    'location': result.get('location'),
    'match_percentage': result.get('match_percentage'),
    'skills_matched': result.get('matched_skills', [])[:5]
}, indent=2))
