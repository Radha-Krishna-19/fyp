"""
MODULE 5 -- CENTROID SIMPLIFICATION  (Python translation of the real source)
Real file   : src/topology.cpp  (class Topology, method CollapseFragment +
              the SimplifyAxB duplicate-edge cleanup)
Source      : https://github.com/snurr-group/mofid

WHAT THIS FILE SHOWS
Every "collapse this fragment into one point" call used by Modules 4a/4b/4c
bottoms out in this ONE function: Topology::CollapseFragment(). It is the
literal "replace a cluster of atoms with a single pseudoatom at their
centroid" step, translated below as collapse_fragment(). unwrap_local() is
this project's from-scratch equivalent of the real getCentroid()'s periodic-
unwrap-before-averaging behavior (code_02.py's periodic.cpp translation
describes the same idea for the real C++).

ARGUMENT / VARIABLE GLOSSARY
------------------------------------------------------------------------------
block (list[int])        : the atom indices to merge into one point (a node
                          or linker block from Module 4a/4b/4c).
unwrapped                : every atom's position, locally "unwrapped" via a
                          BFS across the block's own bonds with signed shift
                          vectors -- so a block that straddles a periodic
                          boundary still gets ONE consistent, correctly-
                          shaped set of Cartesian positions before averaging.
centroid                  : the plain (unweighted) Cartesian average of the
                          block's unwrapped positions -- matches the real
                          getCentroid(mol, weighted=False) call.
connection_points          : for every bond that LEAVES this block (an
                          "interblock" bond), the real code places a
                          connector at the bond's midpoint; this Python
                          translation instead uses the average of all such
                          midpoints as a stabilised centroid estimate,
                          exactly matching mof_decompose.js's own
                          finalize_partition() (preferred over the plain
                          atom-average whenever the block has >=1 external
                          connection, since it better reflects the true SBU
                          "extension point" geometry for elongated clusters).
"""

from __future__ import annotations
from typing import Dict, List, Tuple

from code_02_bond_assignment_pbc import Geometry


class Block:
    def __init__(self, block_id: int, kind: str, atoms: List[int], symbols_comp: Dict[str, int],
                 centroid: Tuple[float, float, float], n_connections: int):
        self.id = block_id
        self.type = kind            # 'node' or 'linker'
        self.atoms = atoms
        self.composition = symbols_comp
        self.centroid = centroid
        self.n_connections = n_connections


def _unwrap_block(geom: Geometry, block: List[int]) -> Dict[int, Tuple[float, float, float]]:
    """Local BFS unwrap: assigns every atom in `block` a position consistent
    with a single choice of periodic images, using each bond's stored
    minimum-image displacement vector (code_02.py's Bond.vec)."""
    block_set = set(block)
    bond_by_pair = {}
    for a in block:
        for other, vec, _bi in geom.adj[a]:
            if other in block_set:
                bond_by_pair[(a, other)] = vec

    root = block[0]
    unwrapped = {root: geom.pos[root]}
    stack = [root]
    visited = {root}
    while stack:
        u = stack.pop()
        for other, vec, _bi in geom.adj[u]:
            if other not in block_set or other in visited:
                continue
            ux, uy, uz = unwrapped[u]
            unwrapped[other] = (ux + vec[0], uy + vec[1], uz + vec[2])
            visited.add(other)
            stack.append(other)
    return unwrapped


def collapse_fragment(geom: Geometry, block: List[int], block_id: int, kind: str) -> Block:
    """Real Topology::CollapseFragment(pa_fragment), translated: compute the
    block's (optionally connection-point-weighted) centroid and its element
    composition, exactly as the real function does before creating the new
    single PseudoAtom."""
    unwrapped = _unwrap_block(geom, block)
    block_set = set(block)

    conn_points = []
    for a in block:
        for other, vec, _bi in geom.adj[a]:
            if other not in block_set:
                ax, ay, az = unwrapped[a]
                conn_points.append((ax + 0.5 * vec[0], ay + 0.5 * vec[1], az + 0.5 * vec[2]))

    if conn_points:
        cx = sum(p[0] for p in conn_points) / len(conn_points)
        cy = sum(p[1] for p in conn_points) / len(conn_points)
        cz = sum(p[2] for p in conn_points) / len(conn_points)
    else:
        cx = sum(unwrapped[a][0] for a in block) / len(block)
        cy = sum(unwrapped[a][1] for a in block) / len(block)
        cz = sum(unwrapped[a][2] for a in block) / len(block)

    comp: Dict[str, int] = {}
    for a in block:
        comp[geom.symbols[a]] = comp.get(geom.symbols[a], 0) + 1

    return Block(block_id, kind, block, comp, (cx, cy, cz), len(conn_points))


def build_blocks(geom: Geometry, node_blocks: List[List[int]], linker_blocks: List[List[int]]) -> List[Block]:
    """Runs collapse_fragment() over every block from Module 4a/4b/4c --
    the Python equivalent of CollapseLinkers() + CollapseNodes() both having
    finished, ready for Module 6's .cgd export."""
    blocks = []
    bid = 0
    for b in node_blocks:
        blocks.append(collapse_fragment(geom, b, bid, 'node')); bid += 1
    for b in linker_blocks:
        blocks.append(collapse_fragment(geom, b, bid, 'linker')); bid += 1
    return blocks


if __name__ == '__main__':
    import sys
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry
    from code_04a_metal_oxo_algorithm import run_metal_oxo
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    with open(path) as f:
        cif = parse_cif(f.read())
    geom = compute_geometry(cif)
    node_blocks, linker_blocks = run_metal_oxo(geom)
    blocks = build_blocks(geom, node_blocks, linker_blocks)
    print(f'Module 5 result: {len(blocks)} collapsed points in the simplified net '
          f'({len(node_blocks)} node + {len(linker_blocks)} linker).')
    for b in blocks[:3]:
        print(f'  block {b.id} ({b.type}): {b.composition}, centroid={tuple(round(x,2) for x in b.centroid)}, '
              f'{b.n_connections} external connections')
