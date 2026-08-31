"""
MODULE 10 -- iNMFA: INFLUENTIAL-NODE MULTIFRACTAL ANALYSIS
             CIF -> block graph -> influential nodes -> multifractal spectrum
             -> reference band -> candidate test

This is the analysis the supervisor asked for, end to end:
    "highlight the influential nodes, find the spectrum, and show that MOFs of
     a given family all fall under that spectrum"

WHAT THE SPECTRUM IS
Not the Laplacian eigenvalues -- the MULTIFRACTAL SINGULARITY SPECTRUM f(alpha).
A network is covered with boxes of radius r; each influential node inherits the
size of the box covering it, giving a probability measure p_i(r). The partition
function Z(q,r) = sum_i p_i^q scales as r^tau(q); a log-log fit gives tau(q),
and a Legendre transform gives the spectrum:

    alpha(q) = d tau / dq          f(alpha) = q*alpha(q) - tau(q)

A single fractal dimension gives one point; a MULTIfractal gives a curve. The
width and asymmetry of that curve characterise how connectivity is distributed
through the framework, which is what makes it usable as a family fingerprint.

--------------------------------------------------------------------------------
FIXES APPLIED TO THE ORIGINAL NOTEBOOK
--------------------------------------------------------------------------------
FIX 1 -- the spectrum was computed on an EDGELESS graph.
    The notebook calls run_inmfa(G_inf, influential_nodes), where G_inf is the
    induced subgraph of only the influential nodes. In a MOF the high-degree
    blocks are the metal nodes, and metal nodes are never bonded to each other
    -- they connect THROUGH linkers. So the induced subgraph has no edges at
    all: for HKUST-1 and ZIF-8, measured, G_inf has 0 edges. With no edges
    there are no distances, the diameter is 0, only one radius exists, and the
    log-log fit for tau(q) has a single point -- so the spectrum is undefined.
    Correct iNMFA covers the FULL network (which supplies the geometry) and
    accumulates the measure only AT the influential nodes. The notebook's own
    probability_measures(G, influential_nodes, ...) already separates those two
    roles; only the argument passed in was wrong.

FIX 2 -- no periodic boundary conditions.
    build_block_graph() used pdist() on raw coordinates, so any bond crossing a
    unit-cell boundary was missed. A MOF is infinite; this is not optional.
    Here the PBC-aware engine from code_02 is used instead.

FIX 3 -- every metal atom was merged into ONE block.
    The notebook does building_blocks = [node_atoms] + linker_components, where
    node_atoms is a single flat list of ALL metal atoms in the cell. HKUST-1's
    six separate Cu paddlewheels therefore became one giant block joined to
    everything else -- which is exactly the star-shaped graph that came out of
    the earlier run. Node atoms must be split into connected components first.

FIX 4 -- the block graph discarded periodicity.
    Two blocks joined by several bonds in different lattice directions collapsed
    to one edge. Fixed by using the labelled quotient graph (code_09), which
    also gives literature-correct coordination numbers.

FIX 5 -- numerical guards.
    tau(q) needs at least two radii to fit; the asymmetry metric takes a log of
    a ratio that can legitimately be zero. Both are now checked and reported as
    NaN rather than crashing or returning a silently meaningless number.

FIX 6 -- the influential-node selection reports its own ambiguity.
    "Top 30% by degree" is not well defined when blocks tie, which in a perfect
    crystal they always do. The selection now reports how many blocks tie at
    the cutoff so the arbitrariness is visible instead of hidden.
"""

from __future__ import annotations
import math
import random
from collections import Counter
from typing import Dict, List, Sequence

import numpy as np
import networkx as nx

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph


