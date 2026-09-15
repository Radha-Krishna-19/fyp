"""Grouped multifractal spectra: every structure's f(alpha) vs alpha curve,
on the CORRECT coarse-grained supercell graph, coloured by class
(Narrow/Medium/Wide terciles of Delta-alpha), for both full datasets.
matplotlib only.

This is the grouped version of the standard "all spectra overlaid" figure
this project already uses (site fig10, panel b): same idea, but coloured by
class instead of left as one colour, and computed on the graph the method
actually calls for instead of the withdrawn atomic graph.

Reads full_band_hmof_cg.json, full_band_core_cg.json (per-structure spectra,
now including the full alpha(q)/f_alpha(q) curves) and
subband_explain_hmof.json, subband_explain_core.json (class thresholds).
Writes grouped_spectra_figure.png.
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


def classify(recs, q25, q75):
    for r in recs:
        r['class'] = ('Narrow' if r['width'] <= q25 else
                       'Medium' if r['width'] <= q75 else 'Wide')
    return recs


def clean_curve(alpha, f_alpha):
    a = np.asarray(alpha, float)
    f = np.asarray(f_alpha, float)
    m = np.isfinite(a) & np.isfinite(f)
    a, f = a[m], f[m]
    o = np.argsort(a)
    a, f = a[o], f[o]
    au, inv = np.unique(a, return_inverse=True)
    return au, np.array([f[inv == k].mean() for k in range(len(au))])


def main():
    hmof = load('full_band_hmof_cg.json')
    core = load('full_band_core_cg.json')
    hmof_x = load('subband_explain_hmof.json')
    core_x = load('subband_explain_core.json')

    hg = classify([r for r in hmof['records'] if r.get('ok')], hmof_x['q25'], hmof_x['q75'])
    cg = classify([r for r in core['records'] if r.get('ok')], core_x['q25'], core_x['q75'])

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))

    for ax, recs, label, n_total in ((axes[0], hg, 'hMOF', 77), (axes[1], cg, 'CoRE MOF', 61)):
        for r in recs:
            a, f = clean_curve(r['alpha'], r['f_alpha'])
            if len(a) < 3:
                continue
            ax.plot(a, f, color=COLORS[r['class']], alpha=0.55, lw=1.1)
        for cls in ('Narrow', 'Medium', 'Wide'):
            ax.plot([], [], color=COLORS[cls], lw=2.5, label=cls)
        ax.set_xlabel(r'$\alpha$')
        ax.set_ylabel(r'$f(\alpha)$')
        ax.set_title(f'{label}: {len(recs)}/{n_total} spectra,\ncoloured by class, coarse-grained supercell graph')
        ax.legend(fontsize=9, title='class (terciles)')
        ax.grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(HERE, 'grouped_spectra_figure.png')
    fig.savefig(out, dpi=150)
    print(f'written {out}')

    # console summary: alpha_0 (apex) and asymmetry per class, both datasets
    for label, recs in (('hMOF', hg), ('CoRE MOF', cg)):
        print(f'\n{label}:')
        for cls in ('Narrow', 'Medium', 'Wide'):
            rows = [r for r in recs if r['class'] == cls]
            if not rows:
                continue
            a0 = np.mean([r['alpha_0'] for r in rows])
            asym = np.mean([r['asymmetry'] for r in rows])
            print(f'  {cls:8s} n={len(rows):3d}  mean alpha_0={a0:.3f}  mean asymmetry={asym:+.3f}')


if __name__ == '__main__':
    main()
