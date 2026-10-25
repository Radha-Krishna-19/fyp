
import os
os.makedirs('mofmorph', exist_ok=True)
open('mofmorph/__init__.py','w').close()







CIF = 'MOF5.cif'       # change this to your file name (.cif or extxyz with a cell)
NAME = 'MOF-5'
N_FAMILIES = 24        # how many face families to use (more = safer shape, slower)
if not os.path.exists(CIF):
    try:
        from google.colab import files
        up = files.upload(); CIF = list(up)[0]
    except ImportError:
        raise SystemExit('Put the file next to this notebook and set CIF above.')
import sys, warnings, numpy as np
warnings.filterwarnings('ignore'); sys.path.insert(0, '.')
from ase.io import read
from mofmorph.hybrid import uff_gammas, hybrid_shape
from mofmorph.models import describe, bfdh

_a = read(CIF)
if abs(np.linalg.det(_a.cell[:])) < 1e-6:
    raise SystemExit('STOP: this file has no unit cell (no lattice). Crystal faces need a periodic structure; use a CIF.')
F, fams, names, gamma_uff, crystal = uff_gammas(CIF, NAME, n_families=N_FAMILIES)
print(NAME, crystal.spacegroup, f'(#{crystal.sg_number})', len(crystal.numbers), 'atoms in the standard cell')
for n in crystal.notes: print('note:', n)
gamma_external = {}      # e.g. {'{100}': 0.12, '{111}': 0.20}
gamma = gamma_external if gamma_external else gamma_uff
print('Using', 'EXTERNAL' if gamma_external else 'UFF', 'energies for', len(gamma), 'face families')
import matplotlib.pyplot as plt
from mofmorph import render
ws = [0, 0.25, 0.5, 0.75, 1]
shapes, titles, table = [], [], []
for w in ws:
    try:
        s = hybrid_shape(F, fams, names, gamma, w)
    except Exception as e:
        raise SystemExit(f'Could not close the shape at w={w} (not enough face families). Increase N_FAMILIES and rerun. ({str(e)[:80]})')
    shapes.append(s); nm = describe(s, 0.01); titles.append(f"w={w}\n{nm}")
    table.append((w, nm, round(float(s.summary()["sphericity"]), 3)))
fig = plt.figure(figsize=(3*len(ws), 3.4))
for n, (s, t) in enumerate(zip(shapes, titles)):
    render.draw(fig.add_subplot(1, len(ws), n+1, projection="3d"), s, t)
plt.suptitle(f"{NAME}: w=0 is BFDH, w=1 is Wulff, in between is the hybrid"); plt.show()
for r in table: print(r)
print("BFDH with all faces (40 families):", describe(bfdh(F, 40)[0], 0.01))