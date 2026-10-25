"""
run_02_spectrum_of_predicted_crystal_shapes_MOF5.py
===================================================

QUESTION
--------
The morphology half of the project predicts DIFFERENT crystal shapes for the same MOF,
depending on the method:

    method                         MOF-5 shape it predicts     where the numbers come from
    BFDH (face spacing)            truncated octahedron        morphology/results/hybrid_results.json  R_bfdh
    BFDH x Wulff blend, w = 0.5    truncated cube              same file, R = R_bfdh^0.5 * R_wulff^0.5
    UFF Wulff (force field)        cube                        same file, R_wulff
    CHGNet cleavage Wulff          truncated octahedron        morphology/results/chgnet_cleavage_results.json
                                                               ['MOF-5']['all_slabs']['gamma']

If we build each predicted crystal as a finite particle of MOF-5 (same number of building
blocks) and measure the multifractal spectrum width Delta-alpha of its graph, do the
predicted shapes give different Delta-alpha? If yes, the connectivity descriptor of the first
half of the project carries information about the morphology predicted in the second half.

Three reference polyhedra are added so the result can be read against simple shapes:
cube {100}, octahedron {111} and rhombic dodecahedron {110}.

METHOD
------
1. Quotient graph of MOF-5 (32 blocks per conventional cubic cell) with a Cartesian centroid
   for every block (particle_graph_tools.load_quotient_graph_with_positions).
2. A cloud of blocks over cells -7..7 on each axis (15^3 cells, 108 000 blocks).
3. For each shape: scale the polyhedron until it holds the target number of blocks
   (2000 and 4000, two sizes so we can see whether the ordering of shapes survives a change
   of size), take the graph of those blocks, keep its largest connected piece.
4. Delta-alpha with the band settings, five seeds (particle_graph_tools.spectrum_width).
5. Size control: centroid-cut CUBES at eight sizes give two trends,
       Delta-alpha = a + b ln D   (D = graph diameter in steps)
       Delta-alpha = c + d ln N   (N = number of blocks in the particle)
   For each shape we report how far it lies from each trend at its own D and its own N.
   Both are needed. In a pcu net the graph distance behaves like the "taxicab" (L1) distance,
   so an octahedron (the L1 ball) has a much SMALLER diameter than a cube with the same
   number of blocks. Comparing at equal N ("same amount of crystal") is therefore the fairer
   test of shape; comparing at equal D shows how much of the effect is just the diameter.

OUTPUT
------
results/02_predicted_crystal_shapes_MOF5.json      every number used on the website
Run time: about 5 to 10 minutes on a laptop.

LIMITS (also stated on the website)
-----------------------------------
* One MOF. MOF-5 is the only one of the four demonstration MOFs whose file holds an
  orthogonal conventional cell AND whose block graph is connected (see run_01 for ZIF-8).
* A block is inside the particle if its centroid is inside the polyhedron, so the surface is
  a staircase at the scale of one building block.
* The error bar is the spread over random seeds of the box covering, not the method's error.
"""
import json
import os
import time

import numpy as np

import particle_graph_tools as T

CIF = os.path.join(T.PYDIR, 'MOF5.cif')
HYBRID_JSON = os.path.join(T.MORPHDIR, 'results', 'hybrid_results.json')
CHGNET_JSON = os.path.join(T.MORPHDIR, 'results', 'chgnet_cleavage_results.json')
OUT = os.path.join(T.RESULTS, '02_predicted_crystal_shapes_MOF5.json')

TARGET_BLOCKS = (2000, 4000)                  # two particle sizes
CUBE_TREND_TARGETS = (500, 1000, 1500, 2000, 3000, 4000, 6000, 8000)
CLOUD_HALF_WIDTH = 7                          # cells -7..7 on each axis


def predicted_shapes():
    """Distance R of every face family for each shape, read from the morphology results."""
    hy = json.load(open(HYBRID_JSON))['MOF-5']
    ch = json.load(open(CHGNET_JSON))['MOF-5']['all_slabs']['gamma']
    Rb, Rw = hy['R_bfdh'], hy['R_wulff']
    blend = {k: Rb[k] ** 0.5 * Rw[k] ** 0.5 for k in Rb}
    return {
        'cube {100} (reference)': {'{100}': 1.0},
        'octahedron {111} (reference)': {'{111}': 1.0},
        'rhombic dodecahedron {110} (reference)': {'{110}': 1.0},
        'BFDH prediction': dict(Rb),
        'BFDH x Wulff blend w=0.5': blend,
        'UFF Wulff prediction': dict(Rw),
        'CHGNet cleavage Wulff prediction': dict(ch),
    }


