"""
MODULE 15 -- Delta-alpha(D) SWEEPS ON BOTH DATASETS, CAPPED FOR COST

WHY THIS MODULE EXISTS
docs/project_notes.md and code_12_converged_band.py establish that Delta-alpha diverges
with supercell diameter on four demonstration structures. This module asks
whether the DIVERGENCE SLOPE -- not the value, which is now known to be
uninterpretable -- differs between frameworks, on a real (if capped) sample
from each of this project's two published datasets. If the slope itself
varies systematically between frameworks, it is a candidate size-independent
descriptor; if not, that too is worth knowing before proposing one.

COST CONTROL (explicit project limit for this sweep)
  - at most 20 structures per dataset
  - chosen for SIZE spread (a proxy for topological spread where net labels
    are not available -- see the module docstring in code_14 and the F-task
    write-up for why net assignment needs Systre, which is not run here)
  - supercell replication capped so no analysed graph exceeds ~5000 nodes
  - a short, fixed sweep of supercell multipliers (2, 3, 4), not the full
    (2,3,4,6,8) sweep in code_12 -- three points are enough to fit a slope,
    and the cost of five points across 40 structures would be prohibitive
  - one seed, not the 3-seed average code_12 uses for a single structure's
    finite-size study -- this trades per-point precision for coverage across
    many structures, which is the right trade for "does the slope vary
    between frameworks", not "what is the exact slope of one framework"

WHAT THIS DOES NOT DO
This is not a replacement for code_12's careful single-structure sweep, and
it does not re-establish non-convergence (already established). It measures
one number per structure -- the slope of Delta-alpha against ln(diameter)
over 3 points -- and asks whether that number's spread across frameworks is
larger than its own noise.
"""
from __future__ import annotations

import json
import math
import os
import time

import numpy as np

from code_12_converged_band import (quotient_graph_from_cif, replicate,
                                      select_influential, fast_diameter, spectrum)

MAX_NODES = 5000
N_VALUES = (2, 3, 4)


def slope_for_structure(cif_path, n_values=N_VALUES, max_nodes=MAX_NODES,
                         n_trials=15, seed=0):
    name = os.path.splitext(os.path.basename(cif_path))[0]
    try:
        blocks, edges, _geom = quotient_graph_from_cif(cif_path)
    except Exception as e:
        return {'name': name, 'ok': False, 'reason': f'decomposition failed: {type(e).__name__}: {e}'}

    K = len(blocks)
    if K == 0:
        return {'name': name, 'ok': False, 'reason': 'no building blocks'}

    diams, widths = [], []
    for n in n_values:
        if K * n ** 3 > max_nodes:
            continue
        try:
            G, _kind = replicate(blocks, edges, n)
            infl, _sel = select_influential(G)
            diam = fast_diameter(G)
            r = spectrum(G, infl, n_trials=n_trials, seed=seed, diameter=diam)
        except Exception as e:
            continue
        if r.get('ok'):
            diams.append(r['diameter'])
            widths.append(r['width'])

    if len(diams) < 2:
        return {'name': name, 'ok': False, 'reason': f'only {len(diams)} usable sizes under the {max_nodes}-node cap'}

    diams = np.array(diams, dtype=float)
    widths = np.array(widths, dtype=float)
    slope, icept = np.polyfit(np.log(diams), widths, 1)
    return {'name': name, 'ok': True, 'K_blocks': K, 'diameters': diams.tolist(),
            'widths': widths.tolist(), 'slope': float(slope), 'intercept': float(icept),
            'n_points': len(diams)}


def run_dataset(cif_dir, label, max_structures=20, out_path=None, verbose=True):
    files = sorted(f for f in os.listdir(cif_dir) if f.lower().endswith('.cif'))
    files = files[:max_structures]
    if verbose:
        print(f'\n{label}: {len(files)} structures (capped at {max_structures})')
    records = []
    t0 = time.time()
    for f in files:
        rec = slope_for_structure(os.path.join(cif_dir, f))
        records.append(rec)
        if verbose:
            if rec.get('ok'):
                print(f"  {rec['name']:36s} blocks={rec['K_blocks']:5d} "
                      f"points={rec['n_points']}  slope={rec['slope']:+.3f}")
            else:
                print(f"  {rec['name']:36s} SKIPPED: {rec['reason']}")
    if verbose:
        print(f'  {label} took {time.time()-t0:.1f}s')

    good = [r for r in records if r.get('ok')]
    slopes = [r['slope'] for r in good]
    result = {'label': label, 'n_input': len(files), 'n_usable': len(good),
              'records': records,
              'slope_mean': float(np.mean(slopes)) if slopes else None,
              'slope_sd': float(np.std(slopes)) if slopes else None,
              'slope_min': float(np.min(slopes)) if slopes else None,
              'slope_max': float(np.max(slopes)) if slopes else None}
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w') as fh:
            json.dump(result, fh, indent=2, default=str)
    if verbose and slopes:
        print(f'  slope: mean={result["slope_mean"]:.3f} sd={result["slope_sd"]:.3f} '
              f'range={result["slope_min"]:.3f}-{result["slope_max"]:.3f}  n={len(slopes)}')
    return result


if __name__ == '__main__':
    import sys
    hmof_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', 'data', 'structures', 'hmof')
    core_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join('..', '..', 'data', 'structures', 'core_mof_2019')
    out_dir = os.path.join('..', '..', 'data', 'spectrum_descriptors', 'size_scaling')

    hmof_result = run_dataset(hmof_dir, 'hMOF', max_structures=20,
                               out_path=os.path.join(out_dir, 'slope_sweep_hmof.json'))
    core_result = run_dataset(core_dir, 'CoRE MOF', max_structures=20,
                               out_path=os.path.join(out_dir, 'slope_sweep_core.json'))

    print(f"\n{'='*70}\nSUMMARY")
    print(f"  hMOF     : n={hmof_result['n_usable']:2d}  slope mean={hmof_result['slope_mean']:.3f} "
          f"sd={hmof_result['slope_sd']:.3f}")
    print(f"  CoRE MOF : n={core_result['n_usable']:2d}  slope mean={core_result['slope_mean']:.3f} "
          f"sd={core_result['slope_sd']:.3f}")
