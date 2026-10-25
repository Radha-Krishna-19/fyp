"""
MODULE 11 -- NMFA / iNMFA EXACTLY AS PUBLISHED

Source paper
    Xiao et al., "Deciphering the generating rules and functionalities of
    complex networks", Scientific Reports 11, 22964 (2021).
    https://www.nature.com/articles/s41598-021-02203-4

WHY THIS MODULE EXISTS
code_10 implemented the multifractal pipeline using **box-covering** -- the
Song/Havlin algorithm that tiles a network with randomly-seeded boxes. The paper
does something different and says so explicitly: it proposes the **box-growing**
method, and contrasts it with "the box-counting method that calculate[s] the
dimension of the whole network".

The distinction is not cosmetic:

    box-COVERING   tile the whole network with boxes; a node's measure is the
                   size of whichever box happens to cover it. The tiling is
                   randomly seeded, so the answer is stochastic and needs many
                   trials to stabilise.

    box-GROWING    centre a box on node i and grow its radius; the measure is
                   M_i(r), the number of nodes within distance r of i.
                   Completely DETERMINISTIC -- no seeds, no trials, no spread.

Because the paper's measure is deterministic, the entire reproducibility problem
that dominated the earlier implementation simply does not arise. That is the
single biggest practical consequence of using the published method.

THE PUBLISHED EQUATIONS (paper's Methods section)

    box-growing        M_i(r) = number of nodes within distance r of node i
    NFD (node i)       D_i    = slope of  ln M_i(r)  vs  ln r
    probability        u_i(r) = M_i(r) / M          M = total number of nodes
    partition function U_q(r) = SUM_{i in I} u_i(r)^q
    power law          U_q(r) ~ (r/d)^tau(q)        d = network radius
    mass exponent      tau(q) = ln U_q(r) / ln(r/d)     [in practice: log-log slope]
    Legendre           alpha(q) = d tau / dq
                       f(alpha) = q*alpha(q) - tau(q)
    generalized dim    D(q)  = tau(q) / q
    specific heat      C(q)  ~ -d^2 tau / dq^2
    asymmetry          A = ln[ (alpha_0 - alpha_min) / (alpha_max - alpha_0) ]
                       alpha_0 = the alpha at which f(alpha) is MAXIMUM

    NMFA   -> I = every node in the network
    iNMFA  -> I = the top 10% of nodes by influence  (the variant our brief uses)

INTERPRETATION, per the paper
    width w = alpha_max - alpha_min   degree of structural HETEROGENEITY
    alpha_0                           degree of structural COMPLEXITY
    A > 0   frequent structures dominate  ("clump", e.g. preferential attachment)
    A < 0   rare structures dominate      ("thorn", e.g. sparse random graphs)
    A ~ 0   symmetric, no dominant structure
"""

from __future__ import annotations
import math
from collections import Counter
from typing import Dict, List, Sequence

import numpy as np
import networkx as nx

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph
from code_10_multifractal_spectrum import supercell_graph, select_influential


# ----------------------------------------------------------- box growing
def growth_curves(G):
    """M_i(r) for every node i and every radius r  --  the paper's box-growing.

    Deterministic: one BFS per node. No random seeding anywhere, so repeated
    runs on the same graph give bit-identical results.
    """
    nodes = list(G.nodes())
    N = len(nodes)
    dist = dict(nx.all_pairs_shortest_path_length(nx.Graph(G)))
    ecc = {i: (max(dist[i].values()) if dist[i] else 0) for i in nodes}
    d_net = max(ecc.values()) if ecc else 1          # network radius (max box radius)
    radii = list(range(1, max(d_net, 2) + 1))

    M = {}
    for i in nodes:
        di = dist[i]
        counts = Counter(di.values())
        run, curve = 0, []
        for r in radii:
            run += counts.get(r, 0)
            curve.append(run + 1)                     # +1: node i itself is in its own box
        M[i] = np.array(curve, dtype=float)
    return M, radii, d_net, N


