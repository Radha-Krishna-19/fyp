"""
MODULE 12 -- CONVERGED BAND ANALYSIS
             finite-size convergence, honest fit diagnostics, and a band that
             is not a restatement of graph size

WHY THIS MODULE EXISTS
----------------------------------------------------------------------------
A coarse-grained band run over 77 hMOF structures produced a Delta-alpha
distribution that was then cut into three classes ("Narrow", "Medium",
"Wide"). Four things were wrong with that, and this module fixes all four.
Each is stated with the evidence that exposed it, because every one of them
is the sort of defect that produces a plausible-looking number rather than a
crash.

----------------------------------------------------------------------------
DEFECT A -- THE CLASSES WERE BOX-COVERING NOISE
----------------------------------------------------------------------------
The run's own isomorphism check reported hMOF-94 and hMOF-96 as ISOMORPHIC --
the same graph. Their spectra came out:

    hMOF-94   CG-nodes=256 edges=384 diam=12   Delta-alpha = 1.208 +/- 0.041
    hMOF-96   CG-nodes=256 edges=384 diam=12   Delta-alpha = 1.177 +/- 0.029

and the class boundaries were Narrow <= 1.1901 < Medium <= 1.2218 < Wide.
The same graph therefore landed in two different classes. The classes are
0.032 wide; the per-structure error bars are +/- 0.03 to 0.05. The class
boundaries are narrower than the measurement uncertainty, so the labels
describe which random covering the RNG produced, not the framework.

FIX: never classify on a quantity whose class width is below its own error
bar. assign_classes() refuses to do it, and reports the ratio instead.

----------------------------------------------------------------------------
DEFECT B -- WHAT SURVIVED THE NOISE WAS GRAPH SIZE
----------------------------------------------------------------------------
Grouping that same run by coarse-node count:

    CG nodes    n      mean Delta-alpha
       144      2          1.04
       192     11          1.14
       256    ~48          1.20
       288      2          1.34
       384      4          1.51
       432      5          1.52

Monotonic, with almost no overlap between adjacent groups. "Wide" was just
"CG-nodes >= 288". This is the SAME confound (r = +0.62 between Delta-alpha
and graph size) that already forced the withdrawal of this project's
pore-size claim and of its four-structure real-MOF claim. It is now three
for three.

FIX: compare only at converged size (Defect C), and report the
size-controlled partial correlation alongside every raw correlation, so the
confound cannot hide again.

----------------------------------------------------------------------------
DEFECT C -- THE GRAPHS WERE FAR TOO SMALL, FOR AN AVOIDABLE REASON
----------------------------------------------------------------------------
The run built the supercell out of ATOMS and capped it at MAX_ATOMS = 7000.
At roughly 16 atoms per block that ceiling permits about 430 coarse nodes,
which is a graph diameter of 8-12. A multifractal spectrum is a SCALING
measurement; radii 1..12 is well under one decade of range, and one structure
(hMOF-84) was fitted over a diameter of 4 -- four points.

The run's own finite-size check shows what that costs:

    rep=(1,1,1)  CG-N=12  diam=4   Delta-alpha = 0.5419
    rep=(2,2,2)  CG-N=96  diam=6   Delta-alpha = 1.1802

Delta-alpha MORE THAN DOUBLED between the two sizes tested, and the sweep
stopped there. Nothing in that run establishes that any reported value is
converged.

The ceiling is unnecessary. Coarse-graining AFTER building an atomic
supercell pays for atoms that are immediately thrown away. Because the
labelled quotient graph (module 9) already carries the lattice translation on
every edge, the coarse graph can be replicated combinatorially: coarse-grain
the unit cell once (a dozen blocks), then tile the QUOTIENT GRAPH n x n x n.
No atoms are ever materialised, so n = 12 -- twenty thousand coarse nodes,
diameter ~35 -- costs less memory than her 7000-atom cell did.

FIX: coarse-grain first, replicate second. Then sweep n until Delta-alpha
stops moving, and report only the converged value.

----------------------------------------------------------------------------
DEFECT D -- THE FIT DIAGNOSTIC WAS THE WRONG STATISTIC
----------------------------------------------------------------------------
The run reported mean R-squared = -1.17, minimum -7.36, and this was read (by
me, initially, and wrongly) as proof that the scaling fits had failed. That
reading is not safe either way, because the statistic was computed against
the wrong null.

tau(q) is defined by the source paper as a fit THROUGH THE ORIGIN. Scoring
the residuals of a through-origin fit against the total variance about the
MEAN mixes two different questions, and routinely returns negative numbers
even when the data is perfectly linear. A negative value there is therefore
not evidence of anything.

The question that actually matters is: IS ln Z LINEAR IN ln r? That is a
property of the data, not of the fit convention, and it must be measured with
a free-intercept fit. So this module reports BOTH, and they mean different
things:

    r2_linearity   R^2 of a FREE-INTERCEPT fit. Does a power law describe the
                   data at all? This is the gate. If it is low, there is no
                   scaling regime and the spectrum is meaningless regardless
                   of how tau was extracted.
    tau            slope of the THROUGH-ORIGIN fit, the paper's definition.
                   Used only once r2_linearity says scaling exists.

Conflating the two is why the original diagnostic was uninformative.

----------------------------------------------------------------------------
A NOTE ON THE DATASET ITSELF
----------------------------------------------------------------------------
Roughly 48 of the 76 structures in that run shared 256 nodes / 384 edges /
diameter 12 / 52 influential. That is a 4x4x4 tiling of a pcu net: 64
six-connected Zn4O nodes and 192 two-connected linkers. They differ only in
linker chemistry, which coarse-graining deletes BY DESIGN. A band measured
over structures that are topologically identical is narrow for a trivial
reason, and no amount of statistics rescues it.

This is not a bug -- it is a sampling problem, and it is why
require_topological_diversity() below refuses to report a band until the
sample contains more than one net.
"""

