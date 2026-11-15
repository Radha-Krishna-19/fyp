"""GNN surrogate for MOF slab surface energies (option a: structure graph -> gamma).

Teacher : steps 1-6 of mofwulff (healed slab + CHGNet relaxation) -> gamma_relaxed per (MOF, face, termination)
Student : a message-passing GNN on the atom graph of the *unrelaxed* healed slab -> gamma
Then    : lowest predicted gamma per face family -> mofwulff.wulff -> habit (unchanged step 8)

Design rules (each one is a choice, documented here so it can be defended):
  * Input geometry = UNRELAXED healed slab (steps 1-5 only). Relaxation is the expensive step the
    student is meant to skip, so it cannot be an input at inference. Training on relaxed CIFs would
    give a model that needs CHGNet relaxation before it can be used.
  * Edges = the pipeline's own bond rules (mofwulff.bond_kind: org / MM / ML / MO), periodic in-plane.
  * Readout is physical: each atom gets an excess energy e_i (eV); gamma = sum(e_i) / (2A).
    This mirrors gamma = (E_slab - N e_bulk - n E_H2O) / 2A, so the model is size-consistent
    (thicker slab or bigger surface cell -> same gamma).
  * Split by MOF (leave-one-MOF-out, or grouped k-fold for >10 MOFs). A MOF in the test fold never
    appears in training.
  * Baselines are run in every fold: constant mean, linear fit on broken bonds per area, and (when the
    label is relaxed gamma) CHGNet static gamma. The GNN is only useful if it beats them.
  * Surface-localised readout: e_i is multiplied by a smooth cutoff w(depth) that is 1 at the surface
    and 0 deeper than DEPTH_MAX. Atoms deep inside the slab are bulk, so they must add nothing; without
    this, a small per-atom bias adds up in thick slabs (MIL-101: 14,700-atom slabs -> gamma -0.45).
  * positive=True (default for target="gamma") makes gamma = softplus(raw): a crystal with a Wulff shape
    needs gamma > 0 on every face.
  * BFDH (geometry only, project note "CIF to Shape"): d_eff = d_hkl / n, n = first order whose
    structure factor is not cancelled; growth distance proportional to 1/d_eff. Used as a baseline in
    cross-validation and as a cross-check printed next to every GNN prediction.
  * target="delta" learns gamma_relaxed - gamma_static instead (needs one CHGNet single point per slab
    at inference, seconds on a GPU). target="gamma" needs no CHGNet at all.
"""
import json, math, re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from pymatgen.core import Element, Lattice, Structure
from scipy.stats import spearmanr

import mofwulff as mw

EV_A2_TO_J_M2 = mw.EV_A2_TO_J_M2
EDGE_KINDS = ["org", "MM", "ML", "MO"]
N_RBF = 16
RBF_MU = np.linspace(0.8, mw.OUT_REACH, N_RBF)
DEPTH_MAX = 12.0                       # A; atoms deeper than this are treated as bulk-like
NODE_FLOAT = 4 + len(EDGE_KINDS) + 2   # is_metal, is_cap, is_donor, is_lig_donor, bond counts, depth, exp(-depth/2)


