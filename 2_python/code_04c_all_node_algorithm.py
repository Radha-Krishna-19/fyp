"""
MODULE 4c -- ALL NODE ALGORITHM  (Python translation of the real source)
Real file   : src/deconstructor.cpp  (class AllNodeDeconstructor, which
              inherits from SingleNodeDeconstructor -- see code_04b.py)
Source      : https://github.com/snurr-group/mofid
Paper       : 10.1021/acs.cgd.8b00126, tree-decomposition step inspired by
              Algorithm 2 of arXiv:1802.04364v2

HOW THIS DIFFERS FROM MODULE 4b (single-node)
AllNodeDeconstructor reuses SingleNodeDeconstructor's node/linker split
verbatim. The only thing it overrides is CollapseLinkers(): instead of
collapsing an entire linker molecule into one point, it first finds internal
BRANCH POINTS (atoms with graph degree >= 3, counting only heavy/non-H atoms,
once the linker is reduced to its skeleton) and keeps those as separate
vertices, with the straight-chain atoms between them collapsed into simple
connecting edges. This is what turns one biphenyl-tetracarboxylate linker
vertex (single-node) into two separate 3-connected phenyl-ring vertices
(all-node) for MOF-505/NOTT-100-type structures.

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
comp (set[int])          : one linker fragment's atom indices (from
                          code_04b's linker_blocks).
branch_points             : atoms within `comp` whose heavy-atom (non-H)
                          degree, counted ONLY among neighbours also in
                          `comp`, is >= 3 -- e.g. the two ring carbons where
                          a biphenyl linker forks into two rigid halves.
                          (Real C++: TreeDecomposition()'s TREE_BRANCH_POINT
                          label.)
bp_groups                 : each branch point's own eventual sub-block --
                          also absorbs any hydrogen bonded ONLY to that
                          branch point, so it doesn't become an orphaned,
                          disconnected 1-atom fragment of its own.
remaining                 : every other atom of the fragment (the straight-
                          chain / ring pieces between branch points) --
                          split into its own connected sub-blocks, the
                          Python equivalent of the real code's
                          TREE_INT_BRANCH / TREE_EXT_CONN chain-collapse.
"""

from __future__ import annotations
from typing import List, Set

from code_02_bond_assignment_pbc import Geometry
from code_04a_metal_oxo_algorithm import _connected_components
from code_04b_single_node_algorithm import detect_initial_nodes_and_linkers_single_node


def split_all_node_branches(geom: Geometry, linker_blocks: List[List[int]]) -> List[List[int]]:
    """Real AllNodeDeconstructor::CollapseLinkers() / TreeDecomposition(),
    translated as a simplified structural analog: repeatedly identify
    degree>=3 heavy-atom junctions within each linker fragment and split the
    fragment into one sub-block per branch point plus one sub-block per
    remaining chain/ring piece. Captures the same core idea (rigid branch
    points become their own vertices) without reproducing every ring-fusion
    edge case of the real C++."""
    refined: List[List[int]] = []
    for comp in linker_blocks:
        if len(comp) <= 2:
            refined.append(comp)
            continue
        comp_set = set(comp)
        branch_points = []
        for a in comp:
            if geom.symbols[a] == 'H':
                continue
            deg = sum(1 for other, _v, _b in geom.adj[a] if other in comp_set and geom.symbols[other] != 'H')
            if deg >= 3:
                branch_points.append(a)

        if not branch_points:
            refined.append(comp)
            continue

        bp_set = set(branch_points)
        bp_groups = {bp: [bp] for bp in branch_points}
        remaining: List[int] = []
        for a in comp:
            if a in bp_set:
                continue
            if geom.symbols[a] == 'H':
                heavy_nbors = [other for other, _v, _b in geom.adj[a] if other in comp_set]
                if len(heavy_nbors) == 1 and heavy_nbors[0] in bp_set:
                    bp_groups[heavy_nbors[0]].append(a)
                    continue
            remaining.append(a)

        for piece in _connected_components(set(remaining), geom.bonds):
            refined.append(piece)
        for group in bp_groups.values():
            refined.append(sorted(group))
    return refined


def run_all_node(geom: Geometry):
    """Returns (node_blocks, linker_blocks), ready for code_05.py."""
    nodes = detect_initial_nodes_and_linkers_single_node(geom)   # reused verbatim from 4b
    linkers = set(range(geom.n)) - nodes
    node_blocks = _connected_components(nodes, geom.bonds)
    linker_blocks_single = _connected_components(linkers, geom.bonds)
    linker_blocks_all_node = split_all_node_branches(geom, linker_blocks_single)
    return node_blocks, linker_blocks_all_node


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif)
    node_blocks, linker_blocks = run_all_node(geom)
    print(f'Module 4c (all-node) result for {path}:')
    print(f'  {len(node_blocks)} node blocks')
    print(f'  {len(linker_blocks)} linker blocks (sizes: {[len(b) for b in linker_blocks]})')
    print('  For BTC/BDC-type linkers (no true branch point) this count matches single-node '
          'exactly -- try ZIF-8.cif to see a real divergence (its methyl substituent creates one).')