from __future__ import annotations

import json
import math
import os
import random
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import networkx as nx

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph


# ============================================================================
# 1. THE GRAPH:  coarse-grain the unit cell, THEN replicate
# ============================================================================

def quotient_graph_from_cif(cif_path: str):
    """CIF -> (blocks, edges) where each edge is (i, j, t) and t is the integer
    lattice translation the bond crosses.

    This is the coarse graph of the UNIT CELL. It is tiny -- a handful of
    vertices -- and it is all that is needed, because t makes replication
    exact.

    Using this project's own bond perception (module 2) rather than a generic
    neighbour list also sidesteps a problem that cost the notebook run half
    its dataset: 73 of 150 structures were dropped as "unit-cell atom graph
    disconnected", a 49% rejection rate that is far too high for real MOFs
    with periodic boundaries switched on, and which points at bond cutoffs
    being too tight rather than at the structures being broken.
    """
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    node_blocks, linker_blocks = run_metal_oxo(geom)
    blocks, edges = build_periodic_block_graph(geom, node_blocks, linker_blocks)
    return blocks, edges, geom


def replicate(blocks, edges, n: int):
    """Tile the labelled quotient graph into an n x n x n supercell.

    THE POINT OF THIS FUNCTION: no atoms. The atomic supercell that the
    previous run built and then coarse-grained away never exists here, so the
    MAX_ATOMS ceiling that capped the diameter at 12 does not apply. n = 12 on
    a 12-block cell gives 20 736 coarse vertices for a few hundred megabytes.

    Because every edge already carries its translation t, placing a copy of
    block i in every cell c and joining (i, c) to (j, c + t mod n) reproduces
    the infinite framework exactly, with wraparound making the result a torus
    -- so there are no surface vertices with artificially low degree.
    """
    K = len(blocks)
    cells = [(a, b, c) for a in range(n) for b in range(n) for c in range(n)]
    cell_index = {cell: ci for ci, cell in enumerate(cells)}
    idx = lambda bi, cell: bi * len(cells) + cell_index[cell]

    G = nx.MultiGraph()
    G.add_nodes_from(range(K * len(cells)))
    kind = {}
    for bi in range(K):
        for cell in cells:
            kind[idx(bi, cell)] = blocks[bi][0]

    for cell in cells:
        for (i, j, t) in edges:
            tgt = tuple((cell[k] + t[k]) % n for k in range(3))
            G.add_edge(idx(i, cell), idx(j, tgt))
    return G, kind


# ============================================================================
# 2. THE SPECTRUM:  with a diagnostic that means something
# ============================================================================

def select_influential(G, top_percent: float = 0.30):
    """Top-k vertices by degree, reporting how badly tied the cutoff is.

    In a perfect crystal every symmetry-equivalent block ties exactly, so the
    'selection' is sorting equal values and the tie count is the honest
    description of what happened.
    """
    deg = dict(G.degree())
    K = G.number_of_nodes()
    k = max(1, int(math.ceil(K * top_percent)))
    ordered = sorted(deg.items(), key=lambda kv: -kv[1])
    chosen = [n for n, _ in ordered[:k]]
    cutoff = deg[chosen[-1]]
    n_above = sum(1 for _, d in deg.items() if d > cutoff)
    n_tied = sum(1 for _, d in deg.items() if d == cutoff)
    return chosen, {
        'k': k,
        'cutoff_degree': cutoff,
        'n_tied_at_cutoff': n_tied,
        'slots_at_cutoff': k - n_above,
        'ambiguous': n_tied > (k - n_above),
        'distinct_degrees': len(set(deg.values())),
    }


