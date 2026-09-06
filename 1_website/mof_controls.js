// mof_controls.js
// Wires the "upload a .cif" / "reset to default" UI to mof_decompose.js's
// buildAllVariants() and mof_stages.js's setSource(). Depends on
// mof_decompose.js and mof_stages.js both being loaded first.

(function (root) {
  'use strict';

  function init(fileInputEl, resetBtnEl, statusEl, defaultMultiVariantData) {
    fileInputEl.addEventListener('change', () => {
      const file = fileInputEl.files && fileInputEl.files[0];
      if (!file) return;
      statusEl.textContent = 'Parsing ' + file.name + ' …';
      statusEl.className = 'cif-status';
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = MOFDecompose.parseCIF(reader.result);
          const V = MOFDecompose.buildAllVariants(parsed.atoms, parsed.cellMatrix);
          const name = file.name.replace(/\.cif$/i, '');
          MOFStages.setSource(V, name, false);
          statusEl.textContent = 'Loaded ' + file.name + ': ' + V.n_atoms + ' atoms (' + V.formula + '). Walk through the stages above to see how this structure gets decomposed.';
          statusEl.className = 'cif-status ok';
        } catch (err) {
          statusEl.textContent = 'Could not parse ' + file.name + ': ' + err.message;
          statusEl.className = 'cif-status err';
        }
      };
      reader.onerror = () => {
        statusEl.textContent = 'Failed to read ' + file.name + '.';
        statusEl.className = 'cif-status err';
      };
      reader.readAsText(file);
      fileInputEl.value = '';
    });

    resetBtnEl.addEventListener('click', () => {
      MOFStages.setSource(defaultMultiVariantData, 'HKUST-1 · Cu₃(BTC)₂', true);
      statusEl.textContent = '';
      statusEl.className = 'cif-status';
      fileInputEl.value = '';
    });
  }

  root.MOFControls = { init };
})(typeof window !== 'undefined' ? window : globalThis);
