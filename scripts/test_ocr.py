import sys
import os
# Ensure project root is on sys.path so imports work when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser import parse_resume, extract_text_from_pdf
files=['uploads/Priyanshi Vaghani.pdf','uploads/RESUME_VIDHI.pdf']
for f in files:
    print('---',f)
    try:
        data=parse_resume(f)
        print('name:',data.get('name'))
        print('email:',data.get('email'))
        print('mobile:',data.get('mobile'))
        t=extract_text_from_pdf(f)
        print('chars=',len(t))
    except Exception as e:
        print('ERROR',e)
