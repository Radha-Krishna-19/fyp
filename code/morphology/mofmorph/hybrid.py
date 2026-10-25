"""Face energies for ANY crystal system (not only cubic) and the BFDH / Wulff / hybrid shapes.

Every symmetry family of faces (from faces.families) gets its own UFF cleavage energy, computed
on the SAME standardized cell that the Miller indices refer to, so no cubic assumption is made.
"""
import numpy as np
from ase import Atoms
from ase.build import make_supercell
from .structure import load
from .faces import enumerate_faces, families

from .forcefield import pair_list, pair_energies, surface_energy


def family_names(fams):
    """Plain label like {111}; if two different families share a label (non-cubic cells) add the
    representative direction, e.g. {100}[0,0,1]."""
    cnt = {}
    for f in fams:
        cnt[f["label"]] = cnt.get(f["label"], 0) + 1
    return [f["label"] if cnt[f["label"]] == 1 else f"{f['label']}[{','.join(map(str, f['family']))}]" for f in fams]


def atoms_for_energy(path, c):
    """All atoms of the file (hydrogens included) in a cell whose basis is the conventional basis
    that c's Miller indices refer to.

    structure.load() may find the symmetry only after dropping H (ZIF-8 is such a case) and then
    returns an H-free crystal. Energies must still see every atom, so the file's own atoms are
    re-expressed in the conventional basis (an integer supercell of the file cell). If that is not
    possible (the file holds a supercell of the conventional cell) the crystal's own atoms are used
    and a warning is printed."""
    import warnings
    import spglib
    from ase.io import read
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        at = read(path)
    if c.used_hydrogen or "H" not in at.get_chemical_symbols():
        return Atoms(numbers=c.numbers, scaled_positions=c.frac, cell=c.lattice, pbc=True)
    noh = at[[s != "H" for s in at.get_chemical_symbols()]]
    d = spglib.get_symmetry_dataset((noh.cell[:], noh.get_scaled_positions(), noh.numbers), symprec=c.symprec)
    P = np.array(d.transformation_matrix, float)
    Lc = (at.cell[:].T @ np.linalg.inv(P)).T            # conventional basis in the file's frame
    M = Lc @ np.linalg.inv(at.cell[:])
    if not np.allclose(M, np.rint(M), atol=1e-4):
        print(f"  warning: {path}: conventional cell is not an integer multiple of the file cell; "
              "energies use the H-free structure")
        return Atoms(numbers=c.numbers, scaled_positions=c.frac, cell=c.lattice, pbc=True)
    big = make_supercell(at, np.rint(M).astype(int))
    big.wrap()
    return big


def uff_gammas(path, name, n_families=24, max_index=6, min_cell=None, rcut=12.0, verbose=True):
    """Returns (faces, fams, names, gamma) with gamma[name] in J/m^2 for the n_families widest-spaced families."""
    c = load(path, name)
    F = enumerate_faces(c, max_index)
    fams = families(F)[:n_families]
    names = family_names(fams)
    atoms = atoms_for_energy(path, c)
    i, j, d, D, bonded, excl = pair_list(atoms, rcut=rcut)
    cost = pair_energies(atoms, i, j, d, bonded, excl)
    gamma = {}
    for f, nm in zip(fams, names):
        g = surface_energy(atoms, f["family"], pairs=(i, j, D, cost))[0]
        if verbose:
            print(f"  {nm:18s} d={f['d']:7.3f}  gamma={g:.4f} J/m2")
        if g > 0:
            gamma[nm] = float(g)
    return F, fams, names, gamma, c


def rates(fams, names, gamma, w):
    """Hybrid rate per family: Rb^(1-w) * Rw^w (w=0 BFDH, w=1 Wulff), both scaled to min = 1."""
    byname = dict(zip(names, fams))
    use = [k for k in names if k in gamma]
    dj = {k: byname[k]["d_eff"] for k in use}
    Rb = {k: max(dj.values()) / dj[k] for k in use}; m = min(Rb.values()); Rb = {k: v / m for k, v in Rb.items()}
    g0 = min(gamma[k] for k in use); Rw = {k: gamma[k] / g0 for k in use}
    return {k: Rb[k] ** (1 - w) * Rw[k] ** w for k in use}


def hybrid_shape(F, fams, names, gamma, w):
    """Polytope with one rate per family (keyed by family tuple, so no label collisions)."""
    from .shape import Shape
    from .models import _planes
    R = rates(fams, names, gamma, w)
    rate_by_family = {f["family"]: R[nm] for f, nm in zip(fams, names) if nm in R}
    normals, dists, tags = _planes(F, rate_by_family, set(rate_by_family))
    return Shape(normals, dists, tags)
