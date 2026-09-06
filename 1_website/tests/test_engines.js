// test_engines.js — boots each page's real scripts in jsdom and checks that
// the computed content actually landed. This is the test that matters: the
// pages are mostly empty containers until the engines fill them, so a script
// that silently no-ops produces a page that looks fine to a static check and
// blank to a human.
const path = require('path');
const SITE = path.join(__dirname, '..');
const fs = require('fs');
const { JSDOM } = require('jsdom');

let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS  ' : 'FAIL  ') + m); if (!c) fails++; };

function boot(page) {
  const html = fs.readFileSync(path.join(SITE, page), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'outside-only', pretendToBeVisual: true,
                                url: 'https://example.org/' + page });
  const W = dom.window;

  // --- stubs for the things jsdom has no implementation of ---------------
  W.HTMLCanvasElement.prototype.getContext = function () {
    const noop = () => {};
    return new Proxy({ measureText: () => ({ width: 10 }),
                       createLinearGradient: () => ({ addColorStop: noop }),
                       getImageData: () => ({ data: [] }),
                       canvas: this },
      { get: (t, k) => (k in t ? t[k] : noop), set: () => true });
  };
  W.IntersectionObserver = class { constructor(cb){this.cb=cb;} observe(el){this.cb([{isIntersecting:true,target:el}],this);} unobserve(){} disconnect(){} };
  W.ResizeObserver = class { observe(){} unobserve(){} disconnect(){} };
  W.matchMedia = W.matchMedia || (q => ({ matches:false, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} }));
  W.requestAnimationFrame = fn => setTimeout(() => fn(Date.now()), 0);
  W.scrollTo = () => {};

  // minimal THREE stub — enough for the renderers to construct without WebGL
  const vecStub = () => new Proxy({}, { get: (t, k) => (k === 'x' || k === 'y' || k === 'z' ? 0 : () => vecStub()) });
  const O3 = class {
    constructor(){ this.children=[]; this.position=vecStub(); this.rotation=vecStub();
                   this.scale=vecStub(); this.material={}; this.geometry={}; this.userData={}; }
    add(){return this;} remove(){} traverse(){} lookAt(){} updateMatrixWorld(){}
    clear(){} getObjectByName(){return null;} };
  const Geo = class { constructor(){} setFromPoints(){return this;} dispose(){} translate(){} };
  const V3 = class { constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;}
    set(){return this;} copy(){return this;} clone(){return new V3();} add(){return this;}
    setScalar(){return this;} multiply(){return this;} negate(){return this;}
    setFromMatrixPosition(){return this;} project(){return this;} unproject(){return this;}
    cross(){return this;} dot(){return 0;} angleTo(){return 0;} equals(){return false;}
    toArray(){return [0,0,0];} fromArray(){return this;} setLength(){return this;}
    sub(){return this;} multiplyScalar(){return this;} divideScalar(){return this;}
    normalize(){return this;} length(){return 1;} distanceTo(){return 1;}
    crossVectors(){return this;} subVectors(){return this;} applyQuaternion(){return this;}
    setFromMatrixColumn(){return this;} addVectors(){return this;} lerp(){return this;} };
  W.THREE = new Proxy({
    Scene:O3, Group:O3, Object3D:O3, Mesh:O3, Line:O3, LineSegments:O3, Points:O3,
    PerspectiveCamera: class extends O3 { updateProjectionMatrix(){} },
    WebGLRenderer: class { constructor(){this.domElement=dom.window.document.createElement('canvas');}
                           setSize(){} setPixelRatio(){} render(){} dispose(){} setClearColor(){} },
    Vector2:V3, Vector3:V3, Color: class { constructor(){} setHex(){return this;} },
    SphereGeometry:Geo, CylinderGeometry:Geo, BoxGeometry:Geo, BufferGeometry:Geo,
    EdgesGeometry:Geo, MeshStandardMaterial:class{constructor(){} dispose(){}},
    MeshBasicMaterial:class{constructor(){} dispose(){}}, LineBasicMaterial:class{constructor(){} dispose(){}},
    PointsMaterial:class{constructor(){} dispose(){}},
    DirectionalLight:O3, AmbientLight:O3, HemisphereLight:O3, PointLight:O3,
    Raycaster:class{setFromCamera(){} intersectObjects(){return [];}},
    Matrix4:class{}, Quaternion:class{}, Float32BufferAttribute:class{},
  }, { get:(t,k)=> k in t ? t[k] : O3 });

  const errs = [];
  // run every local <script src> in document order, exactly as a browser would
  [...dom.window.document.querySelectorAll('script[src]')].forEach(s => {
    const src = s.getAttribute('src');
    if (/^https?:/.test(src) || src === 'three.min.js') return;
    try { W.eval(fs.readFileSync(path.join(SITE, src), 'utf8')); }
    catch (e) { errs.push(src + ': ' + e.message); }
  });
  try { W.document.dispatchEvent(new W.Event('DOMContentLoaded', { bubbles: true })); }
  catch (e) { errs.push('DOMContentLoaded: ' + e.message); }
  return { W, D: W.document, errs };
}

const filled = (D, id) => { const e = D.getElementById(id); return !!e && e.innerHTML.trim().length > 30; };

