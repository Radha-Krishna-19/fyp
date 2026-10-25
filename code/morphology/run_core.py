"""BFDH, UFF Wulff and hybrid shapes for real CoRE MOF 2019 structures of every crystal system.

The handoff asked for the pipeline to be tried on CoRE MOF structures (the CO2-screening set of
this project). Eight were chosen from the 61 CoRE MOF 2019 CIFs in `data/structures/core_mof_2019/`
to cover six crystal systems and six metals, with at most 840 atoms so the force-field sum stays
quick.  No experimental shapes are known to us for them, so this
is a demonstration that the method runs on any framework, not a validation.

Faces: the 12 widest-spaced symmetry families with |h|,|k|,|l| <= 3. Energies: Phase 4 UFF
(unrelaxed, flat 70 kcal/mol bond cost, all atoms including H). Shapes: BFDH on the same faces,
UFF Wulff, and the hybrid at w = 0.5.

Run:  python -I run_core.py      Writes results/core_results.json and results/figs/core_shapes.png
"""
import os, sys, json, time, shutil, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mofmorph.hybrid import uff_gammas, hybrid_shape
from mofmorph.models import describe
from mofmorph.render import draw

PICK = ["ABAVIJ", "ACIBIY", "ACOLOV", "ACIBOE", "ABETIN", "ABEXEN", "ACAJIY", "ADATAC"]
SYSTEM = [(2, "triclinic"), (15, "monoclinic"), (74, "orthorhombic"), (142, "tetragonal"),
          (167, "trigonal"), (194, "hexagonal"), (230, "cubic")]
DATA = os.path.join(HERE, "..", "..", "data", "structures", "core_mof_2019")   # the 61 CoRE MOF 2019 CIFs used by the project


def crystal_system(n):
    return next(s for top, s in SYSTEM if n <= top)


def main():
    out, shapes = {}, []
    for code in PICK:
        path = os.path.join(DATA, f"{code}_clean.cif")
        t0 = time.time()
        F, fams, names, gamma, c = uff_gammas(path, code, n_families=12, max_index=3, verbose=False)
        rec = dict(spacegroup=c.spacegroup, sg_number=int(c.sg_number), crystal_system=crystal_system(c.sg_number),
                   metals=sorted(set(_symbols(c)) - {"C", "H", "N", "O", "S", "Cl", "Br", "F", "P"}),
                   gamma_J_m2={k: round(v, 4) for k, v in gamma.items()}, shapes={})
        row = []
        for label, w in (("BFDH", 0.0), ("hybrid w=0.5", 0.5), ("UFF Wulff", 1.0)):
            s = hybrid_shape(F, fams, names, gamma, w)
            sm = s.summary()
            rec["shapes"][label] = dict(name=describe(s, 0.01), sphericity=round(sm["sphericity"], 3),
                                        aspect_ratio=round(sm["aspect_ratio"], 2),
                                        faces={k: round(float(v), 3) for k, v in sm["face_area_fraction"].items() if v > 0.01})
            row.append(s)
        out[code] = rec; shapes.append((code, rec, row))
        b, u = rec["shapes"]["BFDH"], rec["shapes"]["UFF Wulff"]
        print(f"{code} {c.spacegroup:10s} {rec['crystal_system']:12s} ({time.time()-t0:4.0f}s)  "
              f"BFDH aspect {b['aspect_ratio']} | UFF aspect {u['aspect_ratio']}  "
              f"UFF top faces {dict(sorted(u['faces'].items(), key=lambda x: -x[1])[:3])}", flush=True)
    json.dump(out, open(os.path.join(HERE, "results", "core_results.json"), "w"), indent=1)

    fig = plt.figure(figsize=(3 * 2.6, len(shapes) * 2.7))
    for r, (code, rec, row) in enumerate(shapes):
        for col, (label, s) in enumerate(zip(("BFDH", "hybrid w=0.5", "UFF Wulff"), row)):
            ax = fig.add_subplot(len(shapes), 3, r * 3 + col + 1, projection="3d")
            draw(ax, s, f"{code} ({rec['spacegroup']}): {label}" if col == 0 else label)
    plt.savefig(os.path.join(HERE, "results", "figs", "core_shapes.png"), dpi=110, bbox_inches="tight"); plt.close(fig)
    shutil.copyfile(os.path.join(HERE, "results", "figs", "core_shapes.png"),
                    os.path.join(HERE, "..", "..", "website", "figures", "morph", "core_shapes.png"))


def _symbols(c):
    from ase.data import chemical_symbols
    return [chemical_symbols[z] for z in c.numbers]


if __name__ == "__main__":
    main()
