"""Phase 4 check: does the UFF Wulff shape survive a chemically more realistic bond cost?

Phase 4 charges every cut bond the same flat 70 kcal/mol (UFF's default Morse depth). In a MOF
the bonds a surface actually breaks are mostly metal-ligand coordination bonds (Zn-O, Cu-O, Zr-O,
Zn-N), which are weaker than the C-C and C-H bonds inside a linker. A plane that cuts through a
linker should therefore cost more than one that cuts metal-ligand bonds, and a flat cost hides
that difference.

This script keeps organic bonds (no metal atom) at 70 kcal/mol and multiplies the cost of every
bond to a metal atom by f = 1 (Phase 4 as published), 0.5 and 0.25. The van der Waals part is
unchanged. If a MOF's shape is the same for all f, the Phase 4 shape does not depend on the flat
bond assumption; if it changes, the Phase 4 shape should be quoted only with that caveat.

Run:  python -I run_bond_sensitivity.py      Writes results/bond_sensitivity.json
"""
import os, sys, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import numpy as np
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families
from mofmorph.models import from_rates, describe
from mofmorph.forcefield import pair_list, pair_energies, surface_energy
from run_phase4 import conventional_atoms, MOFS, REPS, CIF

METALS = {"Zn", "Cu", "Zr", "Hf", "Co", "Mg", "Fe", "Cr", "Al"}
FACTORS = (1.0, 0.5, 0.25)


def main():
    out = {}
    for name, fn in MOFS:
        atoms, sg = conventional_atoms(os.path.join(CIF, fn)); atoms.wrap()
        F = enumerate_faces(load(os.path.join(CIF, fn), name), 6)
        labels = {f["label"] for f in families(F)}
        i, j, d, D, bonded, excl = pair_list(atoms, rcut=12.0)
        base = pair_energies(atoms, i, j, d, bonded, excl)
        sym = np.array(atoms.get_chemical_symbols())
        metal_bond = bonded & (np.isin(sym[i], list(METALS)) | np.isin(sym[j], list(METALS)))
        rec = dict(spacegroup=sg, n_bonds=int(bonded.sum()), n_metal_ligand_bonds=int(metal_bond.sum()), by_factor={})
        for fct in FACTORS:
            cost = np.where(metal_bond, base * fct, base)
            gam = {}
            for lab, hkl in REPS.items():
                if lab in labels:
                    g = surface_energy(atoms, hkl, pairs=(i, j, D, cost))[0]
                    if g > 0:
                        gam[lab] = round(float(g), 5)
            sh = from_rates(F, gam)
            fr = sh.summary()["face_area_fraction"]
            rec["by_factor"][str(fct)] = dict(gamma_J_m2=gam, shape=describe(sh, 0.01),
                                              faces={k: round(float(v), 3) for k, v in fr.items() if v > 0.005})
            print(f"{name:8s} f={fct:<5} {describe(sh, 0.01):28s}", {k: round(v, 3) for k, v in gam.items()})
        shapes = {v["shape"] for v in rec["by_factor"].values()}
        rec["shape_robust"] = len(shapes) == 1
        out[name] = rec
    json.dump(out, open(os.path.join(HERE, "results", "bond_sensitivity.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
