"""Keerthi's MorphoGraph-MOF CHGNet slabs -> Wulff shape -> compare with lab shapes.

Her notebook (MorphoGraph_MOF_revised.ipynb, md5 90a57760...) relaxes stoichiometric
slabs with CHGNet and records, per slab, pair_excess = (E_slab - N*E_bulk)/A, which is
gamma_top + gamma_bottom. Her pair-equation fit was underdetermined for every facet, so
the notebook produced no surface energies and no Wulff shape.

This script takes the standard cleavage-energy estimate instead:
    gamma(hkl) = min over terminations of pair_excess / 2
i.e. the lowest-energy stoichiometric cut, split equally between its two faces.
It also reports the median termination as a sensitivity check, because the spread
between terminations is large.

Run from the repository root:  python Experimental_Morphology_Task/compare/keerthi_vs_lab.py
Writes keerthi_vs_lab.json and KEERTHI_VS_LAB.md next to this script.
"""
import glob
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, HalfspaceIntersection

ROOT = Path(__file__).resolve().parents[2]          # repository root
RUNS = ROOT / "OUTPUTSSSSSSS"
HERE = Path(__file__).resolve().parent
EV_A2_TO_J_M2 = 16.0218

# Lab benchmark: additive-free crystals from ../dataset (record ids given in the report).
LAB = {
    "MOF-5": {"shape": "cube", "facet": "{100}",
              "evidence": "suresh2021-1..4, suresh2022-1 (DEF), mulyati2015-1..3 (DMF); two independent labs",
              "co2": "18.15 mmol/g at 298 K, 25 bar (arjmandi2016); weak at 1 bar"},
    "HKUST-1": {"shape": "octahedron", "facet": "{111}",
                "evidence": "ediati2019-1, rubio2014-1..3, zelenka2024-1, yanez2024-1, klemba2025-1/2 ('bipyramid'); 4+ labs",
                "co2": "5.84 mmol/g at 273 K, 1 bar (zelenka2024); 2.8 at 298 K (yanez2024)"},
    "UiO-66": {"shape": "octahedron", "facet": "{111}",
               "evidence": "schaate2011-2 (abstract), morelli2020-1/2 (GVL, PC), noorani2025-1 (UiO-66-NH2)",
               "co2": "3.66 mmol/g at 273 K, 1 bar (cao2018)"},
}


def conv_family(prim_hkl, L):
    """Primitive Miller index -> conventional-cubic plane normal, as small integers."""
    n = np.array(prim_hkl, float) @ np.linalg.inv(L).T
    n = n / np.abs(n[np.abs(n) > 1e-6]).min()
    return tuple(int(round(x)) for x in n)


def family_key(v):
    return "{" + "".join(str(x) for x in sorted(np.abs(v), reverse=True)) + "}"


def cubic_orbit(v, signed):
    """All cubic-equivalent normals of v. With signed=True (point group -43m) only
    even numbers of sign flips are kept for {111}, which separates {111}+ from {111}-."""
    out = set()
    for p in itertools.permutations(v):
        for s in itertools.product((1, -1), repeat=3):
            w = tuple(a * b for a, b in zip(p, s))
            if signed and len(set(np.abs(v))) == 1 and np.prod(w) * np.prod(v) < 0:
                continue
            out.add(w)
    return out


def wulff(planes):
    """planes: list of (normal, gamma). Returns area fraction per family label."""
    normals = np.array([np.array(n, float) / np.linalg.norm(n) for n, _, _ in planes])
    gam = np.array([g for _, g, _ in planes])
    hs = np.hstack([normals, -gam[:, None]])
    verts = HalfspaceIntersection(hs, np.zeros(3)).intersections
    hull = ConvexHull(verts)
    area = {}
    for simplex, eq in zip(hull.simplices, hull.equations):
        tri = verts[simplex]
        a = 0.5 * np.linalg.norm(np.cross(tri[1] - tri[0], tri[2] - tri[0]))
        i = int(np.argmax(normals @ eq[:3]))
        lab = planes[i][2]
        area[lab] = area.get(lab, 0.0) + a
    tot = sum(area.values())
    return {k: v / tot for k, v in sorted(area.items(), key=lambda kv: -kv[1])}


