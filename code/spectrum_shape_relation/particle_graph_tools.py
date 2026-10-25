"""
particle_graph_tools.py
=======================

Shared tools for the "spectrum <-> crystal shape" study.

WHAT THIS FOLDER IS FOR
-----------------------
The project has two halves.

  * First half (before Panel Review 1): describe each MOF by a number computed from its
    connectivity alone, the multifractal spectrum width (Delta-alpha), and try to sort MOFs
    into classes with it. Code: code/spectrum_pipeline/code_09 ... code_18.
  * Second half (after the panel): from the same unit cell, predict the crystal SHAPE
    (morphology) with BFDH, Wulff, a BFDH x Wulff blend and CHGNet energies.
    Code: code/morphology/.

Both halves start from the same object: the labelled quotient graph of the MOF's building
blocks (metal clusters = "nodes", organic linkers = "linkers"; each edge carries the integer
lattice translation it crosses). This module joins the two halves.

THE KEY IDEA
------------
Every spectrum in the first half was measured on a TORUS: the quotient graph tiled n x n x n
WITH wrap-around, so it has no surface and therefore no shape. A real crystal is a finite
particle with faces. Here we build FINITE particles:

    1. tile the quotient graph over many unit cells WITHOUT wrap-around,
    2. place every building block at its real Cartesian position (block centroid + cell offset),
    3. keep only the blocks that lie inside a chosen shape (a box, or a crystal polyhedron
       predicted by BFDH / Wulff / CHGNet),
    4. measure the multifractal spectrum width Delta-alpha of that finite graph.

Then we can ask: does Delta-alpha change with the particle's shape when the number of blocks
is held (nearly) fixed?

SPECTRUM SETTINGS (identical to the full CoRE / hMOF bands, code_17)
--------------------------------------------------------------------
    influential vertices : top 20 % by degree           (TOP_FRACTION)
    fitted radii         : 1 ... half the diameter      (WINDOW_FRACTION)
    trials per seed      : 20                          (N_TRIALS)
    seeds                : 0, 1, 2, 3, 4                (SEEDS)
The reported error bar is the spread over seeds. It measures the randomness of the box
covering only, NOT the uncertainty of the method itself.

All heavy lifting (box covering, tau(q), alpha, f(alpha)) is done by the project's own
code_12_converged_band.py, so nothing about the spectrum is re-implemented here.
"""
import itertools
import os
import sys

