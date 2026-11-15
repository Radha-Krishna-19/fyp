"""Sweep the water chemical potential and record, per MOF, the main face and the shape name, plus figures.

Run:  python water_mu_sweep.py <water_mu.csv from water_mu_analysis.py> <static run dir> <out dir>
Writes water_mu_sweep.json, fig_gamma_vs_mu_<MOF>.png for the MOFs with a negative slab, and
fig_main_face_vs_mu.png (one row per MOF, colour = main face, cross = no shape because some gamma <= 0).
"""
import json, sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mofgnn as G
import water_mu_analysis as W

csv, static_dir, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
df = pd.read_csv(csv, dtype={"family": str})
rel = df[df["nb_gamma_relaxed"].notna() & (df["nb_converged"] == True)].copy()
GRID = np.round(np.arange(-1.0, 0.1001, 0.025), 3)
res = dict(script="water_mu_sweep.py", grid_eV=GRID.tolist(), conditions_dmu_eV=W.CONDITIONS, mofs={})

for mof, g in rel.groupby("mof", sort=False):
    meta = G.load_meta(static_dir, mof)
    rows = []
    for mu in GRID:
        gam = (g["nb_gamma_relaxed"] - g["slope_J_m2_per_eV"] * mu).to_numpy()
        best = {}
        for (fam, face, t), v in zip(g[["family", "face", "termination"]].itertuples(index=False), gam):
            if fam not in best or v < best[fam][0]:
                best[fam] = (v, face, int(t))
        habit, dom, w = G.habit_from_gammas(meta, {k: v[0] for k, v in best.items()})
        rows.append(dict(dmu=float(mu), habit=habit, main_face=dom, min_gamma=float(min(v[0] for v in best.values())),
                         face_order=[v[1] for v in sorted(best.values())]))
    ok = [r for r in rows if r["main_face"]]
    res["mofs"][mof] = dict(sweep=rows,
                            no_shape_from_dmu=min([r["dmu"] for r in rows if r["min_gamma"] <= 0], default=None),
                            main_faces_seen=sorted({r["main_face"] for r in ok}),
                            n_families=int(g["family"].nunique()))
json.dump(res, open(f"{out}/water_mu_sweep.json", "w"), indent=1, default=float)

# ---- figure 1: main face against dmu, one row per MOF
mofs = list(res["mofs"])
faces = sorted({f for m in mofs for f in res["mofs"][m]["main_faces_seen"]})
PAL = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000", "#999999",
       "#7F3C8D", "#11A579", "#3969AC"]
col = {f: PAL[i % len(PAL)] for i, f in enumerate(faces)}
TAG = {c: "ABCDE"[i] for i, c in enumerate(W.CONDITIONS)}
fig, ax = plt.subplots(figsize=(9, 0.42 * len(mofs) + 1.6))
for y, m in enumerate(mofs):
    for r in res["mofs"][m]["sweep"]:
        if r["main_face"]:
            ax.add_patch(plt.Rectangle((r["dmu"] - 0.0125, y - 0.4), 0.025, 0.8, color=col[r["main_face"]], lw=0))
        else:
            ax.plot(r["dmu"], y, "x", color="k", ms=4)
for name, mu in W.CONDITIONS.items():
    ax.axvline(mu, color="0.35", lw=0.8, ls="--")
    ax.text(mu, len(mofs) - 0.25, TAG[name], fontsize=8, ha="center", va="bottom", fontweight="bold")
ax.set_yticks(range(len(mofs))); ax.set_yticklabels(mofs, fontsize=8)
ax.set_xlim(GRID[0] - 0.02, GRID[-1] + 0.02); ax.set_ylim(-0.6, len(mofs) + 0.4)
ax.set_xlabel("Δμ of water relative to a free molecule at 0 K (eV per molecule)")
ax.set_title("Main face of the Wulff shape against the water reference (× = no shape: some γ ≤ 0)", fontsize=9)
handles = [plt.Rectangle((0, 0), 1, 1, color=col[f]) for f in faces]
ax.legend(handles, faces, fontsize=7, ncol=min(9, len(faces)), loc="upper left", bbox_to_anchor=(0, -0.10), frameon=False,
          title="main face", title_fontsize=7)
fig.text(0.01, 0.005, "  ".join(f"{TAG[c]}: {c} ({v:+.3f} eV)" for c, v in W.CONDITIONS.items()), fontsize=6.5)
fig.tight_layout(); fig.savefig(f"{out}/fig_main_face_vs_mu.png", dpi=150); plt.close(fig)

# ---- figure 2: gamma against dmu for each MOF that has a negative slab at dmu = 0
for m in [m for m in mofs if res["mofs"][m]["no_shape_from_dmu"] is not None]:
    g = rel[rel["mof"] == m]
    fig, ax = plt.subplots(figsize=(6, 4))
    mu = np.linspace(-1.0, 0.1, 50)
    for (face), gg in g.groupby("face"):
        env = np.min([r.nb_gamma_relaxed - r.slope_J_m2_per_eV * mu for r in gg.itertuples()], axis=0)
        ax.plot(mu, env, label=face, lw=1.8)
    ax.axhline(0, color="k", lw=0.8)
    for i, (name, v) in enumerate(W.CONDITIONS.items()):
        ax.axvline(v, color="0.5", lw=0.7, ls="--")
        ax.text(v, ax.get_ylim()[1], "ABCDE"[i], fontsize=8, ha="center", va="bottom", fontweight="bold")
    ax.set_xlabel("Δμ of water (eV per molecule)"); ax.set_ylabel("γ, lowest termination (J/m²)")
    ax.set_title(f"{m}: surface energy of each face against the water reference", fontsize=9, pad=16)
    ax.legend(fontsize=8, title="face", title_fontsize=8)
    fig.text(0.01, 0.005, "A 0 K molecule (notebook)  B vapour 298 K 1 bar  C liquid water 298 K  D vapour 298 K 50 % RH  E vapour 400 K 1 bar", fontsize=6)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(f"{out}/fig_gamma_vs_mu_{m}.png", dpi=150); plt.close(fig)
print("wrote", out, {m: (v["no_shape_from_dmu"], v["main_faces_seen"]) for m, v in res["mofs"].items()})
