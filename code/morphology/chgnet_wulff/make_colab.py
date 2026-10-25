"""Build MOF_Wulff_Colab.ipynb from the three modules, so the notebook never drifts from them.

    python make_colab.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


cells = [md("""
# MOF crystal shape from CHGNet surface energies, checked against lab results

1. Upload **`mofs.csv`** (columns `mof, cif`, optional `faces, symprec`) and the CIF files it names.
2. Upload a **lab CSV**: either the project dataset `experimental_morphology.csv` (the
   additive-free rows give the benchmark shape for each MOF) or a simple table `mof, shape`.
3. Choose settings, run, and download `wulff_summary.csv`, `surface_energies.csv`, `slabs.csv`.

Nothing about any MOF is written into the code: every MOF, CIF, face list and lab shape comes
from the uploaded files. You can also upload one `.zip` holding the CSVs and CIFs.

**Method.** Slabs are built from whole metal clusters and whole linkers (only metal-linker
bonds are cut, every slab is stoichiometric). CHGNet relaxes the atoms at fixed cell;
gamma = (E_slab - N e_bulk) / 2A. The lowest gamma per face family gives the Wulff shape.
Optional water capping heals each broken metal-ligand bond with one H2O.

**Test small first.** Tick `QUICK_TEST` (no relaxation, seconds per MOF) and/or fill `ONLY`
with one MOF name. Results are cached, so a full run afterwards reuses everything.
"""),
    code("""
# 1. Install (about 1-2 minutes). Colab already has torch.
!pip -q install chgnet pymatgen networkx
import chgnet, pymatgen, torch
print("chgnet", chgnet.__version__, "| torch", torch.__version__, "| GPU:", torch.cuda.is_available())
"""),
    code("""
# 2. Optional: keep the cache and results on Google Drive so a disconnect loses nothing.
SAVE_TO_DRIVE = False  #@param {type:"boolean"}
import os
OUT_DIR = "/content/results"
if SAVE_TO_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT_DIR = "/content/drive/MyDrive/mof_wulff_results"
os.makedirs(OUT_DIR, exist_ok=True)
print("results will be written to", OUT_DIR)
"""),
]
for name in ("blockslab.py", "capping.py", "chgnet_wulff.py", "plot_results.py"):
    cells.append(code(f"%%writefile {name}\n" + (HERE / name).read_text(encoding="utf-8")))

cells += [
    code("""
# 3. Upload mofs.csv, the lab CSV and the CIF files (or one zip containing them).
import zipfile, glob, pandas as pd
from google.colab import files
os.makedirs("/content/inputs", exist_ok=True)
os.chdir("/content/inputs")
up = files.upload()
for name in up:
    if name.lower().endswith(".zip"):
        zipfile.ZipFile(name).extractall("/content/inputs")
csvs = glob.glob("/content/inputs/**/*.csv", recursive=True)
MOFS_CSV = LAB_CSV = None
for c in csvs:
    cols = {x.strip().lower() for x in pd.read_csv(c, nrows=1).columns}
    if {"mof", "cif"} <= cols:
        MOFS_CSV = c
    elif "morphology" in cols or "shape" in cols:
        LAB_CSV = c
print("MOF list :", MOFS_CSV)
print("lab table:", LAB_CSV)
os.chdir("/content")
if MOFS_CSV:
    t = pd.read_csv(MOFS_CSV)
    base = os.path.dirname(MOFS_CSV)
    t["cif_found"] = [os.path.exists(c if os.path.isabs(c) else os.path.join(base, c)) for c in t["cif"]]
    display(t)
    if not t["cif_found"].all():
        print("Some CIFs are missing: upload them (same names as in the 'cif' column) and rerun this cell.")
"""),
    code("""
# 4. Settings
QUICK_TEST  = True   #@param {type:"boolean"}
ONLY        = ""     #@param {type:"string"}
RELAX_STEPS = 600    #@param {type:"integer"}
FMAX        = 0.05   #@param {type:"number"}
MAX_TERMS   = 3      #@param {type:"integer"}
THICKNESS   = 15.0   #@param {type:"number"}
DEFAULT_FACES = "100 110 111"  #@param {type:"string"}
CAP         = "none" #@param ["none", "water"]
SAVE_SLABS  = False  #@param {type:"boolean"}
"""),
    code("""
# 5. Run. Rerunning skips every slab already in the cache.
import importlib, sys
sys.path.insert(0, "/content")
import chgnet_wulff; importlib.reload(chgnet_wulff)
argv = ["--mofs", MOFS_CSV, "--out", OUT_DIR, "--relax-steps", str(RELAX_STEPS), "--fmax", str(FMAX),
        "--max-terms", str(MAX_TERMS), "--thickness", str(THICKNESS), "--faces", DEFAULT_FACES, "--cap", CAP]
if LAB_CSV: argv += ["--lab", LAB_CSV]
if QUICK_TEST: argv += ["--static"]
if ONLY.strip(): argv += ["--only"] + [x.strip() for x in ONLY.split(",") if x.strip()]
if SAVE_SLABS: argv += ["--save-slabs"]
summary = chgnet_wulff.main(argv)
"""),
    code("""
# 6. Results
import pandas as pd
display(pd.read_csv(f"{OUT_DIR}/wulff_summary.csv"))
display(pd.read_csv(f"{OUT_DIR}/surface_energies.csv")[["mof", "face", "termination", "gamma_J_m2",
        "basis", "converged", "n_atoms", "seconds"]])
"""),
    code("""
# 7. Picture: predicted Wulff shape | lab shape | surface energy per face, one row per MOF
import plot_results; importlib.reload(plot_results)
from IPython.display import Image, display
display(Image(str(plot_results.main(OUT_DIR))))
"""),
    code("""
# 8. Download everything as one zip (includes shapes.png)
import shutil
from google.colab import files
shutil.make_archive("/content/mof_wulff_results", "zip", OUT_DIR)
files.download("/content/mof_wulff_results.zip")
"""),
]

nb = {"cells": cells, "metadata": {"colab": {"provenance": []},
                                    "kernelspec": {"name": "python3", "display_name": "Python 3"},
                                    "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(HERE / "MOF_Wulff_Colab.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote MOF_Wulff_Colab.ipynb with", len(cells), "cells")
