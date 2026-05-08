import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser import extract_text_from_pdf, extract_mobile

f = 'uploads/RESUME_VIDHI.pdf'
t = extract_text_from_pdf(f)
print("All text:")
print(t)
print("\n" + "="*60)
print(f"Extracted mobile: {extract_mobile(t)}")
