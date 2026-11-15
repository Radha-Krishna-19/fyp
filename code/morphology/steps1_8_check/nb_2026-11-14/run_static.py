"""Steps 1-6 of the 14 Nov notebook on CPU: bulk relaxed (800 steps, fmax 0.05) as in the notebook,
slabs static only (relax_top_k=0). Gives n_water, area and static gamma per slab to compare with the notebook."""
import sys, json, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, mofwulff as mw
cifdir, out = sys.argv[1], sys.argv[2]
NAMES = [("ZIF-8", "ZIF-8"), ("HKUST-1", "Cu-BTC"), ("Mg-MOF-74", "MgMOF-74"), ("UiO-66", "UIO-66")] + \
        [(n, n) for n in "MOF-1-Dybtsev-dmol IRMOF-1 IRMOF-15 MIL-140A-DFT MIL-47 MOF-70 MIL-88A-open MIL-88B-open CoBDP Ni-DOBDC Cd3BTB2 ZnBDC".split()]
if len(sys.argv) > 3:
    want = sys.argv[3].split(","); known = dict(NAMES)
    NAMES = [(n, known.get(n, n)) for n in want]
cfg = dict(symprec=0.1, disorder="majority", max_index=1, n_families=4, thickness=15.0, vacuum=15.0,
           max_terms=8, cap="water", relax_steps=800, fmax=0.05, relax_top_k=0)
if len(sys.argv) > 4 and sys.argv[4] == "static_bulk":   # cell 9 STATIC_LIST: relax_steps=0 (bulk not relaxed)
    cfg.update(relax_steps=0)
eng = mw.Engine()
for name, fn in NAMES:
    t = time.time()
    try:
        meta, fams, recs, bulk = mw.run_mof(eng, name, f"{cifdir}/{fn}.cif", out, **cfg)
    except Exception as e:
        print(name, "FAILED", type(e).__name__, e, flush=True); continue
    pd.DataFrame(recs).to_csv(f"{out}/static_{name}.csv", index=False)
    print(f"DONE {name} {len(recs)} rows {time.time()-t:.0f}s", flush=True)
