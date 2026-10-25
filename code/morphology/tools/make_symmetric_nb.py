"""Build the symmetric-slab Colab notebook from MorphoGraph_MOF_colab_4MOFs.ipynb.

Usage: python make_symmetric_nb.py <in.ipynb> <out.ipynb>
Every change to the science code is an exact, asserted string replacement marked
"SYMMETRIC-SLAB CHANGE", so the diff against the original stays readable.
"""
import json
import sys

src_nb, out_nb = sys.argv[1], sys.argv[2]
nb = json.load(open(src_nb, encoding="utf-8"))


def replace_once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{what}: expected 1 match, found {n}")
    return text.replace(old, new)


# ---- science code (cell 4 holds MAIN_SRC as a string literal) ----------------------
ns = {}
exec("".join(nb["cells"][4]["source"]), ns)
main = ns["MAIN_SRC"]

main = replace_once(main,
'''TERMINATION_SHIFT_TOL_FRACTIONAL = SETTINGS["TERMINATION_SHIFT_TOL_FRACTIONAL"]
''',
'''TERMINATION_SHIFT_TOL_FRACTIONAL = SETTINGS["TERMINATION_SHIFT_TOL_FRACTIONAL"]
# SYMMETRIC-SLAB CHANGE: two added settings.
SYMMETRIC_SLABS = bool(SETTINGS.get("SYMMETRIC_SLABS", True))
PAIR_AVERAGE_FALLBACK = bool(SETTINGS.get("PAIR_AVERAGE_FALLBACK", True))
KEEP_LINKERS_INTACT = bool(SETTINGS.get("KEEP_LINKERS_INTACT", True))
# Organic bonds a MOF surface should not cut (A): breaking them leaves loose H, CH, C2H2 or CO2
# pieces in the slab, which the first runs showed in most slabs. Metal-ligand bonds may be cut.
LINKER_BONDS = {("C", "C"): 1.75, ("C", "H"): 1.25, ("C", "O"): 1.6, ("C", "N"): 1.6,
                ("N", "N"): 1.6, ("N", "H"): 1.2, ("O", "H"): 1.2}
''', "settings")

# 0. Do not cut linkers: pymatgen keeps only terminations that break none of LINKER_BONDS.
main = replace_once(main,
'''            if "ftol" in get_params:
                get_kwargs["ftol"] = TERMINATION_SHIFT_TOL_FRACTIONAL
''',
'''            if "ftol" in get_params:
                get_kwargs["ftol"] = TERMINATION_SHIFT_TOL_FRACTIONAL
            # SYMMETRIC-SLAB CHANGE: keep linkers whole if pymatgen supports it and at least one
            # such termination exists; otherwise fall back to unrestricted cutting and say so.
            if KEEP_LINKERS_INTACT and "bonds" in get_params and "max_broken_bonds" in get_params:
                present = {str(e) for e in bulk_final.composition.elements}
                bonds = {k: v for k, v in LINKER_BONDS.items() if set(k) <= present}
                try:
                    trial = generator.get_slabs(**dict(get_kwargs, bonds=bonds, max_broken_bonds=0))
                except Exception as bond_exc:
                    trial = []
                    print(f"  Linker-preserving cut failed: {type(bond_exc).__name__}: {bond_exc}")
                if trial:
                    get_kwargs["bonds"] = bonds
                    get_kwargs["max_broken_bonds"] = 0
                    print(f"  Linker-preserving terminations: {len(trial)} (C-C, C-H, C-O, C-N bonds kept whole)")
                else:
                    print("  No termination keeps every linker whole; unrestricted cutting is used for this facet.")
''', "linker bonds")

# 1. Also generate symmetrized slabs (same termination on both faces).
main = replace_once(main,
'''            generated = generator.get_slabs(**get_kwargs)
            generator_primitive_mode = bool(use_primitive_surface_cell)
''',
'''            generated = list(generator.get_slabs(**get_kwargs))
            slab_modes = ["as_cut"] * len(generated)
            # SYMMETRIC-SLAB CHANGE: also ask pymatgen for symmetrized slabs, whose two faces
            # carry the same termination, so that gamma = pair excess / 2 for that termination.
            if SYMMETRIC_SLABS and "symmetrize" in get_params:
                try:
                    sym_kwargs = dict(get_kwargs)
                    sym_kwargs["symmetrize"] = True
                    sym_generated = list(generator.get_slabs(**sym_kwargs))
                    generated += sym_generated
                    slab_modes += ["symmetrized"] * len(sym_generated)
                    print(f"  Symmetrized termination candidates added: {len(sym_generated)}")
                except Exception as sym_exc:
                    print(f"  Symmetrized slab generation failed: {type(sym_exc).__name__}: {sym_exc}")
            generator_primitive_mode = bool(use_primitive_surface_cell)
''', "slab generation")

