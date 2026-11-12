"""
figure_sources.py: the producing script and the input data of every image on the website.

build_site.py adds a "Source" line under every <figure> that shows one of these images and has
no source line yet, so each figure says how it was obtained. tests/test_pages.js fails if any
image on the site is missing from this table.

Paths are from the repository root.
"""
MP = 'code/morphology/'
SS = 'data/spectrum_descriptors/size_scaling/'
RF = 'docs/report_figures/'
PR = 'docs/reports/morphology_primer_source/'
NB = 'notebooks/spectrum/'
SR = 'code/spectrum_shape_relation/'

FIGURE_SOURCES = {
    # ---- first half: spectrum of the MOF graph ----------------------------------------------
    'figures/fig01_mof_concept.png': ('Schematic drawn in Matplotlib; the drawing script was not kept', None),
    'figures/fig02_pipeline.png': ('Schematic drawn in Matplotlib; the drawing script was not kept', None),
    'figures/fig03_periodic_vs_naive.png': (RF + 'make_figures.py', 'the four demonstration CIFs, through code/spectrum_pipeline/code_09_network_analysis.py'),
    'figures/fig04_degeneracy.png': (RF + 'make_figures.py', 'the four demonstration CIFs (degree distributions)'),
    'figures/fig05_defect.png': ('Drawn in Matplotlib by a script that was not kept; the same numbers are recomputed live on the Network page', 'website/HKUST-1.cif'),
    'figures/fig06_boxgrowing.png': ('Drawn in Matplotlib by a script that was not kept; the same curves are recomputed live on the Network page', 'website/HKUST-1.cif'),
    'figures/fig07_tau_fix.png': (RF + 'make_figures.py', NB + 'results.json'),
    'figures/fig08_band77.png': (NB + 'mof_band_analysis.ipynb, step 11', NB + 'results.json (77 hMOF, atomic graph)'),
    'figures/fig09_real_vs_hmof.png': (RF + 'make_real_band_figures.py', NB + 'real_results.json and ' + NB + 'results.json'),
    'figures/fig10_real_band61.png': (NB + 'real_mof_band.ipynb, step 11', NB + 'real_results.json (61 CoRE MOF, atomic graph)'),
    'figures/fig11_real_spectra61.png': (NB + 'real_mof_band.ipynb, step 9', NB + 'real_results.json'),
    'figures/fig12_size_strata.png': ('code/spectrum_pipeline/_make_strata_figure.py', SS + 'size_strata.json and data/spectrum_descriptors/independent_cg_run/independent_cg_run_76_hmof.csv'),
    'figures/fig13_convergence.png': (SS + 'make_convergence_figure.py', SS + 'convergence_sweep.json (code/spectrum_pipeline/_run_size_scaling.py)'),
    'figures/fig14_slope_sweep.png': (SS + 'make_slope_figure.py', SS + 'slope_sweep_hmof.json and slope_sweep_core.json (code_15_dataset_sweeps.py)'),
    'figures/fig15_full_band.png': (SS + 'make_full_band_figure.py', SS + 'full_band_hmof_cg.json and full_band_core_cg.json (code_17_full_correct_band.py)'),
    'figures/fig16_full_band_vs_size.png': (SS + 'make_full_band_figure.py', SS + 'full_band_hmof_cg.json and full_band_core_cg.json'),
    'figures/fig17_grouped_spectra.png': (SS + 'make_grouped_spectra_figure.py', SS + 'subband_explain_hmof.json and subband_explain_core.json (code_18_subband_explain.py)'),
    'figures/fig17b_xenon_core_raw_reference.png': ('An independent coarse-grained run outside this repository; shown for comparison only', 'CoRE MOF 2019, xenon-tested records'),
    'figures/fig17c_xenon_core_bands_reference.png': ('An independent coarse-grained run outside this repository; shown for comparison only', 'CoRE MOF 2019, xenon-tested records'),
    'figures/spectrum_vs_shape.png': (SS + 'make_spectrum_vs_shape_figure.py', SS + 'spectrum_vs_shape_MOF5.json (code/spectrum_pipeline/code_19_spectrum_vs_shape.py)'),
    # ---- teaching figures (morphology primer and Learn 2) -----------------------------------
    'figures/learn/levels.png': (PR + 'figs2.py', None),
    'figures/learn/lattice2d.png': (PR + 'figs2.py', None),
    'figures/learn/miller.png': (PR + 'figs2.py', None),
    'figures/learn/dspacing.png': (PR + 'figs2.py', None),
    'figures/learn/absences.png': (PR + 'figs2.py', None),
    'figures/learn/growth.png': (PR + 'figs2.py', None),
    'figures/learn/wulff2d.png': (PR + 'figs2.py', None),
    'figures/learn/fsk.png': (PR + 'figs2.py', None),
    'figures/learn/quotient.png': (PR + 'figs2.py', None),
    'figures/learn/morph_path.png': (PR + 'figs1.py', None),
    'figures/learn/rod_plate.png': (PR + 'figs1.py', None),
    'figures/learn/bfdh_FI.png': (PR + 'figs1.py', None),
    'figures/learn/mofs.png': (PR + 'figs3.py', 'the four demonstration CIFs in code/spectrum_pipeline/'),
    'figures/learn/prototypes.png': (PR + 'figs3.py', None),
    'figures/learn/pipeline.png': (PR + 'figs3.py', None),
    'figures/learn/cut_terminations.png': ('website/_build/make_learn_energy_figures.py', None),
    'figures/learn/torus_vs_particle.png': ('website/_build/make_learn_energy_figures.py', None),
    'figures/learn/confound_example.png': ('website/_build/make_learn_energy_figures.py', SR + 'results/03_core_mof_spectrum_vs_bfdh_shape.json'),
    # ---- second half: morphology ---------------------------------------------------------------
    'figures/morph/MOF-5_morph.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/ZIF-8_morph.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/UiO-66_tetrahedral.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/UiO-66_growth_in_time.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/MOF-5_graphrule.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/UiO-66_graphrule.png': (MP + 'run_phase1.py', MP + 'results/phase1_results.json'),
    'figures/morph/attach.png': (PR + 'figs4.py', PR + 'fig/attach.json'),
    'figures/morph/phase3_slices.png': (MP + 'figs_phase3.py', MP + 'results/phase3_results.json'),
    'figures/morph/phase3_shapes.png': (MP + 'figs_phase3.py', MP + 'results/phase3_results.json'),
    'figures/morph/phase4_compare.png': (MP + 'figs_phase4.py', MP + 'results/phase4_results.json and phase3_results.json'),
    'figures/morph/MOF-5_phase4.png': (MP + 'run_phase4.py', MP + 'results/phase4_results.json'),
    'figures/morph/HKUST-1_phase4.png': (MP + 'run_phase4.py', MP + 'results/phase4_results.json'),
    'figures/morph/UiO-66_phase4.png': (MP + 'run_phase4.py', MP + 'results/phase4_results.json'),
    'figures/morph/ZIF-8_phase4.png': (MP + 'run_phase4.py', MP + 'results/phase4_results.json'),
    'figures/morph/MOF-5_deform_c.png': (MP + 'run_deform.py', MP + 'results/deform_results.json'),
    'figures/morph/ZIF-8_deform_c.png': (MP + 'run_deform.py', MP + 'results/deform_results.json'),
    'figures/morph/MOF-5_deform_gamma.png': (MP + 'run_deform.py', MP + 'results/deform_results.json'),
    'figures/morph/UiO-66_deform_gamma.png': (MP + 'run_deform.py', MP + 'results/deform_results.json'),
    'figures/morph/deform_curves.png': (MP + 'figs_deform.py', MP + 'results/deform_results.json'),
    'figures/morph/methods_vs_experiment.png': (MP + 'figs_experiment.py', MP + 'results/ (phase 1, 3, 4, bond sensitivity, CHGNet) and data/experimental_morphology/compare/comparison.csv'),
    'figures/morph/core_shapes.png': (MP + 'run_core.py', MP + 'results/core_results.json'),
    # ---- the bridge between the halves -----------------------------------------------------------
    'figures/relation/01_box_particles_MOF5.png': (SR + 'make_figures_spectrum_shape_relation.py', SR + 'results/01_box_particles_MOF5.json (run_01)'),
    'figures/relation/02_predicted_crystal_shapes_MOF5.png': (SR + 'make_figures_spectrum_shape_relation.py', SR + 'results/02_predicted_crystal_shapes_MOF5.json (run_02)'),
    'figures/relation/03_core_mof_spectrum_vs_bfdh_shape.png': (SR + 'make_figures_spectrum_shape_relation.py', SR + 'results/03_core_mof_spectrum_vs_bfdh_shape.json (run_03)'),
    'figures/relation/04_dimension_profile_MOF5.png': (SR + 'make_figures_spectrum_shape_relation.py', SR + 'results/04_dimension_profile_MOF5.json (run_04)'),
    # ---- morphology map (10 November) -----------------------------------------------------------
    'figures/map/fig_map_regions.png': (MP + 'morphology_map/figures.py', MP + 'morphology_map/phase_grid.npz (phase_grid.py)'),
    'figures/map/fig_map_models.png': (MP + 'morphology_map/figures.py', MP + 'morphology_map/model_points.json (model_points.py)'),
    'figures/map/fig_conditions.png': (MP + 'morphology_map/figures.py', MP + 'morphology_map/series_results.json and dimension_along_map.json'),
}

GITHUB = 'https://github.com/Radha-Krishna-19/fyp/blob/main/'


def source_line(src):
    """HTML for the Source line of one image."""
    script, data = FIGURE_SOURCES[src]
    def link(path_text):
        first = path_text.split(',')[0].split(' (')[0].strip()
        if '/' in first and not first.startswith(('An ', 'Drawn', 'Schematic')):
            return f'<a href="{GITHUB}{first}"><code>{first}</code></a>' + path_text[len(first):]
        return path_text
    out = f'<b>Source:</b> {link(script)}'
    if data:
        out += f'; data: {link(data)}'
    return f'<p class="provenance">{out}.</p>'
