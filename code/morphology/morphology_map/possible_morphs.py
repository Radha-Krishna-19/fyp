"""Possible morphologies of a given CIF, generated from its surface energies.
Start from the structure's point (g100, g110, g111). A modulator that binds face F lowers g_F
(Gibbs adsorption); lowering one face at a time, g_F -> s * g_F for s from 1 down to 0.05, traces
three paths on the map. Every shape on those paths is a possible morphology of that CIF; the
baseline itself is the additive-free prediction. Compared with the on-map shapes seen in the lab
(data/experimental_morphology). Shapes off the cubic map (plate, rod, ...) cannot be generated."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import json, sys, numpy as np, pandas as pd
from cubic_wulff import shape
P = json.load(open(_os.path.join(HERE, "model_points.json")))
lab = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else LAB_CSV)
ONMAP = {"cube", "truncated_cube", "cuboctahedron", "truncated_octahedron", "octahedron",
         "cube_truncated_edges", "truncated_rhombic_dodecahedron", "rhombic_dodecahedron"}
BASE = {"MOF-5": "UFF Wulff", "HKUST-1": "Steps 1-8 CHGNet, static", "UiO-66": "Steps 1-8 CHGNet, static", "ZIF-8": "Steps 1-8 CHGNet, static"}
out = {}
for m, src in BASE.items():
    g0 = P[m][src]["g"]; g0 = {k.strip("{}"): v for k, v in g0.items()}
    base, _ = shape(g0["100"], g0["110"], g0["111"])
    paths = {}
    for F in ("100", "110", "111"):
        seq = []
        for s in np.linspace(1, 0.05, 96):
            g = dict(g0); g[F] = g0[F] * s
            c, _ = shape(g["100"], g["110"], g["111"])
            if seq and {seq[-1], c} == {"truncated_cube", "truncated_octahedron"}:
                seq.append("cuboctahedron")      # the cuboctahedron is the single line y = 2/sqrt3: crossed, never sampled
            if not seq or seq[-1] != c: seq.append(c)
        paths[F] = seq
    gen = sorted({c for seq in paths.values() for c in seq})
    seen = sorted(set(lab[lab.mof == m].morphology) & ONMAP)
    off = sorted(set(lab[lab.mof == m].morphology) - ONMAP)
    cover = [c for c in seen if c in gen]
    out[m] = dict(baseline_source=src, baseline=base, paths=paths, generated=gen, lab_on_map=seen,
                  lab_covered=cover, lab_off_map=off)
    print(f"\n{m} (baseline from {src}): additive-free prediction = {base}")
    for F, seq in paths.items(): print(f"   lower g{F}: {' -> '.join(seq)}")
    print(f"   lab shapes on the map: {seen}; generated: {len(cover)}/{len(seen)}; off the map: {off}")
json.dump(out, open(_os.path.join(HERE, "possible_morphs.json"), "w"), indent=1)