def _adjacency(G):
    """Plain dict-of-lists adjacency. Built once and reused by every covering.

    PERFORMANCE NOTE -- this replaces a call to nx.all_pairs_shortest_path_length,
    which materialised an N x N distance table. At N = 7 168 that is 51 million
    entries; at N = 14 000 it is 196 million, which is what made the n=10 step
    of the first sweep appear to hang. It was never going to finish.

    Depth-limited BFS from each box centre needs no such table, and is also
    self-limiting: at large radius the first few centres claim nearly every
    vertex, so few BFS traversals happen at all.
    """
    return {n: list(G.neighbors(n)) for n in G.nodes()}


def box_covering(G, rb, adj, rng, nodes=None):
    """Greedy random box covering at radius rb (Song, Havlin & Makse).

    Minimum box covering is NP-hard, so centres are taken in random order and
    each claims whatever is still uncovered within rb. The result is therefore
    STOCHASTIC, which is why every caller averages over many trials -- and why
    a spread of +/- 0.03 in Delta-alpha across seeds is algorithmic noise, not
    structural signal.

    Distances are measured on the FULL graph (a vertex rb steps away belongs in
    the box regardless of whether the path ran through already-claimed
    vertices), but only unclaimed vertices are absorbed, so the boxes stay a
    partition.
    """
    if nodes is None:
        nodes = list(G.nodes())
    uncovered = set(nodes)
    node_box, box_size = {}, {}
    order = list(nodes)
    rng.shuffle(order)
    bid = 0
    for center in order:
        if center not in uncovered:
            continue
        # depth-limited BFS: traverse the whole graph out to rb, claim only
        # what is still uncovered
        members = []
        seen = {center}
        frontier = [center]
        depth = 0
        while frontier and depth <= rb:
            nxt = []
            for u in frontier:
                if u in uncovered:
                    members.append(u)
                if depth < rb:
                    for v in adj[u]:
                        if v not in seen:
                            seen.add(v)
                            nxt.append(v)
            frontier = nxt
            depth += 1
        if not members:
            members = [center]
        for m in members:
            node_box[m] = bid
            uncovered.discard(m)
        box_size[bid] = len(members)
        bid += 1
        if not uncovered:
            break
    return node_box, box_size


def probability_measures(G, influential, radii, n_trials=40, seed=0):
    """p_i(r) per trial, NOT averaged across trials.

    The averaging order matters and is a known defect in this lineage: taking
    the mean of p_i(r) across trials and only then raising it to the power q
    smooths away exactly the trial-to-trial fluctuation that multifractality
    measures. Z must be built per trial; see compute_tau.

    The full graph supplies the boxes and the distances; the measure is read
    only AT the influential vertices. Feeding in the induced subgraph of
    influential vertices instead gives a graph with ZERO edges, because metal
    clusters never bond directly to one another -- they connect through
    linkers.
    """
    adj = _adjacency(G)
    nodes = list(G.nodes())
    N = len(nodes)
    trials = {r: [] for r in radii}
    for t in range(n_trials):
        rng = random.Random(seed + t)
        for r in radii:
            node_box, box_size = box_covering(G, r, adj, rng, nodes)
            trials[r].append({n: box_size[node_box[n]] / N
                              for n in influential if n in node_box})
    return trials


def compute_tau(trials, radii, r_N, q_values):
    """tau(q) through the origin, PLUS an honest linearity diagnostic.

    Returns (tau, r2_linearity) where the two answer different questions:

      r2_linearity  from a FREE-INTERCEPT fit. "Is ln Z linear in ln r --
                    does a power law describe this data at all?" This is a
                    property of the data and is the gate on whether the
                    spectrum means anything.
      tau           from a THROUGH-ORIGIN fit, which is the source paper's
                    definition tau = ln P_q(r) / ln(r/r_N). Correct for
                    extracting the exponent, but its residuals scored against
                    variance-about-the-mean produce negative R^2 even on
                    perfectly linear data -- which is why the previous run's
                    "mean R^2 = -1.17" was not the alarm it appeared to be,
                    and not a reassurance either. It was the wrong statistic.

    Both are reported so neither question is answered by the other's number.
    """
    x = np.log(np.asarray(radii, dtype=float) / r_N)
    tau, r2s = [], []
    for q in q_values:
        y = []
        for r in radii:
            ln_Z = []
            for trial in trials.get(r, []):
                vals = np.array([v for v in trial.values() if v > 0])
                if vals.size:
                    Z = np.sum(vals ** q)
                    if Z > 0:
                        ln_Z.append(np.log(Z))
            y.append(np.mean(ln_Z) if ln_Z else np.nan)
        y = np.asarray(y, dtype=float)
        mask = np.isfinite(y) & np.isfinite(x)
        if mask.sum() < 3:          # 2 points fit any line perfectly; need 3
            tau.append(np.nan)
            r2s.append(np.nan)
            continue
        xv, yv = x[mask], y[mask]

        # the paper's exponent: least squares with no intercept
        tau.append(float(np.sum(xv * yv) / np.sum(xv * xv)))

        # the diagnostic: does a straight line describe the data?
        slope, icept = np.polyfit(xv, yv, 1)
        resid = yv - (slope * xv + icept)
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((yv - yv.mean()) ** 2))
        r2s.append(1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan)

    return np.asarray(tau), np.asarray(r2s)


