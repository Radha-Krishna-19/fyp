"""
run_01_spectrum_of_box_particles_same_cell_count.py
===================================================

QUESTION
--------
Same MOF, same number of unit cells, different particle shape (cube, slab, plate, rod):
does the spectrum width Delta-alpha change? And is the change more than what the change of
graph diameter alone would cause?

This is the first and simplest bridge between the two halves of the project. Every spectrum in
the first half was measured on a torus (no surface, no shape). Here the quotient graph is tiled
WITHOUT wrap-around inside a box of na x nb x nc unit cells, so the particle has a surface and
a shape.

    shape         box (cells)   unit cells
    cube          4 x 4 x 4     64
    slab          8 x 4 x 2     64
    plate         8 x 8 x 1     64
    rod          16 x 2 x 2     64

A size trend Delta-alpha = a + b ln D is fitted on cubes of side 2 ... 6, and each shape is
compared with what that trend predicts at the shape's own diameter D.

This script reproduces code/spectrum_pipeline/code_19_spectrum_vs_shape.py using the shared tools in
particle_graph_tools.py, and then CHECKS that both give the same numbers (two routes to the
same result, as the project's house rule asks).

STRUCTURES
----------
MOF-5 (code/spectrum_pipeline/MOF5.cif, conventional cubic cell, 32 blocks per cell).
ZIF-8 (code/spectrum_pipeline/ZIF-8.cif) is also run, but its block graph falls apart into many pieces even
for a plain cube, so its numbers are recorded and NOT used for any conclusion. HKUST-1 and
UiO-66 files hold primitive (non-orthogonal) cells and are not cut as boxes.

OUTPUT
------
results/01_box_particles_MOF5.json, results/01_box_particles_ZIF8.json
Run time: about 4 minutes per structure.
"""
import json
import os
import sys
import time

import networkx as nx
import numpy as np

import particle_graph_tools as T

CUBE_SIDES = (2, 3, 4, 5, 6)
SHAPES = [('cube 4x4x4', (4, 4, 4)), ('plate 8x8x1', (8, 8, 1)),
          ('rod 16x2x2', (16, 2, 2)), ('slab 8x4x2', (8, 4, 2))]
STRUCTURES = {'MOF5': ('MOF-5', 'MOF5.cif'), 'ZIF8': ('ZIF-8', 'ZIF-8.cif')}
CODE19_JSON = os.path.join(T.REPO, 'data', 'spectrum_descriptors', 'size_scaling', 'spectrum_vs_shape_{}.json')


def measure_box(q, box):
    G = T.box_particle(q, *box)
    r = T.spectrum_width(G)
    r.update(box=list(box), cells=box[0] * box[1] * box[2], nodes=G.number_of_nodes(),
             edges=G.number_of_edges(), components=nx.number_connected_components(G))
    return r


def run(key):
    name, cif = STRUCTURES[key]
    t0 = time.time()
    q = T.load_quotient_graph_with_positions(os.path.join(T.PYDIR, cif))
    out = dict(structure=name, blocks_per_cell=len(q['blocks']), cubes=[], shapes=[])
    for n in CUBE_SIDES:
        r = measure_box(q, (n, n, n))
        out['cubes'].append(r)
        print(f'  {name} cube {n}: nodes {r["nodes"]:5d} pieces {r["components"]:3d} D {r["diameter"]:3d} '
              f'width {r["width_mean"]:.3f} +- {r["width_sd"]:.3f}', flush=True)
    a, b = T.fit_size_trend([r['diameter'] for r in out['cubes']], [r['width_mean'] for r in out['cubes']])
    out['trend'] = dict(a=a, b=b)
    for label, box in SHAPES:
        r = measure_box(q, box)
        r['label'] = label
        r['trend_prediction'] = a + b * np.log(r['diameter'])
        r['excess_over_trend'] = r['width_mean'] - r['trend_prediction']
        out['shapes'].append(r)
        print(f'  {name} {label:12s}: D {r["diameter"]:3d} width {r["width_mean"]:.3f} +- {r["width_sd"]:.3f} '
              f'trend {r["trend_prediction"]:.3f} difference {r["excess_over_trend"]:+.3f}', flush=True)

    # ---- cross-check against code_19 (independent script, same method) -------------------
    ref_path = CODE19_JSON.format(key)
    if os.path.exists(ref_path):
        ref = json.load(open(ref_path))
        pairs = list(zip(ref['shapes'], out['shapes'])) + list(zip(ref['cubes'], out['cubes']))
        worst = max(abs(x['width_mean'] - y['width_mean']) for x, y in pairs)
        same_graph = all(x['nodes'] == y['nodes'] and x['diameter'] == y['diameter'] for x, y in pairs)
        out['check_against_code_19'] = dict(same_graphs=same_graph, largest_width_difference=worst)
        print(f'  check against code_19: same graphs {same_graph}, largest width difference {worst:.2e}')
    out['seconds'] = round(time.time() - t0, 1)
    path = os.path.join(T.RESULTS, f'01_box_particles_{key}.json')
    json.dump(out, open(path, 'w'), indent=1, default=float)
    print('wrote', path)


if __name__ == '__main__':
    os.makedirs(T.RESULTS, exist_ok=True)
    for key in (sys.argv[1:] or ['MOF5', 'ZIF8']):
        run(key)
