"""PROPOSAL ONLY (not the team's final code): Isha's v4 morphology-spectrum cells (14 to 14c, morphspec.py, unchanged
except for file paths) added to the corrected notebook of 15 November, plus the 4-line `bounded=` option in wulff()
that v4 introduced. Writes MOF_Wulff_v4_spectrum_plus_corrections_PROPOSAL.ipynb next to this file.

Run from this folder:  python make_merged_notebook.py
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
V4 = json.load(open(HERE.parent / "MOF_Wulff_steps1-8_plus_GNN_v4.ipynb"))
COR = json.load(open(HERE.parent.parent / "nb_2026-11-14" / "MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb"))

def src(c): return "".join(c["source"])
def setsrc(c, s): c["source"] = s.splitlines(keepends=True)

cells = [json.loads(json.dumps(c)) for c in COR["cells"]]
# 1. the corrected mofwulff cell gets v4's bounded= option (identical lines to v4)
mw = next(c for c in cells if src(c).startswith("%%writefile mofwulff.py"))
s = src(mw)
s = s.replace("def wulff(conv, families, gammas, rotations):", "def wulff(conv, families, gammas, rotations, bounded=None):", 1)
old = ("    for d in DIRS[::4]:\n        res = linprog(-d, A_ub=A, b_ub=bvec, bounds=[(None, None)] * 3, method=\"highs\")\n"
       "        if res.status == 3:\n            open_dirs.append(d)")
new = ("    if bounded is not True:\n        for d in DIRS[::4]:\n"
       "            res = linprog(-d, A_ub=A, b_ub=bvec, bounds=[(None, None)] * 3, method=\"highs\")\n"
       "            if res.status == 3:\n                open_dirs.append(d)")
assert old in s, "wulff() body not found"
setsrc(mw, s.replace(old, new, 1))
# 2. Isha's spectrum cells, paths adapted to the corrected notebook (BASE, CIF_DIR)
spec = [json.loads(json.dumps(c)) for c in V4["cells"][23:28]]
for c in spec:
    s = src(c)
    s = s.replace("%%writefile /content/morphspec.py", "%%writefile morphspec.py")
    s = s.replace('sys.path.insert(0, "/content")', "sys.path.insert(0, BASE)")
    s = s.replace('"/content/cifs/Mg-MOF-74.cif"', 'CIF_DIR + "/Mg-MOF-74.cif"')
    s = s.replace('"/content/cifs/', 'CIF_DIR + "/')
    s = s.replace('cif = "/content/" + fname', "cif = os.path.join(BASE, fname)")
    setsrc(c, s)
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None
rep = next(i for i, c in enumerate(cells) if src(c).startswith("## What to report"))
cells = cells[:rep] + spec + cells[rep:]
nb = dict(COR); nb["cells"] = cells
out = HERE / "MOF_Wulff_v4_spectrum_plus_corrections_PROPOSAL.ipynb"
json.dump(nb, open(out, "w"), indent=1)
print("wrote", out, len(cells), "cells")
