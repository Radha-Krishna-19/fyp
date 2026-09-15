"""Grouped multifractal spectra, drawn the same way on both datasets.

Two panels per dataset, matching one plotting convention throughout this
project: LEFT is every individual spectrum, coloured by class, so nothing is
asserted that is not a real curve underneath; RIGHT is the class average --
mean +/- one standard deviation across members, on a common alpha grid.
Gaussian smoothing (sigma=0.8 on individual curves, sigma=1.0 on the mean/std
band) is applied ONLY to the drawing; every stored Delta-alpha, alpha_0 and
asymmetry number comes from the raw, unsmoothed spectrum. Where the averaged
curve runs out of members before the grid does, the last valid value is held
flat by construction (np.interp clamps outside its input range) rather than
stopping the line -- an honest way to draw "no data past here" without either
inventing a value or leaving a visual gap that reads as a mistake.

matplotlib + scipy only. Reads full_band_hmof_cg.json, full_band_core_cg.json
(curves) and subband_explain_hmof.json, subband_explain_core.json (class
thresholds). Writes grouped_spectra_figure.png.
"""
import json
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

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
    a = np.asarray(alpha, dtype=float)
    f = np.asarray(f_alpha, dtype=float)
    valid = np.isfinite(a) & np.isfinite(f)
    a, f = a[valid], f[valid]
    order = np.argsort(a)
    a, f = a[order], f[order]
    unique_alpha, inverse = np.unique(a, return_inverse=True)
    unique_f = np.array([f[inverse == k].mean() for k in range(len(unique_alpha))])
    return unique_alpha, unique_f


def draw_dataset(ax_raw, ax_avg, recs, label, n_total):
    # ---- left: every individual spectrum, coloured by class -------------
    for r in recs:
        alpha, f = clean_curve(r['alpha'], r['f_alpha'])
        if len(alpha) < 3:
            continue
        f_plot = gaussian_filter1d(f, sigma=0.8)
        ax_raw.plot(alpha, f_plot, color=COLORS[r['class']], alpha=0.40, lw=1.3)

    ax_raw.set_xlabel(r'$\alpha(q)$', fontsize=12)
    ax_raw.set_ylabel(r'$f(\alpha)$', fontsize=12)
    ax_raw.set_title(f'{label}: iNMFA Spectra\nCoarse-Grained Supercell Graphs ({len(recs)}/{n_total})',
                      fontsize=13)
    ax_raw.grid(alpha=0.25)

    # ---- right: class average, mean +/- 1 sd on a common grid -----------
    class_data = defaultdict(list)
    for r in recs:
        alpha, f = clean_curve(r['alpha'], r['f_alpha'])
        if len(alpha) < 3:
            continue
        class_data[r['class']].append((alpha, f))

    all_alpha = np.concatenate([clean_curve(r['alpha'], r['f_alpha'])[0] for r in recs
                                 if len(clean_curve(r['alpha'], r['f_alpha'])[0]) >= 3])
    alpha_low = np.percentile(all_alpha, 2)
    alpha_high = np.percentile(all_alpha, 98)
    grid = np.linspace(alpha_low, alpha_high, 120)

    for cls in ('Narrow', 'Medium', 'Wide'):
        if cls not in class_data:
            continue
        stack = []
        for alpha, f in class_data[cls]:
            interpolated = np.interp(grid, alpha, f, left=np.nan, right=np.nan)
            stack.append(interpolated)
        stack = np.asarray(stack, dtype=float)

        mean = np.nanmean(stack, axis=0)
        std = np.nanstd(stack, axis=0)

        valid = np.isfinite(mean)
        if valid.sum() >= 3:
            mean[~valid] = np.interp(grid[~valid], grid[valid], mean[valid])
            std[~valid] = np.interp(grid[~valid], grid[valid], std[valid])

        mean_plot = gaussian_filter1d(mean, sigma=1.0)
        std_plot = gaussian_filter1d(std, sigma=1.0)

        ax_avg.plot(grid, mean_plot, color=COLORS[cls], lw=2.6,
                    label=f'{cls} (n={len(class_data[cls])})')
        ax_avg.fill_between(grid, mean_plot - std_plot, mean_plot + std_plot,
                             color=COLORS[cls], alpha=0.18)

    ax_avg.set_xlabel(r'$\alpha(q)$', fontsize=12)
    ax_avg.set_ylabel(r'$f(\alpha)$', fontsize=12)
    ax_avg.set_title(f'{label}: Average Spectrum by $\\Delta\\alpha$ Class', fontsize=13)
    ax_avg.legend(title='class (terciles of $\\Delta\\alpha$)')
    ax_avg.grid(alpha=0.25)


def main():
    hmof = load('full_band_hmof_cg.json')
    core = load('full_band_core_cg.json')
    hmof_x = load('subband_explain_hmof.json')
    core_x = load('subband_explain_core.json')

    hg = classify([r for r in hmof['records'] if r.get('ok')], hmof_x['q25'], hmof_x['q75'])
    cg = classify([r for r in core['records'] if r.get('ok')], core_x['q25'], core_x['q75'])

    fig, axes = plt.subplots(2, 2, figsize=(15, 12.4))

    draw_dataset(axes[0, 0], axes[0, 1], hg, 'hMOF', 77)
    draw_dataset(axes[1, 0], axes[1, 1], cg, 'CoRE MOF', 61)

    fig.tight_layout()
    out = os.path.join(HERE, 'grouped_spectra_figure.png')
    fig.savefig(out, dpi=160, bbox_inches='tight')
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
