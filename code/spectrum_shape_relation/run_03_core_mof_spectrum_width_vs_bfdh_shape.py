"""
run_03_core_mof_spectrum_width_vs_bfdh_shape.py
===============================================

QUESTION
--------
Across many real MOFs, is the first-half descriptor (the spectrum width Delta-alpha, measured
on the periodic graph) related to the crystal shape the second half predicts for the SAME MOF?
If it is, after the known effect of graph size has been removed, then the connectivity
descriptor carries morphology information and could be used to screen MOFs for shape.

DATA
----
* Delta-alpha for the CoRE MOF 2019 set: data/spectrum_descriptors/size_scaling/full_band_core_cg.json
  (written by code/spectrum_pipeline/code_17_full_correct_band.py; coarse-grained quotient graph tiled to
  48 Angstrom per axis; 55 of 61 structures usable).
* The 61 CoRE MOF CIF files: data/core_mof_cifs/ (a copy of fyp/_work/core_cifs, kept here so
  this folder is complete on its own).
* Predicted shape: BFDH from the morphology package (code/morphology/mofmorph):
  symmetry by spglib, faces up to |h|,|k|,|l| <= 4, the 40 widest-spaced face families
  (the setting used for Phase 1b), then
      sphericity    = pi^(1/3) (6 V)^(2/3) / A          (1 for a sphere, 0.806 for a cube)
      aspect ratio  = sqrt(largest / smallest eigenvalue of the gyration tensor)
                      (1 for any cubic shape; > 1 for rods and plates)
  BFDH is used because it needs no energies, so it can be run on every structure. UFF energies
  for all 55 would take hours; run_core.py has them for 8.

STATISTICS
----------
* Spearman rank correlation rho (robust to outliers and to non-linear but monotone links).
* Size-controlled ("partial") rho: rank both variables, regress each rank on the rank of
  ln(coarse-grained node count), correlate the residuals. This removes the size effect that
  killed the first-half classes (r = +0.72 between Delta-alpha and node count on CoRE MOF).
* Permutation p-value (10 000 shuffles) and a bootstrap 95 % interval (5 000 resamples).
* Each test is repeated on the structures whose graph is one connected piece, because some
  CoRE graphs keep solvent fragments as extra pieces (see docs/project_notes.md, "New finding").

OUTPUT
------
results/03_core_mof_spectrum_vs_bfdh_shape.json   per-structure table + every statistic
Run time: about 2 to 5 minutes.
"""
import json
import os
import time
import warnings

import numpy as np

import particle_graph_tools as T   # sets up sys.path for the morphology package

warnings.filterwarnings('ignore')
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces
from mofmorph.models import bfdh, describe

BAND_JSON = os.path.join(T.REPO, 'data', 'spectrum_descriptors', 'size_scaling', 'full_band_core_cg.json')
CIF_DIR = os.path.join(T.REPO, 'data', 'structures', 'core_mof_2019')
OUT = os.path.join(T.RESULTS, '03_core_mof_spectrum_vs_bfdh_shape.json')
MAX_INDEX, N_FAMILIES = 4, 40
RNG = np.random.default_rng(0)


