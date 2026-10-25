# Experimental data for CO2-adsorbing MOFs, aligned by synthesis condition

The task: lab-measured results for MOFs that adsorb CO2, aligned per MOF by
solvent, temperature, kinetics and molecular factors (additives, modulators,
linker:metal ratio). Three linked tables, all keyed by MOF name:

1. **Crystal shape against synthesis conditions** (`experimental_morphology.csv`).
   This is what the morphology pipeline (CHGNet surface energies, Wulff, BFDH)
   has to reproduce.
2. **Crystallisation kinetics** (`kinetics.csv`).
3. **CO2 uptake against synthesis conditions** (`co2_adsorption.csv`).

Collected 2026-10-13/14 for the morphology direction of the project (pipeline
Step 8: "test on known experimental morphologies").

## Files

| File | What it is |
|---|---|
| `experimental_morphology.csv` | The combined dataset, one row per (condition, shape) observation. Generated. |
| `aligned_by_mof.md` | The same rows grouped by MOF, then by source and by the variable the source changed. Generated. |
| `records/<source>.jsonl` | The curated records, one file per paper. Edit these. |
| `sources.jsonl` | Citation, DOI, and how much of each paper was read (`full_text` or `abstract`). |
| `mofs.json` | Metal, linker, RCSR net and space group for each MOF. |
| `SCHEMA.md` | Every field and its allowed values. |
| `build_dataset.py` | Validates every record against the schema and regenerates the outputs. Run `python build_dataset.py`. |
| `kinetics.jsonl` → `kinetics.csv` | Measured crystallisation kinetics (rate constants, Avrami exponent, activation energies), joined to the shape data by MOF name. |
| `co2_adsorption.jsonl` → `co2_adsorption.csv` | Measured CO2 uptake (mmol/g at a stated temperature and pressure), heat of adsorption and CO2/N2 selectivity, each tied to the synthesis conditions of the sample measured. |

`records/yuliarto2021.jsonl` and `records/zif67_langmuir2025.jsonl` are empty
leftovers of two renamed files and can be deleted.

## Coverage

104 shape records from 28 papers covering 13 MOFs, 25 kinetics rows, and 18
CO2 uptake rows. `co2_capture` in `mofs.json` says how strong a CO2
adsorbent each MOF is generally considered to be. That label is the
curator's summary of the general literature, not a value measured in this
dataset.

| MOF | CO2 adsorbent? | Shape records | CO2 rows | Kinetics | Levers covered |
|---|---|---|---|---|---|
| HKUST-1 | yes | 22 (8 papers) | - | 4 | temperature and residence time, solvent, lauric acid, salts, SDS, CTAB, acetic acid, ligand:metal ratio, citric acid |
| UiO-66 | yes | 10 (6 papers) | 1 | 4 | time at 140 C, pre-formation temperature, HBr, acetic/benzoic acid, polyacid |
| UiO-66-NH2 | yes | 1 | 2 | 1 | amine linker (vs UiO-66), graphene oxide |
| Mg-MOF-74 | yes (strongest) | 4 (abstracts) | 1 | Co/Ni analogues: 4 | sodium acetate, EtOH/H2O fraction, water amount |
| CALF-20 | yes (commercial) | - | 12 | - | heating method (solvothermal vs microwave) and time |
| MIL-101(Cr) | yes | - | 2 | - | CO2 uptake against adsorption temperature |
| ZIF-8 | moderate | 30 (6 papers) | - | 6 | Hmim/Zn ratio, time, solvent x method, CTAB, TRIS, temperature |
| ZIF-67 | moderate | 3 | - | 1 | CTAB, stirring, temperature |
| MIL-53(Fe) | moderate | 3 | - | 3 | HCl |
| MOF-5 | weak | 18 (3 papers) | - | - | temperature x time, metal:ligand ratio and dilution, 10 additives |
| IRMOF-3, IRMOF-8, SNU-70, Zn4O(FMA)3 | weak | 13 (1 paper) | - | - | designed additives |

82 shape records come from papers read in full and 22 from abstracts. Every
row says which.

Kinetics rows: HKUST-1 (4), UiO-66 and variants (5), ZIF-8 (6), ZIF-67,
MIL-53(Fe) (3, one per heating method), CPO-27/MOF-74 Co and Ni (4),
MOF-801, MOF-14. Two rows come from papers read in full (Cravillon 2012,
Semivrazhskaya 2023). The rest come from Table 1 of the Van Vleet et al.
2018 review, with each row naming its primary paper. The review's PDF text
loses empty table cells, so each row is marked `unambiguous` or `inferred`
and keeps the raw printed row. The ZIF-8 row matches Cravillon 2012, read
in full, to every digit, which confirms the column mapping.

