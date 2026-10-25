"""Turn a MorphoGraph-MOF (CHGNet) results folder into face energies and Wulff shapes.

Why this module exists
----------------------
The CHGNet notebook relaxes stoichiometric slabs. One slab has a TOP face and a BOTTOM face, so
its excess energy per area is only the SUM

    p = (E_slab - N * E_bulk_per_atom) / A  =  gamma_top + gamma_bottom          (1)

The notebook then tries to solve for every termination's own gamma from many such sums. For MOFs
there are more terminations than independent sums (e.g. MOF-5: 37 unknowns, rank 20), so it returns
no gammas at all and no Wulff shape.

The fix used here: the CLEAVAGE energy (standard in surface science)
---------------------------------------------------------------------
Cutting a crystal along a plane always creates two faces at once: (hkl) on one piece and
(-h -k -l) on the other. Equation (1) is exactly the energy of that cut. We take the cheapest cut
for each plane orientation and give each of the two faces half of it:

    gamma_cl(hkl) = min over terminations of p / 2                               (2)

* If (hkl) and (-h-k-l) belong to the SAME symmetry family (any crystal with an inversion centre,
  e.g. MOF-5, HKUST-1 in Fm-3m), both faces of the crystal are of that family and (2) is the
  standard cleavage (average) surface energy. Since p = gamma_top + gamma_bottom >= 2 min(gamma),
  (2) is also an UPPER bound on the lowest termination energy of that orientation.
* If they are DIFFERENT families (no inversion, e.g. {111}+ / {111}- in F-43m UiO-66, I-43m ZIF-8),
  a cut only gives gamma(+) + gamma(-). The two cannot be separated from these slabs, so both
  get p/2 and the result is flagged "split_equal": the shape cannot then distinguish + from -.

Only slabs that are stoichiometric and force-converged are used (the notebook's own tests).
Optionally slabs whose relaxation detached fragments can be excluded (see `fragments`).
"""
import csv
import glob
import json
import os
import warnings
from math import gcd

import numpy as np
import spglib
from ase.io import read

from .structure import Crystal
from .faces import enumerate_faces, families, plain
from .shape import Shape
from .models import describe

EV_A2_TO_J_M2 = 16.021766


