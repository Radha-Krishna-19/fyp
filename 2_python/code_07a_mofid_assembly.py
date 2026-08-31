"""
MODULE 7a — MOFid ASSEMBLY (real source)
File in the real repo : Python/run_mofid.py
Source                 : https://github.com/snurr-group/mofid
Paper                  : Bucior et al., Cryst. Growth Des. 2019, 19, 6487-6495

WHAT THIS FILE SHOWS
Modules 1-6 (all C++, see code_00/04a/04b/04c/05/06) only ever produce
intermediate artifacts on disk: per-block SMILES text files and a
topology.cgd file per algorithm. This Python file is the actual glue that
runs the C++ binary, reads those artifacts back off disk, and assembles the
final MOFid string handed to the user. It is the real, un-simplified
implementation of "Module 7a" from the pipeline description.

ARGUMENT / VARIABLE GLOSSARY
--------------------------------------------------------------------------------
cif_path                 : path to the input .cif (Module 1's raw input).
output_path               : directory where the C++ binary already wrote its
                            SMILES/topology files (defaults to "Output").
extract_fragments(...)    : (defined in mofid.id_constructor, not reproduced
                            here) runs the C++ `bin/sbu` executable under the
                            hood via subprocess, then parses the resulting
                            python_smiles_parts.txt into two lists of SMILES
                            strings (node_fragments, linker_fragments), plus
                            the catenation count `cat` and a `base_mofkey`
                            string (the metal + linker InChIKey portion,
                            still missing its topology field).
node_fragments /
linker_fragments (list[str]) : canonical SMILES strings for every unique
                            inorganic node and organic linker found by the
                            metal-oxo algorithm (Module 4a) -- this is exactly
                            the "Output (inorganic)" / "Output (organic)" data
                            described in the pipeline write-up.
cat (int or None)         : catenation count from CheckCatenation() (code_04a's
                            sibling method); None if no MOF/net was found at all.
sn_topology / an_topology : the RCSR three-letter codes read back from the
                            Single-Node and All-Node algorithms' own
                            topology.cgd -> Systre runs (Module 6), via
                            extract_topology() parsing Systre's stdout/output.
topology (str)            : sn_topology alone if it matches an_topology (or if
                            an_topology errored out); otherwise BOTH codes,
                            comma-joined, e.g. "nbo,fof" -- this directly
                            implements the pipeline's "always report single-
                            node topology alongside any differing all-node
                            result" rule.
mof_name (str)            : the CIF's filename (without extension), used only
                            as a free-text comment/label in the final string.
mofkey (str)              : starts as `base_mofkey` (metal(s) + linker
                            InChIKey(s), from the C++ layer's GetMOFkey() --
                            see code_07b); assemble_mofkey() (in
                            id_constructor.py) appends the resolved topology
                            code to finish it off, exactly matching Module 7b's
                            "METAL(S).InChIKey1[...].MOFkey-v1.TOPOLOGY" format.
commit_ref (str)          : the short git commit hash of the MOFid installation
                            that generated this ID, read from .git/ORIG_HEAD --
                            included so results can be traced back to the exact
                            version of the algorithm that produced them (falls
                            back to 'NO_REF' if not running from a git checkout).
all_fragments (list[str]) : node_fragments + linker_fragments, concatenated
                            then SORTED ALPHABETICALLY -- this is exactly the
                            "SMILES sorting" step described in the pipeline
                            (ensures the same MOF always yields byte-identical
                            MOFid output, independent of internal atom order).
assemble_mofid(...)       : (in id_constructor.py) joins all_fragments with the
                            SMILES dot-notation, appends a TAB, then the
                            "MOFid-v1.TOPO[,ALT_TOPO].catN;comment" metadata
                            block -- this is the literal string format
                            documented in the pipeline's Module 7a section.
identifiers (dict)        : the final bundled result returned to the caller,
                            containing both assembled ID strings plus their
                            raw ingredients (individual SMILES, topology, cat,
                            cif name) for programmatic use.
--------------------------------------------------------------------------------
"""

import sys
import os
import json
from mofid.id_constructor import (extract_fragments, extract_topology,
    assemble_mofkey, assemble_mofid, parse_mofid)
