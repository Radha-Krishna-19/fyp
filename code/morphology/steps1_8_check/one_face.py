import sys, os, torch, time, resource; torch.set_num_threads(2); import watch
sys.path.insert(0, sys.argv[1]); import mofwulff as mw
name, cif, out, face = sys.argv[2], sys.argv[3], sys.argv[4], tuple(int(c) for c in sys.argv[5])
eng = mw.Engine(device="cpu")
meta, fams, recs, bulk = mw.run_mof(eng, name, cif, out, faces=[face], symprec=0.1, disorder="majority", max_index=1,
                                    n_families=4, thickness=15.0, vacuum=15.0, max_terms=8, cap="water",
                                    relax_steps=800, fmax=0.05, relax_top_k=1)
for r in recs: print("REC", {k: r.get(k) for k in ("face", "termination", "n_atoms", "gamma_static_J_m2", "gamma_relaxed_J_m2", "steps", "final_fmax", "converged", "relax_seconds")})
print("max RSS GB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
