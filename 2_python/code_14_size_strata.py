"""
MODULE 14 -- ARE THE Narrow/Medium/Wide CLASSES CHEMISTRY, OR SIZE?

WHY THIS MODULE EXISTS
An independent coarse-grained run (`~/Downloads/mof_cg_spectrum.ipynb`, recorded
in CLAUDE.md) cut 76 hMOF frameworks into three classes by the 25th/75th
percentile of Delta-alpha: Narrow <= 1.1901 < Medium <= 1.2218 < Wide. Two
things about those classes were already flagged as suspect: the classes are
narrower than the per-structure error bar (Defect 5 in CLAUDE.md), and the
same graph (hMOF-94 and hMOF-96, confirmed isomorphic by the run's own check)
landed in different classes.

This module asks the next question directly: if not chemistry, what DOES
predict which class a structure falls into? It rebuilds the CORRECT
coarse-grained quotient graph (this project's own code_09/code_12, not the
atomic-then-coarse-grain route that run used) for every hMOF CIF this project has
on disk, computes standard graph statistics on it, and reports those
statistics grouped by that run's own published class labels.

DATA AVAILABILITY
Only 34 of the 76 hMOF CIFs are available locally (MOFX-DB was not re-queried
for this module, per this session's instruction not to re-fetch). All three
classes are represented (10 Narrow, 18 Medium, 6 Wide from this subset), which
is enough to show whether the pattern holds; it is not a claim about all 76.

WHAT IS COMPUTED PER STRUCTURE
  - the coarse-grained quotient graph of the UNIT CELL (no replication) --
    n_nodes, n_edges, diameter
  - the same graph replicated to a small, fixed rule (n such that
    n_nodes * n^3 is at least 150, capped at n=4) -- large enough for
    clustering and assortativity to be non-degenerate, small enough to stay
    cheap. This is the SIZE-STRATA graph the statistics below are computed on.
  - degree sequence: mean, std, coefficient of variation, min, max
  - degree assortativity coefficient (do high-degree blocks connect to other
    high-degree blocks, or to low-degree ones?)
  - average clustering coefficient
  - number of connected components (always 1 here, since code_12's replicate
    tiles a connected graph onto a torus, but checked rather than assumed)
  - a degree-heterogeneity measure: the Shannon entropy of the degree
    distribution, normalised by its maximum -- 0 means every block has the
    same degree, 1 means degrees are maximally spread out relative to the
    number of distinct values seen
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict

import numpy as np
import networkx as nx

import math

from code_12_converged_band import quotient_graph_from_cif, replicate

MIN_CELL_LENGTH = 48.0  # matches MIN_CELL_LENGTH in both band notebooks


def degree_entropy(degrees):
    """Shannon entropy of the degree distribution, normalised to [0, 1] by
    the entropy of a uniform distribution over the same number of distinct
    values. 0 = one degree value (a regular graph); 1 = as spread out as the
    number of distinct values allows."""
    counts = Counter(degrees)
    n = sum(counts.values())
    probs = [c / n for c in counts.values()]
    h = -sum(p * math.log(p) for p in probs if p > 0)
    h_max = math.log(len(counts)) if len(counts) > 1 else 1.0
    return h / h_max if h_max > 0 else 0.0


def structure_stats(cif_path, min_cell_length=MIN_CELL_LENGTH, max_n=8):
    """Replicate to the SAME rule the original band notebooks used for their
    atomic supercell -- reach min_cell_length in every lattice direction --
    but applied to the coarse-grained quotient graph (block count K, not atom
    count). This reproduces the same size VARIATION across structures that
    drove that atomic-then-coarsen run, on the correct graph."""
    blocks, edges, geom = quotient_graph_from_cif(cif_path)
    K = len(blocks)

    M = geom.cell_matrix
    axis_lengths = [math.sqrt(sum(M[i][k] ** 2 for k in range(3))) for i in range(3)]
    n = max(1, math.ceil(min_cell_length / min(axis_lengths)))
    n = min(n, max_n)
    G, _kind = replicate(blocks, edges, n)
    Gs = nx.Graph(G)  # collapse the MultiGraph to a simple graph for standard stats

    degs = np.array([d for _, d in Gs.degree()])
    n_components = nx.number_connected_components(Gs)

    try:
        assort = nx.degree_assortativity_coefficient(Gs)
    except Exception:
        assort = float('nan')

    return {
        'unit_cell_blocks': K,
        'unit_cell_edges': len(edges),
        'supercell_n': n,
        'n_nodes': Gs.number_of_nodes(),
        'n_edges': Gs.number_of_edges(),
        'degree_mean': float(degs.mean()),
        'degree_std': float(degs.std()),
        'degree_cv': float(degs.std() / degs.mean()) if degs.mean() > 0 else float('nan'),
        'degree_min': int(degs.min()),
        'degree_max': int(degs.max()),
        'degree_entropy_norm': degree_entropy(degs.tolist()),
        'assortativity': float(assort) if assort is not None else float('nan'),
        'avg_clustering': float(nx.average_clustering(Gs)),
        'n_components': n_components,
    }


def run(cif_dir, class_csv, out_json):
    import csv
    classes = {}
    delta_alpha = {}
    diameters_reported = {}
    cg_nodes_reported = {}
    for row in csv.DictReader(open(class_csv, encoding='utf-8')):
        classes[row['name']] = row['class_printed_edges']
        delta_alpha[row['name']] = float(row['delta_alpha'])
        diameters_reported[row['name']] = int(row['diameter'])
        cg_nodes_reported[row['name']] = int(row['cg_nodes'])

    records = {}
    for f in sorted(os.listdir(cif_dir)):
        if not f.lower().endswith('.cif'):
            continue
        name = os.path.splitext(f)[0]
        if name not in classes:
            continue
        try:
            stats = structure_stats(os.path.join(cif_dir, f))
        except Exception as e:
            print(f'  {name}: FAILED ({type(e).__name__}: {e})')
            continue
        stats['class'] = classes[name]
        stats['delta_alpha_teammate_run'] = delta_alpha[name]
        stats['diameter_teammate_run'] = diameters_reported[name]
        stats['cg_nodes_teammate_run'] = cg_nodes_reported[name]
        records[name] = stats
        print(f"  {name:12s} class={stats['class']:7s} "
              f"unit_cell_blocks={stats['unit_cell_blocks']:4d} "
              f"CG-N={stats['n_nodes']:5d} deg_mean={stats['degree_mean']:.2f} "
              f"deg_cv={stats['degree_cv']:.3f} assort={stats['assortativity']:+.3f} "
              f"clustering={stats['avg_clustering']:.4f} entropy={stats['degree_entropy_norm']:.3f}")

    by_class = defaultdict(list)
    for name, r in records.items():
        by_class[r['class']].append(r)

    summary = {}
    for cls in ('Narrow', 'Medium', 'Wide'):
        rows = by_class.get(cls, [])
        if not rows:
            continue
        summary[cls] = {
            'n': len(rows),
            'mean_unit_cell_blocks': float(np.mean([r['unit_cell_blocks'] for r in rows])),
            'mean_cg_nodes_teammate_run': float(np.mean([r['cg_nodes_teammate_run'] for r in rows])),
            'mean_diameter_teammate_run': float(np.mean([r['diameter_teammate_run'] for r in rows])),
            'mean_degree_mean': float(np.mean([r['degree_mean'] for r in rows])),
            'mean_degree_cv': float(np.mean([r['degree_cv'] for r in rows])),
            'mean_assortativity': float(np.nanmean([r['assortativity'] for r in rows])),
            'mean_clustering': float(np.mean([r['avg_clustering'] for r in rows])),
            'mean_degree_entropy_norm': float(np.mean([r['degree_entropy_norm'] for r in rows])),
            'mean_delta_alpha': float(np.mean([r['delta_alpha_teammate_run'] for r in rows])),
        }

    corr = {}
    names = list(records.keys())
    da = np.array([records[n]['delta_alpha_teammate_run'] for n in names])
    for key in ('unit_cell_blocks', 'cg_nodes_teammate_run', 'diameter_teammate_run',
                'degree_mean', 'degree_cv', 'assortativity', 'avg_clustering',
                'degree_entropy_norm'):
        vals = np.array([records[n][key] for n in names], dtype=float)
        mask = np.isfinite(vals) & np.isfinite(da)
        corr[key] = float(np.corrcoef(vals[mask], da[mask])[0, 1]) if mask.sum() > 2 else float('nan')

    out = {'records': records, 'by_class_summary': summary,
           'corr_with_delta_alpha': corr}
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(out, f, indent=2, default=str)

    print(f"\n{'-'*70}")
    print("By-class summary (34 of 76 structures -- all three classes represented):")
    for cls, s in summary.items():
        print(f"  {cls:8s} n={s['n']:3d}  unit_cell_blocks={s['mean_unit_cell_blocks']:.1f}  "
              f"CG-N(teammate)={s['mean_cg_nodes_teammate_run']:.0f}  "
              f"diam(teammate)={s['mean_diameter_teammate_run']:.1f}  "
              f"deg_mean={s['mean_degree_mean']:.2f}  deg_cv={s['mean_degree_cv']:.3f}  "
              f"assort={s['mean_assortativity']:+.3f}  clustering={s['mean_clustering']:.4f}  "
              f"entropy={s['mean_degree_entropy_norm']:.3f}  mean_dAlpha={s['mean_delta_alpha']:.4f}")
    print("\nCorrelation of each statistic with the teammate's Delta-alpha (34 structures):")
    for k, v in corr.items():
        print(f"  {k:24s} r={v:+.3f}")
    print(f"\nWritten to {out_json}")
    return out


if __name__ == '__main__':
    import sys
    cif_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', '_work', 'hmof_cifs')
    class_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join('..', '..', '_work', 'teammate_cg_run.csv')
    out_json = sys.argv[3] if len(sys.argv) > 3 else os.path.join('..', '9_dataset', 'size_scaling', 'size_strata.json')
    run(cif_dir, class_csv, out_json)
