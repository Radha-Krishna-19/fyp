"""Checks for the benchmark, shape-steering and shape-to-adsorption results (run after the three scripts).
Run:  python3 code/morphology/check_new_analyses.py      exits non-zero on any failure."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'morphology_map'))
from cubic_wulff import wulff_areas
R = lambda n: json.load(open(os.path.join(HERE, 'results', n)))
B, S, A = R('benchmark_mofs.json'), R('shape_steering.json'), R('shape_adsorption.json')
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
# 1. benchmark: the four original MOFs keep their Phase 4 UFF shapes
P4 = json.load(open(os.path.join(HERE, 'results', 'phase4_results.json')))
for m in ('MOF-5', 'HKUST-1', 'UiO-66', 'ZIF-8'):
    ok(B['predictions'][m]['uff']['shape'] == P4[m]['shape_wulff_uff']['name'], f'{m}: benchmark UFF shape equals Phase 4 ({P4[m]["shape_wulff_uff"]["name"]})')
# 2. steering: applying the pure-shape factor gives (to within 1 %) a single face family
for m, r in S['mofs'].items():
    g = r['gamma_uff']
    for F, st in r['steering'].items():
        h = dict(g); h[F] = g[F] * st['factor_for_pure_shape'] * 0.999
        fr = wulff_areas(h['100'], h['110'], h['111'])
        ok(fr[F] > 0.99, f'{m}: lowering g{F} by {st["lower_by_percent_for_pure_shape"]} % gives the pure {st["target_pure_shape"]} ({fr[F]:.3f})')
# 3. adsorption: the plane sampling agrees with independent random 3D sampling
for m, r in A['mofs'].items():
    for F, f in r['faces'].items():
        d = abs(f['CO2']['open_fraction_mean_over_positions'] - r['bulk_open_fraction_3D']['CO2'])
        ok(d < 0.015, f'{m} {{{F}}}: plane-averaged open fraction {f["CO2"]["open_fraction_mean_over_positions"]} vs 3D {r["bulk_open_fraction_3D"]["CO2"]}')
print(f'{len(fails)} failures'); sys.exit(1 if fails else 0)
