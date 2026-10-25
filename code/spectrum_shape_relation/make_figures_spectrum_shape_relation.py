"""
make_figures_spectrum_shape_relation.py
=======================================

Draws the three figures of the spectrum <-> shape study from the result files. Nothing is
computed here except the plotting; every number comes from results/*.json.

    figures/01_box_particles_MOF5.png
        left : Delta-alpha against graph diameter; cubes (size trend) and the 64-cell
               slab, plate and rod.
        right: Delta-alpha of the four 64-cell boxes.
    figures/02_predicted_crystal_shapes_MOF5.png
        Delta-alpha of each predicted crystal shape of MOF-5 (BFDH, blend, UFF Wulff, CHGNet)
        and the three reference polyhedra, at about 2000 and 4000 blocks, drawn against the
        cube size trend in block count.
    figures/03_core_mof_spectrum_vs_bfdh_shape.png
        CoRE MOF: aspect ratio of the BFDH shape against Delta-alpha (left) and against
        graph size (right), showing that the raw link goes through size.
    figures/04_dimension_profile_MOF5.png
        left : local dimension d(r) = d ln M / d ln r of the four 1024-cell boxes, against
               r / D; the plate and the rod run at a lower dimension over most scales.
        right: r_half / D (radius holding half of the particle, over the diameter) for the
               seven compact shapes at about 4000 and 8000 blocks, with the seed spread.

The website copies these files into website/figures/relation/.
Run:  python make_figures_spectrum_shape_relation.py
"""
import json
import os
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
FIG = os.path.join(HERE, 'figures')
SITE_FIG = os.path.join(HERE, '..', '..', 'website', 'figures', 'relation')

COL = {'cube': '#1f4e9c', 'slab': '#2e8b57', 'plate': '#c27c0e', 'rod': '#b91c1c'}


def clean(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


def fig01():
    d = json.load(open(os.path.join(RES, '01_box_particles_MOF5.json')))
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    cx = [r['diameter'] for r in d['cubes']]
    cy = [r['width_mean'] for r in d['cubes']]
    ax[0].plot(cx, cy, 'o-', color='#555', label='cubes, 2 to 6 cells per side')
    xx = np.linspace(min(cx), 80, 50)
    ax[0].plot(xx, d['trend']['a'] + d['trend']['b'] * np.log(xx), '--', color='#999', label='cube trend, extended')
    for r in d['shapes']:
        k = r['label'].split()[0]
        ax[0].errorbar(r['diameter'], r['width_mean'], yerr=r['width_sd'], fmt='s', color=COL[k], ms=8, label=r['label'])
    ax[0].set_xlabel('diameter of the particle graph (steps)')
    ax[0].set_ylabel('spectrum width  Δα')
    ax[0].set_title('Plates, slabs and rods fall below the cube size trend', fontsize=10)
    ax[0].legend(fontsize=7.5, frameon=False)
    lab = [r['label'] for r in d['shapes']]
    ax[1].bar(range(len(lab)), [r['width_mean'] for r in d['shapes']], yerr=[r['width_sd'] for r in d['shapes']],
              color=[COL[l.split()[0]] for l in lab], capsize=3)
    ax[1].set_xticks(range(len(lab)))
    ax[1].set_xticklabels([l.replace(' ', '\n') for l in lab], fontsize=8)
    ax[1].set_ylim(1.2, 1.8)
    ax[1].set_ylabel('spectrum width  Δα')
    ax[1].set_title(f'64 unit cells ({d["shapes"][0]["nodes"]} blocks) in every shape', fontsize=10)
    for a in ax:
        clean(a)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, '01_box_particles_MOF5.png'), dpi=150)
    plt.close(fig)


def fig02():
    d = json.load(open(os.path.join(RES, '02_predicted_crystal_shapes_MOF5.json')))
    t = d['cube_trend']
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    pts = t['points']
    ax.plot([p['blocks_in_largest_piece'] for p in pts], [p['width_mean'] for p in pts], 'o', color='#555',
            label='cubes (size trend)')
    xx = np.linspace(min(p['blocks_in_largest_piece'] for p in pts), max(p['blocks_in_largest_piece'] for p in pts), 50)
    ax.plot(xx, t['c_blocks'] + t['d_blocks'] * np.log(xx), '--', color='#999')
    marks = {'BFDH prediction': ('#b91c1c', 'v'), 'BFDH x Wulff blend w=0.5': ('#7b3fa0', 'D'),
             'UFF Wulff prediction': ('#1f4e9c', 's'), 'CHGNet cleavage Wulff prediction': ('#c27c0e', '^'),
             'cube {100} (reference)': ('#888', 's'), 'octahedron {111} (reference)': ('#888', '^'),
             'rhombic dodecahedron {110} (reference)': ('#888', 'h')}
    seen = set()
    for r in d['shapes']:
        c, m = marks[r['shape']]
        ax.errorbar(r['blocks_in_largest_piece'], r['width_mean'], yerr=r['width_sd'], fmt=m, color=c, ms=8,
                    mfc='none' if 'reference' in r['shape'] else c,
                    label=None if r['shape'] in seen else r['shape'])
        seen.add(r['shape'])
    ax.set_xscale('log')
    ax.set_xlabel('number of building blocks in the particle (log scale)')
    ax.set_ylabel('spectrum width  Δα')
    ax.set_title('MOF-5: spectrum width of each predicted crystal shape, against the cube size trend', fontsize=10)
    ax.legend(fontsize=7.5, frameon=False, loc='upper left')
    clean(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, '02_predicted_crystal_shapes_MOF5.png'), dpi=150)
    plt.close(fig)


