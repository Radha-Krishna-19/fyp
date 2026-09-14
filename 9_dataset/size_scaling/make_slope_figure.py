"""Figure for task D: does the Delta-alpha(D) divergence SLOPE differ between
frameworks, and between datasets? matplotlib only.

Reads slope_sweep_hmof.json and slope_sweep_core.json (written by
2_python/code_15_dataset_sweeps.py), draws:
  (a) each structure's Delta-alpha vs ln(diameter) points and fitted line,
      hMOF in blue, CoRE MOF in red, on one axis
  (b) the distribution of fitted slopes, one dataset per row

Run from this directory. Writes slope_sweep_figure.png here.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    hmof = json.load(open(os.path.join(HERE, 'slope_sweep_hmof.json')))
    core = json.load(open(os.path.join(HERE, 'slope_sweep_core.json')))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for rec in hmof['records']:
        if not rec.get('ok'):
            continue
        d = np.array(rec['diameters']); w = np.array(rec['widths'])
        ax1.plot(np.log(d), w, 'o-', color='#1f5fa8', alpha=0.5, ms=4, lw=1)
    for rec in core['records']:
        if not rec.get('ok'):
            continue
        d = np.array(rec['diameters']); w = np.array(rec['widths'])
        ax1.plot(np.log(d), w, 's-', color='#b91c1c', alpha=0.5, ms=4, lw=1)

    ax1.plot([], [], 'o-', color='#1f5fa8', label=f"hMOF (n={hmof['n_usable']}, capped at 20)")
    ax1.plot([], [], 's-', color='#b91c1c', label=f"CoRE MOF (n={core['n_usable']}, capped at 20)")
    ax1.set_xlabel('ln(graph diameter D)')
    ax1.set_ylabel(r'$\Delta\alpha$')
    ax1.set_title('(a) Per-structure divergence, both datasets\n(3-point sweep, capped at 5000 nodes)')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.25)

    hs = [r['slope'] for r in hmof['records'] if r.get('ok')]
    cs = [r['slope'] for r in core['records'] if r.get('ok')]
    ax2.hist(hs, bins=8, alpha=0.6, color='#1f5fa8', label=f'hMOF (sd={np.std(hs):.3f})')
    ax2.hist(cs, bins=8, alpha=0.6, color='#b91c1c', label=f'CoRE MOF (sd={np.std(cs):.3f})')
    ax2.axvline(np.mean(hs), color='#1f5fa8', ls='--', lw=1.5)
    ax2.axvline(np.mean(cs), color='#b91c1c', ls='--', lw=1.5)
    ax2.set_xlabel(r'fitted slope of $\Delta\alpha$ vs ln(D), per structure')
    ax2.set_ylabel('number of structures')
    ax2.set_title('(b) The slope varies more across CoRE MOF\nthan across hMOF -- candidate descriptor, not a result')
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.25, axis='y')

    fig.tight_layout()
    out = os.path.join(HERE, 'slope_sweep_figure.png')
    fig.savefig(out, dpi=150)
    print(f'written {out}')
    print(f"hMOF     slope mean={np.mean(hs):.3f} sd={np.std(hs):.3f} range={min(hs):.3f}-{max(hs):.3f} n={len(hs)}")
    print(f"CoRE MOF slope mean={np.mean(cs):.3f} sd={np.std(cs):.3f} range={min(cs):.3f}-{max(cs):.3f} n={len(cs)}")


if __name__ == '__main__':
    main()
