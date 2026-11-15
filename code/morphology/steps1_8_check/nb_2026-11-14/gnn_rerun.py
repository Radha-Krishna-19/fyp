"""Rerun the notebook's GNN cross-validation (cells 10-11) with the original labels and with corrected labels.

Run:  python gnn_rerun.py <notebook.ipynb> <static run dir (16 relaxed MOFs)> <static-only run dir (41 MOFs)> <work dir> [epochs] [seeds]

Labels: relaxed gamma from the notebook's printed log (cells 7 and 18), joined to the slabs rebuilt by the
CPU rerun (identical slabs: static gamma agrees to 0.0005 J/m^2 on every one). Two arms, everything else equal:
  original  : gamma at dmu = 0 (free molecule at 0 K), gamma <= 0 labels kept  (as in the notebook)
  corrected : gamma at the liquid-water reference (dmu = -0.5695 eV), gamma <= 0 labels dropped
Same folds (grouped by MOF family, as in cell 11), same seeds, same pretraining on static gamma.
"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, pandas as pd, torch
import mofwulff as mw, mofgnn as G
import water_mu_analysis as W

nb, d16, d41, work = sys.argv[1:5]
EPOCHS = int(sys.argv[5]) if len(sys.argv) > 5 else 300
SEEDS = int(sys.argv[6]) if len(sys.argv) > 6 else 3
torch.set_num_threads(2)
os.makedirs(work, exist_ok=True)

log = W.parse_notebook(nb)
frames = []
for d in (d16, d41):
    for p in sorted(os.listdir(d)):
        if p.startswith("static_") and p.endswith(".csv"):
            frames.append(pd.read_csv(os.path.join(d, p), dtype={"family": str}))
S = pd.concat(frames, ignore_index=True)
S = S[S["cap"] == "water"].drop(columns=[c for c in ("gamma_relaxed_J_m2", "converged") if c in S])
L = log[log["nb_gamma_relaxed"].notna()][["mof", "face", "termination", "nb_gamma_relaxed", "nb_converged"]]
S = S.merge(L.rename(columns={"nb_gamma_relaxed": "gamma_relaxed_J_m2", "nb_converged": "converged"}),
            on=["mof", "face", "termination"], how="left")
# graphs: export_graphs reads the unrelaxed CIF paths written by the rerun; one out_dir for both runs
for d in (d16, d41):
    os.makedirs(os.path.join(work, "cache"), exist_ok=True)
    for m in os.listdir(os.path.join(d, "cache")):
        dst = os.path.join(work, "cache", m)
        if not os.path.exists(dst):
            os.symlink(os.path.join(d, "cache", m), dst)
S.to_csv(os.path.join(work, "slabs_all.csv"), index=False)
INDEX = G.export_graphs(work, os.path.join(work, "slabs_all.csv"), cap="water")

FAMILIES = {"MOF-74": ["Mg-MOF-74", "Ni-DOBDC", "Zn-DOBDC", "Co-DOBDC", "ZnMOF-74"],
            "MIL-88": ["MIL-88A-open", "MIL-88A-dry", "MIL-88B-open", "MIL-88B-dry", "MIL-88C-open", "MIL-88C-dry",
                       "MIL-88D-open", "MIL-88D-dry"],
            "MIL-140": ["MIL-140A-DFT", "MIL-140B-DFT", "MIL-140C-DFT", "MIL-140D-DFT"],
            "IRMOF": ["IRMOF-1", "IRMOF-2", "IRMOF-3", "IRMOF-4", "IRMOF-6", "IRMOF-7", "IRMOF-8", "IRMOF-9", "IRMOF-10",
                      "IRMOF-12", "IRMOF-13", "IRMOF-14", "IRMOF-15", "IRMOF-16"],
            "UiO": ["UiO-66", "Zr-TPDC"], "ZIF-sod": ["ZIF-8", "ZIF-90"], "ZIF-7/9": ["ZIF-7", "ZIF-9"]}
GROUPS = {m: f for f, ms in FAMILIES.items() for m in ms}
KW = dict(epochs=EPOCHS, hidden=64, layers=4, rank_weight=0.5)
out = dict(script="gnn_rerun.py", epochs=EPOCHS, seeds=SEEDS, n_graphs=int(len(INDEX)),
           n_relaxed_labels=int(INDEX["gamma_relaxed_J_m2"].notna().sum()), arms={})
arms = {"original": (INDEX, False), "corrected": (G.at_water_mu(INDEX, mw.WATER_DMU_EV["liquid_298K"]), True)}
for name, (idx, drop) in arms.items():
    t = time.time()
    torch.manual_seed(0); np.random.seed(0)
    lab_mofs = idx[idx["gamma_relaxed_J_m2"].notna()]["mof"].nunique()
    orig_load = G.load_dataset
    G.load_dataset = lambda index, label="gamma_relaxed_J_m2", target="gamma", require_converged=True, _d=drop: \
        orig_load(index, label, target, require_converged, drop_nonpositive=_d)
    try:
        P, M, Sm = G.cross_validate(work, idx, label="gamma_relaxed_J_m2", target="gamma", n_seeds=SEEDS,
                                    val_mofs=1 if lab_mofs >= 8 else 0, pretrain=True, pretrain_epochs=30,
                                    groups=GROUPS, **KW)
    finally:
        G.load_dataset = orig_load
    M.to_csv(os.path.join(work, f"cv_per_mof_{name}.csv"), index=False)
    out["arms"][name] = dict(summary=json.loads(Sm.round(4).to_json(orient="index")), seconds=round(time.time() - t))
    json.dump(out, open(os.path.join(work, "gnn_rerun.json"), "w"), indent=1)
    print(name, "\n", Sm.round(3), flush=True)
