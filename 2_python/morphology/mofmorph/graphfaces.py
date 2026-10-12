"""Phase 3: crystal faces from the periodic graph.

A labelled quotient graph (vertices with positions in one cell, edges (i, j, t)
carrying the lattice translation t) is enough to compute, for any face (hkl),
three graph quantities, all of them EXACT (no finite cluster):

  E_att(hkl)  attachment number per growth unit: when one slice of thickness d
              (the face's effective spacing) attaches to the crystal, the number
              of links formed per vertex of the slice. Hartman-Bennema: growth
              rate R is proportional to it.
  gamma(hkl)  broken-bond surface energy: links cut per unit area by the
              cutting plane. Wulff: face distance is proportional to it.
  rank(hkl)   periodicity rank of the slice: the dimension of the lattice of
              translations carried by cycles of links INSIDE one slice.
              2 = F face (flat), 1 = S face (stepped), 0 = K face (kinked):
              the Hartman-Perdok classes, measured with the periodicity rank
              used in our earlier work.

The slice boundary (termination) is chosen to minimise E_att, the usual rule
that a crystal face exposes the cut through the fewest bonds.

How the exact counting works. Translate the whole framework by a lattice vector
R and every height n.x shifts by n.R, which runs over the multiples k*D of the
lattice-plane spacing D along n. Lattice points on one height level have
in-plane density D/V (V = cell volume). So any count "per unit area" is
(D/V) times a sum over vertices or edges of ONE cell of the number of integers k
that put the translated copy where it is wanted.
"""
from __future__ import annotations
import math
from fractions import Fraction
from functools import reduce
import numpy as np


