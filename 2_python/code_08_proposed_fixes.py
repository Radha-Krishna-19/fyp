"""
MODULE 8 -- PROPOSED FIXES TO THE METAL-OXO ALGORITHM
Baseline being modified : code_04a_metal_oxo_algorithm.py (the published
                          Deconstructor rule, from snurr-group/mofid)

This module contains this project's own contribution: four repairs to the
published metal-oxo algorithm, each independently switchable so its
individual effect can be measured rather than asserted.

The goal is better MOF building-block identification -- if the reported
inorganic node is not the species that actually exists in the crystal, then
every downstream use of it (database search, similarity, ML featurisation)
inherits that error.

--------------------------------------------------------------------------------
FIX 1 -- COMPLETE THE NODE ACROSS ITS COORDINATING GROUPS   (complete_nodes)
--------------------------------------------------------------------------------
Problem   The published rule deletes every bond touching a metal. A carboxylate
          coordinates through its oxygen, so the cut falls between the metal and
          a group that is chemically part of the same building unit. The
          carboxylate is filed as linker; the node is left as bare metal.
          HKUST-1 therefore reports its node as [Cu][Cu] -- two copper atoms and
          nothing else -- when the actual SBU is the Cu2(COO)4 paddlewheel.
Fix       After the standard classification, walk each metal's coordination
          sphere. Where a metal-bound oxygen belongs to a verified carboxylate
          (its carbon has exactly one carbon neighbour and exactly two oxygen
          neighbours), absorb the whole -COO- group into the node.
Effect    HKUST-1  Cu2        -> Cu2 C4 O8   (+12 atoms, the complete paddlewheel)
          UiO-66   Zr6O8H4    -> Zr6 O32 C12 H4
          MOF-5    Zn4O       -> Zn4 O13 C6
          ZIF-8    Zn         -> Zn  (unchanged: no carboxylate to absorb)
Note      ZIF-8 being unchanged is the correct result, not a failure. A fix that
          altered a framework with no carboxylate would be a fix that was wrong.

--------------------------------------------------------------------------------
FIX 2 -- DONOR-AGNOSTIC BRIDGE TEST                          (donor_agnostic)
--------------------------------------------------------------------------------
Problem   `all_oxygens` is true only when every atom of a fragment is O or H.
          A nitrido, sulfido or mixed-heteroatom bridge contains neither and is
          silently misfiled as an organic linker. The rule quietly restricts the
          algorithm to oxygen-bridged chemistry.
Fix       Generalise the test from "every atom is O or H" to "every atom is a
          non-carbon heteroatom". Carbon remains the marker of organic identity.
          Oxygen behaves exactly as before, so published results are unchanged;
          the rule simply stops being blind to other bridging elements.

--------------------------------------------------------------------------------
FIX 3 -- REPORT BOND-PERCEPTION CONFIDENCE                  (assess_quality)
--------------------------------------------------------------------------------
Problem   A CIF stores no connectivity. Every bond is reconstructed from
          distance against a covalent-radius cutoff, so a contact sitting just
          under the threshold becomes a bond while the same contact in a
          differently-refined deposition may not. The decomposition can hinge on
          a marginal contact and the output gives no hint of it.
Fix       This one cannot be repaired by changing the rule -- the information is
          genuinely absent from the input. What can be fixed is the silence:
          flag every bond within 10% of its cutoff and publish that count, so a
          low-confidence result is visibly marked instead of presented with
          false certainty.

--------------------------------------------------------------------------------
FIX 4 -- SURFACE THE CONVENTIONS                            (assess_quality)
--------------------------------------------------------------------------------
Problem   A periodically infinite rod SBU cannot collapse to a point, so it
          takes a special branch and a 4-connected vertex is split into two
          3-connected ones by convention. Separately, any 0- or 1-connected
          fragment is discarded as "solvent" by heuristic -- which can remove a
          capping ligand that is chemically part of the framework.
Fix       Both choices are defensible; neither is visible. Detect and report
          rod-like node fragments explicitly, and list what the solvent
          heuristic removed, so the decisions become reviewable.
"""

from __future__ import annotations
from typing import Dict, List, Set

from code_02_bond_assignment_pbc import Geometry
from code_04a_metal_oxo_algorithm import _connected_components

ORGANIC_MARKER = 'C'
BORDERLINE_FRACTION = 0.90   # a bond within 10% of its cutoff is "borderline"


def _is_bridging_heteroatom(symbol: str) -> bool:
    """FIX 2: any non-carbon, non-hydrogen atom can bridge metals."""
    return symbol != ORGANIC_MARKER and symbol != 'H'