def measure(q, keys, xyz, R_by_family, target):
    normals, dists = T.polyhedron_from_family_distances(R_by_family)
    scale = T.scale_for_block_count(xyz, normals, dists, target)
    sel = T.inside(xyz, normals, dists, scale)
    G, pieces = T.graph_of_selected_blocks(q, keys, sel)
    s = T.spectrum_width(G)
    s.update(blocks_inside=int(sel.sum()), blocks_in_largest_piece=G.number_of_nodes(),
             edges=G.number_of_edges(), pieces=int(pieces), scale_angstrom=float(scale))
    return s


def main():
    os.makedirs(T.RESULTS, exist_ok=True)
    t0 = time.time()
    q = T.load_quotient_graph_with_positions(CIF)
    print(f'MOF-5: {len(q["blocks"])} blocks and {len(q["edges"])} edges per cell; '
          f'cell lengths {np.linalg.norm(q["cell"], axis=1).round(3)} A')
    keys, xyz = T.all_block_positions(q, CLOUD_HALF_WIDTH)

    # ---- 1. size trend from cubes ---------------------------------------------------------
    cube = {'{100}': 1.0}
    trend_points = []
    for n in CUBE_TREND_TARGETS:
        r = measure(q, keys, xyz, cube, n)
        trend_points.append(r)
        print(f'  cube trend  target {n:5d}: blocks {r["blocks_in_largest_piece"]:5d}  D {r["diameter"]:3d}  '
              f'width {r["width_mean"]:.3f} +- {r["width_sd"]:.3f}', flush=True)
    a, b = T.fit_size_trend([p['diameter'] for p in trend_points], [p['width_mean'] for p in trend_points])
    resid = [p['width_mean'] - (a + b * np.log(p['diameter'])) for p in trend_points]
    print(f'  trend: width = {a:.3f} + {b:.3f} ln D   (largest |residual| {max(map(abs, resid)):.3f})')
    c, d = T.fit_size_trend([p['blocks_in_largest_piece'] for p in trend_points], [p['width_mean'] for p in trend_points])
    residN = [p['width_mean'] - (c + d * np.log(p['blocks_in_largest_piece'])) for p in trend_points]
    print(f'  trend: width = {c:.3f} + {d:.3f} ln N   (largest |residual| {max(map(abs, residN)):.3f})')

    # ---- 2. every shape at every target size ------------------------------------------------
    shapes = predicted_shapes()
    rows = []
    for target in TARGET_BLOCKS:
        for name, R in shapes.items():
            r = measure(q, keys, xyz, R, target)
            r.update(shape=name, target_blocks=target, R_by_family={k: round(v, 4) for k, v in R.items()})
            r['trend_value_at_D'] = a + b * np.log(r['diameter'])
            r['difference_from_cube_trend'] = r['width_mean'] - r['trend_value_at_D']
            r['trend_value_at_N'] = c + d * np.log(r['blocks_in_largest_piece'])
            r['difference_from_cube_trend_at_equal_blocks'] = r['width_mean'] - r['trend_value_at_N']
            rows.append(r)
            print(f'  {target:5d}  {name:42s} blocks {r["blocks_in_largest_piece"]:5d}  D {r["diameter"]:3d}  '
                  f'width {r["width_mean"]:.3f} +- {r["width_sd"]:.3f}  vs cube trend: at same D {r["difference_from_cube_trend"]:+.3f}, '
                  f'at same N {r["difference_from_cube_trend_at_equal_blocks"]:+.3f}',
                  flush=True)

    out = dict(structure='MOF-5', cif='code/spectrum_pipeline/MOF5.cif',
               settings=dict(top_fraction=T.TOP_FRACTION, window_fraction=T.WINDOW_FRACTION,
                             n_trials=T.N_TRIALS, seeds=list(T.SEEDS), cloud_half_width=CLOUD_HALF_WIDTH),
               cube_trend=dict(a=a, b=b, points=trend_points, max_abs_residual=float(max(map(abs, resid))),
                               c_blocks=c, d_blocks=d, max_abs_residual_blocks=float(max(map(abs, residN)))),
               shapes=rows, seconds=round(time.time() - t0, 1))
    json.dump(out, open(OUT, 'w'), indent=1, default=float)
    print('wrote', OUT, f'({out["seconds"]} s)')


if __name__ == '__main__':
    main()