import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------------------------
# Paths: this file lives in  <repo>/code/spectrum_shape_relation/
# ---------------------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))            # repository root
PYDIR = os.path.join(REPO, 'code', 'spectrum_pipeline')           # <repo>/code/spectrum_pipeline
MORPHDIR = os.path.join(REPO, 'code', 'morphology')                       # <repo>/code/morphology
RESULTS = os.path.join(HERE, 'results')
FIGURES = os.path.join(HERE, 'figures')
DATA = os.path.join(HERE, 'data')
for p in (PYDIR, MORPHDIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import code_12_converged_band as c12                     # spectrum machinery (first half)
from code_05_centroid_simplification import _unwrap_block  # same unwrapping the quotient graph used

# ---------------------------------------------------------------------------------------------
# Spectrum settings (see module docstring)
# ---------------------------------------------------------------------------------------------
TOP_FRACTION = 0.20
WINDOW_FRACTION = 0.50
N_TRIALS = 20
SEEDS = (0, 1, 2, 3, 4)


# =============================================================================================
# 1. The quotient graph of one unit cell, with a real position for every building block
# =============================================================================================
def load_quotient_graph_with_positions(cif_path):
    """Read a CIF and return everything needed to build finite particles.

    Returns a dict with
        blocks      list of (kind, atom_indices)          kind is 'node' or 'linker'
        edges       list of (i, j, t)                      t = integer lattice translation
        cell        3x3 array, rows = lattice vectors a, b, c in Angstrom
        centroid    (K, 3) array: Cartesian centroid of each block in its OWN unwrapped frame

    WHY THE UNWRAPPED FRAME: a block can straddle the cell boundary (half its atoms near
    fractional 0.98, half near 0.02). code_09 unwraps every block into one contiguous piece
    and measures the translation t of every edge relative to those unwrapped frames. Using the
    SAME unwrapping here means "block i in cell c sits at centroid[i] + c . cell" is exactly
    consistent with the edge labels t, so a particle cut in space is also cut correctly in
    the graph.
    """
    blocks, edges, geom = c12.quotient_graph_from_cif(cif_path)
    cell = np.array(geom.cell_matrix, dtype=float)
    centroid = []
    for _kind, atom_ids in blocks:
        unwrapped = _unwrap_block(geom, atom_ids)         # {atom index: (x, y, z)}
        centroid.append(np.mean([unwrapped[a] for a in atom_ids], axis=0))
    return dict(blocks=blocks, edges=edges, cell=cell, centroid=np.array(centroid))


# =============================================================================================
# 2. Finite particles
# =============================================================================================
def box_particle(q, na, nb, nc):
    """Tile the quotient graph in a box of na x nb x nc unit cells WITHOUT wrap-around.

    Every block of every cell is kept; an edge is kept only if both ends lie inside the box.
    This is the construction of code_19_spectrum_vs_shape.py (cube / slab / plate / rod).
    """
    K = len(q['blocks'])
    cells = [(a, b, c) for a in range(na) for b in range(nb) for c in range(nc)]
    index_of_cell = {cell: i for i, cell in enumerate(cells)}
    G = nx.Graph()
    G.add_nodes_from(range(K * len(cells)))
    for cell in cells:
        for (i, j, t) in q['edges']:
            target = (cell[0] + t[0], cell[1] + t[1], cell[2] + t[2])
            if target in index_of_cell:                       # no wrap-around: outside = dropped
                G.add_edge(i * len(cells) + index_of_cell[cell], j * len(cells) + index_of_cell[target])
    return G


def all_block_positions(q, half_width):
    """Positions of every block in cells -half_width ... +half_width along each axis.

    Returns (keys, xyz) where keys[n] = (block index i, cell tuple) and xyz[n] its position,
    with the origin moved to the centre of the cloud so that polyhedra can be centred at 0.
    """
    rng = range(-half_width, half_width + 1)
    keys, xyz = [], []
    for cell in itertools.product(rng, rng, rng):
        offset = np.array(cell, float) @ q['cell']            # cell vector sum  c_a a + c_b b + c_c c
        for i in range(len(q['blocks'])):
            keys.append((i, cell))
            xyz.append(q['centroid'][i] + offset)
    xyz = np.array(xyz)
    # Put the origin at the mean position of the blocks of cell (0, 0, 0). The cloud spans the
    # same number of cells on each side, so a polyhedron centred at 0 sits in its middle.
    return keys, xyz - q['centroid'].mean(axis=0)


def graph_of_selected_blocks(q, keys, selected):
    """Graph on the selected blocks; an edge exists if the quotient graph joins the two blocks
    across their cell difference. Only the largest connected piece is returned (blocks cut off
    at the surface, e.g. a linker whose node lies outside, are surface debris, not particle)."""
    chosen = {keys[n] for n in np.flatnonzero(selected)}
    vid = {k: v for v, k in enumerate(sorted(chosen))}
    G = nx.Graph()
    G.add_nodes_from(range(len(vid)))
    for (i, cell) in chosen:
        for (a, b, t) in q['edges']:
            if a != i:
                continue
            other = (b, (cell[0] + t[0], cell[1] + t[1], cell[2] + t[2]))
            if other in vid:
                G.add_edge(vid[(i, cell)], vid[other])
        # edges are stored once as (a, b, t); also walk them backwards (b -> a with -t)
        for (a, b, t) in q['edges']:
            if b != i:
                continue
            other = (a, (cell[0] - t[0], cell[1] - t[1], cell[2] - t[2]))
            if other in vid:
                G.add_edge(vid[(i, cell)], vid[other])
    n_pieces = nx.number_connected_components(G)
    biggest = max(nx.connected_components(G), key=len)
    return G.subgraph(biggest).copy(), n_pieces


# =============================================================================================
# 3. Crystal polyhedra (the shapes predicted in the morphology half)
# =============================================================================================
def cubic_family_normals(hkl):
    """All symmetry-equivalent unit normals of a cubic face family {hkl} (signs and permutations).
    Valid for cubic crystals only (MOF-5 here)."""
    out = set()
    for perm in itertools.permutations(hkl):
        for signs in itertools.product((1, -1), repeat=3):
            v = tuple(s * p for s, p in zip(signs, perm))
            if any(v):
                out.add(v)
    return [np.array(v, float) / np.linalg.norm(v) for v in sorted(out)]


def polyhedron_from_family_distances(R_by_family):
    """{'{100}': R, '{111}': R, ...}  ->  (normals, distances) of the convex polyhedron
    P = { x : n_f . x <= R_f for every face f }  (the Wulff / BFDH construction)."""
    normals, dists = [], []
    for fam, R in R_by_family.items():
        hkl = tuple(int(ch) for ch in fam.strip('{}+-'))
        for n in cubic_family_normals(hkl):
            normals.append(n)
            dists.append(R)
    return np.array(normals), np.array(dists)


def inside(xyz, normals, dists, scale):
    """True for every point inside the polyhedron scaled by `scale` (Angstrom per unit R)."""
    return np.all(xyz @ normals.T <= dists * scale + 1e-9, axis=1)


def scale_for_block_count(xyz, normals, dists, target):
    """Find the scale at which the polyhedron contains as close as possible to `target` blocks
    (bisection; the count is a step function of the scale, so it is matched to within a few %)."""
    lo, hi = 0.0, 1.0
    while inside(xyz, normals, dists, hi).sum() < target:
        hi *= 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if inside(xyz, normals, dists, mid).sum() < target:
            lo = mid
        else:
            hi = mid
    return hi


# =============================================================================================
# 4. The spectrum width of a finite particle
# =============================================================================================
def spectrum_width(G):
    """Delta-alpha of graph G: mean and standard deviation over SEEDS, plus the diameter.
    Uses code_12.spectrum with the band settings. Returns None for the width if the graph is
    too small to scale over (diameter < 8, code_12's own gate)."""
    adj = c12._adjacency(G)
    diameter = c12.fast_diameter(G, adj)
    influential, _ = c12.select_influential(G, TOP_FRACTION)
    widths = []
    for seed in SEEDS:
        s = c12.spectrum(G, influential, n_trials=N_TRIALS, seed=seed, diameter=diameter,
                         window_frac=WINDOW_FRACTION)
        if s.get('ok'):
            widths.append(s['width'])
    if not widths:
        return dict(diameter=int(diameter), width_mean=None, width_sd=None, n_ok=0)
    return dict(diameter=int(diameter), width_mean=float(np.mean(widths)),
                width_sd=float(np.std(widths, ddof=1)) if len(widths) > 1 else 0.0, n_ok=len(widths))


def fit_size_trend(diameters, widths):
    """Fit Delta-alpha = a + b ln(D). Returns (a, b). The first half of the project found this
    form on every net (R^2 >= 0.998), which is why size must be controlled before shape."""
    b, a = np.polyfit(np.log(np.asarray(diameters, float)), np.asarray(widths, float), 1)
    return float(a), float(b)
