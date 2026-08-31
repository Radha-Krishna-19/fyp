"""
MODULE 4a -- THE ORIGINAL METAL-OXO ALGORITHM  (Python translation)
Real file   : src/deconstructor.cpp  (base class `Deconstructor` + its thin
              subclass `MetalOxoDeconstructor`)
Header      : src/deconstructor.h
Source      : https://github.com/snurr-group/mofid
Paper       : Bucior et al., "Identification schemes for metal-organic
              frameworks...", Cryst. Growth Des. 2019, 19, 6487-6495.

IMPORTANT DISCOVERY WHILE TRACING THE SOURCE (unchanged from the C++ version)
`MetalOxoDeconstructor` does NOT override DetectInitialNodesAndLinkers(),
CollapseLinkers(), or CollapseNodes(). It inherits every one of those
directly from the base `Deconstructor` class translated below, unchanged.
Its own code only adds PostSimplification() (rod-SBU cleanup) and InChI/
MOFkey export helpers (code_07b.py). In other words:

    THE "METAL-OXO ALGORITHM" *IS* THE BASE Deconstructor CLASS.

THE CORE IDEA IN ONE SENTENCE
Delete every bond that touches a metal atom, look at what molecular
fragments fall out, and classify each fragment as "node" (lone metal atoms,
or fragments made purely of O/H -- i.e. bridging oxo/hydroxo/aqua groups) or
"linker" (everything else, including carboxylate groups, because a
carboxylate carbon is only ever bonded to metal through its OXYGEN, so
cutting metal bonds leaves the whole -COO- group attached to the organic
ring it belongs to).

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
geom                    : this project's Geometry object (code_02.py) -- the
                          Python stand-in for parent_molp / orig_mof: the
                          untouched, all-atom, PBC-bonded structure. Never
                          modified in place by anything below.
split_bonds             : the REAL algorithm's "split_mol" scratch copy,
                          translated as just a filtered COPY of geom.bonds
                          with every metal-touching bond removed (via
                          code_03.delete_bonds) -- nothing about geom itself
                          is mutated.
fragments               : the disconnected atom-index groups left over after
                          removing those bonds -- Python's equivalent of
                          OBMol::Separate() on the bond-deleted scratch copy.
all_oxygens (bool)      : True if literally every atom in a fragment is O or
                          H. This is the ONLY test used to recognize a
                          genuine "metal-oxide" fragment (oxo/hydroxo/aqua/
                          peroxo bridge) versus an organic linker fragment --
                          there is no separate hydroxyl-vs-methoxy special
                          case in this original algorithm (added later, only
                          in single-node, code_04b.py).
role                    : dict[atom_index] -> 'node' | 'linker', the Python
                          equivalent of tagging each PseudoAtom's role via
                          simplified_net.SetRoleToAtoms().
node_set                : the final, RE-MERGED set of atom indices that will
                          collapse into node blocks -- computed by
                          collapse_nodes() below, which is the Python
                          translation of the real CollapseNodes()'s
                          "FragmentWithIntConns" re-merge step (two node
                          fragments that still share a bond of their own,
                          e.g. a Cu-Cu paddlewheel bond, get merged back into
                          ONE cluster here).
"""

from __future__ import annotations
from typing import Dict, List, Set

from code_02_bond_assignment_pbc import Geometry
from code_03_element_classification import delete_bonds


def _connected_components(atom_indices: Set[int], bonds) -> List[List[int]]:
    """Python translation of OBMol::Separate() / the VirtualMol connected-
    components walk used throughout the real Topology/VirtualMol classes:
    BFS the given bond list, restricted to `atom_indices`."""
    adj: Dict[int, List[int]] = {i: [] for i in atom_indices}
    for bd in bonds:
        if bd.lo in adj and bd.hi in adj:
            adj[bd.lo].append(bd.hi)
            adj[bd.hi].append(bd.lo)
    visited: Set[int] = set()
    comps: List[List[int]] = []
    for start in atom_indices:
        if start in visited:
            continue
        stack, comp = [start], []
        visited.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    stack.append(v)
        comps.append(sorted(comp))
    return comps


