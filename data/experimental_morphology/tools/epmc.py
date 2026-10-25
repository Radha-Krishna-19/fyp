"""Europe PMC helpers.
  python -I epmc.py search "<query>" [n]      -> list hits with PMCID, DOI, open-access flag
  python -I epmc.py text PMCxxxx out.txt      -> full text (plain text from JATS XML)
"""
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import xml.etree.ElementTree as ET

import requests

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def search(q, n=15):
    r = requests.get(f"{BASE}/search", params={"query": q, "format": "json", "pageSize": n,
                                                "resultType": "lite"}, timeout=60)
    for h in r.json()["resultList"]["result"]:
        print(f"{h.get('pmcid','-'):12} {h.get('doi','-'):38} OA={h.get('isOpenAccess')} "
              f"{h.get('pubYear')} | {h.get('title','')[:110]}")


def text(pmcid, out):
    r = requests.get(f"{BASE}/{pmcid}/fullTextXML", timeout=120)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    parts = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("title", "p", "caption", "td", "th", "article-title", "label"):
            t = " ".join("".join(el.itertext()).split())
            if t:
                parts.append(("\n## " if tag == "title" else "") + t)
    s = "\n".join(parts)
    s = re.sub(r"\n{3,}", "\n\n", s)
    open(out, "w", encoding="utf-8").write(s)
    print(len(s), "chars")


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
    else:
        text(sys.argv[2], sys.argv[3])
