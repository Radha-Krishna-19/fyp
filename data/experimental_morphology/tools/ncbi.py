"""python -I ncbi.py <pmc number> out.txt : full text from NCBI efetch (PMC XML)."""
import re, sys, xml.etree.ElementTree as ET, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                 params={"db": "pmc", "id": sys.argv[1]}, timeout=120)
root = ET.fromstring(r.content)
parts = []
for el in root.iter():
    tag = el.tag.split("}")[-1]
    if tag in ("title", "p", "caption", "td", "th", "article-title"):
        t = " ".join("".join(el.itertext()).split())
        if t:
            parts.append(("\n## " if tag == "title" else "") + t)
s = "\n".join(parts)
open(sys.argv[2], "w", encoding="utf-8").write(s)
print(len(s), "chars")
