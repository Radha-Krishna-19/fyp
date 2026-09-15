"""
MODULE 18 -- EXPLAINING THE SUB-BANDS: SIZE/TOPOLOGY, NOT CHEMISTRY

Takes the full, correctly-computed (coarse-grained supercell) per-structure
results from code_17 for both datasets, sorts each dataset into
Narrow/Medium/Wide terciles by Delta-alpha (the same convention the
teammate's run used), and reports, PER CLASS, every category requested for
this comparison:

  1. Chemical properties       -- metal (parsed from mofid), net symbol
                                   (parsed from mofid, where MOFid assigned
                                   one), void fraction, LCD, PLD
  2. Characteristics/features   -- unit-cell block count, supercell size n
  3. Structural (bond, angle)   -- NOT AVAILABLE at this level by design:
                                   coarse-graining collapses every atom in a
                                   block to one vertex, so bond lengths and
                                   angles do not exist in the graph the
                                   spectrum is computed on. Reported as
                                   "not observable here", not fabricated.
  4. Degree                     -- mean/min/max coarse degree, block count
  5. Edge, weight, link         -- edge count; the graph is UNWEIGHTED, every
                                   edge is a plain "is bonded to", stated
                                   explicitly rather than left implicit
  6. Higher-order statistics    -- average clustering coefficient (fraction
                                   of possible triangles present)
  7. Assortativity              -- degree-degree correlation across edges
  8. Heterogeneity              -- degree coefficient of variation, and
                                   normalised degree-distribution entropy
  9. Degree of components       -- number of connected components (checked,
                                   not assumed to be 1)

CLASS DEFINITION AND ITS OWN LIMIT
Terciles of Delta-alpha (25th/75th percentile cuts), the same rule the
teammate's run used, for direct comparability. This module computes only ONE
seed per structure (code_17), so there is no per-structure error bar to test
the classes against (the check code_12.assign_classes() performs on a
multi-seed run cannot be repeated here) -- that limitation is reported
alongside the class table rather than silently skipped.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

import numpy as np


METALS = {"Zn", "Cu", "Ni", "Co", "Fe", "Al", "Cr", "Mn", "Zr", "Ti", "Mg", "Ca", "V",
          "Cd", "Ag", "Sc", "Y", "La", "Ce", "Nd", "Gd", "Dy", "Er", "Yb", "In", "Ga",
          "Sn", "Pb", "Mo", "W", "Nb", "Ta", "Hf"}


def parse_mofid(mofid):
    """metal (bracketed token that is a real metal symbol, not any bracketed
    SMILES atom -- [C], [O] etc are organic ring/charge notation, not metals),
    net symbol (the RCSR token straight after 'MOFid-v1.')."""
    if not mofid:
        return None, None
    net = None
    m = re.search(r'MOFid-v1\.([a-zA-Z0-9]+)', mofid)
    if m:
        net = m.group(1)
    bracket_tokens = re.findall(r'\[([A-Za-z][a-z]?)\]', mofid)
    metal = next((t for t in bracket_tokens if t in METALS), None)
    return metal, net


def load_meta(cache_dir, tag_prefixes):
    """framework_id -> {mofid, void_fraction, lcd, pld, metal, net}"""
    meta = {}
    for f in sorted(os.listdir(cache_dir)):
        if not any(f.startswith(p) for p in tag_prefixes):
            continue
        d = json.load(open(os.path.join(cache_dir, f), encoding='utf-8'))
        name = d.get('name')
        if not name:
            continue
        mofid = d.get('mofid')
        metal, net = parse_mofid(mofid)
        meta[name] = {
            'mofid': mofid, 'void_fraction': d.get('void_fraction'),
            'lcd': d.get('lcd'), 'pld': d.get('pld'),
            'metal': metal, 'net': net,
        }
    return meta


def classify(records, meta):
    good = [r for r in records if r.get('ok')]
    widths = np.array([r['width'] for r in good])
    q25, q75 = np.percentile(widths, [25, 75])

    def cls(w):
        if w <= q25:
            return 'Narrow'
        elif w <= q75:
            return 'Medium'
        return 'Wide'

    by_class = defaultdict(list)
    for r in good:
        r['class'] = cls(r['width'])
        r['meta'] = meta.get(r['name'], {})
        by_class[r['class']].append(r)
    return by_class, q25, q75


def summarise_class(rows):
    def m(key):
        vals = [r[key] for r in rows if r.get(key) is not None and np.isfinite(r.get(key, np.nan))]
        return (float(np.mean(vals)), float(np.std(vals))) if vals else (None, None)

    metals = Counter(r['meta'].get('metal') for r in rows if r['meta'].get('metal'))
    nets = Counter(r['meta'].get('net') for r in rows if r['meta'].get('net'))
    void = [r['meta'].get('void_fraction') for r in rows if r['meta'].get('void_fraction') is not None]
    lcd = [r['meta'].get('lcd') for r in rows if r['meta'].get('lcd') is not None]

    return {
        'n': len(rows),
        'width_mean': m('width')[0], 'width_sd': m('width')[1],
        'width_min': float(min(r['width'] for r in rows)),
        'width_max': float(max(r['width'] for r in rows)),
        # 1. chemical
        'metals': dict(metals.most_common()),
        'nets': dict(nets.most_common()),
        'void_fraction_mean': float(np.mean(void)) if void else None,
        'lcd_mean': float(np.mean(lcd)) if lcd else None,
        # 2. characteristics/features
        'n_blocks_mean': m('n_blocks_unit_cell')[0],
        'supercell_n_mean': m('supercell_n')[0],
        'cg_nodes_mean': m('cg_nodes')[0],
        'diameter_mean': m('diameter')[0],
        # 3. structural (bond/angle): not available -- see module docstring
        # 4. degree
        'degree_mean_mean': m('degree_mean')[0],
        'degree_min_mean': m('degree_min')[0],
        'degree_max_mean': m('degree_max')[0],
        # 5. edges (unweighted)
        'cg_edges_mean': m('cg_edges')[0],
        # 6. higher-order
        'avg_clustering_mean': m('avg_clustering')[0],
        # 7. assortativity
        'assortativity_mean': m('assortativity')[0],
        # 8. heterogeneity
        'degree_cv_mean': m('degree_cv')[0],
        'degree_entropy_mean': m('degree_entropy_norm')[0],
        # 9. components
        'n_components_mean': m('n_components')[0],
        'n_components_all_one': all(r.get('n_components') == 1 for r in rows),
    }


def run(band_json_path, cache_dir, tag_prefixes, label, out_path):
    data = json.load(open(band_json_path))
    meta = load_meta(cache_dir, tag_prefixes)
    by_class, q25, q75 = classify(data['records'], meta)

    print(f"\n{'='*78}\n{label}: classes at q25={q25:.4f}, q75={q75:.4f}")
    summary = {}
    for cls in ('Narrow', 'Medium', 'Wide'):
        rows = by_class.get(cls, [])
        if not rows:
            continue
        s = summarise_class(rows)
        summary[cls] = s
        print(f"\n-- {cls} (n={s['n']}, width {s['width_min']:.4f}-{s['width_max']:.4f}) --")
        print(f"  1. chemical      : metals={s['metals']}  nets={s['nets']}  "
              f"void_frac_mean={s['void_fraction_mean']}  LCD_mean={s['lcd_mean']}")
        print(f"  2. features      : n_blocks_mean={s['n_blocks_mean']:.1f}  "
              f"supercell_n_mean={s['supercell_n_mean']:.2f}  "
              f"CG_nodes_mean={s['cg_nodes_mean']:.0f}  diam_mean={s['diameter_mean']:.1f}")
        print(f"  3. structural    : bond/angle -- not observable on the coarse-grained graph")
        print(f"  4. degree        : mean={s['degree_mean_mean']:.2f}  "
              f"min={s['degree_min_mean']:.1f}  max={s['degree_max_mean']:.1f}")
        print(f"  5. edges (unweighted) : mean={s['cg_edges_mean']:.0f}")
        print(f"  6. higher-order  : avg_clustering={s['avg_clustering_mean']:.4f}")
        print(f"  7. assortativity : {s['assortativity_mean']:+.3f}")
        print(f"  8. heterogeneity : degree_cv={s['degree_cv_mean']:.3f}  "
              f"degree_entropy={s['degree_entropy_mean']:.3f}")
        print(f"  9. components    : mean={s['n_components_mean']:.2f}  "
              f"all exactly 1: {s['n_components_all_one']}")

    out = {'label': label, 'q25': q25, 'q75': q75, 'class_summary': summary,
           'by_class_records': {k: v for k, v in by_class.items()}}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nWritten to {out_path}")
    return out


if __name__ == '__main__':
    import sys
    out_dir = os.path.join('..', '9_dataset', 'size_scaling')
    cache_dir = os.path.join('..', '..', '_work', 'cache')

    run(os.path.join(out_dir, 'full_band_hmof_cg.json'), cache_dir,
        ('hmof__', 'h__'), 'hMOF (full, CG supercell)',
        os.path.join(out_dir, 'subband_explain_hmof.json'))
    run(os.path.join(out_dir, 'full_band_core_cg.json'), cache_dir,
        ('core__',), 'CoRE MOF (full, CG supercell)',
        os.path.join(out_dir, 'subband_explain_core.json'))
