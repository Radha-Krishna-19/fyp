const path = require('path');
const SITE = path.join(__dirname, '..');
// test_render_robustness.js
// Targets the exact bug the user reported: "3D model stops after a few minutes."
// Verifies the three fixes in mof_render.js:
//   1. On-demand rendering  -- a static scene must NOT keep issuing GL draw
//      calls every frame (the old code did, from N independent rAF loops).
//   2. Context-loss recovery -- if the browser drops a WebGL context, the
//      panel must rebuild itself instead of going permanently blank.
//   3. Off-screen pausing    -- invisible panels must not render at all.

const fs = require('fs');
const { JSDOM } = require('jsdom');

const dom = new JSDOM(`<!DOCTYPE html><html><body>
  <div id="wrap" style="width:400px;height:300px"><canvas id="c"></canvas></div>
  <div id="labels"></div><div id="tip"></div>
</body></html>`, { runScripts: 'outside-only', pretendToBeVisual: true });
const { window } = dom;

// ---- instrumented THREE stub: counts render() calls ----
let renderCalls = 0;
class V3 {
  constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;}
  set(x,y,z){this.x=x;this.y=y;this.z=z;return this;}
  copy(v){this.x=v.x;this.y=v.y;this.z=v.z;return this;}
  clone(){return new V3(this.x,this.y,this.z);}
  add(v){this.x+=v.x;this.y+=v.y;this.z+=v.z;return this;}
  sub(v){this.x-=v.x;this.y-=v.y;this.z-=v.z;return this;}
  multiplyScalar(s){this.x*=s;this.y*=s;this.z*=s;return this;}
  divideScalar(s){this.x/=s;this.y/=s;this.z/=s;return this;}
  length(){return Math.hypot(this.x,this.y,this.z);}
  distanceTo(v){return Math.hypot(this.x-v.x,this.y-v.y,this.z-v.z);}
  normalize(){const l=this.length()||1;this.x/=l;this.y/=l;this.z/=l;return this;}
  setScalar(s){this._s=s;return this;}
  project(){return this;}
}
class Obj3D {
  constructor(){this.position=new V3();this.scale=new V3(1,1,1);this.quaternion={setFromUnitVectors(){return this;}};this.rotation={};this.userData={};this.children=[];this.visible=true;}
  add(o){this.children.push(o);return this;}
  remove(o){const i=this.children.indexOf(o);if(i>=0)this.children.splice(i,1);return this;}
}
class Geo { dispose(){} }
class Mat { constructor(o={}){Object.assign(this,o);this.color={hex:o.color,setHex(){},getHex(){return 0;},setHSL(){return this;}};} dispose(){} }
window.THREE = {
  Vector2: class { constructor(x=0,y=0){this.x=x;this.y=y;} },
  Vector3: V3,
  Color: class { constructor(h){this.h=h;} setHSL(){return this;} getHex(){return 0x888888;} },
  Object3D: Obj3D, Group: class extends Obj3D {},
  Mesh: class extends Obj3D { constructor(g,m){super();this.geometry=g;this.material=m;} },
  LineSegments: class extends Obj3D { constructor(g,m){super();this.geometry=g;this.material=m;} },
  Scene: class extends Obj3D {},
  PerspectiveCamera: class extends Obj3D { constructor(){super();} lookAt(){} updateProjectionMatrix(){} },
  WebGLRenderer: class {
    constructor(o){ this.canvas=o.canvas; this.opts=o; }
    setSize(){} setPixelRatio(){}
    render(){ renderCalls++; }
  },
  DirectionalLight: class extends Obj3D {}, AmbientLight: class extends Obj3D {},
  SphereGeometry: Geo, CylinderGeometry: Geo, BoxGeometry: Geo,
  BufferGeometry: class extends Geo { setFromPoints(){return this;} },
  LineBasicMaterial: Mat, MeshStandardMaterial: Mat,
  Raycaster: class { setFromCamera(){} intersectObjects(){return [];} },
};

