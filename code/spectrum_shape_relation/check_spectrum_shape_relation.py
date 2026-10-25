"""
check_spectrum_shape_relation.py
================================

Checks for the spectrum <-> shape study. Run after the three run_0x scripts:

    python check_spectrum_shape_relation.py

Each check prints PASS or FAIL with what was tested. The script exits with status 1 if any
check fails. The checks are of three kinds:

  A. the tools are right on cases whose answer is known by hand;
  B. the two independent routes to the box-particle numbers agree (run_01 vs code_19);
  C. the saved results are internally consistent (sizes matched, counts complete, the
     statistics recomputed from the saved table give the saved values).
"""
import json
import os
import sys

import numpy as np
from scipy import stats

import particle_graph_tools as T

RES = T.RESULTS
fails = 0


def ok(cond, msg):
    global fails
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    fails += 0 if cond else 1


# ---- A. tools on known cases ---------------------------------------------------------------
# A cube {100} with R = 1 contains the points with max(|x|,|y|,|z|) <= 1.
g = np.array([[x, y, z] for x in range(-3, 4) for y in range(-3, 4) for z in range(-3, 4)], float)
n, d = T.polyhedron_from_family_distances({'{100}': 1.0})
ok(len(n) == 6 and T.inside(g, n, d, 1.0).sum() == 27, 'cube {100}: 6 faces, 27 lattice points with |x|,|y|,|z| <= 1')
# An octahedron {111} with R = 1/sqrt(3) * 1 contains |x|+|y|+|z| <= 1 -> 7 lattice points.
n, d = T.polyhedron_from_family_distances({'{111}': 1.0})
ok(len(n) == 8 and T.inside(g, n, d, 1 / np.sqrt(3)).sum() == 7, 'octahedron {111}: 8 faces, 7 points with |x|+|y|+|z| <= 1')
n, d = T.polyhedron_from_family_distances({'{110}': 1.0})
ok(len(n) == 12, 'rhombic dodecahedron {110}: 12 faces')
ok(abs(T.fit_size_trend([10, 20, 40], [1 + 0.5 * np.log(10), 1 + 0.5 * np.log(20), 1 + 0.5 * np.log(40)])[1] - 0.5) < 1e-9,
   'size-trend fit recovers a known slope')

sys.path.insert(0, T.HERE)
import run_03_core_mof_spectrum_width_vs_bfdh_shape as R3
x = np.random.default_rng(1).normal(size=30)
y = x + np.random.default_rng(2).normal(size=30)
ok(abs(R3.spearman(x, y) - stats.spearmanr(x, y).correlation) < 1e-12, 'our Spearman equals scipy.stats.spearmanr')

# ---- B. two routes agree ------------------------------------------------------------------------
p1 = os.path.join(RES, '01_box_particles_MOF5.json')
if os.path.exists(p1):
    r1 = json.load(open(p1))
    c = r1.get('check_against_code_19', {})
    ok(c.get('same_graphs') is True, 'run_01 builds the same box graphs as code_19 (nodes and diameters)')
    ok(c.get('largest_width_difference', 1) < 1e-9, 'run_01 and code_19 give identical widths')
    ok(all(r['components'] == 1 for r in r1['shapes'] + r1['cubes']), 'every MOF-5 box particle is one connected piece')
    cube = next(r for r in r1['shapes'] if r['label'].startswith('cube'))
    others = [r for r in r1['shapes'] if not r['label'].startswith('cube')]
    spread = max(r['width_sd'] for r in r1['shapes'])
    ok(all(cube['width_mean'] - r['width_mean'] > 5 * spread for r in others),
       'cube width exceeds slab, plate and rod by more than 5x the seed spread')
else:
    ok(False, 'results/01_box_particles_MOF5.json exists')

# ---- C. saved results are consistent --------------------------------------------------------------
p2 = os.path.join(RES, '02_predicted_crystal_shapes_MOF5.json')
if os.path.exists(p2):
    r2 = json.load(open(p2))
    worst = max(abs(r['blocks_in_largest_piece'] - r['target_blocks']) / r['target_blocks'] for r in r2['shapes'])
    ok(worst < 0.15, f'every predicted-shape particle is within 15% of its target size (worst {worst:.1%})')
    ok(all(r['n_ok'] == len(T.SEEDS) for r in r2['shapes']), 'every predicted-shape spectrum passed on all seeds')
    ok(r2['cube_trend']['max_abs_residual_blocks'] < 0.06, 'the cube trend in block count fits within 0.06')
    for r in r2['shapes']:
        again = r['width_mean'] - (r2['cube_trend']['c_blocks'] + r2['cube_trend']['d_blocks'] * np.log(r['blocks_in_largest_piece']))
        if abs(again - r['difference_from_cube_trend_at_equal_blocks']) > 1e-9:
            ok(False, f'difference at equal blocks recomputes for {r["shape"]}')
            break
    else:
        ok(True, 'every "difference at equal blocks" recomputes from the saved trend')
else:
    ok(False, 'results/02_predicted_crystal_shapes_MOF5.json exists')

p3 = os.path.join(RES, '03_core_mof_spectrum_vs_bfdh_shape.json')
if os.path.exists(p3):
    r3 = json.load(open(p3))
    band = json.load(open(R3.BAND_JSON))
    usable = sum(1 for r in band['records'] if r.get('ok'))
    ok(r3['n_with_shape'] == usable, f'a BFDH shape was found for every usable CoRE structure ({r3["n_with_shape"]}/{usable})')
    S = r3['structures']
    rho = stats.spearmanr([r['width'] for r in S], [r['aspect_ratio'] for r in S]).correlation
    ok(abs(rho - r3['tests']['all usable']['width vs aspect ratio']['spearman']) < 1e-9,
       'saved rho(width, aspect ratio) recomputes with scipy')
else:
    ok(False, 'results/03_core_mof_spectrum_vs_bfdh_shape.json exists')

print(f'\n{fails} FAILURES' if fails else '\nAll checks passed.')
sys.exit(1 if fails else 0)
