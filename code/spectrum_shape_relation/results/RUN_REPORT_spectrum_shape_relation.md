# Run report: spectrum <-> crystal shape

run at 2026-10-16 05:46 on Linux-6.6.122+-x86_64-with-glibc2.39, Python 3.13.16, RECOMPUTE=True

spectrum settings: {'top': 0.2, 'window': 0.5, 'trials': 20, 'seeds': (0, 1, 2, 3, 4)}
size trend on cubes: width = -1.139 + 0.753 ln D
shape        blocks    D          width  trend at D difference
cube 4x4x4     2048   44    1.722 +- 0.003       1.708     +0.014
plate 8x8x1    2048   64    1.591 +- 0.006       1.990     -0.399
rod 16x2x2     2048   76    1.410 +- 0.008       2.120     -0.710
slab 8x4x2     2048   52    1.626 +- 0.009       1.834     -0.208
check against code_19: {'same_graphs': True, 'largest_width_difference': 0.0}
ZIF-8 (NOT used): connected pieces per cube = [34, 67, 112, 169, 238]
cube trend: width = -1.228 + 0.764 ln D   and   width = -0.481 + 0.279 ln N
target shape                                          N   D          width  vs trend (same N)  vs trend (same D)
  2000 cube {100} (reference)                      2176  44    1.673 +- 0.003             +0.008             +0.012
  2000 octahedron {111} (reference)                1988  28    1.638 +- 0.005             -0.001             +0.322
  2000 rhombic dodecahedron {110} (reference)      2166  36    1.687 +- 0.006             +0.023             +0.178
  2000 BFDH prediction                             2086  30    1.670 +- 0.002             +0.018             +0.301
  2000 BFDH x Wulff blend w=0.5                    2072  36    1.701 +- 0.006             +0.050             +0.193
  2000 UFF Wulff prediction                        2176  44    1.673 +- 0.003             +0.008             +0.012
  2000 CHGNet cleavage Wulff prediction            2020  28    1.606 +- 0.003             -0.038             +0.290
  4000 cube {100} (reference)                      4000  55    1.838 +- 0.009             +0.004             +0.006
  4000 octahedron {111} (reference)                4266  36    1.811 +- 0.002             -0.041             +0.303
  4000 rhombic dodecahedron {110} (reference)      4186  46    1.803 +- 0.004             -0.044             +0.108
  4000 BFDH prediction                             4068  38    1.861 +- 0.004             +0.022             +0.312
  4000 BFDH x Wulff blend w=0.5                    4028  46    1.857 +- 0.005             +0.020             +0.161
  4000 UFF Wulff prediction                        4000  55    1.838 +- 0.009             +0.004             +0.006
  4000 CHGNet cleavage Wulff prediction            4074  36    1.832 +- 0.001             -0.007             +0.324
structures with a spectrum and a BFDH shape: 55

[all usable]
  width vs sphericity          n=55  raw rho -0.384 (p 0.0045)   size held fixed rho +0.003 (p 0.981, 95% CI -0.32 to +0.34)
  width vs aspect ratio        n=55  raw rho +0.504 (p 0.0003)   size held fixed rho +0.001 (p 0.993, 95% CI -0.32 to +0.34)
  width vs cell length ratio   n=55  raw rho +0.623 (p 0.0001)   size held fixed rho +0.095 (p 0.493, 95% CI -0.15 to +0.35)
  sphericity vs ln(node count) n=55  rho -0.479
  width vs ln(node count)      n=55  rho +0.805

[one connected piece only]
  width vs sphericity          n=52  raw rho -0.419 (p 0.0027)   size held fixed rho -0.072 (p 0.620, 95% CI -0.42 to +0.31)
  width vs aspect ratio        n=52  raw rho +0.567 (p 0.0001)   size held fixed rho +0.132 (p 0.356, 95% CI -0.19 to +0.43)
  width vs cell length ratio   n=52  raw rho +0.638 (p 0.0001)   size held fixed rho +0.122 (p 0.399, 95% CI -0.15 to +0.39)
  sphericity vs ln(node count) n=52  rho -0.465
  width vs ln(node count)      n=52  rho +0.825
PASS  cube {100}: 6 faces, 27 lattice points with |x|,|y|,|z| <= 1
PASS  octahedron {111}: 8 faces, 7 points with |x|+|y|+|z| <= 1
PASS  rhombic dodecahedron {110}: 12 faces
PASS  size-trend fit recovers a known slope
PASS  our Spearman equals scipy.stats.spearmanr
PASS  run_01 builds the same box graphs as code_19 (nodes and diameters)
PASS  run_01 and code_19 give identical widths
PASS  every MOF-5 box particle is one connected piece
PASS  cube width exceeds slab, plate and rod by more than 5x the seed spread
PASS  every predicted-shape particle is within 15% of its target size (worst 8.8%)
PASS  every predicted-shape spectrum passed on all seeds
PASS  the cube trend in block count fits within 0.06
PASS  every "difference at equal blocks" recomputes from the saved trend
PASS  a BFDH shape was found for every usable CoRE structure (55/55)
PASS  saved rho(width, aspect ratio) recomputes with scipy

All checks passed.

