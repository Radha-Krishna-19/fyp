"""Figure for the Experiment page: each method's shape next to what the crystals show.

Rows: MOF-5, HKUST-1, UiO-66, ZIF-8. Columns: BFDH; UFF Wulff (Phase 4, flat bond cost);
UFF Wulff with metal-ligand bonds at 0.25x; CHGNet cleavage-energy proxy (intact slabs only).
ZIF-8 has no CHGNet run. Reads results/bond_sensitivity.json, results/slab_pieces.json and the
CHGNet zips; writes results/figs/methods_vs_experiment.png and copies it to the website.

Run:  python -I figs_experiment.py   (after run_bond_sensitivity.py and slab_check.py)
"""
import os, sys, json, shutil, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces
from mofmorph.models import bfdh, from_rates, describe
from mofmorph.render import draw
from mofmorph.chgnet_post import cleavage_energies, wulff_from
from run_phase4 import MOFS, CIF
from mofmorph.chgnet_runs import runs

EXPERIMENT = {"MOF-5": "cube (8 of 8 records)", "HKUST-1": "octahedron (5 of 5)",
              "UiO-66": "poorly faceted; octahedra\nonly with a modulator", "ZIF-8": "rhombic dodecahedron (10 of 10)"}
BS = json.load(open(os.path.join(HERE, "results", "bond_sensitivity.json")))
PIECES = json.load(open(os.path.join(HERE, "results", "slab_pieces.json")))


def chgnet_shape(name):
    found = runs(name)
    if not found or name not in PIECES:
        return None
    folder = found[0].path
    excl = {(x["miller"], x["term"]) for x in PIECES[name] if x["small_initial"] or x["small_relaxed"]}
    return wulff_from(cleavage_energies(folder, exclude=excl))


def main():
    cols = ["BFDH (geometry)", "UFF Wulff\n(flat bond cost)", "UFF Wulff\n(metal-ligand x 0.25)", "CHGNet cleavage\n(intact slabs)"]
    fig = plt.figure(figsize=(12.4, 12.2))
    for r, (name, fn) in enumerate(MOFS):
        F = enumerate_faces(load(os.path.join(CIF, fn), name), 6)
        shapes = [bfdh(F, 40)[0],
                  from_rates(F, BS[name]["by_factor"]["1.0"]["gamma_J_m2"]),
                  from_rates(F, BS[name]["by_factor"]["0.25"]["gamma_J_m2"]),
                  chgnet_shape(name)]
        for c, s in enumerate(shapes):
            ax = fig.add_subplot(4, 5, r * 5 + c + 1, projection="3d")
            if s is None:
                ax.set_axis_off(); ax.text2D(0.5, 0.5, "no CHGNet run", ha="center", fontsize=9, transform=ax.transAxes)
            else:
                draw(ax, s, describe(s, 0.01))
            if r == 0:
                ax.text2D(0.5, 1.22, cols[c], ha="center", fontsize=10, weight="bold", transform=ax.transAxes)
        ax = fig.add_subplot(4, 5, r * 5 + 5); ax.set_axis_off()
        ax.text(0.0, 0.5, f"{name}\nexperiment:\n{EXPERIMENT[name]}", fontsize=10, va="center")
        if r == 0:
            ax.text(0.0, 1.12, "What crystals show", fontsize=10, weight="bold", transform=ax.transAxes)
    fig.text(0.5, 0.005, "Colours: blue {100}, red {111} (pink {111}- where it differs), green {110}, brown {311}, purple {211}.",
             ha="center", fontsize=9)
    os.makedirs(os.path.join(HERE, "results", "figs"), exist_ok=True)
    out = os.path.join(HERE, "results", "figs", "methods_vs_experiment.png")
    plt.savefig(out, dpi=130, bbox_inches="tight"); plt.close(fig)
    web = os.path.join(HERE, "..", "..", "website", "figures", "morph", "methods_vs_experiment.png")
    shutil.copyfile(out, web)
    print("wrote", out, "and", os.path.abspath(web))


if __name__ == "__main__":
    main()
