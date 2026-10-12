"""Phase 1b: deform the cell of each MOF and recompute the BFDH shape.
Run: python3 2_python/morphology/run_deform.py [cif folder]    Writes results/deform_results.json and figures."""
import sys, os, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import numpy as np
from mofmorph.structure import load
from mofmorph.deform import stretch, bfdh_shape, extents, parameters, habit
from mofmorph.models import describe
from mofmorph.faces import families
from mofmorph import render
CIF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "1_website")
OUT = os.path.join(HERE, "results"); os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
MOFS = [("MOF-5", "MOF5.cif"), ("HKUST-1", "HKUST-1.cif"), ("UiO-66", "UiO-66.cif"), ("ZIF-8", "ZIF-8.cif")]
LC = [0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
GAM = [60, 75, 90, 105, 120]

def rec(c, d):
    s, F = bfdh_shape(c, d)
    h, ba, cb = habit(s); e = extents(s)
    a, b, cc, al, be, ga = parameters(d.lattice)
    return s, dict(a=round(a, 3), b=round(b, 3), c=round(cc, 3), alpha=round(al, 2), beta=round(be, 2), gamma=round(ga, 2),
                   operations=int(len(d.rotations)), n_families=len(families(F)), name=describe(s, 0.01), habit=h,
                   b_over_a=round(ba, 4), c_over_b=round(cb, 4), sphericity=round(s.sphericity(), 4), kappa2=round(float(s.kappa2()), 4),
                   half_widths=[round(float(x), 4) for x in e])

R = {}
for name, fn in MOFS:
    c = load(os.path.join(CIF, fn), name); R[name] = dict(spacegroup=c.spacegroup, operations=int(len(c.rotations)), c_stretch=[], shear=[])
    shapes, titles = [], []
    for lc in LC:
        s, r = rec(c, stretch(c, lc=lc)); r["lc"] = lc; R[name]["c_stretch"].append(r)
        if lc in (0.25, 0.5, 1.0, 1.5, 3.0):
            shapes.append(s); titles.append(f"c x {lc}\n{r['habit']}")
    render.row(shapes, titles, os.path.join(OUT, "figs", f"{name}_deform_c.png"), size=2.6)
    shapes, titles = [], []
    for g in GAM:
        s, r = rec(c, stretch(c, gamma=g)); r["gamma_set"] = g; R[name]["shear"].append(r)
        shapes.append(s); titles.append(f"gamma = {g}\n{r['habit']}")
    render.row(shapes, titles, os.path.join(OUT, "figs", f"{name}_deform_gamma.png"), size=2.6)
    print(f"\n{name} {c.spacegroup}")
    for r in R[name]["c_stretch"]:
        print(f"  c x {r['lc']:<4} ops={r['operations']:3d} families={r['n_families']:3d} {r['habit']:7s} {r['name']:28s} b/a={r['b_over_a']:.3f} c/b={r['c_over_b']:.3f} halfwidths={r['half_widths']}")
    for r in R[name]["shear"]:
        print(f"  gamma {r['gamma_set']:<4} ops={r['operations']:3d} {r['habit']:7s} {r['name']}")
json.dump(R, open(os.path.join(OUT, "deform_results.json"), "w"), indent=1)