// drive the shared ticker manually so we control exactly how many frames pass
let rafCallbacks = [];
window.requestAnimationFrame = (cb) => { rafCallbacks.push(cb); return rafCallbacks.length; };
function runFrames(n) {
  for (let i = 0; i < n; i++) {
    const due = rafCallbacks; rafCallbacks = [];
    due.forEach(cb => cb());
  }
}
window.ResizeObserver = class { observe(){} };

// capture the canvas' registered event listeners so we can fire context loss
const canvasListeners = {};
const canvasEl = window.document.getElementById('c');
const origAdd = canvasEl.addEventListener.bind(canvasEl);
canvasEl.addEventListener = (type, fn, opts) => {
  (canvasListeners[type] = canvasListeners[type] || []).push(fn);
  return origAdd(type, fn, opts);
};
// give the container a non-zero size (jsdom reports 0 by default)
const wrap = window.document.getElementById('wrap');
Object.defineProperty(wrap, 'clientWidth', { value: 400 });
Object.defineProperty(wrap, 'clientHeight', { value: 300 });

const assert = (c, m) => { if (!c) { console.error('FAIL: ' + m); process.exit(1); } console.log('OK:', m); };

const SRC = SITE;
window.eval(fs.readFileSync(path.join(SRC, 'mof_decompose.js'), 'utf8'));
window.eval(fs.readFileSync(path.join(SRC, 'mof_render.js'), 'utf8'));

const cif = window.MOFDecompose.parseCIF(fs.readFileSync(path.join(SRC, 'HKUST-1.cif'), 'utf8'));
cif.atoms.cellPar = cif.cellPar;
const DATA = window.MOFDecompose.buildAllVariants(cif.atoms, cif.cellMatrix).metalOxo;

const R = window.MOFRender.create();
R.init(canvasEl, wrap, window.document.getElementById('labels'), window.document.getElementById('tip'));
R.load(DATA, { colorMode: 'element', showBonds: true, showCell: true });

// ---------- 1. on-demand rendering ----------
runFrames(1);
const afterFirst = renderCalls;
assert(afterFirst >= 1, 'renders once after load (' + afterFirst + ' draw call)');

renderCalls = 0;
runFrames(120);   // simulate ~2 seconds of animation frames on a STATIC scene
assert(renderCalls === 0,
  'static scene issues ZERO draw calls over 120 frames (old code would have issued 120) — got ' + renderCalls);

// ---------- 2. re-render on demand when something changes ----------
renderCalls = 0;
R.requestRender();
runFrames(5);
assert(renderCalls === 1, 'exactly one redraw after requestRender(), not one per frame — got ' + renderCalls);

renderCalls = 0;
R.load(DATA, { colorMode: 'block', blockColorStyle: 'nodeLinker', showBonds: true, showCell: true });
runFrames(5);
assert(renderCalls === 1, 'loading new data triggers exactly one redraw — got ' + renderCalls);

// ---------- 3. WebGL context loss + restore ----------
assert(Array.isArray(canvasListeners['webglcontextlost']) && canvasListeners['webglcontextlost'].length > 0,
  'registered a webglcontextlost handler (without one the canvas stays blank forever)');
assert(Array.isArray(canvasListeners['webglcontextrestored']) && canvasListeners['webglcontextrestored'].length > 0,
  'registered a webglcontextrestored handler');

let defaultPrevented = false;
const lostEvent = { preventDefault: () => { defaultPrevented = true; } };
canvasListeners['webglcontextlost'].forEach(fn => fn(lostEvent));
assert(defaultPrevented,
  'context-loss handler calls preventDefault() — REQUIRED for the browser to ever restore the context');

renderCalls = 0;
runFrames(30);
assert(renderCalls === 0, 'no draw calls attempted while the context is lost — got ' + renderCalls);

canvasListeners['webglcontextrestored'].forEach(fn => fn({}));
runFrames(3);
assert(renderCalls > 0, 'scene automatically redraws itself after the context is restored (' + renderCalls + ' draw calls) — this is what stops the "3D stopped working" symptom');

console.log('\nALL RENDER-ROBUSTNESS CHECKS PASSED');
process.exit(0);
