import sys, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for q in sys.argv[1:]:
    print("###", q)
    r = requests.get("https://api.openalex.org/works", timeout=60, headers={"User-Agent":"fyp"},
        params={"search": q, "filter": "is_oa:true,type:article", "per-page": 12, "sort": "cited_by_count:desc"})
    for w in r.json()["results"]:
        print(f"  {(w.get('doi') or '-').replace('https://doi.org/',''):38} {w.get('publication_year')} cit={w.get('cited_by_count'):<5} {w['open_access']['oa_url']}\n      {w.get('title','')[:120]}")
