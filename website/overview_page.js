// overview_page.js
// Fills the live evidence tables in the overview sections of index.html. Everything here is computed
// from the real CIF files at page load -- the overview makes claims, and these
// tables are the receipts for them.

(function () {
  // The four summaries this module produces are split across the overview and
  // methodology pages. An unguarded innerHTML on an id that is not on THIS
  // page throws, and that exception kills every summary after it -- a failure
  // that leaves the page looking merely empty rather than broken. Each write
  // is therefore guarded.
  function setHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  'use strict';

  const LIT = {
    'HKUST-1': { node: 4, linker: 3, net: 'tbo', sbu: 'Cu₂ paddlewheel' },
    'UiO-66':  { node: 12, linker: 2, net: 'fcu', sbu: 'Zr₆O₄(OH)₄' },
    'MOF-5':   { node: 6, linker: 2, net: 'pcu', sbu: 'Zn₄O' },
    'ZIF-8':   { node: 4, linker: 2, net: 'sod', sbu: 'single Zn' },
  };

  function fmt(c) {
    return Object.entries(c).sort((a, b) => b[1] - a[1]).map(([e, n]) => e + n).join(' ');
  }

  document.addEventListener('DOMContentLoaded', function () {
    const D = window.MOFDecompose, N = window.MOFNetwork;
    const names = Object.keys(window.DEFAULT_CIFS);
    const R = {};

    names.forEach(name => {
      const p = D.parseCIF(window.DEFAULT_CIFS[name]);
      p.atoms.cellPar = p.cellPar;
      const published = D.buildMetalOxoVariant(p.atoms, p.cellMatrix);
      const fixed = D.buildMetalOxoVariant(p.atoms, p.cellMatrix,
        { fixes: { completeNodes: true, donorAgnostic: true } });
      const G = N.buildQuotientGraph(published);
      const deg = N.degrees(G);
      const naive = N.buildNaiveGraph(published);
      const ndeg = N.degrees(naive);
      const an = N.analyse(published);
      R[name] = { published, fixed, G, deg, ndeg, naive, an, p };
    });

    // ---------- 1. the tie evidence: why "top-k by degree" is arbitrary ----------
    let rows = '';
    names.forEach(name => {
      const { G, deg } = R[name];
      const max = Math.max.apply(null, deg);
      const ties = deg.filter(v => v === max).length;
      const distinct = new Set(deg).size;
      rows += '<tr><td class="dt-label">' + name + '</td>' +
        '<td class="dt-value">' + G.n + '</td>' +
        '<td class="dt-value">' + distinct + '</td>' +
        '<td class="dt-value">' + max + '</td>' +
        '<td class="dt-value" style="color:var(--bad)">' + ties + ' of ' + G.n + '</td>' +
        '<td class="dt-note">' + (ties > 1
          ? 'a “top-' + ties + '” list could be ordered ' + ties + '! ways — all equally valid'
          : 'only one block at this degree, but still only ' + distinct + ' distinct values overall') +
        '</td></tr>';
    });
    setHTML('tie-evidence',
      '<table class="data-table"><thead><tr><td>Structure</td><td>Blocks</td>' +
      '<td>Distinct degree values</td><td>Max degree</td><td>Blocks tied at max</td>' +
      '<td>Consequence</td></tr></thead><tbody>' + rows + '</tbody></table>');

    // ---------- 2. what the degree DOES buy you ----------
    let rows2 = '';
    names.forEach(name => {
      const { deg, G, ndeg, naive } = R[name];
      const lit = LIT[name] || {};
      const nodeDeg = Array.from(new Set(G.blocks.map((b, i) => b.type === 'metal' ? deg[i] : null).filter(v => v !== null)));
      const naiveNode = Array.from(new Set(naive.blocks.map((b, i) => b.type === 'metal' ? ndeg[i] : null).filter(v => v !== null)));
      const ok = nodeDeg.length === 1 && nodeDeg[0] === lit.node;
      rows2 += '<tr><td class="dt-label">' + name + '</td>' +
        '<td class="dt-value">' + (lit.sbu || '') + '</td>' +
        '<td class="dt-value" style="color:var(--good)">' + nodeDeg.join(',') + '</td>' +
        '<td class="dt-value">' + lit.node + '</td>' +
        '<td class="dt-value">' + lit.net + '</td>' +
        '<td class="dt-note">' + (ok ? '<b style="color:var(--good)">✓ matches</b>' : '<b style="color:var(--bad)">✗</b>') +
        ' · naive graph would say ' + naiveNode.join(',') + '</td></tr>';
    });
    setHTML('degree-value',
      '<table class="data-table"><thead><tr><td>Structure</td><td>Inorganic SBU</td>' +
      '<td>Coordination number we compute</td><td>Published</td><td>Net</td><td>Check</td>' +
      '</tr></thead><tbody>' + rows2 + '</tbody></table>');

    // ---------- 3. headline results across the whole project ----------
    let rows3 = '';
    names.forEach(name => {
      const { published, fixed, an, p } = R[name];
      const nb = published.blocks.find(b => b.type === 'metal');
      const na = fixed.blocks.find(b => b.type === 'metal');
      const gained = (na ? na.n_atoms : 0) - (nb ? nb.n_atoms : 0);
      rows3 += '<tr><td class="dt-label">' + name + '</td>' +
        '<td class="dt-value">' + p.atoms.length + '</td>' +
        '<td class="dt-value">' + published.bonds.length + '</td>' +
        '<td class="dt-value">' + (nb ? fmt(nb.composition) : '—') + '</td>' +
        '<td class="dt-value" style="color:var(--good)">' + (na ? fmt(na.composition) : '—') + '</td>' +
        '<td class="dt-value">' + (gained > 0 ? '+' + gained : '0') + '</td>' +
        '<td class="dt-value">' + an.lambda2.toFixed(2) + '</td></tr>';
    });
    setHTML('results-summary',
      '<table class="data-table"><thead><tr><td>Structure</td><td>Atoms</td><td>Bonds inferred</td>' +
      '<td>Node — published rule</td><td>Node — with our fixes</td><td>Atoms recovered</td><td>λ₂</td>' +
      '</tr></thead><tbody>' + rows3 + '</tbody></table>');

    // ---------- 4. defect: where influence becomes real ----------
    let rows4 = '';
    names.forEach(name => {
      const { published, an } = R[name];
      const linkers = published.blocks.filter(b => b.type === 'linker');
      if (!linkers.length) return;
      const d = N.analyse(published, { excludeBlocks: [linkers[0].id] });
      const broke = d.distinctCentrality > an.distinctCentrality;
      rows4 += '<tr><td class="dt-label">' + name + '</td>' +
        '<td class="dt-value">' + an.distinctCentrality + '</td>' +
        '<td class="dt-value" style="color:' + (broke ? PAL.good : PAL.text3) + '">' + d.distinctCentrality + '</td>' +
        '<td class="dt-value">' + an.lambda2.toFixed(3) + ' → ' + d.lambda2.toFixed(3) + '</td>' +
        '<td class="dt-note">' + (broke
          ? 'symmetry broken — blocks now distinguishable, ranking becomes meaningful'
          : 'remaining blocks still all equivalent — no ranking possible even now') + '</td></tr>';
    });
    setHTML('defect-summary',
      '<table class="data-table"><thead><tr><td>Structure</td><td>Distinct centralities (perfect)</td>' +
      '<td>After removing 1 linker</td><td>λ₂ change</td><td>Meaning</td></tr></thead><tbody>' +
      rows4 + '</tbody></table>');
  });
})();
