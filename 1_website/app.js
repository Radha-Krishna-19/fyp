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

    // ---------- Sections 2 & 3: limitations + before/after ----------
    // Both are built lazily (each 3D panel costs a WebGL context).
    const allStructures = {};
    Object.keys(window.DEFAULT_CIFS).forEach(function (name) {
      const p = parseDefault(window.DEFAULT_CIFS[name]);
      allStructures[name] = { atoms: p.atoms, cellMatrix: p.cellMatrix };
    });
    MetalOxoDrawbacks.setStructures(allStructures);

    let sectionsReady = false;
    function initLimitationsAndDemo() {
      if (sectionsReady) return;
      sectionsReady = true;
      try {
      MetalOxoDrawbacks.buildSection2(document.getElementById('limitations'));
      MetalOxoDrawbacks.buildSection3({
        before: {
          canvas: document.getElementById('s3-before-canvas'),
          container: document.getElementById('s3-before-wrap'),
          labels: document.getElementById('s3-before-labels'),
          hoverTip: document.getElementById('s3-before-hovertip'),
        },
        after: {
          canvas: document.getElementById('s3-after-canvas'),
          container: document.getElementById('s3-after-wrap'),
          labels: document.getElementById('s3-after-labels'),
          hoverTip: document.getElementById('s3-after-hovertip'),
        },
      }, {
        tabs: document.getElementById('struct-tabs'),
        beforeName: document.getElementById('s3-before-name'),
        afterName: document.getElementById('s3-after-name'),
        beforeStats: document.getElementById('s3-before-stats'),
        afterStats: document.getElementById('s3-after-stats'),
        verdict: document.getElementById('s3-verdict'),
        summary: document.getElementById('s3-summary'),
      });
      } catch (err) {
        // One broken section must never take down the rest of the page.
        const box = document.getElementById('limitations');
        if (box) box.innerHTML = '<div class="verdict">Could not build this section: ' +
          (err && err.message ? err.message : err) + '</div>';
      }
    }

    const limAnchor = document.getElementById('drawbacks');
    if (typeof IntersectionObserver !== 'undefined' && limAnchor) {
      const io = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) { initLimitationsAndDemo(); io.disconnect(); }
      }, { rootMargin: '400px' });
      io.observe(limAnchor);
    } else {
      initLimitationsAndDemo();
    }

    // ---------- Section 3b: lazy-load the embedded pipeline tool ----------
    // The iframe spins up its own WebGL context, so its src is only set once
    // the user scrolls to it. Without this the panel stays blank forever.
    const frame = document.getElementById('pipeline-frame');
    if (frame && frame.dataset.src) {
      const loadFrame = function () { if (!frame.getAttribute('src')) frame.setAttribute('src', frame.dataset.src); };
      if (typeof IntersectionObserver !== 'undefined') {
        const io2 = new IntersectionObserver(function (entries) {
          if (entries.some(function (e) { return e.isIntersecting; })) { loadFrame(); io2.disconnect(); }
        }, { rootMargin: '600px' });
        io2.observe(frame);
      } else {
        loadFrame();
      }
      // also load immediately if the user jumps straight there via the nav
      const navLink = document.querySelector('.top-nav a[href="#pipeline-tool"], .top-nav a[href="#pipeline"]');
      if (navLink) navLink.addEventListener('click', loadFrame);
      // safety net: if it somehow hasn't loaded after 3s on screen, load it
      setTimeout(loadFrame, 3000);
    }

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
