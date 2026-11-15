"""Morphology spectrum: every distinct Wulff shape class that a MOF's face set can produce when the
relative surface energies change, and how far each class is from the favoured (computed) shape.

Structure only, by design: no solvent, temperature, additive or concentration inputs anywhere.

Definitions (documented so the output can be defended):
  * Face set: the face families that have a gamma (from CHGNet, the GNN or BFDH). Low-index only
    (MAX_INDEX of the pipeline), so faces such as {211} can never appear.
  * Map axes: gamma ratios r_k = gamma_k / gamma_ref, ref = {100} if present, else the first family.
    A Wulff shape depends only on these ratios (it is scale-invariant), so n faces give n-1 axes.
    Cubic {100},{110},{111}: x = gamma{110}/gamma{100}, y = gamma{111}/gamma{100}.
  * Scan: up to 2 axes -> full grid (default 0.3..2.5, step 0.05, widened to include the favoured
    and BFDH points). 3 or more axes -> scrambled Sobol points, log-uniform in the same range, in
    batches until two batches in a row add no new class or max_samples is reached.
  * Shape class: habit label (mofwulff.name_habit, follows the project note) + the set of faces
    covering at least FACE_MIN of the surface. Truncated shapes are continuous families, so area
    fractions are reported as ranges inside a class, not used to split classes.
  * Distance from the favoured shape (the structure-specific result): for a gamma vector g and the
    favoured g0, spread = max_k ln(g_k/g0_k) - min_k ln(g_k/g0_k). It does not depend on the overall
    scale or on the choice of ref. Reported as min_ratio_change_pct = (exp(spread) - 1) * 100:
    "the gamma ratio of two faces must change by at least this much". lower_face is the face that
    becomes relatively cheaper, raise_face the one that becomes dearer. The closest scanned point of
    each class is refined by bisection along the straight line (in log-gamma space) from g0, and the
    returned gamma vector is re-checked to be in that class, so the number is an upper bound reached by
    a real, verified gamma vector.
  * Favoured gamma <= 0 (e.g. CHGNet for Mg-MOF-74, CALF-20-Cl): no favoured shape and no distances;
    the class list is still produced (it then reflects symmetry and face set only).
"""
import inspect
import itertools
import json
import math
import re
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Lattice, Structure

import mofwulff as mw
import mofgnn as G

FACE_MIN = 0.05                    # a face "is present" if it covers >= 5 % of the surface (same tolerance
                                   # as mofwulff.name_habit, which calls a shape a cube when {100} > 95 %)
PURE = {"cube": "{100}", "octahedron": "{111}", "rhombic_dodecahedron": "{110}"}
DEFAULT_GRID = (0.3, 2.5, 0.05)    # ratio range and step (spec: 0.3-2.5, step 0.02-0.05)
GAMMA_MIN = 1e-3                   # J/m^2; below this the favoured point is treated as undefined
FORBIDDEN_ARGS = ("solvent", "temperature", "temp", "additive", "modulator", "concentration", "time")


# ============================================================================ helpers
def _tag(name):
    return re.sub(r"[^\w.-]", "_", str(name))


def _face_order(name):
    """Sort face names like {100} < {110} < {111} < {2-10} by their digits."""
    return [int(x) for x in re.findall(r"\d", name)], name


def _dummy_conv(conv_lattice):
    return Structure(Lattice(conv_lattice), ["H"], [[0, 0, 0]])


def ratio_change(g, g0, keys):
    """(spread, lower key, raise key) between gamma vectors g and g0 (dicts), scale-free."""
    lr = np.array([math.log(g[k] / g0[k]) for k in keys])
    return float(lr.max() - lr.min()), keys[int(lr.argmin())], keys[int(lr.argmax())]


def pct(spread):
    return (math.exp(spread) - 1.0) * 100.0


# ============================================================================ B3: pure Wulff function
def wulff_from_gammas(conv, families, gammas, rotations, crystal_system, face_min=FACE_MIN, bounded=None):
    """gamma vector -> shape. Never raises.

    Returns dict(ok, habit, label, faces_present, class_id, area_fractions {face name: fraction},
    bounded, w) or dict(ok=False, reason=...)."""
    names = {f["key"]: f["name"] for f in families}
    g = {k: float(v) for k, v in gammas.items() if v is not None and np.isfinite(v)}
    if len(g) < 2:
        return dict(ok=False, reason="fewer than 2 faces with a gamma")
    bad = [names.get(k, k) for k, v in g.items() if v <= 0]
    if bad:
        return dict(ok=False, reason="gamma <= 0 for " + ", ".join(bad))
    try:
        w = mw.wulff(conv, families, g, rotations, bounded=bounded)
    except Exception as exc:                                        # degenerate polyhedron etc.
        return dict(ok=False, reason=f"Wulff failed: {type(exc).__name__}: {exc}")
    if w is None:
        return dict(ok=False, reason="no faces")
    habit = mw.name_habit(w, families, crystal_system, conv)
    label = G.habit_class(habit)
    fr = {names.get(k, k): float(v) for k, v in w["area_fractions"].items() if k != "open"}
    present = tuple(sorted((n for n, v in fr.items() if v >= face_min), key=_face_order))
    if label in PURE:                       # pure shapes: one face by definition (name tolerance = 5 %)
        present = (PURE[label],)
    elif crystal_system == "cubic" and len(present) == 1 and present[0] in PURE.values():
        # only one face covers >= 5 %: two small facets (< 5 % each) do not make it a truncated shape
        label = {v: k for k, v in PURE.items()}[present[0]]
    return dict(ok=True, habit=habit if G.habit_class(habit) == label or crystal_system != "cubic" else label,
                label=label, faces_present=present,
                class_id=f"{label} | {'+'.join(present)}", area_fractions=fr, bounded=bool(w["bounded"]), w=w)


