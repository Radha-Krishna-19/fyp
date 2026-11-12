"""Figures for the morphology map. fig_map.png: map + model points per MOF;
fig_conditions.png: condition series on the two axes and the graph read-out r_half/D."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
S2, S3 = 2 ** 0.5, 3 ** 0.5
g = np.load(_os.path.join(HERE, "phase_grid.npz"), allow_pickle=True); xs, ys, lab, classes = g["xs"], g["ys"], g["lab"], list(g["classes"])
TINT = {"cube": "#c9dcf5", "truncated_cube": "#e1ecfa", "cuboctahedron": "#eeeeee", "truncated_octahedron": "#fbe3d8",
        "octahedron": "#f6c7b3", "cube_truncated_edges": "#d9eee8", "truncated_rhombic_dodecahedron": "#e4f5ee",
        "rhombic_dodecahedron": "#bfe8d8", "rd_truncated_by_111": "#efe8d0", "octahedron_truncated_by_110": "#f3e4cf",
        "all_three_families": "#f4f3ef"}
SHORT = {"cube": "cube", "truncated_cube": "truncated\ncube", "truncated_octahedron": "truncated\noctahedron",
         "octahedron": "octahedron", "cube_truncated_edges": "cube,\ntrunc.\nedges",
         "truncated_rhombic_dodecahedron": "truncated rhombic\ndodecahedron", "rhombic_dodecahedron": "rhombic\ndodecahedron",
         "all_three_families": "all three\nfamilies"}
cmap = ListedColormap([TINT[c] for c in classes])
INK, INK2 = "#0b0b0b", "#52514e"
MODELS = ["BFDH", "Attachment energy", "Broken-bond Wulff", "UFF Wulff", "CHGNet cleavage (Oct)",
          "Steps 1-8 CHGNet, static", "Steps 1-8 CHGNet, relaxed"]
COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#e34948"]
MK = ["o", "s", "^", "D", "v", "P", "*"]
LAB = {"MOF-5": "cube", "HKUST-1": "octahedron", "UiO-66": "cube (poorly faceted)", "ZIF-8": "rhombic dodecahedron"}

def base(ax, labels=True):
    ax.pcolormesh(xs, ys, lab, cmap=cmap, vmin=-0.5, vmax=len(classes) - 0.5, shading="nearest", rasterized=True)
    ax.set_xscale("log"); ax.set_yscale("log")
    kw = dict(color=INK2, lw=0.8, ls="--")
    ax.plot([S2, 3.2], [S3, S3], **kw); ax.plot([S2, S2], [S3, 2.2], **kw)
    ax.axhline(2 / S3, xmin=0, xmax=1, color=INK2, lw=0.6, ls=":")
    ax.plot([0.4, 1 / S2], [0.4 * 1.5 ** 0.5, 1 / S2 * 1.5 ** 0.5], **kw); ax.plot([1 / S2, 1 / S2], [1 / S2 * 1.5 ** 0.5, 2.2], **kw)
    ax.plot([1.5 ** 0.5 / S3, 3.2], [1 / S3, 1 / S3], **kw)
    ax.set_xlim(0.4, 3.2); ax.set_ylim(0.4, 2.2)
    ticks = [0.5, 0.707, 1, 1.414, 2, 3]; ax.set_xticks(ticks); ax.set_xticklabels(["0.5", "1/√2", "1", "√2", "2", "3"])
    yt = [0.5, 0.577, 0.866, 1.155, 1.732]; ax.set_yticks(yt); ax.set_yticklabels(["0.5", "1/√3", "0.87", "2/√3", "√3"])
    ax.minorticks_off()
    ax.set_xlabel("γ{110} / γ{100}", color=INK2); ax.set_ylabel("γ{111} / γ{100}", color=INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    for s in ax.spines.values(): s.set_color("#c3c2b7")
    if labels:
        for c, (x, y) in {"cube": (2.3, 1.95), "truncated_cube": (2.3, 1.42), "truncated_octahedron": (2.3, 0.80),
                          "octahedron": (1.6, 0.46), "rhombic_dodecahedron": (0.5, 1.6), "truncated_rhombic_dodecahedron": (0.88, 1.95), "cube_truncated_edges": (1.22, 1.5),
                          "all_three_families": (1.05, 1.08)}.items():
            ax.text(x, y, SHORT[c], ha="center", va="center", fontsize=7, color=INK2)

# figure 1: the map on its own
fig, ax = plt.subplots(figsize=(6.4, 5.2)); base(ax)
ax.text(2.6, 2 / S3 * 1.03, "cuboctahedron: y = 2/√3", fontsize=7, color=INK2, ha="center")
ax.set_title("Cubic morphology map: every shape is a region of (γ110/γ100, γ111/γ100)", fontsize=10, color=INK)
fig.tight_layout(); fig.savefig(_os.path.join(HERE, "fig_map_regions.png"), dpi=200); plt.close(fig)

# figure 2: model points per MOF
P = json.load(open(_os.path.join(HERE, "model_points.json")))
fig, axs = plt.subplots(2, 2, figsize=(11, 9))
for ax, m in zip(axs.flat, ["MOF-5", "HKUST-1", "UiO-66", "ZIF-8"]):
    base(ax, labels=True)
    for i, name in enumerate(MODELS):
        if name in P[m]:
            p = P[m][name]
            ax.scatter([min(p["x"], 3.1)], [min(p["y"], 2.15)], s=70 if MK[i] != "*" else 150, marker=MK[i], color=COL[i],
                       edgecolor="white", linewidth=1.2, zorder=5, label=name)
    ax.set_title(f"{m}   (lab, no additive: {LAB[m]})", fontsize=10, color=INK)
h, l = axs.flat[0].get_legend_handles_labels()
hh, ll = [], []
for a in axs.flat:
    for hi, li in zip(*a.get_legend_handles_labels()):
        if li not in ll: hh.append(hi); ll.append(li)
fig.legend(hh, ll, loc="lower center", ncol=4, frameon=False, fontsize=9)
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(_os.path.join(HERE, "fig_map_models.png"), dpi=200); plt.close(fig)

# figure 3: condition series and the graph read-out along the two axes
S = json.load(open(_os.path.join(HERE, "series_results.json")))["series"]; D = json.load(open(_os.path.join(HERE, "dimension_along_map.json")))
A111 = ["cube", "truncated_cube", "cuboctahedron", "truncated_octahedron", "octahedron"]
A110 = ["cube", "cube_truncated_edges", "truncated_rhombic_dodecahedron", "rhombic_dodecahedron"]
fig, axs = plt.subplots(2, 2, figsize=(12, 7.2), gridspec_kw=dict(width_ratios=[1.35, 1]))
for row, (axis, order) in enumerate([("{100}-{111}", A111), ("{100}-{110}", A110)]):
    ax = axs[row, 0]; k = 0
    for s in S:
        if s["axis"] != axis: continue
        pos = [order.index(x) for x in s["shapes"] if x in order]
        ax.plot(pos, [k] * len(pos), color="#2a78d6", lw=2, zorder=2)
        ax.scatter(pos, [k] * len(pos), s=60, color="#2a78d6", edgecolor="white", lw=1.5, zorder=3)
        prev = [p for p in pos if p != pos[-1]]
        ax.annotate("", xy=(pos[-1], k), xytext=(prev[-1] if prev else pos[-1], k),
                    arrowprops=dict(arrowstyle="-|>", color="#2a78d6", lw=2))
        ax.text(-0.25, k, f"{s['series']}\n{s['condition']}", ha="right", va="center", fontsize=7.5, color=INK)
        if s["leaves_map_at"]: ax.text(pos[-1] + 0.12, k, f"then {s['leaves_map_at']}", fontsize=7, color=INK2, va="center")
        k += 1
    ax.set_xticks(range(len(order))); ax.set_xticklabels([o.replace("_", "\n") for o in order], fontsize=8, color=INK2)
    ax.set_yticks([]); ax.set_ylim(-0.7, k - 0.3); ax.set_xlim(-0.3, len(order) - 0.4)
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    ax.set_title(f"Lab series along the {axis} axis (dose increases left to right on each line)", fontsize=9.5, color=INK)
    ax2 = axs[row, 1]; pts = D[axis]["points"]
    r = [p["ratio"] for p in pts]; v = [p["r_half_over_D"] for p in pts]; sd = [p["sd"] for p in pts]
    ax2.errorbar(r, v, yerr=sd, color="#eb6834", marker="o", ms=6, lw=2, capsize=3)
    for p in pts: ax2.annotate(p["shape"].replace("_", " "), (p["ratio"], p["r_half_over_D"]), textcoords="offset points",
                               xytext=(4, 6), fontsize=6.5, color=INK2, rotation=20)
    ax2.set_xlabel("γ111/γ100" if axis == "{100}-{111}" else "γ110/γ100", color=INK2)
    ax2.set_ylabel("r½ / D of a 4000-block MOF-5 crystal", color=INK2)
    ax2.set_title("Graph read-out (dimension profile) along the same axis", fontsize=9.5, color=INK)
    ax2.grid(color="#eeeeee"); ax2.tick_params(colors=INK2, labelsize=8)
    for sp in ("top", "right"): ax2.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(_os.path.join(HERE, "fig_conditions.png"), dpi=200); plt.close(fig)
print("figures written")
