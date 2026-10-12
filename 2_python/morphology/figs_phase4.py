"""Figure: for each MOF, the three shape models side by side (Phase 3 attachment, Phase 3 broken-bond Wulff, Phase 4 UFF Wulff)."""
import sys, os, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
CIF = os.path.join(HERE, "..", "..", "1_website")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces
from mofmorph.models import from_rates, describe
from mofmorph import render
P3 = json.load(open(os.path.join(HERE, "results", "phase3_results.json"))); P4 = json.load(open(os.path.join(HERE, "results", "phase4_results.json")))
FN = {"MOF-5": "MOF5.cif", "HKUST-1": "HKUST-1.cif", "UiO-66": "UiO-66.cif", "ZIF-8": "ZIF-8.cif"}
fig = plt.figure(figsize=(10.5, 13))
for r, (name, fn) in enumerate(FN.items()):
    F = enumerate_faces(load(os.path.join(CIF, fn), name), 6)
    att = {k: v["E_att"] for k, v in P3[name]["faces"].items() if v["E_att"] > 0}
    bb = {k: v["gamma"] for k, v in P3[name]["faces"].items() if v["gamma"] > 0}
    uff = {k: v["gamma"] for k, v in P4[name]["faces"].items() if v["gamma"] > 0}
    for c, (rates, t) in enumerate([(att, "attachment energy (Phase 3)"), (bb, "broken-bond Wulff (Phase 3)"), (uff, "UFF cleavage Wulff (Phase 4)")]):
        s = from_rates(F, rates)
        ax = fig.add_subplot(4, 3, 3 * r + c + 1, projection="3d"); render.draw(ax, s, f"{name}\n{t}\n{describe(s, 0.01)}")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "results", "figs", "phase4_compare.png"), dpi=170, bbox_inches="tight")
print("ok")
