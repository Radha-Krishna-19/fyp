# Check sheet: second extraction of 20 laboratory records

Purpose: the benchmark rests on 134 records extracted by one person. A second person re-extracts a random
sample **without looking at the dataset first**, then compares. Sample drawn with
`random.Random(20261112).sample(range(134), 20)` over the rows of
`data/experimental_morphology/dataset/experimental_morphology.csv`, so anyone can redraw it.

**How:** for each record open the paper at the stated figure or table (DOI below), write down the MOF, the
shape as the authors describe it, the exposed faces if stated, the additive (or none), the solvent and the
temperature. Only then open the CSV row and mark each field agree / disagree. Report the agreement rate per
field; any disagreement on the shape or the additive is a correction to the dataset.

Checker: ________   Date: ________

| # | record_id | MOF | DOI | Where in the paper | Shape (yours) | Faces | Additive | Solvent | T (°C) | Agrees with CSV? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | HKUST-1-mao2013-1 | HKUST-1 | 10.1039/c3ta12402a | Abstract |  |  |  |  |  |  |
| 2 | UiO-66-cao2018-1 | UiO-66 | 10.3390/ma11040589 | Fig. 2a; Section 3.2 |  |  |  |  |  |  |
| 3 | ZIF-8-cravillon2012-4 | ZIF-8 | 10.1039/c1ce06002c | Fig. 5g,h; Fig. 6 |  |  |  |  |  |  |
| 4 | ZIF-8-cravillon2012-5 | ZIF-8 | 10.1039/c1ce06002c | Experimental; Fig. 7; Tables 1-4 |  |  |  |  |  |  |
| 5 | Mg-MOF-74-xin2024-1 | Mg-MOF-74 | 10.3390/coatings14040383 | Section 2.2; Section 3; Fig. 2a |  |  |  |  |  |  |
| 6 | ZIF-67-langmuir2025-1 | ZIF-67 | 10.1021/acs.langmuir.5c01142 | Table 1; Fig. 3 |  |  |  |  |  |  |
| 7 | ZIF-67-langmuir2025-2 | ZIF-67 | 10.1021/acs.langmuir.5c01142 | Fig. 4 |  |  |  |  |  |  |
| 8 | HKUST-1-rubio2014-3 | HKUST-1 | 10.1038/srep05443 | Fig. 2; Methods (plug-flow reactor, 1.2 min) |  |  |  |  |  |  |
| 9 | MOF-5-suresh2021-3 | MOF-5 | 10.1021/jacs.1c04926 | Fig. 1 |  |  |  |  |  |  |
| 10 | MOF-5-suresh2021-4 | MOF-5 | 10.1021/jacs.1c04926 | Fig. 1 |  |  |  |  |  |  |
| 11 | IRMOF-3-suresh2022-3 | IRMOF-3 | 10.1002/chem.202200334 | Fig. 3b |  |  |  |  |  |  |
| 12 | IRMOF-8-suresh2022-3 | IRMOF-8 | 10.1002/chem.202200334 | Fig. 4c |  |  |  |  |  |  |
| 13 | ZIF-8-tezerjani2021-3 | ZIF-8 | 10.1039/d1ra02856a | Table 1, Table 2, Fig. 7 (sample M3) |  |  |  |  |  |  |
| 14 | HKUST-1-wijaya2021-1 | HKUST-1 | 10.3390/molecules26216430 | Fig. 5g; Methods |  |  |  |  |  |  |
| 15 | Mg-MOF-74-wu2024-12 | Mg-MOF-74 | 10.1039/d4ra03943b | Fig. 4A |  |  |  |  |  |  |
| 16 | Mg-MOF-74-wu2024-13 | Mg-MOF-74 | 10.1039/d4ra03943b | Fig. 4D |  |  |  |  |  |  |
| 17 | ZIF-8-zheng2017-3 | ZIF-8 | 10.1039/c7nr03739b | Fig. 1C |  |  |  |  |  |  |
| 18 | ZIF-8-oh2023-1 | ZIF-8 | 10.1038/s41598-023-39507-6 | Results, Fig. 1a; Preparation of C-ZIF-8 |  |  |  |  |  |  |
| 19 | ZIF-8-oh2023-4 | ZIF-8 | 10.1038/s41598-023-39507-6 | Results, Fig. 1d; Preparation of P-ZIF-8 |  |  |  |  |  |  |
| 20 | UiO-66-morelli2020-3 | UiO-66 | D. Morelli Venturi, F. Campana, F. Marmo | Results; Fig. S33; Table 3 |  |  |  |  |  |  |

Result: shape agrees in ___ / 20; additive agrees in ___ / 20; faces agree in ___ / ___ stated.