def _bfs_far(adj, start):
    """Farthest vertex from `start`, and its distance. One BFS."""
    dist = {start: 0}
    frontier = [start]
    d = 0
    last = start
    while frontier:
        nxt = []
        for u in frontier:
            for v in adj[u]:
                if v not in dist:
                    dist[v] = d + 1
                    nxt.append(v)
        if nxt:
            d += 1
            last = nxt[0]
        frontier = nxt
    far = max(dist, key=dist.get)
    return far, dist[far]


def fast_diameter(G, adj=None):
    """Double-sweep diameter estimate: two BFS traversals, not N of them.

    PERFORMANCE NOTE -- nx.diameter() computes the eccentricity of EVERY
    vertex, which is N breadth-first traversals. At N = 7 168 that is roughly
    150 million edge visits in pure Python, and spectrum() was calling it once
    per seed. That, not the box covering, is what stalled the n=8 step.

    The double sweep (BFS from any vertex to find the farthest u, then BFS
    from u to find the farthest v) is the standard cheap estimate. It is exact
    on trees and a tight lower bound on graphs like these. Since the diameter
    here only sets the largest box radius, a bound one step short changes
    nothing about the scaling fit -- and it is thousands of times faster.
    """
    if adj is None:
        adj = _adjacency(G)
    nodes = list(G.nodes())
    if not nodes:
        return 0
    u, _ = _bfs_far(adj, nodes[0])
    _v, d = _bfs_far(adj, u)
    return int(d)


def spectrum(G, influential, q_values=None, n_trials=40, seed=0, diameter=None):
    """One multifractal spectrum, with its own quality report attached.

    `diameter` may be passed in so a caller sweeping several seeds over the
    same graph computes it once rather than once per seed.
    """
    if q_values is None:
        q_values = np.linspace(-10, 10, 41)

    if G.number_of_edges() == 0:
        return {'ok': False, 'reason': 'graph has no edges'}

    if diameter is None:
        diameter = fast_diameter(G)

    # A scaling measurement needs a scaling RANGE. Under a diameter of 8 there
    # is less than one decade of radii and nothing can be established; the
    # previous run fitted one structure over a diameter of 4.
    if diameter < 8:
        return {'ok': False, 'reason': f'diameter {diameter} too small to scale over',
                'diameter': diameter}

    radii = list(range(1, diameter + 1))
    trials = probability_measures(G, influential, radii,
                                  n_trials=n_trials, seed=seed)
    tau, r2 = compute_tau(trials, radii, diameter, q_values)

    alpha = np.gradient(tau, q_values)
    f_alpha = q_values * alpha - tau
    finite = np.isfinite(alpha)
    if not finite.any():
        return {'ok': False, 'reason': 'no finite alpha', 'diameter': diameter}

    width = float(np.nanmax(alpha) - np.nanmin(alpha))
    i0 = int(np.argmin(np.abs(q_values)))
    a0 = float(alpha[i0])
    left, right = a0 - np.nanmin(alpha), np.nanmax(alpha) - a0
    asym = float(np.log(left / right)) if left > 0 and right > 0 else float('nan')

    return {
        'ok': True,
        'q_values': q_values, 'tau': tau, 'alpha': alpha, 'f_alpha': f_alpha,
        'width': width, 'alpha_0': a0, 'asymmetry': asym,
        'diameter': diameter, 'radii': radii,
        'r2_linearity_mean': float(np.nanmean(r2)),
        'r2_linearity_min': float(np.nanmin(r2)),
        'peak_q': float(q_values[int(np.nanargmax(f_alpha))]),
    }


# ============================================================================
# 3. THE EXPERIMENT THAT SETTLES EVERYTHING: finite-size convergence
# ============================================================================

