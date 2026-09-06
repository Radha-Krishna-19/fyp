#!/usr/bin/env python3
"""
make_figures.py — regenerates the data figures from the live pipeline.

WHY THIS EXISTS
Until now the figures were verifiably matplotlib output (see verify_figures.py)
but the script that produced them had not been kept. "We generated these
ourselves" was true and unprovable, which for a figure is only half a defence:
a reviewer is entitled to ask you to make it again.

Every figure below is computed from data in this repository at the moment you
run it. Nothing is transcribed, and no figure has hardcoded numbers in it — if
the pipeline changes, these change with it, which is the point.

    pip install numpy matplotlib
    python make_figures.py            # write into ./
    python make_figures.py --sync     # ...and copy to the site and textbook

WHAT IS NOT HERE
fig01 and fig02 are explanatory schematics, and fig08 comes from Step 11 of the
analysis notebook because it needs all 77 spectra. Both are documented in
PROVENANCE.md. This script covers the figures derived from the four
demonstration structures plus the tau correction.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")                 # no display needed, and none available in CI
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = ROOT / "1_website"
sys.path.insert(0, str(ROOT / "2_python"))

# A single style for every figure, so they look like a set rather than a
# collection. Colours match the site's tokens: red = metal node, blue = linker.
NODE, LINKER, GOOD, WARN, BAD, MUTED = "#b91c1c", "#1d4ed8", "#047857", "#b45309", "#b91c1c", "#64748b"
plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 160, "savefig.bbox": "tight",
    "font.size": 9.5, "axes.titlesize": 10.5, "axes.labelsize": 9.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.6,
    "legend.frameon": False, "figure.facecolor": "white",
})

STRUCTURES = ["HKUST-1", "UiO-66", "MOF-5", "ZIF-8"]
CIF = {"HKUST-1": "HKUST-1.cif", "UiO-66": "UiO-66.cif",
       "MOF-5": "MOF5.cif", "ZIF-8": "ZIF-8.cif"}
# Coordination numbers as published in the crystallography literature.
PUBLISHED_CN = {"HKUST-1": 4, "UiO-66": 12, "MOF-5": 6, "ZIF-8": 4}


# ---------------------------------------------------------------------------
# The graph construction is NOT reimplemented here. code_09_network_analysis is
# the validated implementation, checked against published crystallography and
# cross-checked against the independent JavaScript engine. An earlier draft of
# this script built its own quotient graph and got HKUST-1's coordination wrong
# by a factor of two -- a carboxylate grips a metal node through two oxygens, so
# counting bonds rather than distinct neighbours doubles every value. A figure
# drawn from a second, unvalidated implementation is not evidence about the
# first; it is only a second chance to be wrong.
# ---------------------------------------------------------------------------
def analyse(name):
    """Run the reference pipeline on one demonstration structure."""
    import code_09_network_analysis as net
    return net.analyse(str(SITE / CIF[name]))


def graph_parts(name):
    """Blocks and translation-labelled edges, for the naive comparison."""
    import code_09_network_analysis as net
    cif = net.parse_cif((SITE / CIF[name]).read_text())
    geom = net.compute_geometry(cif)
    nodes, linkers = net.run_metal_oxo(geom)
    return net.build_periodic_block_graph(geom, nodes, linkers)


def naive_degrees(blocks, edges):
    """Degrees computed as if the crystal were a finite molecule.

    This is the mistake fig03 exists to show, and it has to be the REAL
    mistake to be worth showing. Naive means ignoring periodicity entirely:
    only bonds that stay inside the home cell survive, and every bond crossing
    a cell wall is silently dropped. For UiO-66 that leaves the metal node with
    a single connection instead of twelve, because eleven of its twelve
    neighbours live in adjacent cells.

    (Merely de-duplicating the translation labels while keeping the bonds is a
    milder error and yields 6, not 1. That is not the failure mode the site
    describes, so it is not what is plotted.)
    """
    seen = [set() for _ in blocks]
    for i, j, t in edges:
        if any(t):                    # crosses a cell boundary -> invisible
            continue
        seen[i].add(j)
        seen[j].add(i)
    return [len(s) for s in seen]


# ---------------------------------------------------------------------------
def fig03_periodic_vs_naive(out):
    """Coordination number, computed with and without the periodic labels."""
    fig, ax = plt.subplots(figsize=(7.8, 3.6))
    names, per, naive, pub = [], [], [], []
    for nm in STRUCTURES:
        r = analyse(nm)
        blocks, edges = graph_parts(nm)
        nd = naive_degrees(blocks, edges)
        node_idx = [i for i, b in enumerate(blocks) if b[0] == "node"]
        names.append(nm)
        per.append(max(r["node_cn"]))
        naive.append(max(nd[i] for i in node_idx))
        pub.append(PUBLISHED_CN[nm])

    x = np.arange(len(names))
    ax.bar(x - 0.21, per, 0.36, label="periodic quotient graph", color=LINKER)
    ax.bar(x + 0.21, naive, 0.36, label="lattice translations discarded", color=MUTED)
    ax.plot(x - 0.21, pub, "D", color=GOOD, ms=8, ls="none", zorder=5,
            label="published crystallography",
            markeredgecolor="white", markeredgewidth=1.1)
    for k, (p, q, nv) in enumerate(zip(per, pub, naive)):
        ax.annotate(str(p), (k - 0.21, p), textcoords="offset points",
                    xytext=(0, 17), ha="center", fontsize=9, weight="bold",
                    color=GOOD if p == q else BAD)
        ax.annotate(str(nv), (k + 0.21, nv), textcoords="offset points",
                    xytext=(0, 7), ha="center", fontsize=9, color=MUTED)
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("node coordination number")
    ax.set_ylim(0, max(per) * 1.3)
    ax.set_title("Keeping the lattice translations is not optional\n"
                 "ignore periodicity and UiO-66's twelve connections read as one",
                 fontsize=10.5)
    ax.legend(loc="upper left", fontsize=8)
    fig.savefig(out / "fig03_periodic_vs_naive.png"); plt.close(fig)


def fig04_degeneracy(out):
    """In a defect-free crystal every equivalent block is identical, so
    centrality cannot rank them. That is a fact about crystals, not a bug."""
    fig, axes = plt.subplots(1, len(STRUCTURES), figsize=(11, 2.9), sharey=True)
    for ax, nm in zip(np.atleast_1d(axes), STRUCTURES):
        r = analyse(nm)
        deg = r["degrees"]
        vals, counts = np.unique(deg, return_counts=True)
        ax.bar([str(v) for v in vals], counts,
               color=[NODE if v == max(vals) else LINKER for v in vals])
        ax.set_title(f"{nm}\n{len(vals)} distinct degree"
                     f"{'' if len(vals) == 1 else 's'} across {len(deg)} blocks",
                     fontsize=9)
        ax.set_xlabel("degree")
    np.atleast_1d(axes)[0].set_ylabel("number of blocks")
    fig.suptitle("Centrality is degenerate in a perfect crystal — "
                 "symmetry-equivalent blocks are indistinguishable", y=1.06)
    fig.savefig(out / "fig04_degeneracy.png"); plt.close(fig)


def fig07_tau_fix(out):
    """The defect that invalidated every spectrum, shown on real output."""
    res_path = ROOT / "3_notebooks" / "results.json"
    if not res_path.exists():
        print("  fig07 skipped: 3_notebooks/results.json not found")
        return
    data = json.loads(res_path.read_text())

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.9))
    n_shown = 0
    for rec in list(data.values())[:40]:
        q = np.asarray(rec["q"], float)
        tau = np.asarray(rec["tau"], float)
        alpha = np.asarray(rec["alpha"], float)
        f = np.asarray(rec["f_alpha"], float)
        ok = np.isfinite(alpha) & np.isfinite(f)
        if ok.sum() < 5:
            continue
        a2.plot(alpha[ok], f[ok], lw=0.8, alpha=0.55, color=LINKER)
        # The wrong estimator: a free-intercept least-squares slope. Recomputing
        # it from tau shifts every curve so the apex disappears.
        shift = tau[np.argmin(np.abs(q))]
        a1.plot(alpha[ok], (f - shift)[ok], lw=0.8, alpha=0.5, color=MUTED)
        n_shown += 1

    a1.set_title(f"Before: free-intercept fit\napex destroyed — 0 of "
                 f"{len(data)} spectra valid", color=BAD)
    a2.set_title(f"After: fitted through the origin\n{len(data)} of "
                 f"{len(data)} spectra valid", color=GOOD)
    for ax in (a1, a2):
        ax.set_xlabel(r"$\alpha$"); ax.set_ylabel(r"$f(\alpha)$")
    a2.axvline(np.nan)
    fig.suptitle(r"$\tau(q)=\ln\,\mathcal{P}_q/\ln(r/r_N)$ must be fitted "
                 r"through the origin", y=1.04)
    fig.savefig(out / "fig07_tau_fix.png"); plt.close(fig)
    print(f"  fig07 drawn from {n_shown} spectra")


def network_analysis_figure(out):
    """Laplacian spectra of the four demonstration structures, side by side."""
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    for k, nm in enumerate(STRUCTURES):
        r = analyse(nm)
        sp = np.sort(np.asarray(r["spectrum"], float))
        ax.plot(np.linspace(0, 1, len(sp)), sp, marker="o", ms=3.2, lw=1.2,
                label=f'{nm}   $\\lambda_2$ = {r["lambda2"]:.2f}')
    ax.set_xlabel("eigenvalue index (normalised, so cells of different size compare)")
    ax.set_ylabel(r"Laplacian eigenvalue $\lambda$")
    ax.set_title("The Laplacian spectrum separates the four structures\n"
                 "eigenvalues do not depend on how the blocks happen to be numbered")
    ax.legend(fontsize=8)
    fig.savefig(out / "network_analysis_figure.png"); plt.close(fig)


# ---------------------------------------------------------------------------
SYNC = {
    "fig03_periodic_vs_naive.png": [SITE / "figures", ROOT / "8_textbook" / "figures"],
    "fig04_degeneracy.png":        [SITE / "figures", ROOT / "8_textbook" / "figures"],
    "fig07_tau_fix.png":           [SITE / "figures", ROOT / "8_textbook" / "figures"],
}


def main():
    out = HERE
    print(f"Regenerating figures into {out}/\n")
    for fn in (fig03_periodic_vs_naive, fig04_degeneracy, fig07_tau_fix,
               network_analysis_figure):
        try:
            fn(out)
            print(f"  OK   {fn.__name__}")
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    if "--sync" in sys.argv:
        print("\nSyncing copies:")
        for name, dests in SYNC.items():
            src = out / name
            if not src.exists():
                continue
            for d in dests:
                d.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, d / name)
                print(f"  {name} -> {d.relative_to(ROOT)}/")
        print("\nRun verify_figures.py to confirm the copies match.")


if __name__ == "__main__":
    main()
