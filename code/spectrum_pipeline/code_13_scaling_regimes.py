"""
MODULE 13 -- DOES THE ATOMIC GRAPH HAVE TWO SCALING REGIMES?

WHY THIS MODULE EXISTS
docs/project_notes.md records that both published bands (the 77-framework hMOF set and the
61-framework CoRE MOF set) ran the multifractal analysis on the ATOMIC
supercell bond graph rather than on the coarse-grained building-block graph
this project's method describes. The concern that raises is not just "wrong
graph" but a specific mathematical objection: an atomic MOF graph should have
structure at two different length scales --

    MOLECULAR   -- distances of a few bonds, inside one metal cluster or one
                   organic linker. Growth here reflects the local chemistry of
                   one building block (how many atoms per cluster, how rigid
                   one linker's own skeleton is).
    FRAMEWORK   -- distances of many bonds, spanning several building blocks.
                   Growth here reflects how clusters and linkers are wired
                   together -- the net.

Fitting ONE power law across both, as the atomic-graph runs did, describes
neither regime correctly if the two really do have different exponents. This
module tests that directly, rather than asserting it, using the mass-radius
relation M(r) = mean number of atoms within r bond-steps of a reference atom.

METHOD
1. Build the atomic labelled quotient graph of the unit cell -- one vertex per
   ATOM (not per building block), using the SAME translation-tracking used for
   the block graph, by passing single-atom "blocks" to
   code_09.build_periodic_block_graph. This reuses the exact periodicity logic
   the project already relies on, rather than a second implementation of it.
2. Replicate n x n x n (code_12.replicate is graph-content-agnostic: it only
   needs `blocks` and `(i, j, t)` edges, and does not care whether a block
   holds one atom or fifty).
3. BFS from a sample of centre atoms, record the CUMULATIVE atom count within
   radius r for r = 1 .. diameter, average ln(count) over centres at each r.
4. Fit ln(count) vs ln(r) three ways: one straight line across the whole
   range; and two straight lines, split at r0 = the diameter (in ATOM bond
   steps) of one linker block -- a boundary chosen from the chemistry (where
   one linker's own skeleton ends), not tuned to make the result come out a
   particular way.
5. Report whether the two-segment fit's residual is meaningfully smaller than
   the one-segment fit's, and what the two slopes are. If they differ, that is
   the two regimes, made concrete rather than argued from general principles.

This is deliberately a SEPARATE, simpler diagnostic from the full multifractal
machinery in code_12 -- it asks a narrower question (is there one exponent or
two?) with a method any reader can check by hand.
"""
from __future__ import annotations

import json
import math
import os
import random
from typing import List, Tuple

import numpy as np
import networkx as nx

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph
from code_12_converged_band import replicate, fast_diameter, _adjacency, _bfs_far


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

def atomic_quotient_graph(cif_path: str):
    """The SAME labelled-quotient-graph construction used for building blocks,
    applied with one atom per block. Returns (blocks, edges, geom, linker_atom_diam)
    where linker_atom_diam is the diameter (in atom bond-steps) of the largest
    linker block -- the a-priori molecular/framework boundary for this structure.
    """
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    node_blocks, linker_blocks = run_metal_oxo(geom)
    atom_blocks = [[i] for i in range(len(geom.symbols))]
    blocks, edges = build_periodic_block_graph(geom, atom_blocks, [])

    # r0: diameter of one linker's own atom-to-atom graph (unit cell, no PBC
    # needed since a linker does not span a cell boundary in these structures).
    atom_adj = {i: [] for i in range(len(geom.symbols))}
    for bd in geom.bonds:
        atom_adj[bd.lo].append(bd.hi)
        atom_adj[bd.hi].append(bd.lo)
    linker_diams = []
    for lb in linker_blocks:
        sub = set(lb)
        adj = {a: [n for n in atom_adj[a] if n in sub] for a in lb}
        far, _ = _bfs_far(adj, lb[0])
        _, d = _bfs_far(adj, far)
        linker_diams.append(d)
    r0 = int(round(np.median(linker_diams))) if linker_diams else 3
    return blocks, edges, geom, max(r0, 2)


def mass_radius(G, n_centres=12, seed=0, max_r=None):
    """Mean ln(count within r) over a sample of centres, for r = 1 .. diameter."""
    adj = _adjacency(G)
    nodes = list(G.nodes())
    rng = random.Random(seed)
    centres = rng.sample(nodes, min(n_centres, len(nodes)))
    diam = fast_diameter(G, adj)
    if max_r:
        diam = min(diam, max_r)
    radii = list(range(1, diam + 1))
    counts = {r: [] for r in radii}
    for c in centres:
        dist = {c: 0}
        frontier = [c]
        d = 0
        cum = 1
        per_r = {}
        while frontier and d < diam:
            nxt = []
            for u in frontier:
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = d + 1
                        nxt.append(v)
            d += 1
            cum += len(nxt)
            per_r[d] = cum
            frontier = nxt
        last = 1
        for r in radii:
            last = per_r.get(r, last)
            counts[r].append(last)
    mean_ln = np.array([np.mean(np.log(counts[r])) for r in radii])
    return np.array(radii, dtype=float), mean_ln


