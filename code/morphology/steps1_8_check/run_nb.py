"""Runs cell 5 (steps 1-6 and 8) of Kshitij's MOF_Wulff_steps1-8.ipynb unchanged, outside Colab.
usage: python run_nb.py <mofwulff dir> <cif dir> <out dir> <quick|full> [MOF,MOF]"""
import sys, json, re, os, torch; torch.set_num_threads(2)
sys.path.insert(0, sys.argv[1]); import mofwulff as mw
import pandas as pd
CIFD, OUT_DIR, MODE = sys.argv[2], sys.argv[3], sys.argv[4]
ONLY = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()
os.makedirs(OUT_DIR, exist_ok=True)
MOFS = pd.DataFrame([
    dict(mof="ZIF-8", source="ZIF-8.cif", reference_habit="rhombic dodecahedron {110}"),
    dict(mof="HKUST-1", source="Cu-BTC.cif", reference_habit="octahedron {111}"),
    dict(mof="Mg-MOF-74", source="MgMOF-74.cif", reference_habit="hexagonal rods/needles along c"),
    dict(mof="UiO-66", source="UIO-66.cif", reference_habit="octahedron {111}")])
QUICK_TEST = MODE == "quick"
# notebook defaults (cell 4)
cfg = dict(symprec=0.1, disorder="majority", max_index=1, n_families=4, thickness=15.0, vacuum=15.0,
           max_terms=8, cap="water", relax_steps=0 if QUICK_TEST else 800, fmax=0.05, relax_top_k=int(os.environ.get("TOPK", "2")))
eng = mw.Engine(device="cpu")
ALL, SUMMARY = [], []
for _, r in MOFS.iterrows():
    name = r["mof"]
    if ONLY and name not in ONLY: continue
    meta, fams, recs, bulk = mw.run_mof(eng, name, f"{CIFD}/{r['source']}", OUT_DIR, faces=None, **cfg)
    ALL += recs
    row, w = mw.wulff_report(meta, fams, recs, OUT_DIR, "water", need_relaxed=not QUICK_TEST)
    row.update(reference_habit=r["reference_habit"], bulk_converged=bulk["converged"],
               n_unconverged=sum(1 for x in recs if x.get("converged") is False),
               n_rejected=sum(1 for x in recs if str(x.get("status", "")).startswith("rejected")),
               notes="; ".join(meta["notes"]))
    if w is not None:
        row["wulff_vertices"] = json.dumps(w["vertices"].round(5).tolist())
    SUMMARY.append(row)
    tag = "_".join(sorted(ONLY)) if ONLY else "all"
    pd.DataFrame(ALL).to_csv(f"{OUT_DIR}/slabs_{tag}.csv", index=False)
    pd.DataFrame(SUMMARY).to_csv(f"{OUT_DIR}/wulff_summary_{tag}.csv", index=False)
    print("SUMMARY", {k: v for k, v in row.items() if k not in ("wulff_vertices", "notes")}, flush=True)
