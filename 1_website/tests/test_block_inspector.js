/* =====================================================================
   test_block_inspector.js — the coarse-grained vertex must be openable.

   WHAT THIS GUARDS
   After centroid simplification a whole cluster of atoms is drawn as one
   sphere, and the atoms themselves are removed from the scene. Hovering that
   sphere now draws what is inside it. This suite checks the drawing is real:
   that it contains the right number of atoms, that the bonds it draws are
   bonds that genuinely exist inside that block, and that it only appears when
   the atoms are actually hidden — a diagram of atoms you can already see
   would be clutter, not explanation.

   It runs the projection maths directly rather than through WebGL, because
   jsdom has no GL context. The geometry is the part that can be wrong; the
   sphere it hangs off is not.
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const SITE = path.join(__dirname, '..');
let failures = 0, checks = 0;
function ok(cond, msg) {
  checks++;
  if (cond) console.log('PASS  ' + msg);
  else { failures++; console.log('FAIL  ' + msg); }
}

// ---- boot the engine modules on a real CIF --------------------------------
const dom = new JSDOM('<!DOCTYPE html><body></body>', { runScripts: 'outside-only' });
const W = dom.window;
W.requestAnimationFrame = fn => setTimeout(fn, 0);
['assets/palette.js', 'mof_decompose.js'].forEach(f =>
  W.eval(fs.readFileSync(path.join(SITE, f), 'utf8')));

const cif = fs.readFileSync(path.join(SITE, 'HKUST-1.cif'), 'utf8');
const D = W.MOFDecompose;
const parsed = D.parseCIF(cif);
// metalOxo is the variant the walkthrough coarse-grains, so it is the one the
// inspector will be opened on.
const variant = D.buildAllVariants(parsed.atoms, parsed.cellMatrix).metalOxo;

ok(variant.blocks.length > 0, `decomposition produced blocks (${variant.blocks.length})`);

// ---- the data the inspector reads ----------------------------------------
// It needs, for each block: the atom indices, and the bonds among them.
const atoms = variant.atoms;
const geom = variant;
ok(!!atoms && atoms.length > 0, `atoms available to the inspector (${atoms.length})`);
ok(Array.isArray(geom.bonds) && geom.bonds.length > 0,
   `bonds available to the inspector (${geom.bonds.length})`);

let withInternal = 0, badRef = 0, emptyBlocks = 0;
variant.blocks.forEach(b => {
  const idx = b.atoms || [];
  if (idx.length === 0) { emptyBlocks++; return; }
  if (idx.some(i => i < 0 || i >= atoms.length)) badRef++;
  const inBlock = new Set(idx);
  const internal = geom.bonds.filter(bd => inBlock.has(bd.a) && inBlock.has(bd.b));
  const leaving  = geom.bonds.filter(bd => inBlock.has(bd.a) !== inBlock.has(bd.b));
  if (internal.length > 0) withInternal++;
  // a block with more than one atom and no internal bond would be a block that
  // was never actually connected — that is a decomposition bug, not a drawing one
  if (idx.length > 1) {
    ok.silent = true;
    if (internal.length === 0) { failures++; checks++; console.log(`FAIL  block #${b.id} has ${idx.length} atoms but no internal bonds`); }
  }
  b._internal = internal.length;
  b._leaving = leaving.length;
});
ok(emptyBlocks === 0, 'no block is empty');
ok(badRef === 0, 'every block references atoms that exist');
ok(withInternal > 0, `blocks with internal bonds to draw (${withInternal}/${variant.blocks.length})`);

// the metal nodes are the interesting case: they must contain several atoms
const metals = variant.blocks.filter(b => b.type === 'metal');
ok(metals.length > 0, `metal blocks found (${metals.length})`);
ok(metals.every(b => (b.atoms || []).length >= 2),
   'every metal block holds more than one atom — there is something to look inside');
ok(metals.every(b => b._leaving > 0),
   'every metal block has bonds leaving it — it is genuinely part of the framework');

// ---- the projection must not collapse a flat block to a line -------------
// A carboxylate linker is close to planar. Projecting onto the two widest
// directions has to keep it two-dimensional, or the diagram shows a stripe.
function principalSpread(pts) {
  const n = pts.length, c = [0, 0, 0];
  pts.forEach(p => { c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; });
  c[0] /= n; c[1] /= n; c[2] /= n;
  const C = [[0,0,0],[0,0,0],[0,0,0]];
  pts.forEach(p => {
    const d = [p[0]-c[0], p[1]-c[1], p[2]-c[2]];
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i][j] += d[i]*d[j];
  });
  const mul = (M, v) => [M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
                         M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
                         M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2]];
  const norm = v => { const L = Math.hypot(...v) || 1; return [v[0]/L, v[1]/L, v[2]/L]; };
  let u = norm([1, 0.3, 0.1]);
  for (let k = 0; k < 24; k++) u = norm(mul(C, u));
  let lam = 0;
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) lam += u[a]*C[a][b]*u[b];
  const Dm = C.map((row, i) => row.map((val, j) => val - lam*u[i]*u[j]));
  let v = norm([0.2, 1, 0.4]);
  for (let k = 0; k < 24; k++) v = norm(mul(Dm, v));
  const dot = u[0]*v[0] + u[1]*v[1] + u[2]*v[2];
  v = norm([v[0]-dot*u[0], v[1]-dot*u[1], v[2]-dot*u[2]]);
  let sx = 0, sy = 0;
  pts.forEach(p => {
    const d = [p[0]-c[0], p[1]-c[1], p[2]-c[2]];
    sx = Math.max(sx, Math.abs(d[0]*u[0]+d[1]*u[1]+d[2]*u[2]));
    sy = Math.max(sy, Math.abs(d[0]*v[0]+d[1]*v[1]+d[2]*v[2]));
  });
  return { sx, sy };
}

let degenerate = 0, tested = 0;
variant.blocks.forEach(b => {
  const idx = b.atoms || [];
  if (idx.length < 3) return;
  tested++;
  const pts = idx.map(i => atoms[i].pos || [atoms[i].x, atoms[i].y, atoms[i].z]);
  const { sx, sy } = principalSpread(pts);
  if (sy < 1e-6 || sx / Math.max(sy, 1e-9) > 60) degenerate++;
});
ok(tested > 0, `blocks large enough to project tested (${tested})`);
ok(degenerate === 0,
   `no block collapses to a line under the projection (${degenerate} degenerate)`);

// ---- the wiring on the page ----------------------------------------------
const render = fs.readFileSync(path.join(SITE, 'mof_render.js'), 'utf8');
ok(/renderBlockInspector/.test(render), 'the inspector is wired into the hover handler');
ok(/if \(!atomGroup\.visible\) inspect = b;/.test(render),
   'it only opens once the atoms are hidden — no diagram of atoms already on screen');
ok(/principalPlane/.test(render), 'the projection plane is chosen, not assumed');

const css = fs.readFileSync(path.join(SITE, 'assets', 'design.css'), 'utf8');
ok(/\.bi-svg/.test(css) && /hover-tip:has\(\.bi-svg\)/.test(css),
   'the tooltip widens only when it carries a diagram');

console.log(`\n${checks - failures}/${checks} checks passed.`);
if (failures) { console.log('BLOCK-INSPECTOR CHECKS FAILED'); process.exit(1); }
console.log('ALL BLOCK-INSPECTOR CHECKS PASSED');
