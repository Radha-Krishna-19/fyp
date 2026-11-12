"""Dry run of slab generation (no CHGNet): which slab options can give individual surface energies?

For each MOF and each facet class of the CHGNet runs, this builds slabs with pymatgen exactly as
the notebooks do (same relaxed bulk cell, 15 A slab, 20 A vacuum, ftol 0.1) and counts:
  as_cut     - the team's CHGNet notebook: every termination, linkers may be cut;
  intact     - only terminations that break no C-C, C-H, C-O, C-N bond (KEEP_LINKERS_INTACT);
  symmetrized- pymatgen's symmetrize=True slabs (the symmetric-slab notebook adds these).
For each it reports how many are stoichiometric and how many are symmetric (both faces equal).
A stoichiometric AND symmetric slab gives gamma = excess / 2 for its termination directly.

Run:  python -I slab_options_check.py      Writes results/slab_options.json
"""
import csv, glob, io, json, os, sys, warnings, zipfile
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
from pymatgen.core import Structure
from pymatgen.core.surface import SlabGenerator

LINKER_BONDS = {("C", "C"): 1.75, ("C", "H"): 1.25, ("C", "O"): 1.6, ("C", "N"): 1.6,
                ("N", "N"): 1.6, ("N", "H"): 1.2, ("O", "H"): 1.2}


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mofmorph.chgnet_runs import runs

def proportional(slab, bulk):
    a, b = slab.composition.get_el_amt_dict(), bulk.composition.get_el_amt_dict()
    if set(a) != set(b):
        return False
    r = [a[e] / b[e] for e in b]
    return max(r) - min(r) < 1e-6


def count(slabs, bulk):
    st = [s for s in slabs if proportional(s, bulk)]
    sym = [s for s in slabs if s.is_symmetric(symprec=0.1)]
    both = [s for s in st if s.is_symmetric(symprec=0.1)]
    return dict(n=len(slabs), stoichiometric=len(st), symmetric=len(sym), stoich_and_symmetric=len(both))


def main():
    out = {}
    for run in runs():
        name = run.mof
        Z = run; names = Z.namelist()
        fit = next((n for n in names if n.endswith("_surface_pair_fit_summary.csv")), None)
        rows = list(csv.DictReader(io.StringIO(Z.read(fit).decode()))) if fit else []
        if not rows:
            continue
        bulk = Structure.from_str(Z.read(next(n for n in names if n.endswith("_bulk_relaxed_fixed_cell.cif"))).decode(), fmt="cif")
        bonds = {k: v for k, v in LINKER_BONDS.items() if set(k) <= {str(e) for e in bulk.composition.elements}}
        out[name] = {}
        for r in rows:
            hkl = (int(r["h"]), int(r["k"]), int(r["l"]))
            gen = SlabGenerator(bulk, hkl, 15.0, 20.0, in_unit_planes=False, center_slab=True, primitive=True, reorient_lattice=True)
            res = dict(as_cut=count(gen.get_slabs(symmetrize=False, filter_out_sym_slabs=False, ftol=0.1), bulk))
            try:
                res["intact"] = count(gen.get_slabs(bonds=bonds, max_broken_bonds=0, symmetrize=False,
                                                    filter_out_sym_slabs=False, ftol=0.1), bulk)
            except Exception as e:
                res["intact"] = dict(error=f"{type(e).__name__}: {e}")
            try:
                res["symmetrized"] = count(gen.get_slabs(symmetrize=True, filter_out_sym_slabs=False, ftol=0.1), bulk)
            except Exception as e:
                res["symmetrized"] = dict(error=f"{type(e).__name__}: {e}")
            out[name][r["miller"]] = res
            print(name, r["miller"], res, flush=True)
    json.dump(out, open(os.path.join(HERE, "results", "slab_options.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
