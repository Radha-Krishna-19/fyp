# CHGNet surface energies → Wulff shape → lab comparison

Takes MOF CIFs and a table of laboratory crystal shapes, computes CHGNet surface energies,
builds the Wulff shape and reports whether it matches the lab. Nothing about any MOF is
written into the code: everything comes from two CSV files.

## Run on Google Colab

1. Open `MOF_Wulff_Colab.ipynb` in Colab (File → Upload notebook).
2. Run cell 1 (install) and, if you want results saved to Drive, cell 2.
3. Run the three `%%writefile` cells.
4. Run the upload cell. Upload `mofs.csv`, the lab CSV and every CIF that `mofs.csv` names,
   or one `.zip` holding all of them. The cell lists what it found and flags missing CIFs.
5. Settings cell: keep `QUICK_TEST` ticked for the first run (no relaxation, seconds per
   MOF). Put one name in `ONLY` to test a single MOF. Then untick `QUICK_TEST` for the
   real run; cached slabs are not recomputed.
6. Run, look at the tables, download the zip.

After editing any `.py` file, run `python make_colab.py` to rebuild the notebook.

## Input files

`mofs.csv`

| column | required | meaning |
|---|---|---|
| `mof` | yes | name; must match the name used in the lab CSV (case, spaces, hyphens ignored) |
| `cif` | yes | CIF file name, relative to the CSV, or an absolute path |
| `faces` | no | e.g. `100 110 111`; default from the settings |
| `symprec` | no | symmetry tolerance in Å, default 0.1 |

Lab CSV, either layout:
- **Project dataset** ([`data/experimental_morphology/dataset/experimental_morphology.csv`](../../../data/experimental_morphology/dataset/experimental_morphology.csv)):
  rows with no additive are the benchmark, and the most frequent shape per MOF is the lab
  shape. A tie is reported as `ambiguous:a/b`, never resolved silently.
- **Simple table**: columns `mof, shape` (optional `facet, source`).

`example_inputs/` holds a working `mofs.csv`, the four demonstration CIFs and the dataset CSV.

## Output files (in the results folder)

| file | content |
|---|---|
| `wulff_summary.csv` | per MOF: predicted shape, dominant face, area fractions, γ per face, lab shape, number of lab records, match flags |
| `surface_energies.csv` | the lowest-γ slab per MOF and face (the values used for the Wulff shape) |
| `slabs.csv` | every slab computed: termination, atoms, area, steps, convergence, energy, γ |
| `cache/<MOF>/` | one JSON per slab (and CIFs with `--save-slabs`) |

## Method and its limits

- `blockslab.py`: slabs made of whole metal clusters and whole linkers. Only metal–linker
  bonds are cut and every slab is stoichiometric. Flat pymatgen cuts slice clusters: in
  MOF-5 the lowest {111} flat cut (0.098 J/m²) breaks a Zn4O cluster, and in UiO-66 every
  flat {100} cut splits a Zr6 cluster.
- γ = (E_slab − N·e_bulk)/(2A), atoms relaxed at fixed cell with CHGNet. Most slabs have
  different top and bottom faces, so γ is the average of the two (`basis = asymmetric_average`).
- `capping.py` (`--cap water`): each broken metal–ligand bond is healed with one H2O.
  This is a crude stand-in for solvent; the capping positions are guesses that relaxation
  corrects.
- Vacuum (or water-capped) surface energies cannot reproduce shapes that a modulator or
  surfactant controls. That is why only additive-free lab records are used as the benchmark.
- Flat-cut CHGNet energies from this code reproduce those of Keerthi's notebook
  (HKUST-1 {111} 0.151, {100} 0.164; UiO-66 {100} 0.211, {111} 0.288 J/m²), so the CHGNet
  numbers agree between the two implementations. What differs is the choice of slabs.