# ============================================================================ graph building
def slab_graph(st, n_slab_atoms, area_A2):
    """Atom graph of one healed slab.

    Nodes: atomic number (embedded) + float features
           [is_metal, is_cap (atom added by healing), is_donor, is_ligand_donor,
            bond counts per kind (org, MM, ML, MO), depth below nearest surface / DEPTH_MAX, exp(-depth/2)].
    Edges: every pair the pipeline calls a bond, both directions; features = kind one-hot + distance RBF.
    The slab normal is the c axis (block_slabs builds c = n * (thickness + vacuum)); healing appends
    cap atoms after the n_slab_atoms framework atoms, so index >= n_slab_atoms marks a cap atom.
    """
    nbs = st.get_all_neighbors(mw.OUT_REACH)
    lig = mw.ligand_donors(st, nbs)
    sym = [x.specie.symbol for x in st]
    src, dst, kind, dist = [], [], [], []
    counts = np.zeros((len(st), len(EDGE_KINDS)))
    for i in range(len(st)):
        for n in nbs[i]:
            k = mw.bond_kind(sym[i], sym[n.index], n.nn_distance, i in lig, n.index in lig)
            if k:
                src.append(n.index); dst.append(i); kind.append(EDGE_KINDS.index(k)); dist.append(n.nn_distance)
                counts[i, EDGE_KINDS.index(k)] += 1
    chat = st.lattice.matrix[2] / np.linalg.norm(st.lattice.matrix[2])
    z = st.cart_coords @ chat
    frame = z[:n_slab_atoms]
    depth = np.clip(np.minimum(z - frame.min(), frame.max() - z), 0, DEPTH_MAX)
    is_cap = np.arange(len(st)) >= n_slab_atoms
    x = np.c_[[mw.is_metal(s) for s in sym], is_cap, [s in mw.DONORS for s in sym],
              [i in lig for i in range(len(st))], counts, depth / DEPTH_MAX, np.exp(-depth / 2)].astype(np.float32)
    d = np.array(dist)
    ea = np.c_[np.eye(len(EDGE_KINDS))[kind], np.exp(-((d[:, None] - RBF_MU) / 0.15) ** 2)].astype(np.float32)
    return dict(z=torch.tensor([Element(s).Z for s in sym], dtype=torch.long), x=torch.from_numpy(x),
                edge_index=torch.tensor([src, dst], dtype=torch.long), edge_attr=torch.from_numpy(ea),
                area=float(area_A2), n_atoms=len(st))


def read_cif_in_order(path):
    """Read a pipeline CIF with the original site order.

    pymatgen writes sites in order but its CIF parser regroups them by element, so the healing caps
    (appended last) no longer sit at index >= n_slab_atoms. The writer's labels carry the original
    index (O0, H1, C2, ...), so the order is restored from them."""
    st = Structure.from_file(path)
    num = [re.search(r"(\d+)$", str(s.label or "")) for s in st]
    if all(num) and len({int(n.group(1)) for n in num}) == len(st):
        order = np.argsort([int(n.group(1)) for n in num])
        st = Structure.from_sites([st[int(i)] for i in order])
    return st


def _resolve(path, out_dir):
    """slabs.csv stores absolute Colab paths; re-root them under out_dir if the results moved."""
    if isinstance(path, str) and Path(path).exists():
        return path
    if not isinstance(path, str) or "structures/" not in path:
        return None
    p = Path(out_dir) / ("structures/" + path.split("structures/", 1)[1])
    return str(p) if p.exists() else None


def export_graphs(out_dir, slabs_csv=None, cap="water", source="unrelaxed"):
    """Turn every healed slab of slabs.csv into a graph file (out_dir/graphs/*.pt) + index.csv.

    One row per slab with graph path and all labels (gamma_static_J_m2, gamma_relaxed_J_m2, converged).
    source="unrelaxed" (default, see module docstring) or "relaxed" (only for analysis).
    """
    out_dir = Path(out_dir)
    df = pd.read_csv(slabs_csv or out_dir / "slabs.csv")
    for c in ("gamma_relaxed_J_m2", "converged", "unrelaxed_cif", "relaxed_cif"):
        if c not in df:
            df[c] = np.nan                     # static-only runs (QUICK_TEST) have no relaxation columns
    df = df[(df["cap"] == cap) & df["gamma_static_J_m2"].notna()].copy()
    gdir = out_dir / "graphs"; gdir.mkdir(exist_ok=True)
    rows, skipped = [], Counter()
    for _, r in df.iterrows():
        cif = _resolve(r.get("unrelaxed_cif" if source == "unrelaxed" else "relaxed_cif"), out_dir)
        if cif is None:
            skipped["missing cif"] += 1; continue
        p = gdir / (Path(cif).stem + ".pt")
        if not p.exists():
            st = read_cif_in_order(cif)
            n_slab = int(r["n_slab_atoms"])
            if len(st) != int(r["n_atoms"]):
                skipped["atom count mismatch"] += 1; continue
            if not {s.specie.symbol for s in st[n_slab:]} <= {"O", "H"}:
                skipped["cap atoms not O/H (site order lost)"] += 1; continue
            torch.save(slab_graph(st, n_slab, r["area_A2"]), p)
        rows.append({**r.to_dict(), "graph": str(p)})
    idx = pd.DataFrame(rows)
    idx.to_csv(gdir / "index.csv", index=False)
    print(f"{len(idx)} graphs from {idx['mof'].nunique() if len(idx) else 0} MOFs -> {gdir}"
          + (f" | skipped {dict(skipped)}" if skipped else ""))
    return idx