def fig03():
    d = json.load(open(os.path.join(RES, '03_core_mof_spectrum_vs_bfdh_shape.json')))
    S = d['structures']
    tests = d['tests']['all usable']
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    ar = [r['aspect_ratio'] for r in S]
    ax[0].scatter(ar, [r['width'] for r in S], c=np.log10([r['cg_nodes'] for r in S]), cmap='viridis', s=28)
    ax[0].set_xlabel('aspect ratio of the predicted (BFDH) crystal')
    ax[0].set_ylabel('spectrum width Δα (periodic graph)')
    v = tests['width vs aspect ratio']
    ax[0].set_title(f"raw ρ = {v['spearman']:+.2f};  with size held fixed ρ = "
                    f"{v['partial_spearman_size_controlled']:+.2f}", fontsize=10)
    sc = ax[1].scatter([r['cg_nodes'] for r in S], [r['width'] for r in S], c=ar, cmap='plasma', s=28)
    ax[1].set_xscale('log')
    ax[1].set_xlabel('number of blocks in the periodic graph (log scale)')
    ax[1].set_ylabel('spectrum width Δα')
    ax[1].set_title(f"size alone: ρ = {tests['width vs ln(node count)']['spearman']:+.2f}", fontsize=10)
    cb = plt.colorbar(sc, ax=ax[1])
    cb.set_label('BFDH aspect ratio')
    for a in ax:
        clean(a)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, '03_core_mof_spectrum_vs_bfdh_shape.png'), dpi=150)
    plt.close(fig)


def fig04():
    d = json.load(open(os.path.join(RES, '04_dimension_profile_MOF5.json')))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={'width_ratios': [1, 1.25]})
    for name, p in d['boxes'].items():
        k = name.split()[0]
        r = np.array(p['r'], float)
        y = np.array([np.nan if v is None else v for v in p['d_mean']])
        ax[0].plot(r / p['diameter'], y, color=COL[k], lw=1.8, label=f"{name} (N = {p['blocks']})")
    for (name, p), ls in zip(d.get('reference_lattices', {}).items(), (':', '--', '-.')):
        r = np.array(p['r'], float)
        y = np.array([np.nan if v is None else v for v in p['d_mean']])
        ax[0].plot(r / p['diameter'], y, color='0.45', lw=1.0, ls=ls,
                   label=f"reference: {name} ({p['dimension']}D)")
    ax[0].set_xlabel('radius r / diameter D of the particle graph')
    ax[0].set_ylabel('local dimension  d(r) = d ln M / d ln r')
    ax[0].set_title('Cube, plate and rod follow the 3D, 2D and 1D references', fontsize=10)
    ax[0].set_ylim(0, 3)
    ax[0].legend(fontsize=6.8, frameon=False)
    polys = d['polyhedra']
    names = list(dict.fromkeys(p['shape'] for p in polys))
    short = [n.replace(' (reference)', '').replace(' prediction', '').replace('cleavage ', '') for n in names]
    x = np.arange(len(names))
    for off, target, colr in ((-0.18, 4000, '#1f4e9c'), (0.18, 8000, '#c27c0e')):
        vals = [next(p for p in polys if p['shape'] == n and p['target_blocks'] == target) for n in names]
        ax[1].errorbar(x + off, [v['r_half_over_D_mean'] for v in vals], yerr=[v['r_half_over_D_sd'] for v in vals],
                       fmt='o', color=colr, ms=6, capsize=3, label=f'about {target} blocks')
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(short, rotation=30, ha='right', fontsize=8)
    ax[1].set_ylabel('r_half / D')
    ax[1].set_title('The fill profile separates the compact shapes', fontsize=10)
    ax[1].legend(fontsize=8, frameon=False)
    for a in ax:
        clean(a)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, '04_dimension_profile_MOF5.png'), dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    for f, need in ((fig01, '01_box_particles_MOF5.json'), (fig02, '02_predicted_crystal_shapes_MOF5.json'),
                    (fig03, '03_core_mof_spectrum_vs_bfdh_shape.json'),
                    (fig04, '04_dimension_profile_MOF5.json')):
        if os.path.exists(os.path.join(RES, need)):
            f()
            print('drew', f.__name__)
        else:
            print('skipped', f.__name__, '(run the matching run_0x script first)')
    if os.path.isdir(os.path.dirname(SITE_FIG)):
        os.makedirs(SITE_FIG, exist_ok=True)
        for name in os.listdir(FIG):
            shutil.copyfile(os.path.join(FIG, name), os.path.join(SITE_FIG, name))
        print('copied figures to', os.path.abspath(SITE_FIG))
