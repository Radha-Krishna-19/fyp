"""Every surface-energy model of the project as a point (x, y) = (g110/g100, g111/g100) on the cubic map.
Distances are used where a model gives growth distances (BFDH 1/d_eff, attachment energy E_att).
Tetrahedral splits {111}+/{111}- (UiO-66 F-43m, ZIF-8 I-43m) use the lower of the two."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import json, sys, os
_A = sys.argv[1:]
REPO = _A[0] if len(_A) > 0 else REPO_ROOT
KQ = _A[1] if len(_A) > 1 else _os.path.join(HERE, '..', 'steps1_8_check', 'results_quick', 'wulff_summary_all.csv')
KF = _A[2] if len(_A) > 2 else _os.path.join(HERE, '..', 'steps1_8_check', 'results_full_fixed', 'wulff_summary_ZIF-8.csv')
R = os.path.join(REPO, "code", "morphology", "results")
p3 = json.load(open(os.path.join(R, "phase3_results.json"))); p4 = json.load(open(os.path.join(R, "phase4_results.json")))
ch = json.load(open(os.path.join(R, "chgnet_cleavage_results.json")))
def get(fd, fam, field=None):
    vals = [(v if field is None else v[field]) for k, v in fd.items() if k.strip("+-") == fam]
    return min(vals) if vals else None
pts = {}
for m in ["MOF-5", "HKUST-1", "UiO-66", "ZIF-8"]:
    f3 = p3[m]["faces"]; P = {}
    d = {k: 1.0 / get(f3, k, "d_eff") for k in ("{100}", "{110}", "{111}")}
    P["BFDH"] = d
    P["Attachment energy"] = {k: get(f3, k, "E_att") for k in ("{100}", "{110}", "{111}")}
    P["Broken-bond Wulff"] = {k: get(f3, k, "gamma") for k in ("{100}", "{110}", "{111}")}
    P["UFF Wulff"] = {k: get(p4[m]["faces"], k, "gamma") for k in ("{100}", "{110}", "{111}")}
    if m in ch: P["CHGNet cleavage (Oct)"] = {k: get(ch[m]["all_slabs"]["gamma"], k) for k in ("{100}", "{110}", "{111}")}
    pts[m] = {name: dict(x=v["{110}"] / v["{100}"], y=v["{111}"] / v["{100}"], g=v) for name, v in P.items()}
import csv
for label, path in (("Kshitij CHGNet, static", KQ), ("Kshitij CHGNet, relaxed", KF)):
    if not path or not os.path.exists(path): continue
    for r in csv.DictReader(open(path)):
        if r["mof"] in pts and r.get("gamma_100") and r.get("gamma_110") and r.get("gamma_111"):
            g = {k: float(r[f"gamma_{k}"]) for k in ("100", "110", "111")}
            pts[r["mof"]][label] = dict(x=g["110"] / g["100"], y=g["111"] / g["100"], g=g)
# Exact shape and area fractions of each point (added so possible_morphs.py and figures.py can read them).
from cubic_wulff import shape as _shape
for _m, _P in pts.items():
    for _name, _v in _P.items():
        _g = _v["g"]; _k = ("{100}", "{110}", "{111}") if "{100}" in _g else ("100", "110", "111")
        _v["exact"], _v["fr"] = _shape(_g[_k[0]], _g[_k[1]], _g[_k[2]])
json.dump(pts, open(_os.path.join(HERE, "model_points.json"), "w"), indent=1)
for m, P in pts.items():
    for k, v in P.items(): print(f"{m:8s} {k:28s} x={v['x']:.3f} y={v['y']:.3f}")