# ---------------------------------------------------------------------------
# the periodic graph
# ---------------------------------------------------------------------------
class PeriodicGraph:
    """lattice: rows = cell vectors (Angstrom or any unit), positions: Cartesian
    positions of the vertices of one cell, edges: list of (i, j, t) meaning vertex
    i in cell 0 is linked to vertex j in cell t. kinds: optional vertex labels."""

    def __init__(self, lattice, positions, edges, kinds=None):
        self.L = np.asarray(lattice, float)
        self.X = np.asarray(positions, float)
        self.edges = [(int(i), int(j), tuple(int(x) for x in t)) for i, j, t in edges]
        self.kinds = kinds or ["v"] * len(self.X)
        self.V = abs(np.linalg.det(self.L))
        self.B = np.linalg.inv(self.L).T          # rows = reciprocal vectors (no 2 pi)

    def edge_vector(self, e):
        i, j, t = e
        return self.X[j] + np.asarray(t) @ self.L - self.X[i]

    def degrees(self):
        d = [0] * len(self.X)
        for i, j, _t in self.edges:
            d[i] += 1; d[j] += 1
        return d

    def lattice_spacing(self, n):
        """Spacing D of lattice planes perpendicular to the unit vector n: the
        reciprocal-lattice vector parallel to n with the smallest length is 1/D."""
        m = self.L @ n                              # components of n in the reciprocal basis
        k = np.argmax(np.abs(m))
        m = m / m[k]
        fr = [Fraction(float(x)).limit_denominator(48) for x in m]
        den = reduce(lambda a, b: a * b // math.gcd(a, b), [f.denominator for f in fr], 1)
        ints = [int(f * den) for f in fr]
        g = reduce(math.gcd, [abs(x) for x in ints if x] or [1])
        ints = np.array([x // g for x in ints], float)
        G = ints @ self.B
        assert np.allclose(np.cross(G, n), 0, atol=1e-6 * np.linalg.norm(G)), "n is not a lattice direction"
        return 1.0 / np.linalg.norm(G)


def contract_two_connected(G: PeriodicGraph, keep_kinds=("node",)):
    """Standard topological deconstruction: a vertex of degree 2 that is not a
    node (a ditopic linker) is replaced by a single edge joining its two
    neighbours. Linkers with three or more connections stay as vertices.
    Returns a new PeriodicGraph over the remaining vertices."""
    deg = G.degrees()
    drop = [k not in keep_kinds and deg[v] == 2 for v, k in enumerate(G.kinds)]
    nbr = {v: [] for v in range(len(G.X))}
    for i, j, t in G.edges:
        nbr[i].append((j, np.array(t))); nbr[j].append((i, -np.array(t)))
    keep = [v for v in range(len(G.X)) if not drop[v]]
    new_id = {v: k for k, v in enumerate(keep)}
    edges, seen = [], set()
    for i, j, t in G.edges:
        for a, b, tt in ((i, j, np.array(t)), (j, i, -np.array(t))):
            if drop[a] or not drop[b]:
                continue
            # a kept, b dropped: follow b to its other neighbour
            others = [(c, tc) for c, tc in nbr[b] if not (c == a and np.array_equal(tc, -tt))]
            if len(others) != 1:
                continue
            c, tc = others[0]
            if drop[c]:
                continue
            T = tuple(int(x) for x in (tt + tc))
            key = (new_id[a], new_id[c], T)
            rkey = (new_id[c], new_id[a], tuple(-x for x in T))
            if key in seen or rkey in seen:
                continue
            seen.add(key); edges.append(key)
    for i, j, t in G.edges:
        if not drop[i] and not drop[j]:
            edges.append((new_id[i], new_id[j], t))
    return PeriodicGraph(G.L, G.X[keep], edges, [G.kinds[v] for v in keep])


# ---------------------------------------------------------------------------
# exact slice quantities
# ---------------------------------------------------------------------------
def _count_k(lo, hi, D):
    """Number of integers k with lo < k*D <= hi."""
    return max(0, math.floor(hi / D + 1e-9) - math.floor(lo / D + 1e-9))


def _vertices_in_slice(h, h0, d, D):
    # vertex at height h + kD lies in (h0, h0 + d]
    return _count_k(h0 - h, h0 + d - h, D)


def face_quantities(G: PeriodicGraph, n, d, terminations=None):
    """For the face with unit normal n and slice thickness d, return a dict with
    E_att, gamma and the chosen termination h0, evaluated exactly.

    terminations: candidate boundary heights; default = midpoints between the
    distinct vertex heights within one period D (any boundary between two
    consecutive vertex levels cuts the same links)."""
    n = np.asarray(n, float); n = n / np.linalg.norm(n)
    D = G.lattice_spacing(n)
    h = (G.X @ n) % D
    if terminations is None:
        lv = np.unique(np.round(h, 6))
        lv = np.concatenate([lv, [lv[0] + D]])
        terminations = [(lv[k] + lv[k + 1]) / 2 for k in range(len(lv) - 1)]
    dens = D / G.V
    out = []
    for h0 in terminations:
        nv = sum(_vertices_in_slice(hi, h0, d, D) for hi in h)          # vertices per surface cell in slice
        if nv == 0:
            continue
        att = 0      # links with one end in the slice and the other at or below h0
        cut = 0      # links crossing the plane at h0
        for e in G.edges:
            i, j, _t = e
            hi = G.X[i] @ n
            hj = hi + G.edge_vector(e) @ n
            lo, hi_ = (hi, hj) if hi <= hj else (hj, hi)
            # copies shifted by kD: lower end <= h0 < upper end
            cut += _count_k(h0 - hi_, h0 - lo, D)
            # upper end in (h0, h0+d] and lower end <= h0
            k_lo = max(h0 - hi_, h0 - hi_)                              # upper end > h0
            # integers k with h0 < hi_+kD <= h0+d and lo+kD <= h0
            a = max(h0 - hi_, -1e300); b = min(h0 + d - hi_, h0 - lo)
            if b > a:
                att += _count_k(a, b, D)
        out.append(dict(h0=h0, E_att=att / nv, gamma=cut * dens, slice_vertices=nv, D=D))
    best = min(out, key=lambda r: (round(r["E_att"], 9), r["gamma"]))
    best["all_terminations"] = [(round(r["h0"], 4), round(r["E_att"], 4), round(r["gamma"], 6)) for r in out]
    best["gamma_min"] = min(r["gamma"] for r in out)
    return best


# ---------------------------------------------------------------------------
# periodicity rank of one slice (Hartman-Perdok class)
# ---------------------------------------------------------------------------
def slice_rank(G: PeriodicGraph, n, d, h0, reach=4):
    """Dimension of the lattice of translations carried by paths of links that
    stay inside one slice (h0, h0 + d]. 2 -> F, 1 -> S, 0 -> K."""
    n = np.asarray(n, float); n = n / np.linalg.norm(n)
    rng = range(-reach, reach + 1)
    verts = {}
    for a in rng:
        for b in rng:
            for c in rng:
                cell = np.array([a, b, c])
                off = cell @ G.L
                for i, x in enumerate(G.X):
                    hh = (x + off) @ n
                    if h0 < hh <= h0 + d + 1e-9:
                        verts[(i, a, b, c)] = len(verts)
    if not verts:
        return 0
    adj = [[] for _ in verts]
    for (i, a, b, c), u in verts.items():
        for (p, q, t) in G.edges:
            for s, o, tt in ((p, q, t), (q, p, tuple(-x for x in t))):
                if s != i:
                    continue
                key = (o, a + tt[0], b + tt[1], c + tt[2])
                if key in verts:
                    adj[u].append(verts[key])
    # components, then translations between copies of the same quotient vertex
    keys = list(verts)
    comp = [-1] * len(keys); rank = 0
    for s in range(len(keys)):
        if comp[s] >= 0:
            continue
        stack = [s]; comp[s] = s; members = []
        while stack:
            u = stack.pop(); members.append(u)
            for w in adj[u]:
                if comp[w] < 0:
                    comp[w] = s; stack.append(w)
        by_vertex = {}
        for u in members:
            i, a, b, c = keys[u]
            by_vertex.setdefault(i, []).append((a, b, c))
        vecs = []
        for cells in by_vertex.values():
            c0 = np.array(cells[0])
            vecs += [np.array(cc) - c0 for cc in cells[1:]]
        if vecs:
            rank = max(rank, int(np.linalg.matrix_rank(np.array(vecs, float))))
    return rank


FSK = {2: "F", 1: "S", 0: "K"}


def classify(G: PeriodicGraph, n, d):
    q = face_quantities(G, n, d)
    r = slice_rank(G, n, d, q["h0"])
    q["rank"] = r; q["class"] = FSK.get(r, "?")
    return q