def name_shape(frac):
    f = lambda k: sum(v for kk, v in frac.items() if kk.startswith(k))
    f100, f111, f110 = f("{100}"), f("{111}"), f("{110}")
    top = max(frac, key=frac.get)
    if f100 > 0.95:
        return "cube"
    if f111 > 0.95:
        return "octahedron"
    if f110 > 0.95:
        return "rhombic dodecahedron"
    if top.startswith("{111}") and f100 > 0.05:
        return "truncated octahedron" if f111 > 0.6 else "cuboctahedron-like"
    if top.startswith("{100}") and f111 > 0.05:
        return "truncated cube"
    return f"mixed, dominant {top}"


def main():
    results = {}
    for mof in LAB:
        d = Path(glob.glob(str(RUNS / f"{mof}_*" / "MorphoGraph*"))[0])
        meta = json.load(open(next(d.glob("*_metadata.json"))))
        L = np.array(meta["working_lattice_matrix_A"])
        df = pd.read_csv(next(d.glob("*_surface_pair_records.csv")))
        ok = df[(df.status == "pair_fit_underdetermined") & df.stoichiometric]
        signed = mof == "UiO-66"          # her UiO-66 cell is F-43m (ordered mu3-OH)
        out = {"run": d.name, "n_slabs_used": int(len(ok)),
               "n_slabs_not_converged": int((df.status == "excluded_not_converged").sum()),
               "facets": {}, "wulff": {}}
        for est in ("min", "median"):
            planes, seen = [], set()
            for (h, k, l), g in ok.groupby(["h", "k", "l"]):
                v = conv_family((h, k, l), L)
                pe = g.pair_excess_eV_A2 * EV_A2_TO_J_M2
                gamma = float((pe.min() if est == "min" else pe.median()) / 2)
                label = family_key(v)
                if signed and label == "{111}":
                    label += "+" if np.prod(v) > 0 else "-"
                if est == "min":
                    out["facets"][label] = {"primitive_hkl": [int(h), int(k), int(l)],
                                            "conventional_normal": list(v),
                                            "n_terminations": int(len(g)),
                                            "gamma_min_J_m2": round(float(pe.min() / 2), 4),
                                            "gamma_median_J_m2": round(float(pe.median() / 2), 4),
                                            "gamma_max_J_m2": round(float(pe.max() / 2), 4)}
                for w in cubic_orbit(v, signed):
                    if w not in seen:
                        seen.add(w)
                        planes.append((w, gamma, label))
            frac = wulff(planes)
            out["wulff"][est] = {"area_fraction": {k: round(v, 3) for k, v in frac.items()},
                                 "shape": name_shape(frac)}
        g = out["facets"]
        g111 = g.get("{111}", g.get("{111}+", g.get("{111}-")))["gamma_min_J_m2"]
        out["gamma100_over_gamma111"] = round(g["{100}"]["gamma_min_J_m2"] / g111, 3)
        lab = LAB[mof]
        pred = out["wulff"]["min"]
        top = max(pred["area_fraction"], key=pred["area_fraction"].get)
        out["lab"] = lab
        out["shape_match"] = pred["shape"] == lab["shape"]
        out["dominant_facet_match"] = top.rstrip("+-") == lab["facet"]
        results[mof] = out
    (HERE / "keerthi_vs_lab.json").write_text(json.dumps(results, indent=1))
    return results


if __name__ == "__main__":
    res = main()
    for m, r in res.items():
        print(f"\n== {m}  gamma100/gamma111 = {r['gamma100_over_gamma111']}")
        for k, v in r["facets"].items():
            print(f"   {k:7} gamma min {v['gamma_min_J_m2']:.3f}  median {v['gamma_median_J_m2']:.3f}  (n={v['n_terminations']})")
        for est in ("min", "median"):
            w = r["wulff"][est]
            print(f"   Wulff[{est}]: {w['shape']:22} {w['area_fraction']}")
        print(f"   LAB: {r['lab']['shape']} {r['lab']['facet']}  -> shape match {r['shape_match']}, dominant facet match {r['dominant_facet_match']}")
