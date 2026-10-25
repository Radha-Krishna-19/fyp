"""Growth-rate models that turn a set of faces into a shape.

All models produce the same kind of object, a polytope P = {x : n_f . x <= R_f}; they differ
only in how the face distances R_f are chosen (primer, Sections 6-8 and 14).
"""
import math
import numpy as np
from .faces import families, plain, family_label
from .shape import Shape


def _labels(faces):
    return {F["family"]: F["label"] for F in families(faces)}


def _planes(faces, rate_of_family, families_used):
    lab = _labels(faces)
    normals, dists, tags = [], [], []
    for f in faces.values():
        key = f.family
        if key in families_used:
            normals.append(f.normal); dists.append(rate_of_family[key]); tags.append(lab[key])
    return normals, dists, tags


def _match(label, rates_by_label):
    """'{111}+' matches a rate given for '{111}+' or, failing that, for '{111}'."""
    if label in rates_by_label:
        return rates_by_label[label]
    base = label.rstrip("+-")
    return rates_by_label.get(base)


def bfdh(faces, n_families=10):
    """BFDH: R_hkl proportional to 1/d_eff. Uses the n_families with largest d_eff."""
    fams = families(faces)[:n_families]
    dmax = fams[0]["d_eff"]
    rate = {F["family"]: dmax / F["d_eff"] for F in fams}       # leading family at distance 1
    n, d, t = _planes(faces, rate, set(rate))
    return Shape(n, d, t), rate


def from_rates(faces, rates_by_label):
    """rates_by_label: {'{111}': 1.0, '{100}': 1.2, ...} using plain family labels."""
    rate = {}
    for F in families(faces):
        r = _match(F["label"], rates_by_label)
        if r is not None:
            rate[F["family"]] = r
    n, d, t = _planes(faces, rate, set(rate))
    return Shape(n, d, t)


def attachment_rates(c_by_label, beta):
    """Graph rule: R_f = exp(beta * c_f), c_f = attachment number (links formed by a new node).
    beta ~ (energy per link)/(kT); beta -> 0 makes all rates equal, large beta makes the
    slowest face dominate completely."""
    return {k: math.exp(beta * c) for k, c in c_by_label.items()}


def fibonacci_sphere(n=300):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


def grow_from_seed(faces, rates_by_label, time, r0=1.0, v_rough=None, n_sphere=400):
    """Shape at time t of a crystal grown from a spherical seed of radius r0.
    Listed faces move at their rates; all other (rough) directions move at v_rough
    (default 1.5 x the fastest listed rate), so they disappear quickly."""
    rate = {}
    for F in families(faces):
        r = _match(F["label"], rates_by_label)
        if r is not None:
            rate[F["family"]] = r
    lab = _labels(faces)
    v_rough = v_rough or 1.5 * max(rate.values())
    normals, dists, tags = [], [], []
    for f in faces.values():
        if f.family in rate:
            normals.append(f.normal); dists.append(r0 + rate[f.family] * time); tags.append(lab[f.family])
    for n in fibonacci_sphere(n_sphere):
        normals.append(n); dists.append(r0 + v_rough * time); tags.append("rough")
    return Shape(normals, dists, tags)


def describe(shape, min_frac=1e-9):
    """Name the shape from the faces whose area fraction exceeds min_frac (exact by default)."""
    fr = shape.face_fractions()
    rough = fr.get("rough", 0.0)
    if rough > 0.5:
        return "ball (mostly rough surface)"
    if rough > 0.05:
        return "rounded " + shape_name_without_rough(shape, min_frac)
    return shape_name_without_rough(shape, min_frac)


def shape_name_without_rough(shape, min_frac=1e-9):
    fr, cnt = {}, {}
    tot_all = sum(f["area"] for f in shape.faces if f["tag"] != "rough")
    keep = {}
    for f in shape.faces:
        if f["tag"] != "rough":
            keep[f["tag"]] = keep.get(f["tag"], 0) + f["area"]
    keep = {k for k, v in keep.items() if v / tot_all > min_frac}
    for f in shape.faces:
        if f["tag"] == "rough" or f["tag"] not in keep:
            continue
        fr[f["tag"]] = fr.get(f["tag"], 0) + f["area"]; cnt[f["tag"]] = cnt.get(f["tag"], 0) + 1
    tot = sum(fr.values()); fr = {k: v / tot for k, v in fr.items()}
    cnt = {k: cnt[k] for k in fr}
    # tetrahedral halves
    if set(fr) in ({"{111}+"}, {"{111}-"}) and sum(cnt.values()) == 4:
        return "tetrahedron"
    if set(fr) == {"{111}+", "{111}-"}:
        return "octahedron" if abs(fr["{111}+"] - fr["{111}-"]) < 0.02 else "truncated tetrahedron"
    if {"{111}+", "{111}-"} <= set(fr) or {"{111}+"} <= set(fr) or {"{111}-"} <= set(fr):
        merged = {}
        for k, v in fr.items():
            merged[k.rstrip("+-")] = merged.get(k.rstrip("+-"), 0) + v
        if abs(fr.get("{111}+", 0) - fr.get("{111}-", 0)) > 0.02:
            return "tetrahedral " + _basic(merged, shape, cnt).replace("truncated octahedron","trunc. octahedron")
        fr = merged
    return _basic(fr, shape, cnt)


def _basic(fr, shape, cnt):
    keys = set(fr); nv = len(shape.V)
    c = {}
    for k, v in cnt.items():
        c[k.rstrip("+-")] = c.get(k.rstrip("+-"), 0) + v
    if keys == {"{100}"} and c.get("{100}") == 6: return "cube"
    if keys == {"{111}"} and c.get("{111}") == 8: return "octahedron"
    if keys == {"{110}"} and c.get("{110}") == 12: return "rhombic dodecahedron"
    # named by face SHAPE, not by which family has more area: a {111} face that is a
    # triangle means cube corners were cut (truncated cube); a hexagon means octahedron
    # corners were cut (truncated octahedron)
    def corners(base):
        return max([len(f["poly"]) for f in shape.faces if f["tag"].rstrip("+-") == base and f["tag"] in cnt] or [0])
    if keys == {"{100}", "{111}"}:
        if nv == 12: return "cuboctahedron"
        return "truncated octahedron" if corners("{111}") >= 6 else "truncated cube"
    if keys == {"{100}", "{110}"}:
        # one combinatorial type throughout (6 squares, 12 hexagons, a chamfered cube),
        # so here the larger family names it
        return "truncated rhombic dodecahedron" if fr["{110}"] > fr["{100}"] else "chamfered cube"
    if keys == {"{100}", "{110}", "{111}"}:
        return "rhombicuboctahedron-like"
    return " + ".join(sorted(keys))
