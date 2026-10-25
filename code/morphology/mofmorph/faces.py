"""Allowed crystal faces, effective spacings and symmetry families.

Systematic-absence rule (primer, Proposition 1): reflection h is absent if the space group
contains an operation (R, t) with h R = h and h.t not an integer.
"""
from dataclasses import dataclass
from math import gcd
import itertools
import numpy as np


def is_absent(h, rotations, translations, tol=1e-6):
    h = np.asarray(h)
    for R, t in zip(rotations, translations):
        if np.array_equal(h @ R, h):
            ph = float(h @ t)
            if abs(ph - round(ph)) > tol:
                return True
    return False


@dataclass
class Face:
    hkl: tuple          # primitive direction (no common factor)
    order: int          # n: first allowed reflection is n*hkl
    d: float            # d_hkl of the primitive direction (Angstrom)
    d_eff: float        # d / n
    normal: np.ndarray  # Cartesian unit normal
    family: tuple       # canonical representative of the symmetry family


def _primitive(v):
    g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    return tuple(int(x // g) for x in v)


def enumerate_faces(crystal, max_index=6, absence_ops=None):
    """absence_ops=(rotations, translations): operations used for the systematic-absence test.
    By default the crystal's own operations. A deformed crystal (deform.py) passes the ORIGINAL
    operations here, because absences depend only on fractional coordinates (Proposition 14),
    while its families are the orbits of the smaller isometric subgroup."""
    rots, trans = crystal.rotations, crystal.translations
    if absence_ops is not None:
        rots_abs, trans_abs = absence_ops
    else:
        rots_abs, trans_abs = rots, trans
    B = crystal.recip
    point_ops = {tuple(R.ravel()) for R in rots}
    point_ops = [np.array(r).reshape(3, 3) for r in point_ops]
    faces = {}
    rng = range(-max_index, max_index + 1)
    for v in itertools.product(rng, rng, rng):
        if v == (0, 0, 0) or _primitive(v) != v:
            continue
        h = np.array(v)
        n = 1
        while is_absent(n * h, rots_abs, trans_abs):
            n += 1
            if n > 12:
                break
        g = h @ B
        d = 1.0 / np.linalg.norm(g)
        # symmetry family: all h R (row vector convention), canonical = max tuple
        fam = max(tuple(int(x) for x in (h @ R)) for R in point_ops)
        faces[v] = Face(hkl=v, order=n, d=d, d_eff=d / n, normal=g / np.linalg.norm(g), family=fam)
    return faces


def families(faces):
    """Group faces by family; return list sorted by decreasing d_eff."""
    fam = {}
    for f in faces.values():
        fam.setdefault(f.family, []).append(f)
    out = []
    for key, fs in fam.items():
        out.append(dict(family=key, members=fs, d=fs[0].d, d_eff=fs[0].d_eff, order=fs[0].order,
                        multiplicity=len(fs), label=family_label(key, len(fs))))
    out.sort(key=lambda x: (-x["d_eff"], -x["multiplicity"]))
    return out


def label(hkl):
    return "{" + "".join(f"\\bar{{{-x}}}" if x < 0 else str(x) for x in hkl) + "}"


def plain(hkl):
    return "{" + "".join(str(abs(x)) for x in sorted(hkl, key=lambda x: -abs(x))) + "}"


def full_cubic_multiplicity(hkl):
    vals = set()
    for p in itertools.permutations(hkl):
        for sg in itertools.product((1, -1), repeat=3):
            vals.add(tuple(a * b for a, b in zip(p, sg)))
    return len(vals)


def family_label(key, multiplicity):
    """Plain label like {111}; in non-centrosymmetric tetrahedral groups (e.g. F-43m, I-43m) the
    cubic family splits in two halves, labelled {111}+ and {111}- by the sign of h*k*l."""
    lab = plain(key)
    if multiplicity < full_cubic_multiplicity(key) and all(key):
        lab += "+" if key[0] * key[1] * key[2] > 0 else "-"
    return lab
