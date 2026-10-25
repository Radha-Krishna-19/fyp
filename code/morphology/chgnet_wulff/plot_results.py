"""Draw predicted vs lab crystal shapes from the pipeline's CSV output.

    python plot_results.py <results folder>            -> <results folder>/shapes.png

Reads wulff_summary.csv (lab shape, predicted shape, area fractions) and
surface_energies.csv (gamma per face). Nothing about any MOF is written here.
One row per MOF: predicted Wulff shape | ideal lab shape | surface energy bars.
"""
import itertools
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import HalfspaceIntersection

FAMILIES = ["{100}", "{110}", "{111}"]
COLOR = {"{100}": "#2a78d6", "{110}": "#eb6834", "{111}": "#1baf7a"}   # validated categorical slots 1-3
INK, MUTED = "#2b2b29", "#8a8984"

# Relative face energies that produce each named ideal polyhedron (geometry definitions).
IDEAL = {"cube": {"{100}": 1.0}, "octahedron": {"{111}": 1.0},
         "rhombic_dodecahedron": {"{110}": 1.0},
         "truncated_octahedron": {"{111}": 1.0, "{100}": 1.15},
         "truncated_cube": {"{100}": 1.0, "{111}": 1.6},
         "cuboctahedron": {"{100}": 1.0, "{111}": 0.866},
         "truncated_rhombic_dodecahedron": {"{110}": 1.0, "{100}": 1.2}}


def orbit(fam):
    base = tuple(int(c) for c in fam.strip("{}"))
    out = set()
    for p in itertools.permutations(base):
        for s in itertools.product((1, -1), repeat=3):
            out.add(tuple(a * b for a, b in zip(p, s)))
    return [np.array(v, float) / np.linalg.norm(v) for v in out]


def polyhedron(gammas):
    """gammas: {family: gamma}. Returns list of (polygon vertices, family) faces."""
    planes = [(n, g, f) for f, g in gammas.items() for n in orbit(f)]
    hs = np.array([[*n, -g] for n, g, _ in planes])
    V = HalfspaceIntersection(hs, np.zeros(3)).intersections
    V = np.unique(np.round(V, 9), axis=0)
    faces = []
    for n, g, f in planes:
        on = V[np.abs(V @ n - g) < 1e-6 * max(1, g)]
        if len(on) < 3:
            continue
        c = on.mean(axis=0)
        u = on[0] - c
        u /= np.linalg.norm(u)
        w = np.cross(n, u)
        order = np.argsort(np.arctan2((on - c) @ w, (on - c) @ u))
        faces.append((on[order], f))
    scale = np.abs(V).max()
    return [(p / scale, f) for p, f in faces]


def draw(ax, gammas, title):
    for poly, fam in polyhedron(gammas):
        ax.add_collection3d(Poly3DCollection([poly], facecolor=COLOR[fam], edgecolor=INK,
                                             linewidth=0.6, alpha=0.95))
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=22, azim=35); ax.set_axis_off()
    ax.set_title(title, fontsize=10, color=INK)


def main(folder):
    folder = Path(folder)
    sm = pd.read_csv(folder / "wulff_summary.csv")
    se = pd.read_csv(folder / "surface_energies.csv")
    n = len(sm)
    fig = plt.figure(figsize=(12, 3.4 * n), facecolor="white")
    for i, r in sm.reset_index(drop=True).iterrows():
        mof = r["mof"]
        g = {row["face"]: row["gamma_J_m2"] for _, row in se[se["mof"] == mof].iterrows()}
        g = {f: v for f, v in g.items() if f in FAMILIES}
        frac = json.loads(r["area_fractions"]) if isinstance(r.get("area_fractions"), str) else {}
        pred = str(r.get("predicted_shape", "")).replace("_", " ")
        ax = fig.add_subplot(n, 3, 3 * i + 1, projection="3d")
        if len(g) >= 2:
            draw(ax, g, f"{mof}\npredicted: {pred}")
        else:
            ax.set_axis_off(); ax.set_title(f"{mof}\nnot enough faces", fontsize=10)
        ax2 = fig.add_subplot(n, 3, 3 * i + 2, projection="3d")
        lab = str(r.get("lab_shape", "")) if pd.notna(r.get("lab_shape")) else ""
        nrec = int(r["lab_n_records"]) if pd.notna(r.get("lab_n_records")) else 0
        if lab in IDEAL:
            draw(ax2, IDEAL[lab], f"lab: {lab.replace('_', ' ')}\n({nrec} records, no additive)")
        else:
            ax2.set_axis_off()
            ax2.set_title(f"lab: {lab or 'no lab data'}\n({nrec} records)", fontsize=10, color=INK)
        ax3 = fig.add_subplot(n, 3, 3 * i + 3)
        fams = [f for f in FAMILIES if f in g]
        vals = [g[f] for f in fams]
        bars = ax3.bar(fams, vals, color=[COLOR[f] for f in fams], width=0.55,
                       edgecolor="white", linewidth=2)
        for b, f, v in zip(bars, fams, vals):
            ax3.text(b.get_x() + b.get_width() / 2, v, f"{v:.3f}\n{frac.get(f, 0) * 100:.0f}% of surface",
                     ha="center", va="bottom", fontsize=8, color=INK)
        ax3.set_ylabel("surface energy γ (J/m²)", fontsize=9, color=INK)
        ax3.set_ylim(0, max(vals) * 1.45 if vals else 1)
        ax3.spines[["top", "right"]].set_visible(False)
        ax3.tick_params(colors=MUTED, labelsize=9)
        match = "match" if r.get("shape_match") is True or str(r.get("shape_match")) == "True" else \
            ("main face matches" if str(r.get("dominant_face_match")) == "True" else "no match")
        ax3.set_title(f"lowest γ grows biggest  ·  {match}", fontsize=9, color=INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[f]) for f in FAMILIES]
    fig.legend(handles, FAMILIES, loc="upper center", ncol=3, frameon=False, fontsize=10,
               title="face family", title_fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = folder / "shapes.png"
    fig.savefig(out, dpi=140)
    print("wrote", out)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
