"""Shape class on a grid of x = g110/g100, y = g111/g100 (cubic Wulff, exact). Writes phase_grid.npz."""
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(HERE, '..', '..', '..'))
LAB_CSV = _os.path.join(REPO_ROOT, 'data', 'experimental_morphology', 'dataset', 'experimental_morphology.csv')
import numpy as np, time
from cubic_wulff import shape
CLASSES = ["cube", "truncated_cube", "cuboctahedron", "truncated_octahedron", "octahedron",
           "cube_truncated_edges", "truncated_rhombic_dodecahedron", "rhombic_dodecahedron",
           "rd_truncated_by_111", "octahedron_truncated_by_110", "all_three_families"]
xs = np.geomspace(0.4, 3.2, 150); ys = np.geomspace(0.4, 2.2, 150)
lab = np.zeros((len(ys), len(xs)), int); f = np.zeros((len(ys), len(xs), 3))
t = time.time()
for i, y in enumerate(ys):
    for j, x in enumerate(xs):
        c, fr = shape(1.0, x, y)
        lab[i, j] = CLASSES.index(c); f[i, j] = [fr["100"], fr["110"], fr["111"]]
np.savez(_os.path.join(HERE, "phase_grid.npz"), xs=xs, ys=ys, lab=lab, f=f, classes=np.array(CLASSES))
print("grid done", round(time.time() - t, 1), "s;", {CLASSES[k]: int((lab == k).sum()) for k in np.unique(lab)})
