#!/usr/bin/env python3
"""
make_real_band_figures.py — the synthesised-vs-hypothetical comparison figure.

WHY THIS SCRIPT EXISTS
The analysis notebook emits a figure called `real_vs_hypothetical.png`, but it
can only draw the row it has data for. When the notebook is run on its own — as
it was for the 61-structure run — the 77-hMOF `results.json` is not in the Colab
session, so the figure comes out with the title "synthesised vs hypothetical"
and a single row. A comparison figure showing one of the two things being
compared is worse than no figure, because the title asserts a comparison the
picture does not contain.

This script draws it properly, from both files, on one shared axis.

WHAT THE COMPARISON IS FOR
Every quantitative result in this project before the real-MOF run was computed
on hMOF frameworks: chemically reasonable, computer-generated, never made in a
laboratory. The question a reviewer asks is whether the descriptor says anything
about materials or only about one generator's output. That question needs real
structures, enough of them to be a distribution rather than an anecdote, and
computed through the identical pipeline.

WHAT IT REPLACES
An earlier version of this comparison used four synthesised structures
(HKUST-1, UiO-66, MOF-5, ZIF-8) run through the website's JavaScript engine, and
reported that they sat clear of the hMOF band with no overlap. That claim is
withdrawn, and the reason is in panel (b): those four were expanded to 256-972
blocks, while the 77 hMOFs occupy 3024-6592. Not one of the 77 is as small as
the largest of the four. Since Delta-alpha rises with atom count (r = +0.73
across the 77), the two sets were never on comparable footing — the same
size confound the project already identified when it withdrew the pore-size
claim. The 61 real frameworks here are size-matched by construction: 59 of them
land inside or above the hMOF range.

Run:  python make_real_band_figures.py [--sync]
      --sync also copies the outputs into 1_website/figures/ and 8_textbook/figures/
"""
import json
import os
import shutil
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REAL = os.path.join(ROOT, "3_notebooks", "real_results.json")
HMOF = os.path.join(ROOT, "3_notebooks", "results.json")

SYNC = {
    "fig09_real_vs_hmof.png": [
        os.path.join(ROOT, "1_website", "figures"),
        os.path.join(ROOT, "8_textbook", "figures"),
    ],
}

# Colours chosen to match the site's brand/node inks rather than matplotlib's
# defaults, so the figure does not look foreign next to the canvas charts.
C_HMOF = "#3b6ea5"
C_REAL = "#b4413c"


def load():
    real = json.load(open(REAL))
    hmof = json.load(open(HMOF))
    return real, hmof


def widths(d):
    return np.array([d[k]["width"] for k in d])


def atoms(d):
    return np.array([d[k]["N"] for k in d])


def band_row(ax, y, vals, colour, label, sub):
    """A full-range whisker, an interquartile box, a median tick, one dot each.

    Deliberately not a violin or a KDE: with n = 61 and n = 77 a kernel density
    invents smoothness the data has not earned, and the reader cannot count the
    points. Every structure is drawn, so the reader can see the sample size.
    """
    s = np.sort(vals)
    q1, med, q3 = np.percentile(s, [25, 50, 75])
    ax.plot([s[0], s[-1]], [y, y], color=colour, lw=1.4, alpha=0.55, zorder=2)
    ax.add_patch(plt.Rectangle((q1, y - 0.17), q3 - q1, 0.34,
                               facecolor=colour, alpha=0.16,
                               edgecolor=colour, lw=1.2, zorder=3))
    ax.plot([med, med], [y - 0.17, y + 0.17], color=colour, lw=2.4, zorder=5)
    jitter = (np.random.RandomState(0).rand(len(s)) - 0.5) * 0.13
    ax.scatter(s, np.full(len(s), y) + jitter, s=13, color=colour,
               alpha=0.75, zorder=4, linewidths=0)
    ax.text(-0.012, y, label, transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=11.5, fontweight="600")
    ax.text(-0.012, y - 0.30, sub, transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=9.5, color="#666")
    return s[0], s[-1], med


