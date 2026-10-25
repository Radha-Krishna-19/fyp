"""Combine BFDH (R ~ 1/d_eff) and Wulff (R ~ gamma): hybrid R = Rb^(1-w) * Rw^w, geometric blend.
All models use the SAME faces (those with a UFF gamma) so the comparison is fair."""
import sys, os, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import numpy as np
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families
from mofmorph.models import from_rates, describe, bfdh
CIF = os.path.join(HERE, "..", "..", "website")
P4 = json.load(open(os.path.join(HERE, "results", "phase4_results.json")))
FN = {"MOF-5": "MOF5.cif", "HKUST-1": "HKUST-1.cif", "UiO-66": "UiO-66.cif", "ZIF-8": "ZIF-8.cif"}
out = {}
for name, fn in FN.items():
    F = enumerate_faces(load(os.path.join(CIF, fn), name), 6)
    fam = {f["label"]: f for f in families(F)}
    fam.update({f["label"].rstrip("+-"): f for f in families(F) if f["label"].rstrip("+-") not in fam})
    gam = {k: v["gamma"] for k, v in P4[name]["faces"].items() if v["gamma"] > 0}
    dj = {k: fam[k]["d_eff"] for k in gam}
    Rb = {k: max(dj.values()) / dj[k] for k in gam}; mb = min(Rb.values()); Rb = {k: v / mb for k, v in Rb.items()}
    mg = min(gam.values()); Rw = {k: v / mg for k, v in gam.items()}
    res = {"gamma": gam, "R_bfdh": {k: round(float(v), 3) for k, v in Rb.items()}, "R_wulff": {k: round(float(v), 3) for k, v in Rw.items()}}
    full, _ = bfdh(F, 40); res["bfdh_full40"] = describe(full, 0.01)
    res["shapes"] = {}
    for w in (0, 0.25, 0.5, 0.75, 1):
        R = {k: Rb[k] ** (1 - w) * Rw[k] ** w for k in gam}
        s = from_rates(F, R); sm = s.summary()
        res["shapes"][str(w)] = dict(name=describe(s, 0.01), sphericity=round(sm["sphericity"], 3),
                                     faces={k: round(float(v), 3) for k, v in sm["face_area_fraction"].items() if v > 0.005})
    out[name] = res
    print(f"\n{name}  BFDH(40 fams)={res['bfdh_full40']}\n  R_bfdh={res['R_bfdh']}\n  R_wulff={res['R_wulff']}")
    for w, v in res["shapes"].items():
        print(f"  w={w:5s} {v['name']:28s} sph={v['sphericity']} {v['faces']}")
json.dump(out, open(os.path.join(HERE, "results", "hybrid_results.json"), "w"), indent=1)
