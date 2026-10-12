"""Checks of the Phase-1 code against cases with known answers."""
import numpy as np, warnings, tempfile, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")
from ase.build import bulk
from ase.io import write
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families, plain
from mofmorph.models import bfdh, describe
from mofmorph.shape import Shape

def from_atoms(at, name):
    p = os.path.join(tempfile.mkdtemp(), name + ".cif"); write(p, at); return load(p, name)

ok = True
def check(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg); ok &= bool(cond)

# 1. lattice types -> classic BFDH shapes
cases = [("Po simple cubic", bulk("Po", "sc", a=3.35), "cube"),
         ("Cu fcc", bulk("Cu", "fcc", a=3.61, cubic=True), "truncated octahedron"),
         ("Fe bcc", bulk("Fe", "bcc", a=2.87, cubic=True), "rhombic dodecahedron")]
for nm, at, expect in cases:
    c = from_atoms(at, nm.split()[0]); F = enumerate_faces(c, 4); s, _ = bfdh(F)
    check(describe(s) == expect, f"{nm}: {c.spacegroup} -> BFDH '{describe(s)}' (expected {expect})")

# 2. diamond: glide-plane absences beyond centring
c = from_atoms(bulk("Si", "diamond", a=5.431), "Si"); F = enumerate_faces(c, 4)
check(c.spacegroup == "Fd-3m", f"Si space group {c.spacegroup}")
check(F[(1, 1, 1)].order == 1, "Si (111) allowed")
check(F[(1, 0, 0)].order == 4, f"Si (100): first allowed reflection is (400) (got order {F[(1,0,0)].order})")
check(F[(1, 1, 0)].order == 2, "Si (110): first allowed reflection is (220)")
a = 5.431
check(abs(F[(1, 0, 0)].d_eff - a / 4) < 1e-6, "Si d_eff(100) = a/4")

# 3. descriptors of exact solids
def cube(): return Shape([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]], [1]*6, ["{100}"]*6)
def octa():
    N = [[x,y,z] for x in (1,-1) for y in (1,-1) for z in (1,-1)]; return Shape(N, [1]*8, ["{111}"]*8)
cu, oc = cube(), octa()
check(abs(cu.sphericity() - 0.8060) < 1e-3, f"cube sphericity {cu.sphericity():.4f}")
check(abs(oc.sphericity() - 0.8456) < 1e-3, f"octahedron sphericity {oc.sphericity():.4f}")
check(cu.kappa2() < 1e-12 and oc.kappa2() < 1e-12, "kappa^2 = 0 for cube and octahedron (exact)")
check(abs(cu.q_l(4) - 0.7638) < 1e-3 and abs(cu.q_l(6) - 0.3536) < 1e-3, f"cube Q4={cu.q_l(4):.4f}, Q6={cu.q_l(6):.4f}")
check(abs(oc.q_l(4) - 0.5092) < 1e-3 and abs(oc.q_l(6) - 0.6285) < 1e-3, f"octahedron Q4={oc.q_l(4):.4f}, Q6={oc.q_l(6):.4f}")
g = cu.gyration(); check(abs(g[0,0] - 1/3) < 1e-9, f"cube gyration diagonal {g[0,0]:.6f} (exact 1/3)")
print("\nALL PASS" if ok else "\nSOME FAILED")