def two_segment_fit(x, y, split_r):
    """Compare one straight-line fit across all of x,y against two, split at
    split_r. Returns dict with both slopes, both R^2, and the combined
    residual comparison."""
    mask_lo = x <= split_r
    mask_hi = x > split_r
    if mask_lo.sum() < 3 or mask_hi.sum() < 3:
        return {'ok': False, 'reason': f'not enough points either side of r0={split_r}'}

    def fit(xs, ys):
        A = np.polyfit(np.log(xs), ys, 1)
        slope, icept = A
        pred = slope * np.log(xs) + icept
        ss_res = float(np.sum((ys - pred) ** 2))
        ss_tot = float(np.sum((ys - ys.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
        return slope, r2, ss_res

    slope_all, r2_all, ss_all = fit(x, y)
    slope_lo, r2_lo, ss_lo = fit(x[mask_lo], y[mask_lo])
    slope_hi, r2_hi, ss_hi = fit(x[mask_hi], y[mask_hi])
    ss_two = ss_lo + ss_hi

    return {
        'ok': True,
        'split_r': split_r,
        'n_points': len(x),
        'slope_single_fit': slope_all,
        'r2_single_fit': r2_all,
        'ss_res_single_fit': ss_all,
        'slope_molecular_regime': slope_lo,
        'r2_molecular_regime': r2_lo,
        'slope_framework_regime': slope_hi,
        'r2_framework_regime': r2_hi,
        'ss_res_two_segment': ss_two,
        'residual_improvement': (ss_all - ss_two) / ss_all if ss_all > 0 else float('nan'),
        'slope_difference': slope_hi - slope_lo,
        'verdict': (
            'two regimes detected: slopes differ and the two-segment fit '
            'reduces the residual materially'
            if abs(slope_hi - slope_lo) > 0.05 and (ss_all - ss_two) / max(ss_all, 1e-12) > 0.10
            else 'no clear evidence of two distinct regimes at this split point'
        ),
    }


def analyse_structure(cif_path: str, n: int = 4, n_centres: int = 12, seed: int = 0):
    name = os.path.splitext(os.path.basename(cif_path))[0]
    blocks, edges, geom, r0 = atomic_quotient_graph(cif_path)
    K = len(blocks)
    if K * n ** 3 > 40000:
        n = max(1, int(round((40000 / K) ** (1 / 3))))
    G, _kind = replicate(blocks, edges, n)
    x, y = mass_radius(G, n_centres=n_centres, seed=seed)
    fit = two_segment_fit(x, y, r0)
    return {
        'name': name, 'n_atoms_unit_cell': K, 'supercell_n': n,
        'atoms_analysed': G.number_of_nodes(), 'linker_atom_diameter_r0': r0,
        'fit': fit,
    }


if __name__ == '__main__':
    import sys
    cifs = sys.argv[1:] or [os.path.join(HERE, c) for c in ('HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif')]
    out = {}
    for cif in cifs:
        if not os.path.exists(cif):
            print(f'skip {cif}: not found')
            continue
        print(f'\n{cif}')
        rec = analyse_structure(cif)
        out[rec['name']] = rec
        f = rec['fit']
        if f.get('ok'):
            print(f"  atoms analysed: {rec['atoms_analysed']}  r0 (linker atom diameter): {rec['linker_atom_diameter_r0']}")
            print(f"  single fit:      slope={f['slope_single_fit']:+.3f}  R2={f['r2_single_fit']:.3f}")
            print(f"  molecular regime (r<=r0): slope={f['slope_molecular_regime']:+.3f}  R2={f['r2_molecular_regime']:.3f}")
            print(f"  framework regime (r>r0):  slope={f['slope_framework_regime']:+.3f}  R2={f['r2_framework_regime']:.3f}")
            print(f"  residual improvement from splitting: {f['residual_improvement']:.1%}")
            print(f"  VERDICT: {f['verdict']}")
        else:
            print(f"  {f.get('reason')}")

    outdir = os.path.join(REPO, 'data', 'spectrum_descriptors', 'size_scaling')
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'scaling_regimes.json'), 'w') as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nWritten to {os.path.join(outdir, 'scaling_regimes.json')}")
