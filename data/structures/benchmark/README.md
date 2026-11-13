# Structures added for the 8-MOF benchmark

Used by `code/morphology/run_benchmark_mofs.py`, which scores the structure-only shape prediction against the laboratory records.

| File | Framework | Source |
|---|---|---|
| `IRMOF-3.cif` | IRMOF-3, Zn4O(NH2-bdc)3 | RASPA2 library (commit 6498ab1). Stored in P1; the amino groups are ordered, so only the four F-centring translations are found as symmetry. The centring decides the cancelled planes, so BFDH matches MOF-5. |
| `IRMOF-8.cif` | IRMOF-8, Zn4O(ndc)3 | RASPA2 library. Stored in P1; the ordered naphthalene linkers leave only P2_1/c symmetry (4 operations) and no centring. Its BFDH shape therefore differs from that of an ideal Fm-3m framework; results for IRMOF-8 depend on this ordering and are reported with that caveat. |
| `ZIF-67.cif` | ZIF-67, Co(mIm)2 | Built from `website/ZIF-8.cif` by `build_zif67.py` (every Zn replaced by Co). ZIF-67 and ZIF-8 are isostructural. |
| `build_zif67.py` | | the script that writes ZIF-67.cif |

SHA-256:

```
bf7839cc9e04294f5aca7a332d47a5a68b39f0837aa2215bbe936b31d4ca4e08  IRMOF-3.cif
b0e073ec41e9a5c41631d970fcbc06b91902ff32a42c96fec774aeba88197918  IRMOF-8.cif
ae7f291c6f82e5b86456bf5774acf7b1fb0d9b5010c1e27d59b66a1ec4f038c3  ZIF-67.cif
```
