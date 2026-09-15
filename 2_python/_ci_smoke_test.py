"""
CI SMOKE TEST -- fast, no-dependency-beyond-numpy/networkx checks that the
Python reference implementation still runs and still gets known answers
right. Not a substitute for the JS test suites (which check the browser
engine); this is the Python side's equivalent, run in GitHub Actions.

Runs in seconds, not minutes: it does NOT run the multifractal spectrum or
any supercell sweep (those take tens of seconds to minutes per structure --
see 2_python/code_12_converged_band.py and _run_size_scaling.py, which are
one-off analysis scripts, not CI checks). It checks the parts that must
never silently break: CIF parsing, PBC bond perception, the metal-oxo
decomposition, and the periodic quotient graph's coordination numbers
against published crystallography -- the same numbers the site's own
test_engines.js checks on the JavaScript side.

Exits non-zero (and prints which check failed) on any failure, so CI fails
loudly rather than a silently wrong number shipping.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_09_network_analysis import build_periodic_block_graph, coordination_numbers

# Published coordination number of the highest-degree node in each
# structure's unit cell -- the same figures the site's fig03 figure and
# test_engines.js check on the JS engine. See references [11]-[14] on the
# site's References page for the source of each number.
EXPECTED_MAX_NODE_DEGREE = {
    'HKUST-1.cif': 4,   # Cu paddlewheel, tbo net
    'MOF5.cif': 6,      # Zn4O node, pcu net
    'ZIF-8.cif': 4,     # tetrahedral Zn, sod net
    'UiO-66.cif': 12,   # Zr6 cluster, fcu net -- the case a naive (non-periodic)
                        # graph construction gets wrong (reports 6 or fewer)
}

failures = []


def check(label, condition):
    status = 'PASS' if condition else 'FAIL'
    print(f'  [{status}] {label}')
    if not condition:
        failures.append(label)


print('CI smoke test: Python reference pipeline\n')

for cif, expected_degree in EXPECTED_MAX_NODE_DEGREE.items():
    print(f'{cif}:')
    if not os.path.exists(cif):
        check(f'{cif} exists', False)
        continue

    cif_parsed = parse_cif(open(cif).read())
    check(f'{cif}: CIF parses to at least one atom', len(cif_parsed.atoms) > 0)

    geom = compute_geometry(cif_parsed)
    check(f'{cif}: bond perception finds at least one bond', len(geom.bonds) > 0)

    node_blocks, linker_blocks = run_metal_oxo(geom)
    check(f'{cif}: metal-oxo decomposition finds at least one node block', len(node_blocks) > 0)
    check(f'{cif}: metal-oxo decomposition finds at least one linker block', len(linker_blocks) > 0)

    blocks, edges = build_periodic_block_graph(geom, node_blocks, linker_blocks)
    deg = coordination_numbers(blocks, edges)
    node_degrees = [d for (kind, _b), d in zip(blocks, deg) if kind == 'node']
    max_node_degree = max(node_degrees) if node_degrees else 0
    check(f'{cif}: highest node coordination number is {expected_degree} '
          f'(published; a non-periodic graph would under-report this)',
          max_node_degree == expected_degree)
    print()

if failures:
    print(f'{len(failures)} check(s) FAILED:')
    for f in failures:
        print(f'  - {f}')
    sys.exit(1)

print('All Python smoke checks passed.')