def detect_initial_nodes_and_linkers(geom: Geometry) -> Dict[int, str]:
    """STEP 1 -- real Deconstructor::DetectInitialNodesAndLinkers(), translated
    line-for-line:
        1. deleteBonds(&split_mol, true)          -- code_03.delete_bonds
        2. fragments = split_mol.Separate()        -- _connected_components
        3. for each fragment: NumAtoms()==1 / all_oxygens / else            """
    split_bonds = delete_bonds(geom, only_metals=True)          # 1. cut metal bonds
    fragments = _connected_components(set(range(geom.n)), split_bonds)  # 2. Separate()

    role: Dict[int, str] = {}
    for frag in fragments:                                       # 3. classify
        if len(frag) == 1:
            # A single, isolated atom (almost always a bare metal ion) -> node
            for a in frag:
                role[a] = 'node'
            continue
        all_oxygens = all(geom.symbols[a] in ('O', 'H') for a in frag)
        tag = 'node' if all_oxygens else 'linker'
        for a in frag:
            role[a] = tag
    return role


def collapse_nodes_merge(geom: Geometry, role: Dict[int, str]) -> List[List[int]]:
    """STEP 3 -- real Deconstructor::CollapseNodes()'s re-merge step,
    translated: node_pa = FragmentWithIntConns(GetAtomsOfRole("node")) then
    Separate(). Using the ORIGINAL (not bond-deleted) bond graph here is
    exactly what lets two node fragments from Step 1 that still share a bond
    of their own (e.g. a direct Cu-Cu paddlewheel bond) merge back into ONE
    cluster -- this is the moment metal-oxo's famously "tiny" nodes take
    their final shape. (The real infinite-rod branch, using isPeriodicChain,
    is omitted here for brevity -- see the full C++ file / code_02.py's
    is_periodic_chain() for that logic; none of this project's example
    structures contain a rod SBU.)"""
    node_atoms = {a for a, r in role.items() if r == 'node'}
    return _connected_components(node_atoms, geom.bonds)   # original graph, not bond-deleted


def collapse_linkers_separate(geom: Geometry, role: Dict[int, str]) -> List[List[int]]:
    """STEP 2 -- real Deconstructor::CollapseLinkers()'s fragment split:
    linker_pa = FragmentWithIntConns(GetAtomsOfRole("linker")).Separate().
    Each returned group later becomes one PseudoAtom via CollapseFragment()
    (code_05.py) -- metal-oxo never merges separate linker molecules the way
    collapse_nodes_merge() can merge node fragments."""
    linker_atoms = {a for a, r in role.items() if r == 'linker'}
    return _connected_components(linker_atoms, geom.bonds)


def run_metal_oxo(geom: Geometry):
    """The Python translation of Deconstructor::SimplifyMOF(), Steps 1-3 only
    (Step 4 SimplifyTopology / Step 5 PostSimplification are cleanup passes
    with no default-structure effect here -- see the real C++ for their full
    logic). Returns (node_blocks, linker_blocks): lists of atom-index groups,
    ready for code_05.py's centroid collapse."""
    role = detect_initial_nodes_and_linkers(geom)      # Step 1
    linker_blocks = collapse_linkers_separate(geom, role)   # Step 2
    node_blocks = collapse_nodes_merge(geom, role)           # Step 3
    return node_blocks, linker_blocks


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif)
    node_blocks, linker_blocks = run_metal_oxo(geom)
    print(f'Module 4a (metal-oxo) result for {path}:')
    print(f'  {len(node_blocks)} node blocks   (sizes: {[len(b) for b in node_blocks]})')
    print(f'  {len(linker_blocks)} linker blocks (sizes: {[len(b) for b in linker_blocks]})')
    if node_blocks:
        smallest = min(node_blocks, key=len)
        comp = {}
        for a in smallest:
            comp[geom.symbols[a]] = comp.get(geom.symbols[a], 0) + 1
        print(f'  smallest node block composition: {comp}  <- e.g. HKUST-1 gives {{"Cu": 2}}, matching [Cu][Cu] in the real MOFid paper')