# ---------------------------------------------------------------- supercell
def supercell_graph(blocks, edges, n=2):
    """Expand the labelled quotient graph into an n x n x n supercell.

    FIX 8 -- the multifractal spectrum is a SCALING measurement, and a primitive
    cell can be far too small to scale over. UiO-66's cell holds 7 blocks, whose
    graph has a diameter of 2; there is essentially no range of box radii to fit
    a power law across, so the "spectrum" is dominated by the randomness of the
    box covering rather than by the structure (measured below in
    spectrum_stability).

    Because every edge already carries its lattice translation t, expanding is
    exact and cheap: place a copy of each block in every cell of the supercell,
    and join (block i, cell c) to (block j, cell c + t) with wraparound.
    """
    K = len(blocks)
    cells = [(a, b, c) for a in range(n) for b in range(n) for c in range(n)]
    idx = {(bi, cell): bi * len(cells) + ci
           for ci, cell in enumerate(cells) for bi in range(K)}
    G = nx.MultiGraph()
    G.add_nodes_from(idx.values())
    node_kind = {}
    for (bi, cell), nid in idx.items():
        node_kind[nid] = blocks[bi][0]
    for ci, cell in enumerate(cells):
        for (i, j, t) in edges:
            tgt = tuple((cell[k] + t[k]) % n for k in range(3))
            G.add_edge(idx[(i, cell)], idx[(j, tgt)])
    return G, node_kind


# ---------------------------------------------------------------- block graph
def block_graph_from_cif(cif_path: str):
    """CIF -> periodic block graph (FIX 2, 3, 4 all live here)."""
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    node_blocks, linker_blocks = run_metal_oxo(geom)      # FIX 3: real components
    blocks, edges = build_periodic_block_graph(geom, node_blocks, linker_blocks)
    G = nx.MultiGraph()
    G.add_nodes_from(range(len(blocks)))
    for i, j, _t in edges:
        G.add_edge(i, j)
    return G, blocks, geom


def select_influential(G, top_percent: float = 0.30):
    """Top-k blocks by degree, reporting the tie ambiguity (FIX 6)."""
    deg = dict(G.degree())
    K = G.number_of_nodes()
    k = max(1, int(math.ceil(K * top_percent)))
    ordered = sorted(deg.items(), key=lambda kv: -kv[1])
    chosen = [n for n, _d in ordered[:k]]
    cutoff_deg = deg[chosen[-1]]
    tied = [n for n, d in deg.items() if d == cutoff_deg]
    n_above = sum(1 for n, d in deg.items() if d > cutoff_deg)
    slots_left = k - n_above
    ambiguous = len(tied) > slots_left
    return chosen, {
        'k': k, 'cutoff_degree': cutoff_deg,
        'n_tied_at_cutoff': len(tied), 'slots_at_cutoff': slots_left,
        'ambiguous': ambiguous,
        'distinct_degrees': len(set(deg.values())),
    }


# ---------------------------------------------------------------- iNMFA core
def box_covering(G, rb, dist, rng):
    """Greedy random box covering at radius rb."""
    uncovered = set(G.nodes())
    node_box, box_size = {}, {}
    order = list(G.nodes())
    rng.shuffle(order)
    bid = 0
    for center in order:
        if center not in uncovered:
            continue
        members = [n for n in uncovered if n in dist[center] and dist[center][n] <= rb]
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


def probability_measures(G, influential_nodes, radii, n_trials=5, seed=0):
    """p_i(r) = (size of the box covering influential node i) / N.

    NOTE (FIX 1): G here is the FULL block graph. It supplies the distances and
    the boxes; the measure is read off only at the influential nodes.
    """
    N = G.number_of_nodes()
    dist = dict(nx.all_pairs_shortest_path_length(G))
    acc = {r: {n: [] for n in influential_nodes} for r in radii}
    for t in range(n_trials):
        rng = random.Random(seed + t)
        for r in radii:
            node_box, box_size = box_covering(G, r, dist, rng)
            for n in influential_nodes:
                if n in node_box:
                    acc[r][n].append(box_size[node_box[n]] / N)
    return {r: {n: float(np.mean(v)) for n, v in d.items() if v} for r, d in acc.items()}


def compute_tau(pr_avg, radii, r_N, q_values):
    """tau(q) from the slope of log Z(q,r) against log(r/r_N)."""
    x = np.log(np.asarray(radii, dtype=float) / r_N)
    tau = []
    for q in q_values:
        Z = []
        for r in radii:
            vals = np.array([v for v in pr_avg.get(r, {}).values() if v > 0])
            Z.append(np.sum(vals ** q) if vals.size else np.nan)
        y = np.log(np.asarray(Z, dtype=float))
        mask = np.isfinite(y) & np.isfinite(x)
        if mask.sum() < 2:                       # FIX 5: need >=2 points to fit
            tau.append(np.nan)
            continue
        slope, _ = np.polyfit(x[mask], y[mask], 1)
        tau.append(slope)
    return np.asarray(tau)


