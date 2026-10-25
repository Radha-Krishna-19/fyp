# Schema for `records.jsonl`

One JSON object per line. One object is one synthesis condition that a paper
reports together with the crystal shape it produced. A paper that varies one
parameter over five values gives five records sharing a `source_id`.

A field the paper does not report is `null`. No value is estimated, converted
from a different quantity, or copied from a "typical" recipe.

## Identity

| Field | Meaning |
|---|---|
| `record_id` | `<MOF>-<source_id>-<n>`, unique |
| `mof` | Canonical name used in this project: `ZIF-8`, `HKUST-1`, `UiO-66`, `MOF-5`, ... |
| `metal` | Metal element of the node |
| `linker` | Bridging linker as an abbreviation (`H2BDC`, `H3BTC`, `Hmim`, ...) |
| `net` | RCSR net symbol of the framework (`sod`, `tbo`, `fcu`, `pcu`, ...) |
| `space_group` | Space group of the framework as normally reported |

## Synthesis conditions

| Field | Meaning |
|---|---|
| `method` | `solvothermal`, `room_temperature`, `microwave`, `hydrothermal`, `microfluidic`, `electrochemical`, `hot_injection`, ... |
| `metal_salt` | Metal source as written (`ZnCl2`, `Zn(NO3)2·6H2O`, ...) |
| `metal_conc_mM` | Metal concentration in the reaction mixture, mM, only when stated or directly computable from stated amounts and volume (the computation is noted in `notes`) |
| `linker_to_metal` | Molar ratio bridging-linker : metal |
| `solvent` | Solvent or mixture as written (`MeOH`, `DMF`, `H2O/EtOH 1:1 v/v`) |
| `additive` | Modulator, surfactant, salt or base as written (`sodium formate`, `CTAB`, `acetic acid`) or `none` |
| `additive_amount` | Amount as written, with its unit or basis (`2 eq. per Zn`, `30 eq. per Zr`, `0.5 mM`) |
| `additive_role` | Role the **authors** assign: `coordination_modulator`, `deprotonation_base`, `capping_agent`, `surfactant`, `other`, or `null` |
| `temperature_C` | Reaction temperature in °C |
| `time_h` | Reaction time in hours (minutes converted, original in `notes`) |
| `heating` | `oven`, `oil_bath`, `microwave`, `none` |
| `stirring` | `true`, `false`, `null` |

## Outcome

| Field | Meaning |
|---|---|
| `morphology` | Controlled vocabulary, see below |
| `morphology_as_written` | The authors' own words |
| `facets` | Exposed facet families as written, e.g. `{100}+{110}` |
| `size_um` | Characteristic size in micrometres, as reported (mean, or range as `"a-b"`) |
| `size_basis` | What the size is: `edge`, `diameter`, `max`, `mean`, ... |
| `evidence` | `SEM`, `TEM`, `optical`, `in_situ_XRD`, ... |

`morphology` vocabulary (cubic MOFs): `cube`, `truncated_cube`,
`cube_truncated_edges`, `cuboctahedron`, `truncated_octahedron`, `octahedron`,
`rhombic_dodecahedron`, `truncated_rhombic_dodecahedron`, `tetrahedron`,
`sphere`, `plate`, `rod`, `needle`, `intergrown`, `irregular`, `other`.
Non-cubic MOFs add `hexagonal_prism`, `hexagonal_rod`, `bipyramid`, ... as needed.

## Kinetics and regime

| Field | Meaning |
|---|---|
| `regime` | `thermodynamic` if the authors show the shape persists or is reached at long time; `kinetic` if they show it is transient or growth-rate controlled; `unknown` otherwise. Never inferred by the curator from the shape alone. |
| `kinetics` | Measured rate data as written: Avrami n, k, activation energy, induction time |
| `mechanism_as_written` | The authors' explanation, summarised in a sentence |

## Provenance

| Field | Meaning |
|---|---|
| `source_id` | Short key, e.g. `cravillon2012` |
| `doi` | DOI |
| `citation` | Authors, journal, year, volume, pages |
| `access` | `full_text` (curator read the methods and results), `abstract` (abstract only), `secondary` (taken from a review that cites the primary work; primary DOI goes in `notes`) |
| `locator` | Where in the source: `Experimental`, `Fig. 5`, `Table S1`, ... |
| `varied` | The variable this source changed across its series (`time`, `temperature`, `Hmim/Zn ratio`, `modulator eq.`, ...), so records from one controlled series can be aligned; absent for a single condition |
| `notes` | Anything that qualifies the record |