## What the data says, lever by lever

Each line cites the records it rests on. "Same lab" means the agreement is
not independent.

**Solvent**
- ZIF-8, Zn:Hmim 1:8: methanol and DMF both give rhombic dodecahedra by
  stirring, solvothermal and ultrasonic routes; water gives a different,
  layered phase (flakes or rods), not sod ZIF-8 (`tezerjani2021-1..9`).
  Particle size order between MeOH and DMF reverses between room-temperature
  stirring and 140 C solvothermal.
- HKUST-1: water-ethanol gives cuboctahedral seeds, pure ethanol gives
  octahedral seeds (`mao2013`, abstract only).

**Temperature and time**
- ZIF-8 in MeOH with formate at 120 C: cube with truncated edges at 15-20 min,
  rhombic dodecahedron by 45 min and at 4 h, with Ostwald ripening between
  (`cravillon2012-1..4`). The authors conclude the rhombic dodecahedron is the
  equilibrium shape. This is the only series in the set that separates a
  kinetic shape from a thermodynamic one directly.
- Crystallisation kinetics (`kinetics.csv`):
  - **ZIF-8:** in MeOH with formate at 120-140 C, Ea(nucleation) is
    69.0 kJ/mol and Ea(growth) 71.8 kJ/mol. In DMF at 110 C the rate
    constants are about 100 times smaller (115 and 88 kJ/mol).
  - **HKUST-1:** at 105 C, Ea(n) 71.6 kJ/mol and Ea(g) 63.8 kJ/mol. In
    H2O/EtOH at 100 C, microwave heating raises the nucleation rate constant
    about 7-fold over conventional heating.
  - **UiO-66:** 62 kJ/mol for both steps, with nucleation about ten times
    faster than growth, which explains its narrow ~200 nm crystallites. A
    separate HCl-modulated run at 80 C gave only 11-22 kJ/mol.
  - **MIL-53(Fe):** at 70 C in DMF, ultrasound gives the fastest rates,
    then microwave, then conventional heating.
  - **General:** activation energies cluster at 60-100 kJ/mol but depend on
    solvent, heating method and linker substituent.
- MOF-5: 110-150 C for 12-18 h gives cubes with a broad 200-1300 um spread;
  60-90 C for 24-72 h narrows the spread but lowers BET area; the shape stays
  cubic throughout (`suresh2021-5`). An independent lab in DMF agrees: cubes
  at 105, 120 and 140 C, with 140 C for 12 h giving the smallest and
  smoothest (85-95 um) and lower temperature with longer time giving
  250-300 um (`mulyati2015-1..3`).
- HKUST-1 in ethanol, continuous flow: octahedra at 80 C and at 140 C, and at
  residence times from 1 to 10 min. Shorter times give smaller particles
  (100 nm to 1 um) and less ideal shapes, but the habit stays octahedral
  (`rubio2014-1..3`).
- UiO-66 without modulator, DMF, 140 C: cube-like clusters at 6 h; from
  36 h new XRD peaks appear and by 72 h the product is needle-like and no
  longer phase-pure UiO-66 (`rahmawati2014-1..2`). Unmodulated UiO-66 is not
  the stable end product at this temperature.
- UiO-66: raising the cluster pre-formation temperature from 120-130 C to
  140 C changes cubes to spheres (`ahmad2025-1..3`).
- IRMOF-8 with additive: rhombic dodecahedra both at room temperature
  (12 days) and at 85 C (24 h); without additive, room temperature gives a
  cube/cuboctahedron mixture (`suresh2022`).

**Linker:metal ratio and concentration**
- ZIF-8 in MeOH, room temperature: Hmim/Zn 1 gives cubes (with by-products),
  2-4 truncated rhombic dodecahedra, 8-16 rhombic dodecahedra; size falls from
  1 um to 0.1 um between ratios 4 and 16 (`zhang2018-1..5`).
- MOF-5: ratio and dilution change size (279-2349 um) but not the cubic shape
  (`suresh2021-1..4`).
- HKUST-1: raising ligand:metal from 0.25 to 1.00 changes octahedra to rods
  (`wijaya2021-2`, trend statement).
