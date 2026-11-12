# MOFX-DB metadata of the 138 structures

One JSON file per structure, as returned by MOFX-DB when the CIFs were fetched in September 2026
(`hmof__*` and `h__*`: the 77 hMOF; `core__*`: the 61 CoRE MOF 2019). Only the descriptive fields are
kept (identifier, name, database, MOFid, void fraction, surface areas, pore limiting diameter `pld`, largest
cavity diameter `lcd`, in Å); the isotherms and CIF text of the original download are dropped.

Read by `code/spectrum_pipeline/code_18_subband_explain.py` (chemistry of the Narrow / Medium / Wide
classes). Until 12 November 2026 that script read these files only from an untracked `.cache/` folder, so
its results could not be regenerated from the repository. MOFX-DB returned no MOFid for the CoRE MOF
records (`mofid` is null there), as stated on the Results page.
