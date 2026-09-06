// mof_stages.js
// Defines the 7 pipeline stages and wires the stage-switcher UI to
// MOFRender.load(). Depends on: mof_decompose.js (for the variant data
// shape) and mof_render.js (for the actual 3D drawing) both being loaded
// first. mof_controls.js supplies the "current multi-variant DATA" (either
// the embedded default HKUST-1 example, or a freshly uploaded CIF) via
// window.MOFStages.setSource(multiVariantData, label).

(function (root) {
  'use strict';

  const STAGES = [
    {
      id: 'm1', label: '1 · CIF Input', variant: 'singleNode',
      colorMode: 'element', showBonds: false, netOnly: false,
      title: 'Module 1 — CIF File Input',
      blurb: 'Just the raw atomic positions from the .cif, expanded to the full unit cell. No bonds exist yet — a CIF never stores connectivity, only fractional coordinates, elements, and the cell/symmetry needed to build the periodic lattice.',
      codeFiles: ['code_01_cif_input.py'],
    },
    {
      id: 'm2', label: '2 · Bond Assignment', variant: 'singleNode',
      colorMode: 'element', showBonds: true, netOnly: false,
      title: 'Module 2 — Bond Assignment',
      blurb: 'Every bond you now see was computed, not read from the file: a periodic-boundary-aware covalent-radius cutoff test between every pair of atoms (searching all 27 neighbouring unit-cell images to find the true minimum-image distance).',
      codeFiles: ['code_02_bond_assignment_pbc.py'],
    },
    {
      id: 'm3', label: '3 · Element Classification', variant: 'singleNode',
      colorMode: 'metalNonmetal', showBonds: true, netOnly: false,
      title: 'Module 3 — Element Classification',
      blurb: 'Every atom is now labelled strictly METAL (red) or NONMETAL (blue) via the IUPAC InChI lookup table — a binary split with no metalloid middle ground. This labelled graph is the shared input every decomposition algorithm below reads from.',
      codeFiles: ['code_03_element_classification.py'],
    },
    {
      id: 'm4a', label: '4a · Metal-Oxo Split', variant: 'metalOxo',
      colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, netOnly: false,
      title: 'Module 4a — Metal-Oxo Algorithm (this project’s main subject)',
      blurb: 'Node atoms (red) = metal atoms + only PURE oxo/hydroxo/aqua bridging oxygens. Carboxylate oxygens are bonded to carbon, so the whole –COO– group is excluded and stays linker (blue) — notice the metal node markers below are now tiny (often just the bare metal atoms) compared to the other two algorithms.',
      codeFiles: ['code_04a_metal_oxo_algorithm.py'],
    },
    {
      id: 'm4b', label: '4b · Single-Node Split', variant: 'singleNode',
      colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, netOnly: false,
      title: 'Module 4b — Single Node Algorithm',
      blurb: 'This time coordinated carboxylate groups are FOLDED INTO the node (red) — the node cluster is chemically larger and more complete, while the linker (blue) shrinks down to just its rigid aromatic/aliphatic core.',
      codeFiles: ['code_04b_single_node_algorithm.py'],
    },
    {
      id: 'm4c', label: '4c · All-Node Split', variant: 'allNode',
      colorMode: 'block', blockColorStyle: 'palette', showBonds: true, netOnly: false,
      title: 'Module 4c — All Node Algorithm',
      blurb: 'Starts from the single-node split, then further divides any linker with an internal branch point (a heavy atom bonded to 3+ other heavy atoms within the linker) into separate branch-point and branch sub-blocks — each gets its own color below. For linkers with no true branch point (like BTC or BDC), this looks identical to 4b, which matches real literature: all-node only diverges from single-node for linkers like biphenyl-tetracarboxylate.',
      codeFiles: ['code_04c_all_node_algorithm.py'],
    },
    {
      id: 'm5', label: '5–6 · Simplified Net', variant: 'singleNode',
      colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, netOnly: true,
      title: 'Modules 5 & 6 — Centroid Simplification + Systre Topology',
      blurb: 'Every building block has now collapsed to a single point at its centroid, connected by straight edges — this abstract periodic graph (built on the single-node partition) is exactly what gets exported to a .cgd file and handed to the external Systre program for topological identification.',
      codeFiles: ['code_05_centroid_simplification.py', 'code_06_systre_topology_export.py', 'code_07a_mofid_assembly.py', 'code_07b_mofkey_assembly.py'],
    },
  ];

  let currentSource = null;   // {label, formula, metalOxo, singleNode, allNode}
  let currentIndex = 0;
  let els = {};

  function dataForStage(stage) {
    return currentSource[stage.variant];
  }

  function renderPanel(stage) {
    els.title.textContent = stage.title;
    els.blurb.textContent = stage.blurb;
    els.codeRefs.innerHTML = stage.codeFiles.map(f => '<span class="code-chip">' + f + '</span>').join(' ');

    if (stage.id === 'm5') {
      const D = dataForStage(stage);
      const nBlocks = D.n_metal_blocks + D.n_linker_blocks;
      let extra = '<div class="stage-extra"><b>' + nBlocks + '</b> vertices in the simplified net (' +
        D.n_metal_blocks + ' node + ' + D.n_linker_blocks + ' linker).</div>';
      if (currentSource.isDefault) {
        extra += '<div class="stage-extra">Known literature values for HKUST-1 (Cu-BTC) — <i>not recomputed live; Systre itself is an external Java tool, not run in-browser</i>:' +
          '<div class="example-strip">Topology (RCSR): <b>tbo</b></div>' +
          '<div class="example-strip">MOFid: [Cu][Cu].[O-]C(=O)c1cc(cc(c1)C(=O)[O-])C(=O)[O-]&nbsp;&nbsp;MOFid-v1.tbo.cat0;Cu-BTC</div>' +
          '<div class="example-strip">MOFkey: Cu.QMKYBPDZANOJGF.MOFkey-v1.tbo</div></div>';
      } else {
        extra += '<div class="stage-extra">Topology assignment (Module 6) requires the external Systre tool and RCSR lookup — not computed in-browser for uploaded structures. The simplified net shown above is exactly what would be exported to a .cgd file and handed to it.</div>';
      }
      els.extra.innerHTML = extra;
      els.extra.style.display = 'block';
    } else {
      els.extra.style.display = 'none';
      els.extra.innerHTML = '';
    }

    els.stepper.querySelectorAll('.stage-btn').forEach((b, i) => {
      b.classList.toggle('active', i === currentIndex);
    });
    els.prevBtn.disabled = currentIndex === 0;
    els.nextBtn.disabled = currentIndex === STAGES.length - 1;
    els.formula.textContent = currentSource.formula + '  ·  ' + currentSource.n_atoms + ' atoms';
  }

  function showStage(index) {
    currentIndex = Math.max(0, Math.min(STAGES.length - 1, index));
    const stage = STAGES[currentIndex];
    const DATA = dataForStage(stage);
    MOFRender.load(DATA, {
      colorMode: stage.colorMode,
      blockColorStyle: stage.blockColorStyle || 'nodeLinker',
      showBonds: stage.showBonds,
      showCell: true,
      netOnly: !!stage.netOnly,
    });
    renderPanel(stage);
  }

  function setSource(multiVariantData, label, isDefault) {
    currentSource = Object.assign({ label: label || 'Uploaded structure', isDefault: !!isDefault }, multiVariantData);
    showStage(currentIndex);
  }

  function buildUI(container) {
    container.innerHTML =
      '<div id="stage-stepper" class="stage-stepper"></div>' +
      '<div class="stage-nav"><button id="stage-prev">&larr; Previous</button><span id="stage-formula" class="stage-formula"></span><button id="stage-next">Next &rarr;</button></div>' +
      '<div class="stage-panel">' +
        '<h3 id="stage-title"></h3>' +
        '<div id="stage-code-refs" class="code-refs"></div>' +
        '<p id="stage-blurb"></p>' +
        '<div id="stage-extra"></div>' +
      '</div>';

    els.stepper = container.querySelector('#stage-stepper');
    els.prevBtn = container.querySelector('#stage-prev');
    els.nextBtn = container.querySelector('#stage-next');
    els.formula = container.querySelector('#stage-formula');
    els.title = container.querySelector('#stage-title');
    els.blurb = container.querySelector('#stage-blurb');
    els.codeRefs = container.querySelector('#stage-code-refs');
    els.extra = container.querySelector('#stage-extra');

    STAGES.forEach((s, i) => {
      const b = document.createElement('button');
      b.className = 'stage-btn';
      b.textContent = s.label;
      b.addEventListener('click', () => showStage(i));
      els.stepper.appendChild(b);
    });
    els.prevBtn.addEventListener('click', () => showStage(currentIndex - 1));
    els.nextBtn.addEventListener('click', () => showStage(currentIndex + 1));
  }

  root.MOFStages = { STAGES, buildUI, setSource, showStage, getCurrentIndex: () => currentIndex };
})(typeof window !== 'undefined' ? window : globalThis);