# ============================================================================ model
class GatedConv(nn.Module):
    """CGCNN-style gated message passing with a residual update."""
    def __init__(self, h, e):
        super().__init__()
        self.lin = nn.Linear(2 * h + e, 2 * h)
        self.norm = nn.LayerNorm(h)

    def forward(self, x, ei, ea):
        s, d = ei
        gate, core = self.lin(torch.cat([x[d], x[s], ea], -1)).chunk(2, -1)
        msg = torch.sigmoid(gate) * F.softplus(core)
        agg = torch.zeros_like(x).index_add_(0, d, msg)
        return F.softplus(x + self.norm(agg))


def surface_weight(depth):
    """1 at the surface, 0 deeper than DEPTH_MAX (cosine cutoff)."""
    return 0.5 * (1 + torch.cos(math.pi * torch.clamp(depth, max=DEPTH_MAX) / DEPTH_MAX))


class SlabGNN(nn.Module):
    """Atom graph -> per-atom excess energy (eV) x surface weight -> gamma = sum / 2A (J/m^2)."""
    def __init__(self, hidden=64, layers=4, max_z=100, positive=True):
        super().__init__()
        self.positive = positive
        self.emb = nn.Embedding(max_z + 1, hidden)
        self.inp = nn.Linear(NODE_FLOAT, hidden)
        e_dim = len(EDGE_KINDS) + N_RBF
        self.convs = nn.ModuleList([GatedConv(hidden, e_dim) for _ in range(layers)])
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Softplus(), nn.Linear(hidden, 1))

    def forward(self, b):
        x = self.emb(b["z"]) + self.inp(b["x"])
        for c in self.convs:
            x = c(x, b["edge_index"], b["edge_attr"])
        e_atom = self.head(x).squeeze(-1) * surface_weight(b["x"][:, 8] * DEPTH_MAX)
        e_slab = torch.zeros(b["n_graphs"], device=x.device).index_add_(0, b["batch"], e_atom)
        g = e_slab / (2 * b["area"]) * EV_A2_TO_J_M2
        return F.softplus(g) if self.positive else g      # beta=1: no dead zone for negative raw values


def collate(graphs, device):
    zs, xs, eis, eas, batch, off = [], [], [], [], [], 0
    for i, g in enumerate(graphs):
        zs.append(g["z"]); xs.append(g["x"]); eas.append(g["edge_attr"]); eis.append(g["edge_index"] + off)
        batch.append(torch.full((g["n_atoms"],), i, dtype=torch.long)); off += g["n_atoms"]
    return dict(z=torch.cat(zs).to(device), x=torch.cat(xs).to(device), edge_index=torch.cat(eis, 1).to(device),
                edge_attr=torch.cat(eas).to(device), batch=torch.cat(batch).to(device), n_graphs=len(graphs),
                area=torch.tensor([g["area"] for g in graphs], dtype=torch.float32, device=device))


# ============================================================================ data
def load_dataset(index, label="gamma_relaxed_J_m2", target="gamma", require_converged=True):
    """Labelled rows of index.csv + their graphs.

    label  : column used as truth. gamma_relaxed_J_m2 for real runs. gamma_static_J_m2 only for
             smoke tests (the pipeline relaxes just RELAX_TOP_K terminations per family).
    target : "gamma" -> model predicts the label; "delta" -> model predicts label - gamma_static.
    Returns (labelled DataFrame, {graph path: graph}) ; unlabelled rows stay in `index` for inference.
    """
    idx = index if isinstance(index, pd.DataFrame) else pd.read_csv(index)
    lab = idx[idx[label].notna()].copy()
    if require_converged and label == "gamma_relaxed_J_m2" and "converged" in lab:
        lab = lab[lab["converged"].astype(str).str.lower() == "true"]
    lab["y"] = lab[label] - (lab["gamma_static_J_m2"] if target == "delta" else 0.0)
    graphs = {p: torch.load(p, weights_only=False) for p in idx["graph"]}
    return lab.reset_index(drop=True), graphs


def _mof_batches(df, batch_size, rng):
    """Batches that keep a MOF's slabs together, so the ranking loss sees within-MOF pairs."""
    groups = [g.index.to_numpy() for _, g in df.groupby("mof")]
    rng.shuffle(groups)
    cur = []
    for g in groups:
        g = rng.permutation(g)
        for i in range(0, len(g), batch_size):
            cur.extend(g[i:i + batch_size].tolist())
            if len(cur) >= batch_size:
                yield cur; cur = []
    if cur:
        yield cur


