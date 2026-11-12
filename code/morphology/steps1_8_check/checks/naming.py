"""Check name_habit() of mofwulff.py against the exact Wulff geometry of a cubic {100}+{111} crystal.
r = gamma111/gamma100. Exact: r >= sqrt3 cube; 2/sqrt3 < r < sqrt3 truncated cube; r = 2/sqrt3 cuboctahedron;
1/sqrt3 < r < 2/sqrt3 truncated octahedron; r <= 1/sqrt3 octahedron."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import sys, numpy as np, json; sys.path.insert(0, sys.argv[1]); import mofwulff as mw
from pymatgen.core import Lattice, Structure
conv = Structure(Lattice.cubic(10), ["H"], [[0,0,0]])
rots = [np.array(R) for R in __import__('itertools').chain()]
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
rots = []
for op in SpacegroupAnalyzer(Structure(Lattice.cubic(10), ["H"], [[0,0,0]])).get_symmetry_operations():
    R = np.round(op.rotation_matrix).astype(int)
    if not any(np.array_equal(R,q) for q in rots): rots.append(R)
fams = mw.face_families(conv, rots, 1, 6)
s3 = 3**0.5
def exact(r):
    if r >= s3-1e-9: return "cube"
    if abs(r-2/s3) < 1e-6: return "cuboctahedron"
    if r > 2/s3: return "truncated_cube"
    if r > 1/s3+1e-9: return "truncated_octahedron"
    return "octahedron"
rows = []
for r in [0.55, 0.62, 0.70, 0.80, 0.873, 0.95, 1.05, 1.10, 2/s3, 1.20, 1.35, 1.50, 1.65, 1.80]:
    w = mw.wulff(conv, fams, {"100": 1.0, "111": r, "110": 10.0}, rots)
    nm = mw.name_habit(w, fams, "cubic", conv)
    fr = {k: round(v,3) for k,v in w["area_fractions"].items()}
    rows.append((round(r,3), fr.get("100",0), fr.get("111",0), nm, exact(r), nm == exact(r)))
    print(f"r={r:.3f}  f100={fr.get('100',0):.3f} f111={fr.get('111',0):.3f}  name_habit={nm:22s} exact={exact(r):22s} {'OK' if nm==exact(r) else 'WRONG'}")
json.dump(rows, open(_os.path.join(HERE, "naming_check.json"),"w"), indent=1)
