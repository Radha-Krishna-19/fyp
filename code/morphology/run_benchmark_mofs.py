"""Benchmark: predict each MOF's crystal shape from its structure alone and score the prediction
against the laboratory records, for every MOF in the dataset that has a usable structure file.

Run from anywhere:  python3 code/morphology/run_benchmark_mofs.py
Writes code/morphology/results/benchmark_mofs.json (and prints a summary).

Structures (column "structure" in the output says which kind each one is):
  measured   a crystal structure from a published file: MOF-5, HKUST-1, UiO-66, ZIF-8 (website/),
             Mg-MOF-74 (data/structures/general_lattice/), IRMOF-3 and IRMOF-8 (data/structures/benchmark/,
             RASPA2 library)
  built      ZIF-67: ZIF-8.cif with Zn replaced by Co (data/structures/benchmark/build_zif67.py); the
             two are isostructural
  stand-in   MIL-53(Fe) scored with the MIL-53(Cr) file, and UiO-66-NH2 with the UiO-66 file: the same
             framework with a different metal or an extra side group. Scored, but reported separately
  none       SNU-70 and Zn4O(FMA)3: no structure file available here; not scored

Structure-only predictions (no laboratory information is used):
  BFDH   the any-lattice BFDH shape (run_general_shape.run_one): its habit (compact, rod, plate) and,
         for a cubic cell, the face family with the largest share of the surface
  UFF    for cubic cells, the Wulff shape from unrelaxed UFF cleavage energies (the Phase 4 method,
         run_phase4.py), and its largest face family

Laboratory labels (data/experimental_morphology/dataset/experimental_morphology.csv):
  dominant face: cube, truncated cube, cube with truncated edges, cuboctahedron -> {100};
                 octahedron, truncated octahedron -> {111}; rhombic dodecahedron and its truncation -> {110}
  habit: the shapes above -> compact; rod, hexagonal rod, needle, spindle -> rod; plate -> plate;
         irregular, intergrown, other, sphere and bipyramid are not scored
Baselines learned from the records, for comparison:
  per-MOF majority, scored two ways: leaving out one paper at a time (it may still have seen other
  papers on the same MOF), and leaving out one MOF at a time (a MOF it has never seen, which is the
  situation of a new framework; it then falls back to the majority over the other MOFs)
"""
import os, sys, json, re, math, time, warnings
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd

LAB = os.path.join(REPO, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
OUT = os.path.join(HERE, 'results', 'benchmark_mofs.json')
W, G, B = os.path.join(REPO, 'website'), os.path.join(REPO, 'data', 'structures', 'general_lattice'), os.path.join(REPO, 'data', 'structures', 'benchmark')
MOFS = [  # dataset name, file, kind
    ('MOF-5', os.path.join(W, 'MOF5.cif'), 'measured'),
    ('HKUST-1', os.path.join(W, 'HKUST-1.cif'), 'measured'),
    ('UiO-66', os.path.join(W, 'UiO-66.cif'), 'measured'),
    ('ZIF-8', os.path.join(W, 'ZIF-8.cif'), 'measured'),
    ('Mg-MOF-74', os.path.join(G, 'MgMOF-74.cif'), 'measured'),
    ('IRMOF-3', os.path.join(B, 'IRMOF-3.cif'), 'measured'),
    ('IRMOF-8', os.path.join(B, 'IRMOF-8.cif'), 'measured'),
    ('ZIF-67', os.path.join(B, 'ZIF-67.cif'), 'built'),
    ('MIL-53(Fe)', os.path.join(G, 'MIL-53Cr-lt.cif'), 'stand-in'),
    ('UiO-66-NH2', os.path.join(W, 'UiO-66.cif'), 'stand-in'),
    ('SNU-70', None, 'none'),
    ('Zn4O(FMA)3', None, 'none'),
]
DOM = {'cube': '100', 'truncated_cube': '100', 'cube_truncated_edges': '100', 'cuboctahedron': '100',
       'truncated_octahedron': '111', 'octahedron': '111', 'rhombic_dodecahedron': '110', 'truncated_rhombic_dodecahedron': '110'}
HABIT = dict({k: 'compact' for k in DOM}, rod='rod', hexagonal_rod='rod', needle='rod', spindle='rod', plate='plate')


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def cubic_family(hkl):
    return ''.join(str(x) for x in sorted((abs(int(v)) for v in hkl), reverse=True))


def bfdh_prediction(path):
    from run_general_shape import run_one
    r = run_one(path)
    a, b, c, al, be, ga = r['cell']
    if r['lattice_system'] == 'cubic' and not (abs(a - b) < 1e-3 * a and abs(b - c) < 1e-3 * a and max(abs(al - 90), abs(be - 90), abs(ga - 90)) < 0.01):
        # a cubic crystal stored in a smaller (primitive) cell, e.g. HKUST-1: redo it in the conventional
        # cubic cell so that the face families read as {100}, {110}, {111}. The shape is the same.
        import tempfile, run_phase4 as P4
        from ase.io import write
        at, _ = P4.conventional_atoms(path)
        tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(path))
        write(tmp, at, format='cif')
        r = run_one(tmp)
    out = dict(cell=r['cell'], spacegroup=r['spacegroup'], operations=r['operations'], lattice_system=r['lattice_system'],
               habit={'equant': 'compact', 'lath': 'rod'}.get(r['habit'], r['habit']), b_over_a=r['b_over_a'], c_over_b=r['c_over_b'],
               long_axis_uvw=r['long_axis_uvw'])
    a, b, c, al, be, ga = r['cell']
    if abs(a - b) < 1e-3 * a and abs(b - c) < 1e-3 * a and max(abs(al - 90), abs(be - 90), abs(ga - 90)) < 0.01:
        share = Counter()
        for F in r['families']:
            share[cubic_family(F['hkl'])] += F['area_fraction']
        fam, frac = share.most_common(1)[0]
        out['dominant_face'] = fam
        out['face_shares'] = {k: round(v, 4) for k, v in share.items() if v > 1e-4}
    return out