- HKUST-1 in EtOH/DMF/H2O 1:1:1 at 100 C:
  - Without additives, crystals are octahedral (intergrown).
  - CTAB:BTC 0.3 keeps the octahedra (16-18 um) but makes them mesoporous.
  - CTAB 0.6 makes them irregular.
  - Adding acetic acid on top of CTAB also makes them irregular
    (`ediati2019-1..4`). In contrast, acetic acid alone at room temperature
    in EtOH/H2O kept them octahedral (`wijaya2021-3`).

**Modulators, surfactants and salts** (facet-selective binding)
- HKUST-1, two directions:
  - Lauric acid takes octahedron to cuboctahedron to cube (`umemura2011`).
  - Inorganic salts (`liu2016`) and SDS (`wu2020`) take cube to cuboctahedron
    to octahedron. These two come from independent laboratories and agree.
- ZIF-8:
  - CTAB caps {100} and gives cubes; TRIS caps {111} and gives octahedra
    (`zheng2017`).
  - Together they give hexapods and burr puzzles.
  - More TRIS gives flakes, then flowers.
- MOF-5 and its analogues (same lab):
  - An additive changes the shape only when its length matches the
    cluster-to-cluster distance across a pore window.
  - H3BTB gives a cuboctahedron at about 2 mol % and an octahedron at about
    4 mol %. Above about 4 mol % a second phase (UMCM-1) appears.
  - m-Terphenyl dicarboxylic acids give rhombic dodecahedra.
  - Alkane diacids change nothing (`suresh2021`, `suresh2022`).
- UiO-66:
  - Low benzoic or acetic acid gives intergrown crystals; more gives
    individual crystals (`schaate2011`, abstract).
  - HBr at 0.2 M precursor gives agglomerated cuboctahedra (`chen2022`).
  - Polyacrylic acid gives small, irregular particles (`bentz2019`).
- MIL-53(Fe): HCl turns columnar crystals into double spindles. At 40 uL HCl
  a MIL-88 phase and layered crystals appear (`jiang2019`).
- ZIF-67: a CTAB level chosen from the ZIF-8 map gave plates but not clean
  cubes. A recipe tuned for one MOF does not carry over to its isostructural
  partner (`pacheco2025`).

**CO2 uptake against synthesis** (`co2_adsorption.csv`)
- CALF-20 in MeOH at 180 C (`pereira2025`): microwave heating for 4 h gives
  4.89 mmol/g at 273 K and 4.02 mmol/g at 298 K, 1 bar. The 48 h solvothermal
  route gives 4.65 and 3.38. Microwave runs shorter than 4 h are incompletely
  converted (extra PXRD peaks) and adsorb less (3.06-4.24 at 273 K). Uptake
  tracks BET area across all six samples.
- UiO-66 against UiO-66-NH2 (`cao2018`, same lab and recipe): at almost the
  same BET area (838 vs 822 m2/g), the amine raises uptake from 3.66 to
  3.93 mmol/g at 273 K, and CO2/N2 selectivity from 14.8 to 22.8. In the same
  paper the NH2 crystals are smaller cubes (150 nm against 300 nm).
- Mg-MOF-74 (`xin2024`, abstract): sodium acetate turns cauliflower-like
  particles into 400 nm rods and gives 3.67 mmol/g in a fixed bed at 30 C
  and 0.1 bar CO2.
- MIL-101(Cr) (`liu2013`): 0.495 mmol/g at 298 K falling to 0.279 at 348 K
  under 0.1 atm CO2 (breakthrough).
- Uptake values measured by different methods (volumetric isotherm at 1 bar
  against fixed-bed breakthrough at 0.1 bar) cannot be compared directly;
  `measurement` and `uptake_P_bar` say which applies to each row.
- No paper here measures CO2 uptake on two different crystal shapes of the
  same MOF at matched surface area, so the data cannot yet say whether shape
  itself changes CO2 uptake. Searched for and not found in open access.

## What this means for the computational pipeline

1. **Vacuum surface energies cannot reproduce most of these results.** The
   CHGNet notebook ([`notebooks/morphograph_mof/MorphoGraph_MOF_revised.ipynb`](../../../notebooks/morphograph_mof/MorphoGraph_MOF_revised.ipynb)) computes gamma for
   bare slabs. In the data above, the shape of one MOF moves across the whole
   cube–cuboctahedron–octahedron range with the additive alone. Two
   additives even push HKUST-1 in opposite directions. A single set of
   vacuum gammas predicts one shape per MOF. The fair test is therefore
   against additive-free, long-time records.
