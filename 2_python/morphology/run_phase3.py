"""Phase 3: crystal faces and shapes from the periodic graph of each MOF.

Run from anywhere:  python3 2_python/morphology/run_phase3.py
Writes results/phase3_results.json and results/figs/*_phase3*.png.

Steps for each CIF:
 1. Decompose into building blocks and build the labelled quotient graph with the
    project's own pipeline (code_12.quotient_graph_from_cif): bond perception,
    metal-oxo decomposition, edges (i, j, t).
 2. Place each block at the centroid of its unwrapped atoms.
 3. Contract two-connected linkers into edges (standard topological
    deconstruction). Nodes and linkers with three or more connections remain.
 4. For each face family, with the slice thickness d_eff from the space group
    (Phase 1), compute exactly: the attachment number per growth unit, the
    broken-bond surface energy, and the Hartman-Perdok class (F/S/K).
 5. Shapes: growth rates R proportional to the attachment number (Hartman-
    Bennema), and a Wulff shape from the broken-bond surface energies.
"""
import sys, os, json, math, warnings
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))          # the project's 2_python modules
warnings.filterwarnings("ignore")
import numpy as np
import spglib

from code_12_converged_band import quotient_graph_from_cif
from code_05_centroid_simplification import _unwrap_block
from mofmorph.structure import load
from mofmorph.faces import enumerate_faces, families
from mofmorph.models import from_rates, describe
from mofmorph.graphfaces import PeriodicGraph, contract_two_connected, classify
from mofmorph import render

CIF = os.path.join(HERE, "..")
OUT = os.path.join(HERE, "results"); os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
MOFS = [("MOF-5", "MOF5.cif"), ("HKUST-1", "HKUST-1.cif"), ("UiO-66", "UiO-66.cif"), ("ZIF-8", "ZIF-8.cif")]
REPS = {"{100}": (1, 0, 0), "{110}": (1, 1, 0), "{111}": (1, 1, 1), "{111}+": (1, 1, 1), "{111}-": (1, 1, -1),
        "{211}": (2, 1, 1), "{211}+": (2, 1, 1), "{211}-": (2, 1, -1), "{221}": (2, 2, 1), "{310}": (3, 1, 0),
        "{311}": (3, 1, 1), "{311}+": (3, 1, 1), "{311}-": (3, 1, -1)}


def periodic_graph(path):
    blocks, edges, geom = quotient_graph_from_cif(path)
    L = np.array(geom.cell_matrix, float)               # rows = lattice vectors (code_09 convention)
    X, kinds = [], []
    for kind, atoms in blocks:
        u = _unwrap_block(geom, atoms)
        X.append(np.mean([u[a] for a in atoms], axis=0)); kinds.append(kind)
    G = PeriodicGraph(L, np.array(X), edges, kinds)
    return G, geom


def conventional_axes(geom):
    """Conventional cubic cell vectors expressed in the CIF's Cartesian frame.
    spglib: (a_s b_s c_s) = (a b c) P^-1 with basis vectors as columns."""
    L = np.array(geom.cell_matrix, float)
    frac = np.array(geom.pos) @ np.linalg.inv(L)
    nums = [1 + (hash(s) % 90) for s in geom.symbols]
    noH = [k for k, s in enumerate(geom.symbols) if s != "H"]
    best = None
    for idx in (list(range(len(nums))), noH):
        for sp in (1e-3, 1e-2, 5e-2, 1e-1):
            d = spglib.get_symmetry_dataset((L, frac[idx] % 1, [nums[k] for k in idx]), symprec=sp)
            if d is not None:
                if best is None or d.number > best.number:
                    best = d
                break
    P = np.array(best.transformation_matrix, float)
    Lc = (L.T @ np.linalg.inv(P)).T                     # rows = conventional vectors
    return Lc, best.international


def summarize(s):
    d = s.summary(); d["name"] = describe(s); d["name_major_faces"] = describe(s, 0.01)
    d["minor_faces"] = sorted(k for k, v in d["face_area_fraction"].items() if 0 < v <= 0.01)
    d["face_area_fraction"] = {k: round(v, 4) for k, v in d["face_area_fraction"].items()}
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}


def main():
    R = {}
    for name, fn in MOFS:
        path = os.path.join(CIF, fn)
        G0, geom = periodic_graph(path)
        G = contract_two_connected(G0)
        Lc, sg = conventional_axes(geom)
        a_conv = float(np.mean(np.linalg.norm(Lc, axis=1)))
        Bc = np.linalg.inv(Lc).T
        c = load(path, name); F = enumerate_faces(c, 6)
        fam = {f["label"]: f for f in families(F)}
        deg = G.degrees()
        rec = dict(spacegroup=sg, a_conv=round(a_conv, 3),
                   quotient=dict(blocks=len(G0.X), links=len(G0.edges),
                                 node_degrees=sorted(set(dd for dd, k in zip(G0.degrees(), G0.kinds) if k == "node")),
                                 linker_degrees=sorted(set(dd for dd, k in zip(G0.degrees(), G0.kinds) if k == "linker"))),
                   net=dict(vertices=len(G.X), links=len(G.edges), vertex_degrees=sorted(set(deg)),
                            kinds={k: G.kinds.count(k) for k in set(G.kinds)}),
                   faces={})
        for lab, hkl in REPS.items():
            if lab not in fam:
                continue
            n = np.array(hkl, float) @ Bc; n /= np.linalg.norm(n)
            d = fam[lab]["d_eff"]
            q = classify(G, n, d)
            rec["faces"][lab] = dict(d_eff=round(d, 3), E_att=round(q["E_att"], 4), gamma=round(q["gamma_min"], 6),
                                     rank=q["rank"], cls=q["class"], terminations=q["all_terminations"])
        # shapes: attachment-energy growth shape and broken-bond Wulff shape
        att = {lab: v["E_att"] for lab, v in rec["faces"].items() if v["E_att"] > 0}
        gam = {lab: v["gamma"] for lab, v in rec["faces"].items() if v["gamma"] > 0}
        s_att = from_rates(F, att); s_wul = from_rates(F, gam)
        rec["shape_attachment"] = summarize(s_att); rec["shape_wulff_broken_bond"] = summarize(s_wul)
        render.row([s_att, s_wul], [f"{name}: attachment energy\n{describe(s_att, 0.01)}", f"{name}: broken-bond Wulff\n{describe(s_wul, 0.01)}"],
                   os.path.join(OUT, "figs", f"{name}_phase3.png"), size=3.0)
        R[name] = rec
        print(f"\n{name}  {sg}  a={a_conv:.3f}  quotient {len(G0.X)} blocks/{len(G0.edges)} links -> net "
              f"{len(G.X)} vertices/{len(G.edges)} links, degrees {sorted(set(deg))}")
        for lab, v in rec["faces"].items():
            print(f"   {lab:7s} d_eff={v['d_eff']:7.3f}  E_att={v['E_att']:.3f}  gamma={v['gamma']:.5f}  {v['cls']}")
        print("   attachment shape:", describe(s_att, 0.01), "| broken-bond Wulff:", describe(s_wul, 0.01),
              "| faces under 1% of area:", rec["shape_wulff_broken_bond"]["minor_faces"])

    json.dump(R, open(os.path.join(OUT, "phase3_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
