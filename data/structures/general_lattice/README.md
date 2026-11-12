# CIF files for the "Any Lattice" section of the CIF to Shape page

Six non-cubic MOFs and one cubic reference, used by `code/morphology/run_general_shape.py` (Python,
symmetry by spglib) and `website/mof_general_shape.js` (browser). `website/tests/test_general_shape.js`
checks that the two give the same numbers.

| File | Framework | Source |
|---|---|---|
| `MgMOF-74.cif` | Mg-MOF-74, Mg2(dobdc), R-3 | RASPA2 library |
| `MIL-53Cr-lt.cif` | MIL-53(Cr), hydrated narrow-pore form, C2/c | RASPA2 library (`MIL-53(Cr)lt.cif`, renamed) |
| `MIL-47.cif` | MIL-47(V), Pnma | RASPA2 library |
| `MIL-88A-open.cif` | MIL-88A(Fe), swollen form | RASPA2 library |
| `MIL-88A-dry.cif` | MIL-88A(Fe), dry form | RASPA2 library |
| `ZIF-7.cif` | ZIF-7, R-3 | RASPA2 library |
| `MOF5.cif` | MOF-5, Fm-3m | the project's own file, identical to `website/MOF5.cif` |

RASPA2 library: https://github.com/iRASPA/RASPA2, folder `structures/mofs/cif`, commit
`6498ab1eec9c8e0f063dcd0d71dd7add372c529b`. The files are used unchanged apart from the one rename.
The literature reference for each structure is in the `_citation_` lines of its file.

SHA-256:

```
aa71711c65795fd1b3a0bf7c680ad6568fa451d9bf2625745bde15001e230375  MIL-47.cif
9a74630f4dbe8854b4ca4b133f92f22102f52d89cf9c504c2feb39cc75e62bf4  MIL-53Cr-lt.cif
2910f39696cc5c93a39dd4cebdacbcfe1fbea6a9088cd55df10b946f40f8e774  MIL-88A-dry.cif
cd73eef47b05f33f617a036df7c44dc59e34480b7aff6aa0104380b7bd435f7e  MIL-88A-open.cif
6c02e61d0a82f52cc1f93a06f09072d2c780ccaa2645ee54b4baea2c3d8acdbd  MOF5.cif
84923453752f66781295f70de4d8eaba8ecc8510d676ebcfd547ee8d68e23e43  MgMOF-74.cif
4102587072048fdab7a5fbfcb35434c5595b821e0da2ec8a6df155256752936d  ZIF-7.cif
```