main = replace_once(main,
'''            "slab_generator_primitive_surface_cell": generator_primitive_mode,
        }
        try:''',
'''            "slab_generator_primitive_surface_cell": generator_primitive_mode,
            "slab_mode": slab_modes[term_i - 1],  # SYMMETRIC-SLAB CHANGE
        }
        try:''', "slab_mode column")

# 2. A slab that was symmetric before relaxation keeps one shared unknown even if the
#    unconstrained relaxation breaks the symmetry slightly.
main = replace_once(main,
'''            if base["symmetric_after_relaxation"]:
                base["bottom_fingerprint_relaxed"] = base["top_fingerprint_relaxed"]''',
'''            # SYMMETRIC-SLAB CHANGE: a slab built symmetric (verified before relaxation) also
            # keeps one shared unknown; relaxation is unconstrained and can break the symmetry
            # by small amounts. The two cases are recorded separately in the CSV.
            if base["symmetric_after_relaxation"] or base["symmetric_diagnostic"]:
                base["bottom_fingerprint_relaxed"] = base["top_fingerprint_relaxed"]''',
"symmetric unknown")

# 3. Keep the termination energies that are identifiable even when the whole system is not.
main = replace_once(main,
'''    if rank < len(terminations):
        fit_row["fit_status"] = "underdetermined_surface_energies"''',
'''    # SYMMETRIC-SLAB CHANGE: an underdetermined system can still fix some unknowns exactly
    # (for example a termination seen on both faces of a symmetric slab). Column j is
    # identifiable when every null-space vector of A has a zero j-th component.
    if rank < len(terminations):
        _u, _s, _vt = np.linalg.svd(A)
        null_basis = _vt[rank:]
        identifiable = [fp for fp, j in col_index.items() if np.all(np.abs(null_basis[:, j]) < 1e-8)]
        if identifiable:
            solution, _resid, _rank, _singular = np.linalg.lstsq(A, y, rcond=None)
            residuals = A @ solution - y
            rms = float(np.sqrt(np.mean(residuals ** 2)))
            fit_row["fit_rms_eV_A2"] = rms
            fit_row["n_identifiable_terminations"] = len(identifiable)
            if np.isfinite(rms) and rms <= PAIR_FIT_RMS_TOL_EV_A2:
                fit_row["fit_status"] = "fit_partial_identified"
                fit_row["fit_validation"] = "partial_identifiable_subset"
                fit_row["detail"] = (
                    f"Rank {rank} < {len(terminations)} unknowns, but {len(identifiable)} termination energies are "
                    "uniquely fixed (null-space test). Only those are reported; the lowest of them is an upper bound "
                    "on the facet's lowest termination energy."
                )
                for fp in identifiable:
                    gamma_eV_A2 = float(solution[col_index[fp]])
                    positive = bool(np.isfinite(gamma_eV_A2) and gamma_eV_A2 > 0)
                    surface_gamma_rows.append({
                        "h": hkl[0], "k": hkl[1], "l": hkl[2], "miller": fmt_hkl(hkl),
                        "termination_fingerprint": fp, "gamma_eV_A2": gamma_eV_A2,
                        "gamma_J_m2": gamma_eV_A2 * 16.02176634,
                        "positive_gamma": positive, "fit_rank": rank, "fit_unknowns": len(terminations),
                        "fit_rms_eV_A2": rms,
                        "fit_status": "fit_partial_identified" if positive else "fit_partial_nonpositive_gamma",
                        "fit_validation": "partial_identifiable_subset",
                        "n_pair_equations": n_equations,
                        "n_redundant_equations": n_redundant_equations,
                    })
                fit_summary_rows.append(fit_row)
                continue
    if rank < len(terminations):
        fit_row["fit_status"] = "underdetermined_surface_energies"''', "partial fit")

# 4. Section 8: use partially identified facets too.
main = replace_once(main,
'''    if fit_state.empty or fit_state.iloc[-1]["fit_status"] != "fit_ok":
        continue''',
'''    # SYMMETRIC-SLAB CHANGE: partially identified facets are used as well.
    if fit_state.empty or fit_state.iloc[-1]["fit_status"] not in ("fit_ok", "fit_partial_identified"):
        continue
    partial_fit = fit_state.iloc[-1]["fit_status"] == "fit_partial_identified"''', "section 8 gate")

