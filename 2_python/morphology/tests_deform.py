"""Checks for the cell-deformation module against exact answers."""
import numpy as np, warnings, tempfile, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); warnings.filterwarnings("ignore")
from ase import Atoms
from ase.io import write
from mofmorph.structure import load
from mofmorph.deform import stretch, bfdh_shape, extents, parameters, cell_from_parameters, habit
from mofmorph.models import describe
from mofmorph.faces import enumerate_faces, families
ok = True
def check(c, m):
    global ok; print(("PASS " if c else "FAIL ") + m); ok &= bool(c)
def crystal(at, name):
    p = os.path.join(tempfile.mkdtemp(), name + ".cif"); write(p, at); return load(p, name)

# 1. cell parameters round trip
L = cell_from_parameters(3, 4, 5, 80, 95, 110); a = parameters(L)
check(np.allclose(a, (3, 4, 5, 80, 95, 110)), f"cell parameters round trip {np.round(a, 6)}")

# 2. simple cubic point lattice, stretch c by 2: box with half-widths (2, 2, 1)... BFDH: R proportional to 1/length
po = crystal(Atoms("Po", cell=[3, 3, 3], pbc=True, scaled_positions=[[0, 0, 0]]), "Po")
d = stretch(po, lc=2.0); s, F = bfdh_shape(po, d)
e = extents(s)
check(len(po.rotations) == 48 and len(d.rotations) == 16, f"symmetry drops from m-3m to 4/mmm: {len(po.rotations)} -> {len(d.rotations)} operations")
check(np.allclose(e / e[2], [2, 2, 1], atol=1e-9),
      f"cube stretched 2x along c gives a plate, half-widths proportional to 1/length: {np.round(e / e.min(), 6)}")
check(abs(s.volume / (8 * 2 * 2 * 1) - 1) < 1e-9, f"it is exactly a box (volume {s.volume:.6f}, expected 32 in units of R_001)")
check(habit(s)[0] == "plate", f"habit of the stretched cube is '{habit(s)[0]}' (b/a={habit(s)[1]:.3f}, c/b={habit(s)[2]:.3f})")
r = stretch(po, lc=0.5); sr, _ = bfdh_shape(po, r)
check(habit(sr)[0] == "rod" and np.allclose(extents(sr) / extents(sr)[0], [1, 1, 2]), f"cube compressed 2x along c gives a rod, half-widths {np.round(extents(sr) / extents(sr)[0], 6)}")

# 3. allowed faces do not change under deformation (Proposition 14)
fcc = crystal(Atoms("Cu4", cell=[4, 4, 4], pbc=True, scaled_positions=[[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]]), "fcc")
d2 = stretch(fcc, la=1.3, lb=0.9, lc=1.7, gamma=80)
F0 = enumerate_faces(fcc, 4); F1 = enumerate_faces(d2, 4, absence_ops=(fcc.rotations, fcc.translations))
check(all(F0[k].order == F1[k].order for k in F0), "orders n of every face (hence the allowed set) unchanged by the deformation")

# 4. families split exactly as counting predicts: cubic {100} = 6 faces, tetragonal -> {100}:4 + {001}:2
d3 = stretch(po, lc=1.3); fam = families(enumerate_faces(d3, 1, absence_ops=(po.rotations, po.translations)))
sizes = sorted(f["multiplicity"] for f in fam if f["d_eff"] > 0 and f["family"] in [(1,0,0),(0,0,1),(0,1,0),(0,0,-1),(0,-1,0),(-1,0,0)])
check(sizes == [2, 4], f"cubic {{100}} (6 faces) splits under c-stretch into families of {sizes}")
n_c = {len(f["members"]) for f in families(enumerate_faces(po, 1))}
check(6 in n_c, "undeformed cube has a single 6-face {100} family")

# 5. uniform scaling does not change a BFDH shape
d4 = stretch(po, 2.0, 2.0, 2.0); s0, _ = bfdh_shape(po, po); s4, _ = bfdh_shape(po, d4)
check(abs(s0.sphericity() - s4.sphericity()) < 1e-9, "uniform scaling of the cell leaves the shape unchanged")

# 6. Proposition 16: in an orthogonal cell the BFDH polytope is a box unless some plane has n_f below the weighted mean of the axial orders
from ase.build import bulk
rng = np.random.default_rng(3)
parents = {"P": crystal(Atoms("Po", cell=[3, 3, 3], pbc=True, scaled_positions=[[0, 0, 0]]), "P3"),
           "I": crystal(bulk("Fe", "bcc", a=3.0, cubic=True), "I3"), "F": crystal(bulk("Cu", "fcc", a=3.6, cubic=True), "F3")}
bad = 0; cnt = {"box": 0, "cut": 0}
for cen, par in parents.items():
    for _ in range(25):
        la, lb, lc = np.exp(rng.uniform(-1.0, 1.0, 3))
        d = stretch(par, la, lb, lc); s, F = bfdh_shape(par, d)
        fams = families(F)[:40]
        n_ax = [F[(1, 0, 0)].order, F[(0, 1, 0)].order, F[(0, 0, 1)].order]
        a = np.linalg.norm(d.lattice, axis=1)
        cut = False
        for fam in fams:
            h = np.array(fam["members"][0].hkl, float); w = (h / a) ** 2; w = w / w.sum()
            if fam["order"] < float(w @ n_ax) - 1e-9:
                cut = True
        is_box = len(s.faces) == 6
        cnt["cut" if cut else "box"] += 1
        bad += (is_box == cut)
check(bad == 0, f"Proposition 16 criterion (box iff no plane with n_f < weighted mean of axial orders) agrees on 75 random cells ({cnt})")
print("\nALL PASS" if ok else "\nSOME FAILED")
