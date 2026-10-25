"""
make_notebook_spectrum_shape_relation.py
========================================

Writes Spectrum_Shape_Relation.ipynb, the notebook that walks through the whole
spectrum <-> crystal-shape study step by step, with a plain-words and a technical explanation
before every step. The notebook calls the same scripts as the command line, so the notebook and
the scripts cannot disagree.

    python make_notebook_spectrum_shape_relation.py                 # write the notebook
    python make_notebook_spectrum_shape_relation.py --execute       # write and run it (saves outputs)

In the notebook, RECOMPUTE = False reads the saved results (seconds). RECOMPUTE = True runs
every calculation again (about 20 minutes on a laptop).
"""
import os
import sys

import nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(HERE, 'Spectrum_Shape_Relation.ipynb')

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
md("""# Spectrum and crystal shape: joining the two halves of the project

**Project:** 23CSE498 Final Year Project, Amrita Vishwa Vidyapeetham, Coimbatore.
**Folder:** `code/spectrum_shape_relation/`

## What this notebook does

**In simple words.** Before the panel review we described each MOF by one number computed from
how its building blocks are connected (the *spectrum width*, written Δα) and tried to sort MOFs
into groups with it. After the panel review we predicted the *outside shape* of MOF crystals
(cube, octahedron, plate, rod...). This notebook asks whether the two are related: does the
spectrum number change when the crystal shape changes, and can the number tell us anything about
the shape a MOF will take?

**In technical words.** Both halves start from the labelled quotient graph of the MOF's
building blocks. Every earlier spectrum was measured on a torus (the graph tiled with
wrap-around), which has no surface and no shape. Here the graph is tiled *without* wrap-around
and cut to a finite particle of a chosen shape. We then measure Δα (top 20 % of blocks by degree
as influential, radii to half the diameter, 20 trials, 5 seeds; the settings of the full CoRE and
hMOF bands) and compare shapes at matched size.

| Step | Script | Question |
|---|---|---|
| 1 | `run_01_spectrum_of_box_particles_same_cell_count.py` | Same MOF-5, same 64 cells, cube / slab / plate / rod: does Δα change? |
| 2 | `run_02_spectrum_of_predicted_crystal_shapes_MOF5.py` | Does Δα separate the shapes that BFDH, the blend, UFF Wulff and CHGNet predict for MOF-5? |
| 3 | `run_03_core_mof_spectrum_width_vs_bfdh_shape.py` | Across 55 real CoRE MOFs, is the periodic-graph Δα related to the predicted shape once size is held fixed? |
| 4 | `make_figures_spectrum_shape_relation.py` | Figures |
| 5 | `check_spectrum_shape_relation.py` | Checks |

**Requirements:** numpy, scipy, networkx, matplotlib, ase, spglib (all used elsewhere in the
project). Run from inside this folder, or in Colab after uploading the repository (see README.md).
"""),
code("""# ---- 0. install the libraries this study needs (safe to re-run; skips what is already there) ----
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'numpy', 'scipy', 'networkx', 'matplotlib', 'ase', 'spglib'])
print('libraries ready')"""),
code("""# ---- 1. find the project folder ----------------------------------------------------------------
# ON YOUR PC (Jupyter / VS Code): open this notebook from
#     code/spectrum_shape_relation/ of the repository and run all. Nothing else to do.
# IN GOOGLE COLAB: upload the zip  spectrum_shape_relation_bundle.zip  (written to build/ by make_colab_bundle_spectrum_shape_relation.py)
#     when the upload box appears. It is unpacked and used automatically.
import os, sys, json, zipfile
IN_COLAB = 'google.colab' in sys.modules
if IN_COLAB:
    from google.colab import files
    up = files.upload()                                   # choose spectrum_shape_relation_bundle.zip
    zipfile.ZipFile(next(iter(up))).extractall('/content/bundle')
    os.chdir('/content/bundle/code/spectrum_shape_relation')
HERE = os.path.abspath('.')
assert os.path.exists(os.path.join(HERE, 'particle_graph_tools.py')), \\
    'Open this notebook from code/spectrum_shape_relation/ (or upload the bundle in Colab)'
sys.path.insert(0, HERE)
import particle_graph_tools as T      # also adds code/spectrum_pipeline/ and code/morphology/ to the path

# True: run every calculation (about 20 minutes on a laptop).  False: only read saved results.
RECOMPUTE = True

def load(name):
    return json.load(open(os.path.join(T.RESULTS, name)))

# Everything printed with say() is ALSO written to results/RUN_REPORT_spectrum_shape_relation.md,
# so the results can be read later from the file, without screenshots.
os.makedirs(T.RESULTS, exist_ok=True)
REPORT = os.path.join(T.RESULTS, 'RUN_REPORT_spectrum_shape_relation.md')
import datetime, platform
open(REPORT, 'w').write(f"# Run report: spectrum <-> crystal shape\\n\\nrun at {datetime.datetime.now():%Y-%m-%d %H:%M} on "
                        f"{platform.platform()}, Python {platform.python_version()}, RECOMPUTE={RECOMPUTE}\\n\\n")
def say(*lines):
    for line in lines:
        print(line)
        open(REPORT, 'a').write(str(line) + '\\n')
say('spectrum settings: ' + str(dict(top=T.TOP_FRACTION, window=T.WINDOW_FRACTION, trials=T.N_TRIALS, seeds=T.SEEDS)))"""),
md("""## Step 1. Same number of cells, four box shapes (MOF-5)

**In simple words.** We build a small MOF-5 crystal out of 64 unit cells, four times: as a cube,
a thick slab, a thin plate and a long rod. Same amount of material each time, only the shape
changes. Then we measure the spectrum number of each.

**In technical words.** `box_particle(q, na, nb, nc)` tiles the quotient graph in a box of
cells without wrap-around (an edge whose far end leaves the box is dropped). A size trend
Δα = a + b ln D is fitted on cubes of side 2–6, where D is the graph diameter, and each shape is
compared with the trend at its own D. The script also re-checks its numbers against the
independent script `code/spectrum_pipeline/code_19_spectrum_vs_shape.py`."""),
code("""import run_01_spectrum_of_box_particles_same_cell_count as S1
if RECOMPUTE:
    S1.run('MOF5'); S1.run('ZIF8')
r1 = load('01_box_particles_MOF5.json')
say(f"size trend on cubes: width = {r1['trend']['a']:.3f} + {r1['trend']['b']:.3f} ln D")
say(f"{'shape':12s} {'blocks':>6s} {'D':>4s} {'width':>14s} {'trend at D':>11s} {'difference':>10s}")
for r in r1['shapes']:
    say(f"{r['label']:12s} {r['nodes']:6d} {r['diameter']:4d} {r['width_mean']:8.3f} +- {r['width_sd']:.3f} "
          f"{r['trend_prediction']:11.3f} {r['excess_over_trend']:+10.3f}")
say('check against code_19: ' + str(r1.get('check_against_code_19')))
z = load('01_box_particles_ZIF8.json') if os.path.exists(os.path.join(T.RESULTS, '01_box_particles_ZIF8.json')) else None
if z:
    say('ZIF-8 (NOT used): connected pieces per cube = ' + str([c['components'] for c in z['cubes']]))"""),
