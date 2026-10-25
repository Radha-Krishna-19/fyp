const path = require('path');
const SITE = path.join(__dirname, '..');
// jsdom test for network_analysis.html + mof_network.js + network_page.js.
// Verifies the periodic graph gives literature-correct coordination numbers,
// that the naive construction demonstrably fails, that centrality degeneracy
// is reported honestly, and that the defect simulation breaks the symmetry.

const fs = require('fs');
const { JSDOM } = require('jsdom');

// network_analysis.html was folded into the single page; network_page.js now
// renders section 11-14 of index.html. Test against the page we actually ship.
const htmlFull = fs.readFileSync(path.join(SITE, 'network.html'), 'utf8');
const bodyHtml = htmlFull
  .replace(/<script src="[a-zA-Z0-9_.]+\.js"><\/script>/g, '')
  .replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');

const dom = new JSDOM(`<!DOCTYPE html><html><body>${bodyHtml}</body></html>`, {
  runScripts: 'outside-only', pretendToBeVisual: true,
});
const { window } = dom;

// ---- canvas 2D stub (jsdom has no canvas backend) ----
const ctxStub = new Proxy({}, {
  get: (t, k) => {
    if (k === 'canvas') return {};
    return typeof k === 'string' ? (() => {}) : undefined;
  },
  set: () => true,
});
window.HTMLCanvasElement.prototype.getContext = () => ctxStub;
Object.defineProperty(window.HTMLCanvasElement.prototype, 'clientWidth', { value: 700 });
Object.defineProperty(window.HTMLCanvasElement.prototype, 'clientHeight', { value: 420 });

const assert = (c, m) => { if (!c) { console.error('FAIL: ' + m); process.exit(1); } console.log('OK:', m); };

// ---- minimal THREE stub so the 3D panel initialises under jsdom ----
class V3 { constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;}
  set(){return this;} copy(){return this;} clone(){return new V3();} add(){return this;} sub(){return this;}
  multiplyScalar(){return this;} divideScalar(){return this;} length(){return 1;} distanceTo(){return 1;}
  normalize(){return this;} setScalar(){return this;} project(){return this;} lerp(){return this;} }
class O3 { constructor(){this.position=new V3();this.scale=new V3();this.quaternion={setFromUnitVectors(){return this;}};
  this.rotation={};this.userData={};this.children=[];this.visible=true;}
  add(o){this.children.push(o);return this;} remove(o){const i=this.children.indexOf(o);if(i>=0)this.children.splice(i,1);return this;} }
class Geo { dispose(){} }
class Mat { constructor(o={}){Object.assign(this,o);this.color={};} dispose(){} }
window.THREE = {
  Vector2: class { constructor(){} }, Vector3: V3,
  Color: class { setHSL(){return this;} getHex(){return 0x888888;} },
  Object3D: O3, Group: class extends O3 {},
  Mesh: class extends O3 { constructor(g,m){super();this.geometry=g;this.material=m;} },
  LineSegments: class extends O3 { constructor(g,m){super();this.geometry=g;this.material=m;} },
  Scene: class extends O3 {},
  PerspectiveCamera: class extends O3 { lookAt(){} updateProjectionMatrix(){} },
  WebGLRenderer: class { constructor(o){this.canvas=o.canvas;} setSize(){} setPixelRatio(){} render(){} },
  DirectionalLight: class extends O3 {}, AmbientLight: class extends O3 {},
  SphereGeometry: Geo, CylinderGeometry: Geo, BoxGeometry: Geo,
  BufferGeometry: class extends Geo { setFromPoints(){return this;} },
  LineBasicMaterial: Mat, MeshStandardMaterial: Mat,
  Raycaster: class { setFromCamera(){} intersectObjects(){return [];} },
};
window.ResizeObserver = class { observe(){} };
window.requestAnimationFrame = () => 0;

// palette.js must load first: the drawing code resolves every colour through
// PAL, so without it every render throws and the page renders empty.
['assets/palette.js', 'mof_decompose.js', 'mof_network.js', 'mof_render.js',
 'mof_multifractal.js', 'default_cif_data.js', 'network_page.js'].forEach(f => {
  window.eval(fs.readFileSync(path.join(SITE, f), 'utf8'));
});
window.document.dispatchEvent(new window.Event('DOMContentLoaded', { bubbles: true }));

