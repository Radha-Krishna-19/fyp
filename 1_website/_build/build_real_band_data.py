#!/usr/bin/env python3
"""
build_real_band_data.py — writes 1_website/real_band_data.js from the
61-framework real-MOF run in 3_notebooks/real_results.json.

WHAT REPLACED WHAT
This supersedes build_real_band.js, which computed the same section from four
local CIFs (HKUST-1, UiO-66, MOF-5, ZIF-8) using the website's JavaScript
engine. That version is kept in this folder because the coordination-number
check it performs is still the clearest demonstration that the periodic graph
construction is correct — UiO-66 comes out at 12 with periodicity and 1 without.
What it can no longer support is the BAND claim, for the reason recorded in
make_real_band_figures.py: its four structures were 256-972 atoms while the 77
hMOFs are 3024-6592, so the comparison measured graph size, not chemistry.

The 61 structures here come from the analysis notebook, are size-matched by
construction, and are computed by the Python pipeline — the same code that
produced the 77-framework result they are compared against. Same code on both
sides of a comparison is the point; two implementations would leave any
difference ambiguous between chemistry and implementation.

All statistics are computed HERE, in Python, and written into the file as
numbers. The page does not recompute them in JavaScript, so there is exactly one
place where a statistic can be wrong, and it is version-controlled.

Run:  python _build/build_real_band_data.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(SITE, ".."))

REAL = os.path.join(ROOT, "3_notebooks", "real_results.json")
HMOF = os.path.join(ROOT, "3_notebooks", "results.json")
OUT = os.path.join(SITE, "real_band_data.js")

# Curves are decimated before they are written: the spectra are smooth, the
# chart is a few hundred pixels wide, and shipping all 41 q-points for 61
# structures triples the file for detail no reader can see.
Q_STRIDE = 2


def partial_corr(x, y, z):
    """Correlation of x and y with z held constant."""
    rxy, rxz, ryz = (np.corrcoef(x, y)[0, 1], np.corrcoef(x, z)[0, 1],
                     np.corrcoef(y, z)[0, 1])
    return (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def main():
    real = json.load(open(REAL))
    hmof = json.load(open(HMOF))

    wr = np.array([real[k]["width"] for k in real])
    wh = np.array([hmof[k]["width"] for k in hmof])
    Nr = np.array([real[k]["N"] for k in real], dtype=float)
    Nh = np.array([hmof[k]["N"] for k in hmof], dtype=float)
    lcd = np.array([real[k]["lcd"] for k in real], dtype=float)
    ar = np.array([real[k]["asymmetry"] for k in real])
    ah = np.array([hmof[k]["asymmetry"] for k in hmof])

    records = {}
    for name, r in sorted(real.items(), key=lambda kv: -kv[1]["width"]):
        q = np.array(r["q"])
        keep = list(range(0, len(q), Q_STRIDE))
        if keep[-1] != len(q) - 1:
            keep.append(len(q) - 1)
        records[name] = {
            "width": round(r["width"], 4),
            "width_sd": round(r["width_sd"], 4),
            "asymmetry": round(r["asymmetry"], 3),
            "asymmetry_sd": round(r["asymmetry_sd"], 3),
            "N": r["N"],
            "diameter": r["diameter"],
            "n_nodes": r["n_nodes"],
            "n_linkers": r["n_linkers"],
            "n_influential": r["n_influential"],
            "lcd": round(r["lcd"], 3) if r.get("lcd") is not None else None,
            "pld": round(r["pld"], 3) if r.get("pld") is not None else None,
            "rep": r.get("rep"),
            "database": r.get("database", "CoREMOF 2019"),
            "alpha": [round(float(r["alpha"][i]), 4) for i in keep],
            "f_alpha": [round(float(r["f_alpha"][i]), 4) for i in keep],
            "q": [round(float(q[i]), 2) for i in keep],
        }

    olo, ohi = float(max(wr.min(), wh.min())), float(min(wr.max(), wh.max()))
    stats_block = {
        "n": int(len(wr)),
        "n_hmof": int(len(wh)),
        "source": "CoRE MOF 2019 (Zenodo 10.5281/zenodo.3370236), Xe-tested subset",
        "w_min": round(float(wr.min()), 4),
        "w_max": round(float(wr.max()), 4),
        "w_mean": round(float(wr.mean()), 4),
        "w_sd": round(float(wr.std(ddof=1)), 4),
        "w_median": round(float(np.median(wr)), 4),
        "w_q1": round(float(np.percentile(wr, 25)), 4),
        "w_q3": round(float(np.percentile(wr, 75)), 4),
        "h_min": round(float(wh.min()), 4),
        "h_max": round(float(wh.max()), 4),
        "h_mean": round(float(wh.mean()), 4),
        "h_sd": round(float(wh.std(ddof=1)), 4),
        "h_median": round(float(np.median(wh)), 4),
        "overlap_lo": round(olo, 4),
        "overlap_hi": round(ohi, 4),
        "overlap_frac_real": round(float(((wr >= olo) & (wr <= ohi)).mean()), 4),
        "overlap_frac_hmof": round(float(((wh >= olo) & (wh <= ohi)).mean()), 4),
        "mean_diff": round(float(wr.mean() - wh.mean()), 4),
        "asym_real": round(float(ar.mean()), 3),
        "asym_hmof": round(float(ah.mean()), 3),
        "N_min": int(Nr.min()), "N_max": int(Nr.max()),
        "N_median": int(np.median(Nr)),
        "hN_min": int(Nh.min()), "hN_max": int(Nh.max()),
        "n_size_matched": int(((Nr >= Nh.min())).sum()),
        "r_width_atoms_real": round(float(np.corrcoef(wr, Nr)[0, 1]), 3),
        "r_width_atoms_hmof": round(float(np.corrcoef(wh, Nh)[0, 1]), 3),
        "r_width_lcd_real": round(float(np.corrcoef(wr, lcd)[0, 1]), 3),
        "r_width_lcd_given_size": round(float(partial_corr(wr, lcd, Nr)), 3),
    }

    try:
        from scipy import stats as st
        stats_block["p_welch"] = round(float(st.ttest_ind(wr, wh, equal_var=False).pvalue), 4)
        stats_block["p_mannwhitney"] = round(float(st.mannwhitneyu(wr, wh).pvalue), 4)
        stats_block["p_levene"] = round(float(st.levene(wr, wh).pvalue), 4)
        pooled = np.sqrt(((len(wr) - 1) * wr.var(ddof=1) + (len(wh) - 1) * wh.var(ddof=1))
                         / (len(wr) + len(wh) - 2))
        stats_block["cohens_d"] = round(float((wr.mean() - wh.mean()) / pooled), 3)
        lo, hi = st.t.interval(0.95, len(wr) + len(wh) - 2,
                               loc=wr.mean() - wh.mean(),
                               scale=pooled * np.sqrt(1 / len(wr) + 1 / len(wh)))
        stats_block["ci95_lo"] = round(float(lo), 4)
        stats_block["ci95_hi"] = round(float(hi), 4)
    except ImportError:
        raise SystemExit("scipy is required: the page states p-values, so they must be computed.")

    header = f"""// real_band_data.js — GENERATED by _build/build_real_band_data.py. Do not edit by hand.
