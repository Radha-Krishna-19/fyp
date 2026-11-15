"""From one CIF file to its crystal faces and BFDH shape, in one command.

Run from anywhere:  python3 code/morphology/cif_shape.py path/to/structure.cif [--stretch a b c] [--json out.json]

Prints the space group found (spglib), the allowed face families with their effective spacings and
area fractions, and whether the BFDH shape is compact (equant), a rod, a plate or a lath. These are the
steps of run_general_shape.run_one, the same code that the website's "From a CIF to a shape" page is
checked against (website/tests/test_general_shape.js). --stretch scales the cell axes with the atoms
at fixed fractional coordinates (the "Changing the cell" page).

What it does not do: it does not use surface energies (see run_phase4.py for the cubic Wulff step) and
it does not predict which shape a laboratory will grow; it gives the shape the symmetry and plane
spacings imply.
"""
import argparse, json, os, sys, warnings
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
warnings.filterwarnings("ignore")
from run_general_shape import run_one


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cif")
    ap.add_argument("--stretch", nargs=3, type=float, default=(1.0, 1.0, 1.0))
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    r = run_one(os.path.abspath(a.cif), tuple(a.stretch))
    print(f"{r['file']}: {r['n_atoms']} atoms, space group {r['spacegroup']} (No. {r['sg_number']}, "
          f"{r['lattice_system']}), {r['operations']} symmetry operations")
    print(f"cell a b c alpha beta gamma = {' '.join(str(x) for x in r['cell'])}")
    print(f"BFDH shape: {r['habit']}  (b/a = {r['b_over_a']:.3f}, c/b = {r['c_over_b']:.3f}, sphericity {r['sphericity']:.3f})")
    print(f"{'family':12s} {'mult':>4s} {'d (A)':>8s} {'order':>5s} {'d_eff':>8s} {'area':>6s}")
    for f in r["families"]:
        if f["area_fraction"] > 0:
            print(f"{f['label']:12s} {f['multiplicity']:4d} {f['d']:8.3f} {f['order']:5d} {f['d_eff']:8.3f} {f['area_fraction']:6.1%}")
    if r["operations"] == 1:
        print("warning: the file has no symmetry beyond translation (P1); faces that symmetry would forbid are not removed")
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)
    return r


if __name__ == "__main__":
    main()
