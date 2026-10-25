#!/usr/bin/env python3
"""
update_code_sources.py: regenerates website/code_sources.js from the files on disk.

code_sources.js embeds the source of every file listed in SOURCES below, so the in-page
source browser (code.html and the "view code" links on every page) works from a local copy
with no web server. Every entry is re-read from disk on each run, so the browser never shows
an older version of a file than the repository holds.

Run:   python website/_build/update_code_sources.py
Then:  python website/_build/build_site.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WEBSITE = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(WEBSITE, '..'))
OUT = os.path.join(WEBSITE, 'code_sources.js')

SP = 'code/spectrum_pipeline/'
MO = 'code/morphology/'
SR = 'code/spectrum_shape_relation/'
SS = 'data/spectrum_descriptors/size_scaling/'

# (path from the repository root, tag shown on the card, one-line description)
SOURCES = [
    # ---- first half: the published decomposition pipeline (Python translation) ----
    (SP + 'code_00_pipeline_driver.py', 'Driver', 'Runs the whole published chain end to end for one CIF'),
    (SP + 'code_01_cif_input.py', 'Module 1', 'Read the CIF: cell, symmetry, atoms. No bonds exist yet'),
    (SP + 'code_02_bond_assignment_pbc.py', 'Module 2', 'Infer bonds: 27-image minimum-image search with covalent-radius cutoffs'),
    (SP + 'code_03_element_classification.py', 'Module 3', 'is_metal(): the IUPAC non-metal table'),
    (SP + 'code_04a_metal_oxo_algorithm.py', 'Module 4a', 'The metal-oxo decomposition algorithm used throughout the project'),
    (SP + 'code_04b_single_node_algorithm.py', 'Module 4b', 'Single-node algorithm: walks outward atom by atom'),
    (SP + 'code_04c_all_node_algorithm.py', 'Module 4c', 'All-node algorithm: splits linkers at branch points'),
    (SP + 'code_05_centroid_simplification.py', 'Module 5', 'Collapse each building block to a single point'),
    (SP + 'code_06_systre_topology_export.py', 'Module 6', 'Writes a .cgd file for Systre'),
    (SP + 'code_07a_mofid_assembly.py', 'Module 7a', 'MOFid string assembly'),
    (SP + 'code_07b_mofkey_assembly.py', 'Module 7b', 'MOFkey assembly'),
    # ---- first half: this project's analysis -------------------------------------
    (SP + 'code_09_network_analysis.py', 'OURS', 'Periodic quotient graph, centrality, Laplacian spectrum'),
    (SP + 'code_10_multifractal_spectrum.py', 'OURS', 'Influential-node multifractal spectrum (iNMFA), reference band, candidate test'),
    (SP + 'code_11_nmfa_paper.py', 'OURS', 'NMFA exactly as published: deterministic box growing'),
    (SP + 'code_12_converged_band.py', 'OURS', 'Coarse-grained quotient graph replicated combinatorially; finite-size and q-range convergence sweep'),
    (SP + 'code_13_scaling_regimes.py', 'OURS', 'Tests whether the atomic graph has two scaling regimes (molecular and framework)'),
    (SP + 'code_14_size_strata.py', 'OURS', 'Rebuilds the coarse-grained graph independently; network statistics per Narrow/Medium/Wide class'),
    (SP + 'code_15_dataset_sweeps.py', 'OURS', 'Capped Δα(D) slope sweep on both datasets'),
    (SP + 'code_16_topological_diversity.py', 'OURS', 'Classifies structures by coordination signature; topologically diverse comparison set'),
    (SP + 'code_17_full_correct_band.py', 'OURS', 'The full band on the coarse-grained supercell graph: all 77 hMOF and all 61 CoRE MOF'),
    (SP + 'code_18_subband_explain.py', 'OURS', 'Narrow/Medium/Wide classes compared on nine categories per dataset'),
    (SP + 'code_19_spectrum_vs_shape.py', 'OURS', 'Spectrum width of finite MOF-5 particles cut as cube, slab, plate and rod'),
    (SP + '_ci_smoke_test.py', 'Verify', 'The coordination-number checks run by GitHub Actions on every push'),
    (SP + '_run_size_scaling.py', 'Verify', 'Driver of the finite-size and q-range convergence sweep (fig13)'),
    (SP + '_prove_ordering_equivalence.py', 'Verify', 'Proof that coarse-grain-then-replicate equals replicate-then-coarse-grain'),
    (SP + '_test_window_frac.py', 'Verify', 'Effect of a half-diameter fitting window on the convergence of Δα'),
    (SS + 'make_convergence_figure.py', 'Figure', 'Draws fig13: Δα against ln(diameter) from the convergence sweep'),
    (SS + 'make_slope_figure.py', 'Figure', 'Draws fig14: the Δα(D) slope across both datasets'),
    (SS + 'make_full_band_figure.py', 'Figure', 'Draws fig15 and fig16: the full band and the band against graph size'),
    (SS + 'make_grouped_spectra_figure.py', 'Figure', 'Draws fig17: mean ± 1 sd spectrum envelope per class'),
    # ---- second half: crystal morphology ------------------------------------------
    (MO + 'mofmorph/structure.py', 'OURS', 'Loads a CIF, finds the space group with spglib (with and without H), conventional cell'),
    (MO + 'mofmorph/faces.py', 'OURS', 'Allowed face families, systematic absences, effective spacing d_eff (BFDH input)'),
    (MO + 'mofmorph/shape.py', 'OURS', 'Convex polytope from face distances; areas, volume, sphericity, shape descriptors'),
    (MO + 'mofmorph/models.py', 'OURS', 'Growth-rate models (BFDH, graph rule, Wulff) and the shape names'),
    (MO + 'mofmorph/graphrule.py', 'OURS', 'Attachment numbers of a node on each face of an ideal net'),
    (MO + 'mofmorph/graphfaces.py', 'OURS', 'Phase 3: slices of the real periodic net, attachment and broken-bond energies, F/S/K classes'),
    (MO + 'mofmorph/forcefield.py', 'OURS', 'Phase 4: UFF cleavage energy of every face from the atoms'),
    (MO + 'mofmorph/deform.py', 'OURS', 'Phase 1b: change the cell parameters, recompute allowed faces and symmetry'),
    (MO + 'mofmorph/hybrid.py', 'OURS', 'BFDH × Wulff blend R = R_BFDH^(1−w) · R_Wulff^w'),
    (MO + 'mofmorph/chgnet_post.py', 'OURS', 'CHGNet slab energies to cleavage-energy bounds and Wulff shapes'),
    (MO + 'mofmorph/chgnet_runs.py', 'OURS', 'Access to the CHGNet result folders in data/chgnet_morphograph_runs/'),
    (MO + 'run_phase1.py', 'Run', 'Phase 1: symmetry, allowed faces, BFDH shapes and morph families for four MOFs'),
    (MO + 'run_phase3.py', 'Run', 'Phase 3: graph-face energies and shapes for four MOFs'),
    (MO + 'run_phase4.py', 'Run', 'Phase 4: UFF cleavage energies and Wulff shapes'),
    (MO + 'run_deform.py', 'Run', 'Phase 1b: 52 deformed cells and their BFDH shapes'),
    (MO + 'run_hybrid.py', 'Run', 'Blend shapes at w = 0, 0.25, 0.5, 0.75, 1'),
    (MO + 'run_bond_sensitivity.py', 'Run', 'Wulff shapes when the metal-ligand bond cost is reduced'),
    (MO + 'run_core.py', 'Run', 'BFDH, blend and UFF Wulff shapes for eight CoRE MOF 2019 structures'),
    (MO + 'run_chgnet_cleavage.py', 'Run', 'Cleavage-energy shapes from the CHGNet runs (all slabs and intact slabs)'),
    (MO + 'slab_check.py', 'Verify', 'Detached pieces in every CHGNet slab before and after relaxation'),
    (MO + 'slab_options_check.py', 'Verify', 'Which slab options keep linkers whole (needs pymatgen)'),
    (MO + 'tests.py', 'Verify', 'Phase 1 checks: symmetry, absences, exact shape thresholds'),
    (MO + 'tests_phase3.py', 'Verify', 'Phase 3 checks against textbook nets'),
    (MO + 'tests_phase4.py', 'Verify', 'Phase 4 checks against exact surface energies'),
    (MO + 'tests_deform.py', 'Verify', 'Phase 1b checks: subgroup symmetry and the box criterion'),
    (MO + 'tests_review.py', 'Verify', 'Checks added in the review of 2026-10-14'),
    # ---- the bridge between the halves ----------------------------------------------
    (SR + 'particle_graph_tools.py', 'OURS', 'Finite crystal particles cut from the quotient graph; spectrum width of a particle'),
    (SR + 'run_01_spectrum_of_box_particles_same_cell_count.py', 'Run', 'Δα of MOF-5 cube, slab, plate and rod particles at 64 cells'),
    (SR + 'run_02_spectrum_of_predicted_crystal_shapes_MOF5.py', 'Run', 'Δα of the predicted MOF-5 crystal shapes at equal block count'),
    (SR + 'run_03_core_mof_spectrum_width_vs_bfdh_shape.py', 'Run', 'CoRE MOF: Δα against BFDH aspect ratio with graph size held fixed'),
    (SR + 'run_04_dimension_profile_of_crystal_particles.py', 'Run', 'Mass-radius dimension profile of crystal particles (box-counting idea)'),
    (SR + 'make_figures_spectrum_shape_relation.py', 'Figure', 'Draws the four figures of the spectrum-shape study'),
    (SR + 'check_spectrum_shape_relation.py', 'Verify', 'Checks of the spectrum-shape result files'),
    # ---- the browser engines -----------------------------------------------------------
    ('website/app.js', 'JS', 'Page bootstrap and lazy initialisation'),
    ('website/band_data.js', 'JS', 'Spectra of the hMOF band, exported from notebooks/spectrum/results.json'),
    ('website/band_page.js', 'JS', 'The hMOF band: plotting and hold-out tests'),
    ('website/mof_controls.js', 'JS', 'Standalone pipeline tool: CIF upload'),
    ('website/mof_decompose.js', 'JS', 'Browser engine: CIF parsing, periodic bonding, the three decomposition algorithms'),
    ('website/mof_multifractal.js', 'JS', 'iNMFA (box covering) and NMFA (box growing, as published)'),
    ('website/mof_network.js', 'JS', 'Quotient graph, Jacobi eigensolver, centrality, defect simulation'),
    ('website/mof_render.js', 'JS', 'Three.js renderer with WebGL context-loss recovery'),
    ('website/mof_stages.js', 'JS', 'Standalone pipeline tool: stage stepper'),
    ('website/mof_morphology.js', 'JS', 'Browser morphology engine (independent of the Python package, checked against it)'),
    ('website/mof_deform.js', 'JS', 'Browser engine for deformed orthogonal cells'),
    ('website/network_page.js', 'JS', 'Network and spectrum sections'),
    ('website/overview_page.js', 'JS', 'Overview page: live evidence tables'),
    ('website/pipeline_walkthrough.js', 'JS', 'The 18-step module walkthrough'),
]


def lang_of(path):
    return 'javascript' if path.endswith('.js') else 'python'


def main():
    data, missing = {}, []
    for rel, tag, desc in SOURCES:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        name = os.path.basename(rel)
        if name in data:
            raise SystemExit(f'duplicate file name in the source browser: {name}')
        data[name] = {'src': open(path, encoding='utf-8').read(), 'lang': lang_of(rel),
                      'tag': tag, 'desc': desc, 'path': rel}
    if missing:
        raise SystemExit('missing files: ' + ', '.join(missing))
    header = ('// code_sources.js: every source file shown in the in-page code browser, embedded so the\n'
              '// browser works without a web server. Generated by website/_build/update_code_sources.py.\n'
              'window.CODE_SOURCES = ')
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(header + json.dumps(data, indent=0, ensure_ascii=False) + ';\n')
    print(f'wrote {OUT}: {len(data)} files')


if __name__ == '__main__':
    main()