main = replace_once(main,
'''        vals = [gamma_by_fp[fp] for fp in fps if fp in gamma_by_fp]
        if len(vals) != len(fps):
            return None''',
'''        vals = [gamma_by_fp[fp] for fp in fps if fp in gamma_by_fp]
        if not vals or (len(vals) != len(fps) and not partial_fit):  # SYMMETRIC-SLAB CHANGE
            return None''', "partial scenarios")

# 5. Pair-average fallback for facet classes that still have no energy.
main = replace_once(main,
'''direction_gamma_J_m2 = direction_gamma_scenarios["minimum"]
''',
'''direction_gamma_J_m2 = direction_gamma_scenarios["minimum"]

# SYMMETRIC-SLAB CHANGE: record where each directed energy came from, and fill facet classes
# that still have none with half of their lowest pair excess. For any slab,
# min(gamma_top, gamma_bottom) <= (gamma_top + gamma_bottom)/2, so this is an UPPER BOUND on
# the lowest termination energy of that facet, not a fitted value. It assigns the same number
# to (hkl) and (-h-k-l); in a non-centrosymmetric crystal these can differ.
direction_gamma_source = {}
for rep in miller_reps:
    fs = fit_summary_df[(fit_summary_df["h"] == rep[0]) & (fit_summary_df["k"] == rep[1]) & (fit_summary_df["l"] == rep[2])]
    status = fs.iloc[-1]["fit_status"] if len(fs) else "none"
    tag = {"fit_ok": "fitted", "fit_partial_identified": "partial_fit_upper_bound"}.get(status)
    if tag:
        for direction in miller_orbits[rep]:
            if direction in direction_gamma_J_m2:
                direction_gamma_source[direction] = tag
if PAIR_AVERAGE_FALLBACK:
    for rep in miller_reps:
        rep_group = valid_pair_df[
            (pd.to_numeric(valid_pair_df["h"], errors="coerce") == rep[0]) &
            (pd.to_numeric(valid_pair_df["k"], errors="coerce") == rep[1]) &
            (pd.to_numeric(valid_pair_df["l"], errors="coerce") == rep[2])
        ]
        excess = pd.to_numeric(rep_group["pair_excess_eV_A2"], errors="coerce").dropna()
        excess = excess[excess > 0]
        if excess.empty:
            continue
        bound = float(excess.min()) / 2.0 * 16.02176634
        opposite_rep = direction_to_rep.get(tuple(-v for v in rep))
        for orbit_rep in (rep, opposite_rep):
            if orbit_rep is None:
                continue
            for direction in miller_orbits[orbit_rep]:
                if direction_gamma_source.get(direction) == "fitted":
                    continue
                old = direction_gamma_J_m2.get(direction)
                if old is None or bound < old:
                    direction_gamma_J_m2[direction] = bound
                    direction_gamma_source[direction] = "pair_average_upper_bound"
estimated_directions = sorted(d for d, s in direction_gamma_source.items() if s != "fitted")
if estimated_directions:
    print(f"{len(estimated_directions)} directed energies are upper-bound estimates "
          "(partial fit or pair average), not fitted termination energies.")
''', "pair-average fallback")

# 6. Label a shape that contains estimates differently from a fully fitted one.
main = replace_once(main,
'''        item = build_polyhedron(scenario_labels[scenario], gamma_map, working_structure.lattice)
        if scenario == "minimum":''',
'''        _label = scenario_labels[scenario]
        if scenario == "minimum" and estimated_directions:  # SYMMETRIC-SLAB CHANGE
            _label = "CHGNet_upper_bound_estimate_Wulff_PARTLY_PAIR_AVERAGED"
        item = build_polyhedron(_label, gamma_map, working_structure.lattice)
        if scenario == "minimum":''', "label")

main = replace_once(main,
'''            if morphology["label"].startswith("CHGNet_minimum") else''',
'''            if morphology["label"].startswith("CHGNet_minimum") else
            "CHGNet Wulff from upper-bound estimates (partial fits and/or half the lowest pair excess); not fully fitted"
            if morphology["label"].startswith("CHGNet_upper_bound") else''', "method text")

main = replace_once(main,
'''    "valid_signed_direction_energy_count": int(len(direction_gamma_J_m2)),''',
'''    "valid_signed_direction_energy_count": int(len(direction_gamma_J_m2)),
    "direction_energy_source": {fmt_hkl(d): s for d, s in direction_gamma_source.items()},  # SYMMETRIC-SLAB CHANGE
    "direction_gamma_J_m2": {fmt_hkl(d): g for d, g in direction_gamma_J_m2.items()},''', "metadata")

