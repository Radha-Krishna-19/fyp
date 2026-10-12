"""Phase 4 checks against exact answers."""
import numpy as np, warnings, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); warnings.filterwarnings("ignore")
from ase.build import bulk
from mofmorph.forcefield import *
from mofmorph.forcefield import KCAL
ok = True
def check(c, m):
    global ok; print(("PASS " if c else "FAIL ") + m); ok &= bool(c)

# 1. simple cubic, one bond per cell edge, no LJ: gamma = D_bond/(2 a^2) for every (100)
a = 3.0
at = bulk("Zn", "sc", a=a)
i, j, d, D, bonded, excl = pair_list(at, rcut=3.5, bond_scale=1.3)
cov = 1.22
print("pairs", len(i), "bonded", bonded.sum())
at2 = at.copy()
cost = pair_energies(at2, i, j, d, bonded, excl)
g, s, dsp, _ = surface_energy(at2, (1, 0, 0), pairs=(i, j, D, np.where(bonded, D_BOND, 0.0)))
exact = 0.5 * D_BOND / a**2 * KCAL * 1000 / 6.02214076e23 * 1e20
check(abs(g - exact) / exact < 1e-9, f"sc (100): gamma {g:.4f} J/m2 = D/(2a^2) = {exact:.4f}")
# (110): crossed bonds per cell: 2 of 3 axes cross; spacing a/sqrt2; gamma = 0.5*(d/V)*2*D
g110 = surface_energy(at2, (1, 1, 0), pairs=(i, j, D, np.where(bonded, D_BOND, 0.0)))[0]
ex110 = 0.5 * (a / np.sqrt(2)) / a**3 * 2 * D_BOND * KCAL * 1000 / 6.02214076e23 * 1e20
check(abs(g110 - ex110) / ex110 < 1e-9, f"sc (110): gamma {g110:.4f} = {ex110:.4f}")

# 3. LJ crystal: periodic formula vs explicit brute force (pairs across a plane of a big supercell)
from ase.neighborlist import neighbor_list
fcc = bulk("Cu", "fcc", a=4.7, cubic=True)
i, j, d, D, bonded, excl = pair_list(fcc, rcut=9.0, bond_scale=0.5)     # nothing bonded: pure LJ
cost = pair_energies(fcc, i, j, d, bonded, excl)
g100, s100, dsp, _ = surface_energy(fcc, (1, 0, 0), pairs=(i, j, D, cost))
big = fcc.repeat((2, 2, 10)); z = big.get_positions()[:, 2]
I, J, dd, DD = neighbor_list("ijdD", big, 9.0)
pi = z[I]; pj = pi + DD[:, 2]
zc = s100 + 5 * dsp          # a plane well inside, at the same termination offset
cross = (np.minimum(pi, pj) < zc) & (np.maximum(pi, pj) > zc) & (I < J)
sym = np.array(big.get_chemical_symbols()); x, Dw = UFF["Cu"]
lj = Dw * ((x / dd) ** 12 - 2 * (x / dd) ** 6)
area = big.cell[0][0] * big.cell[1][1]
brute = -lj[cross].sum() / area * KCAL * 1000 / 6.02214076e23 * 1e20     # cost of one cut, J/m^2 (two surfaces)
check(abs(0.5 * brute - g100) / g100 < 0.02, f"LJ fcc (100): periodic formula {g100:.5f} vs brute-force slab cut {0.5*brute:.5f} J/m2")
g111 = surface_energy(fcc, (1, 1, 1), pairs=(i, j, D, cost))[0]; g110 = surface_energy(fcc, (1, 1, 0), pairs=(i, j, D, cost))[0]
check(g111 < g100 < g110, f"LJ fcc ordering gamma111 < gamma100 < gamma110: {g111:.5f} < {g100:.5f} < {g110:.5f}")
print("ALL PASS" if ok else "SOME FAILED")
