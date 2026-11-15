"""Relax the slabs whose CHGNet gamma came out <= 0 in the 14 Nov notebook, three ways.

  python relax_cases.py <module dir> <cif dir> <out dir> <variant>
variant  notebook : the notebook's own module, water caps (reproduces the notebook's relaxed gamma)
         fixed    : module with K3, K11 and the one-proton-per-donor healing fix, water caps and bare slabs
Bulk is relaxed exactly as in the notebook (800 steps, fmax 0.05); only the listed face is built.
"""
import sys, os, time
sys.path.insert(0, sys.argv[1])
import pandas as pd, mofwulff as mw
cifdir, out, variant = sys.argv[2], sys.argv[3], sys.argv[4]
CASES = [("ZnBDC", "ZnBDC", (0, 1, 0), 1), ("ZnBDC", "ZnBDC", (0, 0, 1), 1), ("ZnBDC", "ZnBDC", (0, 1, 1), 2),
         ("Cd3BTB2", "Cd3BTB2", (0, 1, 0), 1), ("MIL-47", "MIL-47", (1, 0, 0), 1),
         ("Mg-MOF-74", "MgMOF-74", (-2, 1, 0), 1)]
if len(sys.argv) > 5:
    CASES = [c for c in CASES if c[0] in sys.argv[5].split(",")]
eng = mw.Engine()
rows = []
for name, fn, hkl, k in CASES:
    for cap in (["water"] if variant == "notebook" else ["water", "bare"]):
        cfg = dict(symprec=0.1, disorder="majority", max_index=1, n_families=4, faces=[hkl], thickness=15.0,
                   vacuum=15.0, max_terms=8, cap=cap, relax_steps=800, fmax=0.05, relax_top_k=k)
        t = time.time()
        try:
            meta, fams, recs, bulk = mw.run_mof(eng, name, f"{cifdir}/{fn}.cif", out, **cfg)
        except Exception as e:
            print("FAILED", name, hkl, cap, type(e).__name__, e, flush=True); continue
        for r in recs:
            r["variant"] = variant
        rows += recs
        pd.DataFrame(rows).to_csv(f"{out}/relax_cases_{variant}.csv", index=False)
        print(f"DONE {name} {hkl} {cap} {time.time() - t:.0f}s", flush=True)
