"""
run_04_dimension_profile_of_crystal_particles.py
================================================

QUESTION
--------
Runs 01-03 showed that the multifractal spectrum width (Delta-alpha) of a finite MOF-5
particle is lower for plates and rods than for a cube with the same number of blocks, but
that it does NOT separate the compact crystal shapes predicted by the morphology methods
(BFDH, BFDH x Wulff blend, UFF Wulff, CHGNet Wulff): their widths differ by less than the
scatter of the size trend.

This run applies the mass-radius (cluster-growing) form of box counting, taught in the
Fractals and Scaling course (Santa Fe Institute), to the same particle graphs:

    M(r) = average number of blocks within graph distance r of a block,
    d(r) = d ln M / d ln r          (the local, scale-dependent dimension).

Two questions:
    1. Does d(r) show WHY plates and rods have a lower Delta-alpha, i.e. does the particle
       behave as a lower-dimensional object over a range of scales?
    2. Does the shape of the M(r) curve separate the compact predicted shapes that
       Delta-alpha could not?

METHOD
------
* Particles (all MOF-5, the only demonstration MOF with an orthogonal cell and a connected
  block graph, see run_01):
    - four boxes of 1024 unit cells each (32 768 blocks): cube 10 x 10 x 10 (1000 cells,
      32 000 blocks), slab 16 x 16 x 4, plate 32 x 32 x 1, rod 64 x 4 x 4;
    - the seven polyhedra of run_02 (three references and four predictions) at about
      4000 and 8000 blocks.
* Cluster growing (Song, Havlin and Makse, Nature 433, 392 (2005)): 64 randomly chosen
  centre blocks per seed, five seeds; all graph distances from each centre by breadth-first
  search (scipy.sparse.csgraph.shortest_path, unweighted).
* Read-outs
    d(r)            central difference of ln M against ln r.
    d_at_r_half     d(r) at the radius that holds half of the particle on average.
    r_half_over_D   that radius divided by the largest distance found (the diameter D).
                    A shape that fills its own diameter quickly (a cube in this graph
                    metric) has a small value; a shape whose blocks sit close to the centre
                    relative to its diameter (an octahedron, the "taxicab ball") a large one.
* Calibration: the same calculation on three ideal lattices of known dimension, a path of
  4001 vertices (1), a 121 x 121 square grid (2) and a 41 x 41 x 41 cubic grid (3). On a
  lattice the ball of radius r is a taxicab ball, M(r) = 2r + 1 in one dimension and
  2r^2 + 2r + 1 in two, so the local dimension approaches 1, 2 and 3 only slowly with r and
  then falls as the ball reaches the edge of the finite graph. The peak values of these
  references (about 0.99, 1.83 and 2.64) are what a one-, two- and three-dimensional object
  gives with this method at these sizes; the particles are compared with them, not with the
  ideal 1, 2 and 3.
* The error bar is the standard deviation over the five seeds (choice of centre blocks).
* D is the largest graph distance found from the sampled centres, a lower bound on the
  graph diameter; r_half is an integer radius, so r_half / D moves in steps of 1/D.

OUTPUT
------
results/04_dimension_profile_MOF5.json      every number used on the website and in the figure
Run time: about 1-2 minutes on a laptop.

LIMITS
------
* One MOF and one crystal-building rule (block centroid inside the polyhedron).
* The local dimension of a finite graph never reaches 3, 2 or 1 exactly (see the calibration);
  values are compared between shapes and with the reference lattices.
* r_half_over_D measures shape in the GRAPH metric, in which distance behaves like the
  taxicab (L1) distance for the pcu net of MOF-5. It is a property of the particle graph, and
  it is not claimed to equal any experimental shape measure.
"""
import json
import os
import time

import networkx as nx
import numpy as np
from scipy.sparse.csgraph import shortest_path

import particle_graph_tools as T
import run_02_spectrum_of_predicted_crystal_shapes_MOF5 as R2

CIF = os.path.join(T.PYDIR, 'MOF5.cif')
OUT = os.path.join(T.RESULTS, '04_dimension_profile_MOF5.json')

BOXES = {                     # name -> unit cells along a, b, c (1000 or 1024 cells each)
    'cube 10 x 10 x 10': (10, 10, 10),
    'slab 16 x 16 x 4': (16, 16, 4),
    'plate 32 x 32 x 1': (32, 32, 1),
    'rod 64 x 4 x 4': (64, 4, 4),
}
POLY_TARGETS = (4000, 8000)
N_CENTRES = 64
SEEDS = (0, 1, 2, 3, 4)


def distances_from_random_centres(G, seed):
    """Graph distances from N_CENTRES random blocks to every block (rows = centres)."""
    A = nx.to_scipy_sparse_array(G, format='csr')
    rng = np.random.default_rng(seed)
    centres = rng.choice(G.number_of_nodes(), min(N_CENTRES, G.number_of_nodes()), replace=False)
    return shortest_path(A, directed=False, unweighted=True, indices=centres)