from mofid.cpp_cheminformatics import openbabel_GetSpacedFormula

DEFAULT_OUTPUT_PATH = 'Output'


def cif2mofid(cif_path, output_path=DEFAULT_OUTPUT_PATH):
    # Assemble the MOFid string from all of its pieces (Modules 1-6's outputs).
    # Also exports the MOFkey (Module 7b) in the same result dict for convenience.
    cif_path = os.path.abspath(cif_path)
    output_path = os.path.abspath(output_path)

    # Runs the real C++ pipeline (code_00/04a/04b/04c) under the hood, then
    # parses its SMILES + catenation output back from disk.
    node_fragments, linker_fragments, cat, base_mofkey = extract_fragments(
        cif_path, output_path)

    if cat is not None:
        # Read the RCSR topology codes Systre computed for both the single-node
        # and all-node simplified nets (Module 6's external Java subprocess).
        sn_topology = extract_topology(os.path.join(output_path, 'SingleNode', 'topology.cgd'))
        an_topology = extract_topology(os.path.join(output_path, 'AllNode', 'topology.cgd'))
        if sn_topology == an_topology or an_topology == 'ERROR':
            topology = sn_topology
        else:
            # Report both, comma-separated, when they genuinely differ
            topology = sn_topology + ',' + an_topology
    else:
        topology = 'NA'   # no MOF/net could be resolved at all

    mof_name = os.path.splitext(os.path.basename(cif_path))[0]
    mofkey = base_mofkey
    try:
        with open('.git/ORIG_HEAD', mode='r') as f:
            commit_ref = f.read()[:8]
    except OSError:
        commit_ref = 'NO_REF'

    if topology != 'NA':
        base_topology = topology.split(',')[0]
        mofkey = assemble_mofkey(mofkey, base_topology, commit_ref=commit_ref)

    # Combine node + linker SMILES and sort alphabetically for a canonical,
    # atom-order-independent MOFid string.
    all_fragments = []
    all_fragments.extend(node_fragments)
    all_fragments.extend(linker_fragments)
    all_fragments.sort()

    mofid = assemble_mofid(all_fragments, topology, cat=cat,
                            mof_name=mof_name, commit_ref=commit_ref)
    parsed = parse_mofid(mofid)

    identifiers = {
        'mofid': mofid,
        'mofkey': mofkey,
        'smiles_nodes': node_fragments,
        'smiles_linkers': linker_fragments,
        'smiles': parsed['smiles'],
        'topology': parsed['topology'],
        'cat': parsed['cat'],
        'cifname': parsed['name'],
    }

    # Persist every piece to disk too, for downstream tooling / debugging
    with open(os.path.join(output_path, 'python_mofid.txt'), 'w') as f:
        f.write(identifiers['mofid'] + '\n')
    with open(os.path.join(output_path, 'python_mofkey.txt'), 'w') as f:
        f.write(identifiers['mofkey'] + '\n')
    with open(os.path.join(output_path, 'python_smiles_parts.txt'), 'w') as f:
        for smiles in node_fragments:
            f.write('node' + '\t' + smiles + '\n')
        for smiles in linker_fragments:
            f.write('linker' + '\t' + smiles + '\n')
    with open(os.path.join(output_path, 'python_molec_formula.txt'), 'w') as f:
        f.write(openbabel_GetSpacedFormula(
            os.path.join(output_path, 'orig_mol.cif'), ' ', False) + '\n')

    return identifiers


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) not in [1, 2, 3]:
        raise SyntaxError('Usage: python run_mofid.py path_to_cif_for_analysis.cif OutputPathIfNonstandard OutputMofidOrJson')
    cif_file = args[0]
    output_path = DEFAULT_OUTPUT_PATH
    output_json = False
    if len(args) >= 2:
        output_path = args[1]
    if len(args) == 3:
        if args[2] == "json":
            output_json = True
        elif args[2] != "mofid":
            raise SyntaxError('Third argument must be json, mofid, or not provided')

    identifiers = cif2mofid(cif_file, output_path)
    if output_json:
        print(json.dumps(identifiers))
    else:
        print(identifiers['mofid'])
