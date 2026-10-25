"""
MODULE 19 -- DOES THE MULTIFRACTAL SPECTRUM SEE CRYSTAL SHAPE?

This module is the bridge between the project's first question (a descriptor from
connectivity alone, the multifractal width Delta-alpha) and the panel's second
question (crystal morphology).

Every earlier spectrum in this project was measured on a torus: the quotient graph
tiled n x n x n with wrap-around (code_12.replicate). A torus has no surface and no
shape. A real crystal is a finite piece, a particle, with faces. Here the quotient
graph is tiled WITHOUT wrap-around inside a box of na x nb x nc unit cells, so the
graph is a finite particle with a surface, and the box can be a cube, a plate or a rod.

Question asked: at the SAME number of unit cells (so the same number of building
blocks), does Delta-alpha depend on the shape of the particle, beyond what its
diameter already explains?

Method
  1. For cubes of side n = 2..6, compute Delta-alpha and the diameter D. Fit
     Delta-alpha = a + b ln D (the size trend that every earlier run found).
  2. For one fixed cell count, cut a cube, a plate and a rod. Compute Delta-alpha and D.
  3. Compare each plate or rod with the value the cube trend predicts at that
     particle's own diameter. Differences are judged against the seed-to-seed spread.

Limits: orthogonal-cell MOFs only (MOF-5, ZIF-8); boxes, not faceted polyhedra;
one parameter set; five seeds. The result is a measurement on these two graphs, not a
general law.
"""
import json, os, sys, time
import numpy as np
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import code_12_converged_band as c12

TOP = 0.20        # influential fraction, as in code_17
WINDOW = 0.50     # fitted-radius window, as in code_17
SEEDS = (0, 1, 2, 3, 4)
NTR = 20


def finite_particle(blocks, edges, na, nb, nc):
    """Quotient graph tiled in a na x nb x nc box of cells, NO wrap-around."""
    K = len(blocks)
    cells = [(a, b, c) for a in range(na) for b in range(nb) for c in range(nc)]
    ci = {cell: i for i, cell in enumerate(cells)}
    G = nx.Graph()
    G.add_nodes_from(range(K * len(cells)))
    for cell in cells:
        for (i, j, t) in edges:
            tgt = (cell[0] + t[0], cell[1] + t[1], cell[2] + t[2])
            if tgt in ci:
                G.add_edge(i * len(cells) + ci[cell], j * len(cells) + ci[tgt])
    return G


def width(G, seed):
    adj = c12._adjacency(G)
    D = c12.fast_diameter(G, adj)
    infl, _ = c12.select_influential(G, TOP)
    s = c12.spectrum(G, infl, n_trials=NTR, seed=seed, diameter=D, window_frac=WINDOW)
    return D, (s['width'] if s.get('ok') else None)


def measure(blocks, edges, box):
    G = finite_particle(blocks, edges, *box)
    comps = nx.number_connected_components(G)
    vals, D = [], None
    for sd in SEEDS:
        D, w = width(G, sd)
        if w is not None:
            vals.append(w)
    return dict(box=list(box), cells=box[0] * box[1] * box[2], nodes=G.number_of_nodes(),
                edges=G.number_of_edges(), components=comps, diameter=D,
                n_ok=len(vals), width_mean=float(np.mean(vals)) if vals else None,
                width_sd=float(np.std(vals, ddof=1)) if len(vals) > 1 else None)


def run(name, cif, cube_sides, fixed_boxes):
    blocks, edges, _ = c12.quotient_graph_from_cif(cif)
    out = dict(structure=name, blocks_per_cell=len(blocks), cubes=[], shapes=[])
    for n in cube_sides:
        t = time.time(); r = measure(blocks, edges, (n, n, n)); r['sec'] = round(time.time() - t, 1)
        out['cubes'].append(r); print(name, 'cube', n, r, flush=True)
    for label, box in fixed_boxes:
        t = time.time(); r = measure(blocks, edges, box); r['label'] = label; r['sec'] = round(time.time() - t, 1)
        out['shapes'].append(r); print(name, label, r, flush=True)
    xs = [np.log(r['diameter']) for r in out['cubes'] if r['width_mean'] is not None and r['diameter'] >= 8]
    ys = [r['width_mean'] for r in out['cubes'] if r['width_mean'] is not None and r['diameter'] >= 8]
    if len(xs) >= 2:
        b, a = np.polyfit(xs, ys, 1)
        out['trend'] = dict(a=float(a), b=float(b), n_points=len(xs))
        for r in out['shapes']:
            if r['width_mean'] is not None and r['diameter'] >= 1:
                r['trend_prediction'] = float(a + b * np.log(r['diameter']))
                r['excess_over_trend'] = r['width_mean'] - r['trend_prediction']
    return out


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'MOF5'
    cfg = {
        'MOF5': ('MOF-5', 'MOF5.cif', (2, 3, 4, 5, 6),
                 [('cube 4x4x4', (4, 4, 4)), ('plate 8x8x1', (8, 8, 1)), ('rod 16x2x2', (16, 2, 2)),
                  ('slab 8x4x2', (8, 4, 2))]),
        'ZIF8': ('ZIF-8', 'ZIF-8.cif', (2, 3, 4, 5, 6),
                 [('cube 4x4x4', (4, 4, 4)), ('plate 8x8x1', (8, 8, 1)), ('rod 16x2x2', (16, 2, 2)),
                  ('slab 8x4x2', (8, 4, 2))]),
    }[which]
    res = run(*cfg)
    path = os.path.join(HERE, '..', '..', 'data', 'spectrum_descriptors', 'size_scaling', f'spectrum_vs_shape_{which}.json')
    json.dump(res, open(path, 'w'), indent=1, default=float)
    print('wrote', path)
