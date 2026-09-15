"""
MODULE 17 -- THE FULL, CORRECT BAND ON BOTH DATASETS

WHY THIS MODULE EXISTS
Both published bands (the 77-framework hMOF CSV and the 61-framework CoRE MOF
CSV) ran the multifractal analysis on the ATOMIC supercell graph. This module
runs it correctly -- on the COARSE-GRAINED supercell graph -- across the full
77 and 61 structures (not a capped sample), and computes a full set of graph
statistics per structure (not just Delta-alpha), so the resulting sub-bands
can be explained rather than just observed.

THE GRAPH, STATED ONCE, PRECISELY
  1. Decompose the unit cell into building blocks (metal-oxo algorithm).
  2. Build the LABELLED QUOTIENT GRAPH of those blocks: one vertex per block,
     one edge per inter-block bond, each edge carrying the integer lattice
     translation t it crosses (code_09.build_periodic_block_graph). This is
     "the coarse-grained unit cell" -- typically a handful of vertices.
  3. REPLICATE that block graph n x n x n using t on every edge
     (code_12.replicate). This is exact and combinatorial: no atoms are ever
     built, so reaching a real diameter costs vertices, not atoms. This is
     "the coarse-grained supercell", and it is the graph the spectrum is
     computed on.
  4. Box-cover this graph, sweep q, fit tau(q) through the origin, Legendre
     transform to alpha(q) and f(alpha). Delta-alpha = max(alpha) - min(alpha).

WHY NOT THE OTHER THREE CANDIDATES
  - Coarse-grained UNIT CELL (skip step 3): diameter ~2 for most structures.
    No range of radii to fit a power law over. Necessary but not sufficient.
  - ATOMIC unit cell / ATOMIC supercell (skip step 2, or do 2 after building
    an atomic supercell): mixes two length scales -- molecular (inside one
    block) and framework (between blocks) -- into one fit. This is what both
    published bands actually did (see CLAUDE.md); code_13 measures the
    resulting error directly on the four demonstration structures.
  - "Coarse-grain AFTER an atomic supercell, to save memory": still builds
    the atomic supercell first, so it is capped by MAX_ATOMS long before the
    coarse-grained graph would need to stop. Coarse-graining the unit cell
    FIRST (step 2 before step 3) means replication in step 3 is free of
    atoms entirely -- more blocks, not more atoms, is what a bigger n buys.

SIZING RULE (stated explicitly, applied uniformly to every structure)
Replicate until every lattice direction reaches TARGET_CELL_LENGTH (default
48 A, matching the physical target the original notebooks used for their
-- wrong -- atomic supercell), capped at MAX_NODES coarse vertices so the
full-dataset run stays affordable. This is a real, stated rule, not a
per-structure tuned choice.

WHAT IS COMPUTED PER STRUCTURE
  - Delta-alpha, alpha_0, asymmetry A, r2_linearity (the spectrum)
  - n_blocks (unit cell), cg_nodes, cg_edges, diameter (the supercell graph)
  - degree_mean, degree_std, degree_cv, degree_min, degree_max
  - degree_entropy_norm (heterogeneity)
  - assortativity (degree-degree correlation across edges)
  - avg_clustering (triangle density)
  - n_components (should be 1; checked, not assumed)
  - coordination signature of the unit cell (node degree, linker degree) --
    a proxy for net/topology, see code_16's docstring for its honest limits
"""
from __future__ import annotations

import json
import math
import os
import time
from collections import Counter

import numpy as np
import networkx as nx

from code_12_converged_band import (quotient_graph_from_cif, replicate,
                                      select_influential, fast_diameter, spectrum)

TARGET_CELL_LENGTH = 48.0
MAX_NODES = 6000
MAX_N = 8


def degree_entropy(degrees):
    counts = Counter(degrees)
    n = sum(counts.values())
    probs = [c / n for c in counts.values()]
    h = -sum(p * math.log(p) for p in probs if p > 0)
    h_max = math.log(len(counts)) if len(counts) > 1 else 1.0
    return h / h_max if h_max > 0 else 0.0


def coordination_signature(blocks, edges):
    deg = Counter()
    for i, j, _t in edges:
        deg[i] += 1
        deg[j] += 1
    node_degs = Counter(deg[i] for i, (kind, _b) in enumerate(blocks) if kind == 'node')
    linker_degs = Counter(deg[i] for i, (kind, _b) in enumerate(blocks) if kind == 'linker')
    node_d = node_degs.most_common(1)[0][0] if node_degs else None
    linker_d = linker_degs.most_common(1)[0][0] if linker_degs else None
    single_valued = len(node_degs) <= 1 and len(linker_degs) <= 1
    return node_d, linker_d, single_valued


INFLUENTIAL_FRAC = 0.20  # the top fifth of vertices by degree: the
WINDOW_FRAC = 0.50       # structural core, and radii out to half the
                         # diameter, where box-covering still has several
                         # boxes to average against -- see code_12.spectrum().


