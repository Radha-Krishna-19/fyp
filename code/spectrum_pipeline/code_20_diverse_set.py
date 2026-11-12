"""The first half's graph stages on a diverse set of twelve MOFs, not only the four cubic
demonstration structures.

Run from anywhere:  python3 code/spectrum_pipeline/code_20_diverse_set.py
Writes data/spectrum_descriptors/size_scaling/diverse_set.json and diverse_set_figure.png.

The twelve differ in metal (Zn, Cu, Zr, Mg, Cr, V, Fe), in the kind of node (single metal
atom, paddlewheel, Zn4O, Zr6 and Fe3O clusters, infinite metal-oxide chains), in the linker
(two- and three-ended carboxylates, imidazolates, a pillar), and in the lattice (cubic,
trigonal, hexagonal, tetragonal, orthorhombic, monoclinic).

For each structure:
  1. the labelled quotient graph of the unit cell (code_12.quotient_graph_from_cif): how many
     node and linker blocks, their degrees, and whether the graph is one connected piece;
  2. the finite-size sweep of Delta-alpha with the same settings as the published four-net
     sweep (_run_size_scaling.py): n = 2, 3, 4, 6, 8 (stopping at 25 000 vertices), 20 trials,
     3 seeds, top 30 % influential, radii 1..D;
  3. the fitted slope of Delta-alpha against ln(diameter), its R^2, and the drift between the
     two largest supercells.
The question is the one the four-net sweep asked: does Delta-alpha settle to a value that
belongs to the framework, or keep growing with the size of the supercell?
"""
import os, sys, json, time, collections, warnings
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
warnings.filterwarnings('ignore')
import numpy as np
import networkx as nx
from code_12_converged_band import quotient_graph_from_cif, replicate, finite_size_sweep

GEN = os.path.join(REPO, 'data', 'structures', 'general_lattice')
OUT = os.path.join(REPO, 'data', 'spectrum_descriptors', 'size_scaling')
# name, file, metal, node, linker, lattice
SET = [
    ('MOF-5', os.path.join(HERE, 'MOF5.cif'), 'Zn', 'Zn4O cluster', 'BDC (two-ended)', 'cubic'),
    ('HKUST-1', os.path.join(HERE, 'HKUST-1.cif'), 'Cu', 'Cu2 paddlewheel', 'BTC (three-ended)', 'cubic'),
    ('UiO-66', os.path.join(HERE, 'UiO-66.cif'), 'Zr', 'Zr6 cluster', 'BDC', 'cubic'),
    ('ZIF-8', os.path.join(HERE, 'ZIF-8.cif'), 'Zn', 'single Zn atom', '2-methylimidazolate', 'cubic'),
    ('ZIF-7', os.path.join(GEN, 'ZIF-7.cif'), 'Zn', 'single Zn atom', 'benzimidazolate', 'trigonal'),
    ('MOF-177', os.path.join(GEN, 'MOF-177.cif'), 'Zn', 'Zn4O cluster', 'BTB (three-ended, large)', 'trigonal'),
    ('DMOF-1', os.path.join(GEN, 'DMOF-1.cif'), 'Zn', 'Zn2 paddlewheel', 'BDC and DABCO pillar', 'tetragonal'),
    ('MIL-88A (open)', os.path.join(GEN, 'MIL-88A-open.cif'), 'Fe', 'Fe3O trimer', 'fumarate', 'hexagonal'),
    ('Mg-MOF-74', os.path.join(GEN, 'MgMOF-74.cif'), 'Mg', 'Mg-O chain (rod)', 'dobdc', 'trigonal'),
    ('MIL-53(Cr)', os.path.join(GEN, 'MIL-53Cr-lt.cif'), 'Cr', 'Cr-OH chain (rod)', 'BDC', 'monoclinic'),
    ('MIL-47(V)', os.path.join(GEN, 'MIL-47.cif'), 'V', 'V=O chain (rod)', 'BDC', 'orthorhombic'),
    ('MIL-140A', os.path.join(GEN, 'MIL-140A.cif'), 'Zr', 'Zr-O chain (rod)', 'BDC', 'monoclinic'),
]


