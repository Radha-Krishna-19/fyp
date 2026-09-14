#!/usr/bin/env python3
"""Reads convergence_sweep.json (written by 2_python/_run_size_scaling.py) and
draws the Delta-alpha vs ln(diameter) figure for all four demonstration
structures on one axis, plus a q-range-convergence panel. matplotlib only.

Run:  python make_convergence_figure.py
Reads:  convergence_sweep.json (same directory)
Writes: convergence_figure.png (same directory)
"""
import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'convergence_sweep.json')

COLORS = {'HKUST-1.cif': '#1f5fa8', 'MOF5.cif': '#b91c1c',
          'ZIF-8.cif': '#1a8a5f', 'UiO-66.cif': '#a8621f'}
NET = {'HKUST-1.cif': 'tbo', 'MOF5.cif': 'pcu', 'ZIF-8.cif': 'sod', 'UiO-66.cif': 'fcu'}


def main():
    data = json.load(open(DATA))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # ---- Panel 1: Delta-alpha vs ln(diameter), full q range ----------------
    for cif, rec in data.items():
        sweep = rec['sweep']
        diam = np.array([r['diameter'] for r in sweep], dtype=float)
        width = np.array([r['width_mean'] for r in sweep], dtype=float)
        werr = np.array([r['width_sd'] for r in sweep], dtype=float)
        c = COLORS.get(cif, '#666')
        ax1.errorbar(np.log(diam), width, yerr=werr, marker='o', ms=5, lw=1.6,
                      color=c, label=f'{cif.replace(".cif","")} ({NET.get(cif,"?")})',
                      capsize=3)
        # fit line
        if len(diam) >= 3:
            slope, icept = np.polyfit(np.log(diam), width, 1)
            xs = np.linspace(np.log(diam).min(), np.log(diam).max(), 20)
            ax1.plot(xs, slope * xs + icept, '--', color=c, alpha=0.4, lw=1)

    ax1.set_xlabel('ln(graph diameter D)')
    ax1.set_ylabel(r'$\Delta\alpha$ (spectrum width, full q range $[-10,10]$)')
    ax1.set_title(r'$\Delta\alpha$ grows with supercell size, on every net')
    ax1.legend(fontsize=8, loc='upper left')
    ax1.grid(alpha=0.25)

    # ---- Panel 2: drift at the largest step, across q caps -----------------
    for cif, rec in data.items():
        qc = rec.get('q_range_convergence', {})
        per_cap = qc.get('per_cap', [])
        if not per_cap:
            continue
        caps = [o['q_cap'] for o in per_cap]
        drift = [o['drift_last_step'] for o in per_cap]
        c = COLORS.get(cif, '#666')
        ax2.plot(caps, drift, marker='s', ms=5, lw=1.6, color=c,
                  label=cif.replace('.cif', ''))

    ax2.axhline(0.05, color='#333', ls=':', lw=1.2, label='5% convergence tolerance')
    ax2.set_xlabel(r'q cap ($|q| \leq$ this value)')
    ax2.set_ylabel('drift between the two largest supercells tested')
    ax2.set_title('No q range converges, on any net')
    ax2.invert_xaxis()
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(HERE, 'convergence_figure.png')
    fig.savefig(out, dpi=150)
    print(f'written {out}')


if __name__ == '__main__':
    main()
