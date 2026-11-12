"""Condition series on the morphology map. For every controlled series in the dataset where one
condition increases, the shapes are placed on the two map axes:
  {100}->{111} axis: cube 0, truncated_cube 1, cuboctahedron 2, truncated_octahedron 3, octahedron 4
  {100}->{110} axis: cube 0, cube_truncated_edges 1, truncated_rhombic_dodecahedron 2, rhombic_dodecahedron 3
Gibbs adsorption (d gamma_F = -Gamma_F d mu) says an additive that binds one face family F lowers
gamma_F monotonically with its chemical potential, so its series must move monotonically toward F's
corner of the map. A series 'passes' if every step stays on one axis and never moves backwards.
Shapes off the cubic map (plate, irregular, other, ...) end the testable part of a series."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import json, sys, pandas as pd
A111 = {"cube": 0, "truncated_cube": 1, "cuboctahedron": 2, "truncated_octahedron": 3, "octahedron": 4}
A110 = {"cube": 0, "cube_truncated_edges": 1, "truncated_rhombic_dodecahedron": 2, "rhombic_dodecahedron": 3}
d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else LAB_CSV).set_index("record_id")
# (series name, increasing condition, record ids in increasing order) -- order taken from the
# records' own additive_amount / linker_to_metal / time_h fields, listed for checking
SERIES = [
    ("HKUST-1 + lauric acid (umemura2011)", "modulator: lowest -> intermediate -> highest", ["HKUST-1-umemura2011-1", "HKUST-1-umemura2011-2", "HKUST-1-umemura2011-3"]),
    ("HKUST-1 + inorganic salt (liu2016)", "salt: low -> intermediate -> high", ["HKUST-1-liu2016-1", "HKUST-1-liu2016-2", "HKUST-1-liu2016-3"]),
    ("HKUST-1 + SDS (wu2020)", "SDS: low -> intermediate -> high", ["HKUST-1-wu2020-1", "HKUST-1-wu2020-2", "HKUST-1-wu2020-3"]),
    ("HKUST-1 + CTAB (ediati2019)", "CTAB:H3BTC 0 -> 0.3 -> 0.6", ["HKUST-1-ediati2019-1", "HKUST-1-ediati2019-2", "HKUST-1-ediati2019-3"]),
    ("MOF-5 + H3BTB (suresh2021)", "BTB 0 -> ~2 -> ~4 -> >4 mol %", ["MOF-5-suresh2021-6", "MOF-5-suresh2021-7", "MOF-5-suresh2021-8", "MOF-5-suresh2021-9"]),
    ("ZIF-8, Hmim/Zn ratio (zhang2018)", "Hmim/Zn 1 -> 2 -> 4 -> 8 -> 16", [f"ZIF-8-zhang2018-{i}" for i in range(1, 6)]),
    ("ZIF-8, time (cravillon2012)", "time 0.25 -> 0.33 -> 0.75 -> 4 h", [f"ZIF-8-cravillon2012-{i}" for i in range(1, 5)]),
    ("ZIF-8 + TRIS (zheng2017)", "TRIS 10 -> 50 -> 100 mM", ["ZIF-8-zheng2017-2", "ZIF-8-zheng2017-3", "ZIF-8-zheng2017-4"]),
    ("UiO-66, modulator (schaate2011)", "benzoic/acetic acid low -> high", ["UiO-66-schaate2011-1", "UiO-66-schaate2011-2"]),
    ("UiO-66, temperature (ahmad2025)", "120 -> 130 -> 140 C", ["UiO-66-ahmad2025-1", "UiO-66-ahmad2025-2", "UiO-66-ahmad2025-3"]),
]
out = []
for name, cond, ids in SERIES:
    shapes = [d.loc[i, "morphology"] for i in ids]
    on = []
    for s in shapes:
        if s in A111 or s in A110: on.append(s)
        else: break
    axis, ok, why = None, True, ""
    if len(on) < 2:
        ok, why = None, "fewer than two shapes on the cubic map"
    else:
        p111 = [A111.get(s) for s in on]; p110 = [A110.get(s) for s in on]
        if all(v is not None for v in p111) and len(set(p111)) > 1: axis, pos = "{100}-{111}", p111
        elif all(v is not None for v in p110) and len(set(p110)) > 1: axis, pos = "{100}-{110}", p110
        elif len(set(on)) == 1: axis, pos, ok, why = "no movement", [], None, "shape does not change on the map"
        else: axis, pos, ok, why = "mixed", [], False, "moves between axes"
        if pos:
            steps = [b - a for a, b in zip(pos, pos[1:])]
            if any(s > 0 for s in steps) and any(s < 0 for s in steps): ok, why = False, "reverses direction"
            elif axis.startswith("{"):
                toward = ("{111}" if axis == "{100}-{111}" else "{110}") if pos[-1] > pos[0] else "{100}"
                why = f"moves toward {toward}"
    left = shapes[len(on):]
    out.append(dict(series=name, condition=cond, shapes=shapes, axis=axis, monotone=ok, result=why,
                    leaves_map_at=left[0] if left else None))
    print(f"{name:40s} {' -> '.join(shapes):75s} | {axis} | {'PASS' if ok else ('n/a' if ok is None else 'FAIL')} {why}"
          + (f" | then leaves the map ({left[0]})" if left else ""))
# chance of a monotone order if the same shapes were listed in a random order
from itertools import permutations
from math import prod
pvals = []
for r in out:
    if r["monotone"] and r["axis"] and r["axis"].startswith("{"):
        A = A111 if r["axis"] == "{100}-{111}" else A110
        on = [s for s in r["shapes"] if s in A]
        perms = set(permutations([A[s] for s in on]))
        mono = sum(1 for q in perms if all(b >= a for a, b in zip(q, q[1:])) or all(b <= a for a, b in zip(q, q[1:])))
        r["p_monotone_by_chance"] = round(mono / len(perms), 4); pvals.append(mono / len(perms))
n_move = len(pvals)
print(f"series that move on the map: {n_move}, all monotone; chance that all {n_move} are monotone if orders were random: {prod(pvals):.2e}")
json.dump(dict(series=out, n_moving=n_move, joint_chance=prod(pvals)), open(_os.path.join(HERE, "series_results.json"), "w"), indent=1)