def node_fractal_dimension(M, radii):
    """NFD_i = slope of ln M_i(r) vs ln r  (the paper's node-based fractal dim)."""
    x = np.log(np.asarray(radii, float))
    out = {}
    for i, curve in M.items():
        y = np.log(curve)
        ok = np.isfinite(x) & np.isfinite(y)
        out[i] = float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float('nan')
    return out


# ----------------------------------------------------------- NMFA / iNMFA
def nmfa(G, subset=None, q_values=None):
    """Node-based multifractal analysis, exactly as published.

    subset = None  -> NMFA  (all nodes)
    subset = list  -> iNMFA (restricted to the influential nodes)
    """
    if q_values is None:
        q_values = np.linspace(-10, 10, 41)
    M, radii, d_net, N = growth_curves(G)
    I = list(M.keys()) if subset is None else [i for i in subset if i in M]
    if not I:
        raise ValueError('no nodes in the measure set')

    # u_i(r) = M_i(r) / M      (M = total number of nodes)
    U = np.array([M[i] / N for i in I])               # shape (|I|, len(radii))

    # U_q(r) = sum_i u_i(r)^q ;  power law against the observation scale r/d
    x = np.log(np.asarray(radii, float) / d_net)
    tau = []
    for q in q_values:
        Zq = np.sum(U ** q, axis=0)
        y = np.log(Zq)
        ok = np.isfinite(x) & np.isfinite(y)
        tau.append(float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else np.nan)
    tau = np.asarray(tau)

    alpha = np.gradient(tau, q_values)
    f_alpha = q_values * alpha - tau

    with np.errstate(divide='ignore', invalid='ignore'):
        Dq = np.where(np.abs(q_values) > 1e-9, tau / q_values, np.nan)
    Cq = -np.gradient(np.gradient(tau, q_values), q_values)      # specific heat

    # alpha_0 = alpha where f(alpha) is MAXIMUM (paper's definition)
    fin = np.isfinite(f_alpha) & np.isfinite(alpha)
    if fin.sum():
        a0 = float(alpha[fin][int(np.argmax(f_alpha[fin]))])
        amin, amax = float(np.nanmin(alpha)), float(np.nanmax(alpha))
        L, R = a0 - amin, amax - a0
        A = float(np.log(L / R)) if (L > 0 and R > 0) else float('nan')
    else:
        a0 = amin = amax = A = float('nan')

    return {'q_values': q_values, 'tau': tau, 'alpha': alpha, 'f_alpha': f_alpha,
            'D_q': Dq, 'C_q': Cq, 'radii': radii, 'd_net': d_net, 'N': N,
            'n_measure': len(I), 'alpha_0': a0, 'alpha_min': amin, 'alpha_max': amax,
            'width': amax - amin if np.isfinite(amax) else float('nan'),
            'asymmetry': A, 'ok': bool(np.isfinite(alpha).sum() > 1)}


def structure_distance(r1, r2):
    """Paper's structure distance: divergence between the D(q) curves."""
    a, b = r1['D_q'], r2['D_q']
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.sqrt(np.mean((a[ok] - b[ok]) ** 2))) if ok.sum() else float('nan')


