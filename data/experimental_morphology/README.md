# Experimental morphology task

## The task

> Find actual lab-experimented results for carbon MOFs (MOFs that adsorb CO2)
> and align them properly for each MOF, based on solvent, temperature,
> kinetics, molecular factors and so on. Not everything will be available in
> one place: research, store a lot of data and combine it.

It feeds the MorphoGraph-MOF pipeline (CIF → surfaces → CHGNet surface
energies → BFDH baseline → dataset → GNN → Wulff/BFDH morphology →
validation). This task supplies the experimental side of Step 8, "test on
known experimental morphologies", and the solvent and temperature conditions
the pipeline does not yet model.

## What is in this folder

| Folder | Contents |
|---|---|
| `dataset/` | **The deliverable.** Start with `dataset/README.md`. |
| `dataset/experimental_morphology.csv` | 134 lab results (rebuilt 2026-10-14): MOF, solvent, temperature, time, metal salt and concentration, linker:metal ratio, additive and amount, stirring, heating, observed shape, facets, size, source DOI. |
| `dataset/aligned_by_mof.md` | The same results grouped per MOF and per controlled series (shape against ratio, time, solvent, additive). |
| `dataset/kinetics.csv` | 25 rows of crystallisation kinetics: rate constants, Avrami exponents, activation energies. |
| `dataset/co2_adsorption.csv` | 18 rows of measured CO2 uptake (CALF-20, UiO-66, UiO-66-NH2, Mg-MOF-74, MIL-101(Cr)), each tied to how the sample was made. |
| `dataset/experimental_morphology_unverified.csv` | 11 records whose source could not be identified (no DOI, no copy, not found by search). Kept out of every table and the benchmark until confirmed. |
| `dataset/records/` | The curated source data, one file per paper. |
| `compare/COMPARISON.md` | **Project predictions vs experiment** for MOF-5, HKUST-1, UiO-66 and ZIF-8 (BFDH, graph rule, attachment Wulff, broken-bond Wulff, UFF Wulff with its bond-cost robustness, BFDH x UFF hybrid, CHGNet cleavage-energy proxy). Also shown on the website's Experiment page. Rerun with `python compare/compare_with_project.py`. |
| `PAPERS_USED.md` | Every paper used, with DOI, MOFs, and which table it feeds. |
| Papers | The 15 open-access papers read in full and 7 full texts from PubMed Central are not stored in the repository, because their licences vary; every one is identified by DOI in `PAPERS_USED.md` and `dataset/sources.jsonl`. |
| Notebooks | Keerthi's `MorphoGraph_MOF_revised.ipynb`, the Colab version that was run (`MorphoGraph_MOF_colab_4MOFs.ipynb`) and the symmetric-slab version (not yet run) are in [`notebooks/morphograph_mof/`](../../notebooks/morphograph_mof/); their outputs are in [`data/chgnet_morphograph_runs/`](../chgnet_morphograph_runs/). |
| `tools/` | The literature-search scripts used to find and read the papers. |

## Status (2026-10-14): about 75 % done (CO2 focus)

| Part | Done | Notes |
|---|---|---|
| Find lab results and combine sources | ~90 % | 134 shape results from 35 sources (plus 11 unverified), 18 CO2 uptake rows, 12 MOFs with shapes, 14 with any data |
| Cover the main CO2-adsorbing MOFs | ~70 % | HKUST-1, UiO-66, UiO-66-NH2, ZIF-8, Mg-MOF-74, CALF-20, MIL-101(Cr); Mg-MOF-74 shape data is abstract-only, CALF-20 and MIL-101(Cr) have no shape data |
| Align by additives, modulators, linker:metal ratio | ~90 % | |
| Align by temperature | ~75 % | MOF-5, HKUST-1, UiO-66, ZIF-8, IRMOF-8 |
| Align by kinetics | ~75 % | 9 MOFs; overall crystallisation rates only, not face-specific growth rates |
| Align by solvent | ~40 % | Only ZIF-8 has a full solvent comparison |

## To do

1. **Optional, needs college library access.** Download these and put the
   PDFs locally (they are not committed), then the abstract-only rows can be completed:
   - Umemura et al., JACS 2011, `10.1021/ja204233q` (HKUST-1, lauric acid)
   - Schaate et al., Chem. Eur. J. 2011, `10.1002/chem.201003211` (UiO-66 modulators)
   - Ma et al., Nano Res. 2023, `10.1007/s12274-023-5655-5` (ZIF-8, 30 C vs -40 C)
   - Also useful, and free to read in an ordinary browser (the sites only
     blocked automated download): Xin et al., Coatings 2024,
     `10.3390/coatings14040383`, and Campbell & Tokay 2017 (author copy on
     the Nottingham repository), `10.1016/j.micromeso.2017.05.058`. Both are
     Mg-MOF-74 shape and CO2 papers.
2. Solvent comparisons for MOF-5 (DMF vs DEF) and UiO-66 were searched for
   and not found in open access.
3. No paper found that measures CO2 uptake on two crystal shapes of the same
   MOF; this would link the shape and CO2 tables directly.
4. `dataset/records/yuliarto2021.jsonl` and
   `dataset/records/zif67_langmuir2025.jsonl` are empty leftovers and can be
   deleted.
5. Identify the sources of the 11 unverified records (yanez2024, isaeva2020,
   cortes2019, arjmandi2016, noorani2025): add DOI and citation to
   `sources.jsonl`, set `access` to `full_text`, rebuild.
6. (Done 2026-10-14) A primary source for octahedral modulated UiO-66 was
   found: Butova et al., Nanomaterials 2023, `10.3390/nano13101675`.

## Rebuilding and adding data

```
cd dataset
python build_dataset.py
```

To add a paper, follow "How to add a paper" in `dataset/README.md`.

The scripts in `tools/` need `pip install requests pypdf`. They query
OpenAlex, Europe PMC and NCBI (all free, no key) and only download
open-access copies.

## Additive-free labels that are judgement calls (13 November 2026)

`code/morphology/run_benchmark_mofs.py` counts a record as additive-free when its `additive` is `none` or
blank, or its `additive_amount` contains "or none". Three records depend on that rule:

| Record | Additive | Amount | Counted as |
|---|---|---|---|
| HKUST-1-umemura2011-1 | n-dodecanoic (lauric) acid | lowest (or none) | additive-free |
| HKUST-1-mao2013-1 | not recorded | not recorded | additive-free |
| HKUST-1-mao2013-2 | not recorded | not recorded | additive-free |

The list is regenerated in `benchmark_mofs.json` (`additive_free_judgement_calls`). Checking the two
mao2013 records against the paper is part of the blind second extraction (`docs/defence/check_sheet_records.md`).