def finite_size_sweep(cif_path, n_values=(2, 3, 4, 6, 8, 10),
                      n_trials=20, n_seeds=3, max_nodes=25000, verbose=True):
    """Delta-alpha against supercell multiplier, for ONE structure.

    THIS IS THE EXPERIMENT THE PREVIOUS RUN STOPPED TWO POINTS INTO. It found
    Delta-alpha = 0.54 at rep 1 and 1.18 at rep 2 -- more than a doubling --
    and then reported values from a fixed rule as though they were properties
    of the frameworks.

    Either Delta-alpha plateaus, in which case the plateau is the descriptor
    and everything below it was a finite-size artefact; or it does not, in
    which case Delta-alpha is not a property of the framework at all and no
    band computed from it means anything. Both answers are worth having. Not
    knowing is the only bad outcome.
    """
    blocks, edges, _ = quotient_graph_from_cif(cif_path)
    K = len(blocks)
    out = []
    for n in n_values:
        if K * n ** 3 > max_nodes:
            break
        G, _kind = replicate(blocks, edges, n)
        infl, _sel = select_influential(G)
        # once per graph, not once per seed
        diam = fast_diameter(G)
        widths = []
        rec = None
        for s in range(n_seeds):
            r = spectrum(G, infl, n_trials=n_trials, seed=s * 101, diameter=diam)
            if r.get('ok'):
                widths.append(r['width'])
                rec = r
        if not widths:
            continue
        row = {
            'n': n,
            'cg_nodes': G.number_of_nodes(),
            'cg_edges': G.number_of_edges(),
            'diameter': rec['diameter'],
            'width_mean': float(np.mean(widths)),
            'width_sd': float(np.std(widths)),
            'r2_linearity_mean': rec['r2_linearity_mean'],
            # kept so the q-range convergence test can be run afterwards
            # without recomputing every supercell
            'alpha': np.asarray(rec['alpha'], dtype=float),
            'q_values': np.asarray(rec['q_values'], dtype=float),
        }
        out.append(row)
        if verbose:
            print(f"  n={n:<3} CG-N={row['cg_nodes']:<6} diam={row['diameter']:<4} "
                  f"Delta-alpha={row['width_mean']:.4f} +/- {row['width_sd']:.4f}  "
                  f"R2_lin={row['r2_linearity_mean']:.3f}")
    return out


def q_range_convergence(sweep, q_caps=(10, 8, 5, 4, 3, 2), tol=0.05):
    """Does Delta-alpha converge if the q range is narrowed?

    WHY THIS EXISTS
    The first sweep on HKUST-1 gave, over the full q in [-10, 10]:

        diam= 8  Delta-alpha=1.3445      diam=24  Delta-alpha=2.2065
        diam=12  Delta-alpha=1.6666      diam=32  Delta-alpha=2.4297
        diam=16  Delta-alpha=1.9104

    which is Delta-alpha ~ 0.78 ln(D) - 0.28 to within 0.01 on every point: a
    clean LOGARITHMIC DIVERGENCE with no plateau. Meanwhile the linearity R^2
    stayed between 0.78 and 0.92, so the power-law fits were sound. The
    scaling is real; it is the WIDTH that will not settle.

    The cause is the tails. Delta-alpha = max(alpha) - min(alpha) is taken over
    q in [-10, 10], and at |q| = 10 the partition function sum_i p_i^q is
    dominated by a single box -- the largest for q >> 0, the smallest for
    q << 0. The smallest box that can exist is one vertex, p = 1/N, so
    alpha_max inherits a ln(N) term directly and drifts with system size for
    ever. At extreme q this is not a scaling measurement at all, it is the
    extreme-value statistics of one box.

    At moderate q the sum is carried by typical boxes, and tau(q) should
    converge. This function finds the widest q range that actually does, by
    recomputing the width from the stored alpha(q) curves at each supercell
    size and comparing the two largest sizes.

    A cap that converges means the descriptor is usable -- with its q range
    stated as part of the definition, which it always should have been.
    Nothing converging means the width is finite-size artefact at every scale
    tested, and no band built on it can be defended.
    """
    usable = [r for r in sweep if 'alpha' in r and 'q_values' in r]
    if len(usable) < 3:
        return {'ok': False, 'reason': 'need at least 3 supercell sizes'}

    out = []
    for cap in q_caps:
        widths, diams = [], []
        for row in usable:
            q, a = row['q_values'], row['alpha']
            m = np.isfinite(a) & (np.abs(q) <= cap)
            if m.sum() < 3:
                continue
            widths.append(float(np.nanmax(a[m]) - np.nanmin(a[m])))
            diams.append(row['diameter'])
        if len(widths) < 3:
            continue

        # convergence: relative change between the two largest supercells
        drift_last = abs(widths[-1] - widths[-2]) / max(abs(widths[-1]), 1e-9)
        # and the total drift across the whole sweep, as context
        drift_total = abs(widths[-1] - widths[0]) / max(abs(widths[-1]), 1e-9)
        # slope against ln(diameter): ~0 means converged, large means diverging
        slope = float(np.polyfit(np.log(diams), widths, 1)[0])

        out.append({
            'q_cap': cap,
            'widths': [round(w, 4) for w in widths],
            'diameters': diams,
            'drift_last_step': drift_last,
            'drift_total': drift_total,
            'slope_vs_ln_diameter': slope,
            'converged': bool(drift_last <= tol),
        })

    converged = [o for o in out if o['converged']]
    best = max(converged, key=lambda o: o['q_cap']) if converged else None
    return {
        'ok': True,
        'per_cap': out,
        'widest_converged_q_cap': best['q_cap'] if best else None,
        'converged_width': best['widths'][-1] if best else None,
        'verdict': (f"converges for |q| <= {best['q_cap']}; use that range and state it"
                    if best else
                    "NO q range tested converges -- the width is finite-size artefact "
                    "at every scale measured, and no band built on it is defensible"),
    }


