// app.js
// Bootstraps index.html: wires the Module 4a code+3D walkthrough, the two
// limitations/fix demos, and the CIF-swap control for the walkthrough.
// Depends on (loaded before this file, in order): mof_decompose.js,
// mof_render.js, pipeline_walkthrough.js, band_page.js,
// default_cif_data.js.

(function () {
  'use strict';

  function parseDefault(text) {
    const parsed = MOFDecompose.parseCIF(text);
    parsed.atoms.cellPar = parsed.cellPar;
    return parsed;
  }

  document.addEventListener('DOMContentLoaded', function () {
    // ---------- Section 1: full pipeline (all modules) walkthrough ----------
    PipelineWalkthrough.init(
      document.getElementById('w-canvas'),
      document.getElementById('w-canvas-wrap'),
      document.getElementById('w-labels'),
      document.getElementById('w-hovertip')
    );
    PipelineWalkthrough.buildUI(document.getElementById('w-panel'));

    const hkust = parseDefault(window.DEFAULT_CIFS['HKUST-1']);

    // current structure + engine mode for Section 1
    let curAtoms = hkust.atoms, curCell = hkust.cellMatrix, curLabel = 'HKUST-1 (Cu-BTC)', curDefault = true;
    function renderWalkthrough() {
      PipelineWalkthrough.setSource(curAtoms, curCell, curDefault, curLabel);
    }
    renderWalkthrough();


    // ---------- Section 1 CIF swap (walkthrough only) ----------
    const wFileInput = document.getElementById('w-cif-file');
    const wResetBtn = document.getElementById('w-cif-reset');
    const wStatus = document.getElementById('w-cif-status');
    wFileInput.addEventListener('change', function () {
      const file = wFileInput.files && wFileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function () {
        try {
          const parsed = MOFDecompose.parseCIF(reader.result);
          parsed.atoms.cellPar = parsed.cellPar;
          curAtoms = parsed.atoms; curCell = parsed.cellMatrix;
          curLabel = file.name.replace(/\.cif$/i, ''); curDefault = false;
          renderWalkthrough();
          wStatus.textContent = 'Now walking through ' + file.name + ' (' + parsed.atoms.length + ' atoms).';
          wStatus.className = 'cif-status ok';
        } catch (err) {
          wStatus.textContent = 'Could not parse ' + file.name + ': ' + err.message;
          wStatus.className = 'cif-status err';
        }
      };
      reader.readAsText(file);
      wFileInput.value = '';
    });
    wResetBtn.addEventListener('click', function () {
      curAtoms = hkust.atoms; curCell = hkust.cellMatrix;
      curLabel = 'HKUST-1 (Cu-BTC)'; curDefault = true;
      renderWalkthrough();
      wStatus.textContent = '';
      wStatus.className = 'cif-status';
    });

    // ---------- Sections 2 & 3 (removed) ----------
    // These built the "limitations and proposed fixes" demonstration, driven
    // by metal_oxo_drawbacks.js. That strand of work was withdrawn from the
    // project: we visualise the published metal-oxo decomposition as
    // published and do not modify it, so a before/after comparison would be
    // showing a change we no longer make. The module and its markup were
    // deleted; this block goes with them.

    // The embedded pipeline iframe was removed. It duplicated the walkthrough
    // directly above it -- same CIF upload, same 3D view, same stages -- while
    // costing a second WebGL context on a page that already has one. Browsers
    // cap live contexts per tab, so the duplicate was actively harmful.


    // ---------- section nav smooth scroll ----------
    document.querySelectorAll('.top-nav a').forEach(a => {
      a.addEventListener('click', e => {
        const id = a.getAttribute('href').slice(1);
        const el = document.getElementById(id);
        if (el) { e.preventDefault(); el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      });
    });
  });
})();