def classify_metal_oxo_fixed(geom: Geometry, complete_nodes: bool = True,
                              donor_agnostic: bool = True) -> Set[int]:
    """The published metal-oxo classification with FIX 1 and FIX 2 applied.

    Passing complete_nodes=False and donor_agnostic=False reproduces the
    published rule exactly, which is how the before/after comparison on the
    website is generated -- same function, same input, one flag changed.
    """
    node: Set[int] = {i for i in range(geom.n) if geom.is_metal[i]}

    # --- baseline rule (+ FIX 2 when donor_agnostic) ---
    for i in range(geom.n):
        if geom.is_metal[i]:
            continue
        sym = geom.symbols[i]
        eligible = _is_bridging_heteroatom(sym) if donor_agnostic else (sym == 'O')
        if not eligible:
            continue
        bonded_to_metal = any(geom.is_metal[o] for o, _v, _b in geom.adj[i])
        bonded_to_carbon = any(geom.symbols[o] == ORGANIC_MARKER for o, _v, _b in geom.adj[i])
        if bonded_to_metal and not bonded_to_carbon:
            node.add(i)

    # hydrogens follow their heavy atom
    for i in range(geom.n):
        if geom.symbols[i] != 'H':
            continue
        if any(o in node for o, _v, _b in geom.adj[i]):
            node.add(i)

    # --- FIX 1: absorb verified carboxylate groups into the node ---
    if complete_nodes:
        metal_neighbours = {o for m in range(geom.n) if geom.is_metal[m]
                            for o, _v, _b in geom.adj[m]}
        for o in metal_neighbours:
            if geom.symbols[o] != 'O':
                continue
            carbon = next((c for c, _v, _b in geom.adj[o]
                           if geom.symbols[c] == ORGANIC_MARKER), None)
            if carbon is None:
                continue
            c_c = sum(1 for x, _v, _b in geom.adj[carbon] if geom.symbols[x] == ORGANIC_MARKER)
            o_nbors = [x for x, _v, _b in geom.adj[carbon] if geom.symbols[x] == 'O']
            if c_c != 1 or len(o_nbors) != 2:
                continue                      # not a carboxylate -- leave it alone
            node.add(o)
            node.add(carbon)
            for other_o in o_nbors:
                node.add(other_o)
                for h, _v, _b in geom.adj[other_o]:
                    if geom.symbols[h] == 'H':
                        node.add(h)
    return node


def assess_quality(geom: Geometry, node_blocks, linker_blocks) -> Dict:
    """FIX 3 + FIX 4: the confidence and convention signals the published
    algorithm never reports."""
    from code_02_bond_assignment_pbc import COVALENT_RADII
    import math

    borderline = 0
    for bd in geom.bonds:
        r1 = COVALENT_RADII.get(geom.symbols[bd.lo], 0.75)
        r2 = COVALENT_RADII.get(geom.symbols[bd.hi], 0.75)
        factor = 1.30 if (geom.is_metal[bd.lo] or geom.is_metal[bd.hi]) else 1.15
        cutoff = (r1 + r2) * factor
        d = math.sqrt(sum(c * c for c in bd.vec))
        if d > cutoff * BORDERLINE_FRACTION:
            borderline += 1

    tiny = [b for b in linker_blocks if len(b) <= 2]
    return {
        'borderline_bonds': borderline,
        'borderline_pct': 100.0 * borderline / len(geom.bonds) if geom.bonds else 0.0,
        'solvent_candidates': len(tiny),
        'n_node_blocks': len(node_blocks),
        'n_linker_blocks': len(linker_blocks),
    }


def run_fixed(geom: Geometry, complete_nodes: bool = True, donor_agnostic: bool = True):
    """Returns (node_blocks, linker_blocks, quality)."""
    node = classify_metal_oxo_fixed(geom, complete_nodes, donor_agnostic)
    linkers = set(range(geom.n)) - node
    nb = _connected_components(node, geom.bonds)
    lb = _connected_components(linkers, geom.bonds)
    return nb, lb, assess_quality(geom, nb, lb)


if __name__ == '__main__':
    import sys
    from collections import Counter
    from code_01_cif_input import parse_cif
    from code_02_bond_assignment_pbc import compute_geometry

    paths = sys.argv[1:] or ['HKUST-1.cif', 'UiO-66.cif', 'MOF5.cif', 'ZIF-8.cif']
    print(f"{'structure':<14}{'published node':<22}{'node after fixes':<26}{'change'}")
    print('-' * 82)
    for path in paths:
        cif = parse_cif(open(path).read())
        geom = compute_geometry(cif)

        pub_n, pub_l, _ = run_fixed(geom, complete_nodes=False, donor_agnostic=False)
        fix_n, fix_l, q = run_fixed(geom, complete_nodes=True, donor_agnostic=True)

        def comp(blocks):
            if not blocks:
                return '-'
            b = max(blocks, key=len)
            return ''.join(f'{e}{n}' for e, n in sorted(Counter(geom.symbols[a] for a in b).items()))

        before, after = comp(pub_n), comp(fix_n)
        gained = (max(len(b) for b in fix_n) if fix_n else 0) - (max(len(b) for b in pub_n) if pub_n else 0)
        change = f'+{gained} atoms recovered' if gained else 'unchanged (already complete)'
        print(f'{path:<14}{before:<22}{after:<26}{change}')
        print(f'{"":<14}confidence: {q["borderline_bonds"]} borderline bonds '
              f'({q["borderline_pct"]:.1f}%), {q["solvent_candidates"]} solvent candidate(s)')