# ============================================================================ B1: scan
def scan_morphology_map(conv, families, rotations, crystal_system, gamma_favoured, gamma_bfdh=None,
                        grid=DEFAULT_GRID, max_samples=4096, batch=512, face_min=FACE_MIN, refine_steps=12,
                        seed=0, keep_points=True, log=print):
    """All shape classes reachable by changing relative gammas of the given faces (structure only).

    gamma_favoured: {family key: gamma} from CHGNet / GNN / BFDH. Families without a gamma are left out.
    gamma_bfdh:     optional {family key: 1/d_eff}, placed on the map as a second point.
    Returns a result dict (see module docstring); raises ValueError if fewer than 2 faces have a gamma.
    """
    t0 = time.time()
    keys = [f["key"] for f in families
            if f["key"] in gamma_favoured and gamma_favoured[f["key"]] is not None
            and np.isfinite(gamma_favoured[f["key"]])]
    if len(keys) < 2:
        raise ValueError(f"Morphology spectrum needs a gamma for at least 2 face families; got {len(keys)} "
                         f"({[f['name'] for f in families if f['key'] in keys]}). "
                         "Check that the slabs for this MOF could be cut and healed.")
    fams = [f for f in families if f["key"] in keys]
    names = {f["key"]: f["name"] for f in fams}
    ref = next((f["key"] for f in fams if f["name"] == "{100}"), keys[0])
    free = [k for k in keys if k != ref]
    dims = len(free)
    g0 = {k: float(gamma_favoured[k]) for k in keys}
    fav_ok = min(g0.values()) > GAMMA_MIN
    gb = None
    if gamma_bfdh and all(k in gamma_bfdh and gamma_bfdh[k] and gamma_bfdh[k] > 0 for k in keys):
        gb = {k: float(gamma_bfdh[k]) for k in keys}

    def ratios_of(g):
        return tuple(g[k] / g[ref] for k in free)

    def gammas_of(r):
        return {ref: 1.0, **{k: float(x) for k, x in zip(free, r)}}

    # Whether the polyhedron is closed depends only on the plane set, so check it once (mofwulff.wulff).
    probe = wulff_from_gammas(conv, fams, {k: 1.0 for k in keys}, rotations, crystal_system, face_min)
    closed = True if probe.get("ok") and probe["bounded"] else None

    cache = {}

    def evaluate(g):
        key = tuple(round(g[k] / g[ref], 6) for k in free)
        if key not in cache:
            cache[key] = wulff_from_gammas(conv, fams, g, rotations, crystal_system, face_min, bounded=closed)
        return cache[key]

    lo, hi, step = (float(x) for x in grid)
    special = [r for r in ([ratios_of(g0)] if fav_ok else []) + ([ratios_of(gb)] if gb else [])]
    if special:
        lo = min(lo, 0.9 * min(min(r) for r in special))
        hi = max(hi, 1.1 * max(max(r) for r in special))
    points, failures = [], []

    def add_point(r, kind):
        res = evaluate(gammas_of(r))
        rec = {**{f"r_{names[k]}": x for k, x in zip(free, r)}, "kind": kind, "ok": res["ok"],
               "class_id": res.get("class_id"), "reason": None if res["ok"] else res["reason"]}
        points.append(rec)
        if not res["ok"]:
            failures.append(rec)
        return res

    if dims <= 2:
        method = "grid"
        axis = np.round(np.arange(lo, hi + step / 2, step), 6)
        for r in itertools.product(axis, repeat=dims):
            add_point(r, "grid")
    else:
        method = "sobol"
        import warnings
        from scipy.stats import qmc
        warnings.filterwarnings("ignore", message=".*balance properties of Sobol.*")
        sob = qmc.Sobol(d=dims, scramble=True, seed=seed)
        seen, quiet, n = set(), 0, 0
        while n < max_samples and quiet < 2:
            u = sob.random(min(batch, max_samples - n))
            new = 0
            for row in np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo))):
                res = add_point(tuple(float(x) for x in row), "sample")
                if res["ok"] and res["class_id"] not in seen:
                    seen.add(res["class_id"]); new += 1
            n += len(u)
            quiet = quiet + 1 if new == 0 else 0
    n_scan = len(points)
    fav = add_point(ratios_of(g0), "favoured") if fav_ok else None
    bf = add_point(ratios_of(gb), "bfdh") if gb else None

    # ---------------------------------------------------------------- aggregate classes
    P = pd.DataFrame(points)
    rcols = [f"r_{names[k]}" for k in free]
    classes = {}
    for _, row in P[P["ok"]].iterrows():
        cid = row["class_id"]
        r = tuple(row[c] for c in rcols)
        res = evaluate(gammas_of(r))
        c = classes.setdefault(cid, dict(class_id=cid, label=res["label"], faces_present=list(res["faces_present"]),
                                         example_habit=res["habit"], n_scan_points=0, area_min={}, area_max={},
                                         members=[], contains_favoured=False, contains_bfdh=False))
        if row["kind"] in ("grid", "sample"):
            c["n_scan_points"] += 1
        c["contains_favoured"] |= row["kind"] == "favoured"
        c["contains_bfdh"] |= row["kind"] == "bfdh"
        for f, v in res["area_fractions"].items():
            if v >= face_min:
                c["area_min"][f] = min(c["area_min"].get(f, 1.0), v)
                c["area_max"][f] = max(c["area_max"].get(f, 0.0), v)
        c["members"].append(r)
    n_ok_scan = int(P.iloc[:n_scan]["ok"].sum()) if n_scan else 0

    # ---------------------------------------------------------------- distances (structure-specific part)
    for cid, c in classes.items():
        c["map_fraction"] = c["n_scan_points"] / n_ok_scan if n_ok_scan else 0.0
        if not fav_ok:
            mean = np.exp(np.mean(np.log(np.array(c["members"])), axis=0))      # central point of the class
            r = min(c["members"], key=lambda m: float(np.sum((np.log(m) - np.log(mean)) ** 2)))
            c.update(rep_gammas=gammas_of(r), spread=np.nan, lower_face=None, raise_face=None)
            continue
        if c["contains_favoured"]:
            c.update(rep_gammas=dict(g0), spread=0.0, lower_face=None, raise_face=None)
            continue
        cand = sorted(c["members"], key=lambda m: ratio_change(gammas_of(m), g0, keys)[0])[:3]
        best = None
        for m in cand:
            p = gammas_of(m)
            lo_t, hi_t = 0.0, 1.0
            for _ in range(refine_steps):
                mid = 0.5 * (lo_t + hi_t)
                q = {k: g0[k] ** (1 - mid) * p[k] ** mid for k in keys}
                rq = evaluate(q)
                if rq["ok"] and rq["class_id"] == cid:
                    hi_t = mid
                else:
                    lo_t = mid
            q = {k: g0[k] ** (1 - hi_t) * p[k] ** hi_t for k in keys}
            chk = evaluate(q)
            if not (chk["ok"] and chk["class_id"] == cid):          # safety: keep the scanned point
                q = p
            s, lw, rs = ratio_change(q, g0, keys)
            if best is None or s < best[0]:
                best = (s, lw, rs, q)
        s, lw, rs, q = best
        c.update(rep_gammas=q, spread=s, lower_face=names[lw], raise_face=names[rs])

    order = sorted(classes.values(), key=lambda c: (np.nan_to_num(c["spread"], nan=9e9), -c["map_fraction"]))
    for i, c in enumerate(order):
        c["rank"] = i
        c["min_ratio_change_pct"] = round(pct(c["spread"]), 1) if np.isfinite(c["spread"]) else None
        c["rep_ratios"] = {names[k]: round(c["rep_gammas"][k] / c["rep_gammas"][ref], 4) for k in free}
        c.pop("members")

    bf_info = None
    if gb is not None:
        bf_info = dict(gammas={names[k]: v for k, v in gb.items()}, ratios=dict(zip([names[k] for k in free], ratios_of(gb))),
                       ok=bf["ok"], habit=bf.get("habit"), class_id=bf.get("class_id"),
                       area_fractions=bf.get("area_fractions"))
        if fav_ok:
            s, lw, rs = ratio_change(gb, g0, keys)
            bf_info.update(ratio_change_from_favoured_pct=round(pct(s), 1), lower_face=names[lw], raise_face=names[rs])

    favoured = dict(defined=fav_ok, gammas={names[k]: v for k, v in g0.items()},
                    ratios=dict(zip([names[k] for k in free], ratios_of(g0))) if fav_ok else None)
    if fav_ok:
        favoured.update(ok=fav["ok"], habit=fav.get("habit"), class_id=fav.get("class_id"),
                        area_fractions=fav.get("area_fractions"), reason=fav.get("reason"))
    else:
        favoured["reason"] = "gamma <= 0 (or ~0) for " + ", ".join(names[k] for k in keys if g0[k] <= GAMMA_MIN)
    warnings_ = []
    if fav_ok:
        med = float(np.median(list(g0.values())))
        tiny = [names[k] for k in keys if g0[k] < 0.05 * med]
        if tiny:
            warnings_.append(f"gamma of {tiny} is < 5 % of the median face: that face is almost free to form, "
                             "so the favoured point sits far from the others and distances become very large. "
                             "Check that slab (relaxation, healing) before using these numbers.")

    out = dict(faces=[names[k] for k in keys], face_keys=keys, ref_face=names[ref], axes=[names[k] for k in free],
               crystal_system=crystal_system, method=method, range=(lo, hi), step=step if method == "grid" else None,
               n_scan_points=n_scan, n_failed=len(failures), failure_examples=failures[:5],
               favoured=favoured, bfdh=bf_info, classes=order, unique_habits=[c["class_id"] for c in order],
               seconds=round(time.time() - t0, 1), points=P if keep_points else None, closed_shape=closed is True,
               warnings=warnings_)
    if log:
        log(f"   spectrum: {len(keys)} faces {out['faces']}, {method} {n_scan} points "
            f"({len(failures)} failed) -> {len(order)} shape classes in {out['seconds']} s")
    return out


