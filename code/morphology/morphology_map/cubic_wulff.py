"""Exact Wulff shape of a cubic (m-3m) crystal bounded by {100}, {110} and {111}, and its class.

A face family F with surface energy g_F contributes the planes n.x = g_F for every unit normal n of F
(6, 12 and 8 planes). The Wulff shape is the intersection of the half-spaces n.x <= g_F. A family is
present when its planes keep a face of non-zero area.

Only ratios matter: the shape depends on x = g110/g100 and y = g111/g100.
Closed-form limits (derived in the report):
  {100} only (cube)                  iff  y >= sqrt3   and  x >= sqrt2
  {111} only (octahedron)            iff  y <= 1/sqrt3 and  x >= sqrt(3/2) * y
  {110} only (rhombic dodecahedron)  iff  x <= 1/sqrt2 and  y >= sqrt(3/2) * x
  {100}+{111} with no {110}: cuboctahedron at y = 2/sqrt3 exactly;
      truncated cube for 2/sqrt3 < y < sqrt3, truncated octahedron for 1/sqrt3 < y < 2/sqrt3.
"""
import itertools
import numpy as np
from scipy.spatial import HalfspaceIntersection

S2, S3 = 2 ** 0.5, 3 ** 0.5


def _normals():
    fam = {"100": set(), "110": set(), "111": set()}
    for base, key in (((1, 0, 0), "100"), ((1, 1, 0), "110"), ((1, 1, 1), "111")):
        for p in itertools.permutations(base):
            for s in itertools.product((1, -1), repeat=3):
                fam[key].add(tuple(a * b for a, b in zip(p, s)))
    return {k: np.array(sorted(v), float) / np.linalg.norm(sorted(v)[0]) for k, v in fam.items()}


NORMALS = _normals()          # 6, 12, 8 unit normals


def wulff_areas(g100, g110, g111):
    """Area fraction of each family on the Wulff shape (exact up to floating point)."""
    planes, keys = [], []
    for k, g in (("100", g100), ("110", g110), ("111", g111)):
        for n in NORMALS[k]:
            planes.append(np.r_[n, -g]); keys.append(k)
    planes = np.array(planes)
    V = HalfspaceIntersection(planes, np.zeros(3)).intersections
    V = np.unique(np.round(V, 9), axis=0)
    area = {"100": 0.0, "110": 0.0, "111": 0.0}
    for p, k in zip(planes, keys):
        n, g = p[:3], -p[3]
        on = V[np.abs(V @ n - g) < 1e-7 * max(1.0, g)]
        if len(on) < 3:
            continue
        c = on.mean(0); u = on[0] - c; u /= np.linalg.norm(u); w = np.cross(n, u)
        poly = on[np.argsort(np.arctan2((on - c) @ w, (on - c) @ u))]
        a = 0.5 * abs(np.dot(sum(np.cross(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))), n))
        area[k] += a
    tot = sum(area.values())
    return {k: v / tot for k, v in area.items()}


def classify(fr, tol=0.01, y=None):
    """Shape class from area fractions. tol: smallest fraction counted as a face (1 %, the convention of the project's earlier shape tables).
    For {100}+{111} shapes the cuboctahedron is the single line y = 2/sqrt3; pass y to split
    truncated cube / truncated octahedron exactly, otherwise the {100} fraction 0.634 of the
    cuboctahedron is used as the dividing value."""
    has = {k for k, v in fr.items() if v > tol}
    if has == {"100"}: return "cube"
    if has == {"111"}: return "octahedron"
    if has == {"110"}: return "rhombic_dodecahedron"
    if has == {"100", "111"}:
        if y is not None:
            if abs(y - 2 / S3) < 2e-3: return "cuboctahedron"
            return "truncated_cube" if y > 2 / S3 else "truncated_octahedron"
        return "truncated_cube" if fr["100"] > 0.634 else "truncated_octahedron"
    if has == {"100", "110"}:
        return "cube_truncated_edges" if fr["100"] >= fr["110"] else "truncated_rhombic_dodecahedron"
    if has == {"110", "111"}:
        return "rd_truncated_by_111" if fr["110"] >= fr["111"] else "octahedron_truncated_by_110"
    return "all_three_families"


def shape(g100, g110, g111, tol=0.01):
    fr = wulff_areas(g100, g110, g111)
    return classify(fr, tol, y=g111 / g100 if fr["110"] <= tol else None), fr


if __name__ == "__main__":
    # self-test against the closed-form limits
    tests = [((1, 2, 2), "cube"), ((1, 2, S3 + 1e-3), "cube"), ((1, 2, 1.5), "truncated_cube"),
             ((1, 2, 2 / S3), "cuboctahedron"), ((1, 2, 0.8), "truncated_octahedron"), ((1, 2, 0.5), "octahedron"),
             ((1, 0.7, 1.0), "rhombic_dodecahedron"), ((1, 1.2, 2), "cube_truncated_edges"),
             ((1, 0.8, 2), "truncated_rhombic_dodecahedron")]
    for (a, b, c), want in tests:
        got, fr = shape(a, b, c)
        print(f"{(a, b, round(c, 4))}: {got:32s} want {want:32s} {'OK' if got == want else 'FAIL'}  {dict((k, round(v, 3)) for k, v in fr.items())}")
    fr = wulff_areas(1, 2, 2 / S3); print("cuboctahedron {100} fraction", round(fr["100"], 4), "(exact 6/(6+2*sqrt3) =", round(6 / (6 + 2 * S3), 4), ")")
