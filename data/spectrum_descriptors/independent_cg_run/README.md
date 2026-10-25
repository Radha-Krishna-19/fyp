# Independent coarse-grained run (76 hMOF structures)

`independent_cg_run_76_hmof.csv`: per-structure Δα and Narrow/Medium/Wide class from an independent
coarse-grained run (top 20 % influential blocks, radii up to half the diameter; class thresholds at
the 25th and 75th percentiles: Narrow ≤ 1.190 < Medium ≤ 1.222 < Wide). These are the numbers reported
in the [team paper](../../../docs/paper/G070_Paper.pdf): Δα from 1.032 to 1.582, interquartile band
1.190–1.222.

The column `class_printed_edges` keeps the labels printed by that run (19 Narrow, 36 Medium, 21 Wide).
The paper's Table II gives 19 / 38 / 19. The difference is confined to the Medium/Wide boundary: three
structures have Δα = 1.222 to three decimals, and the run's labels and the paper's exact percentiles
assign them differently. No conclusion depends on it, because the Medium class is narrower (0.032)
than the per-structure error bars (0.013–0.098) and the classes are withdrawn. The analysis that shows the classes follow
graph size is [`code/spectrum_pipeline/code_14_size_strata.py`](../../../code/spectrum_pipeline/code_14_size_strata.py).
