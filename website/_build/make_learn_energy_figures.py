#!/usr/bin/env python3
"""
make_learn_energy_figures.py -> website/figures/learn/*.png  (pictures for learn_energy.html)

    cut_terminations.png   a crystal cut along one plane at two depths (two terminations), and a slab
                           with vacuum above and below
    torus_vs_particle.png  a periodic tiling (wrap-around, no surface) next to a finite particle, and
                           why an octahedron has a small graph diameter (taxicab distance)
    confound_example.png   the confounding example from the project's own data: spectrum width vs
                           predicted aspect ratio for 55 CoRE MOFs, before and after removing graph
                           size (data: code/spectrum_shape_relation/results/03_*.json)

Drawings 1-2 are schematic (no data). Drawing 3 uses only the saved result file.
Run:  python website/_build/make_learn_energy_figures.py
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, '..', 'figures', 'learn')
REL = os.path.join(HERE, '..', '..', 'code', 'spectrum_shape_relation', 'results',
                   '03_core_mof_spectrum_vs_bfdh_shape.json')
METAL, LINK, CUT = '#1f4e9c', '#c27c0e', '#b91c1c'


def crystal(ax, x0, y0, nx, ny, a=1.0):
    """Squares = metal clusters, short bars = linkers between them (a 2D cartoon of a MOF)."""
    for i in range(nx):
        for j in range(ny):
            x, y = x0 + i * a, y0 + j * a
            ax.add_patch(Rectangle((x - .14, y - .14), .28, .28, color=METAL))
            if i < nx - 1:
                ax.plot([x + .14, x + a - .14], [y, y], color=LINK, lw=3)
            if j < ny - 1:
                ax.plot([x, x], [y + .14, y + a - .14], color=LINK, lw=3)


def fig_cut():
    fig, ax = plt.subplots(1, 3, figsize=(12, 4.8))
    # (a) cut between the layers: breaks linkers only, both sides look alike
    crystal(ax[0], 0, 0, 5, 5)
    ax[0].axhline(2.5, color=CUT, lw=2, ls='--')
    ax[0].set_title('Termination A: cut between layers\n(breaks 5 linkers, both sides alike)', fontsize=9)
    # (b) the same plane direction at another depth: through the metal row
    crystal(ax[1], 0, 0, 5, 5)
    ax[1].axhline(2.0, color=CUT, lw=2, ls='--')
    ax[1].set_title('Termination B: same direction, other depth\n(cuts through metal clusters: costs more)', fontsize=9)
    # (c) a slab: periodic sideways, finite up-down, vacuum above and below
    crystal(ax[2], 0, 1.5, 5, 3)
    for y0 in (0, 4.2):
        ax[2].add_patch(Rectangle((-.5, y0), 5, 1.3, color='#e8eef8'))
    ax[2].text(2, .65, 'vacuum', ha='center', fontsize=9)
    ax[2].text(2, 4.85, 'vacuum', ha='center', fontsize=9)
    ax[2].text(4.7, 2.5, 'repeats\nsideways', fontsize=8, ha='left', va='center')
    ax[2].set_title('A slab: two faces (top and bottom),\nvacuum so the faces do not see their copies', fontsize=9)
    for a in ax:
        a.set_xlim(-.6, 5.6); a.set_ylim(-.5, 5.6); a.set_aspect('equal'); a.axis('off')
    plt.tight_layout(rect=(0, 0, 1, 0.93))
    plt.savefig(os.path.join(FIG, 'cut_terminations.png'), dpi=140)
    plt.close(fig)


def fig_torus():
    fig, ax = plt.subplots(1, 3, figsize=(12, 4.8))
    crystal(ax[0], 0, 0, 5, 5)
    for j in range(5):
        ax[0].add_patch(FancyArrowPatch((4.2, j), (4.9, j), arrowstyle='->', color='#777'))
        ax[0].add_patch(FancyArrowPatch((-.9, j), (-.2, j), arrowstyle='->', color='#777'))
    ax[0].set_title('Periodic tiling (torus): the right edge joins the left\nno surface, so no shape', fontsize=9)
    crystal(ax[1], 0, 0, 5, 5)
    ax[1].add_patch(Rectangle((-.4, -.4), 4.8, 4.8, fill=False, ec=CUT, lw=2))
    ax[1].set_title('Finite particle: cut out, no wrap-around\nit has a surface and a shape', fontsize=9)
    # taxicab ball vs square with the same number of points
    pts = [(x, y) for x in range(-4, 5) for y in range(-4, 5)]
    for (x, y) in pts:
        inside_d = abs(x) + abs(y) <= 3
        inside_s = max(abs(x), abs(y)) <= 2
        c = '#7b3fa0' if inside_d and inside_s else (CUT if inside_d else (METAL if inside_s else '#ddd'))
        ax[2].plot(x, y, 'o', color=c, ms=6)
    ax[2].set_title('Distance = steps along the grid ("taxicab").\nDiamond (red + purple, 25 points): farthest points 6 steps apart.\n'
                    'Square (blue + purple, 25 points): farthest points 8 steps apart.', fontsize=8.5)
    for a in ax[:2]:
        a.set_xlim(-1.2, 5.4); a.set_ylim(-.8, 5.0)
    for a in ax:
        a.set_aspect('equal'); a.axis('off')
    plt.tight_layout(rect=(0, 0, 1, 0.9))
    plt.savefig(os.path.join(FIG, 'torus_vs_particle.png'), dpi=140)
    plt.close(fig)


def ranks(x):
    x = np.asarray(x, float)
    r = np.empty(len(x)); r[np.argsort(x, kind='mergesort')] = np.arange(1, len(x) + 1)
    for v in np.unique(x):
        m = x == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def fig_confound():
    d = json.load(open(REL))
    S = d['structures']
    w = ranks([r['width'] for r in S]); a = ranks([r['aspect_ratio'] for r in S]); z = ranks(np.log([r['cg_nodes'] for r in S]))
    A = np.vstack([np.ones_like(z), z]).T
    ew = w - A @ np.linalg.lstsq(A, w, rcond=None)[0]
    ea = a - A @ np.linalg.lstsq(A, a, rcond=None)[0]
    t = d['tests']['all usable']['width vs aspect ratio']
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].scatter(a, w, c=z, cmap='viridis', s=26)
    ax[0].set_xlabel('rank of predicted aspect ratio'); ax[0].set_ylabel('rank of spectrum width')
    ax[0].set_title(f'Before: a clear trend (Spearman ρ = {t["spearman"]:+.2f})\ncolour = graph size: big graphs sit top right', fontsize=9)
    ax[1].scatter(ea, ew, color='#555', s=26)
    ax[1].axhline(0, color='#ccc'); ax[1].axvline(0, color='#ccc')
    ax[1].set_xlabel('aspect ratio, size removed'); ax[1].set_ylabel('spectrum width, size removed')
    ax[1].set_title(f'After removing graph size: no trend\n(partial ρ = {t["partial_spearman_size_controlled"]:+.3f}, p = {t["partial_p"]:.2f})', fontsize=9)
    for x in ax:
        for s in ('top', 'right'):
            x.spines[s].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, 'confound_example.png'), dpi=140)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    fig_cut(); fig_torus(); fig_confound()
    print('wrote cut_terminations.png, torus_vs_particle.png, confound_example.png in', os.path.abspath(FIG))
