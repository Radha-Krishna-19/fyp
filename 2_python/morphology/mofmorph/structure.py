"""Read a CIF, find the true space group, return the conventional cell and its symmetry operations.

Many MOF CIFs are stored in P1 (no symmetry). Hydrogen positions are often disordered or
placed by software and can break the symmetry, so we search for symmetry both with and
without H and keep the higher-symmetry result (reported to the user).
"""
from dataclasses import dataclass, field
import warnings
import numpy as np
import spglib
from ase.io import read


@dataclass
class Crystal:
    name: str
    lattice: np.ndarray            # rows = conventional lattice vectors a, b, c (Angstrom)
    frac: np.ndarray               # fractional positions in the conventional cell
    numbers: np.ndarray            # atomic numbers
    spacegroup: str
    sg_number: int
    rotations: np.ndarray          # (n,3,3) integer, act on fractional coordinates
    translations: np.ndarray       # (n,3)
    symprec: float
    used_hydrogen: bool
    notes: list = field(default_factory=list)

    @property
    def recip(self):
        """Rows = reciprocal vectors a*, b*, c* (no 2*pi), so |h @ recip| = 1/d_hkl."""
        return np.linalg.inv(self.lattice).T

    @property
    def cell_lengths(self):
        return np.linalg.norm(self.lattice, axis=1)


def _dataset(cell, symprec):
    d = spglib.get_symmetry_dataset(cell, symprec=symprec)
    return d


def load(path, name=None, symprecs=(1e-3, 1e-2, 5e-2, 1e-1)):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        atoms = read(path)
    name = name or path
    notes = []
    candidates = []
    for use_h in (True, False):
        a = atoms if use_h else atoms[[s != "H" for s in atoms.get_chemical_symbols()]]
        cell = (a.cell[:], a.get_scaled_positions(), a.numbers)
        for sp in symprecs:
            d = _dataset(cell, sp)
            if d is None:
                continue
            candidates.append((d.number, use_h, -sp, sp, cell))
            break  # smallest tolerance that works for this H choice
    # prefer: higher space-group number at the smallest tolerance; with H if it ties
    best = max(candidates, key=lambda c: (c[0], c[1], c[2]))
    number, use_h, _, sp, cell = best
    with_h = [c for c in candidates if c[1]]
    if not use_h and with_h and with_h[0][0] < number:
        notes.append(f"With H atoms only space group #{with_h[0][0]} is found; without H #{number}. "
                     "H positions in the file break the symmetry; the framework symmetry is used.")
    L, p, num = spglib.standardize_cell(cell, to_primitive=False, no_idealize=False, symprec=sp)
    d = spglib.get_symmetry_dataset((L, p, num), symprec=sp)
    return Crystal(name=name, lattice=np.array(L), frac=np.array(p), numbers=np.array(num),
                   spacegroup=d.international, sg_number=d.number,
                   rotations=np.array(d.rotations), translations=np.array(d.translations),
                   symprec=sp, used_hydrogen=use_h, notes=notes)
