"""Figure: what one slice of a real MOF net looks like for F, S and K faces.
Run after run_phase3.py:  python3 2_python/morphology/figs_phase3.py"""
import sys, os, json, warnings
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
warnings.filterwarnings("ignore")
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from run_phase3 import periodic_graph, conventional_axes, CIF, OUT, REPS
from mofmorph.graphfaces import contract_two_connected, face_quantities

R = json.load(open(os.path.join(OUT, "phase3_results.json")))
panels = [("MOF-5", "MOF5.cif", "{100}"), ("MOF-5", "MOF5.cif", "{110}"), ("MOF-5", "MOF5.cif", "{211}"),
          ("ZIF-8", "ZIF-8.cif", "{110}"), ("ZIF-8", "ZIF-8.cif", "{211}+"), ("ZIF-8", "ZIF-8.cif", "{111}+")]
fig, axs = plt.subplots(2, 3, figsize=(12, 8.2))
cache = {}
for ax, (name, fn, lab) in zip(axs.ravel(), panels):
    if fn not in cache:
        G0, geom = periodic_graph(os.path.join(CIF, fn)); cache[fn] = (contract_two_connected(G0), conventional_axes(geom)[0])
    G, Lc = cache[fn]
    Bc = np.linalg.inv(Lc).T
    n = np.array(REPS[lab], float) @ Bc; n /= np.linalg.norm(n)
    rec = R[name]["faces"][lab]; d = rec["d_eff"]
    h0 = face_quantities(G, n, d)["h0"]
    u = np.cross(n, [0.137, 0.71, 0.29]); u /= np.linalg.norm(u); w = np.cross(n, u)
    pts = {}
    reach = 3
    for a in range(-reach, reach + 1):
        for b in range(-reach, reach + 1):
            for c in range(-reach, reach + 1):
                off = np.array([a, b, c]) @ G.L
                for i, x in enumerate(G.X):
                    y = x + off; hh = y @ n
                    if h0 < hh <= h0 + d + 1e-9 and abs(y @ u) < 60 and abs(y @ w) < 60:
                        pts[(i, a, b, c)] = y
    for (i, a, b, c), y in pts.items():
        for p, q, t in G.edges:
            for s, o, tt in ((p, q, t), (q, p, tuple(-x for x in t))):
                if s != i: continue
                key = (o, a + tt[0], b + tt[1], c + tt[2])
                if key in pts:
                    z = pts[key]; ax.plot([y @ u, z @ u], [y @ w, z @ w], color="#E45756", lw=1.6, zorder=1)
    P = np.array(list(pts.values()))
    if len(P):
        ax.scatter(P @ u, P @ w, s=22, color="#4C78A8", zorder=2)
    ax.set_aspect("equal"); ax.set_xlim(-45, 45); ax.set_ylim(-45, 45); ax.set_xticks([]); ax.set_yticks([])
    word = {"F": "flat: links form a 2D sheet", "S": "stepped: links form 1D chains", "K": "kinked: no connected chains"}[rec["cls"]]
    ax.set_title(f"{name} {lab}  ->  {rec['cls']} face\n{word}\nlinks per new unit E_att = {rec['E_att']:.2f}", fontsize=9.5)
fig.text(0.5, 0.01, "One slice of thickness d_eff seen face-on. Blue: nodes of the net inside the slice. Red: links that stay inside the slice. "
         "A face whose slice is one connected sheet grows slowly, layer by layer.", ha="center", fontsize=9)
plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(os.path.join(OUT, "figs", "phase3_slices.png"), dpi=170); print("ok")
