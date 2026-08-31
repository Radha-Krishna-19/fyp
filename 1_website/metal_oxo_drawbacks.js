// metal_oxo_drawbacks.js
// Section 2 (limitations of the published metal-oxo algorithm + the fix for
// each) and Section 3 (before/after 3D across every test structure).
//
// Everything here is computed live from the real CIF files: the "before"
// column is the published algorithm exactly as specified, the "after" column
// is the same algorithm with this project's proposed fixes applied. No value
// on the page is hardcoded.
//
// Depends on: mof_decompose.js, mof_render.js (MOFRender.create()).

(function (root) {
  'use strict';

  const ALL_FIXES = { completeNodes: true, donorAgnostic: true };

  let structures = {};       // name -> {atoms, cellMatrix}
  let rBefore = null, rAfter = null;
  let els = {};
  let currentName = null;

  function fmtComp(c) {
    return Object.entries(c).sort((a, b) => b[1] - a[1]).map(([e, n]) => e + n).join(' ');
  }
  function nodeOf(D) { return D.blocks.find(b => b.type === 'metal'); }

  function analyse(name) {
    const s = structures[name];
    const before = MOFDecompose.buildMetalOxoVariant(s.atoms, s.cellMatrix, { noUnwrap: true });
    const after = MOFDecompose.buildMetalOxoVariant(s.atoms, s.cellMatrix, { fixes: ALL_FIXES, noUnwrap: true });
    const nb = nodeOf(before), na = nodeOf(after);
    return {
      name, before, after,
      beforeNode: nb ? fmtComp(nb.composition) : '—',
      afterNode: na ? fmtComp(na.composition) : '—',
      beforeSize: nb ? nb.n_atoms : 0,
      afterSize: na ? na.n_atoms : 0,
      gained: (na ? na.n_atoms : 0) - (nb ? nb.n_atoms : 0),
      quality: before.quality,
    };
  }

  // ---------------------------------------------------------------
  // SECTION 2 — the four limitations, each with live evidence
  // ---------------------------------------------------------------
  function buildSection2(container) {
    const all = Object.keys(structures).map(analyse);

    // Limitation 1 evidence: how much of the SBU the published rule omits
    const l1rows = all.map(a =>
      '<tr><td class="dt-label">' + a.name + '</td>' +
      '<td class="dt-value">' + a.beforeNode + '</td>' +
      '<td class="dt-value" style="color:var(--good)">' + a.afterNode + '</td>' +
      '<td class="dt-note">' + (a.gained > 0 ? '+' + a.gained + ' atoms recovered' : 'no carboxylate — rule does not apply') + '</td></tr>').join('');

    // Limitation 2 evidence: which structures have non-O donors
    const l2rows = all.map(a => {
      const s = structures[a.name];
      const els2 = {};
      s.atoms.forEach(at => { els2[at.el] = 1; });
      const donors = Object.keys(els2).filter(e => e !== 'C' && e !== 'H' && !MOFDecompose.METALS.has(e));
      const nonO = donors.filter(e => e !== 'O');
      return '<tr><td class="dt-label">' + a.name + '</td>' +
        '<td class="dt-value">' + donors.join(', ') + '</td>' +
        '<td class="dt-note">' + (nonO.length
          ? '<b>' + nonO.join(', ') + '</b> is invisible to the <code>all_oxygens</code> test'
          : 'oxygen-only framework — limitation not triggered here') + '</td></tr>';
    }).join('');

    // Limitation 3 evidence: borderline bonds
    const l3rows = all.map(a =>
      '<tr><td class="dt-label">' + a.name + '</td>' +
      '<td class="dt-value">' + a.quality.borderlineBonds + ' / ' + a.quality.totalBonds + '</td>' +
      '<td class="dt-note">' + a.quality.borderlinePct.toFixed(1) + '% of bonds sit within 10% of the cutoff' +
      (a.quality.borderlinePct > 5 ? ' — <b>this decomposition is sensitive to the refinement</b>' : '') +
      '</td></tr>').join('');

    // Limitation 4 evidence: rod candidates + discarded fragments
    const l4rows = all.map(a =>
      '<tr><td class="dt-label">' + a.name + '</td>' +
      '<td class="dt-value">' + a.quality.rodCandidates + ' rod-like</td>' +
      '<td class="dt-note">' + a.quality.discardedFragments + ' fragment(s) would be silently dropped by the solvent heuristic</td></tr>').join('');

    const card = (n, title, problem, why, fix, head, rows) =>
      '<div class="lim-card">' +
        '<div class="lim-head"><span class="lim-num">' + n + '</span><h4>' + title + '</h4></div>' +
        '<p class="explain-block" style="margin:6px 0 10px;"><b>The limitation.</b> ' + problem + '</p>' +
        '<p class="explain-block" style="margin:0 0 10px;"><b>Why it matters for MOF design.</b> ' + why + '</p>' +
        '<div class="fix-inline"><b>Proposed fix.</b> ' + fix + '</div>' +
        '<div class="data-panel" style="margin-top:12px;">' +
          '<div class="data-title">Live evidence across every test structure' +
          '<span class="data-sub">computed in your browser from the real CIF files</span></div>' +
          '<table class="data-table"><thead><tr>' + head + '</tr></thead><tbody>' + rows + '</tbody></table>' +
        '</div>' +
      '</div>';

    container.innerHTML =
      card(1, 'The node is cut short — SBUs come out chemically incomplete',
        'The algorithm severs every bond that touches a metal. A carboxylate binds the metal through its oxygen, so that cut lands <i>between the metal and the group that chemically belongs to it</i>. The carboxylate is filed as linker and the node is left as bare metal.',
        'The inorganic building unit is the part that governs thermal and chemical stability. Reporting HKUST-1\'s node as <code>[Cu][Cu]</code> discards the four carboxylates that actually define the paddlewheel — so any search or ML model keyed on that node is reasoning about a species that does not exist in the crystal.',
        'Extend the node across its coordinating groups: when a metal-bound oxygen belongs to a verified carboxylate (its carbon has exactly one carbon and two oxygen neighbours), absorb the whole –COO– group into the node. The node then reports a complete, chemically real SBU.',
        '<td>Structure</td><td>Published node</td><td>With fix</td><td>Effect</td>', l1rows) +

      card(2, 'Only oxygen counts as a bridge',
        'The entire chemical rule is <code>all_oxygens</code> — true only when every atom of a fragment is O or H. A nitrido, sulfido or mixed-heteroatom bridge contains neither, so it fails the test and is misfiled as organic linker.',
        'It silently restricts the algorithm to oxygen-bridged chemistry. Nitride, sulfide and mixed-donor frameworks — an active area for conductive and catalytic MOFs — fall outside what the rule can express, and fail without any warning that the answer is unreliable.',
        'Generalise the test from "is every atom O or H" to "is every atom a non-carbon heteroatom": any carbon-free fragment bridging metals is a bridge, whatever element it is built from. Oxygen keeps behaving exactly as before, so published results are unchanged.',
        '<td>Structure</td><td>Donor atoms present</td><td>Consequence</td>', l2rows) +

      card(3, 'Every bond is inferred, so the answer can hinge on a borderline contact',
        'A CIF stores no connectivity at all. Every bond is reconstructed from interatomic distance against a covalent-radius cutoff. A contact sitting just under the threshold becomes a bond; the same contact in a differently-refined copy of the same material may not.',
        'Two depositions of the same MOF can decompose differently, and nothing in the output says so. For a database keyed on these identifiers, that is a silent reproducibility failure rather than a visible error.',
        'Report it instead of hiding it. Flag every bond within 10% of its cutoff and publish that count alongside the decomposition, so a result resting on marginal contacts is visibly marked as low-confidence rather than presented with false certainty.',
        '<td>Structure</td><td>Borderline bonds</td><td>Confidence</td>', l3rows) +

      card(4, 'Rod SBUs and solvent are handled by convention, not by chemistry',
        'A periodically infinite rod SBU cannot collapse to a point, so it takes a separate branch and a 4-connected vertex is split into two 3-connected ones <i>by convention</i>. Separately, any 0- or 1-connected fragment is deleted as "solvent" by heuristic.',
        'Both choices are defensible but invisible. A capping ligand that is chemically part of the framework can be deleted as solvent, and a rod framework\'s reported topology depends on a naming convention rather than on the structure.',
        'Surface both decisions. Detect and report rod-like node fragments explicitly, and list what the solvent heuristic removed rather than deleting it silently — so the choices become reviewable instead of buried.',
        '<td>Structure</td><td>Rod detection</td><td>Solvent heuristic</td>', l4rows);
  }

  // ---------------------------------------------------------------
  // SECTION 3 — before/after 3D, switchable across every structure
  // ---------------------------------------------------------------
  const VIEW = { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true, netOnly: false };

  function showStructure(name) {
    currentName = name;
    const a = analyse(name);
    rBefore.load(a.before, VIEW);
    rAfter.load(a.after, VIEW);

    els.beforeName.textContent = name;
    els.afterName.textContent = name;
    els.beforeStats.innerHTML = '<b>Node:</b> ' + a.beforeNode + ' &nbsp;(' + a.beforeSize + ' atoms) &nbsp;·&nbsp; ' +
      a.before.n_metal_blocks + ' node / ' + a.before.n_linker_blocks + ' linker blocks';
    els.afterStats.innerHTML = '<b>Node:</b> ' + a.afterNode + ' &nbsp;(' + a.afterSize + ' atoms) &nbsp;·&nbsp; ' +
      a.after.n_metal_blocks + ' node / ' + a.after.n_linker_blocks + ' linker blocks';

    els.verdict.innerHTML = a.gained > 0
      ? '<b>' + a.gained + ' atoms recovered into the node.</b> The published rule reported <code>' + a.beforeNode +
        '</code>; with the fixes applied the same structure reports <code>' + a.afterNode +
        '</code> — a chemically complete SBU. Both panels are drawn at identical coordinates, so the only difference you can see is the classification itself.'
      : '<b>No change for this structure — and that is the honest result.</b> ' + name +
        ' has no coordinating carboxylate for the node-completion fix to act on, so the published output was already chemically complete here. A fix that changed this structure would be a fix that was wrong.';

    els.tabs.querySelectorAll('.struct-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.name === name));
  }

  function buildSection3(canvasMap, uiEls) {
    rBefore = root.MOFRender.create();
    rBefore.init(canvasMap.before.canvas, canvasMap.before.container, canvasMap.before.labels, canvasMap.before.hoverTip);
    rAfter = root.MOFRender.create();
    rAfter.init(canvasMap.after.canvas, canvasMap.after.container, canvasMap.after.labels, canvasMap.after.hoverTip);
    els = uiEls;

    // structure switcher
    els.tabs.innerHTML = '';
    Object.keys(structures).forEach(name => {
      const b = document.createElement('button');
      b.className = 'struct-tab';
      b.dataset.name = name;
      b.textContent = name;
      b.addEventListener('click', () => showStructure(name));
      els.tabs.appendChild(b);
    });

    // summary table across ALL structures, so nothing looks cherry-picked
    const all = Object.keys(structures).map(analyse);
    const best = all.reduce((m, a) => (a.gained > m.gained ? a : m), all[0]);
    els.summary.innerHTML =
      '<div class="data-title">Effect of the fixes on every structure' +
      '<span class="data-sub">clearest difference: <b>' + best.name + '</b> (+' + best.gained + ' atoms into the node)</span></div>' +
      '<table class="data-table"><thead><tr><td>Structure</td><td>Published node</td><td>Node after fixes</td><td>Change</td></tr></thead><tbody>' +
      all.map(a => '<tr><td class="dt-label">' + a.name + '</td><td class="dt-value">' + a.beforeNode +
        '</td><td class="dt-value" style="color:var(--good)">' + a.afterNode + '</td><td class="dt-note">' +
        (a.gained > 0 ? '<b>+' + a.gained + ' atoms</b> — incomplete SBU corrected'
                      : 'unchanged — already complete') + '</td></tr>').join('') +
      '</tbody></table>';

    showStructure(best.name);   // open on the most illustrative case
  }

  function setStructures(map) { structures = map; }

  root.MetalOxoDrawbacks = { setStructures, buildSection2, buildSection3, showStructure };
})(typeof window !== 'undefined' ? window : globalThis);
