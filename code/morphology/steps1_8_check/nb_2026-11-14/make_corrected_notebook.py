"""Build MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb from the team notebook of 14 November.

Run:  python make_corrected_notebook.py
Changes made to the team notebook (everything else is kept as written):
  * cells 3 and 16 write the corrected modules mofwulff.py and mofgnn.py of this folder;
  * the water condition WATER_DMU_EV is a setting, used for the shapes and the GNN labels;
  * the UiO-66 reference shape is corrected (a cube without additives);
  * runs on Google Colab or on any computer with Jupyter: files go to the working folder, not /content;
  * results are zipped and saved to the Downloads folder after each stage (Colab: the browser downloads
    the zip, which lands in the Downloads folder of the computer running the browser; local Jupyter: the
    zip is copied to ~/Downloads). Google Drive is optional and off by default;
  * the two "predict a new MOF" cells, which wait for a file upload, are skipped unless PREDICT_NEW_MOF is on,
    so "Run all" runs to the end without stopping;
  * outputs are cleared.
"""
import copy, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "MOF_Wulff_steps1_8_plus_GNN.ipynb")
OUT = os.path.join(HERE, "MOF_Wulff_steps1_8_plus_GNN_corrected.ipynb")

nb = copy.deepcopy(json.load(open(SRC, encoding="utf-8")))
C = nb["cells"]


def src(i):
    return "".join(C[i]["source"])


def put(i, text):
    C[i]["source"] = text.splitlines(keepends=True)


def sub(i, old, new, count=1):
    s = src(i)
    assert s.count(old) >= 1, (i, old[:60])
    put(i, s.replace(old, new) if count == 0 else s.replace(old, new, count))


# modules
assert src(3).startswith("%%writefile /content/mofwulff.py") and src(16).startswith("%%writefile /content/mofgnn.py")
put(3, "%%writefile mofwulff.py\n" + open(os.path.join(HERE, "mofwulff.py"), encoding="utf-8").read())
put(16, "%%writefile mofgnn.py\n" + open(os.path.join(HERE, "mofgnn.py"), encoding="utf-8").read())

# 1. install: also define BASE (the working folder) and the deliver() helper
sub(1, 'import importlib.util, subprocess, sys, os\n', '''import importlib.util, subprocess, sys, os, shutil, time
BASE = os.getcwd()          # /content on Colab; the notebook's folder in local Jupyter
IN_COLAB = importlib.util.find_spec("google.colab") is not None

def deliver(tag):
    """Zip everything in OUT_DIR and put the zip in the Downloads folder of this computer.
    Colab: the browser downloads it (allow multiple downloads if the browser asks). Local: copied to ~/Downloads."""
    name = f"mof_wulff_results_{tag}_{time.strftime('%Y%m%d_%H%M')}"
    z = shutil.make_archive(os.path.join(BASE, name), "zip", OUT_DIR)
    if IN_COLAB:
        try:
            from google.colab import files; files.download(z); print("downloading", os.path.basename(z), "to your Downloads folder")
        except Exception as e:
            print("could not start the download:", e, "| the zip is at", z)
    else:
        dl = os.path.join(os.path.expanduser("~"), "Downloads"); os.makedirs(dl, exist_ok=True)
        shutil.copy(z, dl); print("saved", os.path.join(dl, os.path.basename(z)))
''')

# 2. output folder
put(2, '''# 2. Output folder. Results are also zipped into your Downloads folder after each stage (deliver()).
SAVE_TO_DRIVE = False  #@param {type:"boolean"}
OUT_DIR = os.path.join(BASE, "results")
if SAVE_TO_DRIVE and IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive"); OUT_DIR = "/content/drive/MyDrive/mof_wulff_results"
os.makedirs(OUT_DIR, exist_ok=True); print("results ->", OUT_DIR)
''')

# 3. MOF list: UiO-66 reference; paths
sub(5, 'dict(mof="UiO-66",    source=RASPA + "UIO-66.cif",   faces="", reference_habit="octahedron {111}")',
    'dict(mof="UiO-66",    source=RASPA + "UIO-66.cif",   faces="", reference_habit="cube {100} without additives; octahedron {111} only with benzoic or acetic acid")')
sub(5, 'CIF_DIR = "/content/cifs"', 'CIF_DIR = os.path.join(BASE, "cifs")')
sub(5, 'fetch(CORE_URL, "/content/CoREMOF2019.zip")', 'fetch(CORE_URL, os.path.join(BASE, "CoREMOF2019.zip"))')

# 4. settings: water condition
sub(6, "SYMPREC      = 0.1", '''WATER_DMU_EV = -0.5695  #@param {type:"number"}
# Water condition for the shapes and the GNN labels: chemical potential of water relative to a free molecule
# at 0 K, in eV. -0.5695 = liquid water at 25 C (default); -0.4809 = vapour, 25 C, 1 bar; 0 = the old
# reference, which gave negative surface energies.
SYMPREC      = 0.1''')

# 5. steps 1-6 and 8
sub(7, 'sys.path.insert(0, "/content")', "sys.path.insert(0, BASE)")
sub(7, "relax_steps=0 if QUICK_TEST else RELAX_STEPS, fmax=FMAX, relax_top_k=RELAX_TOP_K)",
    "relax_steps=0 if QUICK_TEST else RELAX_STEPS, fmax=FMAX, relax_top_k=RELAX_TOP_K,\n           water_dmu_eV=WATER_DMU_EV)")