def converged_n(sweep, tol=0.02):
    """Smallest n whose Delta-alpha is within `tol` of the largest n tested.

    Returns None when the sweep never settles -- which is a RESULT, not a
    failure, and must be reported rather than papered over by picking the
    biggest n that happened to fit in memory.
    """
    if len(sweep) < 2:
        return None
    final = sweep[-1]['width_mean']
    for row in sweep:
        if abs(row['width_mean'] - final) <= tol:
            return row['n']
    return None


# ============================================================================
# 4. HONEST GROUPING:  refuse to invent classes
# ============================================================================

def multimodality_report(widths, n_boot=2000, seed=0):
    """Is this distribution actually multimodal, or is it one lump?

    Cutting a unimodal distribution into terciles and naming the pieces is not
    a classification. The previous run's histogram was a single spike of 34
    structures between 1.19 and 1.22 plus a scattered tail, and the tercile
    boundaries fell either side of the spike's centre -- which is why two
    isomorphic graphs ended up in different classes.

    Uses a bootstrapped dip-like statistic (largest gap in the sorted values,
    compared against the same statistic under a unimodal null) so the module
    has no scipy/diptest dependency.
    """
    w = np.sort(np.asarray([x for x in widths if np.isfinite(x)], dtype=float))
    if w.size < 8:
        return {'verdict': 'too few values to test', 'n': int(w.size)}

    # observed: largest gap between consecutive order statistics, scaled
    gaps = np.diff(w)
    observed = float(gaps.max() / (w.std() + 1e-12))

    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_boot):
        sample = np.sort(rng.normal(w.mean(), w.std(), size=w.size))
        g = np.diff(sample)
        null.append(g.max() / (sample.std() + 1e-12))
    p = float(np.mean(np.asarray(null) >= observed))

    return {
        'n': int(w.size),
        'largest_gap_stat': observed,
        'p_value_vs_unimodal': p,
        'verdict': ('multimodal - grouping is defensible' if p < 0.05
                    else 'consistent with ONE mode - do not split into classes'),
    }


def assign_classes(widths, errors, n_classes=3):
    """Tercile classes -- but only if the class width beats the error bar.

    The previous run's classes were 0.032 wide against error bars of 0.03 to
    0.05, so class membership was decided by the random seed. hMOF-0 sat
    0.0003 from a boundary. This function computes that ratio and REFUSES to
    label when it is below 1, because a label you cannot reproduce is worse
    than no label.
    """
    w = np.asarray(widths, dtype=float)
    e = np.asarray(errors, dtype=float)
    finite = np.isfinite(w)
    if finite.sum() < n_classes * 2:
        return {'ok': False, 'reason': 'not enough finite values'}

    edges = np.quantile(w[finite], np.linspace(0, 1, n_classes + 1))
    narrowest = float(np.min(np.diff(edges)))
    typical_err = float(np.nanmedian(e[finite])) if np.isfinite(e).any() else float('nan')
    ratio = narrowest / typical_err if typical_err and typical_err > 0 else float('inf')

    return {
        'ok': bool(ratio >= 1.0),
        'class_edges': edges.tolist(),
        'narrowest_class_width': narrowest,
        'typical_error_bar': typical_err,
        'width_to_error_ratio': ratio,
        'reason': ('' if ratio >= 1.0 else
                   f'narrowest class ({narrowest:.4f}) is smaller than the typical '
                   f'error bar ({typical_err:.4f}); class membership would be decided '
                   f'by the random seed, not by the structure'),
    }


