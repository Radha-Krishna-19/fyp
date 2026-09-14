"""One-off figure for the size-strata analysis (task E). matplotlib only.
Reads _work/teammate_cg_run.csv (all 76 structures) and
9_dataset/size_scaling/size_strata.json (34-structure network-statistics
subset), draws two panels:
  (a) Delta-alpha vs coarse-grained node count, coloured by the teammate's
      own Narrow/Medium/Wide class -- shows the 48-structure degenerate
      group (256 nodes) spanning all three classes, while every other,
      genuinely distinct graph size is a single class.
  (b) degree heterogeneity (entropy) vs Delta-alpha for the 34-structure
      subset with real network statistics, coloured the same way.
Run from 2_python/. Writes 9_dataset/size_scaling/size_strata_figure.png.
"""
import csv
import json
import os
from collections import Counter, defaultdict

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, '..', '..', '_work', 'teammate_cg_run.csv')
STRATA_PATH = os.path.join(HERE, '..', '9_dataset', 'size_scaling', 'size_strata.json')
OUT_DIR = os.path.join(HERE, '..', '9_dataset', 'size_scaling')

COLORS = {'Narrow': '#27ae60', 'Medium': '#f39c12', 'Wide': '#c0392b'}


def main():
    rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8')))
    strata = json.load(open(STRATA_PATH))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- Panel (a): the full 76, Delta-alpha vs CG node count -------------
    sig_groups = defaultdict(list)
    for r in rows:
        sig_groups[(r['cg_nodes'], r['cg_edges'], r['diameter'])].append(r)

    for cls in ('Narrow', 'Medium', 'Wide'):
        xs = [float(r['cg_nodes']) + np.random.default_rng(hash(r['name']) % 2**32).uniform(-3, 3)
              for r in rows if r['class_printed_edges'] == cls]
        ys = [float(r['delta_alpha']) for r in rows if r['class_printed_edges'] == cls]
        ax1.scatter(xs, ys, s=26, color=COLORS[cls], alpha=0.75, label=cls, edgecolors='none')

    # annotate the degenerate 48-structure group
    deg_key = max(sig_groups, key=lambda k: len(sig_groups[k]))
    deg_rows = sig_groups[deg_key]
    deg_x = float(deg_key[0])
    deg_ys = [float(r['delta_alpha']) for r in deg_rows]
    ax1.annotate(
        f'{len(deg_rows)} structures share this\nEXACT graph ({deg_key[0]} nodes,\n'
        f'{deg_key[1]} edges, diam {deg_key[2]})\nyet span all 3 classes\n'
        f'(Δα {min(deg_ys):.3f}–{max(deg_ys):.3f})',
        xy=(deg_x, np.mean(deg_ys)), xytext=(deg_x + 55, np.mean(deg_ys) - 0.08),
        fontsize=8.5, color='#333',
        arrowprops=dict(arrowstyle='->', color='#333', lw=1))

    ax1.set_xlabel('coarse-grained node count (teammate\'s atomic-then-coarsen supercell)')
    ax1.set_ylabel(r'$\Delta\alpha$')
    ax1.set_title('(a) All 76 hMOF structures: class tracks size,\nexcept where size cannot distinguish them at all')
    ax1.legend(fontsize=9, title='class (teammate\'s quartile cut)')
    ax1.grid(alpha=0.25)

    # ---- Panel (b): degree entropy vs Delta-alpha, 34-structure subset ----
    recs = strata['records']
    for cls in ('Narrow', 'Medium', 'Wide'):
        xs = [r['degree_entropy_norm'] for r in recs.values() if r['class'] == cls]
        ys = [r['delta_alpha_teammate_run'] for r in recs.values() if r['class'] == cls]
        # jitter x slightly since most values coincide exactly
        xs_j = [x + np.random.default_rng(i).uniform(-0.004, 0.004) for i, x in enumerate(xs)]
        ax2.scatter(xs_j, ys, s=30, color=COLORS[cls], alpha=0.8, label=cls, edgecolors='none')

    ax2.set_xlabel('normalised degree-distribution entropy of the correctly\nrebuilt coarse-grained graph (0 = one degree value)')
    ax2.set_ylabel(r'$\Delta\alpha$ (teammate\'s run)')
    ax2.set_title('(b) 34-structure subset with real network statistics:\nmost share one topology, entropy = 0.811 exactly')
    ax2.legend(fontsize=9, title='class')
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, 'size_strata_figure.png')
    fig.savefig(out, dpi=150)
    print(f'written {out}')

    # ---- console summary used in the write-up ----
    total = len(rows)
    frac = len(deg_rows) / total
    print(f'\n{len(deg_rows)}/{total} ({frac:.0%}) structures share the single graph signature {deg_key}')
    cls_counts = Counter(r['class_printed_edges'] for r in deg_rows)
    print(f'  class split within that group: {dict(cls_counts)}')
    others = total - len(deg_rows)
    other_groups = [k for k in sig_groups if k != deg_key]
    mono = sum(1 for k in other_groups if len(set(r['class_printed_edges'] for r in sig_groups[k])) == 1)
    print(f'  of the remaining {len(other_groups)} distinct graph signatures ({others} structures),'
          f' {mono} are entirely one class (monotone in size)')


if __name__ == '__main__':
    main()
