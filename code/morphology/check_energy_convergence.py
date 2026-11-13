"""Convergence of the Phase 4 surface energies in the two numerical settings (audit of 13 November, gap G12).

Run from anywhere:  python3 code/morphology/check_energy_convergence.py
Writes code/morphology/results/energy_convergence.json.

Phase 4 uses a 12 A pair cutoff and 400 offset bins per plane period. This script recomputes gamma for
{100}, {110} and {111} of the four demonstration MOFs at (12 A, 400), (12 A, 1600) and (15 A, 400) and
reports the largest relative change, and whether the face order changes. The bond part does not depend on
the cutoff (bonds are short); the cutoff only adds van der Waals pairs, which are 2-7 % of gamma.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from mofmorph.forcefield import pair_list, pair_energies, cleavage_curve
from run_phase4 import conventional_atoms, MOFS, CIF

OUT = os.path.join(HERE, 'results', 'energy_convergence.json')
FACES = {'{100}': (1, 0, 0), '{110}': (1, 1, 0), '{111}': (1, 1, 1), '{111}-': (-1, -1, -1)}
SETTINGS = [('12A_400bins', 12.0, 400), ('12A_1600bins', 12.0, 1600), ('15A_400bins', 15.0, 400)]


def gammas(atoms, rcut, nbins):
    i, j, d, D, bonded, excl = pair_list(atoms, rcut=rcut)
    cost = pair_energies(atoms, i, j, d, bonded, excl)
    B = np.linalg.inv(atoms.cell[:]).T
    out = {}
    for lab, hkl in FACES.items():
        g = np.array(hkl, float) @ B
        dsp = 1.0 / np.linalg.norm(g)
        _, gam = cleavage_curve(atoms, g * dsp, i, j, D, cost, dsp, nbins=nbins)
        out[lab] = float(gam.min())
    out['{111}'] = min(out['{111}'], out.pop('{111}-'))
    return out


def main():
    t0 = time.time()
    res = dict(script='code/morphology/check_energy_convergence.py', reference='12A_400bins (Phase 4)', mofs={})
    for name, fn in MOFS:
        atoms, _ = conventional_atoms(os.path.join(CIF, fn)); atoms.wrap()
        G = {tag: gammas(atoms, rc, nb) for tag, rc, nb in SETTINGS}
        ref = G['12A_400bins']
        change = {tag: max(abs(G[tag][f] - ref[f]) / ref[f] for f in ref) for tag in G}
        order = {tag: sorted(G[tag], key=G[tag].get) for tag in G}
        res['mofs'][name] = dict(gamma_J_m2={t: {f: round(v, 5) for f, v in g.items()} for t, g in G.items()},
                                 max_relative_change={t: round(c, 5) for t, c in change.items()},
                                 face_order=order, order_unchanged=all(order[t] == order['12A_400bins'] for t in order))
        print(name, {t: round(c, 4) for t, c in change.items()}, 'order unchanged:', res['mofs'][name]['order_unchanged'], flush=True)
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