def fig09(out):
    real, hmof = load()
    wr, wh = widths(real), widths(hmof)
    Nr, Nh = atoms(real), atoms(hmof)

    fig = plt.figure(figsize=(13.2, 6.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], width_ratios=[1.5, 1.0],
                          hspace=0.52, wspace=0.26)

    # ---- (a) the two bands on one axis ------------------------------------
    ax = fig.add_subplot(gs[0, :])
    hlo, hhi, hmed = band_row(ax, 1.0, wh, C_HMOF, "Hypothetical", f"{len(wh)} hMOF frameworks")
    rlo, rhi, rmed = band_row(ax, 0.0, wr, C_REAL, "Synthesised", f"{len(wr)} real CoRE MOFs")

    olo, ohi = max(rlo, hlo), min(rhi, hhi)
    ax.axvspan(olo, ohi, color="#7a9e7a", alpha=0.13, zorder=1)
    ax.text((olo + ohi) / 2, 1.62, f"ranges overlap  {olo:.2f}–{ohi:.2f}",
            ha="center", fontsize=10, color="#4a7a4a", fontweight="600")
    ax.set_ylim(-0.72, 1.78)
    ax.set_yticks([])
    ax.set_xlabel("Δα   (multifractal spectrum width)", fontsize=11)
    ax.set_title("(a) The synthesised frameworks land on the hypothetical band, not beside it",
                 fontsize=12, pad=10)
    ax.grid(axis="x", alpha=0.25)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    # ---- (b) why the earlier 4-structure comparison was not a comparison ---
    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(Nh, wh, s=15, color=C_HMOF, alpha=0.65, linewidths=0, label=f"hypothetical (n={len(wh)})")
    ax.scatter(Nr, wr, s=15, color=C_REAL, alpha=0.7, linewidths=0, label=f"synthesised (n={len(wr)})")
    old_N = np.array([378, 448, 256, 972])
    old_w = np.array([1.6602, 2.2593, 1.7003, 1.8043])
    ax.scatter(old_N, old_w, s=62, facecolor="none", edgecolor="#8a6d1f", lw=1.7,
               marker="D", label="withdrawn 4-structure set", zorder=6)
    ax.set_xlabel("atoms in supercell", fontsize=10)
    ax.set_ylabel("Δα", fontsize=10)
    ax.set_title("(b) the withdrawn set sat off the size range entirely", fontsize=11, pad=8)
    ax.legend(fontsize=8.2, loc="upper right", framealpha=0.9)
    ax.grid(alpha=0.25)

    # ---- (c) the numbers, stated rather than implied -----------------------
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    try:
        from scipy import stats
        p_t = stats.ttest_ind(wr, wh, equal_var=False).pvalue
        p_l = stats.levene(wr, wh).pvalue
        ptxt = (f"difference of means   {wr.mean() - wh.mean():+.3f}\n"
                f"Welch t-test          p = {p_t:.2f}   (centres agree)\n"
                f"Levene variance test  p = {p_l:.3f}  (spreads differ)")
    except ImportError:
        ptxt = f"difference of means   {wr.mean() - wh.mean():+.3f}"
    ax.text(0.0, 0.98,
            f"Synthesised (n={len(wr)})\n"
            f"   Δα   {wr.min():.2f} – {wr.max():.2f}\n"
            f"   mean {wr.mean():.3f} ± {wr.std(ddof=1):.3f}\n\n"
            f"Hypothetical (n={len(wh)})\n"
            f"   Δα   {wh.min():.2f} – {wh.max():.2f}\n"
            f"   mean {wh.mean():.3f} ± {wh.std(ddof=1):.3f}\n\n"
            f"{ptxt}",
            va="top", ha="left", fontsize=9.6, family="monospace", linespacing=1.55)
    ax.set_title("(c) same centre, wider spread", fontsize=11, pad=8, loc="left")

    fig.suptitle("Does the descriptor describe materials, or only one generator's output?",
                 fontsize=13.5, y=0.985)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def main():
    out = os.path.join(HERE, "fig09_real_vs_hmof.png")
    fig09(out)
    if "--sync" in sys.argv:
        for name, dests in SYNC.items():
            src = os.path.join(HERE, name)
            for d in dests:
                if os.path.isdir(d):
                    shutil.copy2(src, os.path.join(d, name))
                    print(f"  synced -> {os.path.join(d, name)}")


if __name__ == "__main__":
    main()
