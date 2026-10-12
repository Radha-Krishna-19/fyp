import os, json, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = json.load(open(os.path.join(HERE, "results", "deform_results.json")))
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
col = {"MOF-5": "#4C78A8", "HKUST-1": "#E45756", "UiO-66": "#54A24B", "ZIF-8": "#B279A2"}
lam = np.array([r["lc"] for r in R["MOF-5"]["c_stretch"]])
for n, v in R.items():
    z = np.array([r["half_widths"][2] / r["half_widths"][0] for r in v["c_stretch"]])
    ax[0].plot(lam, z, "o-", color=col[n], label=n, ms=4)
    ax[1].plot(lam, [r["kappa2"] for r in v["c_stretch"]], "o-", color=col[n], label=n, ms=4)
ax[0].plot(lam, 1 / lam, "k--", lw=1, label="box law 1/λ")
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("stretch of c  (λ = c'/c)"); ax[0].set_ylabel("crystal height / width")
ax[0].axhline(1, color="#bbb", lw=.8); ax[0].legend(fontsize=8); ax[0].set_title("crystal elongation", fontsize=10)
ax[1].set_xscale("log"); ax[1].set_xlabel("stretch of c  (λ = c'/c)"); ax[1].set_ylabel("asphericity κ²"); ax[1].set_title("deviation from isotropy", fontsize=10)
for a in ax: a.grid(alpha=.25)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "results", "figs", "deform_curves.png"), dpi=170)