md("""**Reading.** With the same 2048 blocks the cube has the widest spectrum and the rod the
narrowest; the seed spread is below 0.01, so the differences are real for this procedure. The
plate and rod have *larger* diameters than the cube yet lie *below* the cube trend, so the effect
is not just the diameter. ZIF-8's block graph is in many pieces, so it is not used."""),
md("""## Step 2. The crystal shapes our methods predict for MOF-5

**In simple words.** Our shape methods disagree about MOF-5: one says truncated octahedron,
another says cube. We build each predicted crystal out of the same number of building blocks
(about 2000, and again about 4000) and measure the spectrum number. If the numbers differ, the
spectrum "sees" which shape was predicted.

**In technical words.** Each shape is the polyhedron P = {x : n_f·x ≤ s·R_f}. R_f come from the
morphology results: BFDH and UFF Wulff from `morphology/results/hybrid_results.json`, the blend
as R_BFDH^0.5·R_Wulff^0.5, and CHGNet from the cleavage energies in
`morphology/results/chgnet_cleavage_results.json`. A block belongs to the particle if its centroid
is inside P; s is bisected to hit the target block count; only the largest connected piece is
kept. Size is controlled two ways, by a cube trend in graph diameter D and by a cube trend in
block count N. In a pcu net graph distance behaves like the taxicab (L1) distance, so an
octahedron (the L1 ball) has a much smaller diameter than a cube of equal N; the comparison at
equal N is the fair one for shape."""),
code("""import run_02_spectrum_of_predicted_crystal_shapes_MOF5 as S2
if RECOMPUTE:
    S2.main()
r2 = load('02_predicted_crystal_shapes_MOF5.json')
t = r2['cube_trend']
say(f"cube trend: width = {t['a']:.3f} + {t['b']:.3f} ln D   and   width = {t['c_blocks']:.3f} + {t['d_blocks']:.3f} ln N")
say(f"{'target':>6s} {'shape':42s} {'N':>5s} {'D':>3s} {'width':>14s} {'vs trend (same N)':>18s} {'vs trend (same D)':>18s}")
for r in r2['shapes']:
    say(f"{r['target_blocks']:6d} {r['shape']:42s} {r['blocks_in_largest_piece']:5d} {r['diameter']:3d} "
          f"{r['width_mean']:8.3f} +- {r['width_sd']:.3f} {r['difference_from_cube_trend_at_equal_blocks']:+18.3f} "
          f"{r['difference_from_cube_trend']:+18.3f}")"""),