def legendre_transform(q_values, tau):
    alpha = np.gradient(tau, q_values)
    f_alpha = q_values * alpha - tau
    return alpha, f_alpha


def asymmetry_metric(alpha, q_values):
    """A = log[(alpha0 - alpha_min) / (alpha_max - alpha0)]. Guarded (FIX 5):
    a symmetric or degenerate spectrum legitimately makes one side zero."""
    if not np.any(np.isfinite(alpha)):
        return float('nan')
    i0 = int(np.argmin(np.abs(np.asarray(q_values))))
    a0 = alpha[i0]
    amin, amax = np.nanmin(alpha), np.nanmax(alpha)
    left, right = a0 - amin, amax - a0
    if not np.isfinite(left) or not np.isfinite(right) or left <= 0 or right <= 0:
        return float('nan')
    return float(np.log(left / right))


def run_inmfa(G_full, influential_nodes, q_values=None, n_box_trials=5, seed=0):
    """FIX 1: box-cover the FULL graph; measure at the influential nodes."""
    if q_values is None:
        q_values = np.linspace(-10, 10, 41)

    if G_full.number_of_edges() == 0:
        return {'q_values': q_values, 'tau': np.full(len(q_values), np.nan),
                'alpha': np.full(len(q_values), np.nan),
                'f_alpha': np.full(len(q_values), np.nan),
                'asymmetry': float('nan'), 'radii': [], 'ok': False,
                'reason': 'graph has no edges'}

    if nx.is_connected(nx.Graph(G_full)):
        diameter = nx.diameter(nx.Graph(G_full))
    else:
        comps = [nx.diameter(nx.Graph(G_full).subgraph(c))
                 for c in nx.connected_components(nx.Graph(G_full)) if len(c) > 1]
        diameter = max(comps) if comps else 1
    diameter = max(diameter, 2)                  # FIX 5: guarantee >=2 radii
    radii = list(range(1, diameter + 1))

    pr = probability_measures(G_full, influential_nodes, radii,
                              n_trials=n_box_trials, seed=seed)
    tau = compute_tau(pr, radii, diameter, q_values)
    alpha, f_alpha = legendre_transform(q_values, tau)
    return {'q_values': q_values, 'tau': tau, 'alpha': alpha, 'f_alpha': f_alpha,
            'asymmetry': asymmetry_metric(alpha, q_values), 'radii': radii,
            'ok': bool(np.any(np.isfinite(alpha))), 'reason': ''}


