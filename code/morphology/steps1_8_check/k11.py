"""K11: after the bulk relaxation the relaxed primitive cell is written to CIF and read back, which
re-orients the lattice. primitive_miller() assumes the conventional and primitive cells share one
Cartesian frame, so it converts a conventional face to the wrong primitive plane."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import sys, json, numpy as np; sys.path.insert(0, sys.argv[1]); import mofwulff as mw
from pymatgen.core import Structure
out = {}
for name, cif, rel in [("HKUST-1", "Cu-BTC.cif", "HKUST-1"), ("Mg-MOF-74", "MgMOF-74.cif", "Mg-MOF-74")]:
    info = mw.standardize(f"{sys.argv[2]}/{cif}", 0.1, "majority")
    pr = Structure.from_file(f"{sys.argv[3]}/structures/{rel}/bulk_r800_f0.05.cif")
    fams = mw.face_families(info["conv"], info["rotations"], 1, 4)
    rows = []
    for f in fams:
        hkl = f["rep"]
        right = mw.primitive_miller(info["conv"], info["prim"], hkl)
        try: wrong = mw.primitive_miller(info["conv"], pr, hkl)
        except ValueError: wrong = "conversion fails -> unrelaxed conventional cell used (K3)"
        d_right = info["prim"].lattice.d_hkl(right)
        d_wrong = pr.lattice.d_hkl(wrong) if isinstance(wrong, tuple) else None
        rows.append(dict(face=f["name"], primitive_plane_correct=str(right), primitive_plane_used=str(wrong),
                         d_correct=round(d_right, 3), d_used=None if d_wrong is None else round(d_wrong, 3)))
        print(name, rows[-1])
    out[name] = rows
json.dump(out, open(_os.path.join(HERE, "k11_results.json"), "w"), indent=1)
