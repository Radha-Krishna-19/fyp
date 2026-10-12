"""Phase 4: force-field (unrelaxed UFF) cleavage energies and Wulff shapes for the four MOFs.
Run:  python3 2_python/morphology/run_phase4.py [path-to-cif-folder]
"""
import sys, os, json, warnings, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import numpy as np, spglib
from ase.io import read
from ase.build import make_supercell
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families
from mofmorph.models import from_rates, describe
from mofmorph.forcefield import pair_list, pair_energies, surface_energy
from mofmorph import render

CIF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "1_website")
OUT = os.path.join(HERE, "results"); os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
MOFS = [("MOF-5", "MOF5.cif"), ("HKUST-1", "HKUST-1.cif"), ("UiO-66", "UiO-66.cif"), ("ZIF-8", "ZIF-8.cif")]
REPS = {"{100}": (1, 0, 0), "{110}": (1, 1, 0), "{111}": (1, 1, 1), "{111}+": (1, 1, 1), "{111}-": (1, 1, -1),
        "{211}": (2, 1, 1), "{211}+": (2, 1, 1), "{211}-": (2, 1, -1), "{221}": (2, 2, 1), "{310}": (3, 1, 0)}


def conventional_atoms(path):
    """Atoms in the conventional cubic cell (the symmetry is found without H, as in Phase 1)."""
    at = read(path)
    keep = [k for k, s in enumerate(at.get_chemical_symbols()) if s != "H"]
    best = None
    for idx in (list(range(len(at))), keep):
        for sp in (1e-3, 1e-2, 5e-2, 1e-1):
            cell = (at.cell[:], at.get_scaled_positions()[idx], at.numbers[idx])
            d = spglib.get_symmetry_dataset(cell, symprec=sp)
            if d is not None:
                if best is None or d.number > best.number:
                    best = d
                break
    P = np.array(best.transformation_matrix, float)
    M = np.rint(np.linalg.inv(P).T @ np.eye(3)).astype(int) if False else None
    Lc = (at.cell[:].T @ np.linalg.inv(P)).T
    Mx = np.rint(Lc @ np.linalg.inv(at.cell[:])).astype(int)
    assert np.allclose(Mx @ at.cell[:], Lc, atol=1e-6), "conventional cell is not an integer multiple of the file cell"
    return make_supercell(at, Mx), best.international


def main():
    R = {}
    for name, fn in MOFS:
        t0 = time.time()
        atoms, sg = conventional_atoms(os.path.join(CIF, fn))
        atoms.wrap()
        c = load(os.path.join(CIF, fn), name); F = enumerate_faces(c, 6)
        fam = {f["label"]: f for f in families(F)}
        i, j, d, D, bonded, excl = pair_list(atoms, rcut=12.0)
        cost = pair_energies(atoms, i, j, d, bonded, excl)
        cost_vdw = np.where(bonded, 0.0, cost); cost_bond = np.where(bonded, cost, 0.0)
        rec = dict(spacegroup=sg, n_atoms=len(atoms), a_conv=round(float(np.mean(np.linalg.norm(atoms.cell[:], axis=1))), 3),
                   pairs=int(len(i)), bonds=int(bonded.sum()), faces={})
        for lab, hkl in REPS.items():
            if lab not in fam:
                continue
            g, s, dsp, _ = surface_energy(atoms, hkl, pairs=(i, j, D, cost))
            gv = surface_energy(atoms, hkl, pairs=(i, j, D, cost_vdw))[0]
            gb = surface_energy(atoms, hkl, pairs=(i, j, D, cost_bond))[0]
            rec["faces"][lab] = dict(hkl=list(hkl), d=round(dsp, 3), gamma=round(g, 5), gamma_vdw_only=round(gv, 5), gamma_bond_only=round(gb, 5),
                                     offset=round(s, 3))
        gam = {k: v["gamma"] for k, v in rec["faces"].items() if v["gamma"] > 0}
        sh = from_rates(F, gam)
        sens = {}
        for w in (0, 1, 5, 20, 100):
            gw = {k: v["gamma_bond_only"] + w * v["gamma_vdw_only"] for k, v in rec["faces"].items()}
            sens[str(w)] = describe(from_rates(F, gw), 0.01)
        rec["sensitivity_vdw_weight"] = sens
        rec["shape_wulff_uff"] = dict(name=describe(sh, 0.01), **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in sh.summary().items() if k != "face_area_fraction"},
                                      face_area_fraction={k: round(v, 4) for k, v in sh.summary()["face_area_fraction"].items()})
        render.row([sh], [f"{name}: UFF Wulff\n{describe(sh, 0.01)}"], os.path.join(OUT, "figs", f"{name}_phase4.png"), size=3.2)
        R[name] = rec
        print(f"\n{name} {sg}  atoms={len(atoms)} pairs={len(i)} bonds={int(bonded.sum())}  ({time.time()-t0:.0f}s)")
        for lab, v in rec["faces"].items():
            print(f"   {lab:7s} d={v['d']:7.3f}  gamma={v['gamma']:.4f} J/m2 (vdW {v['gamma_vdw_only']:.4f}, bonds {v['gamma_bond_only']:.4f})")
        print("   Wulff:", rec["shape_wulff_uff"]["name"], "| vdW weight 0/1/5/20/100:", list(sens.values()))
    json.dump(R, open(os.path.join(OUT, "phase4_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
