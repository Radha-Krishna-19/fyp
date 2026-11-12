"""Check: when a face family is simply missing from the list, mofwulff.wulff() reports an unbounded
shape and name_habit() calls it a rod/needle. Uses Kshitij's own Mg-MOF-74 static run (quick)."""
import sys, json, numpy as np; sys.path.insert(0, sys.argv[1]); import mofwulff as mw
from pymatgen.core import Structure, Lattice
meta = json.load(open(sys.argv[2] + "/cache/Mg-MOF-74/meta.json"))
import csv
row = [r for r in csv.DictReader(open(sys.argv[2] + "/wulff_summary_all.csv")) if r["mof"] == "Mg-MOF-74"][0]
info = mw.standardize(sys.argv[3] + "/MgMOF-74.cif", 0.1, "majority")
fams = mw.face_families(info["conv"], info["rotations"], 1, 4)
conv = Structure(Lattice(meta["conv_lattice"]), ["H"], [[0, 0, 0]])
g_all = {f["key"]: float(row["gamma_" + f["key"]]) for f in fams}
print("all four families:", g_all, "->", mw.name_habit(mw.wulff(conv, fams, g_all, info["rotations"]), fams, "trigonal", conv))
for drop in ("001", "101"):
    g = {k: v for k, v in g_all.items() if k != drop}
    print(f"without {{{drop}}}:", mw.name_habit(mw.wulff(conv, fams, g, info["rotations"]), fams, "trigonal", conv))
g = {k: v for k, v in g_all.items() if k not in ("001", "101")}
print("without {001} and {101}:", mw.name_habit(mw.wulff(conv, fams, g, info["rotations"]), fams, "trigonal", conv))
