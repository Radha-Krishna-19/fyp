"""One-off driver for the real finite-size + q-range convergence sweep on the
four demonstration structures, run from this file's own directory so the
relative CIF paths in code_12 resolve regardless of the caller's cwd.
Writes JSON + a plain-text log to 9_dataset/size_scaling/. Not part of the
reference pipeline; delete after the figures are generated, or keep as a
record of how they were produced.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

import numpy as np
from code_12_converged_band import finite_size_sweep, q_range_convergence, converged_n

OUT = os.path.join(HERE, '..', '9_dataset', 'size_scaling')
os.makedirs(OUT, exist_ok=True)

NETS = {'HKUST-1.cif': 'tbo', 'MOF5.cif': 'pcu', 'ZIF-8.cif': 'sod', 'UiO-66.cif': 'fcu'}

results = {}
t0 = time.time()
for cif, net in NETS.items():
    if not os.path.exists(cif):
        print(f'SKIP {cif}: not found in {HERE}')
        continue
    print(f'\n=== {cif} ({net}) ===', flush=True)
    tS = time.time()
    sweep = finite_size_sweep(cif, n_values=(2, 3, 4, 6, 8), n_trials=20, n_seeds=3,
                               max_nodes=25000, verbose=True)
    print(f'  sweep took {time.time()-tS:.1f}s, {len(sweep)} sizes completed', flush=True)
    n_star = converged_n(sweep)
    qc = q_range_convergence(sweep) if len(sweep) >= 3 else {'ok': False, 'reason': 'too few sizes'}
    rec = {
        'net': net,
        'sweep': [{k: v for k, v in row.items() if k not in ('alpha',)}
                  for row in sweep],  # alpha arrays kept separately below
        'alpha_by_row': [row['alpha'].tolist() for row in sweep],
        'q_values': sweep[0]['q_values'].tolist() if sweep else [],
        'converged_n': n_star,
        'q_range_convergence': {k: v for k, v in qc.items()} if qc.get('ok') else qc,
    }
    results[cif] = rec
    print(f'  converged_n={n_star}  verdict={qc.get("verdict")}', flush=True)

with open(os.path.join(OUT, 'convergence_sweep.json'), 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f'\nTotal time: {time.time()-t0:.1f}s')
print(f'Written to {os.path.join(OUT, "convergence_sweep.json")}')
