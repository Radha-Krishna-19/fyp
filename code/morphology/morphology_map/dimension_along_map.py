"""Link to the spectrum work: does the graph read-out r_half/D (dimension profile, run_04) move
monotonically along the morphology map? MOF-5 particles of ~4000 blocks are cut from the
quotient graph for shapes along the two map axes; r_half/D is measured exactly as in run_04
(64 random centres per seed; seeds 0, 1, 2 here to save time; run_04 used 5)."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import sys, os, json, numpy as np
REPO = sys.argv[1] if len(sys.argv) > 1 else REPO_ROOT
sys.path.insert(0, os.path.join(REPO, "code", "spectrum_shape_relation"))
import particle_graph_tools as T
import run_02_spectrum_of_predicted_crystal_shapes_MOF5 as R2
import run_04_dimension_profile_of_crystal_particles as R4
from cubic_wulff import shape
R4.SEEDS = (0, 1, 2)
q = T.load_quotient_graph_with_positions(R4.CIF)
keys, xyz = T.all_block_positions(q, R2.CLOUD_HALF_WIDTH)
S3 = 3 ** 0.5
AXES = {"{100}-{111}": [dict(g100=1.0, g110=9.0, g111=y) for y in (0.50, 0.65, 0.80, 0.95, 2 / S3, 1.35, 1.55, 1.80)],
        "{100}-{110}": [dict(g100=1.0, g110=x, g111=9.0) for x in (0.60, 0.80, 1.00, 1.20, 1.45)]}
out = {}
for axis, pts in AXES.items():
    rows = []
    for g in pts:
        name, fr = shape(g["g100"], g["g110"], g["g111"])
        normals, dists = T.polyhedron_from_family_distances({"{100}": g["g100"], "{110}": g["g110"], "{111}": g["g111"]})
        scale = T.scale_for_block_count(xyz, normals, dists, 4000)
        G, pieces = T.graph_of_selected_blocks(q, keys, T.inside(xyz, normals, dists, scale))
        p = R4.mass_radius_profile(G)
        rows.append(dict(ratio=round(g["g111"] if axis == "{100}-{111}" else g["g110"], 4), shape=name,
                         blocks=p["blocks"], diameter=p["diameter"], r_half_over_D=p["r_half_over_D_mean"],
                         sd=p["r_half_over_D_sd"], d_at_r_half=p["d_at_r_half_mean"]))
        print(axis, rows[-1], flush=True)
    v = [r["r_half_over_D"] for r in rows]
    mono = all(b >= a for a, b in zip(v, v[1:])) or all(b <= a for a, b in zip(v, v[1:]))
    out[axis] = dict(points=rows, monotone=mono)
    print(axis, "monotone in the ratio:", mono, flush=True)
json.dump(out, open(_os.path.join(HERE, "dimension_along_map.json"), "w"), indent=1)