def uff_prediction(path):
    import run_phase4 as P4
    from mofmorph.structure import load
    from mofmorph.faces import enumerate_faces, families
    from mofmorph.models import from_rates, describe
    from mofmorph.forcefield import pair_list, pair_energies, surface_energy
    atoms, sg = P4.conventional_atoms(path); atoms.wrap()
    c = load(path, os.path.basename(path)); F = enumerate_faces(c, 6)
    fam = {f['label']: f for f in families(F)}
    i, j, d, D, bonded, excl = pair_list(atoms, rcut=12.0)
    cost = pair_energies(atoms, i, j, d, bonded, excl)
    gam = {}
    for lab, hkl in P4.REPS.items():
        if lab in fam:
            g = surface_energy(atoms, hkl, pairs=(i, j, D, cost))[0]
            if g > 0:
                gam[lab] = round(float(g), 5)
    sh = from_rates(F, gam)
    fr = sh.summary()['face_area_fraction']
    share = Counter()
    for lab, v in fr.items():
        share[re.sub(r'[{}+-]', '', lab)] += v
    return dict(gamma=gam, shape=describe(sh, 0.01), dominant_face=share.most_common(1)[0][0],
                face_shares={k: round(v, 4) for k, v in share.items()})


def main():
    t0 = time.time()
    lab = pd.read_csv(LAB)
    lab['face'] = lab.morphology.map(DOM)
    lab['habit'] = lab.morphology.map(HABIT)
    lab['additive_free'] = lab.additive.fillna('').str.lower().str.match(r'^\s*$|^none') | lab.additive_amount.fillna('').str.contains('or none')
    pred = {}
    for name, path, kind in MOFS:
        p = dict(structure=kind, file=os.path.relpath(path, REPO) if path else None)
        if path:
            t = time.time()
            p['bfdh'] = bfdh_prediction(path)
            if 'dominant_face' in p['bfdh']:
                try:
                    p['uff'] = uff_prediction(path)
                except Exception as e:   # report, do not hide
                    p['uff_error'] = repr(e)[:200]
            p['seconds'] = round(time.time() - t, 1)
        pred[name] = p
        print(name, kind, json.dumps({k: v for k, v in p.items() if k in ('bfdh', 'uff')}, default=str)[:300], flush=True)

    # ---- per-record scoring ----
    rows = []
    for r in lab.itertuples():
        p = pred.get(r.mof, {})
        rows.append(dict(record=r.record_id, mof=r.mof, source=r.source_id, structure=p.get('structure', 'none'),
                         additive_free=bool(r.additive_free), lab_face=r.face if isinstance(r.face, str) else None,
                         lab_habit=r.habit if isinstance(r.habit, str) else None,
                         bfdh_face=p.get('bfdh', {}).get('dominant_face'), uff_face=p.get('uff', {}).get('dominant_face'),
                         bfdh_habit=p.get('bfdh', {}).get('habit')))
    R = pd.DataFrame(rows)

    # learned baselines: per-MOF majority face, leave one paper out and leave one MOF out
    on = R[R.lab_face.notna()].copy()
    lopo, lomo = [], []
    for i, r in on.iterrows():
        tr = on[on.source != r.source]
        per = tr[tr.mof == r.mof].lab_face
        lopo.append(Counter(per).most_common(1)[0][0] if len(per) else Counter(tr.lab_face).most_common(1)[0][0])
        tr2 = on[on.mof != r.mof]
        lomo.append(Counter(tr2.lab_face).most_common(1)[0][0])
    on['majority_lopo'] = lopo; on['majority_lomo'] = lomo

    def score(df, col, truth, name):
        d = df[df[col].notna() & df[truth].notna()]
        k = int((d[col] == d[truth]).sum()); n = len(d)
        return dict(model=name, correct=k, n=n, accuracy=round(k / n, 3) if n else None, ci95=wilson(k, n))

    groups = {
        'measured_and_built': on.structure.isin(['measured', 'built']),
        'stand_in': on.structure == 'stand-in',
    }
    face_scores = {}
    for g, mask in groups.items():
        for free_name, fmask in (('all', on.additive_free | ~on.additive_free), ('additive_free', on.additive_free), ('with_additive', ~on.additive_free)):
            d = on[mask & fmask]
            face_scores[f'{g}/{free_name}'] = [score(d, 'bfdh_face', 'lab_face', 'BFDH (structure only)'),
                                               score(d, 'uff_face', 'lab_face', 'UFF Wulff (structure only)'),
                                               score(d, 'majority_lopo', 'lab_face', 'per-MOF majority, paper held out'),
                                               score(d, 'majority_lomo', 'lab_face', 'majority, whole MOF held out')]
    hab = R[R.lab_habit.notna() & R.bfdh_habit.notna()]
    habit_scores = {}
    for g, m in (('measured_and_built', hab.structure.isin(['measured', 'built'])), ('stand_in', hab.structure == 'stand-in')):
        habit_scores[g] = score(hab[m], 'bfdh_habit', 'lab_habit', 'BFDH habit (structure only)')
        hb = hab[m].assign(always_compact='compact')
        habit_scores[g + '/baseline_always_compact'] = score(hb, 'always_compact', 'lab_habit', 'always compact')
        rodlike = hab[m & (hab.bfdh_habit != 'compact')]
        habit_scores[g + '/where_bfdh_predicts_non_compact'] = score(rodlike, 'bfdh_habit', 'lab_habit', 'BFDH, MOFs predicted rod or plate')
    per_mof = {}
    for m, g in R.groupby('mof'):
        gf = g[g.lab_face.notna()]; gh = g[g.lab_habit.notna() & g.bfdh_habit.notna()]
        per_mof[m] = dict(structure=pred[m]['structure'], records=len(g), on_map=len(gf),
                          lab_faces=dict(Counter(gf.lab_face)), lab_habits=dict(Counter(g.lab_habit.dropna())),
                          bfdh_face=pred[m].get('bfdh', {}).get('dominant_face'), uff_face=pred[m].get('uff', {}).get('dominant_face'),
                          bfdh_habit=pred[m].get('bfdh', {}).get('habit'),
                          bfdh_face_correct=int((gf.bfdh_face == gf.lab_face).sum()) if len(gf) else None,
                          uff_face_correct=int((gf.uff_face == gf.lab_face).sum()) if len(gf) else None,
                          habit_correct=int((gh.bfdh_habit == gh.lab_habit).sum()), habit_scored=len(gh))
    res = dict(script='code/morphology/run_benchmark_mofs.py', lab_file=os.path.relpath(LAB, REPO), n_records=len(lab),
               n_mofs=lab.mof.nunique(), predictions=pred, face_scores=face_scores, habit_scores=habit_scores, per_mof=per_mof,
               seconds=round(time.time() - t0, 1))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print('\nDominant face (on-map records):')
    for k, v in face_scores.items():
        print(' ', k, [(s['model'], f"{s['correct']}/{s['n']}") for s in v])
    print('Habit:', habit_scores)
    print('wrote', OUT, f'({res["seconds"]} s)')


if __name__ == '__main__':
    main()
