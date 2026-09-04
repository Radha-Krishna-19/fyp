"""
MODULE 9 -- BUILDING-BLOCK NETWORK ANALYSIS
             (influential nodes + spectral fingerprint)

WHY THIS MODULE EXISTS
Once a MOF has been decomposed into building blocks, the framework is a GRAPH:
vertices are blocks, edges are the bonds between them. Two questions follow
naturally, and this module answers both:

    1. Which blocks are structurally influential?      -> centrality measures
    2. Does that graph have a signature per MOF family? -> eigenvalue spectrum

--------------------------------------------------------------------------------
THE CRITICAL DETAIL: THIS MUST BE A *PERIODIC* GRAPH
--------------------------------------------------------------------------------
A MOF is infinite. If you build the block graph naively -- one vertex per block
in the unit cell, one edge per pair of blocks that share a bond -- you silently
destroy the periodicity, because two blocks joined by SEVERAL bonds running in
DIFFERENT lattice directions collapse into a single edge.

The failure is easy to spot and easy to miss:

  * UiO-66's primitive cell contains exactly ONE Zr6 cluster. Every one of its
    12 connections runs out to a periodic image of a linker and back. Collapse
    those and the cluster looks 6-connected, or -- if the linkers are folded in
    too -- the whole cell degenerates into a STAR: one hub joined to everything,
    every other vertex of degree 1.
  * A star is not a framework. Worse, it makes centrality meaningless: every
    non-hub vertex ties at degree 1, so "top-k by degree" just returns whichever
    ties the sort happened to put first.

The fix is the LABELLED QUOTIENT GRAPH, which is also exactly what Systre
consumes (Module 6): each edge is identified not by (blockA, blockB) but by
(blockA, blockB, t) where t is the integer lattice translation the bond
crosses. Two bonds between the same pair of blocks are the SAME edge only if
they cross the same translation.

Verification -- coordination numbers against published crystallography:

    HKUST-1   Cu paddlewheel   4-connected   (tbo net)
    MOF-5     Zn4O             6-connected   (pcu net)
    ZIF-8     Zn               4-connected   (sod net)
    UiO-66    Zr6 cluster     12-connected   (fcu net)

If the graph construction is right, these fall out automatically. If it is
wrong, UiO-66 is the structure that exposes it.

--------------------------------------------------------------------------------
WHAT "SPECTRUM" MEANS HERE
--------------------------------------------------------------------------------
The eigenvalues of the graph Laplacian L = D - A. They are invariant to how the
vertices happen to be numbered, so two structures built from the same building
blocks in the same topology give the same spectrum regardless of atom ordering
in the CIF. That makes the spectrum usable as a family fingerprint -- the basis
for a claim of the form "these MOFs occupy this region of spectral space".

Reported per structure:
    lambda_2   algebraic connectivity (Fiedler value): how hard the net is to cut
    lambda_max largest Laplacian eigenvalue: bounded below by max_degree + 1
    spectral gap, and the full sorted spectrum
"""

from __future__ import annotations
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import numpy as np

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry, Geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_05_centroid_simplification import _unwrap_block