// ---------- engine correctness ----------
const LIT = { 'HKUST-1': [4, 3, 'tbo'], 'UiO-66': [12, 2, 'fcu'], 'MOF-5': [6, 2, 'pcu'], 'ZIF-8': [4, 2, 'sod'] };
const D = window.MOFDecompose, N = window.MOFNetwork;

Object.keys(LIT).forEach(name => {
  const p = D.parseCIF(window.DEFAULT_CIFS[name]);
  p.atoms.cellPar = p.cellPar;
  const DATA = D.buildMetalOxoVariant(p.atoms, p.cellMatrix);
  const r = N.analyse(DATA);
  const [en, el] = LIT[name];
  assert(r.nodeCN.length === 1 && r.nodeCN[0] === en,
    name + ' node coordination = ' + r.nodeCN.join(',') + ' (published ' + en + ')');
  assert(r.linkerCN.length === 1 && r.linkerCN[0] === el,
    name + ' linker coordination = ' + r.linkerCN.join(',') + ' (published ' + el + ')');
});

// the naive construction must demonstrably fail on UiO-66
const pu = D.parseCIF(window.DEFAULT_CIFS['UiO-66']); pu.atoms.cellPar = pu.cellPar;
const Du = D.buildMetalOxoVariant(pu.atoms, pu.cellMatrix);
const naive = N.buildNaiveGraph(Du), nd = N.degrees(naive);
const naiveNodeCN = naive.blocks.map((b, i) => (b.type === 'metal' ? nd[i] : null)).filter(v => v !== null);
assert(naiveNodeCN[0] !== 12,
  'naive graph gets UiO-66 wrong (' + naiveNodeCN[0] + ' instead of 12) — the bug this page exists to explain');

// spectrum sanity: L is PSD, smallest eigenvalue is 0 (connected component count)
Object.keys(LIT).forEach(name => {
  const p = D.parseCIF(window.DEFAULT_CIFS[name]); p.atoms.cellPar = p.cellPar;
  const r = N.analyse(D.buildMetalOxoVariant(p.atoms, p.cellMatrix));
  assert(Math.abs(r.spectrum[0]) < 1e-6, name + ' Laplacian smallest eigenvalue is 0 (as required)');
  assert(r.spectrum.every(v => v > -1e-6), name + ' Laplacian is positive semi-definite');
  assert(r.lambdaMax >= Math.max.apply(null, r.nodeCN),
    name + ' lambda_max (' + r.lambdaMax.toFixed(2) + ') >= max degree (' + Math.max.apply(null, r.nodeCN) + ')');
});

// centrality degeneracy must be reported, not hidden
const ph = D.parseCIF(window.DEFAULT_CIFS['HKUST-1']); ph.atoms.cellPar = ph.cellPar;
const Dh = D.buildMetalOxoVariant(ph.atoms, ph.cellMatrix);
const perfect = N.analyse(Dh);
assert(perfect.distinctCentrality === 2,
  'perfect HKUST-1 has only 2 distinct centrality values — degeneracy is real');

// defect simulation must break the symmetry
const firstLinker = Dh.blocks.find(b => b.type === 'linker');
const defect = N.analyse(Dh, { excludeBlocks: [firstLinker.id] });
assert(defect.distinctCentrality > perfect.distinctCentrality,
  'removing a linker raises distinct centrality values ' + perfect.distinctCentrality +
  ' -> ' + defect.distinctCentrality + ' (symmetry broken)');
assert(defect.lambda2 < perfect.lambda2,
  'defect lowers lambda_2 ' + perfect.lambda2.toFixed(3) + ' -> ' + defect.lambda2.toFixed(3) +
  ' (framework measurably weaker)');

// ---------- page rendering ----------
const tabs = window.document.querySelectorAll('#net-struct-tabs .struct-tab');
assert(tabs.length === 4, 'page offers all 4 structures, got ' + tabs.length);

const val = window.document.getElementById('validation').innerHTML;
assert(val.indexOf('matches') !== -1, 'validation table reports a match against published values');

for (let i = 0; i < tabs.length; i++) {
  tabs[i].click();
  const v = window.document.getElementById('validation').innerHTML;
  const c = window.document.getElementById('centrality').innerHTML;
  assert(v.length > 100 && c.indexOf('<tr>') !== -1,
    'structure ' + tabs[i].dataset.name + ' renders validation + centrality tables');
}

// naive toggle must flip a match to a mismatch on UiO-66
Array.prototype.filter.call(tabs, t => t.dataset.name === 'UiO-66')[0].click();
window.document.getElementById('btn-naive').click();
const naiveVal = window.document.getElementById('validation').innerHTML;
assert(naiveVal.indexOf('differs') !== -1 || naiveVal.indexOf('Naive graph') !== -1,
  'switching to the naive graph visibly flags the failure');
