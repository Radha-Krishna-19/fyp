"""Phase 1b: deform the unit cell (change a, b, c, alpha, beta, gamma) and recompute faces and shapes.

Idea. Keep every atom at its fractional coordinates and change only the lattice,
    L' = L (I + eps)^T          (rows of L are the lattice vectors; eps is a strain)
so the atoms move with the cell. The result is a hypothetical framework derived from the real one.
Three facts (Propositions 14-16 on the Mathematics page):
  14. which faces are allowed (systematic absences) does not change: it depends only on fractional coordinates;
  15. the faces that stay SYMMETRY-EQUIVALENT are those related by operations that are still isometries
      of the new lattice, {(R,t) in G : R^T G' R = G'}, so families split when the cell loses symmetry;
  16. the spacings d_hkl change with the metric G' = L' L'^T, hence so do the BFDH distances and the shape.
"""
from dataclasses import replace
import numpy as np
from .faces import enumerate_faces, families
from .models import bfdh


def cell_from_parameters(a, b, c, alpha, beta, gamma):
    """Rows = lattice vectors for the standard setting (a along x, b in the xy plane)."""
    al, be, ga = np.radians([alpha, beta, gamma])
    va = np.array([a, 0, 0])
    vb = np.array([b * np.cos(ga), b * np.sin(ga), 0])
    cx = c * np.cos(be)
    cy = c * (np.cos(al) - np.cos(be) * np.cos(ga)) / np.sin(ga)
    cz = np.sqrt(max(c * c - cx * cx - cy * cy, 0.0))
    return np.array([va, vb, [cx, cy, cz]])


def parameters(L):
    a, b, c = np.linalg.norm(L, axis=1)
    ang = lambda u, v: np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1)))
    return a, b, c, ang(L[1], L[2]), ang(L[0], L[2]), ang(L[0], L[1])


def deformed(crystal, new_lattice, tol=1e-6):
    """Crystal with a new lattice. Its operations are the original ones that are still isometries."""
    G = new_lattice @ new_lattice.T
    keep = [k for k, R in enumerate(crystal.rotations)
            if np.allclose(R.T @ G @ R, G, atol=tol * np.trace(G))]
    return replace(crystal, lattice=np.array(new_lattice, float),
                   rotations=crystal.rotations[keep], translations=crystal.translations[keep])


def stretch(crystal, la=1.0, lb=1.0, lc=1.0, alpha=None, beta=None, gamma=None):
    """Scale the lattice vectors by (la, lb, lc) and optionally set the angles (degrees, else unchanged)."""
    a, b, c, al, be, ga = parameters(crystal.lattice)
    L = cell_from_parameters(a * la, b * lb, c * lc, al if alpha is None else alpha,
                             be if beta is None else beta, ga if gamma is None else gamma)
    return deformed(crystal, L)


def bfdh_shape(crystal, deformed_crystal, max_index=6, n_families=40):
    F = enumerate_faces(deformed_crystal, max_index, absence_ops=(crystal.rotations, crystal.translations))
    s, rate = bfdh(F, n_families)
    return s, F


def extents(shape):
    """Half-widths of the bounding box along x, y, z (Cartesian axes of the deformed lattice setting)."""
    return np.abs(shape.V).max(axis=0)


def habit(shape, ratio=2 / 3):
    """Zingg classification from the principal radii of gyration a >= b >= c:
    equant (b/a and c/b both above 2/3), rod (b/a < 2/3), plate (c/b < 2/3), lath (both)."""
    w = np.sqrt(np.sort(np.linalg.eigvalsh(shape.gyration()))[::-1])
    ba, cb = w[1] / w[0], w[2] / w[1]
    if ba >= ratio and cb >= ratio:
        return "equant", ba, cb
    if ba < ratio and cb >= ratio:
        return "rod", ba, cb
    if ba >= ratio and cb < ratio:
        return "plate", ba, cb
    return "lath", ba, cb