def _rank_loss(pred, y, mof_ids, tau=0.1, min_gap=0.02):
    """Pairwise logistic loss on within-MOF orderings (the Wulff shape depends on the ordering)."""
    dy = y[:, None] - y[None, :]
    same = (mof_ids[:, None] == mof_ids[None, :]) & (dy.abs() > min_gap)
    if not same.any():
        return pred.sum() * 0
    dp = pred[:, None] - pred[None, :]
    return F.softplus(-torch.sign(dy[same]) * dp[same] / tau).mean()


# ============================================================================ training
def train(df, graphs, epochs=300, hidden=64, layers=4, lr=1e-3, weight_decay=1e-4, batch_size=16,
          rank_weight=0.5, seed=0, device=None, val_df=None, patience=60, verbose=False, positive=True,
          init_state=None):
    """Train one SlabGNN. If val_df is given, keeps the epoch with the lowest validation MAE.
    init_state: weights to start from (fine-tuning after pretraining)."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    model = SlabGNN(hidden, layers, positive=positive).to(device)
    if init_state is not None:
        model.load_state_dict(init_state)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    mof_code = {m: i for i, m in enumerate(df["mof"].unique())}
    best, best_state, bad = np.inf, None, 0
    for ep in range(epochs):
        model.train()
        for ids in _mof_batches(df, batch_size, rng):
            sub = df.loc[ids]
            b = collate([graphs[p] for p in sub["graph"]], device)
            y = torch.tensor(sub["y"].to_numpy(), dtype=torch.float32, device=device)
            m = torch.tensor([mof_code[x] for x in sub["mof"]], device=device)
            pred = model(b)
            loss = F.huber_loss(pred, y, delta=0.3) + rank_weight * _rank_loss(pred, y, m)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        sched.step()
        if val_df is not None and len(val_df):
            mae = float(np.mean(np.abs(predict(model, val_df, graphs, device) - val_df["y"].to_numpy())))
            if mae < best - 1e-4:
                best, bad = mae, 0; best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            else:
                bad += 1
                if bad >= patience:
                    break
        if verbose and ep % 50 == 0:
            print(f"epoch {ep} loss {float(loss):.4f}" + (f" val MAE {best:.4f}" if val_df is not None else ""))
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


@torch.no_grad()
def predict(model, df, graphs, device=None, batch_size=32):
    device = device or next(model.parameters()).device
    model.eval(); out = []
    paths = list(df["graph"])
    for i in range(0, len(paths), batch_size):
        out.append(model(collate([graphs[p] for p in paths[i:i + batch_size]], device)).cpu().numpy())
    return np.concatenate(out) if out else np.array([])


def train_ensemble(df, graphs, n_seeds=3, val_mofs=0, init_states=None, **kw):
    """n_seeds models; if val_mofs > 0, that many training MOFs are held out for early stopping.
    init_states: one state dict per seed (from pretrain), or None."""
    models = []
    for s in range(n_seeds):
        if init_states is not None:
            kw = {**kw, "init_state": init_states[s % len(init_states)]}
        tr, va = df, None
        if val_mofs:
            mofs = np.random.default_rng(100 + s).permutation(df["mof"].unique())
            va = df[df["mof"].isin(mofs[:val_mofs])]; tr = df[~df["mof"].isin(mofs[:val_mofs])]
        models.append(train(tr.reset_index(drop=True), graphs, seed=s,
                            val_df=None if va is None else va.reset_index(drop=True), **kw))
    return models


def pretrain_states(index, graphs, exclude_mofs=(), n_seeds=3, epochs=100, **kw):
    """Pretrain on CHGNet *static* gamma (cheap: seconds per MOF) of every slab whose MOF is not excluded.
    Returns one state dict per seed, used as the starting point for fine-tuning on relaxed gamma.
    In cross-validation the test MOFs are excluded, so nothing about them is seen before testing."""
    pre = index[index["gamma_static_J_m2"].notna() & ~index["mof"].isin(list(exclude_mofs))].copy()
    pre["y"] = pre["gamma_static_J_m2"]
    if pre["mof"].nunique() < 2:
        return None
    ms = train_ensemble(pre.reset_index(drop=True), graphs, n_seeds=n_seeds, epochs=epochs,
                        **{k: v for k, v in kw.items() if k not in ("init_state", "epochs")})
    return [{k: v.detach().clone() for k, v in m.state_dict().items()} for m in ms]


def predict_ensemble(models, df, graphs):
    return np.mean([predict(m, df, graphs) for m in models], axis=0)


# ============================================================================ Wulff from any gamma table
def _families_from_meta(meta):
    conv = Structure(Lattice(meta["conv_lattice"]), ["H"], [[0, 0, 0]])
    rots = [np.array(r) for r in meta["_rotations"]]
    fams = mw.face_families(conv, rots, faces=[tuple(f["rep"]) for f in meta["families"]])
    return conv, fams, rots


def habit_from_gammas(meta, gammas):
    """gammas: {family key: gamma}. Returns (habit name, dominant face, wulff dict)."""
    conv, fams, rots = _families_from_meta(meta)
    g = {k: v for k, v in gammas.items() if np.isfinite(v)}
    if len(g) < 2:
        return "not enough faces", None, None
    if min(g.values()) <= 0:
        return "undefined (gamma <= 0)", None, None
    if min(g.values()) < 1e-3:
        return "undefined (gamma ~ 0)", None, None
    try:
        w = mw.wulff(conv, fams, g, rots)
    except Exception as exc:                     # degenerate polyhedron (e.g. qhull on a point)
        return f"undefined (Wulff failed: {type(exc).__name__})", None, None
    if w is None:
        return "no faces", None, None
    name = mw.name_habit(w, fams, meta["crystal_system"], conv)
    names = {f["key"]: f["name"] for f in fams}
    fr = {names.get(k, k): v for k, v in w["area_fractions"].items()}
    return name, max(fr, key=fr.get), w


def habit_class(name):
    """Coarse habit label for agreement checks ('block/prism: {100} 60%, ...' -> 'block/prism')."""
    return re.split(r"[:(]", str(name))[0].strip()


def load_meta(out_dir, mof):
    return json.loads((Path(out_dir) / "cache" / re.sub(r"[^\w.-]", "_", mof) / "meta.json").read_text())


# ============================================================================ BFDH (geometry only)
def structure_factor(st, hkl):
    """|F(hkl)| / sum(Z): Z-weighted sum of exp(2 pi i h.x) over the atoms of st (project note, Step 7)."""
    Z = np.array([x.specie.Z for x in st], float)
    ph = 2 * np.pi * (st.frac_coords @ np.asarray(hkl, float))
    return float(abs(np.sum(Z * np.exp(1j * ph))) / Z.sum())


def _skeleton(info):
    """Atoms used for the cancellation test: the same skeleton that gave the symmetry in step 1.
    H is always left out (ordered H in a CIF breaks symmetry that the framework has)."""
    st = info["conv"].copy()
    els = {x.specie.symbol for x in st}
    if info["symmetry_source"] == "metal+C":
        st.remove_species([e for e in els if not (mw.is_metal(e) or e == "C")])
    elif "H" in els:
        st.remove_species(["H"])
    return st


def d_eff_table(info, families, max_order=8, tol=0.01):
    """d_eff = d_hkl / n for each family; n = first order n*(hkl) whose |F| / sum(Z) > tol.
    Note: rotations make every member of a family equivalent, so the representative is enough."""
    sk = _skeleton(info)
    out = {}
    for f in families:
        h = np.array(f["rep"]); d = float(info["conv"].lattice.d_hkl(tuple(int(x) for x in h)))
        n = next((k for k in range(1, max_order + 1) if structure_factor(sk, k * h) > tol), None)
        out[f["key"]] = dict(name=f["name"], d=round(d, 4), n=n or max_order, d_eff=round(d / (n or max_order), 4),
                             all_orders_cancelled=n is None)
    return out


def bfdh_for_mof(out_dir, mof):
    """d_eff table for a MOF of the pipeline run (cached in cache/<mof>/bfdh.json). None if the CIF is gone."""
    cdir = Path(out_dir) / "cache" / re.sub(r"[^\w.-]", "_", mof)
    if (cdir / "bfdh.json").exists():
        return json.loads((cdir / "bfdh.json").read_text())
    try:
        meta = load_meta(out_dir, mof)
    except FileNotFoundError:
        return None
    if not Path(meta.get("cif", "")).exists():
        return None
    c = meta.get("config", {})
    info = mw.standardize(meta["cif"], c.get("symprec", 0.1), c.get("disorder", "majority"))
    fams = mw.face_families(info["conv"], info["rotations"], faces=[tuple(f["rep"]) for f in meta["families"]])
    t = d_eff_table(info, fams)
    (cdir / "bfdh.json").write_text(json.dumps(t, indent=1))
    return t


def bfdh_habit(meta, table):
    """BFDH shape: Wulff construction with plane distances proportional to 1/d_eff."""
    return habit_from_gammas(meta, {k: 1.0 / v["d_eff"] for k, v in table.items()})


# ============================================================================ saving / loading
def training_elements(lab, graphs):
    return sorted({Element.from_Z(int(z)).symbol for p in lab["graph"] for z in torch.unique(graphs[p]["z"]).tolist()})


def save_models(path, models, lab, graphs, hidden, layers, label, target):
    torch.save(dict(version=2, states=[m.state_dict() for m in models], hidden=hidden, layers=layers,
                    positive=models[0].positive, label=label, target=target,
                    mofs=sorted(lab["mof"].unique()), elements=training_elements(lab, graphs)), path)


def load_models(path, graphs_dir=None, device=None):
    """Returns (models, checkpoint dict). Old checkpoints (before the surface cutoff) are flagged."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    ck = torch.load(path, weights_only=False, map_location=device)
    if ck.get("version", 1) < 2:
        print("WARNING: this model was trained with the old readout (no surface cutoff, no positivity). "
              "Retrain it (cells 11-12) before trusting predictions.")
    models = []
    for st in ck["states"]:
        m = SlabGNN(ck["hidden"], ck["layers"], positive=ck.get("positive", False)).to(device)
        m.load_state_dict(st); m.eval(); models.append(m)
    if not ck.get("elements") and graphs_dir:
        zs = set()
        for p in Path(graphs_dir).glob("*.pt"):
            zs |= set(torch.load(p, weights_only=False)["z"].tolist())
        ck["elements"] = sorted(Element.from_Z(int(z)).symbol for z in zs)
    return models, ck


