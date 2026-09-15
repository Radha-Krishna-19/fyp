"""Grouped multifractal spectra shown as actual BANDS, not coloured lines.

For each class (Narrow/Medium/Wide) each structure's f(alpha) vs alpha curve
is interpolated onto a common alpha grid, then the class is drawn as a
shaded envelope (mean +/- one standard deviation across its members) with a
solid mean line through the middle -- a band, the way this project uses the
word everywhere else (a range Delta-alpha occupies), applied to the whole
spectrum shape instead of to the single width number. Individual member
curves are drawn underneath, very faint, so the band is not asserted without
showing what it is a band OF.

matplotlib only. Reads full_band_hmof_cg.json, full_band_core_cg.json (curves)
and subband_explain_hmof.json, subband_explain_core.json (class thresholds).
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


def band_for_class(rows, grid):
    """Interpolate every member's curve onto `grid`, return (mean, std,
    n_covering) at each grid point. NaN where fewer than 2 members reach
    that alpha, so the shaded region never implies data that is not there."""
    stack = []
    for r in rows:
        a, f = clean_curve(r['alpha'], r['f_alpha'])
        if len(a) < 3:
            continue
        stack.append(np.interp(grid, a, f, left=np.nan, right=np.nan))
    stack = np.asarray(stack)
    n_covering = np.sum(np.isfinite(stack), axis=0)
    mean = np.nanmean(stack, axis=0)
    std = np.nanstd(stack, axis=0)
    mean[n_covering < 2] = np.nan
    std[n_covering < 2] = np.nan
    return mean, std, n_covering


def main():
    hmof = load('full_band_hmof_cg.json')
    core = load('full_band_core_cg.json')
    hmof_x = load('subband_explain_hmof.json')
    core_x = load('subband_explain_core.json')

    hg = classify([r for r in hmof['records'] if r.get('ok')], hmof_x['q25'], hmof_x['q75'])
    cg = classify([r for r in core['records'] if r.get('ok')], core_x['q25'], core_x['q75'])

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))

    for ax, recs, label, n_total in ((axes[0], hg, 'hMOF', 77), (axes[1], cg, 'CoRE MOF', 61)):
        all_alpha = np.concatenate([
            clean_curve(r['alpha'], r['f_alpha'])[0] for r in recs
            if len(clean_curve(r['alpha'], r['f_alpha'])[0]) >= 3])
        lo, hi = np.percentile(all_alpha, [1, 99])
        grid = np.linspace(lo, hi, 160)

        # faint individual members first, so the band is visibly a summary
        # of real curves and not a synthetic shape
        for r in recs:
            a, f = clean_curve(r['alpha'], r['f_alpha'])
            if len(a) < 3:
                continue
            ax.plot(a, f, color=COLORS[r['class']], alpha=0.12, lw=0.8, zorder=1)

        # the band itself: shaded mean +/- 1 sd, one per class, drawn last
        # so it sits on top of the faint member curves
        for cls in ('Narrow', 'Medium', 'Wide'):
            rows = [r for r in recs if r['class'] == cls]
            if not rows:
                continue
            mean, std, n_cov = band_for_class(rows, grid)
            ax.fill_between(grid, mean - std, mean + std, color=COLORS[cls],
                             alpha=0.30, zorder=2, linewidth=0)
            ax.plot(grid, mean, color=COLORS[cls], lw=2.6, zorder=3,
                     label=f'{cls} (n={len(rows)})')

        ax.set_xlabel(r'$\alpha$')
        ax.set_ylabel(r'$f(\alpha)$')
        ax.set_title(f'{label}: {len(recs)}/{n_total} spectra as three bands\n'
                     f'(shaded = mean $\\pm$ 1 sd within class; faint lines = individual members)')
        ax.legend(fontsize=9, title='class (terciles of $\\Delta\\alpha$)', loc='lower left')
        ax.grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(HERE, 'grouped_spectra_figure.png')
    fig.savefig(out, dpi=150)
    print(f'written {out}')

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