// ---- index / methodology: the overview tables --------------------------
['index.html', 'methodology.html'].forEach(p => {
  const { D, errs } = boot(p);
  ok(errs.length === 0, `${p}: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  if (D.getElementById('tie-evidence')) ok(filled(D, 'tie-evidence'), `${p}: evidence table computed`);
  if (D.getElementById('results-summary')) ok(filled(D, 'results-summary'), `${p}: results summary computed`);
  if (D.getElementById('degree-value')) ok(D.getElementById('degree-value').textContent.trim().length > 0,
                                           `${p}: live coordination number computed`);
});

// ---- decomposition: the module walkthrough -----------------------------
{
  const { D, errs } = boot('decomposition.html');
  ok(errs.length === 0, `decomposition.html: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  ok(filled(D, 'pw-module-tabs'), 'decomposition.html: module tabs built');
  ok(filled(D, 'pw-code-area') || filled(D, 'pw-explain'), 'decomposition.html: walkthrough content rendered');
  const fr = D.getElementById('pipeline-frame');
  ok(!!fr && fr.getAttribute('data-src') === 'mof_pipeline_viewer.html',
     'decomposition.html: interactive tool iframe is wired to its viewer');
}

// ---- network: graph, centrality, defects, Laplacian --------------------
{
  const { D, errs } = boot('network.html');
  ok(errs.length === 0, `network.html: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  ok(D.querySelectorAll('#net-struct-tabs .struct-tab').length === 4, 'network.html: four demonstration structures offered');
  ok(filled(D, 'validation'), 'network.html: coordination-number validation computed');
  ok(filled(D, 'centrality'), 'network.html: centrality table computed');
  ok(filled(D, 'fingerprint-table'), 'network.html: Laplacian fingerprint table computed');
}

// ---- spectrum: the multifractal tables ---------------------------------
{
  const { D, errs } = boot('spectrum.html');
  ok(errs.length === 0, `spectrum.html: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  ok(filled(D, 'mf-table'), 'spectrum.html: multifractal table computed');
  ok(filled(D, 'paper-table'), 'spectrum.html: published-method table computed');
  ok(filled(D, 'mf-fixes'), 'spectrum.html: defect table rendered');
  const v = D.getElementById('mf-verdict');
  ok(!!v && /implementation is correct/i.test(v.textContent),
     'spectrum.html: the four structures are framed as implementation validation');
  ok(!!v && !/reference band is built/i.test(v.textContent),
     'spectrum.html: no band is claimed from the four demonstration structures');
}

// ---- results: the band, from the 77 only -------------------------------
{
  const { W, D, errs } = boot('results.html');
  ok(errs.length === 0, `results.html: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  ok(filled(D, 'band-body'), 'results.html: band section computed');
  const n = Object.keys(W.BAND_DATA || {}).length;
  ok(n === 77, `results.html: band built from 77 frameworks (got ${n})`);
  const demo = ['HKUST-1', 'UiO-66', 'MOF-5', 'ZIF-8'].filter(k => k in (W.BAND_DATA || {}));
  ok(demo.length === 0, `results.html: demonstration structures excluded from the band${demo.length ? ' — found ' + demo : ''}`);
  ok(W.BAND_STATS && W.BAND_STATS.parabolic === 77, 'results.html: all 77 spectra are valid');
  ok(/realmof/.test(D.body.innerHTML), 'results.html: plan for scaling to 50+ real MOFs present');

  // ---- the synthesised-MOF comparison -----------------------------------
  const R = W.REAL_BAND_DATA || {}, RS = W.REAL_BAND_STATS || {};
  ok(Object.keys(R).length === 4, `results.html: four synthesised MOFs computed (got ${Object.keys(R).length})`);
  ok(Object.values(R).every(v => v.synthesised && v.cn_match),
     'results.html: every real MOF reproduces its published coordination number');
  ok(filled(D, 'real-band-body'), 'results.html: synthesised-MOF comparison rendered');
  // the two sets must be kept separate — this is the whole point of the section
  const overlap = Object.keys(R).filter(k => k in W.BAND_DATA);
  ok(overlap.length === 0, 'results.html: real MOFs are not mixed into the 77-framework band');
  const hHi = Math.max(...Object.values(W.BAND_DATA).map(v => v.width));
  ok(RS.w_min > hHi, `results.html: the reported gap is real (hMOF max ${hHi.toFixed(2)} < real min ${RS.w_min.toFixed(2)})`);
  ok(RS.metals.length >= 3, `results.html: the real set spans several metals (${RS.metals})`);
}

// ---- code: the source browser -----------------------------------------
{
  const { W, D, errs } = boot('code.html');
  ok(errs.length === 0, `code.html: all scripts ran clean${errs.length ? ' — ' + errs[0] : ''}`);
  ok(Object.keys(W.CODE_SOURCES || {}).length >= 25, 'code.html: all source files embedded');
  ok(D.querySelectorAll('#code-grid .codecard').length >= 25, 'code.html: source browser lists every file');
  ok(!('enhance.js' in (W.CODE_SOURCES || {})), 'code.html: the removed enhance.js is not still listed');
}

console.log(fails ? `\n${fails} FAILURES` : '\nAll engine tests passed.');
process.exit(fails ? 1 : 0);
