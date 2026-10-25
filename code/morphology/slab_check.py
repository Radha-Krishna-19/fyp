"""Fragment check of the CHGNet (MorphoGraph-MOF) slabs.

For every slab that the notebook relaxed, count the connected pieces before and after relaxation
and name each small piece by its formula, so that a detached H atom, a CO2-like piece and a whole
benzene ring can be told apart. A piece is small when it holds fewer than 5 % of the slab's atoms.

Bonds: ASE covalent radii x 1.15 (Zn-O 2.16 A, Cu-O 2.28 A, Zr-O 2.77 A, C-C 1.75 A cut-offs,
all above the bond lengths in these frameworks, so intact Zn4O / Cu2 / Zr6 clusters stay whole).

Each record also carries the slab's bulk-equivalent thickness, N_slab / N_cell * V_cell / A.

Run:  python -I slab_check.py            (reads data/chgnet_morphograph_runs/<MOF>_<date>/)
Writes results/slab_pieces.json and prints a summary.
"""
import collections
import csv
import glob
import io
import json
import os
import sys
import warnings
import zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mofmorph.chgnet_runs import runs, open_archive

import numpy as np
from ase.io import read
from ase.neighborlist import natural_cutoffs, neighbor_list
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
EV_A2_TO_J_M2 = 16.021766
SMALL = 0.05


def pieces(at, mult=1.15):
    """Connected pieces of the periodic bond graph: list of (size, formula), largest first."""
    i, j = neighbor_list("ij", at, natural_cutoffs(at, mult=mult))
    n = len(at)
    nc, lab = connected_components(coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n)), directed=False)
    sym = np.array(at.get_chemical_symbols())
    out = []
    for c in range(nc):
        idx = np.where(lab == c)[0]
        cnt = collections.Counter(sym[idx])
        formula = "".join(f"{e}{cnt[e] if cnt[e] > 1 else ''}" for e in sorted(cnt))
        out.append((len(idx), formula))
    return sorted(out, reverse=True)


def small_pieces(pc, n):
    return [f for s, f in pc if s < SMALL * n]


def read_cif_from_zip(z, inner):
    with z.open(inner) as fh:
        return read(io.StringIO(fh.read().decode("utf-8")), format="cif")


def check_zip(path):
    z = open_archive(path)
    names = z.namelist()
    rec_name = next(n for n in names if n.endswith("_surface_pair_records.csv"))
    rows = list(csv.DictReader(io.StringIO(z.read(rec_name).decode("utf-8"))))
    bulk = read_cif_from_zip(z, next(n for n in names if n.endswith("_working_cell.cif")))
    n_bulk, v_bulk = len(bulk), bulk.get_volume()

    def inner(p):  # CSV holds paths relative to the notebook's working folder
        tail = p.replace("\\", "/").split("/", 1)[-1] if p else ""
        return next((n for n in names if tail and n.endswith(tail)), None)

    res = []
    for r in rows:
        rel, ini = inner(r.get("relaxed_slab_file")), inner(r.get("initial_slab_file"))
        if not rel or not ini:
            continue
        a_rel, a_ini = read_cif_from_zip(z, rel), read_cif_from_zip(z, ini)
        p_rel, p_ini = pieces(a_rel), pieces(a_ini)
        res.append(dict(miller=r["miller"], term=r["termination"], n=len(a_rel),
                        pair_J_m2=float(r["pair_excess_eV_A2"]) * EV_A2_TO_J_M2,
                        # bulk-equivalent thickness: the slab's atoms packed at bulk density
                        thickness_A=round(len(a_rel) / n_bulk * v_bulk / float(r["area_A2"]), 2),
                        fmax=float(r["fmax_eV_A"]) if r.get("fmax_eV_A") else None,
                        status=r.get("status", ""),
                        small_initial=small_pieces(p_ini, len(a_ini)),
                        small_relaxed=small_pieces(p_rel, len(a_rel)),
                        n_pieces_initial=len(p_ini), n_pieces_relaxed=len(p_rel)))
    return res


def main():
    out = {}
    for run in runs():
        name = run.mof
        res = check_zip(run.path)
        if not res:
            print(f"== {name}: no relaxed slabs in this run")
            continue
        out[name] = res
        cut_before = [x for x in res if x["small_initial"]]
        cut_after = [x for x in res if x["small_relaxed"]]
        kinds = collections.Counter(f for x in res for f in x["small_initial"])
        print(f"== {name}: {len(res)} relaxed slabs; {len(cut_before)} have small detached pieces as CUT "
              f"(before relaxation); {len(cut_after)} after relaxation")
        print("   pieces in the cut slabs (formula: count):", dict(kinds.most_common(8)))
        for x in sorted(res, key=lambda x: x["pair_J_m2"])[:5]:
            print(f"   {x['miller']:12s} t{x['term']:>4s} pair={x['pair_J_m2']:.3f} J/m2 "
                  f"small pieces before={x['small_initial'][:4]} after={x['small_relaxed'][:4]}")
    json.dump(out, open(os.path.join(HERE, "results", "slab_pieces.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