main = replace_once(main,
'''        "A CHGNet Wulff shape is created only when every requested directed facet class has valid positive surface-energy estimates.",''',
'''        "A CHGNet Wulff shape is created only when every requested directed facet class has valid positive surface-energy estimates.",
        "SYMMETRIC-SLAB VERSION: symmetrized slabs are generated in addition to the as-cut slabs; non-stoichiometric ones are still excluded. A slab symmetric before relaxation shares one unknown for both faces.",
        "SYMMETRIC-SLAB VERSION: termination energies fixed by the null-space test are kept from underdetermined systems; facet classes with none fall back to half their lowest pair excess. Both are upper bounds on the facet's lowest termination energy, recorded in direction_energy_source.",''', "method notes")

main = replace_once(main,
'''# 4) Relax stoichiometric slabs, including asymmetric slabs.''',
'''# 4) Relax stoichiometric slabs, including asymmetric slabs.
#    SYMMETRIC-SLAB VERSION: symmetrized slabs are added; see "SYMMETRIC-SLAB CHANGE" comments.''',
"header")

nb["cells"][4]["source"] = [
    "# Science code: original pipeline cell plus the changes marked SYMMETRIC-SLAB CHANGE.\n",
    "MAIN_SRC = " + json.dumps(main, ensure_ascii=False) + "\n",
]

# ---- settings cell -------------------------------------------------------------------
settings = "".join(nb["cells"][2]["source"])
settings = replace_once(settings,
    'MOFS_TO_RUN = ["ZIF-8", "MOF-5", "HKUST-1", "UiO-66"]',
    'MOFS_TO_RUN = ["HKUST-1", "MOF-5", "UiO-66"]', "MOF list")
settings = replace_once(settings,
    '    "TERMINATION_SHIFT_TOL_FRACTIONAL": 0.1,\n',
    '    "TERMINATION_SHIFT_TOL_FRACTIONAL": 0.1,\n'
    '    "SYMMETRIC_SLABS": True,        # added: also build slabs with the same termination on both faces\n'
    '    "PAIR_AVERAGE_FALLBACK": True,  # added: half the lowest pair excess where no gamma is fixed (upper bound)\n'
    '    "KEEP_LINKERS_INTACT": True,    # added: never cut C-C, C-H, C-O, C-N bonds (no loose H/CH/CO2 pieces)\n',
    "new settings")
nb["cells"][2]["source"] = settings.splitlines(keepends=True)

nb["cells"][0]["source"] = [
    "# MorphoGraph-MOF (CHGNet), symmetric-slab version, Colab\n",
    "\n",
    "Same as `MorphoGraph_MOF_colab_4MOFs.ipynb`, with four changes to the science cell, each marked\n",
    "`SYMMETRIC-SLAB CHANGE` in the code:\n",
    "\n",
    "1. A slab that is symmetric as cut (same termination on both faces) counts as ONE termination even if\n",
    "   relaxation breaks its symmetry, so it gives gamma = pair excess / 2 directly. pymatgen's symmetrize\n",
    "   option is also requested; for MOF-5, HKUST-1 and UiO-66 it returns the same slabs as the plain cut\n",
    "   (dry run: code/morphology/slab_options_check.py), and the duplicates are skipped, not relaxed.\n",
    "2. When the pair equations are still underdetermined, the termination energies that they do fix\n",
    "   (null-space test) are kept instead of discarding the whole facet.\n",
    "3. A facet class with no fixed energy falls back to half its lowest pair excess. This is an upper\n",
    "   bound on its lowest termination energy, and the resulting shape is labelled\n",
    "   `CHGNet_upper_bound_estimate_Wulff_PARTLY_PAIR_AVERAGED`. `metadata.json` records the source of\n",
    "   every directed energy (`fitted`, `partial_fit_upper_bound`, `pair_average_upper_bound`).\n",
    "4. Terminations that cut a linker's C-C, C-H, C-O or C-N bonds are skipped when pymatgen can\n",
    "   find any other (`KEEP_LINKERS_INTACT`). The first runs had loose H, CH, C2H2 and CO2 pieces in\n",
    "   most slabs because the cutter sliced through linkers.\n",
    "\n",
    "Slab thickness stays at 15 A (about one to two framework layers); the energies are not\n",
    "thickness-converged. A second run at 30 A on one MOF would test that.\n",
    "\n",
    "What to expect, from the earlier runs: the few symmetric slabs are high-energy terminations (1.4 to 9\n",
    "times the cleavage bound of their face), so most facets will still get the upper-bound estimate.\n",
    "Keeping linkers whole leaves fewer slabs, so the run should be shorter than before.\n",
    "\n",
    "Runs HKUST-1 first, then MOF-5 and UiO-66.\n",
    "Run all cells; each MOF's zip downloads when it finishes.\n",
]

json.dump(nb, open(out_nb, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
compile(main, "<main>", "exec")
print("written", out_nb, "| science code compiles")