//
// The multifractal descriptor for {len(wr)} experimentally SYNTHESISED frameworks,
// drawn from CoRE MOF 2019 and computed by the same Python pipeline that
// produced the {len(wh)}-framework hypothetical result they are compared against.
//
// Supersedes the earlier four-structure version. Those four were 256-972 atoms
// against the hMOFs' {int(Nh.min())}-{int(Nh.max())}, so their apparent separation from the
// hMOF band was a graph-size artefact; see 4_reference/make_real_band_figures.py.
//
// Headline: the two sets share a band. Means differ by {stats_block['mean_diff']:+.3f}
// (Welch p = {stats_block['p_welch']:.2f}); the synthesised set is significantly MORE
// variable (Levene p = {stats_block['p_levene']:.3f}).
"""

    with open(OUT, "w") as f:
        f.write(header)
        f.write("window.REAL_BAND_STATS = " + json.dumps(stats_block, indent=1) + ";\n\n")
        f.write("window.REAL_BAND_DATA = " + json.dumps(records, indent=1) + ";\n")

    print(f"wrote {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB, {len(records)} structures)")
    print(f"  real  Δα {stats_block['w_min']:.2f}-{stats_block['w_max']:.2f}  "
          f"mean {stats_block['w_mean']:.3f} ± {stats_block['w_sd']:.3f}")
    print(f"  hMOF  Δα {stats_block['h_min']:.2f}-{stats_block['h_max']:.2f}  "
          f"mean {stats_block['h_mean']:.3f} ± {stats_block['h_sd']:.3f}")
    print(f"  overlap {stats_block['overlap_lo']:.2f}-{stats_block['overlap_hi']:.2f}, "
          f"Welch p={stats_block['p_welch']:.2f}, Levene p={stats_block['p_levene']:.3f}")


if __name__ == "__main__":
    main()