def analyse_cif(cif_path, top_percent=0.10, min_blocks=60, q_values=None):
    """CIF -> periodic block graph -> supercell -> NMFA and iNMFA.

    top_percent defaults to 0.10 -- the paper's iNMFA uses the top 10% of
    influential nodes (the earlier notebook used 30%).
    """
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    nb, lb = run_metal_oxo(geom)
    blocks, edges = build_periodic_block_graph(geom, nb, lb)
    n = 1
    while len(blocks) * n ** 3 < min_blocks and n < 4:
        n += 1
    if n > 1:
        G, _kind = supercell_graph(blocks, edges, n)
    else:
        G = nx.MultiGraph(); G.add_nodes_from(range(len(blocks)))
        for i, j, _t in edges:
            G.add_edge(i, j)

    influential, sel = select_influential(G, top_percent)
    res_all = nmfa(G, None, q_values)                  # NMFA
    res_inf = nmfa(G, influential, q_values)            # iNMFA
    M, radii, d_net, N = growth_curves(G)
    nfd = node_fractal_dimension(M, radii)
    metals = sorted({geom.symbols[a] for _k, b in blocks for a in b if geom.is_metal[a]})
    return {'cif_path': cif_path, 'G': G, 'supercell': n, 'metals': metals,
            'influential': influential, 'selection': sel,
            'nmfa': res_all, 'inmfa': res_inf,
            'nfd': nfd, 'nfd_mean': float(np.nanmean(list(nfd.values()))),
            'K': G.number_of_nodes()}


if __name__ == '__main__':
    import sys
    paths = sys.argv[1:] or ['HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif']

    print('=' * 96)
    print('NMFA / iNMFA — box-growing method, exactly as published (Sci Rep 11, 22964)')
    print('=' * 96)
    print(f"{'structure':<11}{'metal':<6}{'blocks':<8}{'radius d':<10}{'NFD mean':<11}"
          f"{'alpha_0':<10}{'width w':<10}{'asymmetry A'}")
    print('-' * 96)
    results = {}
    for p in paths:
        r = analyse_cif(p)
        results[p] = r
        s = r['inmfa']
        print(f"{p.replace('.cif',''):<11}{','.join(r['metals']):<6}{r['K']:<8}"
              f"{s['d_net']:<10}{r['nfd_mean']:<11.2f}{s['alpha_0']:<10.2f}"
              f"{s['width']:<10.2f}{s['asymmetry']:.3f}")

    print()
    print('Paper\'s interpretation:  w = heterogeneity,  alpha_0 = complexity,')
    print('A > 0 "clump" (frequent structures dominate),  A < 0 "thorn" (rare dominate).')

    print()
    print('=' * 96)
    print('DETERMINISM — box-growing has no random seeding at all')
    print('=' * 96)
    p0 = paths[0]
    vals = [analyse_cif(p0)['inmfa']['alpha_0'] for _ in range(3)]
    print(f'  {p0}: alpha_0 over 3 independent runs = ' +
          ', '.join(f'{v:.6f}' for v in vals))
    print(f'  spread = {max(vals) - min(vals):.2e}  ->  ' +
          ('bit-identical, as expected' if max(vals) - min(vals) < 1e-12 else 'NOT deterministic'))
    print('  (box-covering needed ~40 trials to get this stable; box-growing needs none)')

    print()
    print('=' * 96)
    print('NMFA (all nodes) vs iNMFA (top 10% influential)')
    print('=' * 96)
    print(f"{'structure':<11}{'NMFA alpha_0':<15}{'iNMFA alpha_0':<16}{'NMFA w':<10}{'iNMFA w'}")
    print('-' * 96)
    for p in paths:
        a, b = results[p]['nmfa'], results[p]['inmfa']
        print(f"{p.replace('.cif',''):<11}{a['alpha_0']:<15.2f}{b['alpha_0']:<16.2f}"
              f"{a['width']:<10.2f}{b['width']:.2f}")

    print()
    print('=' * 96)
    print('STRUCTURE DISTANCE between materials  (RMS difference of D(q))')
    print('=' * 96)
    names = [p.replace('.cif', '') for p in paths]
    print('           ' + ''.join(f'{n:<11}' for n in names))
    for i, p in enumerate(paths):
        row = f'{names[i]:<11}'
        for j, p2 in enumerate(paths):
            row += f"{structure_distance(results[p]['inmfa'], results[p2]['inmfa']):<11.3f}"
        print(row)
    print()
    print('Larger distance = more different generating rules. The diagonal is 0 by construction.')