def mass_radius_profile(G):
    """Average M(r), local dimension d(r) and the read-outs, with spread over SEEDS."""
    N = G.number_of_nodes()
    per_seed = []
    for seed in SEEDS:
        D = distances_from_random_centres(G, seed)
        diameter = int(D.max())
        r = np.arange(1, diameter + 1)
        M = np.array([(D <= k).sum(axis=1).mean() for k in r])
        lr, lm = np.log(r), np.log(M)
        d = np.full(len(r), np.nan)
        d[1:-1] = (lm[2:] - lm[:-2]) / (lr[2:] - lr[:-2])
        i_half = int(np.searchsorted(M, N / 2.0))
        per_seed.append(dict(r=r, M=M, d=d, diameter=diameter, r_half=int(r[i_half]),
                             d_at_r_half=float(d[i_half]) if 0 < i_half < len(r) - 1 else None))
    # average the curves over seeds on the common radius range
    rmax = min(p['diameter'] for p in per_seed)
    M_mean = np.mean([p['M'][:rmax] for p in per_seed], axis=0)
    d_stack = np.array([p['d'][:rmax] for p in per_seed])
    d_mean = np.array([np.nan if np.all(np.isnan(c)) else np.nanmean(c) for c in d_stack.T])
    ratio = [p['r_half'] / p['diameter'] for p in per_seed]
    dh = [p['d_at_r_half'] for p in per_seed if p['d_at_r_half'] is not None]
    return dict(
        blocks=N,
        diameter=int(max(p['diameter'] for p in per_seed)),
        r=list(range(1, rmax + 1)),
        M_mean=[round(float(x), 2) for x in M_mean],
        d_mean=[None if np.isnan(x) else round(float(x), 4) for x in d_mean],
        d_peak=round(float(np.nanmax(d_mean)), 3),
        r_half_over_D_mean=round(float(np.mean(ratio)), 4),
        r_half_over_D_sd=round(float(np.std(ratio, ddof=1)), 4),
        d_at_r_half_mean=round(float(np.mean(dh)), 3) if dh else None,
        d_at_r_half_sd=round(float(np.std(dh, ddof=1)), 3) if len(dh) > 1 else None,
    )


REFERENCE_LATTICES = {        # name -> (dimension, graph)
    'path, 4001 vertices': (1, lambda: nx.path_graph(4001)),
    'square grid 121 x 121': (2, lambda: nx.grid_2d_graph(121, 121)),
    'cubic grid 41 x 41 x 41': (3, lambda: nx.grid_graph([41, 41, 41])),
}


def main():
    os.makedirs(T.RESULTS, exist_ok=True)
    t0 = time.time()
    q = T.load_quotient_graph_with_positions(CIF)

    references = {}
    for name, (dim, make) in REFERENCE_LATTICES.items():
        p = mass_radius_profile(nx.convert_node_labels_to_integers(make()))
        p['dimension'] = dim
        references[name] = p
        print(f'  reference {name:24s} (dimension {dim})  peak d {p["d_peak"]:.2f}  '
              f'd at r_half {p["d_at_r_half_mean"]:.2f}', flush=True)

    boxes = {}
    for name, (a, b, c) in BOXES.items():
        G = T.box_particle(q, a, b, c)
        boxes[name] = mass_radius_profile(G)
        boxes[name]['cells'] = [a, b, c]
        p = boxes[name]
        print(f'  box  {name:20s} N {p["blocks"]:6d}  D {p["diameter"]:4d}  peak d {p["d_peak"]:.2f}  '
              f'd at r_half {p["d_at_r_half_mean"]:.2f} +- {p["d_at_r_half_sd"]:.2f}', flush=True)

    keys, xyz = T.all_block_positions(q, R2.CLOUD_HALF_WIDTH)
    polys = []
    for target in POLY_TARGETS:
        for name, R in R2.predicted_shapes().items():
            normals, dists = T.polyhedron_from_family_distances(R)
            scale = T.scale_for_block_count(xyz, normals, dists, target)
            G, pieces = T.graph_of_selected_blocks(q, keys, T.inside(xyz, normals, dists, scale))
            p = mass_radius_profile(G)
            p.update(shape=name, target_blocks=target, pieces=int(pieces))
            polys.append(p)
            print(f'  poly {target:5d} {name:40s} N {p["blocks"]:5d}  D {p["diameter"]:3d}  '
                  f'r_half/D {p["r_half_over_D_mean"]:.3f} +- {p["r_half_over_D_sd"]:.3f}', flush=True)

    # spread of r_half/D across the compact shapes vs the seed noise, per size
    summary = {}
    for target in POLY_TARGETS:
        vals = [p['r_half_over_D_mean'] for p in polys if p['target_blocks'] == target]
        sds = [p['r_half_over_D_sd'] for p in polys if p['target_blocks'] == target]
        summary[str(target)] = dict(range_min=min(vals), range_max=max(vals),
                                    spread=round(max(vals) - min(vals), 4), largest_seed_sd=max(sds))
    out = dict(
        produced_by='code/spectrum_shape_relation/run_04_dimension_profile_of_crystal_particles.py',
        method=dict(n_centres=N_CENTRES, seeds=list(SEEDS), structure='MOF-5 (pcu)',
                    reference='Song, Havlin and Makse, Nature 433, 392 (2005): cluster-growing'),
        reference_lattices=references, boxes=boxes, polyhedra=polys, compact_shape_separation=summary,
        run_seconds=round(time.time() - t0, 1),
    )
    json.dump(out, open(OUT, 'w'), indent=1)
    print('wrote', OUT, f'({time.time() - t0:.0f} s)')


if __name__ == '__main__':
    main()