2. **Use the long-time, additive-free rows as the benchmark.** The closest
   to an equilibrium shape in this set:
   - ZIF-8 rhombic dodecahedron (`cravillon2012-4`, `zhang2018-4/5`,
     `tezerjani2021` MeOH/DMF rows). BFDH in Phase 1 of this project also
     gives a rhombic dodecahedron for ZIF-8.
   - MOF-5 cube without additives (`suresh2021-1..4`, `suresh2022-1`, and an
     independent lab, `mulyati2015-1..3`).
     BFDH in Phase 1 gives a truncated octahedron for MOF-5, which does not
     match. Phase 1's attachment-number model gives a cube for pcu, which
     does.
   - HKUST-1 octahedron without additives (`ediati2019-1` in
     EtOH/DMF/H2O at 100 C; `rubio2014-1..3` in EtOH at 80-140 C; the
     lowest-modulator end of `umemura2011`). Phase 1's BFDH gives a truncated
     octahedron, which does not match.
   - UiO-66 octahedron (`schaate2011-2`, abstract); fcu attachment numbers in
     Phase 1 give an octahedron.
3. **The additive results are the input the panel's "solvent, temperature
   and every other condition" request needs.** Each modulator record names
   the facet it stabilises. Lowering that facet's gamma by an
   adsorption term is the usual way to add solvent and additive effects to a
   Wulff construction, and these records are the validation targets for it.
4. **hMOF structures cannot be validated this way.** They are hypothetical
   and have never been synthesised, so there is no experimental shape for
   them. Experimental validation has to use real MOFs such as the ones here.

## Limits

- Only ZIF-8 has a full solvent series measured within one paper. HKUST-1
  has an ethanol vs water-ethanol comparison (abstract only). No source
  compares solvents directly for MOF-5 (DMF vs DEF) or UiO-66; both are
  made in DMF in nearly every paper here. Searched and not found in open
  access; the closest UiO-66 lead (Lozano et al. 2017, DMF-free medium) is
  on a repository that did not respond.
- Kinetics are measured for crystallisation (how fast the phase forms), not
  for the growth rate of individual faces. No open source here gives
  face-specific growth rates, which is what a kinetic shape model would need.
- HKUST-1 has no long, slow temperature series. The flow paper covers
  80 and 140 C at residence times of minutes.
- 18 rows rely on abstracts of paywalled papers (Umemura 2011, Liu 2016,
  Mao 2013, Liu 2018, Pan 2011, Ma 2023, Schaate 2011, Wu 2020), so their
  concentrations and temperatures are missing. A copy of any of these from
  the college library would fill them in.
- Shapes are taken from the authors' text. Figure images were not read, so a
  shape the text does not state is not entered.
- Two papers are by one group (Matzger) and account for 28 records.

## Read but not entered (no condition-to-shape statement in the text)

- Webber et al., ACS AMI 2017, NU-1000 modulator (phase purity only).
- Chen et al., Chem. Mater. 2022 (PMC9555823), aromatic acid modulators for
  UiO-66 (crystal-domain sizes; shapes only in SEM figures).
- PMC10520824, review of MOF assembly (typical habits; secondary).
- PMC6979335, review of MOF nanocrystal size control (sizes compiled in its
  ESI; worth mining for size data).
- PMC10618523, correlated disorder in UiO-66 (defects, not shape).
- Rubio-Martinez et al. 2014, UiO-66 in flow at 130 C (size under 100 nm,
  shape not stated); the HKUST-1 part of that paper is entered.
- Van Vleet et al. 2018 review: used only for `kinetics.csv`.
- Oktavian et al., Nat. Commun. 2024 (CALF-20 adsorption and flexibility):
  its quoted uptakes mix simulated and measured values, so none were entered.
- PMC10131197 (JACS Au 2023): ZIF-8 and HKUST-1 grown on gold monolayers,
  not free crystals, and no CO2 data.
- PMC12566313 (Mg-MOF-74 thin films): film morphology and IR CO2 sensing, no
  uptake in mmol/g.
- PMC10579389 (ZIF-8 CO2 at GPa pressures in a diamond anvil cell): not
  comparable with ordinary uptake values.

## How to add a paper

1. Create `records/<firstauthorYEAR>.jsonl` with one JSON object per line,
   following `SCHEMA.md`. Leave out any field the paper does not state.
2. Add the paper to `sources.jsonl`, with `access` set honestly.
3. Run `python build_dataset.py`. It refuses to write anything if a record
   breaks the schema.