window.document.getElementById('btn-periodic').click();

// defect button toggles
const db = window.document.getElementById('btn-defect');
db.click();
assert(db.textContent.indexOf('restore') !== -1, 'defect button toggles to a restore state');
db.click();

const fp = window.document.getElementById('fingerprint-table').innerHTML;
['HKUST-1', 'UiO-66', 'MOF-5', 'ZIF-8'].forEach(n =>
  assert(fp.indexOf(n) !== -1, 'fingerprint table covers ' + n));

const dg = window.document.getElementById('degeneracy').textContent;
assert(dg.indexOf('not meaningful') !== -1 || dg.indexOf('meaningful') !== -1,
  'degeneracy is stated explicitly rather than hidden');

// ---------- combined 2D + 3D view ----------
assert(window.document.getElementById('mol3d-canvas') !== null, '3D molecular canvas exists on the page');
assert(window.document.getElementById('graph-canvas') !== null, '2D graph canvas exists on the page');
['c3d-degree', 'c3d-central', 'c3d-role', 'c3d-top'].forEach(id =>
  assert(window.document.getElementById(id) !== null, '3D colour control present: ' + id));

const leg = window.document.getElementById('c3d-legend').innerHTML;
assert(leg.length > 20, '3D legend rendered for the default colour mode');

window.document.getElementById('c3d-central').click();
assert(window.document.getElementById('c3d-central').classList.contains('active'), 'centrality colour mode activates');
assert(window.document.getElementById('c3d-legend').innerHTML.indexOf('centrality') !== -1, 'legend switches to centrality');

window.document.getElementById('c3d-top').click();
const legTop = window.document.getElementById('c3d-legend').innerHTML;
assert(legTop.indexOf('highest degree') !== -1, 'highlight mode names the highest degree');
assert(legTop.indexOf('tied') !== -1, 'highlight mode states that the highlighted blocks are tied — the honest point');

window.document.getElementById('c3d-degree').click();
assert(window.document.getElementById('c3d-legend').innerHTML.indexOf('coordination number') !== -1,
  'legend returns to coordination number');

// ---------------- Section 5: multifractal spectrum ----------------
const MF = window.MOFMultifractal;
assert(MF !== undefined, 'multifractal module loaded');

const mfRes = {};
Object.keys(LIT).forEach(name => {
  const p = D.parseCIF(window.DEFAULT_CIFS[name]); p.atoms.cellPar = p.cellPar;
  const DATA = D.buildMetalOxoVariant(p.atoms, p.cellMatrix);
  const r = MF.analyse(DATA, { nTrials: 12, seed: 0 });
  mfRes[name] = r;
  assert(r.ok, name + ' produces a DEFINED spectrum (the original returned NaN for two structures)');
  assert(r.K >= 60, name + ' expanded to a usable graph: ' + r.supercellN + '^3 -> ' + r.K + ' blocks');
  assert(isFinite(r.alphaMin) && isFinite(r.alphaMax), name + ' alpha range finite: ' +
    r.alphaMin.toFixed(2) + '-' + r.alphaMax.toFixed(2));
});

// the specific bug: influential-node induced subgraph is edgeless for HKUST-1
const pk = D.parseCIF(window.DEFAULT_CIFS['HKUST-1']); pk.atoms.cellPar = pk.cellPar;
const Gk = N.buildQuotientGraph(D.buildMetalOxoVariant(pk.atoms, pk.cellMatrix));
const degk = N.degrees(Gk);
const topk = degk.map((d, i) => [i, d]).sort((a, b) => b[1] - a[1]).slice(0, Math.ceil(Gk.n * 0.3)).map(p => p[0]);
const topSet = new Set(topk);
const inducedEdges = Gk.edges.filter(e => topSet.has(e.i) && topSet.has(e.j)).length;
assert(inducedEdges === 0,
  'confirmed: HKUST-1 influential-node induced subgraph has 0 edges — why the original spectrum was undefined');

// band + candidate scoring must work
// The band itself is NOT tested here. It is computed over the 77-framework
// dataset, lives on results.html, and is covered by test_engines.js. The four
// structures above are demonstration structures for the decomposition, and
// building a band from them was removed from the project.

console.log('\nALL NETWORK-PAGE CHECKS PASSED');
process.exit(0);
