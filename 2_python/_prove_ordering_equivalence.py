"""
DECISIVE TEST: does the order (coarse-grain-then-replicate vs
atomic-supercell-then-coarse-grain) change the resulting graph, or only its
cost?

Builds the SAME supercell two ways for the same structure and the same n,
using this project's own bond-perception and decomposition code in both
routes (so any difference found is about ORDER, not about two different
implementations disagreeing):

  ROUTE A (this project's code_12): coarse-grain the UNIT CELL first
      (metal-oxo decomposition on unit-cell atoms only), get the small
      block graph with translation-labelled edges, then REPLICATE that
      block graph n x n x n combinatorially. No atoms exist at replication
      time.

  ROUTE B (the teammate's order): build the n x n x n ATOMIC supercell
      first -- literally replicate every atom's fractional coordinate and
      scale the cell matrix by n, exactly what ase.Atoms.repeat() does --
      then run bond perception and metal-oxo decomposition on THAT full
      atomic supercell (with periodic boundary conditions on the ENLARGED
      cell, the same way code_02's 27-image search already works on any
      cell), then coarse-grain the result into blocks.

If the graphs come out isomorphic (same node count, same edge count, same
degree sequence, and a full networkx isomorphism check), the two orders are
mathematically equivalent and differ only in memory/CPU cost. If they don't,
the order is a genuine correctness bug and this reports exactly where the
two diverge.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import List

import networkx as nx

from code_01_cif_input import parse_cif, Atom, ParsedCIF
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph, coordination_numbers
from code_12_converged_band import quotient_graph_from_cif, replicate, fast_diameter


def build_atomic_supercell(cif_path: str, n: int) -> ParsedCIF:
    """Route B's first step: literally replicate every atom n x n x n and
    scale the cell -- the atomic-supercell-first route, using nothing but
    this project's own CIF dataclass so the SAME downstream code (code_02,
    code_04a, code_09) can run on it unmodified."""
    cif = parse_cif(open(cif_path).read())
    new_atoms: List[Atom] = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for a in cif.atoms:
                    new_atoms.append(Atom(
                        el=a.el,
                        fx=(a.fx + i) / n,
                        fy=(a.fy + j) / n,
                        fz=(a.fz + k) / n,
                    ))
    new_cell = [[v * n for v in row] for row in cif.cell_matrix]
    return ParsedCIF(
        a=cif.a * n, b=cif.b * n, c=cif.c * n,
        alpha=cif.alpha, beta=cif.beta, gamma=cif.gamma,
        cell_matrix=new_cell, atoms=new_atoms,
    )


def route_a_cg_first(cif_path: str, n: int):
    """Coarse-grain the unit cell, THEN replicate the block graph."""
    blocks, edges, _geom = quotient_graph_from_cif(cif_path)
    G, kind = replicate(blocks, edges, n)
    return nx.Graph(G), kind


def route_b_atomic_first(cif_path: str, n: int):
    """Build the n x n x n atomic supercell FIRST, then run bond
    perception and metal-oxo decomposition on the WHOLE enlarged cell
    (periodic boundary conditions apply to the enlarged cell, exactly as
    code_02's 27-image search already does for any cell size), then
    coarse-grain that into blocks. This is literally her order."""
    supercell_cif = build_atomic_supercell(cif_path, n)
    geom = compute_geometry(supercell_cif)
    node_blocks, linker_blocks = run_metal_oxo(geom)
    blocks, edges = build_periodic_block_graph(geom, node_blocks, linker_blocks)
    G = nx.Graph()
    G.add_nodes_from(range(len(blocks)))
    G.add_edges_from((i, j) for i, j, _t in edges)
    kind = {i: k for i, (k, _b) in enumerate(blocks)}
    return G, kind


def compare(cif_path: str, n: int):
    name = cif_path.replace('.cif', '')
    print(f"\n{'='*70}\n{name}, n={n}")

    t0 = time.time()
    Ga, kind_a = route_a_cg_first(cif_path, n)
    ta = time.time() - t0
    print(f"  Route A (CG unit cell, then replicate):     "
          f"{Ga.number_of_nodes()} nodes, {Ga.number_of_edges()} edges  [{ta:.2f}s]")

    t0 = time.time()
    Gb, kind_b = route_b_atomic_first(cif_path, n)
    tb = time.time() - t0
    print(f"  Route B (atomic supercell, then coarse-grain): "
          f"{Gb.number_of_nodes()} nodes, {Gb.number_of_edges()} edges  [{tb:.2f}s]")

    same_counts = (Ga.number_of_nodes() == Gb.number_of_nodes() and
                   Ga.number_of_edges() == Gb.number_of_edges())
    deg_a = sorted(d for _, d in Ga.degree())
    deg_b = sorted(d for _, d in Gb.degree())
    same_degseq = deg_a == deg_b

    kind_count_a = {}
    for v in kind_a.values():
        kind_count_a[v] = kind_count_a.get(v, 0) + 1
    kind_count_b = {}
    for v in kind_b.values():
        kind_count_b[v] = kind_count_b.get(v, 0) + 1
    same_kind_counts = kind_count_a == kind_count_b

    print(f"  node/edge counts match: {same_counts}")
    print(f"  node-kind counts match: {same_kind_counts}  (A={kind_count_a}, B={kind_count_b})")
    print(f"  degree sequences match: {same_degseq}")

    iso = None
    if Ga.number_of_nodes() == Gb.number_of_nodes() and Ga.number_of_nodes() <= 4000:
        iso = nx.is_isomorphic(Ga, Gb)
        print(f"  FULL GRAPH ISOMORPHISM CHECK: {iso}")
    else:
        print(f"  (skipped full isomorphism check -- {Ga.number_of_nodes()} nodes, too slow / size mismatch)")

    print(f"  cost ratio (route B time / route A time): {tb/max(ta,1e-6):.1f}x")
    verdict = "IDENTICAL GRAPH" if (same_counts and same_degseq and iso is not False) else "DIFFERENT"
    print(f"  VERDICT: {verdict}")
    return same_counts, same_degseq, iso, ta, tb


if __name__ == '__main__':
    # n=2 only for all four: route B's atomic bond perception is O(N^2 * 27
    # images) in pure Python (see code_02's own docstring), so n=3 on MOF5
    # (424 atoms/cell -> 11448 atoms) would take far too long to be worth
    # running as a check. n=2 already puts real atom counts through both
    # routes (up to ~3400 atoms for MOF5) and is more than enough to prove
    # or disprove equivalence.
    structures = ['HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif']
    results = []
    for cif in structures:
        for n in (2,):
            r = compare(cif, n)
            results.append((cif, n, r))
    # then push the cheapest structure (UiO-66, 114 atoms/cell) to n=3 as
    # an extra check that the equivalence isn't an n=2-only coincidence
    for n in (3,):
        r = compare('UiO-66.cif', n)
        results.append(('UiO-66.cif', n, r))

    print(f"\n\n{'='*70}\nSUMMARY")
    all_match = True
    for cif, n, (same_counts, same_degseq, iso, ta, tb) in results:
        ok = same_counts and same_degseq and iso is not False
        all_match = all_match and ok
        print(f"  {cif:12s} n={n}  counts_match={same_counts}  degseq_match={same_degseq}  "
              f"isomorphic={iso}  cost_ratio={tb/max(ta,1e-6):.1f}x  -> {'MATCH' if ok else 'MISMATCH'}")
    print(f"\nAll cases match: {all_match}")