def _invert3(M):
    a, b, c = M[0]; d, e, f = M[1]; g, h, i = M[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    adj = [[(e * i - f * h), -(b * i - c * h), (b * f - c * e)],
           [-(d * i - f * g), (a * i - c * g), -(a * f - c * d)],
           [(d * h - e * g), -(a * h - b * g), (a * e - b * d)]]
    return [[adj[r][k] / det for k in range(3)] for r in range(3)]


def build_periodic_block_graph(geom: Geometry, node_blocks, linker_blocks):
    """The labelled quotient graph of the building blocks.

    Returns (blocks, edges) where blocks is a list of (kind, atom_indices) and
    edges is a list of (i, j, t) with t the integer lattice translation the
    bond crosses. An edge from a block back to itself across a translation is
    legitimate and is kept -- that is how a framework with one cluster per cell
    stays connected to its own images.
    """
    # ---- blocks become the VERTICES of the graph ---------------------------
    # blocks[i] = (kind, [atom indices]). Order matters only in that the index
    # into this list IS the vertex id used everywhere downstream.
    blocks = [('node', b) for b in node_blocks] + [('linker', b) for b in linker_blocks]
    # Reverse lookup: given an atom, which block does it belong to? Needed because
    # bonds are stored per-ATOM but we need them per-BLOCK.
    atom_to_block: Dict[int, int] = {a: i for i, (_k, b) in enumerate(blocks) for a in b}

    # ---- unwrap each block so it is spatially contiguous -------------------
    # WHY THIS IS NECESSARY: a block can straddle a cell boundary -- half its atoms
    # near fractional coordinate 0.98, half near 0.02. Those are adjacent in reality
    # but numerically a whole cell apart. If we measured translations against the
    # raw coordinates we would compute a spurious extra cell-crossing for every
    # such block. Unwrapping shifts each atom into one self-consistent frame
    # centred on its own block, so the block is one contiguous piece first.
    unwrapped: Dict[int, Tuple[float, float, float]] = {}
    for _kind, b in blocks:
        unwrapped.update(_unwrap_block(geom, b))

    # inv: the INVERSE cell matrix. code_01 built the matrix that converts
    # fractional -> Cartesian; here we need the opposite direction, because we are
    # about to take a Cartesian displacement and ask "how many whole cells is that?"
    inv = _invert3(geom.cell_matrix)

    def to_frac(v):
        """Cartesian displacement (angstroms) -> fractional (cell counts)."""
        return (v[0] * inv[0][0] + v[1] * inv[1][0] + v[2] * inv[2][0],
                v[0] * inv[0][1] + v[1] * inv[1][1] + v[2] * inv[2][1],
                v[0] * inv[0][2] + v[1] * inv[1][2] + v[2] * inv[2][2])

    # ---- turn every inter-block bond into a LABELLED edge -------------------
    # seen: deduplicates edges. The same block-to-block connection can be found
    # from either endpoint, and we want it counted once.
    seen = set()
    edges: List[Tuple[int, int, Tuple[int, int, int]]] = []
    for bd in geom.bonds:
        bi, bj = atom_to_block[bd.lo], atom_to_block[bd.hi]

        # RECOVERING THE TRANSLATION -- the heart of this function.
        # bd.vec is where atom hi sits relative to atom lo, INCLUDING any cell
        # crossing (code_02 stored the winning minimum-image displacement).
        # 'actual' is therefore hi's true position in lo's block frame...
        ui = unwrapped[bd.lo]
        actual = (ui[0] + bd.vec[0], ui[1] + bd.vec[1], ui[2] + bd.vec[2])
        # ...while 'uj' is where hi sits in its OWN block's frame.
        uj = unwrapped[bd.hi]
        # The difference between those two frames is exactly how many whole cells
        # apart the two blocks are. Convert to fractional and round: a clean whole
        # number, because the two frames can only differ by an integer number of cells.
        delta = (actual[0] - uj[0], actual[1] - uj[1], actual[2] - uj[2])
        fr = to_frac(delta)
        t = (int(round(fr[0])), int(round(fr[1])), int(round(fr[2])))

        # A bond from a block to ITSELF within the same cell is internal chemistry
        # (two atoms inside one cluster), not a connection between blocks. Skip it.
        # NOTE the condition: a self-loop with t != (0,0,0) is KEPT, because that is
        # a block bonding to its own periodic image -- which is exactly how UiO-66,
        # with one cluster per cell, stays connected. Dropping those is what makes a
        # naive graph report coordination 1 instead of 12.
        if bi == bj and t == (0, 0, 0):
            continue

        # CANONICAL ORIENTATION: the same physical connection can be written
        # (i, j, t) or (j, i, -t). Pick one deterministically so the dedup set
        # recognises them as identical, otherwise every edge is counted twice.
        if (bj, tuple(-x for x in t)) < (bi, t):
            key = (bj, bi, tuple(-x for x in t))
        else:
            key = (bi, bj, t)
        if key in seen:
            continue
        seen.add(key)
        edges.append(key)
    return blocks, edges


def coordination_numbers(blocks, edges):
    """Degree in the quotient graph = true crystallographic coordination number."""
    deg = Counter()
    for i, j, _t in edges:
        deg[i] += 1
        deg[j] += 1          # a self-loop across a translation counts twice: correct
    return [deg[i] for i in range(len(blocks))]


def adjacency_matrix(blocks, edges):
    n = len(blocks)
    A = np.zeros((n, n))
    for i, j, _t in edges:
        A[i, j] += 1
        A[j, i] += 1
    return A


def centralities(blocks, edges):
    """Which blocks are structurally influential, by three complementary measures."""
    A = adjacency_matrix(blocks, edges)
    n = len(blocks)
    deg = A.sum(axis=1)

    # eigenvector centrality: principal eigenvector of A (Perron-Frobenius)
    vals, vecs = np.linalg.eigh(A)
    principal = np.abs(vecs[:, -1])
    if principal.max() > 0:
        principal = principal / principal.max()

    # random-walk / diffusion importance: stationary distribution of a walk
    stat = deg / deg.sum() if deg.sum() else np.zeros(n)

    return {'degree': deg, 'eigenvector': principal, 'stationary': stat}


def laplacian_spectrum(blocks, edges):
    """Eigenvalues of L = D - A. Invariant to vertex numbering, so usable as a
    family fingerprint."""
    A = adjacency_matrix(blocks, edges)
    D = np.diag(A.sum(axis=1))
    L = D - A
    ev = np.linalg.eigvalsh(L)
    ev = np.sort(np.real(ev))
    return ev


def analyse(cif_path: str) -> Dict:
    geom = compute_geometry(parse_cif(open(cif_path).read()))
    nb, lb = run_metal_oxo(geom)
    blocks, edges = build_periodic_block_graph(geom, nb, lb)
    cn = coordination_numbers(blocks, edges)
    cent = centralities(blocks, edges)
    ev = laplacian_spectrum(blocks, edges)

    node_cn = sorted({cn[i] for i, (k, _b) in enumerate(blocks) if k == 'node'})
    linker_cn = sorted({cn[i] for i, (k, _b) in enumerate(blocks) if k == 'linker'})

    metals = sorted({geom.symbols[a] for _k, b in blocks for a in b
                     if geom.is_metal[a]})

    lam2 = ev[1] if len(ev) > 1 else 0.0
    return {
        'name': cif_path.replace('.cif', ''),
        'metals': metals,
        'n_blocks': len(blocks), 'n_edges': len(edges),
        'node_cn': node_cn, 'linker_cn': linker_cn,
        'degrees': cn,
        'centrality': cent,
        'spectrum': ev,
        'lambda2': lam2, 'lambda_max': ev[-1] if len(ev) else 0.0,
        'blocks': blocks,
    }


if __name__ == '__main__':
    import sys
    paths = sys.argv[1:] or ['HKUST-1.cif', 'MOF5.cif', 'ZIF-8.cif', 'UiO-66.cif']
    expected = {'HKUST-1': ('Cu paddlewheel 4-c, BTC 3-c', 'tbo'),
                'MOF5': ('Zn4O 6-c, BDC 2-c', 'pcu'),
                'ZIF-8': ('Zn 4-c, mIm 2-c', 'sod'),
                'UiO-66': ('Zr6 12-c, BDC 2-c', 'fcu')}

    print('=' * 92)
    print('COORDINATION NUMBERS FROM THE PERIODIC BLOCK GRAPH')
    print('=' * 92)
    print(f"{'structure':<11}{'metal':<7}{'node c.n.':<12}{'linker c.n.':<13}{'expected':<28}{'match'}")
    print('-' * 92)
    results = []
    for p in paths:
        r = analyse(p)
        results.append(r)
        exp = expected.get(r['name'], ('', ''))
        ok = str(r['node_cn']) if r['node_cn'] else '-'
        match = 'YES' if exp[0] and str(r['node_cn'][0]) in exp[0].split()[1] else '--'
        print(f"{r['name']:<11}{','.join(r['metals']):<7}{str(r['node_cn']):<12}"
              f"{str(r['linker_cn']):<13}{exp[0]:<28}{exp[1]}")

    print()
    print('=' * 92)
    print('MOST INFLUENTIAL BLOCKS  (eigenvector centrality of the periodic graph)')
    print('=' * 92)
    for r in results:
        cent = r['centrality']['eigenvector']
        order = np.argsort(-cent)
        top = []
        for i in order[:5]:
            kind = r['blocks'][i][0]
            top.append(f'#{i}({kind[:4]},cn={r["degrees"][i]},c={cent[i]:.2f})')
        print(f"{r['name']:<11}{'  '.join(top)}")
        distinct = len(set(np.round(cent, 3)))
        print(f"{'':11}{distinct} distinct centrality values across {r['n_blocks']} blocks"
              f"{'  <-- ranking is meaningful' if distinct > 2 else '  <-- degenerate, ranking not meaningful'}")

    print()
    print('=' * 92)
    print('LAPLACIAN SPECTRUM  (family fingerprint)')
    print('=' * 92)
    print(f"{'structure':<11}{'blocks':<8}{'edges':<7}{'lambda_2':<11}{'lambda_max':<12}{'first few eigenvalues'}")
    print('-' * 92)
    for r in results:
        head = ', '.join(f'{v:.2f}' for v in r['spectrum'][:6])
        print(f"{r['name']:<11}{r['n_blocks']:<8}{r['n_edges']:<7}"
              f"{r['lambda2']:<11.3f}{r['lambda_max']:<12.3f}{head} ...")

    print()
    print('Note: lambda_2 (algebraic connectivity) measures how strongly the framework')
    print('holds together; lambda_max scales with the highest coordination number.')
    print('Structures sharing an SBU type should occupy a common region of this space --')
    print('that is the claim a larger dataset would let you test properly.')