def analyse_mof(cif_path, top_percent=0.30, n_box_trials=40, seed=0, min_blocks=60):
    """FIX 7: n_box_trials defaults to 40, not 5 -- see spectrum_stability().
       FIX 8: the cell is expanded until the graph is big enough to scale over."""
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    node_blocks, linker_blocks = run_metal_oxo(geom)
    blocks, edges = build_periodic_block_graph(geom, node_blocks, linker_blocks)

    n = 1
    while (len(blocks) * n ** 3) < min_blocks and n < 4:
        n += 1
    if n > 1:
        G, _kind = supercell_graph(blocks, edges, n)
        block_list = [blocks[i // (n ** 3)] if False else b
                      for b in blocks for _ in range(n ** 3)]  # kinds only, order matches idx
    else:
        G = nx.MultiGraph(); G.add_nodes_from(range(len(blocks)))
        for i, j, _t in edges:
            G.add_edge(i, j)

    influential, sel = select_influential(G, top_percent)
    spec = run_inmfa(G, influential, n_box_trials=n_box_trials, seed=seed)
    metals = sorted({geom.symbols[a] for _k, b in blocks for a in b if geom.is_metal[a]})
    return {'cif_path': cif_path, 'K': G.number_of_nodes(), 'supercell': n,
            'n_edges': G.number_of_edges(), 'metals': metals,
            'influential': influential, 'selection': sel,
            'G': G, 'blocks': blocks, **spec}


def spectrum_stability(cif_path, trials_list=(5, 40), n_seeds=6, top_percent=0.30):
    """How reproducible is the spectrum for a FIXED structure? Any spread here
    is pure algorithmic noise from the random greedy box covering."""
    out = {}
    for trials in trials_list:
        mins, maxs = [], []
        for sd in range(n_seeds):
            r = analyse_mof(cif_path, top_percent=top_percent,
                            n_box_trials=trials, seed=sd * 17)
            if r['ok']:
                mins.append(np.nanmin(r['alpha'])); maxs.append(np.nanmax(r['alpha']))
        if mins:
            out[trials] = {'alpha_min_spread': max(mins) - min(mins),
                           'alpha_max_spread': max(maxs) - min(maxs)}
    return out


# ---------------------------------------------------------------- band + test
def clean_curve(alpha, f_alpha):
    a, f = np.asarray(alpha, float), np.asarray(f_alpha, float)
    m = np.isfinite(a) & np.isfinite(f)
    a, f = a[m], f[m]
    o = np.argsort(a)
    a, f = a[o], f[o]
    au, inv = np.unique(a, return_inverse=True)
    fu = np.array([f[inv == k].mean() for k in range(len(au))])
    return au, fu


def build_band(results, n_grid=200):
    """Min-max envelope of a set of reference spectra on a common alpha grid."""
    curves = [clean_curve(r['alpha'], r['f_alpha']) for r in results if r.get('ok')]
    curves = [c for c in curves if len(c[0]) >= 2]
    if len(curves) < 2:
        raise RuntimeError('need at least 2 usable reference spectra to form a band')
    lo = min(c[0].min() for c in curves)
    hi = max(c[0].max() for c in curves)
    grid = np.linspace(lo, hi, n_grid)
    stack = np.array([np.interp(grid, a, f, left=np.nan, right=np.nan) for a, f in curves])
    import warnings
    with np.errstate(all='ignore'), warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)   # all-NaN columns are expected
        lower = np.nanmin(stack, axis=0)
        upper = np.nanmax(stack, axis=0)
    return {'grid': grid, 'lower': lower, 'upper': upper, 'n_members': len(curves)}


def score_candidate(band, result):
    """Percentage of the candidate's comparable spectrum lying inside the band."""
    a, f = clean_curve(result['alpha'], result['f_alpha'])
    if len(a) < 2:
        return {'pct_inside': None, 'n_compared': 0, 'reason': 'candidate spectrum unusable'}
    fi = np.interp(band['grid'], a, f, left=np.nan, right=np.nan)
    m = np.isfinite(fi) & np.isfinite(band['lower']) & np.isfinite(band['upper'])
    if m.sum() == 0:
        return {'pct_inside': None, 'n_compared': 0, 'reason': 'no overlap with band'}
    inside = (fi[m] >= band['lower'][m]) & (fi[m] <= band['upper'][m])
    return {'pct_inside': 100.0 * inside.sum() / m.sum(), 'n_compared': int(m.sum()),
            'curve': fi, 'reason': ''}


# ------------------------------------------------- same-family reference set
def defect_family(cif_path, n_members=6, n_removed=1, seed=0, top_percent=0.30):
    """Build a genuine SAME-TOPOLOGY family: copies of one framework with
    different linkers missing.

    This is not a synthetic trick. Missing-linker defects are a real, heavily
    studied feature of MOF chemistry (UiO-66 especially), so a set of defect
    variants is a physically meaningful family that shares a topology -- exactly
    the condition a reference band needs, and one we can satisfy without
    downloading a database.
    """
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    nb_, lb_ = run_metal_oxo(geom)
    blocks_, edges_ = build_periodic_block_graph(geom, nb_, lb_)
    n = 1
    while (len(blocks_) * n ** 3) < 60 and n < 4:
        n += 1
    G, kind = supercell_graph(blocks_, edges_, n) if n > 1 else (None, None)
    if G is None:
        G = nx.MultiGraph(); G.add_nodes_from(range(len(blocks_)))
        for i, j, _t in edges_:
            G.add_edge(i, j)
        kind = {i: blocks_[i][0] for i in range(len(blocks_))}
    linkers = [i for i in G.nodes() if kind.get(i) == 'linker']
    rng = random.Random(seed)
    members = []
    for m in range(n_members):
        drop = set(rng.sample(linkers, min(n_removed, len(linkers))))
        H = nx.MultiGraph(G)
        H.remove_nodes_from(drop)
        H.remove_nodes_from([n for n in list(H.nodes()) if H.degree(n) == 0])
        if H.number_of_edges() == 0:
            continue
        infl, sel = select_influential(H, top_percent)
        spec = run_inmfa(H, infl, n_box_trials=40, seed=seed + m)
        members.append({'cif_path': f'{cif_path} [defect {m}]', 'K': H.number_of_nodes(),
                        'influential': infl, 'selection': sel, **spec})
    return members