def analyse_one(cif_path, n_trials=20, seed=0):
    name = os.path.splitext(os.path.basename(cif_path))[0]
    try:
        blocks, edges, geom = quotient_graph_from_cif(cif_path)
    except Exception as e:
        return {'name': name, 'ok': False, 'reason': f'decomposition failed: {type(e).__name__}: {e}'}

    K = len(blocks)
    if K == 0:
        return {'name': name, 'ok': False, 'reason': 'no building blocks'}

    M = geom.cell_matrix
    axis_lengths = [math.sqrt(sum(M[i][k] ** 2 for k in range(3))) for i in range(3)]
    n = max(1, math.ceil(TARGET_CELL_LENGTH / min(axis_lengths)))
    while K * n ** 3 > MAX_NODES and n > 1:
        n -= 1
    n = min(n, MAX_N)

    try:
        G, _kind = replicate(blocks, edges, n)
    except Exception as e:
        return {'name': name, 'ok': False, 'reason': f'replication failed: {type(e).__name__}: {e}'}

    Gs = nx.Graph(G)
    if Gs.number_of_edges() == 0:
        return {'name': name, 'ok': False, 'reason': 'coarse graph has no edges'}

    try:
        infl, sel = select_influential(G, top_percent=INFLUENTIAL_FRAC)
        diam = fast_diameter(G)
        spec = spectrum(G, infl, n_trials=n_trials, seed=seed, diameter=diam,
                        window_frac=WINDOW_FRAC)
    except Exception as e:
        return {'name': name, 'ok': False, 'reason': f'spectrum failed: {type(e).__name__}: {e}'}

    if not spec.get('ok'):
        return {'name': name, 'ok': False, 'reason': spec.get('reason', 'spectrum not ok'),
                'diameter': spec.get('diameter')}

    degs = np.array([d for _, d in Gs.degree()])
    try:
        assort = nx.degree_assortativity_coefficient(Gs)
    except Exception:
        assort = float('nan')
    node_d, linker_d, single_valued = coordination_signature(blocks, edges)

    return {
        'name': name, 'ok': True,
        'n_blocks_unit_cell': K,
        'supercell_n': n,
        'cg_nodes': Gs.number_of_nodes(),
        'cg_edges': Gs.number_of_edges(),
        'diameter': spec['diameter'],
        'n_influential': len(infl),
        'width': spec['width'], 'alpha_0': spec['alpha_0'], 'asymmetry': spec['asymmetry'],
        'r2_linearity_mean': spec['r2_linearity_mean'],
        # full curves, kept so the spectra can be plotted and grouped by
        # class after the fact without recomputing anything
        'q_values': spec['q_values'].tolist(),
        'alpha': spec['alpha'].tolist(),
        'f_alpha': spec['f_alpha'].tolist(),
        'degree_mean': float(degs.mean()), 'degree_std': float(degs.std()),
        'degree_cv': float(degs.std() / degs.mean()) if degs.mean() > 0 else float('nan'),
        'degree_min': int(degs.min()), 'degree_max': int(degs.max()),
        'degree_entropy_norm': degree_entropy(degs.tolist()),
        'assortativity': float(assort) if assort is not None else float('nan'),
        'avg_clustering': float(nx.average_clustering(Gs)),
        'n_components': nx.number_connected_components(Gs),
        'node_degree_signature': node_d, 'linker_degree_signature': linker_d,
        'single_valued_signature': single_valued,
    }


def run_dataset(cif_dir, label, out_path, n_trials=20, verbose=True):
    files = sorted(f for f in os.listdir(cif_dir) if f.lower().endswith('.cif'))
    if verbose:
        print(f'\n{label}: {len(files)} structures')
    records = []
    t0 = time.time()
    for f in files:
        rec = analyse_one(os.path.join(cif_dir, f), n_trials=n_trials)
        records.append(rec)
        if verbose:
            if rec.get('ok'):
                print(f"  {rec['name']:36s} CG-N={rec['cg_nodes']:5d} diam={rec['diameter']:3d} "
                      f"width={rec['width']:.4f} deg_cv={rec['degree_cv']:.3f} "
                      f"assort={rec['assortativity']:+.3f} clust={rec['avg_clustering']:.4f}")
            else:
                print(f"  {rec['name']:36s} SKIPPED: {rec['reason']}")
    if verbose:
        print(f'  {label} took {time.time()-t0:.1f}s')

    good = [r for r in records if r.get('ok')]
    result = {'label': label, 'n_input': len(files), 'n_usable': len(good), 'records': records}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as fh:
        json.dump(result, fh, indent=2, default=str)
    if verbose:
        widths = [r['width'] for r in good]
        if widths:
            print(f"  {label}: {len(good)}/{len(files)} usable, "
                  f"width mean={np.mean(widths):.4f} sd={np.std(widths):.4f} "
                  f"range={min(widths):.4f}-{max(widths):.4f}")
    return result


if __name__ == '__main__':
    import sys
    hmof_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', '_work', 'hmof_cifs')
    core_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join('..', '..', '_work', 'core_cifs')
    out_dir = os.path.join('..', '9_dataset', 'size_scaling')

    hmof_result = run_dataset(hmof_dir, 'hMOF (full, CG supercell)',
                               os.path.join(out_dir, 'full_band_hmof_cg.json'))
    core_result = run_dataset(core_dir, 'CoRE MOF (full, CG supercell)',
                               os.path.join(out_dir, 'full_band_core_cg.json'))