def graph_summary(path):
    blocks, edges, geom = quotient_graph_from_cif(path)
    deg = collections.Counter()
    for i, j, t in edges:
        deg[i] += 1; deg[j] += 1
    by = collections.defaultdict(list)
    for i, b in enumerate(blocks):
        by[b[0]].append(deg[i])
    node_node = sum(1 for i, j, t in edges if blocks[i][0] == 'node' and blocks[j][0] == 'node')
    G, _ = replicate(blocks, edges, 2)
    return dict(atoms=len(geom['symbols']) if isinstance(geom, dict) and 'symbols' in geom else None,
                node_blocks=len(by['node']), linker_blocks=len(by['linker']), edges=len(edges),
                node_degrees=sorted(set(by['node'])), linker_degrees=sorted(set(by['linker'])),
                node_node_edges=node_node,
                components_n2=nx.number_connected_components(nx.Graph(G)))


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'diverse_set.json')
    res = json.load(open(path)) if os.path.exists(path) else {}
    for name, cif, metal, node, linker, lattice in SET:
        if only and name not in only:
            continue
        t0 = time.time()
        print(f'\n=== {name} ===', flush=True)
        g = graph_summary(cif)
        print('  graph', g, flush=True)
        sweep = finite_size_sweep(cif, n_values=(2, 3, 4, 6, 8), n_trials=20, n_seeds=3, max_nodes=25000, verbose=True)
        rows = [dict(n=r['n'], cg_nodes=r['cg_nodes'], diameter=r['diameter'], width_mean=r['width_mean'], width_sd=r['width_sd'])
                for r in sweep]
        fit = None
        if len(rows) >= 3:
            x = np.log([r['diameter'] for r in rows]); y = np.array([r['width_mean'] for r in rows])
            A = np.vstack([x, np.ones_like(x)]).T
            (m, c), *_ = np.linalg.lstsq(A, y, rcond=None)
            yhat = m * x + c
            r2 = 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2)
            fit = dict(slope=float(m), intercept=float(c), r2=float(r2),
                       drift_last_two=float(abs(y[-1] - y[-2]) / y[-1]))
        res[name] = dict(file=os.path.relpath(cif, REPO), metal=metal, node=node, linker=linker, lattice=lattice,
                         graph=g, sweep=rows, fit=fit, seconds=round(time.time() - t0, 1))
        json.dump(res, open(path, 'w'), indent=1)
        print(f'  fit {fit}  ({time.time() - t0:.0f}s)', flush=True)
    figure(res)


def figure(res):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    names = [s[0] for s in SET if s[0] in res]
    cmap = plt.get_cmap('tab20')
    for k, n in enumerate(names):
        r = res[n]
        if not r['sweep']:
            continue
        D = [x['diameter'] for x in r['sweep']]; W = [x['width_mean'] for x in r['sweep']]
        ls = '-' if r['lattice'] == 'cubic' else '--'
        axs[0].plot(D, W, ls, marker='o', ms=4, color=cmap(k), label=n)
    axs[0].set_xscale('log'); axs[0].set_xlabel('diameter of the replicated graph (log scale)')
    axs[0].set_ylabel('Δα'); axs[0].set_title('Δα keeps growing with supercell size')
    axs[0].legend(fontsize=7.5, ncol=2, frameon=False)
    fit = [(n, res[n]['fit']['slope'], res[n]['lattice']) for n in names if res[n]['fit']]
    fit.sort(key=lambda t: t[1])
    axs[1].barh([f[0] for f in fit], [f[1] for f in fit], color=['#1d4ed8' if f[2] == 'cubic' else '#b45309' for f in fit])
    axs[1].set_xlabel('slope of Δα against ln(diameter)'); axs[1].set_title('Slope per framework (blue: cubic)')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'diverse_set_figure.png'), dpi=160); plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1:] or None)