# ============================================================================ evaluation
def _family_table(rows, col):
    """Lowest value of `col` per face family."""
    r = rows[rows[col].notna()]
    return r.groupby("family")[col].min().to_dict()


def evaluate_mof(out_dir, mof, test_rows, all_rows, truth_col, pred_cols):
    """Per-MOF metrics for each predictor column.
    truth: lowest labelled gamma per family. prediction: lowest predicted gamma per family over ALL
    terminations (labelled or not), which is how the model is used at inference."""
    meta = load_meta(out_dir, mof)
    true_f = _family_table(test_rows, truth_col)
    true_habit, true_dom, _ = habit_from_gammas(meta, true_f)
    out = []
    for name, col in pred_cols.items():
        if col not in all_rows or all_rows[col].isna().all():
            continue
        pred_f = {k: v for k, v in _family_table(all_rows, col).items() if k in true_f}
        fams = sorted(true_f)
        rho = spearmanr([true_f[k] for k in fams], [pred_f[k] for k in fams]).correlation if len(fams) > 2 else np.nan
        habit, dom, _ = habit_from_gammas(meta, pred_f)
        lab = test_rows[test_rows[col].notna()]
        out.append(dict(mof=mof, model=name, n_labelled=len(lab), n_families=len(fams),
                        MAE_J_m2=float(np.mean(np.abs(lab[col] - lab[truth_col]))),
                        spearman_families=rho,
                        lowest_face_agrees=min(true_f, key=true_f.get) == min(pred_f, key=pred_f.get),
                        true_habit=true_habit, pred_habit=habit,
                        # no Wulff shape exists when the truth has gamma <= 0: not counted as agreement
                        habit_agrees=(habit_class(true_habit) == habit_class(habit)) if true_dom is not None else np.nan,
                        dominant_agrees=(true_dom == dom) if true_dom is not None else np.nan))
    return out


