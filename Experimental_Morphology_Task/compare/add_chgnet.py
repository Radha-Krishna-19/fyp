"""Turn MorphoGraph-MOF (CHGNet) result zips into shapes comparable with the other methods.

    python add_chgnet.py <folder containing *_MorphoGraph_MOF_revised_results_*.zip or extracted folders>

For each MOF it reads the notebook's own outputs:
  *_metadata.json                          working (primitive) lattice used for Miller indices
  *_surface_energies_individual.csv        fitted gamma per directed (h,k,l) and termination
and then
  1. keeps, per directed (h,k,l), the minimum positive fitted gamma with fit_status == fit_ok
     (the notebook's own "CHGNet_minimum_termination_Wulff" rule);
  2. converts each primitive-cell (h,k,l) to the conventional cubic setting of the repository CIF,
     checking the axis choice against the atom positions so that {111}+ and {111}- are not swapped;
  3. checks that symmetry-equivalent directions received the same gamma (consistency check);
  4. builds the Wulff shape with the project's own mofmorph.from_rates and names it with
     mofmorph.describe, exactly as the other five methods were named.
Writes chgnet_shapes.json next to this script. Nothing is invented: a MOF whose required
families lack a valid gamma is reported as such, with no shape.
"""
import csv
import io
import itertools
import json
import math
import sys
import zipfile
from collections import defaultdict
from functools import reduce
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "2_python" / "morphology"))
from mofmorph.structure import load                      # noqa: E402
from mofmorph.faces import enumerate_faces                # noqa: E402
from mofmorph.models import from_rates, describe          # noqa: E402

CIF = {"MOF-5": "MOF5.cif", "HKUST-1": "HKUST-1.cif", "UiO-66": "UiO-66.cif", "ZIF-8": "ZIF-8.cif"}
SIGNED = {"UiO-66", "ZIF-8"}   # non-centrosymmetric: {111} splits into + and -


