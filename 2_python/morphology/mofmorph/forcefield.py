"""Phase 4: unrelaxed cleavage (surface) energy of a crystal plane from a pairwise force field.

Model (all stated, nothing hidden):
  * van der Waals: UFF Lennard-Jones, E(r) = D [ (x/r)^12 - 2 (x/r)^6 ], Lorentz-Berthelot-like
    UFF mixing D_ij = sqrt(D_i D_j), x_ij = sqrt(x_i x_j). Pairs closer than two bonds apart
    (1-2 and 1-3) are excluded, as in UFF.
  * bonds: every bond cut by the plane costs a flat energy D_bond (UFF uses 70 kcal/mol as its
    Morse well depth). Bonds are perceived from covalent radii.
  * the cut is UNRELAXED (atoms stay where they were) and has NO electrostatics.
So gamma is an upper bound on a relaxed surface energy and, for charged frameworks such as UiO-66,
a poor absolute number; only the relative ordering of faces is the intended use.

Exact counting. For a family with plane normal n and lattice spacing d, planes sit at offsets
s + k d. A pair (i, j + T) with projections p_i, p_j is cut by a plane when s + k d lies between
them. If one unit cell of volume V holds all pairs once, planes of one-per-period have total area
V/d per cell, so   gamma(s) = (1/2) (d / V) * sum_pairs eps_pair * c_pair(s),
c = number of planes crossed, the factor 1/2 because a cut makes two surfaces.
"""
import numpy as np
from ase.data import covalent_radii, atomic_numbers
from ase.neighborlist import neighbor_list

KCAL = 4.184  # kJ per kcal
# UFF (x1 [A], D1 [kcal/mol]) Rappe et al. 1992, Table 1
UFF = {"H": (2.886, 0.044), "C": (3.851, 0.105), "N": (3.660, 0.069), "O": (3.500, 0.060),
       "Zn": (2.763, 0.124), "Zr": (3.124, 0.069), "Cu": (3.495, 0.005), "Hf": (3.141, 0.072)}
D_BOND = 70.0  # kcal/mol, UFF default Morse well depth


def pair_list(atoms, rcut=12.0, bond_scale=1.15):
    """All unique pairs (i<j images counted once) with distance, direction vector, bonded flag,
    and 'excluded' flag (1-2 or 1-3)."""
    i, j, d, D = neighbor_list("ijdD", atoms, rcut)
    cov = covalent_radii[atoms.numbers]
    bonded = d < bond_scale * (cov[i] + cov[j])
    n = len(atoms)
    # 1-2 / 1-3 exclusion works on the image-resolved graph: use (atom, image) pairs via supercell trick
    # Simpler and exact for these cells: bonds are short, so exclusion = bonded or sharing a bonded neighbour.
    # a 1-3 pair is two bonds apart; with images, check by position: pair (i, j) with vector D is 1-3 when
    # some k bonded to both with consistent vectors. Do it with explicit neighbour vectors.
    nb = {}
    for a, b, v in zip(i[bonded], j[bonded], D[bonded]):
        nb.setdefault(a, []).append((b, v))
    excl = bonded.copy()
    # vectorised 1-3: for every atom a and every pair of its bonds (b1,v1),(b2,v2), the pair (b1,b2) with vector v2-v1
    one3 = {}
    for a, lst in nb.items():
        for (b1, v1) in lst:
            for (b2, v2) in lst:
                if b1 == b2 and np.allclose(v1, v2):
                    continue
                one3.setdefault((b1, b2), []).append(v2 - v1)
    for idx, (a, b, v) in enumerate(zip(i, j, D)):
        if excl[idx]:
            continue
        for w in one3.get((a, b), ()):
            if np.allclose(v, w, atol=1e-3):
                excl[idx] = True
                break
    keep = i < j
    # pairs with i == j (an atom and its own periodic image) appear twice with +-D; keep one of them
    same = (i == j)
    first = same & (D @ np.array([1.0, 1.0e-3, 1.0e-6]) > 0)
    keep = keep | first
    return i[keep], j[keep], d[keep], D[keep], bonded[keep], excl[keep]


def pair_energies(atoms, i, j, d, bonded, excl, d_bond=D_BOND):
    """Cost (kcal/mol) of cutting each pair: -E_LJ for non-excluded non-bonded pairs, d_bond for bonds."""
    sym = np.array(atoms.get_chemical_symbols())
    x = np.array([UFF[s][0] for s in sym]); Dw = np.array([UFF[s][1] for s in sym])
    xij = np.sqrt(x[i] * x[j]); Dij = np.sqrt(Dw[i] * Dw[j])
    lj = Dij * ((xij / d) ** 12 - 2 * (xij / d) ** 6)
    cost = np.where(bonded, d_bond, np.where(excl, 0.0, -lj))
    cost = np.where((~bonded) & (~excl) & (d < 0.8 * xij), 0.0, cost)   # ignore overlapping non-bonded contacts
    return cost


def cleavage_curve(atoms, n, i, j, D, cost, d, nbins=400):
    """gamma(s) in kJ/mol per A^2 ... returned in J/m^2. n = unit normal (Cartesian). d = plane spacing."""
    p = atoms.get_positions() @ n
    pa = p[i]; pb = pa + D @ n
    lo = np.minimum(pa, pb); hi = np.maximum(pa, pb)
    s_grid = (np.arange(nbins) + 0.5) / nbins * d
    E = np.zeros(nbins)
    # count planes s + k d in (lo, hi): floor((hi - s)/d) - floor((lo - s)/d)
    for b, s in enumerate(s_grid):
        c = np.floor((hi - s) / d) - np.floor((lo - s) / d)
        E[b] = np.sum(cost * c)
    V = abs(np.linalg.det(atoms.cell[:]))
    gamma = 0.5 * (d / V) * E                    # kcal/mol per A^2
    return s_grid, gamma * KCAL * 1000 / 6.02214076e23 * 1e20  # J/m^2


def surface_energy(atoms, hkl, pairs=None, **kw):
    """Minimum over termination offsets of the cleavage energy of the plane family (hkl) in J/m^2."""
    if pairs is None:
        i, j, d, D, bonded, excl = pair_list(atoms, **kw)
        cost = pair_energies(atoms, i, j, d, bonded, excl)
        pairs = (i, j, D, cost)
    i, j, D, cost = pairs
    B = np.linalg.inv(atoms.cell[:]).T
    g = np.array(hkl, float) @ B
    dsp = 1.0 / np.linalg.norm(g); n = g * dsp
    s, gam = cleavage_curve(atoms, n, i, j, D, cost, dsp)
    return float(gam.min()), float(s[gam.argmin()]), dsp, gam