def cross_validate(out_dir, index, label="gamma_relaxed_J_m2", target="gamma", n_folds=None, n_seeds=3,
                   val_mofs=0, pretrain=False, pretrain_epochs=30, pretrain_seeds=1, finetune_lr=3e-4,
                   groups=None, **train_kw):
    """Grouped-by-MOF cross-validation of the GNN against baselines.

    Folds: leave-one-group-out when there are <= 10 groups, otherwise n_folds (default 5) grouped folds.
    groups: {mof: family} so near-copies (Mg/Ni/Zn/Co-MOF-74, the IRMOF series, ...) are always on the
    same side of the split, including during pretraining. MOFs not listed form their own group.
    Returns (per-slab predictions, per-MOF metrics, summary).
    """
    idx = index if isinstance(index, pd.DataFrame) else pd.read_csv(index)
    lab, graphs = load_dataset(idx, label, target)
    mofs = np.array(sorted(lab["mof"].unique()))
    inv_d = {}                                       # (mof, family) -> 1/d_eff, for the BFDH baseline
    for m in idx["mof"].unique():
        t = bfdh_for_mof(out_dir, m)
        if t:
            inv_d.update({(m, k): 1.0 / v["d_eff"] for k, v in t.items()})
    if len(mofs) < 2:
        raise ValueError("need labelled slabs from at least 2 MOFs")
    grp = lambda m: (groups or {}).get(m, m)
    gnames = np.array(sorted({grp(m) for m in mofs}))
    if len(gnames) < 2:
        raise ValueError("need labelled slabs from at least 2 groups")
    k = len(gnames) if (n_folds is None and len(gnames) <= 10) else (n_folds or 5)
    gfolds = np.array_split(np.random.default_rng(0).permutation(gnames), k)
    folds = [np.array([m for m in mofs if grp(m) in set(gf)]) for gf in gfolds]
    all_mofs = idx["mof"].unique()
    preds, metrics = [], []
    for fi, test_mofs in enumerate(folds):
        tr = lab[~lab["mof"].isin(test_mofs)].reset_index(drop=True)
        init = None
        if pretrain:
            test_groups = {grp(m) for m in test_mofs}
            excl = [m for m in all_mofs if grp(m) in test_groups]          # whole test families stay unseen
            init = pretrain_states(idx, graphs, exclude_mofs=excl, n_seeds=pretrain_seeds, epochs=pretrain_epochs,
                                   **{k: v for k, v in train_kw.items() if k in ("hidden", "layers", "batch_size")})
        kw = {"positive": target == "gamma", **train_kw}
        if init is not None:
            kw["lr"] = finetune_lr
        models = train_ensemble(tr, graphs, n_seeds=n_seeds, val_mofs=val_mofs, init_states=init, **kw)
        # baselines fitted on the training MOFs only
        a, b0 = np.polyfit(tr["bonds_per_A2"], tr[label], 1)
        mean_y = tr[label].mean()
        if label != "gamma_static_J_m2":
            s1, s0 = np.polyfit(tr["gamma_static_J_m2"], tr[label], 1)
        trb = tr.assign(inv_d=[inv_d.get((m, f), np.nan) for m, f in zip(tr["mof"], tr["family"])]).dropna(subset=["inv_d"])
        bf = np.polyfit(trb["inv_d"], trb[label], 1) if trb["mof"].nunique() >= 2 else None
        for m in test_mofs:
            all_m = idx[idx["mof"] == m].copy()
            g = predict_ensemble(models, all_m, graphs)
            all_m["pred_gnn"] = g + (all_m["gamma_static_J_m2"].to_numpy() if target == "delta" else 0)
            all_m["pred_mean"] = mean_y
            all_m["pred_bonds_linear"] = a * all_m["bonds_per_A2"] + b0
            if bf is not None:
                iv = np.array([inv_d.get((m, f), np.nan) for f in all_m["family"]])
                if np.isfinite(iv).all():
                    all_m["pred_bfdh_linear"] = bf[0] * iv + bf[1]
            if label != "gamma_static_J_m2":
                all_m["pred_static_chgnet"] = all_m["gamma_static_J_m2"]
                all_m["pred_static_calibrated"] = s1 * all_m["gamma_static_J_m2"] + s0
            all_m["fold"] = fi
            test_rows = all_m[all_m["graph"].isin(lab["graph"])]          # labelled (and converged) slabs
            cols = {c[5:]: c for c in all_m.columns if c.startswith("pred_")}
            metrics += evaluate_mof(out_dir, m, test_rows, all_m, label, cols)
            preds.append(all_m)
        print(f"fold {fi + 1}/{k}: test {list(test_mofs)}, train {tr['mof'].nunique()} MOFs / {len(tr)} slabs"
              + (f", pretrained on static gamma of {len(set(all_mofs) - set(excl))} MOFs" if init is not None else ""))
    P, M = pd.concat(preds), pd.DataFrame(metrics)
    S = M.groupby("model").agg(MAE_J_m2=("MAE_J_m2", "mean"), spearman_families=("spearman_families", "mean"),
                               lowest_face_agrees=("lowest_face_agrees", "mean"), habit_agrees=("habit_agrees", "mean"),
                               dominant_agrees=("dominant_agrees", "mean"), n_mofs=("mof", "count"))
    return P, M, S.sort_values("MAE_J_m2")


