"""Structure-only shape predictions for all 138 dataset structures (77 hMOF, 61 CoRE MOF 2019).

Run from anywhere:  python3 code/morphology/run_dataset_shapes.py
Writes code/morphology/results/dataset_shapes.json.

These are UNVALIDATED PREDICTIONS: no laboratory shapes exist for these structures. For each file:
the symmetry found (spglib, 0.05 A), the BFDH shape and its habit (compact, rod, plate, lath), the
widest face families, and a flag when the file holds fewer symmetry operations than its cell allows
(then missed cancellations can change the shape). Uses run_general_shape.run_one, the same code that
the website's any-lattice section is checked against.
"""
import os, sys, json, time, warnings
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); warnings.filterwarnings('ignore')
from run_general_shape import run_one
SETS = {'hMOF': os.path.join(REPO, 'data', 'structures', 'hmof'), 'CoRE MOF 2019': os.path.join(REPO, 'data', 'structures', 'core_mof_2019')}
OUT = os.path.join(HERE, 'results', 'dataset_shapes.json')


def main():
    t0 = time.time(); res = {}
    for ds, folder in SETS.items():
        for f in sorted(os.listdir(folder)):
            if not f.endswith('.cif'):
                continue
            t = time.time()
            try:
                r = run_one(os.path.join(folder, f))
                top = [x['label'] for x in sorted(r['families'], key=lambda x: -x['area_fraction']) if x['area_fraction'] > 0.05]
                res[f'{ds}/{f}'] = dict(dataset=ds, n_atoms=r['n_atoms'], spacegroup=r['spacegroup'], lattice_system=r['lattice_system'],
                                        operations=r['operations'], habit=r['habit'], b_over_a=r['b_over_a'], c_over_b=r['c_over_b'],
                                        long_axis_uvw=r['long_axis_uvw'], main_faces=top, sphericity=r['sphericity'],
                                        low_symmetry_file=r['sg_number'] == 1, seconds=round(time.time() - t, 1))
            except Exception as e:
                res[f'{ds}/{f}'] = dict(dataset=ds, error=repr(e)[:200])
            print(f, res[f'{ds}/{f}'].get('habit', res[f'{ds}/{f}'].get('error')), flush=True)
    summary = {}
    for ds in SETS:
        rows = [v for v in res.values() if v['dataset'] == ds]
        summary[ds] = dict(files=len(rows), errors=sum('error' in v for v in rows),
                           habits=dict(Counter(v['habit'] for v in rows if 'habit' in v)),
                           lattice_systems=dict(Counter(v['lattice_system'] for v in rows if 'lattice_system' in v)),
                           p1_files=sum(v.get('low_symmetry_file', False) for v in rows))
    json.dump(dict(script='code/morphology/run_dataset_shapes.py', status='unvalidated predictions', summary=summary, structures=res,
                   seconds=round(time.time() - t0, 1)), open(OUT, 'w'), indent=1)
    print(json.dumps(summary, indent=1)); print('wrote', OUT)


if __name__ == '__main__':
    main()
