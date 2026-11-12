# Check of the team's CIF-to-Wulff pipeline, steps 1–8 (10 November 2026)

Kshitij's notebook `MOF_Wulff_steps1-8.ipynb` writes one module, `mofwulff.py`, that goes from a CIF
to a Wulff shape: standardise the structure, split it into building blocks, list face families and
terminations, cut slabs of whole blocks, cap broken metal–linker bonds with dissociated water,
compute CHGNet energies (static, then relaxed for the lowest termination), and build and name the
shape. This folder holds the run of that module outside Colab and the checks of each problem found.
Results and the list of problems (K1–K11) are on the website page "The morphology map", section
"Checking the team's CIF-to-Wulff pipeline".

Needs: `pip install chgnet pymatgen ase spglib pandas torch`, and the four RASPA2 CIFs the notebook
downloads (ZIF-8, HKUST-1, Mg-MOF-74, UiO-66).

| Item | What it is |
|---|---|
| `kshitij_k11fix/mofwulff.py` | Kshitij's module with two marked one-line fixes (K11 in `run_mof`, K3 in `block_slabs`); everything else is his |
| `run_nb.py` | Runs the notebook's cell 5 (steps 1–6 and 8) unchanged: `python run_nb.py kshitij_k11fix <cif folder> <out dir> quick` (static, about 20 s) or `full` (relaxed; needs a GPU or hours of CPU). Environment variable `TOPK` sets RELAX_TOP_K |
| `one_face.py`, `watch.py` | One face at a time with a memory guard (used for HKUST-1 {111}) |
| `slabcheck.py` | Slab sizes and plane checks |
| `k11.py`, `k11_results.json` | K11: after relaxation, HKUST-1 and Mg-MOF-74 faces are converted to the wrong primitive planes |
| `checks/naming.py`, `checks/naming_check.json` | K1: the notebook's shape names against the exact Wulff limits |
| `checks/open_shape.py` | K6: a missing face family is reported as a rod |
| `results_quick/` | Quick (static) mode, all four MOFs: `wulff_summary_all.csv`, `slabs_all.csv`, Wulff PNG and OBJ files, slab CIFs, cache |
| `results_full_fixed/` | Full (relaxed) mode with the K3 and K11 fixes: ZIF-8 complete; HKUST-1 {100} (`fix_HKUST-1.log`) and {111} (`one_face_HKUST-1_111.log`); UiO-66 {100}; Mg-MOF-74 {100} and {2̄10}. Larger slabs ran out of memory on an 8 GB machine |

Status of the problems: K3 and K11 fixed here; K1, K2, K4 and K5–K10 are open and listed for Kshitij.