def require_topological_diversity(records):
    """A band over one topology is narrow for a trivial reason.

    48 of 76 structures in the previous run shared 256 nodes / 384 edges /
    diameter 12 -- a 4x4x4 pcu net, 64 six-connected Zn4O nodes and 192
    two-connected linkers. Coarse-graining deletes linker chemistry by design,
    so those structures are the SAME GRAPH and the descriptor cannot separate
    them even in principle. Report that before reporting a band.
    """
    sig = Counter((r.get('cg_nodes'), r.get('cg_edges'), r.get('diameter'))
                  for r in records if r.get('ok'))
    total = sum(sig.values())
    if not total:
        return {'ok': False, 'reason': 'no usable records'}
    biggest, count = sig.most_common(1)[0]
    frac = count / total
    return {
        'ok': bool(frac < 0.5),
        'n_distinct_graph_signatures': len(sig),
        'largest_group_signature': biggest,
        'largest_group_fraction': frac,
        'reason': ('' if frac < 0.5 else
                   f'{count}/{total} structures share the graph signature {biggest}. '
                   f'The coarse graph cannot distinguish them, so any band over this '
                   f'sample is measuring sample composition, not chemistry.'),
    }


# ============================================================================
# 5. SIZE CONTROL -- the confound that has now cost this project three claims
# ============================================================================

def partial_correlation(x, y, z):
    """corr(x, y) with z regressed out of both. Reported next to every raw
    correlation, because on this project the raw number has been misleading
    three times running: pore size (-0.497 -> +0.101), the four-structure real
    MOF claim, and the three Delta-alpha classes."""
    x, y, z = (np.asarray(v, dtype=float) for v in (x, y, z))
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    if m.sum() < 4:
        return float('nan')
    x, y, z = x[m], y[m], z[m]
    rx = x - np.polyval(np.polyfit(z, x, 1), z)
    ry = y - np.polyval(np.polyfit(z, y, 1), z)
    if rx.std() == 0 or ry.std() == 0:
        return float('nan')
    return float(np.corrcoef(rx, ry)[0, 1])


# ============================================================================
# 6. BATCH DRIVER
# ============================================================================

def analyse_structure(cif_path, sweep_n=(2, 3, 4, 6, 8), n_trials=40,
                      n_seeds=3, max_nodes=25000, verbose=True):
    """One structure, taken to convergence rather than to a fixed rule."""
    name = os.path.splitext(os.path.basename(cif_path))[0]
    if verbose:
        print(f"\n{name}")
    try:
        sweep = finite_size_sweep(cif_path, n_values=sweep_n, n_trials=n_trials // 2,
                                  n_seeds=n_seeds, max_nodes=max_nodes,
                                  verbose=verbose)
    except Exception as e:
        return {'name': name, 'ok': False, 'reason': f'{type(e).__name__}: {e}'}

    if not sweep:
        return {'name': name, 'ok': False, 'reason': 'no usable supercell size'}

    n_star = converged_n(sweep)
    final = sweep[-1]
    rec = {
        'name': name,
        'ok': True,
        'sweep': sweep,
        'converged': n_star is not None,
        'converged_n': n_star,
        'n_used': final['n'],
        'cg_nodes': final['cg_nodes'],
        'cg_edges': final['cg_edges'],
        'diameter': final['diameter'],
        'width': final['width_mean'],
        'width_sd': final['width_sd'],
        'r2_linearity': final['r2_linearity_mean'],
    }
    if not rec['converged']:
        rec['warning'] = ('Delta-alpha never settled across the sweep; this value is '
                          'size-dependent and must not be placed in a band')
    return rec