# ------------------------------------------------------------------------------------------
# statistics helpers (written out so the method is visible, no black boxes)
# ------------------------------------------------------------------------------------------
def ranks(x):
    """Average ranks (ties share the mean rank), as in Spearman's rho."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind='mergesort')
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    for v in np.unique(x):                      # average the ranks of tied values
        m = x == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x, y):
    return float(np.corrcoef(ranks(x), ranks(y))[0, 1])


def partial_spearman(x, y, z):
    """Spearman correlation of x and y with z held fixed (rank residuals)."""
    rx, ry, rz = ranks(x), ranks(y), ranks(z)
    A = np.vstack([np.ones_like(rz), rz]).T
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    return float(np.corrcoef(ex, ey)[0, 1])


def permutation_p(stat, x, y, z=None, n=10000):
    """Two-sided p: how often a random pairing of x and y gives |stat| at least as large."""
    obs = abs(stat(x, y) if z is None else stat(x, y, z))
    y = np.asarray(y)
    hits = 0
    for _ in range(n):
        yp = RNG.permutation(y)
        v = stat(x, yp) if z is None else stat(x, yp, z)
        hits += abs(v) >= obs - 1e-12
    return (hits + 1) / (n + 1)


def bootstrap_ci(stat, x, y, z=None, n=5000):
    x, y = np.asarray(x), np.asarray(y)
    z = None if z is None else np.asarray(z)
    vals = []
    for _ in range(n):
        i = RNG.integers(0, len(x), len(x))
        if len(set(np.asarray(x)[i])) < 3 or len(set(np.asarray(y)[i])) < 3:
            continue
        vals.append(stat(x[i], y[i]) if z is None else stat(x[i], y[i], z[i]))
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def test(x, y, z):
    return dict(n=len(x),
                spearman=spearman(x, y), spearman_p=permutation_p(spearman, x, y),
                spearman_ci95=bootstrap_ci(spearman, x, y),
                partial_spearman_size_controlled=partial_spearman(x, y, z),
                partial_p=permutation_p(partial_spearman, x, y, z),
                partial_ci95=bootstrap_ci(partial_spearman, x, y, z))


# ------------------------------------------------------------------------------------------
def bfdh_shape_of(cif):
    c = load(cif)
    F = enumerate_faces(c, MAX_INDEX)
    s, _ = bfdh(F, n_families=N_FAMILIES)
    lengths = np.linalg.norm(c.lattice, axis=1)
    return dict(spacegroup=c.spacegroup, sg_number=int(c.sg_number),
                bfdh_name=describe(s, 0.01), sphericity=float(s.sphericity()),
                aspect_ratio=float(s.aspect_ratio()),
                cell_length_ratio=float(lengths.max() / lengths.min()))


def main():
    os.makedirs(T.RESULTS, exist_ok=True)
    t0 = time.time()
    band = json.load(open(BAND_JSON))
    rows = []
    for rec in band['records']:
        if not rec.get('ok'):
            continue
        cif = os.path.join(CIF_DIR, rec['name'] + '.cif')
        try:
            shp = bfdh_shape_of(cif)
        except Exception as e:                          # report, never hide, a failure
            print(f"  {rec['name']}: BFDH failed ({type(e).__name__}: {e})")
            continue
        row = dict(name=rec['name'], width=rec['width'], cg_nodes=rec['cg_nodes'], diameter=rec['diameter'],
                   n_components=rec['n_components'], **shp)
        rows.append(row)
        print(f"  {row['name']:16s} {row['spacegroup']:10s} width {row['width']:.3f}  nodes {row['cg_nodes']:5d}  "
              f"BFDH {row['bfdh_name']:28s} sph {row['sphericity']:.3f}  aspect {row['aspect_ratio']:.2f}", flush=True)

    out = dict(n_band_records=len(band['records']), n_with_shape=len(rows),
               settings=dict(max_index=MAX_INDEX, n_families=N_FAMILIES), structures=rows, tests={})
    for subset, keep in (('all usable', lambda r: True), ('one connected piece only', lambda r: r['n_components'] == 1)):
        R = [r for r in rows if keep(r)]
        w = [r['width'] for r in R]
        size = [np.log(r['cg_nodes']) for r in R]
        out['tests'][subset] = {
            'width vs sphericity': test(w, [r['sphericity'] for r in R], size),
            'width vs aspect ratio': test(w, [r['aspect_ratio'] for r in R], size),
            'width vs cell length ratio': test(w, [r['cell_length_ratio'] for r in R], size),
            'sphericity vs ln(node count)': dict(n=len(R), spearman=spearman([r['sphericity'] for r in R], size)),
            'width vs ln(node count)': dict(n=len(R), spearman=spearman(w, size)),
        }
        for k, v in out['tests'][subset].items():
            extra = (f"  size-controlled {v['partial_spearman_size_controlled']:+.3f} (p {v['partial_p']:.3f})"
                     if 'partial_p' in v else '')
            print(f"  [{subset}] {k:32s} n {v['n']:2d}  rho {v['spearman']:+.3f}{extra}")
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(OUT, 'w'), indent=1, default=float)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