# ============================================================================ E: outputs
def _clean(o):
    """JSON-safe copy: numpy -> python, NaN/inf -> None, tuples/sets -> lists."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_clean(v) for v in o]
    if isinstance(o, np.generic):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, (str, int, float, bool)) or o is None:
        return o
    return str(o)


def plot_map(res, path, title=""):
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    P = res["points"]
    cls = res["classes"]
    cmap20 = matplotlib.colormaps["tab20"]
    color = {c["class_id"]: cmap20(i % 20) for i, c in enumerate(cls)}
    idx = {c["class_id"]: i for i, c in enumerate(cls)}
    axes = [f"r_{a}" for a in res["axes"]]
    ref = res["ref_face"]
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    scan = P[P["kind"].isin(["grid", "sample"])]
    if res["method"] == "grid" and len(axes) == 2:
        xs, ys = np.sort(scan[axes[0]].unique()), np.sort(scan[axes[1]].unique())
        Z = np.full((len(ys), len(xs)), np.nan)
        xi = {v: i for i, v in enumerate(xs)}; yi = {v: i for i, v in enumerate(ys)}
        for _, r in scan.iterrows():
            if r["ok"]:
                Z[yi[r[axes[1]]], xi[r[axes[0]]]] = idx[r["class_id"]]
        cm = ListedColormap([color[c["class_id"]] for c in cls])
        ax.pcolormesh(xs, ys, np.ma.masked_invalid(Z), cmap=cm, vmin=-0.5, vmax=len(cls) - 0.5, shading="nearest")
        ax.set_xlabel(f"γ{res['axes'][0]} / γ{ref}"); ax.set_ylabel(f"γ{res['axes'][1]} / γ{ref}")
        xcol, ycol = axes
    elif len(axes) == 1:
        xs = np.sort(scan[axes[0]].unique())
        Z = np.array([[idx.get(scan[scan[axes[0]] == x]["class_id"].iloc[0], np.nan)
                       if scan[scan[axes[0]] == x]["ok"].iloc[0] else np.nan for x in xs]])
        cm = ListedColormap([color[c["class_id"]] for c in cls])
        ax.pcolormesh(xs, [0, 1], np.vstack([Z, Z]), cmap=cm, vmin=-0.5, vmax=len(cls) - 0.5, shading="nearest")
        ax.set_yticks([]); ax.set_xlabel(f"γ{res['axes'][0]} / γ{ref}")
        xcol, ycol = axes[0], None
    else:
        # 3+ ratio axes cannot be drawn as a map: show what matters instead, each class's distance from the
        # favoured shape (or, with no favoured point, its share of the scanned space)
        plt.close(fig)
        n = len(cls)
        fig, ax = plt.subplots(figsize=(8.6, max(3.0, 0.32 * n + 1.2)))
        fav_def = any(c["min_ratio_change_pct"] is not None for c in cls)
        vals = [(c["min_ratio_change_pct"] if fav_def else 100 * c["map_fraction"]) or 0.0 for c in cls]
        ys = np.arange(n)[::-1]
        bars = ax.barh(ys, vals, color=[color[c["class_id"]] for c in cls], edgecolor="none")
        for y, c, v in zip(ys, cls, vals):
            tag = "  favoured" if c["contains_favoured"] else ""
            tag += "  BFDH" if c["contains_bfdh"] else ""
            ax.text(v, y, f" {v:.1f}%{tag}", va="center", fontsize=7)
        ax.set_yticks(ys); ax.set_yticklabels([c["class_id"] for c in cls], fontsize=7)
        ax.set_xlabel("smallest change in a γ ratio that reaches the class (%)" if fav_def
                      else "share of the scanned ratio space (%)  [no favoured point: γ <= 0]")
        if fav_def and max(vals) > 0:
            ax.set_xscale("symlog", linthresh=10); ax.set_xlim(0, max(vals) * 3)
        ax.set_title(title + f"\n{len(axes)} ratio axes ({', '.join(res['axes'])} / {ref}): shown as distance from the favoured shape",
                     fontsize=8)
        fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
        return str(path)
    for kind, mk, fc, lab in (("bfdh", "^", "white", "BFDH (1/d_eff)"), ("favoured", "*", "black", "favoured (computed γ)")):
        q = P[P["kind"] == kind]
        if len(q):
            yv = q[ycol].iloc[0] if ycol else 0.5
            ax.scatter([q[xcol].iloc[0]], [yv], marker=mk, s=220 if mk == "*" else 110, c=fc,
                       edgecolors="black", linewidths=1.0, zorder=5, label=lab)
    handles = [plt.Rectangle((0, 0), 1, 1, color=color[c["class_id"]]) for c in cls]
    labels = [c["class_id"] + (f"  ({c['min_ratio_change_pct']:.0f}%)" if c["min_ratio_change_pct"] is not None else "")
              for c in cls]
    l1 = ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=7, frameon=False,
                   title="shape class (min γ-ratio change)", title_fontsize=7)
    ax.add_artist(l1)
    ax.legend(loc="lower left", bbox_to_anchor=(1.01, 0.0), fontsize=7, frameon=False)
    ax.set_title(title, fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return str(path)


def write_outputs(res, out_dir, name, conv, families, rotations, gamma_source, notes=(), max_images=8):
    """favoured_morphology.json, morphology_spectrum.json/.csv, spectrum_map.png, Wulff images, log."""
    d = Path(out_dir) / "spectrum" / f"{_tag(name)}__{_tag(gamma_source)}"     # one folder per MOF and gamma source
    d.mkdir(parents=True, exist_ok=True)
    fams = [f for f in families if f["key"] in res["face_keys"]]
    key_of = {f["name"]: f["key"] for f in fams}
    files = {}
    fav = res["favoured"]
    favj = dict(mof=name, gamma_source=gamma_source, faces=res["faces"], map_axes=res["axes"], ref_face=res["ref_face"],
                favoured_defined=fav["defined"], gamma_J_m2=fav["gammas"], map_coordinates=fav.get("ratios"),
                habit=fav.get("habit"), class_id=fav.get("class_id"), area_fractions=fav.get("area_fractions"),
                reason=fav.get("reason"), bfdh=res["bfdh"], warnings=res.get("warnings", []), notes=list(notes) + [
                    "Structure only: shapes reachable by changing relative energies of the listed low-index faces. "
                    "Solvent, temperature and additives are not modelled."])
    (d / "favoured_morphology.json").write_text(json.dumps(_clean(favj), indent=1, allow_nan=False)); files["favoured_json"] = str(d / "favoured_morphology.json")
    rows = []
    for c in res["classes"]:
        rows.append(dict(rank=c["rank"], class_id=c["class_id"], label=c["label"], faces_present="+".join(c["faces_present"]),
                         is_favoured=c["contains_favoured"], contains_bfdh=c["contains_bfdh"],
                         map_fraction=round(c["map_fraction"], 4), min_ratio_change_pct=c["min_ratio_change_pct"],
                         lower_face=c["lower_face"], raise_face=c["raise_face"],
                         representative_ratios=json.dumps(c["rep_ratios"]),
                         area_fraction_ranges=json.dumps({f: [round(c["area_min"][f], 3), round(c["area_max"][f], 3)]
                                                          for f in sorted(c["area_min"], key=_face_order)}),
                         example_habit=c["example_habit"]))
    table = pd.DataFrame(rows)
    table.to_csv(d / "morphology_spectrum.csv", index=False); files["spectrum_csv"] = str(d / "morphology_spectrum.csv")
    specj = {k: v for k, v in res.items() if k not in ("points",)}
    specj["classes"] = [{k: v for k, v in c.items() if k != "rep_gammas"} | {"rep_gammas": {n: c["rep_gammas"][key_of[n]] for n in key_of}}
                        for c in res["classes"]]
    specj["mof"] = name; specj["gamma_source"] = gamma_source
    (d / "morphology_spectrum.json").write_text(json.dumps(_clean(specj), indent=1, allow_nan=False))
    files["spectrum_json"] = str(d / "morphology_spectrum.json")
    if res["points"] is not None:
        res["points"].to_csv(d / "spectrum_points.csv", index=False)
        files["map_png"] = plot_map(res, d / "spectrum_map.png",
                                    f"{name}: morphology spectrum ({gamma_source} γ, {res['method']}, {res['n_scan_points']} points)")
    if fav["defined"] and fav.get("ok"):
        w = mw.wulff(conv, fams, {key_of[n]: v for n, v in fav["gammas"].items()}, rotations)
        files["favoured_png"] = mw.render(w, fams, f"{name} favoured ({gamma_source})\n{fav['habit']}", d / "wulff_favoured.png")
        mw.write_obj(w, d / "wulff_favoured.obj"); files["favoured_obj"] = str(d / "wulff_favoured.obj")
    files["class_pngs"] = []
    for c in res["classes"][:max_images]:
        w = mw.wulff(conv, fams, c["rep_gammas"], rotations)
        tag = f"wulff_{c['rank']:02d}_{_tag(c['label'])}.png"
        sub = f"min change {c['min_ratio_change_pct']}%" if c["min_ratio_change_pct"] is not None else ""
        files["class_pngs"].append(mw.render(w, fams, f"{c['class_id']}\n{sub}", d / tag))
    logtxt = [f"MOF {name} | gamma source {gamma_source}", f"faces {res['faces']} (ref {res['ref_face']}, axes {res['axes']})",
              f"favoured gamma {fav['gammas']} -> {fav.get('habit') or fav.get('reason')}",
              f"method {res['method']} range {res['range']} step {res['step']} points {res['n_scan_points']} "
              f"failed {res['n_failed']} closed-shape check skipped {res['closed_shape']}",
              f"{len(res['classes'])} shape classes: " + "; ".join(res["unique_habits"]),
              f"time {res['seconds']} s"] + [f"failure example: {f}" for f in res["failure_examples"]] + list(notes) \
             + [f"WARNING: {w}" for w in res.get("warnings", [])]
    (d / "spectrum_log.txt").write_text("\n".join(logtxt)); files["log"] = str(d / "spectrum_log.txt")
    files["dir"] = str(d)
    return table, files


# ============================================================================ D: entry points
def _gammas_from_rows(rows, cap="water", mode="relaxed"):
    """Lowest gamma per family from slab rows (CSV-safe: NaN -> None, 'True' -> True)."""
    clean = []
    for r in rows:
        r = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in r.items()}
        cv = r.get("converged")
        r["converged"] = cv is True or (isinstance(cv, str) and cv.strip().lower() == "true") or cv == 1
        clean.append(r)
    best = mw.choose_gamma(clean, cap, need_relaxed=(mode == "relaxed"))
    return {k: b["gamma"] for k, b in best.items()}, best


def spectrum_from_pipeline(out_dir, mof, gamma_mode="relaxed", cap="water", grid=DEFAULT_GRID, max_samples=4096,
                           max_images=8, write=True, log=print):
    """Spectrum for a MOF the pipeline already computed (reads the cache; no new CHGNet).
    gamma_mode: 'relaxed' (converged relaxed gamma, as in step 8) or 'static'."""
    out_dir = Path(out_dir)
    meta = G.load_meta(out_dir, mof)
    conv, fams, rots = G._families_from_meta(meta)
    if (out_dir / "slabs_all.csv").exists():
        df = pd.read_csv(out_dir / "slabs_all.csv")
    else:
        parts = [pd.read_csv(out_dir / f) for f in ("slabs.csv", "slabs_train.csv", "slabs_static.csv") if (out_dir / f).exists()]
        if not parts:
            raise FileNotFoundError(f"no slabs CSV in {out_dir}")
        df = pd.concat(parts, ignore_index=True)
    rows = df[df["mof"] == mof].to_dict("records")
    if not rows:
        raise ValueError(f"{mof}: no slab rows in the results CSVs")
    gam, best = _gammas_from_rows(rows, cap, gamma_mode)
    tbl = G.bfdh_for_mof(out_dir, mof)
    gb = {k: 1.0 / v["d_eff"] for k, v in tbl.items()} if tbl else None
    notes = [] if tbl else ["BFDH point missing: the CIF for this MOF is not in this session (run cell 3, or upload it)."]
    missing = [f["name"] for f in fams if f["key"] not in gam]
    if missing:
        notes.append(f"faces without a {gamma_mode} gamma (left out of the map): {missing}")
    res = scan_morphology_map(conv, fams, rots, meta["crystal_system"], gam, gb, grid, max_samples, log=log)
    table, files = write_outputs(res, out_dir, mof, conv, fams, rots, f"CHGNet {gamma_mode}", notes, max_images) if write else (None, {})
    return _package(res, table, files, notes)


def run_spectrum(cif, name, out_dir, gamma_source="gnn", models=None, train_elements=None, gnn_target="gamma",
                 engine=None, pipeline_cfg=None, symprec=0.1, disorder="majority", max_index=1, n_families=4,
                 grid=DEFAULT_GRID, max_samples=4096, max_images=8, log=print):
    """One CIF -> favoured shape + every shape class its faces can produce + distances.

    gamma_source: 'gnn'    steps 1-5 + the trained GNN (seconds; needs models from mofgnn.load_models)
                  'chgnet' full pipeline steps 1-6 via mofwulff.run_mof (slow, cached; needs engine + pipeline_cfg)
                  'bfdh'   geometry only, gamma ~ 1/d_eff (instant)
    No solvent / temperature / additive arguments, by design."""
    notes = []
    if gamma_source == "gnn":
        if not models:
            raise ValueError("gamma_source='gnn' needs models (mofgnn.load_models)")
        df, summ, w, meta = G.predict_mof(models, name, cif, target=gnn_target, train_elements=train_elements,
                                          symprec=symprec, disorder=disorder, max_index=max_index, n_families=n_families)
        conv, fams, rots = G._families_from_meta(meta)
        gam = summ["gammas"]
        gb = {k: 1.0 / v["d_eff"] for k, v in meta["bfdh"].items()}
        notes += [f"GNN warning: {x}" for x in summ["warnings"]]
        cs = meta["crystal_system"]
    elif gamma_source == "chgnet":
        if engine is None or pipeline_cfg is None:
            raise ValueError("gamma_source='chgnet' needs engine (mofwulff.Engine()) and pipeline_cfg (settings dict)")
        meta, fams, recs, bulk = mw.run_mof(engine, name, cif, out_dir, **pipeline_cfg)
        conv = _dummy_conv(meta["conv_lattice"]); rots = [np.array(r) for r in meta["_rotations"]]
        mode = "relaxed" if pipeline_cfg.get("relax_steps", mw.DEFAULTS.get("relax_steps", 0)) else "static"
        gam, best = _gammas_from_rows(recs, pipeline_cfg.get("cap", "water"), mode)
        tbl = G.bfdh_for_mof(out_dir, name)
        gb = {k: 1.0 / v["d_eff"] for k, v in tbl.items()} if tbl else None
        cs = meta["crystal_system"]
        notes.append(f"CHGNet gamma ({mode})")
    elif gamma_source == "bfdh":
        info = mw.standardize(cif, symprec, disorder)
        fams = mw.face_families(info["conv"], info["rotations"], max_index, n_families)
        tbl = G.d_eff_table(info, fams)
        gam = {k: 1.0 / v["d_eff"] for k, v in tbl.items()}
        gb = dict(gam)
        conv = _dummy_conv(info["conv"].lattice.matrix.tolist()); rots = info["rotations"]
        cs = info["crystal_system"]
        notes.append("BFDH: gamma taken proportional to 1/d_eff (geometry only, no energies)")
    else:
        raise ValueError(f"gamma_source must be 'gnn', 'chgnet' or 'bfdh', not {gamma_source!r}")
    res = scan_morphology_map(conv, fams, rots, cs, gam, gb, grid, max_samples, log=log)
    label = f"CHGNet {mode}" if gamma_source == "chgnet" else gamma_source    # same folder name as 14c
    table, files = write_outputs(res, out_dir, name, conv, fams, rots, label, notes, max_images)
    return _package(res, table, files, notes)


def _package(res, table, files, notes):
    fav = res["favoured"]
    notes = list(notes) + [f"WARNING: {w}" for w in res.get("warnings", [])]
    return dict(favoured=fav, unique_habits=res["unique_habits"], classes=res["classes"], table=table,
                grid_points=res["points"], map_coordinates_of_favoured=fav.get("ratios"), face_list=res["faces"],
                gamma_dict=fav["gammas"], bfdh=res["bfdh"], files=files, notes=list(notes), result=res)


# ============================================================================ G: tests
def _cubic_setup():
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    st = Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.64), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    rots = []
    for op in SpacegroupAnalyzer(st).get_symmetry_operations():
        R = np.round(op.rotation_matrix).astype(int)
        if not any(np.array_equal(R, q) for q in rots):
            rots.append(R)
    return st, mw.face_families(st, rots, faces=[(1, 0, 0), (1, 1, 0), (1, 1, 1)]), rots


def _tetragonal_setup():
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    st = Structure.from_spacegroup("I4/mmm", Lattice.tetragonal(10.0, 14.0), ["Zn", "O"], [[0, 0, 0], [0, 0, 0.3]])
    rots = []
    for op in SpacegroupAnalyzer(st).get_symmetry_operations():
        R = np.round(op.rotation_matrix).astype(int)
        if not any(np.array_equal(R, q) for q in rots):
            rots.append(R)
    return st, mw.face_families(st, rots, 1, 4), rots


def run_self_tests(cifs=(), verbose=True):
    """Spec section G. cifs: optional [(path, expected BFDH habit label)] for real-structure checks."""
    say = print if verbose else (lambda *a: None)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail)); say(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

    st, fams, rots = _cubic_setup()
    K = {f["name"]: f["key"] for f in fams}
    one = lambda a, b, c: {K["{100}"]: a, K["{110}"]: b, K["{111}"]: c}
    r = wulff_from_gammas(st, fams, one(1.0, 2.0, 2.0), rots, "cubic")
    check("pure cube gamma -> cube, only {100}", r["ok"] and r["label"] == "cube" and r["faces_present"] == ("{100}",), r.get("class_id"))
    r = wulff_from_gammas(st, fams, one(2.0, 2.0, 1.0), rots, "cubic")
    check("pure octahedron gamma -> octahedron, only {111}", r["ok"] and r["label"] == "octahedron" and r["faces_present"] == ("{111}",), r.get("class_id"))
    r = wulff_from_gammas(st, fams, one(2.0, 1.0, 2.0), rots, "cubic")
    check("pure dodecahedron gamma -> rhombic_dodecahedron", r["ok"] and r["label"] == "rhombic_dodecahedron", r.get("class_id"))
    r = wulff_from_gammas(st, fams, one(1.0, 2.0, 2 / math.sqrt(3)), rots, "cubic")
    check("R111/R100 = 2/sqrt3 -> cuboctahedron (project note, Step 11)", r["ok"] and r["label"] == "cuboctahedron", r.get("class_id"))
    r = wulff_from_gammas(st, fams, one(1.0, 1.0, -0.1), rots, "cubic")
    check("gamma <= 0 -> clean refusal, no crash", not r["ok"] and "gamma <= 0" in r["reason"], r.get("reason"))

    fav = one(1.0, 1.4, 0.85)                       # a truncated octahedron
    grid = (0.3, 2.5, 0.1)
    s1 = scan_morphology_map(st, fams, rots, "cubic", fav, None, grid, log=None)
    labels = {c["label"] for c in s1["classes"]}
    need = {"cube", "octahedron", "rhombic_dodecahedron", "truncated_octahedron", "truncated_cube"}
    check("cubic spectrum contains cube, octahedron, dodecahedron and both truncations", need <= labels, sorted(labels))
    check("favoured point is a truncated octahedron at distance 0",
          s1["favoured"]["habit"] == "truncated_octahedron" and s1["classes"][0]["contains_favoured"] and s1["classes"][0]["spread"] == 0.0)
    cube = next(c for c in s1["classes"] if c["label"] == "cube")
    check("cube is reached by making {100} cheaper relative to {111}",
          cube["lower_face"] == "{100}" or cube["raise_face"] == "{111}",
          f"{cube['min_ratio_change_pct']}%: lower {cube['lower_face']}, raise {cube['raise_face']}")
    ok_rep = all(wulff_from_gammas(st, fams, c["rep_gammas"], rots, "cubic")["class_id"] == c["class_id"] for c in s1["classes"])
    check("every class's representative gamma vector really gives that class", ok_rep)
    # independent check: walk gamma{111} up from the favoured point until the shape is called a cube
    lo_y, hi_y = fav[K["{111}"]], 3.0
    for _ in range(40):
        mid = 0.5 * (lo_y + hi_y)
        rr = wulff_from_gammas(st, fams, one(1.0, max(1.4, 1.5), mid), rots, "cubic")
        lo_y, hi_y = (lo_y, mid) if rr["ok"] and rr["label"] == "cube" else (mid, hi_y)
    direct = (hi_y / fav[K["{111}"]] - 1) * 100
    check("cube distance <= the change found by a direct 1-D walk (scan finds the shortest route)",
          cube["min_ratio_change_pct"] <= direct * 1.01, f"scan {cube['min_ratio_change_pct']}% vs direct walk {direct:.1f}%")
    # geometry check against the analytic result: {111} vanishes from a {100}+{111} crystal at R111/R100 = sqrt3
    lo_y, hi_y = 1.0, 3.0
    for _ in range(40):
        mid = 0.5 * (lo_y + hi_y)
        rr = wulff_from_gammas(st, fams, one(1.0, 2.0, mid), rots, "cubic")
        lo_y, hi_y = (lo_y, mid) if rr["area_fractions"].get("{111}", 0.0) < 1e-9 else (mid, hi_y)
    check("Wulff geometry: {111} vanishes exactly at gamma111/gamma100 = sqrt3 (analytic 1.7321)",
          abs(hi_y - math.sqrt(3)) < 1e-3, f"{hi_y:.4f}")
    check("the named cube boundary (< 5 % {111}) comes before the full vanishing point",
          cube["min_ratio_change_pct"] < (math.sqrt(3) / 0.85 - 1) * 100, f"{cube['min_ratio_change_pct']}% < 103.8%")
    s2 = scan_morphology_map(st, fams, rots, "cubic", fav, None, grid, log=None)
    same = [(c["class_id"], c["n_scan_points"], c["min_ratio_change_pct"]) for c in s1["classes"]] == \
           [(c["class_id"], c["n_scan_points"], c["min_ratio_change_pct"]) for c in s2["classes"]]
    check("same gamma twice -> identical spectrum", same)
    try:
        scan_morphology_map(st, fams, rots, "cubic", {K["{100}"]: 1.0}, None, grid, log=None)
        check("one face only -> clear error", False)
    except ValueError as e:
        check("one face only -> clear error", "at least 2 face families" in str(e), str(e)[:70])
    s3 = scan_morphology_map(st, fams, rots, "cubic", one(1.0, 1.2, -0.05), None, grid, log=None)
    check("favoured gamma <= 0 -> spectrum still listed, no distances",
          not s3["favoured"]["defined"] and len(s3["classes"]) >= 5 and all(c["min_ratio_change_pct"] is None for c in s3["classes"]))
    st2 = scan_morphology_map(st, fams, rots, "cubic", {K["{100}"]: 1.0, K["{111}"]: 0.9}, None, grid, log=None)
    check("two faces -> 1-D scan runs", st2["method"] == "grid" and len(st2["axes"]) == 1 and len(st2["classes"]) >= 3,
          [c["label"] for c in st2["classes"]])

    tst, tfams, trots = _tetragonal_setup()
    tg = {f["key"]: 1.0 + 0.1 * i for i, f in enumerate(tfams)}
    t0 = time.time()
    s4 = scan_morphology_map(tst, tfams, trots, "tetragonal", tg, None, grid, max_samples=1024, log=None)
    check(f"non-cubic ({len(tfams)} faces, {len(tfams) - 1}-D) Sobol scan runs", s4["method"] == "sobol" and len(s4["classes"]) >= 2,
          f"{len(s4['classes'])} classes, {s4['n_scan_points']} points, {time.time() - t0:.0f} s")

    banned = []
    for fn in (scan_morphology_map, run_spectrum, spectrum_from_pipeline):
        banned += [f"{fn.__name__}({p})" for p in inspect.signature(fn).parameters if any(b in p.lower() for b in FORBIDDEN_ARGS)]
    check("no solvent / temperature / additive arguments in the API", not banned, banned)

    for path, expect in cifs:
        if not Path(path).exists():
            say(f"SKIP {path} (not found)"); continue
        with tempfile.TemporaryDirectory() as tmp:
            out = run_spectrum(path, Path(path).stem, tmp, gamma_source="bfdh", grid=(0.3, 2.5, 0.1), max_images=2, log=None)
            got = out["favoured"].get("habit")
            check(f"{Path(path).name}: BFDH favoured shape = {expect}", G.habit_class(got) == expect,
                  f"{got}; {len(out['unique_habits'])} classes; files written: {sorted(k for k in out['files'] if k != 'class_pngs')}")
    n_fail = sum(not ok for _, ok, _ in results)
    say(f"\n{len(results) - n_fail}/{len(results)} tests passed")
    return results


# ============================================================================ notebook helpers
def _rows_all(out_dir):
    out_dir = Path(out_dir)
    if (out_dir / "slabs_all.csv").exists():
        return pd.read_csv(out_dir / "slabs_all.csv")
    parts = [pd.read_csv(out_dir / f) for f in ("slabs.csv", "slabs_train.csv", "slabs_static.csv") if (out_dir / f).exists()]
    if not parts:
        raise FileNotFoundError(f"no slabs CSV in {out_dir}")
    return pd.concat(parts, ignore_index=True)


def spectra_for_pipeline(out_dir, mofs=None, gamma_mode="relaxed", cap="water", grid=DEFAULT_GRID, max_samples=4096,
                         max_images=8, log=print):
    """Spectrum for every MOF already computed by the pipeline (cached gamma, no new CHGNet).
    mofs: list of names; None = every MOF with a gamma for at least 2 faces in gamma_mode.
    Returns (summary DataFrame, {mof: result}); the summary is also saved as spectrum/spectrum_summary_<mode>.csv."""
    out_dir = Path(out_dir)
    df = _rows_all(out_dir)
    if not mofs:
        mofs = []
        for m, g in df.groupby("mof"):
            if len(_gammas_from_rows(g.to_dict("records"), cap, gamma_mode)[0]) >= 2:
                mofs.append(m)
        mofs = sorted(mofs)
    rows, specs = [], {}
    for i, m in enumerate(mofs):
        try:
            o = spectrum_from_pipeline(out_dir, m, gamma_mode, cap, grid, max_samples, max_images, log=None)
        except Exception as e:
            rows.append(dict(mof=m, favoured_shape=f"skipped: {type(e).__name__}: {e}"[:160]))
            if log: log(f"[{i + 1}/{len(mofs)}] {m}: skipped ({e})")
            continue
        specs[m] = o
        fav, cls = o["favoured"], o["classes"]
        alt = next((c for c in cls if not c["contains_favoured"] and c["min_ratio_change_pct"] is not None), None)
        b = o["bfdh"] or {}
        rows.append(dict(mof=m, faces="+".join(o["face_list"]),
                         favoured_shape=fav.get("habit") if fav["defined"] else f"none: {fav['reason']}",
                         n_shape_classes=len(cls),
                         closest_alternative=alt["class_id"] if alt else None,
                         closest_change_pct=alt["min_ratio_change_pct"] if alt else None,
                         closest_how=f"lower {alt['lower_face']} vs {alt['raise_face']}" if alt else None,
                         bfdh_shape=b.get("habit"), bfdh_change_pct=b.get("ratio_change_from_favoured_pct")))
        if log: log(f"[{i + 1}/{len(mofs)}] {m}: {rows[-1]['favoured_shape']} | {len(cls)} classes")
    S = pd.DataFrame(rows)
    (out_dir / "spectrum").mkdir(exist_ok=True)
    S.to_csv(out_dir / "spectrum" / f"spectrum_summary_{gamma_mode}.csv", index=False)
    return S, specs


def show(spec, max_images=8):
    """Print and display one spectrum result in a notebook."""
    from IPython.display import Image, display
    fav = spec["favoured"]
    print("Faces used:", spec["face_list"])
    print("Favoured shape:", fav.get("habit") if fav["defined"] else f"none ({fav['reason']})")
    print("gamma used:", {k: round(v, 4) for k, v in fav["gammas"].items()})
    b = spec["bfdh"]
    if b:
        extra = f" | {b['ratio_change_from_favoured_pct']}% gamma-ratio change from the favoured point" \
            if b.get("ratio_change_from_favoured_pct") is not None else ""
        print("BFDH shape:", b.get("habit"), extra)
    for n in spec["notes"]:
        print("note:", n)
    print(f"\n{len(spec['unique_habits'])} shape classes this face set can produce "
          "(min_ratio_change_pct = smallest change in a gamma ratio that reaches the class):")
    display(spec["table"][["rank", "class_id", "is_favoured", "contains_bfdh", "min_ratio_change_pct",
                           "lower_face", "raise_face", "map_fraction"]])
    f = spec["files"]
    if f.get("map_png"):
        display(Image(f["map_png"]))
    if f.get("favoured_png"):
        display(Image(f["favoured_png"], width=320))
    for pth in f.get("class_pngs", [])[:max_images]:
        display(Image(pth, width=260))
    print("files:", f.get("dir"))