def read_result(src):
    """Return (metadata, gamma rows, pair-fit summary rows, working-cell CIF text) from a zip or folder."""
    if src.suffix == ".zip":
        z = zipfile.ZipFile(src)
        names = z.namelist()
        get = lambda suffix: next(n for n in names if n.endswith(suffix))
        meta = json.loads(z.read(get("_metadata.json")))
        rows = list(csv.DictReader(io.StringIO(z.read(get("_surface_energies_individual.csv")).decode("utf-8"))))
        fits = list(csv.DictReader(io.StringIO(z.read(get("_surface_pair_fit_summary.csv")).decode("utf-8"))))
        wcif = z.read(get("_working_cell.cif")).decode("utf-8")
    else:
        get = lambda suffix: next(src.rglob(f"*{suffix}"))
        meta = json.loads(get("_metadata.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader(get("_surface_energies_individual.csv").open(encoding="utf-8")))
        fits = list(csv.DictReader(get("_surface_pair_fit_summary.csv").open(encoding="utf-8")))
        wcif = get("_working_cell.cif").read_text(encoding="utf-8")
    return meta, rows, fits, wcif


def cubic_axes(prim):
    """Integer combinations of primitive vectors that form an orthogonal, equal-length triad."""
    cands = []
    for c in itertools.product(range(-2, 3), repeat=3):
        if c == (0, 0, 0):
            continue
        v = np.array(c) @ prim
        cands.append((np.linalg.norm(v), c, v))
    cands.sort(key=lambda t: t[0])
    for L in sorted({round(t[0], 3) for t in cands}):
        group = [t for t in cands if abs(t[0] - L) < 1e-3]
        for a, b in itertools.combinations(group, 2):
            if abs(a[2] @ b[2]) > 1e-3 * L * L:
                continue
            for c in group:
                if abs(c[2] @ a[2]) < 1e-3 * L * L and abs(c[2] @ b[2]) < 1e-3 * L * L:
                    T = np.array([a[1], b[1], c[1]])
                    vol_ratio = abs(round(np.linalg.det(T)))
                    if vol_ratio in (1, 2, 4):   # P, I or F centring
                        if np.linalg.det(np.array([a[2], b[2], c[2]])) < 0:
                            T[2] = -T[2]
                        return T
    raise ValueError("no cubic axes found among small integer combinations of the working lattice")


def orient_axes(T, wcif_text, crystal):
    """Find the cubic re-orientation P (one of 48 signed permutations) for which the working cell,
    re-expressed on axes P @ T, reproduces the atoms of the project's conventional cell
    (mofmorph Crystal) up to a translation. Returns P @ T, or None if no orientation matches.
    This fixes the meaning of the signs of (h, k, l), which decides {111}+ against {111}-."""
    import itertools as it
    from pymatgen.core import Structure
    w = Structure.from_str(wcif_text, fmt="cif")
    ref_frac = np.asarray(crystal.frac) % 1.0
    ref_num = np.asarray(crystal.numbers)
    ref_L = np.asarray(crystal.lattice)
    heavy = int(ref_num.max())
    for perm in it.permutations(range(3)):
        for signs in it.product((1, -1), repeat=3):
            P = np.zeros((3, 3), dtype=int)
            for i, (j, s) in enumerate(zip(perm, signs)):
                P[i, j] = s
            M = P @ T
            if round(np.linalg.det(M)) <= 0:
                continue
            conv = w.copy()
            conv.make_supercell(M.tolist())
            cf = np.array([s.frac_coords for s in conv]) % 1.0
            cn = np.array([s.specie.Z for s in conv])
            if len(cf) != len(ref_frac):
                continue
            ok_any = False
            for shift in ref_frac[ref_num == heavy] - cf[cn == heavy][0]:
                ok = True
                for Z in set(ref_num.tolist()):
                    moved = (cf[cn == Z] + shift) % 1.0
                    d = moved[:, None, :] - ref_frac[ref_num == Z][None, :, :]
                    d -= np.round(d)
                    if not np.all(np.min(np.linalg.norm(d @ ref_L, axis=2), axis=1) < 0.5):
                        ok = False
                        break
                if ok:
                    ok_any = True
                    break
            if ok_any:
                return M
    return None


def family_label(hkl, signed):
    h = [abs(x) for x in hkl]
    g = reduce(math.gcd, h)
    key = sorted((x // g for x in h), reverse=True)
    lab = "{" + "".join(map(str, key)) + "}"
    # mofmorph.faces.family_label: in -43m groups every family with all indices non-zero splits
    # into halves labelled by the sign of h*k*l
    if signed and all(x != 0 for x in hkl):
        lab += "+" if hkl[0] * hkl[1] * hkl[2] > 0 else "-"
    return lab


def main(folder):
    folder = Path(folder)
    out = {}
    for src in sorted(list(folder.glob("*.zip")) + [p for p in folder.iterdir() if p.is_dir()]):
        mof = next((m for m in CIF if src.name.startswith(m)), None)
        if mof is None:
            continue
        meta, rows, fits, wcif = read_result(src)
        prim = np.array(meta["working_lattice_matrix_A"], dtype=float)
        T = cubic_axes(prim)
        ref = REPO / "2_python" / CIF[mof]
        crystal = load(str(ref), mof)
        sign_note = "not needed (centrosymmetric)"
        if mof in SIGNED:
            M = orient_axes(T, wcif, crystal)
            if M is not None:
                T = M
                sign_note = "verified: working cell matches the mofmorph conventional cell atom by atom"
            else:
                sign_note = "UNVERIFIED: {111}+ and {111}- may be swapped"
        best = {}
        for r in rows:
            if r.get("fit_status") != "fit_ok":
                continue
            g = float(r["gamma_J_m2"])
            hkl = (int(float(r["h"])), int(float(r["k"])), int(float(r["l"])))
            if g > 0 and (hkl not in best or g < best[hkl]):
                best[hkl] = g
        fam = defaultdict(list)
        directions = []
        for hkl, g in sorted(best.items()):
            conv = tuple(int(round(x)) for x in T @ np.array(hkl))   # (h,k,l)_conv = T (h,k,l)_prim
            lab = family_label(conv, mof in SIGNED)
            fam[lab].append(g)
            directions.append({"primitive_hkl": hkl, "conventional_hkl": conv, "family": lab, "gamma_J_m2": round(g, 5)})
        spread = {k: round(max(v) - min(v), 5) for k, v in fam.items()}
        rates = {k: min(v) for k, v in fam.items()}
        attempted = {}
        for f in fits:
            hkl = (int(float(f["h"])), int(float(f["k"])), int(float(f["l"])))
            lab = family_label(tuple(int(round(x)) for x in T @ np.array(hkl)), mof in SIGNED)
            attempted.setdefault(lab, []).append(f.get("fit_status", "?"))
        missing = sorted(set(attempted) - set(rates))
        rec = {"mof": mof, "source": src.name, "sign_assignment": sign_note,
               "family_gamma_J_m2": {k: round(v, 5) for k, v in rates.items()},
               "within_family_spread_J_m2": spread, "directions": directions,
               "families_attempted": {k: sorted(set(v)) for k, v in attempted.items()},
               "families_without_valid_gamma": missing}
        if missing:
            # Same rule as the notebook: no Wulff shape unless every computed orientation has a
            # valid energy. Dropping the failed families would invent a shape.
            rec["shape"] = None
            rec["shape_error"] = "no valid CHGNet gamma for " + ", ".join(missing)
        elif len(rates) >= 2:
            F = enumerate_faces(crystal, 6)
            try:
                sh = from_rates(F, rates)
                rec["shape"] = describe(sh)
                rec["face_area_fraction"] = {k: round(v, 4) for k, v in sh.summary()["face_area_fraction"].items()}
            except Exception as exc:
                rec["shape"] = None
                rec["shape_error"] = f"{type(exc).__name__}: {exc}"
        else:
            rec["shape"] = None
            rec["shape_error"] = f"only {len(rates)} face families have a valid CHGNet gamma"
        out[mof] = rec
        print(json.dumps({k: rec[k] for k in ("mof", "family_gamma_J_m2", "within_family_spread_J_m2",
                                               "sign_assignment", "shape")}, indent=1))
    (HERE / "chgnet_shapes.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
