"""
MODULE 0 -- PIPELINE DRIVER  (Python translation of the real source)
Real file   : src/sbu.cpp  (main(), analyzeMOF())
Source      : https://github.com/snurr-group/mofid

WHAT THIS FILE SHOWS
The real `sbu` C++ binary's main() reads a CIF path from argv, calls
analyzeMOF() (which runs importCIF(), then all three Deconstructor
subclasses -- MetalOxo, SingleNode, AllNode -- one after another, writing
each one's simplified net + SMILES fragments + .cgd file to its own
Output/<Algorithm>/ subfolder), and returns the metal-oxo-derived MOFid
string. This file is the Python translation of that orchestration, wired up
to every other module in this folder (code_01 through code_07b) -- run it
directly to reproduce, end to end and entirely in Python, everything the
real compiled `sbu` binary does for a single CIF file.

USAGE
    python code_00_pipeline_driver.py HKUST-1.cif
"""

from __future__ import annotations
import sys

from code_01_cif_input import parse_cif
from code_02_bond_assignment_pbc import compute_geometry
from code_03_element_classification import METALS
from code_04a_metal_oxo_algorithm import run_metal_oxo
from code_04b_single_node_algorithm import run_single_node
from code_04c_all_node_algorithm import run_all_node
from code_05_centroid_simplification import build_blocks
from code_06_systre_topology_export import write_systre
from code_07b_mofkey_assembly import get_mofkey


def analyze_mof(cif_path: str, output_dir: str = 'Output') -> dict:
    """Real analyzeMOF(filename, output_dir), translated: runs Modules 1-6
    for all three algorithms, Module 7b for metal-oxo specifically (matching
    the real GetMOFkey()'s own restriction), and returns a summary dict."""
    with open(cif_path) as f:
        cif = parse_cif(f.read())                              # Module 1
    geom = compute_geometry(cif, metal_set=METALS)               # Module 2 + 3

    results = {}
    for name, runner in (('MetalOxo', run_metal_oxo),
                          ('SingleNode', run_single_node),
                          ('AllNode', run_all_node)):
        node_blocks, linker_blocks = runner(geom)                # Module 4a/4b/4c
        blocks = build_blocks(geom, node_blocks, linker_blocks)  # Module 5
        import os
        os.makedirs(f'{output_dir}/{name}', exist_ok=True)
        write_systre(geom, blocks, f'{output_dir}/{name}/topology.cgd',
                     (cif.a, cif.b, cif.c, cif.alpha, cif.beta, cif.gamma),
                     name=name)                                  # Module 6
        results[name] = {
            'n_node_blocks': len(node_blocks), 'n_linker_blocks': len(linker_blocks),
            'node_blocks': node_blocks, 'linker_blocks': linker_blocks,
        }

    # Module 7b: MOFkey is built from the metal-oxo decomposition specifically
    mo = results['MetalOxo']
    mofkey = get_mofkey(geom, mo['node_blocks'], mo['linker_blocks'])   # Module 7

    return {
        'cif_path': cif_path, 'formula': geom.formula, 'n_atoms': geom.n,
        'n_bonds': len(geom.bonds), 'results': results, 'mofkey': mofkey,
    }


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'HKUST-1.cif'
    summary = analyze_mof(path)
    print(f"=== Pipeline driver result for {summary['cif_path']} ===")
    print(f"formula={summary['formula']}  atoms={summary['n_atoms']}  bonds={summary['n_bonds']}")
    for algo, r in summary['results'].items():
        print(f"  {algo:11s}: {r['n_node_blocks']} node blocks, {r['n_linker_blocks']} linker blocks")
    print(f"mofkey (Module 7b; metal+topology fields real, linker keys are placeholders): {summary['mofkey']}")
