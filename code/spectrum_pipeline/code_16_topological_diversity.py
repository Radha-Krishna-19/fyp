"""
MODULE 16 -- A TOPOLOGICALLY DIVERSE COMPARISON SET, CAPPED

WHY THIS MODULE EXISTS
docs/project_notes.md records that ~48 of 76 hMOF structures are the same 4x4x4 pcu net,
so the published hMOF sample cannot show band structure across topologies --
it barely contains more than one topology. This module assembles a genuinely
diverse comparison set from what is available locally (the four demonstration
structures with published net assignments, plus CIFs already fetched for
earlier tasks) and shows what real topological variation looks
like against that degenerate sample.

HOW NETS ARE IDENTIFIED HERE -- AND THE HONEST LIMIT OF THIS METHOD
This project's proper route to a net symbol is code_06 (writes a .cgd file)
fed to Systre, which is Java software not installed in this environment.
Absent that, this module classifies structures by their COORDINATION
SIGNATURE -- the (node degree, linker degree) pair -- which is enough to
name a net ONLY for the simple, single-node-type cases already discussed
elsewhere on this site:
    6-connected node + 2-connected linker  -> pcu   (MOF-5)
    4-connected node + 3-connected linker  -> tbo   (HKUST-1)
    4-connected node + 2-connected linker  -> sod   (ZIF-8; both node types
                                                      4-connected, giving the
                                                      sodalite cage topology)
    12-connected node + 2-connected linker -> fcu   (UiO-66)
This heuristic is stated explicitly because it is NOT a general net
classifier: rht nets, in particular, typically combine TWO node
connectivities (commonly 3- and 4-connected) in one framework, which this
simple pairing cannot recognise, and no structure in the local sample was
found to have an rht-net signature by any method available here. That gap
is reported rather than papered over with a guess.

CAP (explicit project limit for this module)
At most 10 structures, drawn from: the 4 demonstration structures (published
net, ground truth) plus CIFs already fetched for earlier tasks
(hmof_cifs/, core_cifs/) -- no new downloads for this module specifically.
Supercell replication for any comparison figure is the same MAX_NODES cap
used in code_15.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

import networkx as nx

from code_12_converged_band import quotient_graph_from_cif

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

import sys
_USE_ALL = '--all' in sys.argv
sys.argv = [a for a in sys.argv if a != '--all']


def capped_pool(cif_dir):
    """The CIFs this capped analysis originally ran on (15 September 2026), so its committed result can
    be regenerated. Returns None (use every CIF) with --all, or when no list exists for this folder."""
    if _USE_ALL:
        return None
    name = {'hmof': 'capped_pool_hmof.txt', 'core_mof_2019': 'capped_pool_core.txt'}.get(
        os.path.basename(os.path.normpath(cif_dir)))
    path = os.path.join(REPO, 'data', 'spectrum_descriptors', 'size_scaling', name) if name else None
    if not path or not os.path.exists(path):
        return None
    return set(l.strip() for l in open(path) if l.strip() and not l.startswith('#'))


SIGNATURE_TO_NET = {
    (6, 2): 'pcu',
    (4, 3): 'tbo',
    (4, 2): 'sod',
    (12, 2): 'fcu',
}


def coordination_signature(cif_path):
    """(node_degree, linker_degree) for the MOST COMMON degree of each block
    kind -- a single representative pair, which is all the simple nets above
    need. Returns None if the structure has more than one distinct degree
    among either node or linker blocks (multi-node-type net -- outside this
    heuristic's scope, honestly reported as such by the caller)."""
    blocks, edges, _geom = quotient_graph_from_cif(cif_path)
    deg = Counter()
    for i, j, _t in edges:
        deg[i] += 1
        deg[j] += 1
    node_degs = Counter(deg[i] for i, (kind, _b) in enumerate(blocks) if kind == 'node')
    linker_degs = Counter(deg[i] for i, (kind, _b) in enumerate(blocks) if kind == 'linker')
    if not node_degs or not linker_degs:
        return None, 'no node or no linker blocks'
    if len(node_degs) > 1 or len(linker_degs) > 1:
        return None, f'multi-connectivity: node degrees {dict(node_degs)}, linker degrees {dict(linker_degs)}'
    node_d = next(iter(node_degs))
    linker_d = next(iter(linker_degs))
    return (node_d, linker_d), None


def classify_directory(cif_dir, max_structures=None):
    pool = capped_pool(cif_dir)
    files = sorted(f for f in os.listdir(cif_dir) if f.lower().endswith('.cif') and (pool is None or f in pool))
    if max_structures:
        files = files[:max_structures]
    out = {}
    for f in files:
        name = os.path.splitext(f)[0]
        try:
            sig, reason = coordination_signature(os.path.join(cif_dir, f))
        except Exception as e:
            out[name] = {'ok': False, 'reason': f'{type(e).__name__}: {e}'}
            continue
        if sig is None:
            out[name] = {'ok': False, 'reason': reason}
        else:
            out[name] = {'ok': True, 'signature': sig,
                          'net_candidate': SIGNATURE_TO_NET.get(sig, 'unrecognised pairing')}
    return out


def build_diverse_set(demo_dir=None, hmof_dir=None, core_dir=None, target_size=10):
    """Assemble up to target_size structures spanning as many of
    {pcu, tbo, sod, fcu, rht} as this local sample allows, from the four
    demonstration structures (ground-truth net) plus already-fetched CIFs."""
    demo_nets = {'HKUST-1.cif': 'tbo', 'MOF5.cif': 'pcu', 'ZIF-8.cif': 'sod', 'UiO-66.cif': 'fcu'}
    # The demonstration CIFs live next to this script. (Until 12 November the default was the current
    # folder, so a run started elsewhere silently left all four out of the set.)
    demo_dir = demo_dir or os.path.dirname(os.path.abspath(__file__))
    rel = lambda p: os.path.relpath(p, REPO).replace(os.sep, '/')
    chosen = []
    for f, net in demo_nets.items():
        p = os.path.join(demo_dir, f)
        if os.path.exists(p):
            chosen.append({'cif': rel(p), 'name': f.replace('.cif', ''), 'net': net,
                            'source': 'demonstration set, published net'})

    pools = []
    if hmof_dir and os.path.isdir(hmof_dir):
        pools.append(('hMOF', hmof_dir))
    if core_dir and os.path.isdir(core_dir):
        pools.append(('CoRE MOF', core_dir))

    seen_signatures = {demo_nets[f + '.cif' if not f.endswith('.cif') else f]
                        for f in [] }  # placeholder, unused
    found_nets = set(demo_nets.values())
    candidates_by_net = defaultdict(list)
    unclassified = []

    for pool_label, pool_dir in pools:
        cls = classify_directory(pool_dir)
        for name, rec in cls.items():
            if not rec.get('ok'):
                unclassified.append((pool_label, name, rec.get('reason')))
                continue
            net = rec['net_candidate']
            candidates_by_net[net].append((pool_label, name))

    # First pass: add structures whose net is NOT yet covered (genuine new
    # diversity). Second pass, only if slots remain: add up to 2 more of an
    # already-covered net, so the set does not silently pad itself with
    # duplicates of the one net the local sample happens to be full of.
    already_covered = set(found_nets)
    remaining = target_size - len(chosen)
    added = []
    dup_budget = 2

    def take(net_filter):
        nonlocal remaining, dup_budget
        for net, items in candidates_by_net.items():
            if remaining <= 0:
                return
            if net == 'unrecognised pairing' or not net_filter(net):
                continue
            for pool_label, name in items:
                if remaining <= 0 or (net in already_covered and dup_budget <= 0):
                    break
                cif_dir = hmof_dir if pool_label == 'hMOF' else core_dir
                added.append({'cif': rel(os.path.join(cif_dir, name + '.cif')), 'name': name,
                              'net': net, 'source': f'{pool_label}, connectivity-signature candidate'})
                if net in already_covered:
                    dup_budget -= 1
                else:
                    found_nets.add(net)
                remaining -= 1

    take(lambda n: n not in already_covered)   # new nets first
    take(lambda n: True)                        # then duplicates, capped above

    result = {
        'chosen': chosen + added,
        'nets_covered': sorted(found_nets),
        'nets_missing': sorted((set(SIGNATURE_TO_NET.values()) | {'rht'}) - found_nets),
        'n_unclassified': len(unclassified),
        'unclassified_examples': unclassified[:5],
        'pool_signature_tally': {net: len(items) for net, items in candidates_by_net.items()},
    }
    return result


if __name__ == '__main__':
    import sys
    hmof_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'data', 'structures', 'hmof')
    core_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'data', 'structures', 'core_mof_2019')

    result = build_diverse_set(hmof_dir=hmof_dir, core_dir=core_dir, target_size=10)

    print(f"Assembled {len(result['chosen'])} structures:")
    for c in result['chosen']:
        print(f"  {c['name']:36s} net_candidate={c['net']:5s} ({c['source']})")
    print(f"\nNets covered: {result['nets_covered']}")
    print(f"Nets NOT covered by anything in the local sample: {result['nets_missing']}")
    print(f"\n{result['n_unclassified']} structures in the pools had a multi-connectivity or "
          f"unrecognised signature (not classifiable by this heuristic, not necessarily rht):")
    for pool, name, reason in result['unclassified_examples']:
        print(f"  [{pool}] {name}: {reason}")

    out_path = os.path.join(REPO, 'data', 'spectrum_descriptors', 'size_scaling', 'topological_diversity.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as fh:
        json.dump(result, fh, indent=2, default=str)
    print(f'\nWritten to {out_path}')
