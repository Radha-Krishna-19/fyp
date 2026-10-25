"""
make_colab_bundle_spectrum_shape_relation.py
============================================

Builds  build/spectrum_shape_relation_bundle.zip  (at the repository root): every file the notebook
Spectrum_Shape_Relation.ipynb needs, so the notebook can also be run in Google Colab
(upload this zip when the notebook asks). Not needed when running on your own PC.

Contents (paths kept as in the repository):
    code/spectrum_pipeline/*.py and code/spectrum_pipeline/*.cif               the spectrum code (code_01 ... code_19) and the four CIFs
    code/morphology/mofmorph/                  the morphology package (BFDH etc.)
    code/morphology/results/hybrid_results.json, chgnet_cleavage_results.json
    data/spectrum_descriptors/size_scaling/full_band_core_cg.json, spectrum_vs_shape_MOF5.json, spectrum_vs_shape_ZIF8.json
    data/structures/core_mof_2019/*.cif        the 61 CoRE MOF 2019 structures used by run_03
    code/spectrum_shape_relation/              this folder (scripts and notebook), without old results

Run from this folder:   python make_colab_bundle_spectrum_shape_relation.py
"""
import glob
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'build', 'spectrum_shape_relation_bundle.zip')   # build/ is ignored by git

files = (glob.glob(os.path.join(REPO, 'code', 'spectrum_pipeline', '*.py')) + glob.glob(os.path.join(REPO, 'code', 'spectrum_pipeline', '*.cif'))
         + glob.glob(os.path.join(REPO, 'code', 'morphology', 'mofmorph', '*.py'))
         + [os.path.join(REPO, 'code', 'morphology', 'results', f)
            for f in ('hybrid_results.json', 'chgnet_cleavage_results.json')]
         + [os.path.join(REPO, 'data', 'spectrum_descriptors', 'size_scaling', f)
            for f in ('full_band_core_cg.json', 'spectrum_vs_shape_MOF5.json', 'spectrum_vs_shape_ZIF8.json')]
         + glob.glob(os.path.join(REPO, 'data', 'structures', 'core_mof_2019', '*.cif')))
for root, _dirs, names in os.walk(HERE):
    if os.sep + 'results' in root or os.sep + 'figures' in root or '__pycache__' in root:
        continue
    files += [os.path.join(root, n) for n in names]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(set(files)):
        if os.path.exists(f):
            z.write(f, os.path.relpath(f, REPO))
print('wrote', OUT, f'({len(set(files))} files)')