# ============================================================================ inference on a new MOF (no CHGNet)
def slabs_only(name, cif, symprec=0.1, disorder="majority", max_index=1, n_families=4, faces=None,
               thickness=15.0, vacuum=15.0, level_tol=0.3, max_terms=8):
    """Steps 1-5 of the pipeline (same rules, same order), no energies. Yields slab rows + structures.
    Note: slabs are cut from the unrelaxed bulk; the training slabs came from the CHGNet-relaxed bulk."""
    info = mw.standardize(cif, symprec, disorder)
    fams = mw.face_families(info["conv"], info["rotations"], max_index, n_families, faces)
    meta = dict(mof=name, conv_lattice=info["conv"].lattice.matrix.tolist(), crystal_system=info["crystal_system"],
                families=[{"key": f["key"], "name": f["name"], "rep": f["rep"]} for f in fams],
                _rotations=[R.tolist() for R in info["rotations"]], formula=info["formula"],
                elements=sorted({x.specie.symbol for x in info["structure"]}))
    meta["bfdh"] = d_eff_table(info, fams)
    rows = []
    for f in fams:
        made = mw.block_slabs(info["conv"], info["prim"], f["rep"], thickness, vacuum, level_tol)
        for m in made:
            m["miss"], m["broken"] = mw.broken_bonds(m)
            m["bond_density"] = sum(v for k, v in m["broken"].items() if k in ("ML", "MO")) / 2 / m["area_A2"]
        made.sort(key=lambda m: m["bond_density"])
        for ti, m in enumerate(made[:max_terms]):
            st, n_w, status = mw.heal(m, m["miss"])
            if st is None:
                continue
            rows.append(dict(mof=name, family=f["key"], face=f["name"], termination=ti, n_slab_atoms=len(m["slab"]),
                             n_atoms=len(st), n_water=n_w, area_A2=m["area_A2"], bonds_per_A2=m["bond_density"],
                             status=status, _st=st))
    return meta, rows