md("""## Step 3. Across real MOFs: does the periodic-graph Δα know the predicted shape?

**In simple words.** For 55 real MOFs from the CoRE MOF database we already have the spectrum
number from the first half of the project. For each of them we now predict the crystal shape with
BFDH and measure how round it is (sphericity) and how stretched it is (aspect ratio). Then we ask:
do MOFs with a bigger spectrum number tend to have more stretched crystals? And does that link
survive once we remove the known effect of graph size?

**In technical words.** Spearman ρ between Δα (from `data/spectrum_descriptors/size_scaling/full_band_core_cg.json`)
and each BFDH shape descriptor, then the partial Spearman ρ with ln(coarse-grained node count)
held fixed (rank residuals). Permutation p-values (10 000 shuffles), bootstrap 95 % intervals
(5 000 resamples). Repeated on the 52 structures whose periodic graph is one connected piece."""),
md("""**Reading (from the run of 2026-10-16; check it against your own numbers above).** At equal
block count N the cube, octahedron, rhombic dodecahedron and the four predicted shapes all lie
within about ±0.05 of the cube trend, which is the same size as the scatter of the cubes
themselves about their own trend (about 0.04), and their order changes between 2000 and 4000
blocks. So the spectrum does **not** reliably tell apart compact (equant) crystal shapes such as a
cube and a truncated octahedron. Compared at equal *diameter* they look very different, but that
is only because their graph diameters differ. Step 1 showed that the spectrum **does** separate
flattened and elongated particles (plate, rod). In short: Δα responds to how stretched a particle
is, not to which faces a compact particle has."""),
code("""import run_03_core_mof_spectrum_width_vs_bfdh_shape as S3
if RECOMPUTE:
    S3.main()
r3 = load('03_core_mof_spectrum_vs_bfdh_shape.json')
say(f"structures with a spectrum and a BFDH shape: {r3['n_with_shape']}")
for subset, tests in r3['tests'].items():
    say(f"\\n[{subset}]")
    for k, v in tests.items():
        if 'partial_p' in v:
            say(f"  {k:28s} n={v['n']:2d}  raw rho {v['spearman']:+.3f} (p {v['spearman_p']:.4f})   "
                  f"size held fixed rho {v['partial_spearman_size_controlled']:+.3f} (p {v['partial_p']:.3f}, "
                  f"95% CI {v['partial_ci95'][0]:+.2f} to {v['partial_ci95'][1]:+.2f})")
        else:
            say(f"  {k:28s} n={v['n']:2d}  rho {v['spearman']:+.3f}")"""),
md("""**Reading (from the run of 2026-10-16).** The raw correlations are real, but they go through
graph size: more stretched predicted shapes come with bigger periodic graphs (ρ about −0.48
between sphericity and node count), and a bigger graph has a wider spectrum (ρ about +0.8). With size held fixed every correlation is close to zero and not significant. So
the **periodic** Δα of the first half carries no shape information beyond size. Steps 1 and 2 show
where shape information does appear: in the spectrum of a **finite particle**."""),
md("""## Step 4. Figures"""),
code("""import make_figures_spectrum_shape_relation as F
F.fig01(); F.fig02(); F.fig03()
from IPython.display import Image, display
for name in ('01_box_particles_MOF5.png', '02_predicted_crystal_shapes_MOF5.png', '03_core_mof_spectrum_vs_bfdh_shape.png'):
    display(Image(os.path.join(T.FIGURES, name)))"""),
md("""## Step 5. Checks"""),
code("""import subprocess
say(subprocess.run([sys.executable, 'check_spectrum_shape_relation.py'], capture_output=True, text=True).stdout)"""),
md("""## What this does and does not show

* **Shown:** for MOF-5, the spectrum width of a finite particle depends on how flat or elongated
  it is at fixed size (cube vs slab, plate, rod).
* **Not separated:** compact shapes (cube, octahedron, truncated octahedron, the BFDH, blend, UFF
  Wulff and CHGNet predictions); their differences are within the method's own scatter.
* **Shown:** across 55 CoRE MOFs, the periodic Δα of the first half is *not* related to the
  predicted BFDH shape once size is controlled.
* **Not shown:** that this holds for other MOFs (one structure for steps 1–2), for faceted
  particles with smooth surfaces (a block is in or out by its centroid), or that Δα of a particle
  predicts adsorption. The error bars are the seed spread only.
"""),
]

nb = nbf.v4.new_notebook()
nb['cells'] = cells
nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}}
nbf.write(nb, NB)
print('wrote', NB)

if '--execute' in sys.argv:
    from nbclient import NotebookClient
    nb = nbf.read(NB, as_version=4)
    NotebookClient(nb, timeout=3600, kernel_name='python3', resources={'metadata': {'path': HERE}}).execute()
    nbf.write(nb, NB)
    print('executed and saved with outputs')
