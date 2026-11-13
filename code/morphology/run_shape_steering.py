"""Shape steering: for each cubic MOF, how far each face family must be stabilised to change the
dominant face or reach a pure shape, and which additives in the laboratory records did move it.

Run from anywhere:  python3 code/morphology/run_shape_steering.py
Reads  code/morphology/results/benchmark_mofs.json (structure-only UFF surface energies) and the
       laboratory records; writes code/morphology/results/shape_steering.json.

The model. On the cubic morphology map (morphology_map/cubic_wulff.py) the shape depends only on
x = g110/g100 and y = g111/g100. An additive that adsorbs on one family lowers that family's surface
energy (Gibbs: dg = -Gamma dmu). We ask: by what factor f must g_F of one family F be multiplied
(0 < f <= 1) for (a) F to become the face with the largest share of the surface, and (b) the crystal
to become the pure shape of F (cube for {100}, rhombic dodecahedron for {110}, octahedron for {111})?
(b) has closed forms from the map boundaries; (a) is found by bisection on the exact Wulff areas.
A factor of 1 means "already there"; a small factor means "a strongly binding additive is needed".

The evidence. For every additive category (the fixed text rule of condition_model.py), the faces the
laboratory crystals showed, per MOF, with the papers. A category is reported as moving a MOF towards
a face only from that MOF's own records; records of other MOFs are listed separately.

Limits. The surface energies are unrelaxed UFF values without solvent, so the factors are relative
indications, not binding energies; additive binding energies per face are not computed here.
"""
import os, sys, json, math, re
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(HERE, 'morphology_map'))
import numpy as np
import pandas as pd
from cubic_wulff import wulff_areas

BENCH = os.path.join(HERE, 'results', 'benchmark_mofs.json')
LAB = os.path.join(REPO, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
OUT = os.path.join(HERE, 'results', 'shape_steering.json')
S2, S3 = 2 ** 0.5, 3 ** 0.5
PURE = {'100': 'cube', '110': 'rhombic dodecahedron', '111': 'octahedron'}
DOM = {'cube': '100', 'truncated_cube': '100', 'cube_truncated_edges': '100', 'cuboctahedron': '100',
       'truncated_octahedron': '111', 'octahedron': '111', 'rhombic_dodecahedron': '110', 'truncated_rhombic_dodecahedron': '110'}


def gammas_from_benchmark(p):
    g = {}
    for lab, v in p['uff']['gamma'].items():
        k = re.sub(r'[{}+-]', '', lab)
        if k in ('100', '110', '111'):
            g[k] = min(v, g.get(k, v))       # the lower of {111}+ and {111}- is the one that shows
    return g


def shares(g):
    return wulff_areas(g['100'], g['110'], g['111'])


def dominant(g):
    fr = shares(g)
    return max(fr, key=fr.get), fr


def factor_pure(g, F):
    """Largest f such that g_F -> f g_F gives the pure shape of F (closed forms)."""
    a, b, c = g['100'], g['110'], g['111']
    if F == '100':   # need g111/g100 >= sqrt3 and g110/g100 >= sqrt2 with g100 -> f g100
        return min(1.0, c / (S3 * a), b / (S2 * a))
    if F == '111':   # need g111/g100 <= 1/sqrt3 and g110/g100 >= sqrt(3/2) g111/g100
        return min(1.0, a / (S3 * c), b / (math.sqrt(1.5) * c))
    if F == '110':   # need g110/g100 <= 1/sqrt2 and g111/g100 >= sqrt(3/2) g110/g100
        return min(1.0, a / (S2 * b), c / (math.sqrt(1.5) * b))


def factor_dominant(g, F):
    """Largest f such that F has the largest area share (bisection on the exact Wulff areas)."""
    def ok(f):
        h = dict(g); h[F] = g[F] * f
        d, fr = dominant(h)
        return d == F
    if ok(1.0):
        return 1.0
    lo, hi = 1e-3, 1.0               # ok(lo) should hold: a face far below the others dominates
    if not ok(lo):
        return None
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo


def main():
    B = json.load(open(BENCH))
    lab = pd.read_csv(LAB)
    sys.path.insert(0, os.path.join(HERE, 'morphology_map'))
    import importlib.util
    spec = importlib.util.spec_from_file_location('cm_rules', os.path.join(HERE, 'morphology_map', 'condition_model.py'))
    # the additive rule is copied from condition_model.py so that both use the same categories
    src = open(os.path.join(HERE, 'morphology_map', 'condition_model.py')).read()
    rules = eval(src[src.index('ADDITIVE_RULES = [') + len('ADDITIVE_RULES = '):src.index(']\n\n\ndef additive_category') + 1])

    def cat(a, amount):
        if re.search(r'or none', str(amount)):
            return 'none'
        s = '' if pd.isna(a) else str(a).lower()
        for c, rx in rules:
            if re.search(rx, s):
                return c
        return 'other_additive'
    lab['category'] = [cat(a, m) for a, m in zip(lab.additive, lab.additive_amount)]
    lab['face'] = lab.morphology.map(DOM)
    out = {}
    for mof, p in B['predictions'].items():
        if 'uff' not in p:
            continue
        g = gammas_from_benchmark(p)
        d, fr = dominant(g)
        x, y = g['110'] / g['100'], g['111'] / g['100']
        steer = {}
        for F in ('100', '110', '111'):
            fd, fp = factor_dominant(g, F), factor_pure(g, F)
            steer[F] = dict(target_pure_shape=PURE[F], factor_to_dominate=None if fd is None else round(fd, 3),
                            factor_for_pure_shape=round(fp, 3),
                            lower_by_percent_to_dominate=None if fd is None else round(100 * (1 - fd), 1),
                            lower_by_percent_for_pure_shape=round(100 * (1 - fp), 1))
        recs = lab[(lab.mof == mof) & lab.face.notna()]
        evidence = defaultdict(lambda: Counter())
        papers = defaultdict(set)
        for r in recs.itertuples():
            evidence[r.category][r.face] += 1
            papers[r.category].add(r.source_id)
        out[mof] = dict(structure=p['structure'], gamma_uff=g, map_x=round(x, 4), map_y=round(y, 4),
                        predicted_shape=p['uff']['shape'], predicted_dominant=d, shares={k: round(v, 4) for k, v in fr.items()},
                        steering=steer,
                        lab_evidence={c: dict(faces=dict(v), papers=sorted(papers[c])) for c, v in evidence.items()})
        print(f"{mof:11s} x={x:.3f} y={y:.3f}  predicted {p['uff']['shape']} (dominant {{{d}}})")
        for F, s in steer.items():
            print(f"     to make {{{F}}} dominant: lower g{F} by {s['lower_by_percent_to_dominate']} %;  pure {s['target_pure_shape']}: by {s['lower_by_percent_for_pure_shape']} %")
        for c, v in out[mof]['lab_evidence'].items():
            print(f"     lab, {c}: {v['faces']}  ({', '.join(v['papers'])})")
    res = dict(script='code/morphology/run_shape_steering.py', inputs=['code/morphology/results/benchmark_mofs.json', os.path.relpath(LAB, REPO)],
               note='factor = multiplier on one family\'s UFF surface energy; unrelaxed, no solvent: relative indication only', mofs=out)
    json.dump(res, open(OUT, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
