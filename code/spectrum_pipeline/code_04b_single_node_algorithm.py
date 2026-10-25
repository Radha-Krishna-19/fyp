"""
MODULE 4b -- SINGLE NODE ALGORITHM  (Python translation of the real source)
Real file   : src/deconstructor.cpp  (class SingleNodeDeconstructor)
Source      : https://github.com/snurr-group/mofid

HOW THIS DIFFERS FROM MODULE 4a (metal-oxo)
Metal-oxo (code_04a.py) decides node vs. linker by looking at whole
DISCONNECTED FRAGMENTS after cutting every metal bond -- a carboxylate
automatically stays with the linker because it's only cut at the M-O bond.
Single-node instead walks OUTWARD from each metal atom, atom-by-atom, with
explicit chemical rules for oxygen coordination environments -- so it can
correctly decide, atom by atom, whether an oxygen is a bridging oxo/hydroxide
(-> node) or the far oxygen of a coordinating carboxylate (-> ALSO folded
into the node here, unlike metal-oxo, because the WHOLE carboxylate is
treated as part of the node's point of extension).

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
nodes (set[int])        : running set of atom indices assigned to the node
                          SBU. Starts as just the metal atoms, then grows
                          outward one coordination shell at a time.
nn (int)                 : the "nearest neighbour" atom currently being
                          classified (an O directly bonded to a node atom).
attached_carbon          : if nn (an oxygen) has a carbon neighbour, its
                          index -- distinguishes a metal-oxide/hydroxide
                          oxygen from a carboxylate oxygen.
is_carboxylate (bool)    : True only if attached_carbon has exactly 1 carbon
                          neighbour of its own + exactly 2 oxygen neighbours
                          (nn and other_o) -- i.e. it really looks like -COO-.
other_o                  : the SECOND oxygen of the same carboxylate group.

NOTE ON SCOPE
The real C++ also handles nitrogen coordination environments (N-N bridges in
azolate/pyrazolate linkers, pillared MOFs) via CalculateNonmetalRing() -- a
longer ring-finding routine omitted here for tractability, exactly as this
project's JS engine (mof_decompose.js) also documents omitting it. Neither
of this project's default example structures (HKUST-1, UiO-66) need it.
"""

from __future__ import annotations
from typing import Dict, Set

from code_02_bond_assignment_pbc import Geometry
from code_04a_metal_oxo_algorithm import _connected_components


def detect_initial_nodes_and_linkers_single_node(geom: Geometry) -> Set[int]:
    """Real SingleNodeDeconstructor::DetectInitialNodesAndLinkers(),
    translated: start from bare metals, walk their first coordination shell,
    and for every oxygen decide metal-oxide/hydroxide (-> node), carboxylate
    (-> whole group folds into node), or "false alarm" like a methoxy oxygen
    (-> stays linker)."""
    nodes: Set[int] = {i for i in range(geom.n) if geom.is_metal[i]}

    # first shell: every atom directly bonded to a node (metal) atom
    candidates: Set[int] = set()
    for m in list(nodes):
        for other, _vec, _bi in geom.adj[m]:
            candidates.add(other)

    for nn in candidates:
        if geom.symbols[nn] != 'O':
            continue   # nitrogen coordination case omitted -- see module docstring
        attached_carbon = None
        attached_h = []
        metal_oxide_or_carboxylate = True
        for other, _vec, _bi in geom.adj[nn]:
            if other in nodes:
                continue   # the metal(s) it's bonded to
            sym = geom.symbols[other]
            if sym == 'H':
                attached_h.append(other)
            elif sym == 'C':
                attached_carbon = other
            else:
                metal_oxide_or_carboxylate = False   # bonded to something else -> not a clean SBU oxygen

        if not metal_oxide_or_carboxylate:
            nodes.discard(nn)
            continue

        if attached_carbon is None:
            # Genuine metal oxide/hydroxide/aqua oxygen
            nodes.add(nn)
            nodes.update(attached_h)
            continue

        # Candidate carboxylate oxygen -- verify the carbon's valence
        c_c_nbors, c_o_nbors, other_o = 0, 0, None
        for cnb, _vec, _bi in geom.adj[attached_carbon]:
            if geom.symbols[cnb] == 'C':
                c_c_nbors += 1
            elif geom.symbols[cnb] == 'O':
                c_o_nbors += 1
                if cnb != nn:
                    other_o = cnb
        is_carboxylate = (c_c_nbors == 1 and c_o_nbors == 2)

        if not is_carboxylate:
            nodes.discard(nn)   # e.g. a methoxy/ether oxygen -- stays with the linker
        else:
            nodes.add(nn)
            nodes.add(attached_carbon)
            if other_o is not None:
                nodes.add(other_o)
                for onb, _vec, _bi in geom.adj[other_o]:
                    if geom.symbols[onb] == 'H':
                        nodes.add(onb)
            nodes.update(attached_h)

    return nodes


def run_single_node(geom: Geometry):
    """Returns (node_blocks, linker_blocks) exactly like code_04a.run_metal_oxo,
    ready for code_05.py's centroid collapse."""
    nodes = detect_initial_nodes_and_linkers_single_node(geom)
    linkers = set(range(geom.n)) - nodes
    node_blocks = _connected_components(nodes, geom.bonds)
    linker_blocks = _connected_components(linkers, geom.bonds)
    return node_blocks, linker_blocks


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif)
    node_blocks, linker_blocks = run_single_node(geom)
    print(f'Module 4b (single-node) result for {path}:')
    print(f'  {len(node_blocks)} node blocks   (sizes: {[len(b) for b in node_blocks]})')
    print(f'  {len(linker_blocks)} linker blocks (sizes: {[len(b) for b in linker_blocks]})')
    print('  (compare to code_04a.py\'s metal-oxo result on the same file -- single-node\'s '
          'node blocks should be noticeably larger, since carboxylates fold in here.)')
