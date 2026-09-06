# References

Every source this project actually uses — an algorithm we implement, a dataset we query, a
method we follow, or a physical constant we cite. Nothing here is padding.

`references.bib` is the BibTeX file used by the panel-review deck.

---

## 1 · The algorithm we visualise

| # | Reference | Why it is here |
|---|---|---|
| **[1]** | Bucior *et al.*, **"Identification Schemes for Metal–Organic Frameworks to Enable Rapid Search and Cheminformatics Analysis"**, *Cryst. Growth Des.* **19**(11), 6682–6697 (2019). [doi:10.1021/acs.cgd.8b00126](https://doi.org/10.1021/acs.cgd.8b00126) | **The core reference.** Defines MOFid/MOFkey and the metal-oxo, single-node and all-node decomposition algorithms. Modules `code_01`–`code_07` are a faithful Python translation of this pipeline. |

## 2 · The method we implement

| # | Reference | Why it is here |
|---|---|---|
| **[2]** | Xiao, Wang & Li, **"Deciphering the Generating Rules and Functionalities of Complex Networks"**, *Sci. Rep.* **11**, 22964 (2021). [doi:10.1038/s41598-021-02203-4](https://doi.org/10.1038/s41598-021-02203-4) | **The second core reference.** Source of NMFA and iNMFA: the partition function `𝒫_q(r)`, the mass exponent `τ(q) = ln 𝒫_q / ln(r/r_N)`, and the Legendre transform to `f(α)`. **The τ definition in this paper is exactly what our correction restores.** |
| [3] | Song, Havlin & Makse, **"Self-Similarity of Complex Networks"**, *Nature* **433**, 392–395 (2005). [doi:10.1038/nature03248](https://doi.org/10.1038/nature03248) | Introduces box-covering for network fractal dimension — the method family NMFA sits in, and the contrast [2] draws against box-growing. |

## 3 · Topology

| # | Reference | Why it is here |
|---|---|---|
| [4] | Delgado-Friedrichs & O'Keeffe, **"Identification of and Symmetry Computation for Crystal Nets"**, *Acta Cryst. A* **59**(4), 351–360 (2003). | **Systre.** `code_06` writes a genuine `.cgd` input file for it. We do not reimplement the tool. |
| [5] | O'Keeffe *et al.*, **"The Reticular Chemistry Structure Resource (RCSR)"**, *Acc. Chem. Res.* **41**(12), 1782–1789 (2008). | Source of the net symbols `tbo`, `pcu`, `sod`, `fcu` used as ground truth for our coordination-number validation. |
| [6] | Eddaoudi *et al.*, **"Modular Chemistry: Secondary Building Units…"**, *Acc. Chem. Res.* **34**(4), 319–330 (2001). | The **SBU concept** — why node and linker identity are the design variables of the field. |

## 4 · Data

| # | Reference | Why it is here |
|---|---|---|
| [7] | Bobbitt, Chen & Snurr, **"MOFX-DB"**, *J. Chem. Eng. Data* **68**(2), 483–498 (2023). | **The database our notebook queries live.** Supplies the CIFs, MOFid strings and PLD/LCD pore diameters for all 77 frameworks. |
| [8] | Wilmer *et al.*, **"Large-Scale Screening of Hypothetical Metal–Organic Frameworks"**, *Nature Chem.* **4**(2), 83–89 (2012). | **The hMOF database.** Our 77 structures are hMOF entries — *computer-generated candidates, not synthesised materials*. This citation is why we describe them that way. |
| [9] | Chung *et al.*, **"CoRE MOF 2019"**, *J. Chem. Eng. Data* **64**(12), 5985–5998 (2019). | The **experimental** database our notebook requests. The server returned hMOF records instead; our provenance check now detects this. This is the set needed for metal diversity. |

## 5 · Chemistry — constants and test structures

| # | Reference | Why it is here |
|---|---|---|
| [10] | Cordero *et al.*, **"Covalent Radii Revisited"**, *Dalton Trans.* 2832–2838 (2008). | The covalent radii used for distance-based bond perception in `code_02`. |
| [11] | Chui *et al.*, *Science* **283**, 1148–1150 (1999). | **HKUST-1.** Published Cu₂ paddlewheel, 4-connected, `tbo`. |
| [12] | Li, Eddaoudi, O'Keeffe & Yaghi, *Nature* **402**, 276–279 (1999). | **MOF-5 / IRMOF-1.** Zn₄O node, 6-connected, `pcu`. |
| [13] | Park *et al.*, *PNAS* **103**(27), 10186–10191 (2006). | **ZIF-8.** Our chemical control — binds through nitrogen, contains no oxygen. |
| [14] | Cavka *et al.*, *JACS* **130**(42), 13850–13851 (2008). | **UiO-66.** The critical test: its Zr₆ cluster is **12-connected**, which is what exposes a non-periodic graph construction. |
| [15] | Shearer *et al.*, **"Defect Engineering…UiO-66"**, *Chem. Mater.* **28**(11), 3749–3761 (2016). | Establishes that **missing-linker defects are real, common and deliberately engineered** — the justification for our defect simulation being chemistry rather than a workaround. |

## 6 · Network science

| # | Reference | Why it is here |
|---|---|---|
| [16] | Fiedler, **"Algebraic Connectivity of Graphs"**, *Czech. Math. J.* **23**(2), 298–305 (1973). | Defines **λ₂**, which we use to quantify how much a defect weakens a framework. |
| [17] | Brandes, **"A Faster Algorithm for Betweenness Centrality"**, *J. Math. Sociol.* **25**(2), 163–177 (2001). | The betweenness algorithm implemented in `code_09`. |

## 7 · Software

| # | Reference | Why it is here |
|---|---|---|
| [18] | Larsen *et al.*, **"The Atomic Simulation Environment"**, *J. Phys. Condens. Matter* **29**(27), 273002 (2017). | **ASE** — CIF parsing and PBC-aware neighbour lists in the notebook. |
| [19] | Hagberg, Schult & Swart, **"Exploring Network Structure…using NetworkX"**, *SciPy2008*, 11–15. | **NetworkX** — graph structures and algorithms in `code_09` and `code_10`. |

---

## How to read this list

If you only read two, read **[1] and [2]**.

- **[1]** is the algorithm we visualise. Everything in Sections 7–9 of the website is a
  faithful implementation of it.
- **[2]** is the method we apply. Everything in Sections 15–17 comes from it, and the τ
  definition on its page 22 is the one line our correction restores.

**[8] and [9] together explain the dataset problem.** We requested [9] (experimental) and
received [8] (hypothetical). Both are cited because the distinction changes what we are
allowed to claim.

**[15] is why the defect work is legitimate.** Without it, "we deleted a linker" looks like
an arbitrary manipulation. With it, it is standard MOF chemistry.
