import json, re, os
HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "..", "mofmorph") + os.sep
def md(s): return {"cell_type":"markdown","metadata":{},"source":s.strip("\n").splitlines(True)}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s.strip("\n").splitlines(True)}
cells=[]
cells.append(md("""
# MorphoGraph-Lattice: BFDH + Wulff + hybrid crystal shapes

**Input:** a MOF CIF file. **Output:** the possible crystal faces, a surface energy for each face, and the outside crystal shape from three rules:

1. **BFDH** (geometry only): wide-spaced planes grow slowly, so they become big faces.
2. **Wulff** (energy): the lower the surface energy of a face, the bigger it is.
3. **Hybrid** (both together): `R = R_BFDH^(1-w) * R_Wulff^w`, with `w` from 0 (pure BFDH) to 1 (pure Wulff).

The face energies here come from a simple force field (UFF, unrelaxed, no electrostatics, no solvent). It is a rough baseline. If you have better energies (for example CHGNet or DFT) paste them into the **external energies** cell and the same hybrid step uses them.

No CHGNet is needed to run this notebook. It works for any crystal system.
"""))
cells.append(code("%pip install -q ase spglib scipy matplotlib numpy"))
cells.append(md("## 1. Library files (written to disk so you can read them)"))
cells.append(code("import os\nos.makedirs('mofmorph', exist_ok=True)\nopen('mofmorph/__init__.py','w').close()"))
for f in ["structure","faces","shape","models","forcefield","hybrid","render"]:
    src=open(M+f+".py", encoding="utf-8").read()
    if f=="render": src=src.replace('matplotlib.use("Agg")','pass  # inline display in notebooks')
    cells.append(code("%%writefile mofmorph/"+f+".py\n"+src))
cells.append(md("## 2. Choose a MOF\nUpload your CIF (Colab) or put the file next to the notebook. **Any crystal system works** (cubic, tetragonal, hexagonal, low symmetry...). The file must contain the unit cell, so use `.cif` (or an `.xyz`/`.extxyz` that includes the lattice). A plain `.xyz` with no cell cannot give crystal faces and is rejected with a message."))
cells.append(code("""
CIF = 'MOF5.cif'       # change this to your file name (.cif or extxyz with a cell)
NAME = 'MOF-5'
N_FAMILIES = 24        # how many face families to use (more = safer shape, slower)
if not os.path.exists(CIF):
    try:
        from google.colab import files
        up = files.upload(); CIF = list(up)[0]
    except ImportError:
        raise SystemExit('Put the file next to this notebook and set CIF above.')
"""))
cells.append(md("## 3. Faces and UFF face energies\nEvery symmetry family of faces gets its own energy, computed on the same cell the Miller indices refer to."))
cells.append(code("""
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
"""))
cells.append(md("## 4. External energies (optional)\nPaste CHGNet / DFT surface energies in J/m2 here, using the same face names as printed above. Leave it empty to use the UFF values."))
cells.append(code("""
gamma_external = {}      # e.g. {'{100}': 0.12, '{111}': 0.20}
gamma = gamma_external if gamma_external else gamma_uff
print('Using', 'EXTERNAL' if gamma_external else 'UFF', 'energies for', len(gamma), 'face families')
"""))
cells.append(md("## 5. BFDH, Wulff and hybrid shapes"))
cells.append(code("""
import matplotlib.pyplot as plt
from mofmorph import render
ws = [0, 0.25, 0.5, 0.75, 1]
shapes, titles, table = [], [], []
for w in ws:
    try:
        s = hybrid_shape(F, fams, names, gamma, w)
    except Exception as e:
        raise SystemExit(f'Could not close the shape at w={w} (not enough face families). Increase N_FAMILIES and rerun. ({str(e)[:80]})')
    shapes.append(s); nm = describe(s, 0.01); titles.append(f"w={w}\\n{nm}")
    table.append((w, nm, round(float(s.summary()["sphericity"]), 3)))
fig = plt.figure(figsize=(3*len(ws), 3.4))
for n, (s, t) in enumerate(zip(shapes, titles)):
    render.draw(fig.add_subplot(1, len(ws), n+1, projection="3d"), s, t)
plt.suptitle(f"{NAME}: w=0 is BFDH, w=1 is Wulff, in between is the hybrid"); plt.show()
for r in table: print(r)
print("BFDH with all faces (40 families):", describe(bfdh(F, 40)[0], 0.01))
"""))
cells.append(md("""
## What the result means, and its limits
- If BFDH and Wulff give the **same** shape, the hybrid adds nothing. If they **differ**, the hybrid is in between, and only **experimental crystal shapes** (solvent, temperature, modulator) can say which is right.
- The UFF energies are unrelaxed, with no electrostatics, no solvent and no temperature. Treat them as a baseline to beat.
- Shapes are for the crystal as grown (outside shape), not the unit cell.
- Face names: in non-cubic cells the same plain label can belong to different families, so a direction like `[0,0,1]` is added to the name.
- Tested on MOF-5, HKUST-1, UiO-66, ZIF-8 (cubic) and hMOF-0 (R3m). Very large cells (many hundreds of atoms) can be slow.
"""))
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}
json.dump(nb,open(os.path.join(HERE, "..", "MorphoGraph_hybrid.ipynb"),"w",encoding="utf-8"),indent=1)
# test script: run all code cells outside jupyter
open(os.path.join(HERE, "nb_test.py"),"w",encoding="utf-8").write("\n".join(("".join(c['source']) if not "".join(c['source']).startswith('%') else "") for c in cells if c['cell_type']=='code'))
