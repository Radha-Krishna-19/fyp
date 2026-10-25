"""Literature lookup through OpenAlex (no key).
  python -I lit.py doi <doi> [<doi> ...]     -> citation, OA status, OA url, abstract
  python -I lit.py find "<title words>" [n]  -> candidate works with DOI
  python -I lit.py pdf <url> <out.pdf>       -> download a PDF (untrusted data, stored only)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

H = {"User-Agent": "fyp-literature-curation/0.1"}


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = sorted((i, word) for word, idx in inv.items() for i in idx)
    return " ".join(word for _, word in pos)


def cite(w):
    auth = ", ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:8])
    if len(w.get("authorships", [])) > 8:
        auth += " et al."
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
    b = w.get("biblio") or {}
    pages = f"{b.get('first_page')}-{b.get('last_page')}" if b.get("first_page") else ""
    return f"{auth}, {src} {w.get('publication_year')}, {b.get('volume') or ''}, {pages}".strip(", ")


def doi(d):
    r = requests.get(f"https://api.openalex.org/works/https://doi.org/{d}", headers=H, timeout=60)
    if r.status_code != 200:
        print(f"== {d}: HTTP {r.status_code}")
        return
    w = r.json()
    oa = w.get("open_access") or {}
    locs = [l.get("pdf_url") for l in w.get("locations", []) if l.get("pdf_url")]
    print(f"== {d}\nTITLE: {w.get('title')}\nCITE: {cite(w)}\nOA: {oa.get('oa_status')} "
          f"{oa.get('oa_url')}\nPDFS: {locs[:4]}\nABSTRACT: {abstract(w)}\n")


def find(q, n=8):
    r = requests.get("https://api.openalex.org/works", headers=H, timeout=60,
                     params={"search": q, "per-page": n})
    for w in r.json()["results"]:
        print(f"{(w.get('doi') or '-').replace('https://doi.org/',''):40} "
              f"{w.get('publication_year')} OA={w['open_access']['oa_status']:7} "
              f"cit={w.get('cited_by_count')} | {w.get('title','')[:100]}")


def pdf(url, out):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
    ct = r.headers.get("content-type", "")
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        print(f"FAILED {r.status_code} {ct} {len(r.content)} bytes")
        sys.exit(1)
    open(out, "wb").write(r.content)
    print(f"saved {len(r.content)} bytes")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "doi":
        for d in sys.argv[2:]:
            doi(d)
    elif cmd == "find":
        find(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
    else:
        pdf(sys.argv[2], sys.argv[3])