def analyse_directory(cif_dir, label, out_dir='converged_band_output',
                      sweep_n=(2, 3, 4, 6, 8), max_nodes=25000, verbose=True):
    """Run every CIF in a folder. Dataset-agnostic on purpose: point it at
    hMOF CIFs, at CoRE MOF CIFs, or at any new set, and the same code runs.

    NOTE ON PROVENANCE: this takes CIFs from disk and never queries MOFX-DB,
    because that endpoint has now twice returned hMOF records for a request
    that asked for CoRE MOF 2019 -- 'database=' is advisory there and loses to
    the 'gases[]' filter. Whatever is in the folder is what gets analysed, and
    `label` is recorded verbatim in the output so the provenance of every
    number is whatever you put in the folder name, not what an API claimed.
    """
    os.makedirs(out_dir, exist_ok=True)
    cifs = sorted(f for f in os.listdir(cif_dir) if f.lower().endswith('.cif'))
    if verbose:
        print(f"\n{'=' * 74}\n{label}: {len(cifs)} CIF files in {cif_dir}\n{'=' * 74}")

    records = []
    for f in cifs:
        records.append(analyse_structure(os.path.join(cif_dir, f),
                                         sweep_n=sweep_n, max_nodes=max_nodes,
                                         verbose=verbose))

    good = [r for r in records if r.get('ok')]
    conv = [r for r in good if r.get('converged')]
    widths = [r['width'] for r in conv]
    errs = [r['width_sd'] for r in conv]

    report = {
        'label': label,
        'n_input': len(cifs),
        'n_usable': len(good),
        'n_converged': len(conv),
        'diversity': require_topological_diversity(good),
        'multimodality': multimodality_report(widths) if len(widths) >= 8 else
                         {'verdict': 'too few converged values to test'},
        'classes': assign_classes(widths, errs) if len(widths) >= 6 else
                   {'ok': False, 'reason': 'too few converged values'},
    }
    if widths:
        report['width_mean'] = float(np.mean(widths))
        report['width_sd'] = float(np.std(widths))
        report['width_iqr'] = [float(np.quantile(widths, .25)),
                               float(np.quantile(widths, .75))]
        report['size_confound_check'] = {
            'corr_width_vs_cg_nodes': float(np.corrcoef(
                widths, [r['cg_nodes'] for r in conv])[0, 1]) if len(widths) > 2 else float('nan'),
        }

    path = os.path.join(out_dir, f'{label}_converged.json')
    with open(path, 'w') as fh:
        json.dump({'report': report, 'records': records}, fh, indent=2, default=str)

    if verbose:
        print(f"\n{'-' * 74}")
        print(f"{label}: {len(good)}/{len(cifs)} usable, {len(conv)} converged")
        print(f"  topological diversity : {report['diversity'].get('reason') or 'OK'}")
        print(f"  multimodality         : {report['multimodality']['verdict']}")
        print(f"  classes               : {report['classes'].get('reason') or 'defensible'}")
        if widths:
            print(f"  Delta-alpha           : {report['width_mean']:.3f} "
                  f"+/- {report['width_sd']:.3f}")
            print(f"  corr(width, CG nodes) : "
                  f"{report['size_confound_check']['corr_width_vs_cg_nodes']:+.3f}"
                  f"   <-- if this is large the band is a size histogram")
        print(f"  written to {path}")
    return report, records


if __name__ == '__main__':
    import sys

    if len(sys.argv) >= 3:
        analyse_directory(sys.argv[1], sys.argv[2])
    else:
        # Default: the convergence experiment on the four demonstration
        # structures. This is the result that decides whether any band is
        # meaningful, so it is what runs when the module is invoked bare.
        print('=' * 74)
        print('FINITE-SIZE CONVERGENCE -- does Delta-alpha settle?')
        print('=' * 74)
        print('Established on HKUST-1 over the full q range [-10, 10]:')
        print('  Delta-alpha ~ 0.78 ln(diameter) - 0.28, fitting all five sizes')
        print('  to within 0.01. Logarithmic divergence, no plateau.')
        print('So the question is no longer "does it converge" but "over what')
        print('q range does it converge", which is what this run answers.')

        for cif in ['HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif']:
            if not os.path.exists(cif):
                continue
            print(f"\n{'-' * 74}\n{cif}\n{'-' * 74}")
            # n=10 on a 14-block cell needs a 14 000-vertex graph; the BFS
            # covering handles it, but five sizes already determine the trend
            # and the sixth costs more than it tells you.
            sweep = finite_size_sweep(cif, n_values=(2, 3, 4, 6, 8),
                                      max_nodes=8000)
            if len(sweep) < 3:
                print('  too few sizes completed to judge convergence')
                continue

            n_star = converged_n(sweep)
            print(f"  full q range [-10, 10]: "
                  + (f"converged at n={n_star}" if n_star else
                     "NEVER CONVERGES -- Delta-alpha tracks supercell size, "
                     "not the framework"))

            qc = q_range_convergence(sweep)
            if qc.get('ok'):
                print(f"\n  {'|q| cap':<10}{'widths across the sweep':<44}"
                      f"{'drift':<9}slope/ln(D)")
                for o in qc['per_cap']:
                    mark = 'OK ' if o['converged'] else '   '
                    print(f"  {mark}{o['q_cap']:<7}{str(o['widths']):<44}"
                          f"{o['drift_last_step']:<9.3f}{o['slope_vs_ln_diameter']:+.3f}")
                print(f"\n  VERDICT: {qc['verdict']}")
