import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import extract_text_from_pdf

t = extract_text_from_pdf('uploads/Priyanshi Vaghani.pdf')
print('contains 992:', '9924842064' in t)
print('contains 817:', '8178928361' in t)
print('contains 902:', '9023905565' in t)
for s in ['9924842064', '8178928361', '9023905565']:
    print('SEARCH', s, t.find(s))
print('--- digit lines ---')
for i, line in enumerate(t.splitlines()):
    if '9924842064' in line or '8178928361' in line or '9023905565' in line:
        print(i, repr(line))