put(7, src(7).rstrip("\n") + '\ndeliver("steps1-8")\n')

# 8. download everything
put(13, '''# 8. Download everything so far (CSVs, Wulff PNG/OBJ, relaxed slab CIFs, DFT inputs) to your Downloads folder
deliver("after_validation")
''')

# 9. training data
sub(18, 'sys.path.insert(0, "/content")', "sys.path.insert(0, BASE)")
sub(18, 'vacuum=VACUUM, max_terms=MAX_TERMS, cap="water", fmax=FMAX)', 'vacuum=VACUUM, max_terms=MAX_TERMS, cap="water", fmax=FMAX, water_dmu_eV=WATER_DMU_EV)')
put(18, src(18).rstrip("\n") + '\ndeliver("training_data")\n')

# 11. cross-validation at the stated water condition
sub(20, 'INDEX_USE = INDEX[~INDEX["mof"].isin(excl)].reset_index(drop=True)',
    'INDEX_USE = G.at_water_mu(INDEX[~INDEX["mof"].isin(excl)].reset_index(drop=True), WATER_DMU_EV)   # labels at the stated water condition')

# 12. final model, then deliver everything
put(21, src(21).rstrip("\n") + '\ndeliver("final")\n')

# 13. predict a new MOF (twice in the original): skipped unless asked, so Run all does not stop for an upload
for i in (22, 24):
    s = src(i)
    assert s.startswith("# 13. Predict the shape of a new MOF")
    body = s.replace('sys.path.insert(0, "/content")', "sys.path.insert(0, BASE)").replace('cif = "/content/" + fname', "cif = os.path.join(BASE, fname)") \
            .replace('f"/content/wulff_{name}_{label}.png"', 'os.path.join(OUT_DIR, f"wulff_{name}_{label}.png")') \
            .replace("from google.colab import files\n", "")
    body = body.replace("up = files.upload(); fname = list(up)[0];", "fname = NEW_CIF if NEW_CIF else __import__('google.colab').colab.files.upload() and None;")
    lines = body.splitlines()
    head, rest = lines[:2], lines[2:]
    new = head + ['PREDICT_NEW_MOF = False  #@param {type:"boolean"}',
                  'NEW_CIF = ""  #@param {type:"string"}',
                  '# Set PREDICT_NEW_MOF and put the CIF file name in NEW_CIF (in the working folder); on Colab, leave NEW_CIF empty to upload.',
                  'if PREDICT_NEW_MOF:'] + ["    " + l for l in rest]
    put(i, "\n".join(new) + "\n")
# the upload path: replace the one-line trick above with readable code
for i in (22, 24):
    s = src(i).replace("    fname = NEW_CIF if NEW_CIF else __import__('google.colab').colab.files.upload() and None; cif = os.path.join(BASE, fname);",
                       "    if NEW_CIF:\n        fname = NEW_CIF\n    else:\n        from google.colab import files\n        fname = list(files.upload())[0]\n    cif = os.path.join(BASE, fname);")
    put(i, s)

for c in C:
    if c["cell_type"] == "code":
        c["outputs"] = []; c["execution_count"] = None
C.insert(0, {"cell_type": "markdown", "metadata": {}, "source": """# Corrected notebook (15 November 2026): how to run it

**On Google Colab (recommended, needs a GPU):** File > Upload notebook, then Runtime > Change runtime type > T4 GPU, then Runtime > Run all. If the first cell restarts the runtime, press Run all once more. After each stage the results are zipped and downloaded by your browser into the **Downloads** folder of your computer (`mof_wulff_results_<stage>_<date>.zip`); if the browser asks whether to allow several downloads, allow them. Keep the tab open: the full run (16 MOFs relaxed, 41 static, the GNN) takes several hours on a T4.

**On any computer with Jupyter and Python 3.10+ (slow without a GPU):** open the notebook and run all; the zips are copied to `~/Downloads`.

Send the zip called `..._final_...` back; it holds every result. The earlier zips are checkpoints in case the session stops.

**What changed from the team version of 14 November** (details: `code/morphology/steps1_8_check/nb_2026-11-14/README.md` and the website page *ML energies and water*):

- **Water condition.** Surface energies are reported at the water chemical potential `WATER_DMU_EV` (cell 4; default liquid water at 25 °C). The old reference, a free water molecule at 0 K, gave six negative surface energies. The stored `gamma_*_J_m2` columns keep the old reference so old and new runs can be compared; the shapes and the GNN labels use `WATER_DMU_EV`.
- **Relaxed cell used consistently.** Slabs and bulk come from the same relaxed cell, and faces are converted to the right planes after the cell is reloaded (two fixes from 10 November that were missing).
- **Water caps.** A linker oxygen gets at most one hydrogen; a surplus hydrogen turns the nearest metal–OH cap into a water molecule on the metal (before, a bridging oxygen could get two).
- **Metal rods.** Metals that share a linker oxygen form one inorganic unit, so the Mg–O rod of Mg-MOF-74 is kept whole.
- **Shape names** come from the exact limits of the cubic shape map.
- **UiO-66 reference shape** is a cube without additives (octahedra need an acid modulator).
- **GNN.** Labels at `WATER_DMU_EV`; labels ≤ 0 are dropped and listed.
- Runs on Colab or locally; results go to Downloads; Google Drive is optional.
""".splitlines(keepends=True)})
json.dump(nb, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote", OUT, len(C), "cells")
