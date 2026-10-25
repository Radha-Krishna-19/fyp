"""Extract text from a PDF. Usage: python -I pdf2txt.py in.pdf out.txt"""
import sys
from pypdf import PdfReader

r = PdfReader(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for i, p in enumerate(r.pages):
        f.write(f"\n\n===== PAGE {i+1} =====\n")
        f.write(p.extract_text() or "")
print(len(r.pages), "pages")
