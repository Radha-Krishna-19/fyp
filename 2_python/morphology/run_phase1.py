"""Phase 1: from the unit cell to a family of morphologies, for four MOFs.

Run from anywhere:  python3 2_python/morphology/run_phase1.py
Writes results/phase1_results.json and results/figs/*.png next to this file.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, math, os, warnings, numpy as np
warnings.filterwarnings("ignore")
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families, plain
from mofmorph.models import bfdh, from_rates, attachment_rates, grow_from_seed, describe
from mofmorph.graphrule import attachment_number
from mofmorph import render

HERE = os.path.dirname(os.path.abspath(__file__))
CIF = os.path.join(HERE, "..")            # the four CIFs live in 2_python/
OUT = os.path.join(HERE, "results"); os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
MOFS = [("MOF-5", os.path.join(CIF, "MOF5.cif"), "pcu"), ("HKUST-1", os.path.join(CIF, "HKUST-1.cif"), "tbo"),
        ("UiO-66", os.path.join(CIF, "UiO-66.cif"), "fcu"), ("ZIF-8", os.path.join(CIF, "ZIF-8.cif"), "sod")]
R = {}

def summ(s):
    d = s.summary(); d["name"] = describe(s)
    d["face_area_fraction"] = {k: round(v, 4) for k, v in d["face_area_fraction"].items()}
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}

for name, path, netname in MOFS:
    c = load(path, name); F = enumerate_faces(c, 6); fams = families(F)
    rec = dict(spacegroup=c.spacegroup, number=c.sg_number, a=round(float(c.cell_lengths[0]), 3),
               used_hydrogen_for_symmetry=c.used_hydrogen, symprec=c.symprec, notes=c.notes,
               n_symmetry_ops=len(c.rotations))
    rec["families"] = [dict(family=f["label"], first_reflection=f["order"], d=round(f["d"], 3),
                            d_eff=round(f["d_eff"], 3), multiplicity=f["multiplicity"]) for f in fams[:8]]
    s, rate = bfdh(F); rec["bfdh"] = summ(s)
    rec["bfdh_rates"] = {plain(k): round(v, 4) for k, v in rate.items()}
    render.row([s], [f"{name}: BFDH\n{describe(s)}"], f"{OUT}/figs/{name}_bfdh.png", size=3.2)
    # morph family between the two leading families of this lattice
    lead = []
    for f in fams:
        b = f["label"].rstrip("+-")
        if b not in lead: lead.append(b)
    A, Bf = lead[:2]
    series = []
    shapes, titles = [], []
    for t in [3.0, 1.6, 2/math.sqrt(3), 1.0, 0.8, 1/math.sqrt(3)*0.98]:
        sh = from_rates(F, {A: t, Bf: 1.0})
        series.append(dict(ratio=round(t, 4), **summ(sh))); shapes.append(sh)
        titles.append(f"$R_{{{A[1:-1]}}}/R_{{{Bf[1:-1]}}}={t:.2f}$\n{describe(sh)}")
    rec["morph_series"] = dict(family_A=A, family_B=Bf, points=series)
    render.row(shapes, titles, f"{OUT}/figs/{name}_morph.png",
               caption=f"{name}: same unit cell, growth-rate ratio of {A} to {Bf} varied", size=2.4)
    # tetrahedral morph: only possible when the point group splits {111} into two halves
    labels = {f["label"] for f in fams[:6]}
    if {"{111}+", "{111}-"} <= labels:
        tet, shapes, titles = [], [], []
        for r in [1.0, 0.85, 0.7, 0.55, 0.4, 0.3]:
            sh = from_rates(F, {"{111}+": r, "{111}-": 1.0, "{100}": 1.155})
            tet.append(dict(ratio=r, **summ(sh))); shapes.append(sh)
            titles.append(f"$R_{{111+}}/R_{{111-}}={r}$\n{describe(sh)}")
        rec["tetrahedral_series"] = tet
        render.row(shapes, titles, f"{OUT}/figs/{name}_tetrahedral.png",
                   caption=f"{name}: in point group -43m the two halves of {{111}} may grow at different rates", size=2.4)
    R[name] = rec
    print(f"{name:8s} {c.spacegroup:7s} a={rec['a']:.3f}  H used={c.used_hydrogen}  BFDH -> {rec['bfdh']['name']}")
    print("         families:", ", ".join(f"{f['family']}(n={f['first_reflection']}, d_eff={f['d_eff']})" for f in rec["families"][:5]))

# ---- graph rule (attachment numbers) for the two nets where it is well defined
G = {}
for netname, mof in [("pcu", "MOF-5"), ("fcu", "UiO-66")]:
    cnum = {"{100}": attachment_number(netname, (1, 0, 0)), "{110}": attachment_number(netname, (1, 1, 0)),
            "{111}": attachment_number(netname, (1, 1, 1))}
    c = load(dict((m, p) for m, p, _ in MOFS)[mof], mof); F = enumerate_faces(c, 4)
    rows = []; shapes = []; titles = []
    for beta in [0.0, 0.1, 0.3, 0.6, 1.0, 2.0]:
        sh = from_rates(F, attachment_rates(cnum, beta)) if beta > 0 else from_rates(F, {k: 1.0 for k in cnum})
        rows.append(dict(beta=beta, **summ(sh))); shapes.append(sh); titles.append(f"$\\beta={beta}$\n{describe(sh)}")
    render.row(shapes, titles, f"{OUT}/figs/{mof}_graphrule.png",
               caption=f"{mof} ({netname} net): growth rates R = exp(beta * c), c = links formed by a new node", size=2.4)
    G[mof] = dict(net=netname, attachment_numbers=cnum, beta_series=rows)
    print(f"graph rule {mof}: c = {cnum};", [(r['beta'], r['name']) for r in rows])
R["graph_rule"] = G

# ---- growth in time from a spherical seed, UiO-66 graph rule (compare Chen et al. UiO-67 sequence)
c = load(os.path.join(CIF, "UiO-66.cif"), "UiO-66"); F = enumerate_faces(c, 4)
rates = attachment_rates(G["UiO-66"]["attachment_numbers"], 0.6)
shapes, titles, rows = [], [], []
for t in [0.0, 0.02, 0.06, 0.2, 0.8, 4.0]:
    sh = grow_from_seed(F, rates, t, r0=1.0, v_rough=1.1 * max(rates.values())); s = summ(sh); s["time"] = t; rows.append(s)
    shapes.append(sh); titles.append(f"time {t}\n{describe(sh)}")
render.row(shapes, titles, f"{OUT}/figs/UiO-66_growth_in_time.png",
           caption="UiO-66 grown from a spherical seed with graph-rule rates (beta=0.6). Grey = rough, unfaceted surface.", size=2.4)
R["growth_in_time_UiO66"] = rows
print("growth in time:", [(r['time'], r['name']) for r in rows])
json.dump(R, open(f"{OUT}/phase1_results.json", "w"), indent=1, default=str)
