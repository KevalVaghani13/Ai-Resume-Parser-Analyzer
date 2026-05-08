import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser import extract_text_from_pdf, extract_name

files=['uploads/Priyanshi Vaghani.pdf','uploads/RESUME_VIDHI.pdf']
for f in files:
    print('='*60)
    print(f)
    print('='*60)
    t = extract_text_from_pdf(f)
    # Print first 500 chars to see structure
    print("First 500 chars of extracted text:")
    print(repr(t[:500]))
    print("\nFirst 20 lines:")
    lines = t.split('\n')[:20]
    for i, line in enumerate(lines):
        print(f"{i}: {repr(line)}")
    
    name = extract_name(t)
    print(f"\nExtracted name: {name}")
