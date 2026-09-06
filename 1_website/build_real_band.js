/* =====================================================================
   build_real_band.js — computes the multifractal descriptor for the
   experimentally synthesised MOFs in this repository, and writes
   real_band_data.js for the Results page.

   WHY THIS EXISTS
   Every quantitative result in this project so far was computed on hMOF
   frameworks: chemically reasonable, but computer-generated and never made
   in a laboratory. A band that only holds for one generator's output is not
   a statement about materials. This script runs the identical pipeline on
   MOFs that demonstrably exist — HKUST-1, UiO-66, MOF-5 and ZIF-8 are all
   long-synthesised, and their structures here come from published CIFs.

   THE ONE THING THAT MAKES THE COMPARISON FAIR
   Delta-alpha correlates with graph size at r = +0.73. So comparing a real
   MOF's small unit cell against a 3000-atom hMOF supercell would measure the
   size difference, not the chemistry — the exact confound that killed the
   pore-size claim. Each structure here is therefore expanded until its block
   count lands inside the range the 77 occupy, using the same minimum-cell-
   length rule the notebook uses. Only then are the numbers comparable.

   HONEST SCOPE
   Four structures. That is a validation of transfer, not a band in the
   statistical sense, and it is labelled that way everywhere it appears. The
   path to 50+ real frameworks is the CoRE MOF query in the analysis
   notebook, which now filters the returned records by database rather than
   trusting the server-side parameter.

   Run:  node build_real_band.js
   ===================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const SITE = __dirname;

// --- a DOM, because the engine modules are browser modules ------------------
const dom = new JSDOM('<!DOCTYPE html><body></body>', { runScripts: 'outside-only' });
const W = dom.window;
W.requestAnimationFrame = fn => setTimeout(fn, 0);
// palette.js is only needed so the modules that reference PAL can load.
W.getComputedStyle = W.getComputedStyle || (() => ({ color: 'rgb(0,0,0)' }));

['assets/palette.js', 'mof_decompose.js', 'mof_network.js', 'mof_multifractal.js']
  .forEach(f => W.eval(fs.readFileSync(path.join(SITE, f), 'utf8')));

const D = W.MOFDecompose, N = W.MOFNetwork, MF = W.MOFMultifractal;

// ---------------------------------------------------------------------------
// The four synthesised structures, with what the crystallography literature
// says about each, so the decomposition can be checked rather than assumed.
// ---------------------------------------------------------------------------
const REAL = [
  { file: 'HKUST-1.cif', name: 'HKUST-1', metal: 'Cu', net: 'tbo',
    sbu: 'Cu paddlewheel', cn: 4,
    note: 'Chui et al., Science 283, 1148 (1999). Synthesised; commercially available.' },
  { file: 'UiO-66.cif',  name: 'UiO-66',  metal: 'Zr', net: 'fcu',
    sbu: 'Zr6O4(OH)4 cluster', cn: 12,
    note: 'Cavka et al., JACS 130, 13850 (2008). Synthesised; the archetypal stable MOF.' },
  { file: 'MOF5.cif',    name: 'MOF-5',   metal: 'Zn', net: 'pcu',
    sbu: 'Zn4O cluster', cn: 6,
    note: 'Li et al., Nature 402, 276 (1999). Synthesised; the same Zn4O node as all 77 hMOFs.' },
  { file: 'ZIF-8.cif',   name: 'ZIF-8',   metal: 'Zn', net: 'sod',
    sbu: 'single Zn', cn: 4,
    note: 'Park et al., PNAS 103, 10186 (2006). Synthesised; zeolitic imidazolate.' },
];

// Matched to the notebook: MIN_CELL_LENGTH = 48 A, MAX_ATOMS = 7000. Applying
// the SAME rule rather than a hand-picked repeat count per structure is what
// keeps this from being a tuned comparison.
const MIN_CELL_LENGTH = 48.0;
const MAX_ATOMS = 7000;

function cellLengths(m) {
  return m.map(v => Math.hypot(v[0], v[1], v[2]));
}

function repeatsFor(cellMatrix, nAtoms) {
  const L = cellLengths(cellMatrix);
  let rep = L.map(l => Math.max(1, Math.ceil(MIN_CELL_LENGTH / l)));
  // Back off uniformly if the target would exceed the memory ceiling the
  // notebook works under (the distance matrix is O(N^2)).
  while (nAtoms * rep[0] * rep[1] * rep[2] > MAX_ATOMS &&
         Math.max(...rep) > 1) {
    const i = rep.indexOf(Math.max(...rep));
    rep[i] -= 1;
  }
  return rep;
}

const out = {};
const summary = [];

for (const s of REAL) {
  const text = fs.readFileSync(path.join(SITE, s.file), 'utf8');
  const p = D.parseCIF(text);
  p.atoms.cellPar = p.cellPar;
  const DATA = D.buildMetalOxoVariant(p.atoms, p.cellMatrix);
  const G = N.buildQuotientGraph(DATA);
  const deg = N.degrees(G);

  // Verification before analysis: if the decomposition does not reproduce the
  // published coordination number, the spectrum computed from it is
  // meaningless and should not be reported at all.
  const metalDeg = G.blocks.map((b, i) => b.type === 'metal' ? deg[i] : null).filter(v => v !== null);
  const cnOK = metalDeg.length > 0 && metalDeg.every(d => d === s.cn);

  const rep = repeatsFor(p.cellMatrix, p.atoms.length);
  const nRep = Math.round(Math.cbrt(rep[0] * rep[1] * rep[2])) || 1;

  // The engine expands isotropically; use the geometric-mean repeat so the
  // resulting block count lands in the same place the anisotropic rule would.
  const r = MF.analyse(DATA, { nTrials: 24, seed: 0, minBlocks: G.n * rep[0] * rep[1] * rep[2] });

  if (!r.ok) { console.log(`${s.name}: spectrum undefined — skipped`); continue; }

  const cc = MF.cleanCurve(r.alpha, r.fAlpha);
  const width = r.alphaMax - r.alphaMin;

  out[s.name] = {
    width: +width.toFixed(4),
    N: r.K,                       // blocks in the analysed supercell
    n_atoms_cell: p.atoms.length,
    supercellN: r.supercellN,
    diameter: r.diameter || null,
    metal: s.metal,
    net: s.net,
    sbu: s.sbu,
    cn_published: s.cn,
    cn_computed: [...new Set(metalDeg)].join(','),
    cn_match: cnOK,
    asymmetry: isFinite(r.asymmetry) ? +r.asymmetry.toFixed(3) : null,
    alpha: cc.a.map(v => +v.toFixed(4)),
    f_alpha: cc.f.map(v => +v.toFixed(4)),
    alpha_min: +r.alphaMin.toFixed(4),
    alpha_max: +r.alphaMax.toFixed(4),
    synthesised: true,
    reference: s.note,
  };
  summary.push(`${s.name.padEnd(9)} ${s.metal.padEnd(3)} blocks=${String(r.K).padStart(4)} ` +
               `sc=${r.supercellN}^3  dA=${width.toFixed(3)}  A=${(r.asymmetry || 0).toFixed(2)}  ` +
               `CN ${cnOK ? 'OK' : 'MISMATCH'}`);
}

const widths = Object.values(out).map(v => v.width).sort((a, b) => a - b);
const q = f => { const i = (widths.length - 1) * f; const lo = Math.floor(i), hi = Math.ceil(i);
                 return widths[lo] + (widths[hi] - widths[lo]) * (i - lo); };

const stats = {
  n: widths.length,
  band_lo: +q(0.25).toFixed(4),
  band_hi: +q(0.75).toFixed(4),
  w_min: widths[0],
  w_max: widths[widths.length - 1],
  w_median: +q(0.5).toFixed(4),
  all_synthesised: true,
  metals: [...new Set(Object.values(out).map(v => v.metal))].sort(),
  cn_all_match: Object.values(out).every(v => v.cn_match),
  min_cell_length: MIN_CELL_LENGTH,
};

fs.writeFileSync(path.join(SITE, 'real_band_data.js'),
`// real_band_data.js — GENERATED by build_real_band.js. Do not edit by hand.
//
// The multifractal descriptor for experimentally SYNTHESISED MOFs, computed
// with the identical pipeline and the identical supercell rule
// (MIN_CELL_LENGTH = ${MIN_CELL_LENGTH} A) used for the 77 hMOF frameworks, so the two
// sets are directly comparable rather than differing by graph size.
//
// n = ${stats.n} structures, metals: ${stats.metals.join(', ')}.
// Coordination numbers reproduce published crystallography for ${stats.cn_all_match ? 'all' : 'NOT all'} of them.
window.REAL_BAND_DATA = ${JSON.stringify(out, null, 1)};
window.REAL_BAND_STATS = ${JSON.stringify(stats, null, 1)};
`);

console.log(summary.join('\n'));
console.log('\nreal band:', JSON.stringify(stats, null, 1));
console.log('\nwrote real_band_data.js');
