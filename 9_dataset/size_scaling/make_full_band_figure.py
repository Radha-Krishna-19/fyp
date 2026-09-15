"""Figures for the full, correct (coarse-grained supercell) band on both
datasets. matplotlib only.

Reads full_band_hmof_cg.json, full_band_core_cg.json (per-structure spectra)
and subband_explain_hmof.json, subband_explain_core.json (class summaries).
Writes:
  full_band_figure.png     -- both bands, both datasets, one figure
  full_band_vs_size.png    -- Delta-alpha against CG node count and diameter,
                               coloured by class, both datasets -- the figure
                               that shows the sub-bands are graph size
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS = {'Narrow': '#27ae60', 'Medium': '#f39c12', 'Wide': '#c0392b'}


def load(name):
    return json.load(open(os.path.join(HERE, name)))


def main():
    hmof = load('full_band_hmof_cg.json')
    core = load('full_band_core_cg.json')
    hmof_x = load('subband_explain_hmof.json')
    core_x = load('subband_explain_core.json')

    hg = [r for r in hmof['records'] if r.get('ok')]
    cg = [r for r in core['records'] if r.get('ok')]
    for r in hg:
        r['class'] = ('Narrow' if r['width'] <= hmof_x['q25'] else
                       'Medium' if r['width'] <= hmof_x['q75'] else 'Wide')
    for r in cg:
        r['class'] = ('Narrow' if r['width'] <= core_x['q25'] else
                       'Medium' if r['width'] <= core_x['q75'] else 'Wide')

    # ---- Figure 1: both bands, sorted, side by side -----------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, recs, title, q25, q75 in (
        (ax1, hg, f'hMOF, full correct band\n(n={len(hg)}/77 usable)', hmof_x['q25'], hmof_x['q75']),
        (ax2, cg, f'CoRE MOF, full correct band\n(n={len(cg)}/61 usable)', core_x['q25'], core_x['q75']),
    ):
        order = sorted(recs, key=lambda r: r['width'])
        y = np.arange(len(order))
        colors = [COLORS[r['class']] for r in order]
        ax.barh(y, [r['width'] for r in order], color=colors, height=0.85)
        ax.axvline(q25, color='#333', ls=':', lw=1)
        ax.axvline(q75, color='#333', ls=':', lw=1)
        ax.set_yticks([])
        ax.set_xlabel(r'$\Delta\alpha$ (coarse-grained supercell graph)')
        ax.set_title(title)
        ax.grid(alpha=0.25, axis='x')
    for cls in ('Narrow', 'Medium', 'Wide'):
        ax1.bar(0, 0, color=COLORS[cls], label=cls)
    ax1.legend(fontsize=9, loc='lower right', title='class (terciles)')
    fig.tight_layout()
    out1 = os.path.join(HERE, 'full_band_figure.png')
    fig.savefig(out1, dpi=150)
    print(f'written {out1}')

    # ---- Figure 2: Delta-alpha vs CG node count and diameter --------------
    fig, axes = plt.subplots(2, 2, figsize=(12, 9.5))
    for col, (recs, label) in enumerate([(hg, 'hMOF'), (cg, 'CoRE MOF')]):
        ax_n = axes[0, col]
        ax_d = axes[1, col]
        for cls in ('Narrow', 'Medium', 'Wide'):
            pts = [r for r in recs if r['class'] == cls]
            ax_n.scatter([r['cg_nodes'] for r in pts], [r['width'] for r in pts],
                         s=28, color=COLORS[cls], alpha=0.8, label=cls, edgecolors='none')
            ax_d.scatter([r['diameter'] for r in pts], [r['width'] for r in pts],
                         s=28, color=COLORS[cls], alpha=0.8, label=cls, edgecolors='none')
        ax_n.set_xlabel('coarse-grained node count')
        ax_n.set_ylabel(r'$\Delta\alpha$')
        ax_n.set_title(f'{label}: width vs graph size')
        ax_n.grid(alpha=0.25)
        ax_n.legend(fontsize=8)
        ax_d.set_xlabel('graph diameter')
        ax_d.set_ylabel(r'$\Delta\alpha$')
        ax_d.set_title(f'{label}: width vs diameter')
        ax_d.grid(alpha=0.25)

        # correlation annotation
        w = np.array([r['width'] for r in recs])
        n = np.array([r['cg_nodes'] for r in recs], dtype=float)
        d = np.array([r['diameter'] for r in recs], dtype=float)
        rn = np.corrcoef(w, n)[0, 1]
        rd = np.corrcoef(w, d)[0, 1]
        ax_n.text(0.03, 0.95, f'r = {rn:+.2f}', transform=ax_n.transAxes,
                  fontsize=10, fontweight='bold', va='top')
        ax_d.text(0.03, 0.95, f'r = {rd:+.2f}', transform=ax_d.transAxes,
                  fontsize=10, fontweight='bold', va='top')

    fig.suptitle('Even on the CORRECT coarse-grained supercell graph, class tracks graph size',
                 fontsize=12)
    fig.tight_layout()
    out2 = os.path.join(HERE, 'full_band_vs_size.png')
    fig.savefig(out2, dpi=150)
    print(f'written {out2}')

    for label, recs in (('hMOF', hg), ('CoRE MOF', cg)):
        w = np.array([r['width'] for r in recs])
        n = np.array([r['cg_nodes'] for r in recs], dtype=float)
        d = np.array([r['diameter'] for r in recs], dtype=float)
        print(f'{label}: r(width,cg_nodes)={np.corrcoef(w,n)[0,1]:+.3f}  '
              f'r(width,diameter)={np.corrcoef(w,d)[0,1]:+.3f}  n={len(recs)}')


if __name__ == '__main__':
    main()
