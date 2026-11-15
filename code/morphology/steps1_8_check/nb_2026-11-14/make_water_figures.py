"""Schematic figures for the page on machine-learned surface energies and water (no data; drawings).

Run:  python make_water_figures.py <out dir>
  fig_capping_schematic.png : a cut metal-ligand bond, the water cap, and the two-proton problem (K12)
  fig_water_price.png       : the water reference conditions on one axis, with what each one means
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
C = dict(M="#3B6FB6", O="#D1495B", C="#555555", H="#BBBBBB", bad="#B00020", good="#1B7F3B")


def atom(ax, x, y, el, r=None):
    r = r or {"M": 0.30, "O": 0.22, "C": 0.22, "H": 0.13}[el]
    ax.add_patch(Circle((x, y), r, color=C[el], zorder=3))
    ax.text(x, y, {"M": "M"}.get(el, el), ha="center", va="center", fontsize=8 if el != "H" else 6,
            color="white" if el in "MOC" else "black", zorder=4)


def bond(ax, a, b, style="-", color="k", lw=1.6):
    ax.plot([a[0], b[0]], [a[1], b[1]], style, color=color, lw=lw, zorder=2)


fig, axs = plt.subplots(1, 5, figsize=(16, 3.8))
titles = ["1. Inside the crystal", "2. Cut: one bond broken", "3. Water cap (the rule)",
          "4. Bridging O: old rule", "5. Bridging O: fixed rule (K12)"]
for ax, t in zip(axs, titles):
    ax.set_xlim(0, 4); ax.set_ylim(-0.2, 3.6); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t, fontsize=10)
for ax in axs[:3]:
    atom(ax, 3.2, 1.6, "C"); bond(ax, (2.2, 1.6), (3.2, 1.6)); atom(ax, 2.2, 1.6, "O")
bond(axs[0], (0.9, 1.6), (2.2, 1.6)); atom(axs[0], 0.9, 1.6, "M")
axs[0].text(2.0, 0.5, "metal – ligand O – linker", ha="center", fontsize=8)
atom(axs[1], 0.9, 1.6, "M")
axs[1].plot([1.55, 1.55], [0.7, 2.6], "--", color="0.4"); axs[1].text(1.55, 2.75, "cut", ha="center", fontsize=8)
axs[1].text(2.0, 0.4, "metal and O each lose a bond", ha="center", fontsize=8)
atom(axs[2], 0.5, 1.6, "M"); bond(axs[2], (0.5, 1.6), (1.3, 1.6)); atom(axs[2], 1.3, 1.6, "O")
bond(axs[2], (1.3, 1.6), (1.3, 2.25)); atom(axs[2], 1.3, 2.25, "H")
bond(axs[2], (2.2, 1.6), (2.2, 2.25)); atom(axs[2], 2.2, 2.25, "H")
axs[2].text(2.0, 0.35, "OH⁻ on the metal, H⁺ on the O:\none H₂O per broken bond", ha="center", fontsize=8)


def bridging(ax, fixed):
    atom(ax, 0.45, 2.75, "M"); atom(ax, 0.45, 0.45, "M")
    atom(ax, 2.3, 1.6, "O"); atom(ax, 3.3, 1.6, "C"); bond(ax, (2.3, 1.6), (3.3, 1.6))
    bond(ax, (0.45, 2.75), (1.25, 2.75)); atom(ax, 1.25, 2.75, "O"); bond(ax, (1.25, 2.75), (1.25, 3.4)); atom(ax, 1.25, 3.4, "H")
    bond(ax, (0.45, 0.45), (1.25, 0.45)); atom(ax, 1.25, 0.45, "O")
    if fixed:
        bond(ax, (1.25, 0.45), (1.6, 0.0)); atom(ax, 1.6, 0.0, "H")
        bond(ax, (1.25, 0.45), (0.9, 0.0)); atom(ax, 0.9, 0.0, "H")
        bond(ax, (2.3, 1.6), (2.3, 2.3), color=C["good"]); atom(ax, 2.3, 2.3, "H")
        ax.text(2.6, 0.55, "one H on the O;\nthe other cap is\nH₂O bound to the metal", fontsize=7.5, color=C["good"], ha="left")
    else:
        bond(ax, (1.25, 0.45), (1.25, -0.15)); atom(ax, 1.25, -0.15, "H")
        bond(ax, (2.3, 1.6), (2.05, 2.25), color=C["bad"]); atom(ax, 2.05, 2.25, "H")
        bond(ax, (2.3, 1.6), (2.05, 0.95), color=C["bad"]); atom(ax, 2.05, 0.95, "H")
        ax.text(2.6, 2.5, "O bonded to C\nand two H (C–OH₂⁺):\nnot a stable group", fontsize=7.5, color=C["bad"], ha="left")


bridging(axs[3], False); bridging(axs[4], True)
fig.tight_layout(); fig.savefig(f"{out}/fig_capping_schematic.png", dpi=150); plt.close(fig)

# water price axis
conds = [("A", "free molecule at 0 K\n(what the notebook used)", 0.0),
         ("B", "vapour, 25 °C, 1 bar", -0.4809), ("C", "liquid water, 25 °C", -0.5695),
         ("D", "air at 50 % humidity, 25 °C", -0.5874), ("E", "vapour, 127 °C, 1 bar", -0.6857)]
fig, ax = plt.subplots(figsize=(10, 2.6))
ax.axhline(0, color="k", lw=1)
for i, (tag, lab, v) in enumerate(conds):
    ax.plot(v, 0, "o", color="#0072B2", ms=8)
    dx, dy = {"A": (-0.05, 0.55), "B": (0.05, -0.6), "C": (-0.05, 0.55), "D": (-0.17, -0.6), "E": (-0.2, 0.55)}[tag]
    ax.annotate(f"{tag}: {lab}\nΔμ = {v:+.3f} eV", (v, 0), (v + dx, dy), fontsize=8,
                ha="center", va="center", arrowprops=dict(arrowstyle="-", color="0.5"))
ax.annotate("", xy=(-0.95, -1.1), xytext=(0.05, -1.1), arrowprops=dict(arrowstyle="->", color="0.3"))
ax.text(-0.45, -1.3, "to the left, water is harder to take from its surroundings, so water caps cost more and γ rises", ha="center", fontsize=8)
ax.set_xlim(-1.0, 0.15); ax.set_ylim(-1.45, 1.0); ax.set_yticks([])
ax.set_xlabel("Δμ of water relative to a free molecule at 0 K (eV per molecule)")
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(f"{out}/fig_water_price.png", dpi=150); plt.close(fig)
print("wrote", out)