def predict_mof(models, name, cif, target="gamma", train_elements=None, **cfg):
    """CIF -> slabs -> graphs -> GNN gamma per termination -> lowest per family -> Wulff habit.
    Also returns the BFDH shape (geometry only) and the elements the GNN never saw in training."""
    if target == "delta":
        raise ValueError("delta models need CHGNet static gamma; run the pipeline with QUICK_TEST for this MOF")
    meta, rows = slabs_only(name, cif, **cfg)
    graphs = {f"g{i}": slab_graph(r["_st"], r["n_slab_atoms"], r["area_A2"]) for i, r in enumerate(rows)}
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "_st"} for r in rows])
    df["graph"] = list(graphs)
    df["gamma_pred_J_m2"] = predict_ensemble(models, df, graphs)
    fam_g = df.groupby("family")["gamma_pred_J_m2"].min().to_dict()
    habit, dom, w = habit_from_gammas(meta, fam_g)
    b_habit, b_dom, b_w = bfdh_habit(meta, meta["bfdh"])
    unseen = sorted(set(meta["elements"]) - set(train_elements)) if train_elements else []
    warn = []
    if unseen:
        warn.append(f"elements never seen in training: {unseen} -> GNN prediction not reliable")
    if df["n_atoms"].max() > 5000:
        warn.append(f"very large slabs ({df['n_atoms'].max()} atoms); training slabs had < 1000")
    return df, dict(mof=name, habit=habit, dominant_face=dom, gammas=fam_g, bfdh_habit=b_habit,
                    bfdh_dominant_face=b_dom, d_eff={v["name"]: v["d_eff"] for v in meta["bfdh"].values()},
                    unseen_elements=unseen, warnings=warn), w, meta | {"bfdh_wulff": b_w}