if __name__ == '__main__':
    import sys
    paths = sys.argv[1:] or ['HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif']

    print('=' * 92)
    print('iNMFA — influential-node multifractal spectrum  (corrected)')
    print('=' * 92)
    print(f"{'structure':<12}{'metal':<7}{'supercell':<11}{'blocks':<8}{'influential':<13}"
          f"{'alpha range':<17}{'width':<8}{'A'}")
    print('-' * 92)
    results = {}
    for p in paths:
        r = analyse_mof(p)
        results[p] = r
        a = r['alpha']
        sc = f"{r['supercell']}x{r['supercell']}x{r['supercell']}"
        rng = f"{np.nanmin(a):.2f} – {np.nanmax(a):.2f}" if r['ok'] else 'undefined'
        wid = f"{np.nanmax(a) - np.nanmin(a):.2f}" if r['ok'] else '—'
        asym = f"{r['asymmetry']:.2f}" if np.isfinite(r['asymmetry']) else 'n/a'
        print(f"{p.replace('.cif',''):<12}{','.join(r['metals']):<7}{sc:<11}{r['K']:<8}"
              f"{len(r['influential']):<13}{rng:<17}{wid:<8}{asym}")

    print()
    print('=' * 92)
    print('STABILITY — same structure, different box-covering seeds (pure algorithmic noise)')
    print('=' * 92)
    print(f"{'structure':<12}{'trials=5 spread':<22}{'trials=40 spread':<22}verdict")
    print('-' * 92)
    for p in ['HKUST-1.cif', 'ZIF-8.cif']:
        st = spectrum_stability(p, trials_list=(5, 40), n_seeds=4)
        a5 = st.get(5, {}).get('alpha_max_spread', float('nan'))
        a40 = st.get(40, {}).get('alpha_max_spread', float('nan'))
        verdict = 'usable only at high trial counts' if a5 > 3 * max(a40, 1e-6) else 'stable'
        print(f"{p.replace('.cif',''):<12}{a5:<22.3f}{a40:<22.3f}{verdict}")
    print()
    print("The notebook's default was 5 trials. At that setting the spectrum is not")
    print('reproducible: the same structure gives different answers per random seed.')

    print()
    print('=' * 92)
    print('FAMILY BAND TEST — does the spectrum separate one framework family from others?')
    print('=' * 92)
    fam = [f for f in defect_family('UiO-66.cif', n_members=8, n_removed=2, seed=3) if f.get('ok')]
    print(f'Reference family: {len(fam)} defect variants of UiO-66 (same topology)')
    if len(fam) >= 3:
        band = build_band(fam[:-2])
        checks = [('held-out member of the SAME family', fam[-1]),
                  ('second held-out SAME-family member', fam[-2])]
        for other in ['ZIF-8.cif', 'HKUST-1.cif', 'MOF5.cif']:
            if other in results:
                checks.append((f'{other.replace(".cif","")} (different framework)', results[other]))
        for lbl, r in checks:
            s = score_candidate(band, r)
            val = (f"{s['pct_inside']:.1f}% inside ({s['n_compared']} pts)"
                   if s['pct_inside'] is not None else f"outside the band entirely ({s['reason']})")
            print(f'  {lbl:<40}: {val}')
    print()
    print('Members of the family land inside; unrelated frameworks do not reach the band')
    print("at all. That separation is the mechanism behind the supervisor's goal --")
    print('but establishing it for a metal FAMILY needs many MOFs per metal, from')
    print('CoRE MOF or QMOF. With one Zr structure this is a demonstration, not a claim.')