def _prim(v):
    g = gcd(gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    return tuple(int(x // g) for x in v)


def working_crystal(cif, symprec=0.1):
    """Crystal object in the notebook's OWN working cell (no change of basis), so the Miller
    indices in its CSV files can be looked up directly."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        at = read(cif)
    L = np.array(at.cell[:]); frac = at.get_scaled_positions(); num = at.numbers
    d = spglib.get_symmetry_dataset((L, frac, num), symprec=symprec)
    c = Crystal(name=os.path.basename(cif), lattice=L, frac=frac, numbers=num, spacegroup=d.international,
                sg_number=d.number, rotations=np.array(d.rotations), translations=np.array(d.translations),
                symprec=symprec, used_hydrogen=True)
    # conventional (standard) lattice vectors expressed in the SAME Cartesian frame as L
    P = np.array(d.transformation_matrix, float)
    Lconv = np.linalg.inv(P).T @ L
    return c, Lconv


def conventional_hkl(hkl_working, L_working, L_conv):
    """Miller index in the conventional cell of the plane given in the working cell."""
    g = np.array(hkl_working, float) @ np.linalg.inv(L_working).T     # plane normal (reciprocal vector)
    v = L_conv @ g                                                      # components g . a_i(conv)
    v = v / np.abs(v)[np.abs(v) > 1e-9].min()
    for s in range(1, 25):
        w = v * s
        if np.allclose(w, np.rint(w), atol=1e-3):
            return _prim(tuple(int(x) for x in np.rint(w)))
    raise ValueError(f"could not index plane {hkl_working} in the conventional cell")


def family_of(hkl, crystal):
    """Canonical family key (same rule as faces.enumerate_faces)."""
    h = np.array(_prim(tuple(int(x) for x in hkl)))
    ops = {tuple(R.ravel()) for R in crystal.rotations}
    return max(tuple(int(x) for x in (h @ np.array(r).reshape(3, 3))) for r in ops)


def family_names(fams, crystal, L_working, L_conv):
    """Readable names in CONVENTIONAL indices, e.g. {100}, {111}+ ; + / - only when the two
    halves of a family are not related by symmetry (no inversion centre)."""
    names = {}
    for F in fams:
        key = F["family"]
        hc = conventional_hkl(key, L_working, L_conv)
        nm = plain(hc)
        neg = family_of(tuple(-x for x in key), crystal)
        if neg != key:
            s = hc[0] * hc[1] * hc[2]
            nm += "+" if s > 0 else ("-" if s < 0 else f"[{','.join(map(str, key))}]")
        names[key] = nm
    # make names unique if two families still collide (low symmetry)
    seen = {}
    for k, v in list(names.items()):
        if v in seen:
            names[k] = f"{v}[{','.join(map(str, k))}]"
        seen[names[k]] = k
    return names


def read_records(folder):
    f = glob.glob(os.path.join(folder, "*_surface_pair_records.csv"))
    if not f:
        raise FileNotFoundError("no *_surface_pair_records.csv in " + folder)
    return list(csv.DictReader(open(f[0])))


def usable(r, force_tol=0.05):
    """A slab energy is used only if: stoichiometric, relaxed, force-converged, finite."""
    try:
        p = float(r["pair_excess_eV_A2"]); fm = float(r.get("fmax_eV_A") or "nan")
    except ValueError:
        return False
    return (str(r.get("stoichiometric")) == "True" and np.isfinite(p) and np.isfinite(fm)
            and fm <= force_tol and not str(r.get("status", "")).startswith("excluded"))


def cleavage_energies(folder, force_tol=0.05, exclude=None):
    """Returns dict with per-family cleavage gamma (J/m^2) and bookkeeping.
    exclude: optional set of (miller_string, termination_string) slabs to drop (e.g. fragmented)."""
    wc = glob.glob(os.path.join(folder, "*_working_cell.cif"))[0]
    crystal, Lconv = working_crystal(wc)
    faces = enumerate_faces(crystal, 3)
    fams = families(faces)
    names = family_names(fams, crystal, crystal.lattice, Lconv)
    cuts = {}         # unordered pair of families -> list of (p_J_m2, miller, termination)
    n_used = n_all = 0
    for r in read_records(folder):
        if not r.get("relaxed_slab_file") and not r.get("pair_excess_eV_A2"):
            continue
        n_all += 1
        if not usable(r, force_tol):
            continue
        if exclude and (r["miller"], r["termination"]) in exclude:
            continue
        h = _prim((int(r["h"]), int(r["k"]), int(r["l"])))
        fa, fb = family_of(h, crystal), family_of(tuple(-x for x in h), crystal)
        key = tuple(sorted([fa, fb]))
        cuts.setdefault(key, []).append((float(r["pair_excess_eV_A2"]) * EV_A2_TO_J_M2, r["miller"], r["termination"]))
        n_used += 1
    gamma, info = {}, {}
    for key, vals in cuts.items():
        vals.sort()
        g = vals[0][0] / 2.0
        split = key[0] != key[1]
        for fam in set(key):
            nm = names[fam]
            gamma[nm] = round(g, 5)
            info[nm] = dict(gamma_cleavage_J_m2=round(g, 5), min_cut_J_m2=round(vals[0][0], 5),
                            n_slabs=len(vals), best_slab=f"{vals[0][1]} termination {vals[0][2]}",
                            median_cut_J_m2=round(vals[len(vals) // 2][0], 5),
                            split_equal=split, family_working_cell=list(fam))
    return dict(working_cell=wc, spacegroup=crystal.spacegroup, n_slab_records=n_all, n_slabs_used=n_used,
                gamma=gamma, faces_info=info, _faces=faces, _names=names)


def symmetric_slab_gammas(folder, force_tol=0.05, exclude=None):
    """Exact termination energies from slabs that were symmetric as cut.

    A slab whose two faces carry the same termination gives gamma = p / 2 for that termination,
    with no pair equation to solve. The notebook tests symmetry before relaxation
    (symmetric_diagnostic) and again after it, and merges the two unknowns only if the RELAXED slab
    is still symmetric; relaxation without constraints broke the symmetry in every such slab, so the
    notebook used none of them. Here a slab symmetric as cut is taken as one termination on both
    sides. Returns {family name: [(gamma_J_m2, miller, termination), ...]} sorted by gamma."""
    wc = glob.glob(os.path.join(folder, "*_working_cell.cif"))[0]
    crystal, Lconv = working_crystal(wc)
    names = family_names(families(enumerate_faces(crystal, 3)), crystal, crystal.lattice, Lconv)
    out = {}
    for r in read_records(folder):
        if str(r.get("symmetric_diagnostic")) != "True" or not usable(r, force_tol):
            continue
        if exclude and (r["miller"], r["termination"]) in exclude:
            continue
        h = _prim((int(r["h"]), int(r["k"]), int(r["l"])))
        nm = names[family_of(h, crystal)]
        out.setdefault(nm, []).append((round(float(r["pair_excess_eV_A2"]) * EV_A2_TO_J_M2 / 2, 5), r["miller"], r["termination"]))
    return {k: sorted(v) for k, v in out.items()}


def wulff_from(result, gamma=None):
    """Wulff shape on the working-cell faces from per-name gammas (default: the cleavage ones)."""
    gamma = gamma or result["gamma"]
    faces, names = result["_faces"], result["_names"]
    n, d, t = [], [], []
    for f in faces.values():
        nm = names.get(f.family)
        if nm in gamma:
            n.append(f.normal); d.append(gamma[nm]); t.append(nm)
    return Shape(n, d, t)


def bfdh_same_faces(result):
    faces, names = result["_faces"], result["_names"]
    use = set(result["gamma"])
    deff = {names[f.family]: f.d_eff for f in faces.values() if names.get(f.family) in use}
    dmax = max(deff.values())
    return {k: dmax / v for k, v in deff.items()}


def hybrid_from(result, w, gamma=None):
    """R = R_BFDH^(1-w) * R_Wulff^w on the same faces (both scaled to min 1)."""
    gamma = gamma or result["gamma"]
    Rb = bfdh_same_faces(result); mb = min(Rb.values()); Rb = {k: v / mb for k, v in Rb.items()}
    g0 = min(gamma[k] for k in Rb); Rw = {k: gamma[k] / g0 for k in Rb}
    return wulff_from(result, {k: Rb[k] ** (1 - w) * Rw[k] ** w for k in Rb})


def summary(result, w_list=(0, 0.25, 0.5, 0.75, 1)):
    out = {k: v for k, v in result.items() if not k.startswith("_")}
    out["shapes"] = {}
    for w in w_list:
        s = hybrid_from(result, w)
        fr = s.face_fractions()
        out["shapes"][str(w)] = dict(name=describe(s, 0.01), sphericity=round(float(s.sphericity()), 3),
                                     faces={k: round(float(v), 3) for k, v in fr.items() if v > 0.005})
    return out
